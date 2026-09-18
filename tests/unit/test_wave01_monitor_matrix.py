"""WAVE_01 §79 monitor test matrix.

Every case below is driven by a local fake HTTP client, never a real third-party
page: a test that fetches the internet is a test that fails for reasons that have
nothing to do with the code under test, and §79 explicitly forbids tampering
with third-party pages to provoke a change.

The matrix covers what a monitor fleet actually has to get right:

* unchanged / 304 / content-hash-changed — the three outcomes that decide
  whether evidence is produced at all;
* conditional GET headers — the mechanism that keeps the fleet a good citizen;
* timeout / 403 / 404 / 429 / 500 — all of which are *failures*, and none of
  which may be mistaken for "the source said something new";
* failure threshold → degraded, and the rule that a failure never destroys
  evidence already captured.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from app.services import source_monitor as sm

BODY_V1 = b"<html>park policy v1: dogs on leash</html>"
BODY_V2 = b"<html>park policy v2: dogs prohibited</html>"


# --------------------------------------------------------------------- fixtures


class _Resp:
    def __init__(self, status: int, headers: dict[str, str], body: bytes) -> None:
        self.status_code = status
        self.headers = headers
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_bytes(self, chunk_size: int):
        yield self._body


class _Client:
    """Stands in for ``httpx.Client``; records the outgoing headers."""

    def __init__(self, resp: _Resp, sink: list[dict[str, str]]) -> None:
        self._resp = resp
        self._sink = sink

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def stream(self, method, url, headers=None):  # noqa: ANN001
        self._sink.append(dict(headers or {}))
        return self._resp


def _patch(monkeypatch, *, status=200, headers=None, body=BODY_V1, raise_exc=None):
    """Install a fake transport; returns the list that captures sent headers."""
    sent: list[dict[str, str]] = []

    def factory(**kwargs):
        if raise_exc is not None:
            raise raise_exc
        return _Client(_Resp(status, dict(headers or {}), body), sent)

    monkeypatch.setattr(httpx, "Client", factory)
    # SSRF guard is exercised for real in test_source_monitor_ssrf_guard; here
    # the fake transport never opens a socket, so a real DNS lookup would only
    # make the suite depend on the network.
    monkeypatch.setattr(sm, "_assert_public_host", lambda host: None)
    return sent


def _monitor(**over: Any):
    base = dict(
        url="https://example.com/policy",
        monitor_type="url_hash",
        schedule_minutes=1440,
        status="active",
        failure_count=0,
        content_hash=None,
        etag=None,
        last_modified=None,
        last_excerpt=None,
        last_http_status=None,
        last_latency_ms=None,
        last_checked_at=None,
        last_changed_at=None,
        next_check_at=None,
        source_id="src-1",
        place_id="place-1",
        expansion_run_id="EXP-R1-W01-20260918",
    )
    base.update(over)
    return SimpleNamespace(**base)


def _html_headers(body: bytes) -> dict[str, str]:
    return {"content-type": "text/html"}


# ------------------------------------------------------------------ §79 outcomes


def test_unchanged_when_content_identical(monkeypatch):
    sent = _patch(monkeypatch, headers=_html_headers(BODY_V1))
    m = _monitor()
    first = sm.check_monitor(m)
    assert first.outcome == "unchanged"  # baseline: nothing to compare yet
    baseline = m.content_hash
    assert baseline == hashlib.sha256(BODY_V1).hexdigest()

    second = sm.check_monitor(m)
    assert second.outcome == "unchanged"
    assert m.content_hash == baseline
    assert m.last_changed_at is None
    assert m.failure_count == 0
    assert sent, "conditional GET must actually issue a request"


def test_304_not_modified_is_unchanged_and_keeps_validators(monkeypatch):
    _patch(
        monkeypatch,
        status=304,
        headers={"etag": 'W/"v1"', "last-modified": "Mon, 01 Jan 2026 00:00:00 GMT"},
    )
    m = _monitor(content_hash="abc", etag='W/"v1"', last_modified="Mon, 01 Jan 2026 00:00:00 GMT")
    out = sm.check_monitor(m)
    assert out.outcome == "unchanged"
    # The validators are what earns the *next* 304; dropping them on a 304
    # response would silently turn every subsequent sweep into a full download.
    assert m.etag is not None
    assert m.last_modified is not None
    assert m.content_hash == "abc"
    assert m.failure_count == 0


def test_conditional_get_sends_etag_and_last_modified(monkeypatch):
    sent = _patch(monkeypatch, status=304, headers={"etag": 'W/"v1"'})
    m = _monitor(etag='W/"v1"', last_modified="Mon, 01 Jan 2026 00:00:00 GMT")
    sm.check_monitor(m)
    headers = sent[0]
    assert headers.get("if-none-match") == 'W/"v1"'
    assert headers.get("if-modified-since") == "Mon, 01 Jan 2026 00:00:00 GMT"


def test_content_hash_change_is_detected(monkeypatch):
    _patch(monkeypatch, headers=_html_headers(BODY_V1))
    m = _monitor()
    sm.check_monitor(m)
    baseline = m.content_hash

    _patch(monkeypatch, headers=_html_headers(BODY_V2), body=BODY_V2)
    out = sm.check_monitor(m)
    assert out.outcome == "changed"
    assert out.previous_hash == baseline
    assert m.content_hash == hashlib.sha256(BODY_V2).hexdigest()
    assert m.last_changed_at is not None
    assert m.last_excerpt


@pytest.mark.parametrize("status", [403, 404, 500])
def test_http_errors_are_failures_not_changes(monkeypatch, status):
    _patch(monkeypatch, status=status, headers={"content-type": "text/html"})
    m = _monitor(content_hash="previously-captured")
    out = sm.check_monitor(m)
    assert out.outcome == "failed"
    assert m.failure_count == 1
    assert m.last_http_status == status
    # An unreachable source is not a source that said something new.
    assert m.content_hash == "previously-captured"
    assert m.last_changed_at is None


def test_timeout_is_a_failure(monkeypatch):
    _patch(monkeypatch, raise_exc=httpx.ReadTimeout("too slow"))
    m = _monitor()
    assert sm.check_monitor(m).outcome == "failed"
    assert m.failure_count == 1
    assert m.last_checked_at is not None


def test_429_honours_retry_after(monkeypatch):
    _patch(
        monkeypatch,
        status=429,
        headers={"content-type": "text/html", "retry-after": "120"},
    )
    m = _monitor()
    sm.check_monitor(m)
    assert m.failure_count == 1
    delta = (m.next_check_at - m.last_checked_at).total_seconds()
    assert delta == pytest.approx(120, abs=2)


def test_429_without_retry_after_falls_back_to_exponential_backoff(monkeypatch):
    """No Retry-After → exponential backoff, which is still ceiling-capped.

    Note the consequence for a daily monitor: ``MAX_BACKOFF_MINUTES`` (24h) is an
    absolute ceiling, so a 1440-minute schedule backs off to the ceiling rather
    than doubling past it. That is deliberate — the ceiling exists so a source
    that is down for a week is not polled at minute granularity forever.
    """
    _patch(monkeypatch, status=429, headers={"content-type": "text/html"})
    m = _monitor()
    sm.check_monitor(m)
    delta_minutes = (m.next_check_at - m.last_checked_at).total_seconds() / 60
    expected = min(m.schedule_minutes * 2, sm.MAX_BACKOFF_MINUTES)
    assert delta_minutes == pytest.approx(expected, rel=0.01)


def test_retry_after_is_capped(monkeypatch):
    _patch(
        monkeypatch,
        status=429,
        headers={"content-type": "text/html", "retry-after": "99999999"},
    )
    m = _monitor()
    sm.check_monitor(m)
    delta = (m.next_check_at - m.last_checked_at).total_seconds()
    assert delta <= sm.MAX_BACKOFF_MINUTES * 60


def test_failure_threshold_marks_degraded(monkeypatch):
    _patch(monkeypatch, status=500, headers={"content-type": "text/html"})
    m = _monitor()
    for _ in range(sm.FAILURE_THRESHOLD):
        sm.check_monitor(m)
    assert m.failure_count == sm.FAILURE_THRESHOLD
    assert m.status == sm.DEGRADED_STATUS


def test_recovery_resets_failure_count_and_status(monkeypatch):
    _patch(monkeypatch, status=500, headers={"content-type": "text/html"})
    m = _monitor()
    sm.check_monitor(m)
    assert m.failure_count == 1

    _patch(monkeypatch, headers=_html_headers(BODY_V1))
    sm.check_monitor(m)
    assert m.failure_count == 0
    assert m.status == "active"
    assert m.next_check_at > m.last_checked_at


def test_baseline_sweep_records_hash_without_reporting_change(monkeypatch):
    """A first-ever sweep has no previous hash; that is a baseline, not a change.

    Reporting it as a change would manufacture a candidate for content that has
    been on the page since before we started watching.
    """
    _patch(monkeypatch, headers=_html_headers(BODY_V1))
    m = _monitor(content_hash=None)
    out = sm.check_monitor(m)
    assert out.outcome == "unchanged"
    assert m.content_hash is not None


def test_payload_over_cap_is_rejected(monkeypatch):
    big = b"x" * (sm.MAX_BYTES + 10)
    _patch(monkeypatch, headers=_html_headers(big), body=big)
    m = _monitor()
    assert sm.check_monitor(m).outcome == "failed"
    assert m.failure_count == 1
