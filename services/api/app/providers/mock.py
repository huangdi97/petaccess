"""Mock providers: deterministic, test-friendly, no network."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from .base import OcrResult, PetSuggestion


class MockVisionProvider:
    """Deterministic pseudo-classification from image bytes hash.

    species: dog | cat (hash-parity); breed candidates are generic.
    Never suggests service dog. Never returns confirmed weight/height.
    """

    _BREEDS = {
        "dog": ["柴犬", "柯基", "金毛寻回犬", "拉布拉多", "中华田园犬"],
        "cat": ["狸花猫", "英国短毛猫", "布偶猫", "橘猫"],
        "other": ["其他动物"],
    }

    def classify_pet(self, image_bytes: bytes) -> PetSuggestion:
        digest = hashlib.sha256(image_bytes or b"empty").hexdigest()
        species = "dog" if int(digest[0], 16) % 2 == 0 else "cat"
        breeds = self._BREEDS[species]
        idx = int(digest[1:3], 16) % len(breeds)
        return PetSuggestion(
            species=species,
            breed_candidates=[breeds[idx], *([b for i, b in enumerate(breeds) if i != idx][:2])],
            confidence=0.42 + (int(digest[3], 16) / 255) * 0.4,
        )


class MockOCRProvider:
    """Returns canned signage text + rule candidates for demo/testing."""

    _CANNED = [
        "本店允许携带宠物进入户外区域，室内谢绝宠物",
        "宠物需全程牵引",
    ]

    def extract_text(self, image_bytes: bytes) -> OcrResult:
        return OcrResult(
            text_blocks=list(self._CANNED),
            rule_candidates=[
                {
                    "zone_hint": "outdoor",
                    "effect": "allowed",
                    "animal_scope": "ordinary_pet",
                    "action": "enter",
                    "conditions": [{"condition_type": "leash_required", "value_flag": True}],
                },
                {
                    "zone_hint": "indoor",
                    "effect": "prohibited",
                    "animal_scope": "ordinary_pet",
                    "action": "enter",
                    "conditions": [],
                },
            ],
        )


class MockNotificationProvider:
    """Captures notifications in memory AND in Redis (cross-process inspectable).

    Redis storage makes worker-executed sends verifiable from the API/tests;
    failures are silent (mock only).
    """

    sent: list[dict] = []

    def send(self, user_id: str, channel: str, title: str, body: str) -> dict:
        item = {
            "user_id": user_id,
            "channel": channel,
            "title": title,
            "body": body,
            "sent_at": datetime.now(UTC).isoformat(),
        }
        type(self).sent.append(item)
        try:
            import redis as _redis

            from app.core.config import get_settings

            r = _redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
            r.rpush("mock:notifications", json.dumps(item, ensure_ascii=False))
            r.expire("mock:notifications", 86400)
        except Exception:
            pass
        return {"status": "sent_mock", "item": item}


class MockMapProvider:
    """Synthetic map data around the demo city center (no key needed)."""

    _SYNTHETIC = [
        {"name": "星河咖啡·测试店", "lat": 31.2304, "lng": 121.4737, "type": "cafe"},
        {"name": "青岚公园·演示", "lat": 31.2380, "lng": 121.4880, "type": "park"},
        {"name": "云栖中心·测试商场", "lat": 31.2240, "lng": 121.4650, "type": "mall"},
        {"name": "松风社区·演示", "lat": 31.2180, "lng": 121.4950, "type": "residential_community"},
    ]

    def search_places(self, keyword: str, lat: float, lng: float, radius_m: int) -> list[dict]:
        results = (
            [p for p in self._SYNTHETIC if keyword in str(p["name"])]
            if keyword
            else list(self._SYNTHETIC)
        )
        return [
            {
                **p,
                "provider": "mock",
                "external_id": f"mock-poi-{i + 1}",
            }
            for i, p in enumerate(results)
        ]

    def reverse_geocode(self, lat: float, lng: float) -> dict:
        return {"address": f"演示市虚构路 {round(lng * 100) % 100} 号", "provider": "mock"}

    def render_config(self) -> dict:
        return {"provider": "mock", "center": {"lat": 31.23, "lng": 121.47}, "zoom": 14}

    def open_navigation(self, lat: float, lng: float, name: str) -> dict:
        return {"action": "mock_navigation", "lat": lat, "lng": lng, "name": name}
