"""SourceMonitor fetcher with SSRF protection (NEXT_GOAL §B5, §9).

Guards:
- only http/https
- DNS resolution checked against private/loopback/link-local ranges
- response size cap (2 MB), timeout, content-type allowlist (text/html|plain)
- redirect-safe: manual redirect handling, each hop re-validated

change → diff artifact → RuleCandidate; never direct rule mutation.
"""

from __future__ import annotations

import hashlib
import ipaddress
import socket
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import httpx

MAX_BYTES = 2 * 1024 * 1024
ALLOWED_CONTENT_TYPES = ("text/html", "text/plain", "application/json")
ALLOWED_SCHEMES = ("http", "https")

#: consecutive failures before a monitor is reported as degraded. Reaching the
#: threshold NEVER withdraws a rule and NEVER deletes evidence — the whole point
#: of evidence is that it survives the source going away.
FAILURE_THRESHOLD = 3
#: exponential backoff ceiling, so a hostile 429 does not turn into a hammering
MAX_BACKOFF_MINUTES = 24 * 60

#: status used for a monitor that has crossed FAILURE_THRESHOLD. The Wave 01
#: brief names this MONITOR_DEGRADED; 'failing' is the pre-existing equivalent
#: in this codebase and is kept so no existing reader breaks.
DEGRADED_STATUS = "failing"


class MonitorFetchError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class FetchResult:
    ok: bool
    content_hash: str | None
    etag: str | None
    last_modified: str | None
    body_excerpt: str | None
    error_code: str | None
    #: HTTP status of the response, including 304. A monitor that silently
    #: starts receiving 403 is otherwise indistinguishable from an unchanged
    #: page: content_hash simply never moves.
    http_status: int | None = None
    #: wall-clock milliseconds of the sweep, so rate limiting can be tuned with
    #: data instead of guesswork
    latency_ms: int | None = None
    #: seconds the server asked us to wait (429/503 ``Retry-After``). Honouring
    #: it is the difference between backing off and hammering (§33): an
    #: exponential guess that is shorter than the server's own window keeps
    #: earning 429s, and a 429 we caused is indistinguishable from a source that
    #: went away.
    retry_after_seconds: int | None = None


def _parse_retry_after(value: str | None) -> int | None:
    """Parse a ``Retry-After`` header, either delta-seconds or HTTP-date.

    A malformed header must not become a crash inside the sweep — falling back
    to ``None`` simply means "use the normal exponential backoff".
    """
    if not value:
        return None
    raw = value.strip()
    if raw.isdigit():
        return int(raw)
    try:
        from email.utils import parsedate_to_datetime

        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    delta = (when - datetime.now(UTC)).total_seconds()
    return max(0, int(delta))


def _assert_public_host(host: str) -> None:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as err:
        raise MonitorFetchError("dns_failure", "cannot resolve host") from err
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise MonitorFetchError(
                "private_network_blocked", "refusing to fetch private network address"
            )


