from functools import lru_cache

from app.controllers.inference_controller import InferenceController
from app.core.config import get_settings
from app.services.classifier import GestureClassifierService
from app.services.inference import InferenceService
from app.services.media import MediaPipeHandLandmarkService


@lru_cache
def get_inference_controller() -> InferenceController:
    """Construye y cachea el controlador principal de inferencia."""

    settings = get_settings()
    service = InferenceService(
        settings=settings,
        landmark_service=MediaPipeHandLandmarkService(),
        classifier_service=GestureClassifierService(settings=settings),
    )
    return InferenceController(service=service)
