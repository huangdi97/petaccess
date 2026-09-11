"""Idempotency-Key support for high-risk writes (design #27).

Stores the serialized response of the first successful execution in Redis for
24h; replayed requests with the same key receive the same response.
"""

import hashlib
import json
from contextlib import suppress
from typing import cast

import redis

from app.core.config import get_settings
from app.core.errors import Conflict

TTL_SECONDS = 24 * 3600
_client: redis.Redis | None = None


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            get_settings().redis_url, decode_responses=True, socket_connect_timeout=2
        )
    return _client


def _key(scope: str, idem_key: str) -> str:
    digest = hashlib.sha256(idem_key.encode()).hexdigest()[:32]
    return f"idem:{scope}:{digest}"


def get_cached(scope: str, idem_key: str) -> dict | None:
    if not idem_key:
        return None
    try:
        raw = cast("str | None", _redis().get(_key(scope, idem_key)))
    except redis.RedisError:
        return None
    return json.loads(raw) if raw else None


def store(scope: str, idem_key: str, response_body: dict) -> None:
    if not idem_key:
        return
    with suppress(redis.RedisError):
        _redis().set(_key(scope, idem_key), json.dumps(response_body), ex=TTL_SECONDS)


def check_inflight(scope: str, idem_key: str) -> None:
    """Simple in-flight reservation to avoid duplicate concurrent execution."""
    if not idem_key:
        return
    r = _redis()
    try:
        if not r.set(_key(scope, idem_key) + ":inflight", "1", nx=True, ex=60):
            raise Conflict("相同幂等键的请求正在处理中")
    except redis.RedisError:
        return
