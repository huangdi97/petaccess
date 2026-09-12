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
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

MAX_BYTES = 2 * 1024 * 1024
ALLOWED_CONTENT_TYPES = ("text/html", "text/plain", "application/json")
ALLOWED_SCHEMES = ("http", "https")


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


def fetch_url_safely(url: str, *, timeout_seconds: float = 5.0) -> FetchResult:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise MonitorFetchError("scheme_not_allowed", "only http/https are allowed")
    host = parsed.hostname or ""
    _assert_public_host(host)

    body = bytearray()
    etag = last_modified = content_type = None
    try:
        # follow redirects manually and re-validate every hop
        with httpx.Client(
            timeout=timeout_seconds, follow_redirects=False, trust_env=False
        ) as client:
            current = url
            for _hop in range(3):
                with client.stream("GET", current) as resp:
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
                    if resp.status_code >= 400:
                        return FetchResult(False, None, None, None, None, "http_error")
                    content_type = (resp.headers.get("content-type") or "").split(";")[0]
                    if content_type not in ALLOWED_CONTENT_TYPES:
                        raise MonitorFetchError(
                            "content_type_not_allowed",
                            f"content type {content_type} not monitorable",
                        )
                    etag = resp.headers.get("etag")
                    last_modified = resp.headers.get("last-modified")
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
    return FetchResult(True, digest, etag, last_modified, excerpt, None)


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


def check_monitor(monitor) -> CheckOutcome:
    """Run one check cycle for a SourceMonitor row.

    Returns a CheckOutcome and updates the monitor row (hash/etag/status/
    failure_count/next_check). Candidate creation is the caller's job — it needs
    place matching + review context.
    """
    from datetime import UTC, datetime, timedelta

    try:
        result = fetch_url_safely(monitor.url)
    except MonitorFetchError:
        monitor.failure_count = (monitor.failure_count or 0) + 1
        monitor.status = "failing" if monitor.failure_count >= 3 else monitor.status
        monitor.last_checked_at = datetime.now(UTC)
        monitor.next_check_at = datetime.now(UTC) + timedelta(minutes=monitor.schedule_minutes)
        return CheckOutcome("failed")

    monitor.last_checked_at = datetime.now(UTC)
    monitor.next_check_at = datetime.now(UTC) + timedelta(minutes=monitor.schedule_minutes)
    previous_hash = monitor.content_hash
    monitor.content_hash = result.content_hash
    monitor.etag = result.etag
    monitor.last_modified = result.last_modified
    monitor.last_excerpt = (result.body_excerpt or "")[:2000] or None
    monitor.failure_count = 0
    monitor.status = "active"

    if previous_hash is None or previous_hash == result.content_hash:
        return CheckOutcome("unchanged", previous_hash, result)
    monitor.last_changed_at = datetime.now(UTC)
    return CheckOutcome("changed", previous_hash, result)
