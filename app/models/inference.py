from typing import Literal

from pydantic import BaseModel, Field


class LandmarkPoint(BaseModel):
    """Representa un landmark tridimensional de la mano."""

    x: float
    y: float
    z: float


class PredictionResult(BaseModel):
    """Contiene la salida del clasificador para una inferencia."""

    label: str = Field(description="Etiqueta predicha por el clasificador.")
    confidence: float = Field(ge=0.0, le=1.0)


class InferenceMetadata(BaseModel):
    """Incluye metadatos de proceso utiles para trazabilidad funcional."""

    source_type: Literal["frame", "video"]
    processed_frames: int = Field(ge=0)
    hand_detected_frames: int = Field(ge=0)


class InferenceResponse(BaseModel):
    """Contrato de respuesta estandar de la API de inferencia."""

    prediction: PredictionResult
    metadata: InferenceMetadata
    landmarks: list[list[LandmarkPoint]] = Field(
        default_factory=list,
        description="Landmarks detectados por frame. Cada frame contiene 21 puntos si hubo mano.",
    )
