from fastapi import FastAPI

from app.core.config import get_settings
from app.routes.api import api_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para procesar frames y videos con un pipeline de landmarks y clasificacion.",
)
app.include_router(api_router, prefix=settings.api_prefix)


def run() -> None:
    """Ejecuta la aplicacion en modo desarrollo usando Uvicorn."""

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        ssl_certfile=settings.ssl_certfile if settings.ssl_enabled else None,
        ssl_keyfile=settings.ssl_keyfile if settings.ssl_enabled else None,
    )


if __name__ == "__main__":
    run()
