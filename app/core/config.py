from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion central de la aplicacion.

    Agrupa parametros de despliegue y limites operativos usados por el
    pipeline de inferencia.
    """

    app_name: str = "SignCapture API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    host: str = "127.0.0.1"
    port: int = 8000
    ssl_enabled: bool = False
    ssl_certfile: str | None = None
    ssl_keyfile: str | None = None
    cors_allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    max_video_frames: int = Field(default=300, ge=1)
    max_frame_bytes: int = Field(default=5_000_000, ge=1)
    max_video_bytes: int = Field(default=100_000_000, ge=1)

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SIGNCAPTURE_")


@lru_cache
def get_settings() -> Settings:
    """Devuelve una configuracion cacheada para todo el proceso."""

    return Settings()
