"""RealityReport parent-flow API contract tests (Master Goal v0.2.0 §15–§27).

Covers the one-Contribution-many-candidates contract:

- ON_SITE_NOW contribution creates a parent report + candidates, all
  REVIEW_PENDING / UNVERIFIED (one-shot proximity never auto-verifies).
- ON_SITE_PAST without an explicit ``observed_at`` is rejected 422 (the
  submission time must never become the event time).
- EXTERNAL_ONLINE_CONTENT without any time evidence is rejected 422;
  content_published_at and observed_at stay separate fields.
- PARENT_PLACE_ONLY reports cannot attach a candidate to a tenant place
  (mall-level fact must not masquerade as a restaurant-level fact).
- ObservationEffort with animal_observed=false creates an effort row only,
  never a NO_ANIMAL_PRESENCE claim.
- A RealityConfirmation is an append; verified claims are never deleted.
- Anonymous (tokenless) reports are allowed and get a one-time token.
- Idempotency-Key returns the same receipt for a repeated call.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app

ON_SITE_ORIGINS = [
    "on_site_now",
    "on_site_past",
    "external_online_content",
    "operator_provided",
    "official_public_content",
]


@pytest.fixture(scope="module", autouse=True)
def _reset_rate_limits():
    """Clear rate-limit/idempotency counters before the module runs.

    All anonymous requests share the same IP key, so repeated test runs would
    otherwise trip the 20/hour contribution limit on db 1 (test-dedicated).
    """
    import redis as redis_lib

    from app.core.config import get_settings

    r = redis_lib.Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        for key in r.scan_iter(match="ratelimit:*"):
            r.delete(key)
        for key in r.scan_iter(match="idem:*"):
            r.delete(key)
    except redis_lib.RedisError:
        pass  # dev infra may be absent; rate limit then fails open anyway
    yield


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _iso_equal(actual: str | None, expected: str | None) -> bool:
    """Compare ISO datetimes regardless of UTC suffix form (+00:00 vs Z)."""
    if actual is None or expected is None:
        return actual is expected
    from datetime import datetime as dt

    try:
        return dt.fromisoformat(actual.replace("Z", "+00:00")) == dt.fromisoformat(
            expected.replace("Z", "+00:00")
        )
    except ValueError:
        return actual == expected


@pytest.fixture(scope="module")
def place_id(client):
    """A place the demo seed guarantees (星河咖啡·测试店)."""
    r = client.get("/api/v1/places", params={"q": "星河"})
    assert r.status_code == 200, r.text
    items = r.json().get("items", [])
    assert items, "demo seed must contain 星河咖啡·测试店"
    return items[0]["id"]


@pytest.fixture(scope="module")
def signed_user(client) -> dict:
    email = f"rr-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"display_name": "现实记录者", "email": email, "password": "passw0rd123"},
    )
    assert r.status_code in (200, 201), r.text
    tok = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "passw0rd123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _presence_candidate() -> dict:
    return {
        "candidate_type": "observed_presence",
        "animal_scope": "dog",
        "observed_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        "payload": {"observed_action": "enter", "observed_context": "室内入口"},
    }


def _report(origin: str, **overrides) -> dict:
    base: dict = {
        "origin": origin,
        "place_match_evidence_types": ["user_confirmation"],
        "time_evidence_state": "exact_event_time",
        "place_match_state": "exact_place",
        "fact_evidence_state": "insufficient",
        "privacy_state": "private",
        "observed_at": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
        "time_certainty": "approximate",
    }
    base.update(overrides)
    return base


def test_anonymous_on_site_now_report_with_candidate_never_verifies(client, place_id):
    """AC5/§18: one-shot proximity proves device nearby, never event_verified."""
    r = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        json={
            "report": _report("on_site_now"),
            "candidates": [_presence_candidate()],
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["moderation_state"] == "pending"
    assert body["abuse_flags"] == []
    assert len(body["candidates"]) == 1
    cand = body["candidates"][0]
    assert cand["candidate_type"] == "observed_presence"
    assert cand["review_status"] == "REVIEW_PENDING"
    assert cand["verification_status"] == "unverified"
    # anonymous token is returned exactly once for the caller to persist
    assert body["report"]["anonymous_token"]


def test_report_candidate_has_private_traceable_evidence_bundle(client, place_id, signed_user):
    """Every report-backed candidate gets Artifact -> EvidenceBundle provenance."""
    observed = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    r = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        headers=signed_user,
        json={
            "report": _report("on_site_past", observed_at=observed),
            "candidates": [
                {
                    "candidate_type": "observed_presence",
                    "animal_scope": "dog",
                    "observed_at": observed,
                    "payload": {"observed_action": "present"},
                }
            ],
        },
    )
    assert r.status_code == 201, r.text
    report_id = r.json()["report"]["id"]
    cand_id = r.json()["candidates"][0]["id"]

    from app.db.session import get_session_factory
    from app.models import RealityCandidate
    from app.models.evidence import EvidenceBundle, SourceArtifact

    session = get_session_factory()()
    try:
        candidate = session.get(RealityCandidate, cand_id)
        assert candidate is not None
        assert candidate.evidence_bundle_id is not None
        bundle = session.get(EvidenceBundle, candidate.evidence_bundle_id)
        assert bundle is not None
        artifact = session.get(SourceArtifact, bundle.artifact_id)
        assert artifact is not None
        assert artifact.source_content_id == report_id
        assert artifact.display_allowed is False
        assert artifact.redistribution_allowed is False
        assert bundle.place_match_evidence["state"] == "exact_place"
        assert bundle.temporal_evidence["observed_at"] is not None
        assert bundle.license_metadata["structured_fact_publication_only"] is True
    finally:
        session.close()


def test_effort_only_report_keeps_parent_evidence_provenance(client, place_id, signed_user):
    """A no-animal observation stays an effort row linked to its private report evidence."""
    observed = (datetime.now(UTC) - timedelta(minutes=20)).isoformat()
    r = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        headers=signed_user,
        json={
            "report": _report("on_site_past", observed_at=observed),
            "candidates": [],
            "effort": {
                "place_id": place_id,
                "duration_bucket": "min_10_30",
                "covered_zone_ids": [],
                "animal_observed": False,
                "observed_at": observed,
            },
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["candidates"] == []
    assert body["effort_id"]

    from app.db.session import get_session_factory
    from app.models import ObservationEffort
    from app.models.evidence import EvidenceBundle

    session = get_session_factory()()
    try:
        effort = session.get(ObservationEffort, body["effort_id"])
        assert effort is not None
        assert effort.animal_observed is False
        assert effort.report_id == body["report"]["id"]
        assert effort.evidence_bundle_id is not None
        assert session.get(EvidenceBundle, effort.evidence_bundle_id) is not None
    finally:
        session.close()


def test_raw_reality_report_parents_are_not_public(client, place_id):
    """Report parents keep private provenance/tokens; published claims are the public layer."""
    r = client.get(f"/api/v1/places/{place_id}/reality/reports")
    assert r.status_code in (401, 403), r.text


def test_on_site_past_without_observed_at_is_rejected(client, place_id):
    """§19: ON_SITE_PAST must state when it happened; never default to submit time."""
    r = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        json={
            "report": _report("on_site_past", observed_at=None),
            "candidates": [_presence_candidate()],
        },
    )
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "on_site_past_time_required"


def test_external_content_requires_time_evidence(client, place_id):
    """§20: external content without published/event time cannot invent a date."""
    r = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        json={
            "report": _report(
                "external_online_content",
                content_published_at=None,
                claimed_event_at=None,
                observed_at=None,
            ),
            "candidates": [_presence_candidate()],
        },
    )
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "external_time_required"


def test_external_content_keeps_published_and_event_time_separate(client, place_id, signed_user):
    """§20: content_published_at stays distinct from observed_at in the record."""
    published = (datetime.now(UTC) - timedelta(days=3)).isoformat()
    observed = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    r = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        headers=signed_user,
        json={
            "report": _report(
                "external_online_content",
                content_published_at=published,
                claimed_event_at=observed,
                observed_at=observed,
                time_certainty="approximate",
            ),
            "candidates": [_presence_candidate()],
            "external_content": {
                "source_url": "https://example.com/pet-post-1",
                "platform": "xiaohongshu",
                "published_at": published,
            },
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert _iso_equal(body["report"]["content_published_at"], published)
    assert _iso_equal(body["report"]["observed_at"], observed)
    assert not _iso_equal(body["report"]["observed_at"], published)
    assert body["external_content_id"]


def test_parent_place_only_cannot_pin_candidate_to_tenant(client, place_id):
    """§21: mall-level matches must not surface tenant-level reality."""
    r = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        json={
            "report": _report(
                "on_site_now",
                place_match_state="parent_place_only",
                container_place_id=place_id,
                subject_place_id=None,
            ),
            # a candidate pinned to a *different* tenant than the container
            "candidates": [
                {
                    "candidate_type": "observed_presence",
                    "place_id": "00000000-0000-0000-0000-000000000099",
                    "payload": {"observed_action": "enter"},
                }
            ],
        },
    )
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "parent_place_escalation"


def test_imprecise_place_match_cannot_publish_public_claim(client, place_id):
    """§21: review may keep an area-level lead, but publication requires an exact place."""
    email = f"place-match-{uuid.uuid4().hex[:8]}@example.com"
    registered = client.post(
        "/api/v1/auth/register",
        json={"display_name": "地点核验测试", "email": email, "password": "passw0rd123"},
    )
    assert registered.status_code in (200, 201), registered.text
    token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "passw0rd123"},
    ).json()["access_token"]

    created = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "report": _report(
                "external_online_content",
                place_match_state="area_only",
                content_published_at=(datetime.now(UTC) - timedelta(days=1)).isoformat(),
                observed_at=None,
                claimed_event_at=None,
                time_evidence_state="publication_time_only",
            ),
            "candidates": [
                {
                    "candidate_type": "observed_presence",
                    "animal_scope": "dog",
                    "payload": {"observed_action": "present"},
                }
            ],
        },
    )
    assert created.status_code == 201, created.text
    cand_id = created.json()["candidates"][0]["id"]

    from app.db.session import get_session_factory
    from app.models import User

    session = get_session_factory()()
    try:
        user = session.query(User).filter(User.email == email).one()
        user.role = "admin"
        session.commit()
    finally:
        session.close()

    admin_token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "passw0rd123"},
    ).json()["access_token"]
    decision = client.post(
        f"/api/v1/reality/candidates/{cand_id}/decision",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"reality_decision": "verified", "decision_note": None},
    )
    assert decision.status_code == 400, decision.text
    assert decision.json()["error"]["code"] == "reality_exact_place_required"


def test_publication_only_facts_stay_out_of_recent_and_current_summaries(
    client, place_id, signed_user
):
    """A recent post date is not a recent event date or proof a facility is current."""
    before = client.get(f"/api/v1/places/{place_id}/reality").json()
    published = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    created = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        headers=signed_user,
        json={
            "report": _report(
                "external_online_content",
                observed_at=None,
                claimed_event_at=None,
                content_published_at=published,
                time_evidence_state="publication_time_only",
                time_certainty="unknown",
                fact_evidence_state="text_only_external",
            ),
            "candidates": [
                {
                    "candidate_type": "staff_response",
                    "observed_at": None,
                    "payload": {
                        "actor_role": "unknown_staff",
                        "response_action": "request_wait_outside",
                        "staff_awareness_state": "awareness_confirmed",
                    },
                },
                {
                    "candidate_type": "animal_facility",
                    "observed_at": None,
                    "payload": {
                        "facility_type": "water_bowl",
                        "purpose_state": "purpose_signage_supported",
                        "operational_state": "active",
                    },
                },
            ],
            "external_content": {
                "source_url": f"https://example.com/publication-only-{uuid.uuid4().hex}",
                "platform": "web",
                "published_at": published,
            },
        },
    )
    assert created.status_code == 201, created.text

    me = client.get("/api/v1/auth/me", headers=signed_user)
    assert me.status_code == 200, me.text
    from app.db.session import get_session_factory
    from app.models import User

    session = get_session_factory()()
    try:
        user = session.get(User, me.json()["id"])
        assert user is not None
        user.role = "admin"
        session.commit()
    finally:
        session.close()

    for candidate in created.json()["candidates"]:
        decision = client.post(
            f"/api/v1/reality/candidates/{candidate['id']}/decision",
            headers=signed_user,
            json={"reality_decision": "verified", "decision_note": None},
        )
        assert decision.status_code == 200, decision.text

    after = client.get(f"/api/v1/places/{place_id}/reality").json()
    assert after["recent_count_30d"] == before["recent_count_30d"]
    assert after["staff_response_summary"] == before["staff_response_summary"]
    assert after["facility_summary"] == before["facility_summary"]

    events = client.get(f"/api/v1/places/{place_id}/reality/events").json()
    published_events = [
        event
        for event in events
        if event["time_evidence_state"] == "publication_time_only"
        and event["content_published_at"] is not None
    ]
    assert len(published_events) >= 2


def test_effort_never_becomes_no_animal_presence_claim(client, place_id, signed_user):
    """§24: animal_observed=false forms only an ObservationEffort row."""
    before = client.get(f"/api/v1/places/{place_id}/reality").json()
    r = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        headers=signed_user,
        json={
            "report": _report("on_site_now"),
            "effort": {
                "place_id": place_id,
                "duration_bucket": "min_10_30",
                "covered_zone_ids": [],
                "animal_observed": False,
                "observed_at": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
            },
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["effort_id"]
    # consumer reality answer is unchanged (still no claim rows created)
    after = client.get(f"/api/v1/places/{place_id}/reality").json()
    assert after["evidence_count"] == before["evidence_count"]


def test_confirmation_is_append_never_delete(client, place_id, signed_user):
    """§25: a confirmation adds a record; it never removes older facts."""
    # Publish a verified presence first (admin path), then confirm NOT_SEEN_NOW.
    cand_id = _make_verified_presence(client, place_id, signed_user)
    r = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        headers=signed_user,
        json={
            "report": _report("on_site_now"),
            "confirmation": {
                "confirmation_type": "not_seen_now",
                "place_id": place_id,
                "target_candidate_id": cand_id,
                "observed_at": (datetime.now(UTC) - timedelta(minutes=5)).isoformat(),
            },
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["confirmation_id"]
    # the older published claim still exists in the full reality answer
    reality = client.get(f"/api/v1/places/{place_id}/reality").json()
    assert reality["state"] != "no_data"


def test_statff_awareness_unknown_is_stored(client, place_id, signed_user):
    """§22: staff response with awareness UNKNOWN stays 'no observed handling'."""
    r = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        headers=signed_user,
        json={
            "report": _report("on_site_now"),
            "candidates": [
                {
                    "candidate_type": "staff_response",
                    "payload": {
                        "actor_role": "waiter",
                        "response_action": "no_intervention_observed",
                        "staff_awareness_state": "awareness_unknown",
                    },
                }
            ],
        },
    )
    assert r.status_code == 201, r.text
    cand = r.json()["candidates"][0]
    assert cand["verification_status"] == "unverified"
    # as「本次记录未观察到工作人员处理」— never「工作人员未干预」.


def test_idempotency_key_returns_same_receipt(client, place_id, signed_user):
    """Idempotent retries must not create duplicate reports."""
    idem = f"idem-{uuid.uuid4().hex}"
    payload = {
        "report": _report(
            "on_site_now",
            observed_at=(datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        ),
        "candidates": [_presence_candidate()],
    }
    r1 = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        headers={**signed_user, "Idempotency-Key": idem},
        json=payload,
    )
    r2 = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        headers={**signed_user, "Idempotency-Key": idem},
        json=payload,
    )
    assert r1.status_code == 201 and r2.status_code == 201, (r1.text, r2.text)
    assert r1.json()["report"]["id"] == r2.json()["report"]["id"]
    assert r1.json()["candidates"][0]["id"] == r2.json()["candidates"][0]["id"]


def test_reality_trace_distinguishes_fact_from_review(client, place_id):
    """§14: the trace must show the fact and the verification posture separately."""
    r = client.get(f"/api/v1/places/{place_id}/reality/trace")
    assert r.status_code == 200, r.text
    body = r.json()
    labels = {s["label"] for s in body["fact_sections"]}
    review_labels = {s["label"] for s in body["review_sections"]}
    assert "现场摘要" in labels
    assert "核验" in review_labels
    # summary is consumer copy, never a raw internal enum
    assert body["summary"] not in {
        "OBSERVED_RECENTLY",
        "OBSERVED_HISTORICALLY",
        "MULTI_EVIDENCE_OBSERVED",
        "NO_RECENT_RECORD",
        "INSUFFICIENT_OBSERVATION",
        "DISPUTED",
    }


def test_reality_trace_uses_consumer_language_for_verified_demo_facts(client):
    """Trace sections must not leak raw enum vocabulary from staff/facility/freshness axes."""
    r = client.get("/api/v1/places", params={"q": "云栖"})
    assert r.status_code == 200, r.text
    mall_id = r.json()["items"][0]["id"]
    trace = client.get(f"/api/v1/places/{mall_id}/reality/trace")
    assert trace.status_code == 200, trace.text
    visible = " ".join(
        str(section.get("value") or "")
        for section in [*trace.json()["fact_sections"], *trace.json()["review_sections"]]
    )
    for raw in ("request_relocation", "require_carrier", "pet_waiting_area", "FRESH"):
        assert raw not in visible


def test_demo_reality_events_preserve_observed_submitted_reviewed_axes(client):
    """Visual/demo fixture must exercise all three provenance times without conflation."""
    places = client.get("/api/v1/places", params={"q": "云栖", "limit": 10})
    assert places.status_code == 200, places.text
    mall = next(item for item in places.json()["items"] if item["canonical_name"] == "云栖中心·测试商场")

    response = client.get(f"/api/v1/places/{mall['id']}/reality/events")
    assert response.status_code == 200, response.text
    events = response.json()
    assert events
    assert all(event["time_evidence_state"] == "exact_event_time" for event in events)
    assert all(event["submitted_at"] is not None for event in events)
    assert all(event["last_verified_at"] is not None for event in events)
    assert all(event["submitted_at"] != event["last_verified_at"] for event in events)


def test_reality_events_expose_only_published_verified_facts(client, place_id, signed_user):
    """Consumer timeline must not leak review-pending candidates or staff identity."""
    pending = client.post(
        f"/api/v1/places/{place_id}/reality/contributions",
        headers=signed_user,
        json={
            "candidate_type": "observed_presence",
            "place_id": place_id,
            "animal_scope": "dog",
            "observed_at": (datetime.now(UTC) - timedelta(minutes=30)).isoformat(),
            "payload": {"observed_action": "present", "observed_context": "待审核事件"},
        },
    )
    assert pending.status_code == 201, pending.text
    pending_id = pending.json()["id"]

    r = client.get(f"/api/v1/places/{place_id}/reality/events")
    assert r.status_code == 200, r.text
    events = r.json()
    assert all(
        event["verification_status"] in {"human_verified", "human_verified_with_note"}
        for event in events
    )
    assert all(event["id"] != pending_id for event in events)
    assert all("reviewer" not in event for event in events)
    assert all("policy_statement_verbatim" not in event for event in events)
    assert all("anonymous_token" not in event for event in events)
    assert all("reporter_id" not in event for event in events)
    assert all("media_refs" not in event for event in events)
    assert all("source_url" not in event for event in events)


def _make_verified_presence(client, place_id, auth) -> str:
    """Create + human-verify one observed-presence candidate (v0.9 §7.4)."""
    r = client.post(
        f"/api/v1/places/{place_id}/reality/contributions",
        headers=auth,
        json={
            "candidate_type": "observed_presence",
            "place_id": place_id,
            "animal_scope": "dog",
            "observed_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
            "payload": {"observed_action": "enter", "observed_context": "室内"},
        },
    )
    assert r.status_code == 201, r.text
    cand_id = r.json()["id"]

    # Promote the signed-in contributor to admin, then human-verify (v0.9 §7.4:
    # reality_decision is human-only; AI may never write it).
    from app.db.session import get_session_factory
    from app.models import User

    s = get_session_factory()()
    try:
        user = s.query(User).order_by(User.created_at.desc()).first()
        assert user is not None, "seed must contain at least one user"
        user.role = "admin"
        s.commit()
        email = user.email
    finally:
        s.close()

    tok = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "passw0rd123"},
    ).json()["access_token"]
    decision = client.post(
        f"/api/v1/reality/candidates/{cand_id}/decision",
        headers={"Authorization": f"Bearer {tok}"},
        json={"reality_decision": "verified", "decision_note": None},
    )
    assert decision.status_code == 200, decision.text
    return cand_id


def test_my_reality_contributions_lists_only_own_reports(client, signed_user, place_id):
    """M7 B1 — GET /me/reality-contributions returns only the caller's own reports."""
    r = client.post(
        f"/api/v1/places/{place_id}/reality/reports",
        headers=signed_user,
        json={
            "report": _report("on_site_now"),
            "candidates": [_presence_candidate()],
        },
    )
    assert r.status_code == 201, r.text
    report_id = r.json()["report"]["id"]

    got = client.get("/api/v1/me/reality-contributions", headers=signed_user)
    assert got.status_code == 200, got.text
    rows = got.json()
    mine = next((row for row in rows if row["report_id"] == report_id), None)
    assert mine is not None, "the just-created report must appear in my contributions"
    assert mine["place_id"] == place_id
    assert mine["candidates"][0]["candidate_type"] == "observed_presence"
    assert mine["candidates"][0]["review_status"] == "REVIEW_PENDING"

    anon = client.get("/api/v1/me/reality-contributions")
    assert anon.status_code == 401, anon.text
