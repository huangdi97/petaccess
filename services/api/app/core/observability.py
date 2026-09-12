"""Lightweight observability: metrics registry, request context, worker
failure visibility (NEXT_GOAL §A5). No heavyweight deps."""

from __future__ import annotations

import contextvars
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import cast

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


@dataclass
class MetricsRegistry:
    """Thread-safe in-process counters + latency rolling stats."""

    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _latencies: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    _lock: threading.Lock = field(default_factory=threading.Lock)
    MAX_LATENCY_SAMPLES = 500

    def incr(self, name: str, by: int = 1) -> None:
        with self._lock:
            self.counters[name] += by

    def observe_latency(self, name: str, seconds: float) -> None:
        with self._lock:
            series = self._latencies[name]
            series.append(seconds)
            if len(series) > self.MAX_LATENCY_SAMPLES:
                del series[: len(series) - self.MAX_LATENCY_SAMPLES]

    def snapshot(self) -> dict:
        with self._lock:
            latencies = {
                name: {
                    "count": len(series),
                    "p50_ms": int(sorted(series)[len(series) // 2] * 1000),
                    "p95_ms": int(sorted(series)[int(len(series) * 0.95)] * 1000),
                }
                for name, series in self._latencies.items()
                if series
            }
            return {"counters": dict(self.counters), "latency_ms": latencies}


metrics = MetricsRegistry()


def timed(metric_prefix: str):
    """Decorator for request handlers / provider calls."""

    def wrapper(fn):
        def inner(*args, **kwargs):
            start = time.monotonic()
            try:
                return fn(*args, **kwargs)
            finally:
                metrics.observe_latency(metric_prefix, time.monotonic() - start)
                metrics.incr(f"{metric_prefix}.calls")

        return inner

    return wrapper


FAILED_JOBS_KEY = "worker:failed_jobs"
MAX_FAILED_JOBS_KEPT = 200


def record_failed_job(task_name: str, task_id: str, error: str) -> None:
    """Push a failed Celery task to Redis for admin visibility (best-effort)."""
    import json
    from datetime import UTC, datetime

    try:
        import redis as _redis

        from app.core.config import get_settings

        r = _redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
        entry = json.dumps(
            {
                "task": task_name,
                "id": task_id,
                "error": error[:300],
                "failed_at": datetime.now(UTC).isoformat(),
            },
            ensure_ascii=False,
        )
        r.lpush(FAILED_JOBS_KEY, entry)
        r.ltrim(FAILED_JOBS_KEY, 0, MAX_FAILED_JOBS_KEPT - 1)
    except Exception:
        pass


def list_failed_jobs(limit: int = 50) -> list[dict]:
    import json

    try:
        import redis as _redis

        from app.core.config import get_settings

        r = _redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
        rows = cast("list[str]", r.lrange(FAILED_JOBS_KEY, 0, max(0, limit - 1)))
        return [json.loads(x) for x in rows]
    except Exception:
        return []
