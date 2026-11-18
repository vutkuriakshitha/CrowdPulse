from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_DEFAULT_SQLITE = f"sqlite+aiosqlite:///{(_DATA_DIR / 'crowdpulse.db').as_posix()}"
_UPLOAD_DIR = _DATA_DIR / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CrowdPulse"
    environment: str = "development"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    # Control-room JWT auth (Telangana police / stadium ops). Set false only for local script bypass.
    auth_required: bool = True
    access_token_expire_minutes: int = 480  # 8-hour control-room shift

    database_url: str = _DEFAULT_SQLITE
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "crowdpulse"

    video_upload_dir: str = str(_UPLOAD_DIR.resolve())
    max_upload_bytes: int = 500 * 1024 * 1024

    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    detection_stream_key: str = "cp:detections"
    metrics_channel: str = "cp:metrics"
    alerts_channel: str = "cp:alerts"

    risk_orange_threshold: float = 60.0
    risk_red_threshold: float = 80.0
    forecast_horizons_min: List[int] = [5, 10]

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Detection quality (balanced for laptop CPU — prefer recall over speed)
    demo_frame_stride: int = 4
    demo_max_frames: int = 90
    yolo_model_name: str = "yolov8n.pt"
    yolo_imgsz: int = 640
    yolo_conf: float = 0.22
    yolo_iou: float = 0.45
    warm_models_on_startup: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
