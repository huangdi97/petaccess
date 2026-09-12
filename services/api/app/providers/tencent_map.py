"""Tencent LBS MapProvider adapter (ADR-008, PROVIDER_HARDENING_SPEC).

Implements the capabilities the product actually uses:
- keyword/place search (WebService `ws/place/v1/search`, nearby boundary)
- nearby search
- reverse geocode (`ws/geocoder/v1`)
- render config (never exposes the key)
- navigation deep link (`uri/v1/routeplan`)

Contract:
- timeout + bounded retries on transient failures
- provider error normalization to ProviderError codes
- secret redaction: the key never appears in errors/logs/config
- third-party ids stay in ExternalPlaceRef; no batch persistence without license
  confirmation (caller's responsibility, design #22.2)

Live smoke without a real key is BLOCKED_EXTERNAL (B-04) — this file plus the
fixture contract tests are the deliverable that does not need a key.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

from .base import MapProvider

logger = logging.getLogger(__name__)

_API_ROOT = "https://apis.map.qq.com"

# Tencent WebService status codes (WebService API docs): 0 ok; 110/111 key
# problems; 120/121 quota; 310/306 request/permission; others generic.
_STATUS_AUTH = {110, 111}
_STATUS_QUOTA = {120, 121}
_STATUS_CLIENT = {306, 310, 311, 319}


class ProviderError(Exception):
    """Normalized provider failure. `message` is safe to log (key-redacted)."""

    def __init__(self, code: str, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass(frozen=True)
class RemotePlace:
    name: str
    lat: float
    lng: float
    address: str | None
    provider: str
    external_id: str


class TencentMapProvider(MapProvider):
    provider_name = "tencent"

    def __init__(
        self,
        key: str,
        *,
        timeout_seconds: float = 5.0,
        max_retries: int = 2,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not key:
            raise ValueError("TencentMapProvider requires an API key")
        self._key = key
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._transport = transport

    # ------------------------------------------------------------- internals

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=self._timeout, transport=self._transport)

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        params = {**params, "key": self._key}
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = self._client().get(f"{_API_ROOT}{path}", params=params)
            except httpx.TimeoutException:
                last_error = ProviderError("network_timeout", "map provider timeout")
                logger.warning("tencent_map.timeout path=%s attempt=%d", path, attempt)
                continue
            except httpx.HTTPError:
                last_error = ProviderError("network_error", "map provider unreachable")
                logger.warning("tencent_map.network path=%s attempt=%d", path, attempt)
                continue
            if resp.status_code >= 500:
                last_error = ProviderError(
                    "provider_unavailable", "map provider 5xx", status=resp.status_code
                )
                logger.warning("tencent_map.5xx path=%s status=%d", path, resp.status_code)
                continue
            try:
                payload = resp.json()
            except ValueError as err:
                raise ProviderError(
                    "malformed_response",
                    "map provider returned invalid JSON",
                    status=resp.status_code,
                ) from err
            status = payload.get("status")
            if status == 0:
                return payload
            message = str(payload.get("message", "unknown provider error"))
            if status in _STATUS_AUTH:
                raise ProviderError(
                    "auth_failed", "map provider rejected credentials", status=resp.status_code
                )
            if status in _STATUS_QUOTA:
                raise ProviderError(
                    "quota_exceeded", "map provider quota exhausted", status=resp.status_code
                )
            if status in _STATUS_CLIENT:
                raise ProviderError(
                    "bad_request", "map provider rejected request params", status=resp.status_code
                )
            raise ProviderError("provider_error", message, status=resp.status_code)
        raise last_error or ProviderError("unknown", "map provider failed")

    @staticmethod
    def _place_from_poi(poi: dict[str, Any]) -> RemotePlace:
        loc = poi.get("location") or {}
        return RemotePlace(
            name=str(poi.get("title", "")),
            lat=float(loc.get("lat", 0.0)),
            lng=float(loc.get("lng", 0.0)),
            address=poi.get("address"),
            provider=TencentMapProvider.provider_name,
            external_id=str(poi.get("id", "")),
        )

    # ------------------------------------------------------------ public API

    def search_places(
        self, keyword: str, lat: float, lng: float, radius_m: int
    ) -> list[RemotePlace]:
        if not keyword.strip():
            return []
        boundary = f"nearby({lat},{lng},{max(100, min(int(radius_m), 10000))},1)"
        payload = self._get(
            "/ws/place/v1/search",
            {
                "keyword": keyword,
                "boundary": boundary,
                "page_size": "10",
                "page_index": "1",
                "orderby": "_distance",
            },
        )
        data = payload.get("data") or []
        return [self._place_from_poi(p) for p in data]

    def reverse_geocode(self, lat: float, lng: float) -> dict[str, Any]:
        payload = self._get("/ws/geocoder/v1", {"location": f"{lat},{lng}"})
        result = payload.get("result") or {}
        return {
            "address": result.get("address"),
            "recommended": (result.get("formatted_addresses") or {}).get("recommend"),
            "provider": self.provider_name,
        }

    def render_config(self) -> dict[str, Any]:
        # the key NEVER appears here; client uses its own map component config
        return {"provider": self.provider_name, "key_configured": True}

    def open_navigation(self, lat: float, lng: float, name: str) -> dict[str, Any]:
        uri = (
            f"{_API_ROOT}/uri/v1/routeplan?"
            f"to={quote(name)}&todest={lat},{lng}&mode=walk&policy=0"
            "&referer=petaccess"
        )
        return {"action": "open_url", "url": uri, "provider": self.provider_name}

    def healthy(self) -> bool:
        try:
            self._get("/ws/geocoder/v1", {"location": "39.984154,116.307490"})
            return True
        except ProviderError as e:
            return e.code not in ("network_error", "network_timeout")
