"""Quality-baseline coverage tests (PART A A3/A5).

Targets the branches left uncovered by the v0.5 suites:
- BoundaryMatcher verdicts for every stance × value combination
- SourceMonitor fetch guards (dns/redirect/http_error/size/network) + check_monitor paths
- RuleCandidate publish boundary guards + note/success path
"""

import socket
import threading
import types
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.core.errors import ApiError
from app.rulespec.v05_boundary import match as boundary_match
from app.services import source_monitor as sm
from app.services.candidate_service import (
    create_from_extraction,
    transition,
)
from app.services.candidate_service import (
    publish as publish_candidate,
)
from app.services.source_monitor import MonitorFetchError, check_monitor

# captured at import time, before the autouse loopback stub patches the module
_REAL_ASSERT_PUBLIC_HOST = sm._assert_public_host

# --------------------------------------------------------------- BoundaryMatcher


def test_boundary_accept_with_unstructured_value_is_unknown():
    (r,) = boundary_match(
        effective_effect="unknown",
        coexistence={"pet_indoor": "unknown"},
        preferences=[("pet_indoor", "accept")],
    )
    assert r.verdict == "UNKNOWN"


def test_boundary_avoid_conditional_is_unknown_not_conflict():
    (r,) = boundary_match(
        effective_effect="unknown",
        coexistence={"pet_indoor": "conditional"},
        preferences=[("pet_indoor", "avoid")],
    )
    assert r.verdict == "UNKNOWN"
    assert "需人工判断" in r.reason


def test_boundary_require_prohibited_matches_only_explicit_prohibition():
    prohibited = boundary_match(
        effective_effect="unknown",
        coexistence={"pet_indoor": "prohibited"},
        preferences=[("pet_indoor", "require_prohibited")],
    )[0]
    assert prohibited.verdict == "MATCH"
    allowed = boundary_match(
        effective_effect="unknown",
        coexistence={"pet_indoor": "allowed"},
        preferences=[("pet_indoor", "require_prohibited")],
    )[0]
    assert allowed.verdict == "CONFLICT"
    ambiguous = boundary_match(
        effective_effect="unknown",
        coexistence={"pet_indoor": "conditional"},
        preferences=[("pet_indoor", "require_prohibited")],
    )[0]
    assert ambiguous.verdict == "UNKNOWN"
    assert "不当作禁止" in ambiguous.reason


def test_boundary_prefer_available_not_available_insufficient():
    hit = boundary_match(
        effective_effect="unknown",
        coexistence={"pet_elevator": "available"},
        preferences=[("pet_elevator", "prefer")],
    )[0]
    assert hit.verdict == "MATCH"
    miss = boundary_match(
        effective_effect="unknown",
        coexistence={"pet_elevator": "not_available"},
        preferences=[("pet_elevator", "prefer")],
    )[0]
    assert miss.verdict == "CONFLICT"
    unknown = boundary_match(
        effective_effect="unknown",
        coexistence={"pet_elevator": "allowed"},
        preferences=[("pet_elevator", "prefer")],
    )[0]
    assert unknown.verdict == "UNKNOWN"
    assert "信息不足" in unknown.reason


def test_boundary_unknown_stance_never_guesses():
    (r,) = boundary_match(
        effective_effect="allowed",
        coexistence={"pet_indoor": "allowed"},
        preferences=[("pet_indoor", "definitely_not_a_stance")],
    )
    assert r.verdict == "UNKNOWN"
    assert "未知边界类型" in r.reason


# ---------------------------------------------------------------- SourceMonitor


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path.startswith("/redirect"):
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/final")
            self.end_headers()
        elif self.path == "/final":
            body = b"<html>redirected policy page</html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/notfound":
            self.send_response(404)
            self.end_headers()
        elif self.path == "/big":
            body = b"x" * 512
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            body = b"<html>policy v1</html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def local_server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    yield base
    server.shutdown()
    server.server_close()


@pytest.fixture(autouse=True)
def allow_loopback_host(monkeypatch):
    """These tests exercise real loopback TCP but not real DNS; the SSRF guard's
    private-range logic itself is covered by test_v05_track_b."""
    monkeypatch.setattr(sm, "_assert_public_host", lambda host: None)


def test_fetch_follows_redirect_and_revalidates_each_hop(local_server):
    result = sm.fetch_url_safely(f"{local_server}/redirect")
    assert result.ok is True
    assert result.content_hash
    assert "redirected policy page" in result.body_excerpt


def test_fetch_http_error_returns_not_ok(local_server):
    result = sm.fetch_url_safely(f"{local_server}/notfound")
    assert result.ok is False
    assert result.error_code == "http_error"


