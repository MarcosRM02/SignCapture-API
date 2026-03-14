from fastapi import HTTPException, UploadFile, status

from app.services.inference import InferenceService
from app.views.inference_view import build_inference_response


class InferenceController:
    """Adapta los casos de uso de inferencia al contexto HTTP."""

    def __init__(self, service: InferenceService) -> None:
        """Inicializa el controlador con su servicio asociado."""

        self._service = service

    async def infer_frame(self, file: UploadFile) -> dict:
        """Gestiona una peticion de inferencia sobre un frame."""

        try:
            result = await self._service.process_frame(file)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        return build_inference_response(result)

    async def infer_video(self, file: UploadFile) -> dict:
        """Gestiona una peticion de inferencia sobre un video completo."""

        try:
            result = await self._service.process_video(file)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        return build_inference_response(result)
