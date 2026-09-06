"""Application settings loaded from environment (.env at repo root)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "pet-access-map"
    api_base_url: str = "http://localhost:8000"

    database_url: str = "postgresql+psycopg://petaccess:petaccess_dev_only@localhost:5432/petaccess"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minio"
    s3_secret_key: str = "minio_dev_only"
    s3_bucket: str = "petaccess-dev"
    s3_region: str = "us-east-1"
    s3_secure: bool = False

    jwt_secret: str = "CHANGE_ME_FOR_ANY_NONLOCAL_USE"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60
    refresh_token_ttl_days: int = 30

    map_provider: str = "mock"
    tencent_map_key_client: str = ""
    tencent_map_key_server: str = ""

    ai_provider: str = "mock"
    vision_provider: str = "mock"
    ocr_provider: str = "mock"
    ai_api_key: str = ""

    notification_provider: str = "mock"

    feature_real_map: bool = False
    feature_real_ai: bool = False
    feature_operator_claim: bool = True
    feature_dispute: bool = True
    feature_watch: bool = True

    # Anti-abuse: per-user rate limits (window seconds -> max ops)
    contribution_rate_window_seconds: int = 3600
    contribution_rate_max: int = 20
    observation_rate_window_seconds: int = 3600
    observation_rate_max: int = 30

    # Image retention: signage evidence kept under controlled retention;
    # scene photos use short TTL (privacy gate default, see docs #20).
    signage_retention_days: int = 365
    scene_photo_ttl_hours: int = 72


@lru_cache
def get_settings() -> Settings:
    return Settings()