def test_fetch_rejects_oversized_payload(local_server, monkeypatch):
    monkeypatch.setattr(sm, "MAX_BYTES", 10)
    with pytest.raises(MonitorFetchError) as exc:
        sm.fetch_url_safely(f"{local_server}/big")
    assert exc.value.code == "payload_too_large"


def test_fetch_network_error_is_wrapped(monkeypatch):
    # bind then close an ephemeral port so nothing listens there
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    dead_port = probe.getsockname()[1]
    probe.close()
    with pytest.raises(MonitorFetchError) as exc:
        sm.fetch_url_safely(f"http://127.0.0.1:{dead_port}/x")
    assert exc.value.code == "network_error"


def test_fetch_dns_failure_is_wrapped(monkeypatch):
    def _boom(host, *args, **kwargs):
        raise socket.gaierror("no such host")

    monkeypatch.setattr(socket, "getaddrinfo", _boom)
    monkeypatch.setattr(sm, "_assert_public_host", _REAL_ASSERT_PUBLIC_HOST)
    with pytest.raises(MonitorFetchError) as exc:
        sm.fetch_url_safely("https://example.invalid/policy")
    assert exc.value.code == "dns_failure"


def _monitor(base, path="/policy", **overrides):
    defaults = dict(
        url=f"{base}{path}",
        schedule_minutes=30,
        content_hash=None,
        etag=None,
        last_modified=None,
        last_excerpt=None,
        failure_count=0,
        status="active",
        last_checked_at=None,
        next_check_at=None,
        last_changed_at=None,
    )
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def test_check_monitor_failed_path_increments_and_marks_failing_after_three(monkeypatch):
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    dead_port = probe.getsockname()[1]
    probe.close()
    monitor = _monitor(f"http://127.0.0.1:{dead_port}")
    for expected_count in (1, 2):
        outcome = check_monitor(monitor)
        assert outcome.outcome == "failed"
        assert monitor.failure_count == expected_count
        assert monitor.status == "active"
    outcome = check_monitor(monitor)
    assert outcome.outcome == "failed"
    assert monitor.failure_count == 3
    assert monitor.status == "failing"


def test_check_monitor_unchanged_then_changed(local_server):
    monitor = _monitor(local_server)
    first = check_monitor(monitor)
    assert first.outcome == "unchanged"
    assert first.previous_hash is None
    second = check_monitor(monitor)
    assert second.outcome == "unchanged"
    assert second.previous_hash == first.fetch.content_hash
    # now the source content changes → changed outcome carries traceable fetch
    _Handler_original_get = _Handler.do_GET

    def do_GET_v2(self):
        body = b"<html>policy v2 changed</html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    _Handler.do_GET = do_GET_v2
    try:
        third = check_monitor(monitor)
    finally:
        _Handler.do_GET = _Handler_original_get
    assert third.outcome == "changed"
    assert third.previous_hash == first.fetch.content_hash
    assert third.fetch.content_hash != first.fetch.content_hash
    assert monitor.last_changed_at is not None


# ------------------------------------------------------- candidate publish gate


def _source(db, issuer="quality-baseline"):
    from app.models import Source

    src = Source(
        source_type="onsite_signage",
        issuer=issuer,
        directness="direct",
        collected_at="2026-09-13T00:00:00Z",
    )
    db.add(src)
    db.flush()
    return src


def _approved_candidate(db, *, place_id=None, source_id=None, bundle_id=None):
    from app.models import Place, Source
    from app.models.evidence import EvidenceBundle, SourceArtifact

    if source_id is None:
        source_id = _source(db).id
    if bundle_id is None:
        src_row = db.get(Source, source_id)
        artifact = SourceArtifact(
            source_id=src_row.id,
            source_platform="OnsiteEvidenceCollector",
            artifact_type="signage_photo",
            collector_type="OnsiteEvidenceCollector",
            content_hash="b" * 64,
            captured_excerpt="宠物需牵引",
            collected_at=datetime.now(UTC),
            storage_allowed=True,
            display_allowed=True,
            redistribution_allowed=True,
        )
        db.add(artifact)
        db.flush()
        bundle = EvidenceBundle(
            artifact_id=artifact.id,
            source_id=src_row.id,
            source_platform="OnsiteEvidenceCollector",
            quoted_fragment="宠物需牵引",
            content_hash="b" * 64,
            captured_at=datetime.now(UTC),
            place_match_evidence={"matched_by": "manual_review_fixture"},
        )
        db.add(bundle)
        db.flush()
        bundle_id = bundle.id
    if place_id is None:
        place = Place(canonical_name="质量基线测试咖啡", place_type="cafe")
        db.add(place)
        db.flush()
        place_id = place.id
    cand = create_from_extraction(
        db,
        source_id=source_id,
        place_id=place_id,
        extraction_method="ocr",
        animal_scope="ordinary_pet",
        action="enter",
        effect="allowed",
        evidence_bundle_id=bundle_id,
    )
    transition(cand, "REVIEW_PENDING")
    transition(cand, "APPROVED")
    return cand


