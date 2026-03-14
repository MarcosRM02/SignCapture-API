"""Cliente de prueba para enviar frames de webcam al endpoint de inferencia.

Uso basico:
    .\.venv\Scripts\python scripts\webcam_inference_client.py

Ejemplo contra HTTPS con certificado autofirmado:
    .\.venv\Scripts\python scripts\webcam_inference_client.py ^
        --base-url https://127.0.0.1:8000 --insecure
"""

from __future__ import annotations

import argparse
import time
from typing import Any

import cv2
import httpx

WINDOW_NAME = "SignCapture Webcam Client"


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos del cliente de pruebas."""

    parser = argparse.ArgumentParser(
        description="Captura frames de la webcam y los envia a la API de inferencia.",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="URL base donde esta expuesta la API.",
    )
    parser.add_argument(
        "--endpoint",
        default="/api/v1/inference/frame",
        help="Ruta del endpoint de inferencia de frame.",
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Indice de la webcam que se quiere usar.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.75,
        help="Segundos entre cada envio de frame a la API.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout HTTP para cada peticion.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Desactiva la verificacion TLS. Util solo con certificados autofirmados.",
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=85,
        help="Calidad JPEG usada para comprimir el frame antes de enviarlo.",
    )
    return parser


def encode_frame(frame, jpeg_quality: int) -> bytes:
    """Codifica un frame OpenCV a bytes JPEG listos para enviar."""

    ok, buffer = cv2.imencode(
        ".jpg",
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality],
    )
    if not ok:
        raise RuntimeError("No se pudo codificar el frame capturado.")
    return buffer.tobytes()


def send_frame(
    client: httpx.Client,
    endpoint_url: str,
    frame_bytes: bytes,
) -> dict[str, Any]:
    """Envia un frame a la API y devuelve la respuesta JSON."""

    response = client.post(
        endpoint_url,
        files={"file": ("frame.jpg", frame_bytes, "image/jpeg")},
    )
    response.raise_for_status()
    return response.json()


def draw_landmarks(frame, payload: dict[str, Any]) -> None:
    """Dibuja los landmarks devueltos por el backend sobre el frame mostrado."""

    all_landmarks = payload.get("landmarks", [])
    height, width = frame.shape[:2]

    for hand_landmarks in all_landmarks:
        for point in hand_landmarks:
            x = int(point["x"] * width)
            y = int(point["y"] * height)
            cv2.circle(frame, (x, y), 4, (0, 220, 0), thickness=-1)


def draw_panel(frame, payload: dict[str, Any], last_error: str | None) -> None:
    """Pinta un panel de estado con la ultima respuesta del backend."""

    prediction = payload.get("prediction", {})
    metadata = payload.get("metadata", {})
    label = prediction.get("label", "sin respuesta")
    confidence = prediction.get("confidence", 0.0)
    detected = metadata.get("hand_detected_frames", 0)
    processed = metadata.get("processed_frames", 0)
    latency_ms = payload.get("_latency_ms", 0.0)

    panel_lines = [
        f"label: {label}",
        f"confidence: {confidence:.2f}",
        f"processed_frames: {processed}",
        f"hand_detected_frames: {detected}",
        f"backend_latency_ms: {latency_ms:.1f}",
    ]

    if last_error:
        panel_lines.append(f"last_error: {last_error}")

    line_height = 24
    panel_height = 20 + line_height * len(panel_lines)
    cv2.rectangle(frame, (10, 10), (430, 10 + panel_height), (20, 20, 20), thickness=-1)
    cv2.rectangle(frame, (10, 10), (430, 10 + panel_height), (0, 200, 255), thickness=2)

    for index, line in enumerate(panel_lines):
        color = (220, 220, 220) if "last_error" not in line else (0, 120, 255)
        cv2.putText(
            frame,
            line,
            (20, 35 + line_height * index),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )

    cv2.putText(
        frame,
        "q o ESC para salir",
        (20, frame.shape[0] - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def main() -> None:
    """Ejecuta el bucle de captura y envio de frames desde la webcam."""

    args = build_parser().parse_args()
    endpoint_url = f"{args.base_url.rstrip('/')}{args.endpoint}"

    capture = cv2.VideoCapture(args.camera_index)
    if not capture.isOpened():
        raise RuntimeError(
            f"No se pudo abrir la webcam con indice {args.camera_index}.",
        )

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    print("Cliente de pruebas iniciado.")
    print(f"Enviando frames a: {endpoint_url}")
    print("Pulsa q, ESC o cierra la ventana para detener la ejecucion.")

    last_sent_at = 0.0
    last_label: str | None = None
    last_error: str | None = None
    latest_payload: dict[str, Any] = {
        "prediction": {"label": "waiting_backend", "confidence": 0.0},
        "metadata": {"processed_frames": 0, "hand_detected_frames": 0},
        "landmarks": [],
        "_latency_ms": 0.0,
    }

    try:
        with httpx.Client(timeout=args.timeout, verify=not args.insecure) as client:
            while True:
                ok, frame = capture.read()
                if not ok:
                    print("No se pudo leer un frame de la webcam.")
                    time.sleep(args.interval)
                    continue

                display_frame = frame.copy()
                now = time.monotonic()

                if now - last_sent_at >= args.interval:
                    frame_bytes = encode_frame(frame, jpeg_quality=args.jpeg_quality)
                    request_started_at = time.perf_counter()
                    try:
                        latest_payload = send_frame(client, endpoint_url, frame_bytes)
                        latest_payload["_latency_ms"] = (
                            time.perf_counter() - request_started_at
                        ) * 1000
                        last_error = None
                    except httpx.HTTPError as exc:
                        last_error = str(exc)
                        latest_payload["_latency_ms"] = 0.0
                        print(f"Error HTTP enviando frame: {exc}")
                    else:
                        prediction = latest_payload.get("prediction", {})
                        label = prediction.get("label", "unknown")
                        confidence = prediction.get("confidence", 0.0)
                        detected = latest_payload.get("metadata", {}).get(
                            "hand_detected_frames",
                            0,
                        )
                        if label != last_label:
                            print(
                                f"Prediccion: {label} | "
                                f"confidence={confidence:.2f} | "
                                f"hand_detected_frames={detected}",
                            )
                            last_label = label
                    last_sent_at = now

                draw_landmarks(display_frame, latest_payload)
                draw_panel(display_frame, latest_payload, last_error)
                cv2.imshow(WINDOW_NAME, display_frame)

                pressed_key = cv2.waitKey(1) & 0xFF
                if pressed_key in (27, ord("q")):
                    break

                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    break
    except KeyboardInterrupt:
        print("Cliente detenido por el usuario.")
    finally:
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
