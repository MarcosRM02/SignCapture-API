from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "xgboost_asl.pkl"
DEFAULT_MODEL_CLASS_LABELS = "A,B,C,D,E,F,G,H,I,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y"


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
        "*",
    ]
    max_video_frames: int = Field(default=300, ge=1)
    max_frame_bytes: int = Field(default=5_000_000, ge=1)
    max_video_bytes: int = Field(default=100_000_000, ge=1)
    model_path: Path = DEFAULT_MODEL_PATH
    model_top_k: int = Field(default=3, ge=1, le=10)
    prediction_warning_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    prediction_success_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    model_class_labels_csv: str = DEFAULT_MODEL_CLASS_LABELS
    
    # Observability & Alerts settings
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    public_url: str = "https://signcapture-api.onrender.com"
    enable_observability: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SIGNCAPTURE_")

    def get_model_class_labels(self) -> list[str]:
        """Devuelve las etiquetas configuradas para resolver las clases del modelo."""

        return [
            label.strip().upper()
            for label in self.model_class_labels_csv.split(",")
            if label.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Devuelve una configuracion cacheada para todo el proceso."""

    return Settings()
