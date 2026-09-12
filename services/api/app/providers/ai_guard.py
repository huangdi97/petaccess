"""AI provider call guard (PROVIDER_HARDENING_SPEC).

Uniform wrapper around every AI provider call:
- timeout via worker thread (providers are sync callables)
- bounded retry for transient failures
- error normalization to AiProviderError (never leaks provider internals)
- telemetry: structured log with latency; secret redaction on every message
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import Any

logger = logging.getLogger(__name__)

# patterns that must never reach logs
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{8,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)[=:]\s*\S+"),
]


def redact(text: str) -> str:
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


class AiProviderError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class AiGuard:
    """Callable guard shared by /ai endpoints and worker AI tasks."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 8.0,
        max_retries: int = 1,
        telemetry: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._telemetry = telemetry or self._default_telemetry
        self._pool = ThreadPoolExecutor(max_workers=4)

    @staticmethod
    def _default_telemetry(event: str, fields: dict[str, Any]) -> None:
        logger.info("ai_guard.%s %s", event, redact(str(fields)))

    def call(self, provider_name: str, operation: str, fn: Callable[[], Any]) -> Any:
        last: Exception | None = None
        for attempt in range(self._max_retries + 1):
            start = time.monotonic()
            future = self._pool.submit(fn)
            try:
                result = future.result(timeout=self._timeout)
            except FutureTimeout:
                future.cancel()
                last = AiProviderError("timeout", f"{provider_name}.{operation} timed out")
                self._telemetry(
                    "timeout",
                    {"provider": provider_name, "operation": operation, "attempt": attempt},
                )
                continue
            except AiProviderError:
                raise
            except Exception as exc:  # normalize anything a provider raises
                last = AiProviderError("provider_failure", f"{provider_name}.{operation} failed")
                self._telemetry(
                    "error",
                    {
                        "provider": provider_name,
                        "operation": operation,
                        "attempt": attempt,
                        "detail": redact(str(exc))[:200],
                    },
                )
                continue
            self._telemetry(
                "success",
                {
                    "provider": provider_name,
                    "operation": operation,
                    "latency_ms": int((time.monotonic() - start) * 1000),
                },
            )
            return result
        raise last or AiProviderError("unknown", "AI provider failed")
