"""API integration tests: run against the real dockerized stack (PostGIS+Redis).

These cover the G04/G06 flows: auth, RBAC, pets, places search/nearby,
deterministic evaluation over DB rules, observations with idempotency,
watches, dispute lifecycle, admin quality/audit. Verification endpoints are
covered in test_verifications.py.
"""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def user(client):
    email = f"it-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"display_name": "集成测试用户", "email": email, "password": "passw0rd123"},
    )
    assert r.status_code == 201, r.text
    return {"token": r.json()["access_token"], "email": email}


@pytest.fixture(scope="module")
def admin(client, user):
    from app.db.session import get_session_factory
    from app.models import User

    session = get_session_factory()()
    row = session.query(User).filter(User.email == user["email"]).one()
    row.role = "admin"
    session.commit()
    session.close()
    r = client.post("/api/v1/auth/login", json={"email": user["email"], "password": "passw0rd123"})
    assert r.status_code == 200
    return {"token": r.json()["access_token"]}


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    assert client.get("/health").status_code == 200
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert "USE_GEOS" in r.json()["db"]["postgis"]


def test_pet_crud(client, user):
    r = client.post(
        "/api/v1/pets",
        json={
            "display_name": "豆豆",
            "species": "dog",
            "breed_text": "柴犬",
            "weight_kg": 9.5,
        },
        headers=_auth(user["token"]),
    )
    assert r.status_code == 201
    pet_id = r.json()["id"]
    r2 = client.get("/api/v1/pets", headers=_auth(user["token"]))
    assert any(p["id"] == pet_id for p in r2.json()["items"])
    assert client.delete(f"/api/v1/pets/{pet_id}", headers=_auth(user["token"])).status_code == 204


