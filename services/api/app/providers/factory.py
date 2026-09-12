"""Provider factory: mock first; real adapters only when env enables them."""

from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import get_settings

from .base import MapProvider, NotificationProvider, OCRProvider, VisionProvider
from .mock import MockMapProvider, MockNotificationProvider, MockOCRProvider, MockVisionProvider

if TYPE_CHECKING:
    from .storage import StorageProvider


@lru_cache
def get_vision_provider() -> VisionProvider:
    settings = get_settings()
    if settings.feature_real_ai and settings.vision_provider != "mock" and settings.ai_api_key:
        # Real adapter lands with provider credentials; see BLOCKERS.md
        raise RuntimeError(
            f"vision provider '{settings.vision_provider}' 需要实现真实 adapter（当前仅 mock）"
        )
    return MockVisionProvider()


@lru_cache
def get_ocr_provider() -> OCRProvider:
    settings = get_settings()
    if settings.feature_real_ai and settings.ocr_provider != "mock" and settings.ai_api_key:
        raise RuntimeError(
            f"ocr provider '{settings.ocr_provider}' 需要实现真实 adapter（当前仅 mock）"
        )
    return MockOCRProvider()


@lru_cache
def get_notification_provider() -> NotificationProvider:
    settings = get_settings()
    if settings.notification_provider != "mock":
        raise RuntimeError("notification provider 需要真实 adapter（当前仅 mock）")
    return MockNotificationProvider()


@lru_cache
def get_map_provider() -> MapProvider:
    settings = get_settings()
    if settings.map_provider == "tencent" or (
        settings.feature_real_map and settings.tencent_map_key_server
    ):
        key = settings.tencent_map_key_server or settings.tencent_map_key_client
        if not key:
            raise RuntimeError("腾讯地图 Key 未配置（TENCENT_MAP_KEY_*），保持 mock")
        from .tencent_map import TencentMapProvider

        return TencentMapProvider(key)
    return MockMapProvider()


@lru_cache
def get_storage_provider() -> "StorageProvider":
    """MinIO when S3 endpoint is configured; NullStorage for pure unit tests."""
    from .storage import MinioStorageProvider, NullStorageProvider

    settings = get_settings()
    if settings.s3_endpoint:
        return MinioStorageProvider()
    return NullStorageProvider()
