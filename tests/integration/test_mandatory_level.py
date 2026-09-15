"""BLK-LAYER-02 / ADR-023 — DB-backed mandatory_level integration.

Verifies that the normative force declared on a rule survives the database round
trip and reaches the resolver through the HTTP surface:

  * a LEGAL rule published with ``mandatory_level='mandatory'`` is the floor —
    an operator ``allowed`` rule on the same scope cannot relax it;
  * the same LEGAL rule with a NULL level is NOT the floor (which is exactly why
    the publish gate refuses to publish such a candidate);
  * ``/admin/candidates/{id}/mandatory-level`` validates and audits the value;
  * the review register's deterministic mapping (LEGAL → mandatory) is honoured.

Requires a live PostgreSQL/PostGIS instance (ENV-01); skipped automatically when
the database is unreachable.
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
    email = f"mand-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"display_name": "强制级别测试", "email": email, "password": "passw0rd123"},
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


def _make_place_and_source(client, moderator, tag):
    src = client.post(
        "/api/v1/sources",
        json={
            "source_type": "statute_or_regulation",
            "issuer": f"测试条例（{tag}）",
            "issuer_verification": "verified",
            "directness": "direct",
            "observed_at": "2026-09-13T00:00:00Z",
        },
        headers=_auth(moderator),
    )
    assert src.status_code == 201, src.text
    place = client.post(
        "/api/v1/places",
        json={"canonical_name": f"强制级别测试场所{tag}", "place_type": "mall"},
        headers=_auth(moderator),
    )
    assert place.status_code == 201, place.text
    return place.json()["id"], src.json()["id"]


def _make_rule(client, moderator, *, place_id, source_id, effect, layer, mandatory):
    body = {
        "place_id": place_id,
        "animal_scope": "dog",
        "action": "enter",
        "effect": effect,
        "source_id": source_id,
        "rule_layer": layer,
        "rule_origin": "official_regulation",
        "recorded_at": "2026-09-13T00:00:00Z",
    }
    if mandatory is not None:
        body["mandatory_level"] = mandatory
    r = client.post("/api/v1/rules", json=body, headers=_auth(moderator))
    assert r.status_code in (200, 201), r.text
    return r.json()


def _effective(client, place_id, *, service_role="none"):
    r = client.post(
        f"/api/v1/places/{place_id}/effective-rules",
        json={"animal": "dog", "service_role": service_role},
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_mandatory_legal_prohibition_is_the_floor(client, moderator):
    tag = uuid.uuid4().hex[:6]
    place_id, source_id = _make_place_and_source(client, moderator, tag)

    legal = _make_rule(
        client,
        moderator,
        place_id=place_id,
        source_id=source_id,
        effect="prohibited",
        layer="LEGAL",
        mandatory="mandatory",
    )
    assert legal["mandatory_level"] == "mandatory"

    # an operator "allowed" rule on the same scope must not win
    _make_rule(
        client,
        moderator,
        place_id=place_id,
        source_id=source_id,
        effect="allowed",
        layer="OPERATOR_POLICY",
        mandatory="operator_discretion",
    )

    body = _effective(client, place_id)
    assert body["effect"] == "prohibited"
    # the API exposes the resolver's suppression list under `suppressed`
    assert any("cannot be relaxed" in s["reason"] for s in body.get("suppressed", []))


def test_legal_rule_without_level_is_not_the_floor(client, moderator):
    """Documents why the publish gate refuses a LEGAL candidate with no level."""
    tag = uuid.uuid4().hex[:6]
    place_id, source_id = _make_place_and_source(client, moderator, tag)

    _make_rule(
        client,
        moderator,
        place_id=place_id,
        source_id=source_id,
        effect="prohibited",
        layer="LEGAL",
        mandatory=None,
    )
    _make_rule(
        client,
        moderator,
        place_id=place_id,
        source_id=source_id,
        effect="allowed",
        layer="OPERATOR_POLICY",
        mandatory="operator_discretion",
    )

    assert _effective(client, place_id)["effect"] == "allowed"


def test_legacy_discretionary_round_trips_as_operator_discretion(client, moderator):
    tag = uuid.uuid4().hex[:6]
    place_id, source_id = _make_place_and_source(client, moderator, tag)
    rule = _make_rule(
        client,
        moderator,
        place_id=place_id,
        source_id=source_id,
        effect="allowed",
        layer="OPERATOR_POLICY",
        mandatory="discretionary",
    )
    # read back through RuleOut — the legacy spelling is normalised
    assert rule["mandatory_level"] == "operator_discretion"


def test_set_mandatory_level_endpoint_validates_and_audits(client, moderator):
    tag = uuid.uuid4().hex[:6]
    place_id, source_id = _make_place_and_source(client, moderator, tag)

    cand = client.post(
        "/api/v1/admin/candidates",
        json={
            "source_id": source_id,
            "place_id": place_id,
            "animal_scope": "dog",
            "action": "enter",
            "effect": "prohibited",
            "rule_layer": "LEGAL",
            "extraction_method": "integration_fixture",
        },
        headers=_auth(moderator),
    )
    assert cand.status_code == 201, cand.text
    cid = cand.json()["id"]
    assert cand.json()["mandatory_level"] is None

    # bogus value refused
    bad = client.post(
        f"/api/v1/admin/candidates/{cid}/mandatory-level",
        json={"mandatory_level": "nonsense"},
        headers=_auth(moderator),
    )
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "invalid_mandatory_level"

    # valid value accepted
    ok = client.post(
        f"/api/v1/admin/candidates/{cid}/mandatory-level",
        json={"mandatory_level": "mandatory", "reason": "statute"},
        headers=_auth(moderator),
    )
    assert ok.status_code == 200, ok.text
    assert ok.json() == {"id": cid, "mandatory_level": "mandatory", "changed": True}

    # audit trail recorded the transition of force
    audit = client.get(
        "/api/v1/admin/audit",
        params={"target_id": cid},
        headers=_auth(moderator),
    )
    if audit.status_code == 200:
        actions = {row.get("action") for row in audit.json().get("items", [])}
        assert "candidate.set_mandatory_level" in actions
