from __future__ import annotations

from fastapi import UploadFile

from app.core.config import Settings
from app.models.inference import InferenceMetadata, InferenceResponse
from app.services.classifier import GestureClassifierService
from app.services.media import MediaPipeHandLandmarkService


class InferenceService:
    """Caso de uso principal para inferencia sobre frames y videos."""

    def __init__(
        self,
        settings: Settings,
        landmark_service: MediaPipeHandLandmarkService,
        classifier_service: GestureClassifierService,
    ) -> None:
        """Recibe las dependencias necesarias para ejecutar el pipeline."""

        self._settings = settings
        self._landmark_service = landmark_service
        self._classifier_service = classifier_service

    async def process_frame(self, upload: UploadFile) -> InferenceResponse:
        """Procesa un frame individual.

        Args:
            upload: Archivo recibido por FastAPI.

        Returns:
            Respuesta completa de inferencia con prediccion y landmarks.

        Raises:
            ValueError: Si el archivo supera el limite permitido o falla el
                procesamiento posterior.
        """

        payload = await upload.read()
        self._validate_size(payload, self._settings.max_frame_bytes, "frame")
        extracted = self._landmark_service.extract_from_image_bytes(payload)
        classification = self._classifier_service.predict(extracted)
        return InferenceResponse(
            prediction=classification.prediction,
            feedback=classification.feedback,
            metadata=InferenceMetadata(
                source_type="frame",
                processed_frames=1,
                hand_detected_frames=len(extracted),
                prediction_consistency=classification.consistency,
                model_name=self._classifier_service.model_name,
            ),
            landmarks=[frame.landmarks for frame in extracted],
        )

    async def process_video(self, upload: UploadFile) -> InferenceResponse:
        """Procesa un video completo respetando la configuracion actual.

        Args:
            upload: Archivo de video recibido por FastAPI.

        Returns:
            Respuesta agregada con metadatos, landmarks y prediccion.

        Raises:
            ValueError: Si el video excede el limite permitido o falla la
                extraccion de landmarks.
        """

        payload = await upload.read()
        self._validate_size(payload, self._settings.max_video_bytes, "video")
        upload.file.seek(0)
        extraction = self._landmark_service.extract_from_video_file(
            upload.file,
            max_frames=self._settings.max_video_frames,
        )
        classification = self._classifier_service.predict(extraction.extracted_frames)
        return InferenceResponse(
            prediction=classification.prediction,
            feedback=classification.feedback,
            metadata=InferenceMetadata(
                source_type="video",
                processed_frames=extraction.processed_frames,
                hand_detected_frames=len(extraction.extracted_frames),
                prediction_consistency=classification.consistency,
                model_name=self._classifier_service.model_name,
            ),
            landmarks=[frame.landmarks for frame in extraction.extracted_frames],
        )

    @staticmethod
    def _validate_size(payload: bytes, max_size: int, source_type: str) -> None:
        """Valida el tamano maximo permitido para una carga binaria."""

        if len(payload) > max_size:
            raise ValueError(f"El {source_type} supera el tamano maximo permitido.")
