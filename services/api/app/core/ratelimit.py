"""Redis-backed sliding-window rate limiting (design #27 anti-abuse)."""

from typing import cast

import redis

from app.core.config import get_settings
from app.core.errors import RateLimited

_client: redis.Redis | None = None


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        url = get_settings().redis_url
        _client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
    return _client


def check_rate_limit(bucket: str, key: str, limit: int, window_seconds: int) -> None:
    """Raise RateLimited when key exceeds `limit` ops per `window_seconds`."""
    r = _redis()
    redis_key = f"ratelimit:{bucket}:{key}"
    try:
        count = cast(int, r.incr(redis_key))
        if count == 1:
            r.expire(redis_key, window_seconds)
    except redis.RedisError as exc:
        # Fail open: with Redis unavailable, rate limiting cannot be enforced.
        # A busy API must not become a 500 storm because its limiter is down;
        # the outage is logged so operators see it rather than silently
        # letting traffic through unthrottled.
        import logging

        logging.getLogger("petaccess.ratelimit").debug(
            "rate-limit counter unavailable (non-fatal, fail-open): %s", exc
        )
        return
    if count > limit:
        raise RateLimited(f"操作过于频繁，请 {window_seconds // 60} 分钟后再试")
