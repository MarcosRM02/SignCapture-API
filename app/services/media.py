from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import cv2
import mediapipe as mp
import numpy as np

from app.models.inference import LandmarkPoint


@dataclass
class ExtractedFrameLandmarks:
    """Resultado de landmarks para un frame concreto."""

    frame_index: int
    landmarks: list[LandmarkPoint]


@dataclass
class VideoExtractionResult:
    """Resultado agregado del procesamiento de un video."""

    processed_frames: int
    extracted_frames: list[ExtractedFrameLandmarks]


class MediaPipeHandLandmarkService:
    """Encapsula la extraccion de landmarks de mano con MediaPipe."""

    def __init__(self) -> None:
        """Inicializa el acceso al modulo de manos de MediaPipe."""

        self._configure_mediapipe_resource_path()
        try:
            self._mp_hands = mp.solutions.hands
        except AttributeError as exc:
            raise RuntimeError(
                "La instalacion actual de MediaPipe no expone 'solutions.hands'. "
                "Reinstala una version compatible del proyecto."
            ) from exc

    def _configure_mediapipe_resource_path(self) -> None:
        """Ajusta la ruta interna de recursos para entornos Windows con rutas no ASCII."""

        try:
            from mediapipe.python import solution_base
        except Exception:
            return

        current_file = getattr(solution_base, "__file__", None)
        if not current_file:
            return

        short_path = self._to_windows_short_path(Path(current_file))
        if short_path:
            solution_base.__file__ = short_path

    @staticmethod
    def _to_windows_short_path(path: Path) -> str | None:
        """Devuelve la ruta corta de Windows si existe y esta disponible."""

        if os.name != "nt":
            return None

        try:
            import ctypes

            buffer = ctypes.create_unicode_buffer(4096)
            result = ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, len(buffer))
            return buffer.value if result else None
        except Exception:
            return None

    def extract_from_image_bytes(self, image_bytes: bytes) -> list[ExtractedFrameLandmarks]:
        """Extrae landmarks a partir de una imagen codificada en bytes.

        Args:
            image_bytes: Contenido binario del frame recibido.

        Returns:
            Una lista con cero o una deteccion, segun si se encuentra una mano.

        Raises:
            ValueError: Si la imagen no puede decodificarse.
        """

        image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("No se pudo decodificar la imagen enviada.")
        with self._build_hands_processor() as hands:
            frame_landmarks = self._extract_from_bgr_frame(image, frame_index=0, hands=hands)
        return [frame_landmarks] if frame_landmarks else []

    def extract_from_video_file(
        self,
        video_stream: BinaryIO,
        max_frames: int,
    ) -> VideoExtractionResult:
        """Procesa un video y extrae landmarks frame a frame.

        Args:
            video_stream: Flujo binario del video subido.
            max_frames: Limite maximo de frames a procesar.

        Returns:
            Resultado agregado con el total de frames procesados y las
            detecciones efectivas.
        """

        file_bytes = np.asarray(bytearray(video_stream.read()), dtype=np.uint8)
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".mp4",
            dir=".",
            delete=False,
        ) as temp_file:
            temp_file.write(file_bytes.tobytes())
            temp_path = temp_file.name

        capture = cv2.VideoCapture(temp_path)
        extracted: list[ExtractedFrameLandmarks] = []
        frame_index = 0
        try:
            with self._build_hands_processor() as hands:
                while frame_index < max_frames:
                    ok, frame = capture.read()
                    if not ok:
                        break
                    frame_landmarks = self._extract_from_bgr_frame(
                        frame,
                        frame_index=frame_index,
                        hands=hands,
                    )
                    if frame_landmarks:
                        extracted.append(frame_landmarks)
                    frame_index += 1
        finally:
            capture.release()
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return VideoExtractionResult(processed_frames=frame_index, extracted_frames=extracted)

    def _build_hands_processor(self):
        """Construye una instancia de MediaPipe Hands con la configuracion actual."""

        return self._mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=0.5,
        )

    def _extract_from_bgr_frame(
        self,
        frame: np.ndarray,
        frame_index: int,
        hands,
    ) -> ExtractedFrameLandmarks | None:
        """Extrae landmarks de un frame BGR ya decodificado.

        Args:
            frame: Imagen BGR compatible con OpenCV.
            frame_index: Posicion secuencial del frame.
            hands: Procesador MediaPipe ya inicializado.

        Returns:
            Los landmarks del frame si hay deteccion; `None` en caso contrario.
        """

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)

        if not result.multi_hand_landmarks:
            return None

        hand_landmarks = result.multi_hand_landmarks[0]
        landmarks = [
            LandmarkPoint(x=point.x, y=point.y, z=point.z)
            for point in hand_landmarks.landmark
        ]
        return ExtractedFrameLandmarks(frame_index=frame_index, landmarks=landmarks)
