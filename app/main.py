from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routes.api import api_router
from app.core.observability import start_observability_tasks

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Iniciar tareas en segundo plano (Auto-ping y Métricas de Sistema)
    start_observability_tasks()
    yield
    # Limpieza (si fuera necesario)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para procesar frames y videos con un pipeline de landmarks y clasificacion.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
