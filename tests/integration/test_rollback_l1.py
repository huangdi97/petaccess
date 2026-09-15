"""L1 rollback: withdrawing a single AccessRule (ROLLBACK_RUNBOOK §2).

The runbook documents this as the fastest rollback layer (minute-level RTO) and
states an explicit acceptance criterion:

    "撤回后若该场所无其它规则，查询结果应回落为 UNKNOWN（**不是** allowed）"

Until now that path had no integration coverage, and the runbook named an
endpoint that does not exist (``POST /admin/rules/{id}/withdraw``). The real
capability is ``PATCH /admin/rules/{rule_id}`` with ``{"status": "withdrawn"}``,
audited as ``rule.update``. This test pins the behaviour the runbook promises so
the procedure can be followed literally during an incident.

Requires a live PostgreSQL (ENV-01).
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def moderator(client):
    email = f"rb-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"display_name": "回滚测试", "email": email, "password": "passw0rd123"},
    )
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    from app.db.session import get_session_factory
    from app.models import User

    s = get_session_factory()()
    row = s.query(User).filter(User.email == email).one()
    row.role = "moderator"
    s.commit()
    s.close()
    return {"token": token}


def _auth(m):
    return {"Authorization": f"Bearer {m['token']}"}


def _scratch_place_and_source(client, moderator, tag):
    src = client.post(
        "/api/v1/sources",
        json={
            "source_type": "statute_or_regulation",
            "issuer": f"回滚测试来源（{tag}）",
            "issuer_verification": "verified",
            "directness": "direct",
            "observed_at": "2026-09-14T00:00:00Z",
        },
        headers=_auth(moderator),
    )
    assert src.status_code == 201, src.text
    place = client.post(
        "/api/v1/places",
        json={"canonical_name": f"回滚测试场所{tag}", "place_type": "cafe"},
        headers=_auth(moderator),
    )
    assert place.status_code == 201, place.text
    return place.json()["id"], src.json()["id"]


def _create_rule(client, moderator, place_id, source_id, *, effect="allowed"):
    r = client.post(
        "/api/v1/rules",
        json={
            "place_id": place_id,
            "animal_scope": "dog",
            "action": "enter",
            "effect": effect,
            "source_id": source_id,
            "rule_layer": "OPERATOR_POLICY",
            "mandatory_level": "operator_discretion",
            "rule_origin": "official_regulation",
            "recorded_at": "2026-09-14T00:00:00Z",
        },
        headers=_auth(moderator),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _effective(client, place_id):
    r = client.post(
        f"/api/v1/places/{place_id}/effective-rules",
        json={"animal": "dog", "service_role": "none"},
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_l1_withdraw_falls_back_to_unknown_not_allowed(client, moderator):
    tag = uuid.uuid4().hex[:6]
    place_id, source_id = _scratch_place_and_source(client, moderator, tag)
    rule = _create_rule(client, moderator, place_id, source_id)

    # baseline: the rule governs
    before = _effective(client, place_id)
    assert before["effect"] == "allowed"
    assert rule["id"] in before["applicable_rules"]

    # L1 rollback — the documented capability
    r = client.patch(
        f"/api/v1/rules/{rule['id']}",
        json={"status": "withdrawn"},
        headers=_auth(moderator),
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "withdrawn"

    # the runbook's acceptance criterion: UNKNOWN, never allowed
    after = _effective(client, place_id)
    assert after["effect"] == "unknown"
    assert rule["id"] not in after["applicable_rules"]


def test_l1_withdraw_preserves_the_row_and_evidence_chain(client, moderator):
    """Withdraw is a status change, never a delete (history must survive)."""
    tag = uuid.uuid4().hex[:6]
    place_id, source_id = _scratch_place_and_source(client, moderator, tag)
    rule = _create_rule(client, moderator, place_id, source_id)

    client.patch(
        f"/api/v1/rules/{rule['id']}",
        json={"status": "withdrawn"},
        headers=_auth(moderator),
    )
    listed = client.get(f"/api/v1/places/{place_id}/rules")
    assert listed.status_code == 200, listed.text
    rows = listed.json()["items"]
    row = next((x for x in rows if x["id"] == rule["id"]), None)
    assert row is not None, "withdrawn rule must still be listed, not deleted"
    assert row["status"] == "withdrawn"
    # provenance is intact
    assert row["source_id"] == source_id


def test_l1_withdraw_is_audited(client, moderator):
    tag = uuid.uuid4().hex[:6]
    place_id, source_id = _scratch_place_and_source(client, moderator, tag)
    rule = _create_rule(client, moderator, place_id, source_id)

    client.patch(
        f"/api/v1/rules/{rule['id']}",
        json={"status": "withdrawn"},
        headers=_auth(moderator),
    )
    audit = client.get(
        "/api/v1/admin/audit",
        params={"target_id": rule["id"]},
        headers=_auth(moderator),
    )
    assert audit.status_code == 200, audit.text
    rows = audit.json()["items"]
    actions = [row.get("action") for row in rows]
    assert "rule.update" in actions, f"expected an audit trail, got {actions}"
    update_row = next(row for row in rows if row.get("action") == "rule.update")
    assert update_row["before_state"]["status"] == "current"
    assert update_row["after_state"]["status"] == "withdrawn"


def test_l1_withdraw_requires_a_moderator(client, moderator):
    tag = uuid.uuid4().hex[:6]
    place_id, source_id = _scratch_place_and_source(client, moderator, tag)
    rule = _create_rule(client, moderator, place_id, source_id)

    anon = client.patch(f"/api/v1/rules/{rule['id']}", json={"status": "withdrawn"})
    assert anon.status_code in (401, 403)
    # unchanged
    assert _effective(client, place_id)["effect"] == "allowed"


def test_l1_withdraw_of_a_missing_rule_is_404(client, moderator):
    r = client.patch(
        "/api/v1/rules/00000000-0000-0000-0000-000000000000",
        json={"status": "withdrawn"},
        headers=_auth(moderator),
    )
    assert r.status_code == 404
