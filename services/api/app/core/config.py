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

    jwt_secret: str = "dev_only_change_me_min_32_bytes_0123456789abcdef"
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

    # Background-job isolation (§41): the queue name doubles as the Redis list
    # key, so a test worker consuming `petaccess_test` cannot pick up a real
    # production task and vice versa.
    celery_task_queue: str = "petaccess"

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


#: Secrets shipped as defaults so `uvicorn app.main:app` works on a laptop.
#: They are a convenience, never a credential — a deployment that still holds
#: them would be signing tokens with a key published in this repository.
DEV_ONLY_DEFAULTS: frozenset[str] = frozenset(
    {
        "dev_only_change_me_min_32_bytes_0123456789abcdef",  # jwt_secret
    }
)

#: Environments where a dev-only default must be refused at startup (§75:
#: a missing configuration should fail loudly, not surface as a KeyError later).
PRODUCTION_ENVS: frozenset[str] = frozenset({"production", "prod", "staging"})


class InsecureDefaultSecret(RuntimeError):
    """Raised at startup when a published dev secret would be used for real."""


def validate_runtime(settings: Settings) -> None:
    """Fail at boot rather than run with a secret anyone can read from GitHub."""
    if settings.app_env.strip().lower() not in PRODUCTION_ENVS:
        return
    offenders = [name for name in ("jwt_secret",) if getattr(settings, name) in DEV_ONLY_DEFAULTS]
    if offenders:
        raise InsecureDefaultSecret(
            "app_env="
            f"{settings.app_env!r} but these secrets still hold their dev defaults: "
            f"{', '.join(offenders)}. Set them in the environment; refusing to start."
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


#: SQLAlchemy spells the driver as ``postgresql+psycopg://``; libpq (and
#: therefore ``psycopg.connect``) rejects that form outright. This is the *only*
#: place that conversion is written down — ``scripts/dev_api_server.py`` and
#: every script delegate to it, because a second copy is a second chance for a
#: driver mismatch to come back as "the server refused to start".
SQLALCHEMY_PSYCOPG_SCHEME = "postgresql+psycopg://"
LIBPQ_SCHEME = "postgresql://"


def psycopg_url(database_url: str | None) -> str | None:
    """Return ``database_url`` in the libpq form psycopg accepts."""
    if not database_url:
        return None
    return database_url.replace(SQLALCHEMY_PSYCOPG_SCHEME, LIBPQ_SCHEME, 1)
