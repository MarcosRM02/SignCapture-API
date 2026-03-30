from __future__ import annotations

import pickle
from dataclasses import dataclass
from typing import Any

import numpy as np

from app.core.config import Settings
from app.models.inference import (
    ClassificationResult,
    FeedbackResult,
    PredictionCandidate,
    PredictionResult,
)
from app.services.landmark_features import build_feature_vector
from app.services.media import ExtractedFrameLandmarks


@dataclass
class HandPoseDiagnostics:
    """Metricas simples de calidad para enriquecer el feedback."""

    average_area: float
    average_center_offset: float
    clipped_frame_ratio: float


class GestureClassifierService:
    """Encapsula la carga del modelo real y la generacion de feedback."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model: Any | None = None
        self._model_name = "xgboost"
        self._class_labels: list[str] | None = None

    @property
    def model_name(self) -> str:
        """Expone el nombre del modelo cargado para trazabilidad."""

        return self._model_name

    def predict(self, extracted_frames: list[ExtractedFrameLandmarks]) -> ClassificationResult:
        """Predice la letra mas probable y construye feedback accionable."""

        if not extracted_frames:
            return ClassificationResult(
                prediction=PredictionResult(
                    label="sin_deteccion",
                    confidence=0.0,
                    top_candidates=[],
                ),
                feedback=FeedbackResult(
                    level="error",
                    title="No se detecta ninguna mano",
                    message="No puedo identificar la letra mientras la mano no sea visible.",
                    tips=[
                        "Coloca la mano completa dentro del encuadre.",
                        "Acercala un poco mas a la camara y mejora la iluminacion.",
                        "Mantente quieto un instante antes de cambiar de signo.",
                    ],
                ),
                consistency=None,
            )

        model = self._load_model()
        feature_matrix = np.vstack(
            [
                build_feature_vector(self._landmarks_to_array(frame.landmarks))
                for frame in extracted_frames
            ]
        ).astype(np.float32, copy=False)
        probabilities = self._predict_probabilities(model, feature_matrix)
        mean_probabilities = probabilities.mean(axis=0)
        class_labels = self._resolve_class_labels(model, mean_probabilities.shape[0])
        top_candidates = self._build_top_candidates(class_labels, mean_probabilities)

        prediction = PredictionResult(
            label=top_candidates[0].label,
            confidence=top_candidates[0].confidence,
            top_candidates=top_candidates,
        )
        consistency = self._compute_consistency(
            probabilities=probabilities,
            class_labels=class_labels,
            winning_label=prediction.label,
        )
        diagnostics = self._analyze_pose(extracted_frames)
        feedback = self._build_feedback(
            prediction=prediction,
            top_candidates=top_candidates,
            diagnostics=diagnostics,
            consistency=consistency,
            detected_frames=len(extracted_frames),
        )
        return ClassificationResult(
            prediction=prediction,
            feedback=feedback,
            consistency=consistency,
        )

    def _load_model(self) -> Any:
        """Carga el modelo pickle solo una vez por proceso."""

        if self._model is not None:
            return self._model

        model_path = self._settings.model_path
        if not model_path.exists():
            raise RuntimeError(f"No se encontro el modelo configurado en: {model_path}")

        try:
            with model_path.open("rb") as model_file:
                payload = pickle.load(model_file)
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "No se pudo cargar el modelo pickle. "
                "Instala las dependencias 'xgboost' y 'scikit-learn' en la API."
            ) from exc
        except OSError as exc:
            raise RuntimeError(f"No se pudo abrir el modelo en disco: {model_path}") from exc
        except Exception as exc:
            raise RuntimeError("El modelo no se pudo deserializar correctamente.") from exc

        model = payload.get("model") if isinstance(payload, dict) else payload
        if model is None:
            raise RuntimeError("El fichero del modelo no contiene un objeto clasificable valido.")
        if not hasattr(model, "predict_proba"):
            raise RuntimeError("El modelo cargado no expone el metodo 'predict_proba'.")

        if isinstance(payload, dict) and payload.get("model_name"):
            self._model_name = str(payload["model_name"])
        else:
            self._model_name = type(model).__name__

        self._model = model
        return self._model

    @staticmethod
    def _predict_probabilities(model: Any, feature_matrix: np.ndarray) -> np.ndarray:
        try:
            probabilities = np.asarray(model.predict_proba(feature_matrix), dtype=np.float32)
        except Exception as exc:
            raise RuntimeError("El modelo no pudo generar probabilidades de inferencia.") from exc

        if probabilities.ndim != 2 or probabilities.shape[0] == 0 or probabilities.shape[1] == 0:
            raise RuntimeError("La salida de probabilidades del modelo es invalida.")

        return probabilities

    def _resolve_class_labels(self, model: Any, num_classes: int) -> list[str]:
        """Resuelve el mapeo entre indices numericos y letras visibles."""

        if self._class_labels is not None:
            return self._class_labels

        configured_labels = self._settings.get_model_class_labels()
        raw_classes = getattr(model, "classes_", None)

        if raw_classes is not None:
            raw_classes_list = np.asarray(raw_classes).tolist()
            if len(raw_classes_list) == num_classes and all(
                isinstance(item, str) for item in raw_classes_list
            ):
                self._class_labels = [str(item).upper() for item in raw_classes_list]
                return self._class_labels

            if len(raw_classes_list) == num_classes and all(
                isinstance(item, (int, np.integer)) for item in raw_classes_list
            ):
                if len(configured_labels) != num_classes:
                    raise RuntimeError(
                        "El modelo devuelve clases numericas, pero la configuracion "
                        "SIGNCAPTURE_MODEL_CLASS_LABELS_CSV no tiene el mismo tamano."
                    )
                self._class_labels = [configured_labels[int(item)] for item in raw_classes_list]
                return self._class_labels

        if len(configured_labels) == num_classes:
            self._class_labels = configured_labels
            return self._class_labels

        raise RuntimeError(
            "No se pudo resolver el mapeo de clases del modelo. "
            "Revisa SIGNCAPTURE_MODEL_CLASS_LABELS_CSV."
        )

    def _build_top_candidates(
        self,
        class_labels: list[str],
        probabilities: np.ndarray,
    ) -> list[PredictionCandidate]:
        top_k = min(self._settings.model_top_k, len(class_labels))
        ordered_indices = np.argsort(probabilities)[::-1][:top_k]
        return [
            PredictionCandidate(
                label=class_labels[index],
                confidence=float(probabilities[index]),
            )
            for index in ordered_indices
        ]

    @staticmethod
    def _compute_consistency(
        probabilities: np.ndarray,
        class_labels: list[str],
        winning_label: str,
    ) -> float | None:
        if probabilities.shape[0] <= 1:
            return None

        frame_labels = [class_labels[index] for index in probabilities.argmax(axis=1).tolist()]
        hits = sum(label == winning_label for label in frame_labels)
        return hits / len(frame_labels)

    @staticmethod
    def _landmarks_to_array(landmarks) -> np.ndarray:
        return np.array([[point.x, point.y, point.z] for point in landmarks], dtype=np.float64)

    def _analyze_pose(
        self,
        extracted_frames: list[ExtractedFrameLandmarks],
    ) -> HandPoseDiagnostics:
        areas: list[float] = []
        center_offsets: list[float] = []
        clipped_frames = 0

        for frame in extracted_frames:
            landmarks = self._landmarks_to_array(frame.landmarks)

            min_x = float(landmarks[:, 0].min())
            max_x = float(landmarks[:, 0].max())
            min_y = float(landmarks[:, 1].min())
            max_y = float(landmarks[:, 1].max())

            areas.append(max(max_x - min_x, 0.0) * max(max_y - min_y, 0.0))

            center_x = (min_x + max_x) / 2.0
            center_y = (min_y + max_y) / 2.0
            center_offsets.append(float(np.hypot(center_x - 0.5, center_y - 0.5)))

            frame_margin = min(min_x, min_y, 1 - max_x, 1 - max_y)
            if frame_margin < 0.03:
                clipped_frames += 1

        frame_count = max(len(extracted_frames), 1)
        return HandPoseDiagnostics(
            average_area=sum(areas) / frame_count,
            average_center_offset=sum(center_offsets) / frame_count,
            clipped_frame_ratio=clipped_frames / frame_count,
        )

    def _build_feedback(
        self,
        prediction: PredictionResult,
        top_candidates: list[PredictionCandidate],
        diagnostics: HandPoseDiagnostics,
        consistency: float | None,
        detected_frames: int,
    ) -> FeedbackResult:
        ambiguous_candidate = None
        if len(top_candidates) > 1:
            confidence_gap = top_candidates[0].confidence - top_candidates[1].confidence
            if confidence_gap < 0.12:
                ambiguous_candidate = top_candidates[1]

        if prediction.confidence >= self._settings.prediction_success_threshold:
            level = "success"
            title = f"Letra detectada: {prediction.label}"
            message = (
                f"La configuracion de la mano coincide con bastante seguridad "
                f"con la letra {prediction.label}."
            )
        elif prediction.confidence >= self._settings.prediction_warning_threshold:
            level = "info"
            title = f"La letra mas probable es {prediction.label}"
            message = (
                f"Ahora mismo la postura se parece a la letra {prediction.label}, "
                "aunque todavia hay algo de ambiguedad."
            )
        else:
            level = "warning"
            title = f"Prediccion tentativa: {prediction.label}"
            message = (
                f"La letra mas probable es {prediction.label}, pero la confianza "
                "todavia es baja."
            )

        if ambiguous_candidate is not None:
            message += f" La alternativa mas cercana es {ambiguous_candidate.label}."

        if detected_frames > 1 and consistency is not None:
            message += f" La consistencia entre frames es del {consistency:.0%}."

        tips: list[str] = []
        if diagnostics.average_area < 0.10:
            tips.append("Acerca un poco mas la mano a la camara para que ocupe mas espacio.")
        if diagnostics.average_center_offset > 0.22:
            tips.append("Centra la mano antes de cambiar de signo.")
        if diagnostics.clipped_frame_ratio > 0.0:
            tips.append("Evita cortar dedos o la muneca con los bordes del encuadre.")
        if prediction.confidence < self._settings.prediction_success_threshold:
            tips.append("Mantente quieto un instante para que la postura se lea mejor.")
        if ambiguous_candidate is not None:
            tips.append(
                f"Revisa la forma del signo porque el modelo tambien la confunde con {ambiguous_candidate.label}."
            )
        if consistency is not None and consistency < 0.65:
            tips.append("Haz el signo de forma mas estable durante varios frames seguidos.")

        tips = self._dedupe_preserving_order(tips)
        if not tips:
            tips = ["Mantiene la postura un momento mas si quieres confirmar la deteccion."]

        return FeedbackResult(
            level=level,
            title=title,
            message=message,
            tips=tips[:4],
        )

    @staticmethod
    def _dedupe_preserving_order(values: list[str]) -> list[str]:
        unique_values: list[str] = []
        seen: set[str] = set()
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            unique_values.append(value)
        return unique_values
