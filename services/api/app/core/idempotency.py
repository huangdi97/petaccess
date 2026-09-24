"""Idempotency-Key support for high-risk writes (design #27).

Stores the serialized response of the first successful execution in Redis for
24h; replayed requests with the same key receive the same response.
"""

import hashlib
import json
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
    except redis.RedisError as exc:
        # Fail-open: idempotency is a safety net, never a hard dependency. A
        # Redis outage must not turn an otherwise valid request into a 500 or
        # (worse) a silently re-executed write that looks idempotent — the
        # caller just proceeds and stores nothing.
        import logging

        logging.getLogger("petaccess.idempotency").debug(
            "idempotency cache read failed (non-fatal, fail-open): %s", exc
        )
        return None
    return json.loads(raw) if raw else None


def store(scope: str, idem_key: str, response_body: dict) -> None:
    if not idem_key:
        return
    try:
        _redis().set(_key(scope, idem_key), json.dumps(response_body), ex=TTL_SECONDS)
    except redis.RedisError as exc:
        # Fail-open: losing the stored replay must not fail the write that just
        # succeeded. Idempotency degrades to "no cache" during the outage; the
        # caller never sees a 500 from the bookkeeping step itself.
        import logging

        logging.getLogger("petaccess.idempotency").debug(
            "idempotency store failed (non-fatal, fail-open): %s", exc
        )


def check_inflight(scope: str, idem_key: str) -> None:
    """Simple in-flight reservation to avoid duplicate concurrent execution."""
    if not idem_key:
        return
    r = _redis()
    try:
        if not r.set(_key(scope, idem_key) + ":inflight", "1", nx=True, ex=60):
            raise Conflict("相同幂等键的请求正在处理中")
    except redis.RedisError as exc:
        # Fail-open: the in-flight guard is best-effort; losing it must not
        # reject a request when Redis is down. Idempotency still holds for the
        # stored-response path; this only weakens duplicate-concurrency
        # prevention during the outage.
        import logging

        logging.getLogger("petaccess.idempotency").debug(
            "in-flight reservation failed (non-fatal, fail-open): %s", exc
        )
        return
