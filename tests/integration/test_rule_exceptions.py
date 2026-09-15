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


def _new_place_rule(client, moderator) -> dict:
    """A fresh source + place + LEGAL dog-prohibition rule.

    Used by tests that must not inherit the module-scoped fixtures' exceptions
    (a `current` carve-out on a shared rule would leak into other tests).
    """
    suffix = uuid.uuid4().hex[:8]
    src = client.post(
        "/api/v1/sources",
        json={
            "source_type": "statute_or_regulation",
            "issuer": f"测试条例（隔离夹具 {suffix}）",
            "issuer_verification": "verified",
            "directness": "direct",
            "observed_at": "2026-09-13T00:00:00Z",
        },
        headers=_auth(moderator),
    )
    assert src.status_code == 201, src.text
    place = client.post(
        "/api/v1/places",
        json={"canonical_name": f"例外隔离商场{suffix}", "place_type": "mall"},
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

    # create the exception (guide-dog exemption from the same statute).
    # ADR-025: the proviso names 导盲犬 — it must be stored as the precise role
    # with an *exact* normalisation, not as the generic `service_dog` widening.
    exc = client.post(
        "/api/v1/admin/rule-exceptions",
        json={
            "rule_id": ids["rule_id"],
            "animal_scope": "service_dog",
            "effect": "allowed",
            "source_id": ids["source_id"],
            "source_scope_exact": "导盲犬",
            "subject_scope_normalized": "guide_dog",
            "normalization_type": "exact",
            "normative_effect": "exempt_from_prohibition",
            "holder_scope": "person_with_disability",
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


def test_guide_dog_carve_out_does_not_extend_to_other_service_roles(
    client, moderator, rule_and_source
):
    """ADR-025 at the API level: the 导盲犬 proviso governs 导盲犬 only.

    A hearing-dog query (`declared_role`) must fall back to the statutory ban —
    this is the invariant that stops ontology (GUIDE_DOG is-a SERVICE_DOG) from
    being used as a legal argument.
    """
    ids = rule_and_source
    exc = client.post(
        "/api/v1/admin/rule-exceptions",
        json={
            "rule_id": ids["rule_id"],
            "animal_scope": "service_dog",
            "effect": "allowed",
            "source_id": ids["source_id"],
            "subject_scope_normalized": "guide_dog",
            "normalization_type": "exact",
            "normative_effect": "exempt_from_prohibition",
            "holder_scope": "person_with_disability",
        },
        headers=_auth(moderator),
    )
    assert exc.status_code == 201, exc.text
    exc_id = exc.json()["id"]

    def effective(**extra):
        return client.post(
            f"/api/v1/places/{ids['place_id']}/effective-rules",
            json={"animal": "dog", "service_role": "working", **extra},
        ).json()

    assert effective()["effect"] == "allowed"  # underspecified: carve-out found
    assert effective(declared_role="guide_dog")["effect"] == "allowed"
    # the three roles the proviso does NOT name keep the statutory prohibition
    hearing = effective(declared_role="hearing_dog")
    assert hearing["effect"] == "prohibited"
    assert exc_id not in hearing["applied_exceptions"]
    assistance = effective(declared_role="assistance_dog")
    assert assistance["effect"] == "prohibited"
    assert exc_id not in assistance["applied_exceptions"]


def test_bare_service_dog_exception_without_normalisation_confers_nothing(
    client, moderator, rule_and_source
):
    """A carve-out stored as the generic `service_dog` (no declared
    normalisation) is exactly the ADR-025 widening — it must not apply until a
    reviewer re-models it."""
    ids = _new_place_rule(client, moderator)  # isolated: no shared carve-outs
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
    eff = client.post(
        f"/api/v1/places/{ids['place_id']}/effective-rules",
        json={"animal": "dog", "service_role": "working"},
    ).json()
    assert eff["effect"] == "prohibited"
    assert eff["applied_exceptions"] == []


def test_precise_subject_scope_requires_a_declared_normalisation(
    client, moderator, rule_and_source
):
    """Never guess whether a scope is a legal equivalent (ADR-025)."""
    ids = rule_and_source
    r = client.post(
        "/api/v1/admin/rule-exceptions",
        json={
            "rule_id": ids["rule_id"],
            "animal_scope": "service_dog",
            "effect": "allowed",
            "source_id": ids["source_id"],
            "subject_scope_normalized": "guide_dog",
            # normalization_type deliberately omitted
        },
        headers=_auth(moderator),
    )
    assert r.status_code == 422, r.text


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
