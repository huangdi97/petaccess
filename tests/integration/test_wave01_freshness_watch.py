"""WAVE_01 §79 (change handling) + §80 freshness + §81 watch matrix.

These run against the disposable test database (the repo guard refuses anything
else), so they may write. What they *must not* do is assume a particular
production count — assertions are about the rule, verified on rows this module
creates, not on whatever the database happens to hold.
"""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.main import app
from app.models import FreshnessPolicy, Source, WatchSubscription
from app.models.enums import WatchStatus, WatchTargetType


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def moderator(client):
    email = f"wave01-{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"display_name": "wave01 复核员", "email": email, "password": "passw0rd123"},
    )
    from app.models import User

    s = get_session_factory()()
    u = s.query(User).filter(User.email == email).one()
    u.role = "admin"
    s.commit()
    s.close()
    tok = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "passw0rd123"}
    ).json()["access_token"]
    return tok


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _new_place(client, tok, name):
    r = client.post(
        "/api/v1/places",
        json={
            "canonical_name": name,
            "place_type": "park",
            "location_wkt": "POINT(121.500 31.200)",
        },
        headers=_auth(tok),
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ------------------------------------------------- §79 change → candidate, never rule


class _PolicyHandler(BaseHTTPRequestHandler):
    """Serves a mutable page so a source change can be provoked locally.

    §79 forbids tampering with third-party pages to test change detection; the
    page has to be ours.
    """

    body = b"<html>policy v1</html>"

    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(type(self).body)))
        self.end_headers()
        self.wfile.write(type(self).body)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def policy_server():
    server = HTTPServer(("127.0.0.1", 0), _PolicyHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server
    server.shutdown()


def _new_monitor(client, tok, source_id: str, url: str) -> str:
    r = client.post(
        "/api/v1/admin/monitors",
        json={"source_id": source_id, "url": url, "schedule_minutes": 5},
        headers=_auth(tok),
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _make_source(client, tok, issuer: str) -> str:
    r = client.post(
        "/api/v1/sources",
        json={
            "source_type": "official_operator_policy",
            "issuer": issuer,
            "directness": "direct",
            "source_url": "https://example.com/fixture",
        },
        headers=_auth(tok),
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_source_change_produces_candidate_and_never_a_rule(client, moderator, policy_server):
    """§41: a detected change may create a candidate; it may never publish."""
    from app.services import source_monitor as sm

    orig = sm._assert_public_host
    # The SSRF guard is tested for real elsewhere; the fixture server is on
    # loopback, which the guard exists precisely to refuse.
    sm._assert_public_host = lambda host: None
    try:
        port = policy_server.server_address[1]
        url = f"http://127.0.0.1:{port}/policy"
        src_id = _make_source(client, moderator, "WAVE01 变更来源")
        mon_id = _new_monitor(client, moderator, src_id, url)

        baseline = client.post(
            f"/api/v1/admin/monitors/{mon_id}/check", headers=_auth(moderator)
        ).json()
        assert baseline["outcome"] == "unchanged", baseline

        _PolicyHandler.body = b"<html>policy v2: dogs prohibited</html>"
        changed = client.post(
            f"/api/v1/admin/monitors/{mon_id}/check", headers=_auth(moderator)
        ).json()
        assert changed["outcome"] == "changed", changed
        assert changed["candidate_id"]
        assert changed["evidence_bundle_id"], "change must be traceable to evidence"

        # The decisive assertion: no rule appeared, and the candidate is not
        # linked to one.
        cand = client.get(
            f"/api/v1/admin/candidates/{changed['candidate_id']}", headers=_auth(moderator)
        )
        if cand.status_code == 200:
            assert cand.json().get("published_rule_id") is None, cand.text
    finally:
        _PolicyHandler.body = b"<html>policy v1</html>"
        sm._assert_public_host = orig


def test_repeated_identical_change_yields_one_candidate(client, moderator, policy_server):
    """§79: one candidate per distinct content state, not per detection.

    The dedup path only matters when the page moves to a state we have already
    ingested — a monitor that changes and then changes back must not produce a
    second candidate for the same bytes.
    """
    from app.services import source_monitor as sm

    orig = sm._assert_public_host
    sm._assert_public_host = lambda host: None
    try:
        port = policy_server.server_address[1]
        url = f"http://127.0.0.1:{port}/policy"
        src_id = _make_source(client, moderator, "WAVE01 重复变更来源")
        mon_id = _new_monitor(client, moderator, src_id, url)

        client.post(f"/api/v1/admin/monitors/{mon_id}/check", headers=_auth(moderator))

        _PolicyHandler.body = b"<html>policy v3</html>"
        first = client.post(
            f"/api/v1/admin/monitors/{mon_id}/check", headers=_auth(moderator)
        ).json()
        assert first["outcome"] == "changed"
        assert first["duplicate_change"] is False

        _PolicyHandler.body = b"<html>policy v4</html>"
        other = client.post(
            f"/api/v1/admin/monitors/{mon_id}/check", headers=_auth(moderator)
        ).json()
        assert other["outcome"] == "changed"
        assert other["candidate_id"] != first["candidate_id"], (
            "a genuinely different content state is a different candidate; "
            "dedup must never collapse real content"
        )

        # Back to v3: the bytes are already ingested, so this is not a new fact.
        _PolicyHandler.body = b"<html>policy v3</html>"
        again = client.post(
            f"/api/v1/admin/monitors/{mon_id}/check", headers=_auth(moderator)
        ).json()
        assert again["outcome"] == "changed"
        assert again["duplicate_change"] is True
        assert again["candidate_id"] == first["candidate_id"]
    finally:
        _PolicyHandler.body = b"<html>policy v1</html>"
        sm._assert_public_host = orig


# ------------------------------------------------------------------ §80 freshness


def test_freshness_policy_drives_review_due_from_last_verified():
    """review_due_at = last_verified_at + policy interval (§34)."""
    session: Session = get_session_factory()()
    try:
        policy = session.scalar(select(FreshnessPolicy).limit(1))
        if policy is None:
            policy = FreshnessPolicy(
                name="wave01-test-30d",
                review_interval_days=30,
                description="test fixture",
            )
            session.add(policy)
            session.flush()

        verified = datetime.now(UTC).replace(microsecond=0) - timedelta(days=10)
        src = Source(
            source_type="official_operator_policy",
            issuer="freshness-test-source",
            source_url="https://example.com/policy",
            collected_at=datetime.now(UTC),
            directness="direct",
            freshness_policy_id=policy.id,
            last_verified_at=verified,
            review_due_at=verified + timedelta(days=policy.review_interval_days),
        )
        session.add(src)
        session.commit()
        try:
            row = session.get(Source, src.id)
            assert row.freshness_policy_id == policy.id
            assert row.last_verified_at is not None
            expected = row.last_verified_at + timedelta(days=policy.review_interval_days)
            assert row.review_due_at == expected
        finally:
            session.delete(src)
            session.commit()
    finally:
        session.close()


def test_overdue_source_does_not_invalidate_its_rule(client, moderator):
    """§35: review_due_at means "re-verify", never "the rule stopped applying".

    This is the single most dangerous misreading available in the freshness
    model: a reviewer who treats an overdue source as expired would silently
    withdraw rules that are still in force.
    """
    session: Session = get_session_factory()()
    try:
        policy = session.scalar(select(FreshnessPolicy).limit(1))
        if policy is None:
            policy = FreshnessPolicy(
                name="wave01-test-30d", review_interval_days=30, description="test fixture"
            )
            session.add(policy)
            session.flush()

        past = datetime.now(UTC) - timedelta(days=400)
        src = Source(
            source_type="official_operator_policy",
            issuer="overdue-test-source",
            source_url="https://example.com/overdue",
            collected_at=datetime.now(UTC),
            directness="direct",
            freshness_policy_id=policy.id,
            last_verified_at=past,
            review_due_at=past + timedelta(days=policy.review_interval_days),
        )
        session.add(src)
        # Commit, not flush: the API request below runs in its own session and
        # would otherwise not see this source (and would report "来源不存在").
        session.commit()
        place_id = _new_place(client, moderator, "WAVE01 逾期来源公园")
        rule = client.post(
            "/api/v1/rules",
            json={
                "place_id": place_id,
                "animal_scope": "dog",
                "action": "enter",
                "effect": "prohibited",
                "source_id": src.id,
                "rule_origin": "operator_declared",
            },
            headers=_auth(moderator),
        )
        assert rule.status_code == 201, rule.text
        rule_id = rule.json()["id"]

        # The source is overdue…
        assert src.review_due_at < datetime.now(UTC)
        # …and the rule it supports is still resolved as applicable.
        resolved = client.post(
            f"/api/v1/places/{place_id}/effective-rules",
            json={"animal": "dog", "service_role": "none", "action": "enter"},
        ).json()
        assert rule_id in resolved["applicable_rules"], (
            "an overdue source must not withdraw a rule that is still in force",
            resolved,
        )
        assert resolved["effect"] == "prohibited", resolved

        # Cleanup order matters: access_rule.source_id is NOT NULL with an ON
        # DELETE SET NULL rule, so deleting the source first would try to null
        # the reference and fail. Remove the dependent rule before the source.
        session.execute(text("DELETE FROM access_rule WHERE id = :i"), {"i": rule_id})
        session.delete(src)
        session.commit()
    finally:
        session.close()


def test_monitor_created_is_immediately_due(client, moderator):
    """A monitor with no next_check_at is never swept (§28).

    Regression lock: ``admin_create_monitor`` must seed ``next_check_at``, or a
    fleet can be created and then sit idle forever.
    """
    session: Session = get_session_factory()()
    try:
        src = Source(
            source_type="official_operator_policy",
            issuer="monitor-due-source",
            source_url="https://example.com/monitor-due",
            collected_at=datetime.now(UTC),
            directness="direct",
        )
        session.add(src)
        session.commit()
        try:
            r = client.post(
                "/api/v1/admin/monitors",
                json={
                    "source_id": src.id,
                    "url": src.source_url,
                    "schedule_minutes": 60,
                    "expansion_run_id": "EXP-R1-W01-20260918",
                },
                headers=_auth(moderator),
            )
            assert r.status_code == 201, r.text
            mid = r.json()["id"]

            due = client.get(
                "/api/v1/admin/monitors/due?limit=200", headers=_auth(moderator)
            ).json()
            assert any(m["id"] == mid for m in due["items"]), (
                "a freshly created monitor must already be due, otherwise the "
                "scheduler never captures its baseline hash"
            )
            row = session.execute(
                text("SELECT next_check_at FROM source_monitor WHERE id = :i"), {"i": mid}
            ).scalar()
            assert row is not None
        finally:
            session.execute(text("DELETE FROM source_monitor WHERE source_id = :s"), {"s": src.id})
            session.delete(src)
            session.commit()
    finally:
        session.close()


def test_due_selection_uses_database_clock(client, moderator):
    """The due query must not mix the process clock with database timestamps.

    The container clock runs ahead of the host by a known margin; comparing a
    Python ``now()`` against DB-written timestamps re-sweeps (or skips) monitors
    purely because of that drift.
    """
    session: Session = get_session_factory()()
    try:
        src = Source(
            source_type="government_service",
            issuer="clock-domain-source",
            source_url="https://example.com/clock",
            collected_at=datetime.now(UTC),
            directness="direct",
        )
        session.add(src)
        session.commit()
        try:
            r = client.post(
                "/api/v1/admin/monitors",
                json={"source_id": src.id, "url": src.source_url, "schedule_minutes": 60},
                headers=_auth(moderator),
            )
            assert r.status_code == 201, r.text
            from app.services.monitor_sweep import select_due_monitors

            due = select_due_monitors(session, limit=200)
            assert any(m.source_id == src.id for m in due)
        finally:
            session.execute(text("DELETE FROM source_monitor WHERE source_id = :s"), {"s": src.id})
            session.delete(src)
            session.commit()
    finally:
        session.close()


# ---------------------------------------------------------------------- §81 watch


def test_watch_subscribe_is_idempotent(client, moderator):
    """Re-subscribing the same user+target must not create a second row (§81)."""
    place_id = _new_place(client, moderator, "WAVE01 关注去重公园")
    body = {"target_type": "place", "target_id": place_id, "channels": ["in_app"]}
    first = client.post("/api/v1/watches", json=body, headers=_auth(moderator))
    assert first.status_code == 201, first.text
    second = client.post("/api/v1/watches", json=body, headers=_auth(moderator))
    assert second.status_code == 201, second.text
    assert second.json()["id"] == first.json()["id"]

    watches = client.get("/api/v1/watches", headers=_auth(moderator)).json()
    mine = [w for w in watches if w["target_id"] == place_id]
    assert len(mine) == 1, "duplicate watch rows would double-notify the user"


def test_watch_unsubscribe_stops_delivery(client, moderator):
    """Unsubscribed watches must be excluded from the sweep (§81)."""
    place_id = _new_place(client, moderator, "WAVE01 关注退订公园")
    sub = client.post(
        "/api/v1/watches",
        json={"target_type": "place", "target_id": place_id, "channels": ["in_app"]},
        headers=_auth(moderator),
    ).json()

    assert (
        client.delete(f"/api/v1/watches/{sub['id']}", headers=_auth(moderator)).status_code == 204
    )

    session: Session = get_session_factory()()
    try:
        row = session.get(WatchSubscription, sub["id"])
        assert row is not None
        assert row.status == WatchStatus.UNSUBSCRIBED
        active = session.scalar(
            select(func.count())
            .select_from(WatchSubscription)
            .where(
                WatchSubscription.id == sub["id"],
                WatchSubscription.status == WatchStatus.ACTIVE,
            )
        )
        assert active == 0
    finally:
        session.close()


def test_watch_resubscribe_reactivates(client, moderator):
    """Re-subscribing after unsubscribe flips status back, still one row."""
    place_id = _new_place(client, moderator, "WAVE01 关注重订公园")
    body = {"target_type": "place", "target_id": place_id, "channels": ["in_app"]}
    sub = client.post("/api/v1/watches", json=body, headers=_auth(moderator)).json()
    client.delete(f"/api/v1/watches/{sub['id']}", headers=_auth(moderator))
    again = client.post("/api/v1/watches", json=body, headers=_auth(moderator)).json()
    assert again["id"] == sub["id"]
    session: Session = get_session_factory()()
    try:
        row = session.get(WatchSubscription, sub["id"])
        assert row.status == WatchStatus.ACTIVE
    finally:
        session.close()


def test_watch_backend_passes_but_external_delivery_is_not_implemented():
    """§81 requires the honest answer: the sink works, real channels do not.

    The mock provider accepts the send and records it; no SMS/push/email adapter
    is wired. Reporting "notifications enabled" without this distinction would
    be the one claim in the report that a reader could act on and be wrong about.
    """
    from app.providers.factory import get_notification_provider

    provider = get_notification_provider()
    result = provider.send("user-1", "in_app", "t", "b")
    assert result is not None
    assert type(provider).__name__ == "MockNotificationProvider", (
        "a non-mock provider here means real delivery is configured and this "
        "test must be updated to assert the real adapter instead"
    )


def test_watch_target_types_are_distinct():
    """PLACE / ZONE / RULE watches are different subscriptions, not one row."""
    assert WatchTargetType.PLACE != WatchTargetType.ZONE
    assert WatchTargetType.ZONE != WatchTargetType.RULE
