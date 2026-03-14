from __future__ import annotations

from app.models.inference import PredictionResult
from app.services.media import ExtractedFrameLandmarks


class GestureClassifierService:
    """Clasificador placeholder para desacoplar la API del modelo final.

    Implementa una heuristica minima mientras se integra el modelo real.
    """

    def predict(self, extracted_frames: list[ExtractedFrameLandmarks]) -> PredictionResult:
        """Genera una prediccion a partir de una secuencia de landmarks.

        Args:
            extracted_frames: Frames en los que se ha detectado una mano.

        Returns:
            Resultado tipado con etiqueta y confianza.
        """

        if not extracted_frames:
            return PredictionResult(label="no_hand_detected", confidence=0.0)

        if len(extracted_frames) == 1:
            return PredictionResult(label="hand_detected", confidence=0.75)

        return PredictionResult(label="sequence_detected", confidence=0.8)