def fetch_url_safely(
    url: str,
    *,
    timeout_seconds: float = 5.0,
    etag: str | None = None,
    last_modified: str | None = None,
) -> FetchResult:
    """Conditional GET (brief §31): ask, don't download.

    304 handling matters at expansion scale. Re-downloading every monitored
    page on every sweep is the difference between a monitor fleet that is a
    good citizen and one that gets rate-limited into uselessness — and a 429 we
    caused is indistinguishable from a source that went away.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise MonitorFetchError("scheme_not_allowed", "only http/https are allowed")
    host = parsed.hostname or ""
    _assert_public_host(host)

    headers: dict[str, str] = {}
    if etag:
        headers["if-none-match"] = etag
    if last_modified:
        headers["if-modified-since"] = last_modified

    started = time.monotonic()
    body = bytearray()
    etag_out = last_modified_out = None
    status_code = None
    try:
        with httpx.Client(
            timeout=timeout_seconds, follow_redirects=False, trust_env=False
        ) as client:
            current = url
            for _hop in range(3):
                with client.stream("GET", current, headers=headers) as resp:
                    status_code = resp.status_code
                    if resp.status_code in (301, 302, 303, 307, 308):
                        loc = resp.headers.get("location")
                        if not loc:
                            raise MonitorFetchError(
                                "redirect_without_location", "redirect missing target"
                            )
                        parsed_loc = urlparse(loc)
                        if parsed_loc.scheme not in ALLOWED_SCHEMES:
                            raise MonitorFetchError(
                                "scheme_not_allowed", "redirect scheme not allowed"
                            )
                        if parsed_loc.hostname:
                            _assert_public_host(parsed_loc.hostname)
                        current = loc
                        continue
                    if resp.status_code == 304:
                        # Not modified: no body, but the validators are still
                        # worth keeping — they are what earns the next 304.
                        return FetchResult(
                            True,
                            None,
                            resp.headers.get("etag") or etag,
                            resp.headers.get("last-modified") or last_modified,
                            None,
                            None,
                            http_status=304,
                            latency_ms=_elapsed_ms(started),
                        )
                    if resp.status_code >= 400:
                        return FetchResult(
                            False,
                            None,
                            None,
                            None,
                            None,
                            "http_error",
                            http_status=resp.status_code,
                            latency_ms=_elapsed_ms(started),
                            retry_after_seconds=(
                                _parse_retry_after(resp.headers.get("retry-after"))
                                if resp.status_code in (429, 503)
                                else None
                            ),
                        )
                    content_type = (resp.headers.get("content-type") or "").split(";")[0]
                    if content_type not in ALLOWED_CONTENT_TYPES:
                        raise MonitorFetchError(
                            "content_type_not_allowed",
                            f"content type {content_type} not monitorable",
                        )
                    etag_out = resp.headers.get("etag")
                    last_modified_out = resp.headers.get("last-modified")
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        body.extend(chunk)
                        if len(body) > MAX_BYTES:
                            raise MonitorFetchError(
                                "payload_too_large", "monitored content exceeds 2MB"
                            )
                    break
    except httpx.HTTPError as err:
        raise MonitorFetchError("network_error", f"fetch failed: {type(err).__name__}") from err

    digest = hashlib.sha256(bytes(body)).hexdigest()
    excerpt = bytes(body[:2000]).decode("utf-8", errors="replace")
    return FetchResult(
        True,
        digest,
        etag_out,
        last_modified_out,
        excerpt,
        None,
        http_status=status_code,
        latency_ms=_elapsed_ms(started),
    )


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


@dataclass(frozen=True)
class CheckOutcome:
    """Result of one monitor sweep.

    ``fetch`` carries the raw FetchResult when the fetch succeeded, so the
    caller can build a traceable EvidenceBundle (content hash + excerpt) instead
    of discarding the captured bytes.
    """

    outcome: str  # unchanged | changed | failed
    previous_hash: str | None = None
    fetch: FetchResult | None = None


def _next_check(monitor, *, now: datetime, retry_after: int | None = None) -> datetime:
    """Next sweep time, backing off while a monitor keeps failing (§38).

    A 429 means "slow down", not "try again immediately". When the server states
    its own window in ``Retry-After`` that window wins — an exponential guess
    shorter than it just earns another 429. Otherwise use exponential backoff,
    capped so a source that is down for a week is not polled forever at minute
    granularity; it resets the moment the source answers again.
    """
    if retry_after and retry_after > 0:
        return now + timedelta(seconds=min(retry_after, MAX_BACKOFF_MINUTES * 60))
    failures = monitor.failure_count or 0
    if failures <= 0:
        return now + timedelta(minutes=monitor.schedule_minutes)
    backoff = min(
        monitor.schedule_minutes * (2**failures),
        MAX_BACKOFF_MINUTES,
    )
    return now + timedelta(minutes=backoff)


def check_monitor(monitor) -> CheckOutcome:
    """Run one check cycle for a SourceMonitor row.

    Returns a CheckOutcome and updates the monitor row (hash/etag/status/
    failure_count/next_check). Candidate creation is the caller's job — it needs
    place matching + review context.

    Failure semantics (§38): a failed sweep raises failure_count and backs off.
    It never deletes previously captured valid evidence and never withdraws a
    published rule — losing the page is not the same as never having read it.
    """
    now = datetime.now(UTC)
    try:
        result = fetch_url_safely(
            monitor.url,
            etag=monitor.etag,
            last_modified=monitor.last_modified,
        )
    except MonitorFetchError:
        monitor.failure_count = (monitor.failure_count or 0) + 1
        if monitor.failure_count >= FAILURE_THRESHOLD:
            monitor.status = DEGRADED_STATUS
        monitor.last_checked_at = now
        monitor.next_check_at = _next_check(monitor, now=now)
        return CheckOutcome("failed")

    if not result.ok:
        # 403/404/429/500 …: the same degradation path as a network error, and
        # crucially NOT a content change. An unreachable source must never be
        # mistaken for a source that said something new.
        monitor.failure_count = (monitor.failure_count or 0) + 1
        if monitor.failure_count >= FAILURE_THRESHOLD:
            monitor.status = DEGRADED_STATUS
        monitor.last_http_status = result.http_status
        monitor.last_latency_ms = result.latency_ms
        monitor.last_checked_at = now
        monitor.next_check_at = _next_check(
            monitor, now=now, retry_after=result.retry_after_seconds
        )
        return CheckOutcome("failed")

    monitor.last_checked_at = now
    monitor.next_check_at = _next_check(monitor, now=now)
    monitor.last_http_status = result.http_status
    monitor.last_latency_ms = result.latency_ms
    monitor.failure_count = 0
    monitor.status = "active"
    monitor.etag = result.etag or monitor.etag
    monitor.last_modified = result.last_modified or monitor.last_modified

    if result.content_hash is None:
        # 304 Not Modified — validators held, nothing to compare.
        return CheckOutcome("unchanged", monitor.content_hash, result)

    previous_hash = monitor.content_hash
    monitor.content_hash = result.content_hash
    monitor.last_excerpt = (result.body_excerpt or "")[:2000] or None

    if previous_hash is None or previous_hash == result.content_hash:
        return CheckOutcome("unchanged", previous_hash, result)
    monitor.last_changed_at = now
    return CheckOutcome("changed", previous_hash, result)
