from typing import Literal

from pydantic import BaseModel, Field


class LandmarkPoint(BaseModel):
    """Representa un landmark tridimensional de la mano."""

    x: float
    y: float
    z: float


class PredictionCandidate(BaseModel):
    """Alternativa de prediccion con su confianza asociada."""

    label: str = Field(description="Etiqueta candidata.")
    confidence: float = Field(ge=0.0, le=1.0)


class PredictionResult(BaseModel):
    """Contiene la salida del clasificador para una inferencia."""

    label: str = Field(description="Etiqueta predicha por el clasificador.")
    confidence: float = Field(ge=0.0, le=1.0)
    top_candidates: list[PredictionCandidate] = Field(default_factory=list)


class FeedbackResult(BaseModel):
    """Feedback textual para guiar el uso de la herramienta de ensenanza."""

    level: Literal["success", "info", "warning", "error"]
    title: str
    message: str
    tips: list[str] = Field(default_factory=list)


class ClassificationResult(BaseModel):
    """Resultado intermedio del clasificador antes de construir la respuesta HTTP."""

    prediction: PredictionResult
    feedback: FeedbackResult
    consistency: float | None = Field(default=None, ge=0.0, le=1.0)


class InferenceMetadata(BaseModel):
    """Incluye metadatos de proceso utiles para trazabilidad funcional."""

    source_type: Literal["frame", "video"]
    processed_frames: int = Field(ge=0)
    hand_detected_frames: int = Field(ge=0)
    prediction_consistency: float | None = Field(default=None, ge=0.0, le=1.0)
    model_name: str | None = None


class InferenceResponse(BaseModel):
    """Contrato de respuesta estandar de la API de inferencia."""

    prediction: PredictionResult
    feedback: FeedbackResult
    metadata: InferenceMetadata
    landmarks: list[list[LandmarkPoint]] = Field(
        default_factory=list,
        description="Landmarks detectados por frame. Cada frame contiene 21 puntos si hubo mano.",
    )