def test_place_search_and_nearby(client):
    r = client.get("/api/v1/places", params={"q": "星河"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert items and "星河咖啡" in items[0]["canonical_name"]
    r2 = client.get("/api/v1/places/nearby", params={"lat": 31.23, "lng": 121.47, "radius_m": 3000})
    assert r2.status_code == 200
    assert r2.json()["total"] >= 3


def test_evaluate_cafe_zones(client):
    """Design #7.1: indoor prohibited, outdoor conditional leash, service dog allowed."""
    places = client.get("/api/v1/places", params={"q": "星河"}).json()["items"]
    place_id = places[0]["id"]
    zones = client.get(f"/api/v1/places/{place_id}/zones").json()
    indoor = next(z for z in zones if z["indoor_outdoor"] == "indoor")
    outdoor = next(z for z in zones if z["indoor_outdoor"] == "outdoor")

    animal = {"species": "dog", "weight_kg": 9.5}
    r_in = client.post(
        "/api/v1/rules/evaluate",
        json={"animal": animal, "place_id": place_id, "zone_id": indoor["id"]},
    ).json()
    assert r_in["status"] == "RESTRICTED"
    r_out = client.post(
        "/api/v1/rules/evaluate",
        json={"animal": animal, "place_id": place_id, "zone_id": outdoor["id"]},
    ).json()
    assert r_out["status"] == "CONDITIONAL"
    assert any(u["condition_type"] == "leash_required" for u in r_out["unmet_conditions"])

    r_sd = client.post(
        "/api/v1/rules/evaluate",
        json={
            "animal": {"species": "dog", "service_role": "working"},
            "place_id": place_id,
            "zone_id": indoor["id"],
        },
    ).json()
    assert r_sd["status"] == "MATCH"


def test_unknown_weight_is_unknown(client):
    """Design #12: missing required input → UNKNOWN, never guessed."""
    places = client.get("/api/v1/places", params={"q": "云栖"}).json()["items"]
    place_id = places[0]["id"]
    zones = client.get(f"/api/v1/places/{place_id}/zones").json()
    b1 = next(z for z in zones if z["floor_ref"] == "B1")
    f1 = next(z for z in zones if z["floor_ref"] == "1F")
    # B1 prohibited regardless
    r_b1 = client.post(
        "/api/v1/rules/evaluate",
        json={
            "animal": {"species": "dog", "weight_kg": 9.5},
            "place_id": place_id,
            "zone_id": b1["id"],
        },
    ).json()
    assert r_b1["status"] == "RESTRICTED"
    # 1F needs carrier/stroller (obligations) → CONDITIONAL
    r_f1 = client.post(
        "/api/v1/rules/evaluate",
        json={
            "animal": {"species": "dog", "weight_kg": 9.5},
            "place_id": place_id,
            "zone_id": f1["id"],
        },
    ).json()
    assert r_f1["status"] == "CONDITIONAL"


def test_observation_idempotent_and_rate_limited_flow(client, user):
    places = client.get("/api/v1/places", params={"q": "青岚"}).json()["items"]
    place_id = places[0]["id"]
    body = {
        "place_id": place_id,
        "occurred_at": datetime.now(UTC).isoformat(),
        "occurred_precision": "same_day",
        "animal_scope": "dog",
        "observed_action": "enter",
        "staff_action": "no_interaction_observed",
        "place_confidence": "confirmed_on_site",
    }
    key = f"it-obs-{uuid.uuid4().hex[:8]}"
    r1 = client.post(
        "/api/v1/observations", json=body, headers={**_auth(user["token"]), "Idempotency-Key": key}
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/v1/observations", json=body, headers={**_auth(user["token"]), "Idempotency-Key": key}
    )
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]
    # withdraw own observation
    r3 = client.post(
        f"/api/v1/observations/{r1.json()['id']}/withdraw", headers=_auth(user["token"])
    )
    assert r3.status_code == 200


def test_rbac_requires_auth(client):
    assert client.get("/api/v1/pets").status_code == 401
    assert client.get("/api/v1/admin/audit").status_code == 401
    # authenticated user without moderator role → 403

    email = f"rbac-{uuid.uuid4().hex[:8]}@example.com"
    tok = client.post(
        "/api/v1/auth/register",
        json={"display_name": "RBAC", "email": email, "password": "passw0rd123"},
    ).json()["access_token"]
    assert client.get("/api/v1/admin/audit", headers=_auth(tok)).status_code == 403


def test_dispute_lifecycle(client, user, admin):
    """Design #26 flow: submit → counter → resolve, audited."""
    places = client.get("/api/v1/places", params={"q": "青岚"}).json()["items"]
    place_id = places[0]["id"]
    rules = client.get(f"/api/v1/places/{place_id}/rules").json()["items"]
    target = next(r for r in rules if r["status"] == "current")
    r_sub = client.post(
        "/api/v1/disputes",
        json={
            "target_type": "access_rule",
            "target_id": target["id"],
            "reason_code": "rule_inaccurate",
            "notice_text": "集成测试异议",
        },
        headers=_auth(user["token"]),
    )
    assert r_sub.status_code == 201, r_sub.text
    case_id = r_sub.json()["id"]
    r_counter = client.post(
        f"/api/v1/disputes/{case_id}/counter",
        json={"counter_statement": "管理方回复"},
        headers=_auth(admin["token"]),
    )
    assert r_counter.status_code == 200
    r_res = client.post(
        f"/api/v1/disputes/{case_id}/resolve",
        json={"resolution": "rule_restored", "resolution_note": "测试办结"},
        headers=_auth(admin["token"]),
    )
    assert r_res.status_code == 200
    assert r_res.json()["status"] == "resolved"
    # audit trail captured the flow
    audit = client.get(
        "/api/v1/admin/audit", params={"target_type": "dispute_case"}, headers=_auth(admin["token"])
    ).json()
    assert audit["total"] >= 1


def test_watch_subscribe_unsubscribe(client, user):
    places = client.get("/api/v1/places", params={"q": "松风"}).json()["items"]
    place_id = places[0]["id"]
    r = client.post(
        "/api/v1/watches",
        json={"target_type": "place", "target_id": place_id},
        headers=_auth(user["token"]),
    )
    assert r.status_code == 201
    wid = r.json()["id"]
    assert client.delete(f"/api/v1/watches/{wid}", headers=_auth(user["token"])).status_code == 204


def test_ai_mock_endpoints(client, user):
    # mock vision: deterministic suggestion, requires confirmation
    r = client.post(
        "/api/v1/ai/pet-vision",
        files={"image": ("pet.png", b"\x89PNG fake-bytes", "image/png")},
        headers=_auth(user["token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["requires_user_confirmation"] is True
    assert body["species"] in ("dog", "cat")
    r2 = client.post(
        "/api/v1/ai/parse-query",
        json={"text": "周六晚上带 9kg 柴犬去商场"},
        headers=_auth(user["token"]),
    )
    assert r2.status_code == 200
    assert r2.json()["animal"]["species"] == "dog"
