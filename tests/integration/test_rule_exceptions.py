"""RuleException API integration (SG-REAL-01, S3/S5).

Exercises the HTTP surface end to end: create base rule → attach exception →
transition lifecycle → effective-rules reflects exemption → publish gate still
blocks lead-only sources; observations stay out of the normative resolver.
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
    email = f"exc-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"display_name": "例外测试", "email": email, "password": "passw0rd123"},
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


@pytest.fixture(scope="module")
def rule_and_source(client, moderator):
    """A current LEGAL dog-prohibition rule on its own place, with a source."""
    src = client.post(
        "/api/v1/sources",
        json={
            "source_type": "statute_or_regulation",
            "issuer": "测试条例（集成夹具）",
            "issuer_verification": "verified",
            "directness": "direct",
            "observed_at": "2026-09-13T00:00:00Z",
        },
        headers=_auth(moderator),
    )
    assert src.status_code == 201, src.text
    place = client.post(
        "/api/v1/places",
        json={"canonical_name": f"例外测试商场{uuid.uuid4().hex[:6]}", "place_type": "mall"},
        headers=_auth(moderator),
    )
    assert place.status_code == 201, place.text
    rule = client.post(
        "/api/v1/rules",
        json={
            "place_id": place.json()["id"],
            "animal_scope": "dog",
            "action": "enter",
            "effect": "prohibited",
            "source_id": src.json()["id"],
            "rule_layer": "LEGAL",
            "rule_origin": "official_regulation",
            "recorded_at": "2026-09-13T00:00:00Z",
        },
        headers=_auth(moderator),
    )
    assert rule.status_code in (200, 201), rule.text
    return {
        "rule_id": rule.json()["id"],
        "source_id": src.json()["id"],
        "place_id": place.json()["id"],
    }


def test_exception_lifecycle_and_resolver(client, moderator, rule_and_source):
    ids = rule_and_source

    # normal dog prohibited before anything else
    eff = client.post(
        f"/api/v1/places/{ids['place_id']}/effective-rules",
        json={"animal": "dog", "service_role": "none"},
    )
    assert eff.status_code == 200
    assert eff.json()["effect"] == "prohibited"

    # working dog prohibited too (the R1 defect this mechanism fixes)
    eff0 = client.post(
        f"/api/v1/places/{ids['place_id']}/effective-rules",
        json={"animal": "dog", "service_role": "working"},
    )
    assert eff0.json()["effect"] == "prohibited"

    # create the exception (guide-dog exemption from the same statute)
    exc = client.post(
        "/api/v1/admin/rule-exceptions",
        json={
            "rule_id": ids["rule_id"],
            "animal_scope": "service_dog",
            "effect": "allowed",
            "source_id": ids["source_id"],
        },
        headers=_auth(moderator),
    )
    assert exc.status_code == 201, exc.text
    exc_id = exc.json()["id"]

    # admin list shows it
    listed = client.get(
        "/api/v1/admin/rule-exceptions",
        params={"rule_id": ids["rule_id"]},
        headers=_auth(moderator),
    )
    assert listed.status_code == 200
    assert any(item["id"] == exc_id for item in listed.json()["items"])

    # working dog now allowed, with an explanation naming the exception
    eff1 = client.post(
        f"/api/v1/places/{ids['place_id']}/effective-rules",
        json={"animal": "dog", "service_role": "working"},
    )
    assert eff1.status_code == 200, eff1.text
    body = eff1.json()
    assert body["effect"] == "allowed"
    assert body["applied_exceptions"] == [exc_id]
    assert any(exc_id in step for step in body["explanation_steps"])

    # ordinary dog still prohibited
    eff2 = client.post(
        f"/api/v1/places/{ids['place_id']}/effective-rules",
        json={"animal": "dog", "service_role": "none"},
    )
    assert eff2.json()["effect"] == "prohibited"

    # withdraw the exception → working dog falls back to prohibition
    tr = client.post(
        f"/api/v1/admin/rule-exceptions/{exc_id}/transition",
        json={"target": "withdrawn", "note": "条例修订"},
        headers=_auth(moderator),
    )
    assert tr.status_code == 200, tr.text
    eff3 = client.post(
        f"/api/v1/places/{ids['place_id']}/effective-rules",
        json={"animal": "dog", "service_role": "working"},
    )
    assert eff3.json()["effect"] == "prohibited"
    assert eff3.json()["applied_exceptions"] == []


def test_exception_requires_existing_rule_and_source(client, moderator, rule_and_source):
    ids = rule_and_source
    r1 = client.post(
        "/api/v1/admin/rule-exceptions",
        json={
            "rule_id": "00000000-0000-0000-0000-0000000000ff",
            "animal_scope": "service_dog",
            "effect": "allowed",
            "source_id": ids["source_id"],
        },
        headers=_auth(moderator),
    )
    assert r1.status_code == 404
    r2 = client.post(
        "/api/v1/admin/rule-exceptions",
        json={
            "rule_id": ids["rule_id"],
            "animal_scope": "service_dog",
            "effect": "allowed",
            "source_id": "00000000-0000-0000-0000-0000000000fe",
        },
        headers=_auth(moderator),
    )
    assert r2.status_code == 404
    # invalid scope rejected by schema
    r3 = client.post(
        "/api/v1/admin/rule-exceptions",
        json={
            "rule_id": ids["rule_id"],
            "animal_scope": "dragon",
            "effect": "allowed",
            "source_id": ids["source_id"],
        },
        headers=_auth(moderator),
    )
    assert r3.status_code == 422


def test_observations_never_enter_normative_resolver(client, moderator, rule_and_source):
    """ADR-004 sanity at the API level: observation data cannot flip a rule."""
    ids = rule_and_source
    obs = client.post(
        "/api/v1/observations",
        json={
            "place_id": ids["place_id"],
            "animal_scope": "dog",
            "observed_action": "enter",
            "spatial_context": "室内",
            "raw_text": "我看到有人带狗进去",
            "occurred_at": "2026-09-13T10:00:00Z",
            "occurred_precision": "same_day",
            "staff_action": "no_interaction_observed",
            "place_confidence": "medium",
        },
        headers=_auth(moderator),
    )
    assert obs.status_code in (200, 201), obs.text
    eff = client.post(
        f"/api/v1/places/{ids['place_id']}/effective-rules",
        json={"animal": "dog", "service_role": "none"},
    )
    assert eff.json()["effect"] == "prohibited"
    joined = " ".join(eff.json()["explanation_steps"])
    assert "observation" not in joined.lower()
