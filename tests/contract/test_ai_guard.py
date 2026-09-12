"""AiGuard fixture contract tests (PROVIDER_HARDENING_SPEC / A3)."""

import pytest

from app.providers.ai_guard import AiGuard, AiProviderError, redact


def test_success_passthrough_with_telemetry():
    events = []
    guard = AiGuard(telemetry=lambda e, f: events.append((e, f)))
    result = guard.call("mock", "op", lambda: {"ok": True})
    assert result == {"ok": True}
    assert events and events[-1][0] == "success"


def test_timeout_normalized():
    guard = AiGuard(timeout_seconds=0.2, max_retries=0)

    def slow():
        import time

        time.sleep(2)

    with pytest.raises(AiProviderError) as ei:
        guard.call("mock", "slow", slow)
    assert ei.value.code == "timeout"


def test_arbitrary_exception_normalized_and_redacted():
    events = []
    guard = AiGuard(max_retries=0, telemetry=lambda e, f: events.append((e, f)))

    def boom():
        raise RuntimeError("remote said api_key=SECRET1234 blew up")

    with pytest.raises(AiProviderError) as ei:
        guard.call("vendor", "op", boom)
    assert ei.value.code == "provider_failure"
    # raw exception message must not reach telemetry
    flat = str(events)
    assert "SECRET1234" not in flat
    assert "[REDACTED]" in flat


def test_retry_then_success():
    calls = {"n": 0}
    guard = AiGuard(max_retries=1)

    def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("transient")
        return "done"

    assert guard.call("mock", "flaky", flaky) == "done"
    assert calls["n"] == 2


def test_exhausted_retries_raise_normalized():
    guard = AiGuard(max_retries=1)
    with pytest.raises(AiProviderError) as ei:
        guard.call("mock", "always", lambda: (_ for _ in ()).throw(ValueError("x")))
    assert ei.value.code == "provider_failure"


def test_redact_patterns():
    text = "call failed for sk-abcd12345678 with api_key=zzz and token: qqq"
    out = redact(text)
    assert "sk-abcd12345678" not in out
    assert "zzz" not in out
    assert "qqq" not in out
    assert "[REDACTED]" in out


def test_mock_providers_satisfy_protocols():
    from app.providers.base import (
        NaturalLanguageQueryProvider,
        OCRProvider,
        VisionProvider,
    )
    from app.providers.mock import MockNLQueryProvider, MockOCRProvider, MockVisionProvider

    assert isinstance(MockVisionProvider(), VisionProvider)
    assert isinstance(MockOCRProvider(), OCRProvider)
    assert isinstance(MockNLQueryProvider(), NaturalLanguageQueryProvider)
    parsed = MockNLQueryProvider().parse_query("周六晚上带 9kg 柴犬去商场吃饭")
    assert parsed["animal"]["species"] == "dog"
    assert parsed["animal"]["weight_kg"] == 9.0
