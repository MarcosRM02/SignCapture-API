from fastapi import APIRouter, Depends, File, UploadFile, status

from app.dependencies import get_inference_controller

router = APIRouter()


@router.post("/frame", status_code=status.HTTP_200_OK)
async def infer_frame(
    file: UploadFile = File(...),
    controller=Depends(get_inference_controller),
) -> dict:
    """Expone la inferencia de un frame individual."""

    return await controller.infer_frame(file)


@router.post("/video", status_code=status.HTTP_200_OK)
async def infer_video(
    file: UploadFile = File(...),
    controller=Depends(get_inference_controller),
) -> dict:
    """Expone la inferencia de un video completo."""

    return await controller.infer_video(file)
