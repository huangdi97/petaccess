"""Operator claim → questionnaire → versioned rules E2E (GOAL #13 / Phase 8)
and contribution rate-limit / anti-abuse checks (Phase 7)."""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _register(client, name: str) -> dict:
    email = f"{name}-{uuid.uuid4().hex[:8]}@example.com"
    tok = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": name,
            "email": email,
            "password": "passw0rd123",
        },
    ).json()["access_token"]
    return {"token": tok, "email": email}


def _promote_admin(client, user: dict) -> None:
    from app.db.session import get_session_factory
    from app.models import User

    s = get_session_factory()()
    u = s.query(User).filter(User.email == user["email"]).one()
    u.role = "admin"
    s.commit()
    s.close()


def _auth(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


def test_operator_claim_full_loop(client):
    """社区创建场所 → 管理方认领 → Admin 批准 → 问卷 → operator 规则版本化
    → 用户 Observation 仍可提交且不被删除。"""
    operator = _register(client, "认领运营")
    moderator = _register(client, "复核员")
    _promote_admin(client, moderator)
    member = _register(client, "普通用户")

    mod_tok = client.post(
        "/api/v1/auth/login", json={"email": moderator["email"], "password": "passw0rd123"}
    ).json()["access_token"]
    op_tok = client.post(
        "/api/v1/auth/login", json={"email": operator["email"], "password": "passw0rd123"}
    ).json()["access_token"]

    # 1. moderator creates a place + an older operator-policy rule.
    #    Also seed a LEGAL rule in the same cell: an operator questionnaire
    #    must never supersede it.
    place = client.post(
        "/api/v1/places",
        json={
            "canonical_name": "认领演示商店",
            "place_type": "store",
            "location_wkt": "POINT(122.500 30.500)",
        },
        headers=_auth(mod_tok),
    )
    assert place.status_code == 201, place.text
    place_id = place.json()["id"]
    src = client.post(
        "/api/v1/sources",
        json={
            "source_type": "official_operator_policy",
            "issuer": "历史运营方政策",
            "directness": "direct",
        },
        headers=_auth(mod_tok),
    )
    assert src.status_code == 201
    r1 = client.post(
        "/api/v1/rules",
        json={
            "place_id": place_id,
            "animal_scope": "ordinary_pet",
            "action": "enter",
            "effect": "allowed",
            "source_id": src.json()["id"],
            "rule_origin": "operator_declared",
            "rule_layer": "OPERATOR_POLICY",
            "mandatory_level": "operator_discretion",
        },
        headers=_auth(mod_tok),
    )
    assert r1.status_code == 201
    old_operator_rule_id = r1.json()["id"]

    legal_src = client.post(
        "/api/v1/sources",
        json={
            "source_type": "statute_or_regulation",
            "issuer": "测试法定规则",
            "directness": "direct",
        },
        headers=_auth(mod_tok),
    )
    assert legal_src.status_code == 201
    legal_rule = client.post(
        "/api/v1/rules",
        json={
            "place_id": place_id,
            "animal_scope": "ordinary_pet",
            "action": "enter",
            "effect": "allowed",
            "source_id": legal_src.json()["id"],
            "rule_origin": "official_regulation",
            "rule_layer": "LEGAL",
            "mandatory_level": "mandatory",
        },
        headers=_auth(mod_tok),
    )
    assert legal_rule.status_code == 201, legal_rule.text
    legal_rule_id = legal_rule.json()["id"]

    # 2. operator registers an Operator entity via claim flow needs operator_id;
    #    create through admin places/operator path — operator entity seeded? create via API:
    #    v1 exposes no operator CRUD, so use the seeded demo operator.
    operators = client.get("/api/v1/admin/users", headers=_auth(mod_tok))
    assert operators.status_code == 200
    # find seeded operator id from claims of demo data via DB
    from app.db.session import get_session_factory
    from app.models import Operator

    s = get_session_factory()()
    op = s.query(Operator).filter(Operator.name.contains("云栖")).first()
    operator_id = op.id
    s.close()

    # 3. operator submits claim
    claim = client.post(
        "/api/v1/operator-claims",
        json={
            "place_id": place_id,
            "operator_id": operator_id,
            "verification_method": "official_domain_email",
            "evidence_refs": {"domain": "yunqi-demo.example"},
        },
        headers=_auth(op_tok),
    )
    assert claim.status_code == 201, claim.text
    claim_id = claim.json()["id"]

    mine = client.get(
        f"/api/v1/operator-claims/mine?place_id={place_id}",
        headers=_auth(op_tok),
    )
    assert mine.status_code == 200, mine.text
    assert mine.json()[0]["id"] == claim_id
    assert mine.json()[0]["status"] == "submitted"

    other_user_claims = client.get(
        f"/api/v1/operator-claims/mine?place_id={place_id}",
        headers=_auth(member["token"]),
    )
    assert other_user_claims.status_code == 200, other_user_claims.text
    assert other_user_claims.json() == []

    # 4. moderator approves → operator becomes place operator
    review = client.post(
        f"/api/v1/operator-claims/{claim_id}/review", json={"approve": True}, headers=_auth(mod_tok)
    )
    assert review.status_code == 200
    assert review.json()["status"] == "approved"
    place_after = client.get(f"/api/v1/places/{place_id}").json()
    assert place_after["operator_id"] == operator_id

    # 5. questionnaire → only matching prior OPERATOR_POLICY is versioned
    # A conditional policy without an explicit structured condition is not a
    # valid consumer transaction; reject it before any Rule write.
    invalid_conditional = client.post(
        f"/api/v1/operator-claims/{claim_id}/questionnaire",
        json={
            "answers": [
                {
                    "zone_id": None,
                    "animal_scope": "ordinary_pet",
                    "action": "enter",
                    "effect": "conditional",
                    "conditions": [],
                }
            ]
        },
        headers=_auth(op_tok),
    )
    assert invalid_conditional.status_code == 422

    q = client.post(
        f"/api/v1/operator-claims/{claim_id}/questionnaire",
        json={
            "answers": [
                {
                    "zone_id": None,
                    "animal_scope": "ordinary_pet",
                    "action": "enter",
                    "effect": "conditional",
                    "conditions": [{"condition_type": "leash_required", "value_flag": True}],
                },
                {
                    "zone_id": None,
                    "animal_scope": "service_dog",
                    "action": "enter",
                    "effect": "allowed",
                    "conditions": [],
                },
            ]
        },
        headers=_auth(op_tok),
    )
    assert q.status_code == 201, q.text
    assert len(q.json()["created_rules"]) == 2

    rules = client.get(f"/api/v1/places/{place_id}/rules").json()["items"]
    by_id = {rule["id"]: rule for rule in rules}
    current = [rule for rule in rules if rule["status"] == "current"]
    superseded = [rule for rule in rules if rule["status"] == "superseded"]

    assert by_id[old_operator_rule_id]["status"] == "superseded"
    assert by_id[legal_rule_id]["status"] == "current"
    assert by_id[legal_rule_id]["rule_layer"] == "LEGAL"

    created_ids = set(q.json()["created_rules"])
    created = [rule for rule in current if rule["id"] in created_ids]
    assert len(created) == 2
    assert all(rule["rule_origin"] == "operator_declared" for rule in created)
    assert all(rule["rule_layer"] == "OPERATOR_POLICY" for rule in created)
    assert all(rule["mandatory_level"] == "operator_discretion" for rule in created)
    assert old_operator_rule_id in {rule["id"] for rule in superseded}
    ordinary_policy = next(
        rule
        for rule in created
        if rule["animal_scope"] == "ordinary_pet" and rule["action"] == "enter"
    )
    assert ordinary_policy["supersedes_rule_id"] == old_operator_rule_id

    # 6. evaluator reflects the new operator rules
    ev = client.post(
        "/api/v1/rules/evaluate",
        json={"animal": {"species": "dog", "weight_kg": 9.5}, "place_id": place_id},
    ).json()
    assert ev["status"] == "CONDITIONAL"

    # 7. user observation still accepted; operator has NO deletion endpoint
    obs = client.post(
        "/api/v1/observations",
        json={
            "place_id": place_id,
            "occurred_at": datetime.now(UTC).isoformat(),
            "occurred_precision": "same_day",
            "animal_scope": "dog",
            "observed_action": "enter",
            "staff_action": "no_interaction_observed",
            "place_confidence": "confirmed_on_site",
        },
        headers=_auth(member["token"]),
    )
    assert obs.status_code == 201
    # operator token cannot withdraw the member's observation
    withdraw = client.post(
        f"/api/v1/observations/{obs.json()['id']}/withdraw", headers=_auth(op_tok)
    )
    assert withdraw.status_code == 403


def test_contribution_rate_limit(client):
    """Phase 7 anti-abuse: observation endpoint rate-limits per user (30/h)."""
    user = _register(client, "限流用户")
    places = client.get("/api/v1/places").json()["items"]
    place_id = places[0]["id"]
    body = {
        "place_id": place_id,
        "occurred_at": datetime.now(UTC).isoformat(),
        "occurred_precision": "same_day",
        "animal_scope": "dog",
        "observed_action": "enter",
        "staff_action": "no_interaction_observed",
        "place_confidence": "medium",
    }
    # unique idempotency keys; expect 201 until limit, then 429
    codes = []
    for _i in range(32):
        r = client.post(
            "/api/v1/observations",
            json=body,
            headers={**_auth(user["token"]), "Idempotency-Key": f"rl-{uuid.uuid4().hex}"},
        )
        codes.append(r.status_code)
    assert codes.count(201) >= 25
    assert codes[-1] == 429, f"expected final 429, got {codes[-5:]}"


def test_regulation_review_flow(client):
    """Phase 9: NOT_REVIEWED must be distinguishable; review updates audited."""
    moderator = _register(client, "法规复核")
    _promote_admin(client, moderator)
    tok = client.post(
        "/api/v1/auth/login", json={"email": moderator["email"], "password": "passw0rd123"}
    ).json()["access_token"]
    # create our own not_reviewed regulation so the test is repeatable
    src = client.post(
        "/api/v1/sources",
        json={
            "source_type": "statute_or_regulation",
            "issuer": "测试法规来源",
            "directness": "direct",
        },
        headers=_auth(tok),
    )
    assert src.status_code == 201
    reg = client.post(
        "/api/v1/regulations",
        json={
            "jurisdiction_level": "municipal",
            "jurisdiction_id": "test-city",
            "authority": "测试机关",
            "instrument_type": "regulation",
            "document_name": "测试条例",
            "animal_scope": "dog",
            "source_id": src.json()["id"],
            "review_status": "not_reviewed",
        },
        headers=_auth(tok),
    )
    assert reg.status_code == 201, reg.text
    target = reg.json()
    assert target["review_status"] == "not_reviewed"
    r = client.post(
        f"/api/v1/regulations/{target['id']}/review",
        json={"review_status": "no_explicit_rule_found"},
        headers=_auth(tok),
    )
    assert r.status_code == 200
    assert r.json()["review_status"] == "no_explicit_rule_found"
