import logging
import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class AlertService:
    """Servicio para enviar alertas a Telegram u otros canales."""
    
    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
    
    async def send_telegram_alert(self, message: str) -> bool:
        """Envia un mensaje de alerta al grupo de Telegram configurado."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot token o chat_id no configurados. Omitiendo alerta.")
            return False
            
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, json=payload, timeout=10.0)
                if response.status_code == 200:
                    logger.info("Alerta de Telegram enviada exitosamente.")
                    return True
                else:
                    logger.error(f"Fallo al enviar alerta de Telegram: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error de red al enviar alerta de Telegram: {str(e)}")
            return False

# Instancia singleton para ser usada por los routers/background tasks
alert_service = AlertService()