def test_publish_rejects_non_approved_candidate(db_session):
    src = _source(db_session)
    cand = create_from_extraction(
        db_session, source_id=src.id, extraction_method="ocr", raw_text="x"
    )
    with pytest.raises(ApiError) as exc:
        publish_candidate(db_session, cand, reviewer_id="r1")
    assert exc.value.code == "candidate_not_approved"


def test_publish_rejects_unmatched_candidate(db_session):
    src = _source(db_session)
    cand = create_from_extraction(
        db_session,
        source_id=src.id,
        extraction_method="ocr",
        animal_scope="ordinary_pet",
        action="enter",
        effect="allowed",
    )
    assert cand.review_status == "MATCH_PENDING"
    transition(cand, "REVIEW_PENDING")
    transition(cand, "APPROVED")
    with pytest.raises(ApiError) as exc:
        publish_candidate(db_session, cand, reviewer_id="r1")
    assert exc.value.code == "candidate_unmatched"


def test_publish_rejects_missing_source(db_session):
    # DB-level FK normally blocks a nonexistent source; the publish guard is
    # defense-in-depth, so exercise it with an unflushed candidate object.
    from app.models import RuleCandidate

    cand = RuleCandidate(
        source_id="00000000-0000-0000-0000-000000000000",
        place_id="00000000-0000-0000-0000-000000000001",
        extraction_method="ocr",
        animal_scope="ordinary_pet",
        action="enter",
        effect="allowed",
        review_status="APPROVED",
    )
    with pytest.raises(ApiError) as exc:
        publish_candidate(db_session, cand, reviewer_id="r1")
    assert exc.value.code == "source_missing"


def test_publish_rejects_missing_evidence_bundle(db_session):
    from uuid import uuid4

    from app.models import RuleCandidate

    src = _source(db_session)
    # unflushed candidate: no INSERT, so the bundle FK cannot pre-block the guard
    cand = RuleCandidate(
        source_id=src.id,
        place_id="00000000-0000-0000-0000-000000000001",
        zone_id=None,
        extraction_method="ocr",
        animal_scope="ordinary_pet",
        action="enter",
        effect="allowed",
        review_status="APPROVED",
        evidence_bundle_id=str(uuid4()),
    )
    with pytest.raises(ApiError) as exc:
        publish_candidate(db_session, cand, reviewer_id="r1")
    assert exc.value.code == "evidence_bundle_missing"


def test_publish_success_records_rule_note_and_reviewer(db_session):
    cand = _approved_candidate(db_session)
    rule = publish_candidate(db_session, cand, reviewer_id="reviewer-7", note="现场告示一致")
    assert rule.status == "current"
    assert rule.rule_layer == "OPERATOR_POLICY"
    assert cand.review_status == "PUBLISHED"
    assert cand.published_rule_id == rule.id
    assert cand.reviewer_id == "reviewer-7"
    assert cand.review_note == "现场告示一致"


def test_concurrent_publish_single_winner(db_session):
    """A12: two reviewers publishing the same APPROVED candidate must yield
    exactly one AccessRule (atomic compare-and-set, loser rolls back)."""
    from sqlalchemy import func, select

    from app.db.session import get_session_factory
    from app.models import AccessRule, RuleCandidate

    cand = _approved_candidate(db_session)
    cand_id, place_id = cand.id, cand.place_id
    db_session.commit()  # make the APPROVED row visible to other sessions

    s1 = get_session_factory()()
    s2 = get_session_factory()()
    try:
        c1 = s1.get(RuleCandidate, cand_id)
        c2 = s2.get(RuleCandidate, cand_id)
        assert c1.review_status == "APPROVED"
        assert c2.review_status == "APPROVED"

        rule = publish_candidate(s1, c1, reviewer_id="r1")
        s1.commit()

        with pytest.raises(ApiError) as exc:
            publish_candidate(s2, c2, reviewer_id="r2")
        assert exc.value.code == "candidate_already_published"
        s2.rollback()

        total = s1.scalar(
            select(func.count()).select_from(AccessRule).where(AccessRule.place_id == place_id)
        )
        assert total == 1
        assert c1.review_status == "PUBLISHED"
        assert rule.status == "current"
    finally:
        s1.close()
        s2.close()
