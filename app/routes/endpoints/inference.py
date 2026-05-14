from fastapi import APIRouter, Depends, File, UploadFile, status, BackgroundTasks
from pydantic import BaseModel

from app.dependencies import get_inference_controller
from app.services.alert_service import alert_service

router = APIRouter()

# Variables para métricas de modelo simples (Feedback)
_negative_feedback_count = 0
FEEDBACK_ALERT_THRESHOLD = 5

class FeedbackRequest(BaseModel):
    is_correct: bool


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


@router.post("/feedback", status_code=status.HTTP_200_OK)
async def submit_feedback(
    feedback: FeedbackRequest,
    background_tasks: BackgroundTasks
) -> dict:
    """Recibe feedback del usuario y emite alerta si hay deriva detectada."""
    global _negative_feedback_count
    
    if not feedback.is_correct:
        _negative_feedback_count += 1
        
        if _negative_feedback_count >= FEEDBACK_ALERT_THRESHOLD:
            msg = f"📉 <b>ALERTA DE MODELO (Deriva Detectada)</b>\nSe han registrado <b>{_negative_feedback_count} fallos consecutivos/recientes</b> en las predicciones. Es necesario revisar el modelo o reentrenar."
            background_tasks.add_task(alert_service.send_telegram_alert, msg)
            _negative_feedback_count = 0 # Reset después de alertar
    else:
        # Si hay un acierto, bajamos el contador (o lo reiniciamos)
        _negative_feedback_count = max(0, _negative_feedback_count - 1)
        
    return {"status": "Feedback registrado exitosamente"}
