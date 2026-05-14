import asyncio
import logging
import psutil
import httpx
from datetime import datetime

from app.core.config import get_settings
from app.services.alert_service import alert_service

logger = logging.getLogger(__name__)
settings = get_settings()

# Variables de estado para no enviar alertas repetidas continuamente
_cpu_alert_sent = False
_ram_alert_sent = False

async def check_system_metrics() -> None:
    """Monitoriza CPU y RAM periódicamente y envía alertas si exceden el límite."""
    global _cpu_alert_sent, _ram_alert_sent
    
    # Limites (ejemplo: 85%)
    CPU_THRESHOLD = 85.0
    RAM_THRESHOLD = 85.0
    
    while True:
        try:
            # Psutil necesita un intervalo para medir CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            
            # Chequeo CPU
            if cpu_percent > CPU_THRESHOLD:
                if not _cpu_alert_sent:
                    msg = f"⚠️ <b>ALERTA OPERATIVA (CPU)</b>\nEl uso de CPU del contenedor ha alcanzado el <b>{cpu_percent}%</b>. Posible sobrecarga de peticiones o bucle infinito."
                    await alert_service.send_telegram_alert(msg)
                    _cpu_alert_sent = True
            else:
                _cpu_alert_sent = False # Reset si baja
                
            # Chequeo RAM
            if ram_percent > RAM_THRESHOLD:
                if not _ram_alert_sent:
                    msg = f"⚠️ <b>ALERTA OPERATIVA (RAM)</b>\nEl uso de RAM del contenedor ha alcanzado el <b>{ram_percent}%</b>. Riesgo inminente de OOM Kill."
                    await alert_service.send_telegram_alert(msg)
                    _ram_alert_sent = True
            else:
                _ram_alert_sent = False
                
        except Exception as e:
            logger.error(f"Error monitorizando métricas: {e}")
            
        # Esperar 30 segundos antes del próximo chequeo
        await asyncio.sleep(30)


async def auto_ping_keep_alive() -> None:
    """Envía un ping periódico al endpoint público para evitar la suspensión en Render."""
    
    public_url = settings.public_url.rstrip("/")
    if "localhost" in public_url or "127.0.0.1" in public_url:
        logger.info("Auto-ping deshabilitado en entorno local.")
        return
        
    health_endpoint = f"{public_url}{settings.api_prefix}/health"
    
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(health_endpoint, timeout=10.0)
                if response.status_code == 200:
                    logger.debug(f"Auto-ping exitoso a {health_endpoint}")
                else:
                    logger.warning(f"Auto-ping recibió status {response.status_code}")
        except Exception as e:
            logger.error(f"Fallo en Auto-ping a {health_endpoint}: {e}")
            
        # Esperar 5 minutos (300 segundos) para el próximo ping
        await asyncio.sleep(300)


def start_observability_tasks() -> None:
    """Lanza las tareas en segundo plano (fire and forget)."""
    if settings.enable_observability:
        logger.info("Iniciando tareas de observabilidad y keep-alive...")
        asyncio.create_task(check_system_metrics())
        asyncio.create_task(auto_ping_keep_alive())
