"""Verification endpoint integration tests (PART A A3/A5).

Covers the HTTP verification flow that the G10-era docs claimed but tests
never exercised: create (rate limit, not-found, idempotent replay) + list.
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
def user(client):
    email = f"verif-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"display_name": "核验测试用户", "email": email, "password": "passw0rd123"},
    )
    assert r.status_code == 201, r.text
    return {"token": r.json()["access_token"]}


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _some_place_id(client):
    r = client.get("/api/v1/places", params={"limit": 1})
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert items, "no places seeded"
    return items[0]["id"]


def test_create_and_list_verification(client, user):
    place_id = _some_place_id(client)
    r = client.post(
        "/api/v1/verifications",
        json={"place_id": place_id, "result": "still_valid", "note": "现场仍然如此"},
        headers=_auth(user["token"]),
    )
    assert r.status_code == 201, r.text
    ev = r.json()
    assert ev["place_id"] == place_id
    assert ev["result"] == "still_valid"

    r2 = client.get(f"/api/v1/places/{place_id}/verifications")
    assert r2.status_code == 200, r2.text
    page = r2.json()
    assert page["total"] >= 1
    assert any(item["id"] == ev["id"] for item in page["items"])


def test_verification_unknown_place_is_404(client, user):
    r = client.post(
        "/api/v1/verifications",
        json={"place_id": "00000000-0000-0000-0000-0000000000ab", "result": "still_valid"},
        headers=_auth(user["token"]),
    )
    assert r.status_code == 404


def test_verification_requires_auth(client):
    place_id = _some_place_id(client)
    r = client.post(
        "/api/v1/verifications",
        json={"place_id": place_id, "result": "still_valid"},
    )
    assert r.status_code == 401


def test_verification_idempotent_replay(client, user):
    place_id = _some_place_id(client)
    key = f"it-verif-{uuid.uuid4().hex}"
    headers = {**_auth(user["token"]), "Idempotency-Key": key}
    r1 = client.post(
        "/api/v1/verifications",
        json={"place_id": place_id, "result": "still_valid"},
        headers=headers,
    )
    assert r1.status_code == 201, r1.text
    r2 = client.post(
        "/api/v1/verifications",
        json={"place_id": place_id, "result": "still_valid"},
        headers=headers,
    )
    assert r2.status_code == 201, r2.text
    assert r1.json()["id"] == r2.json()["id"]


def test_verification_rate_limited(client, user):
    from app.core.config import get_settings

    place_id = _some_place_id(client)
    max_calls = get_settings().contribution_rate_max
    codes = []
    for _ in range(max_calls + 1):
        r = client.post(
            "/api/v1/verifications",
            json={"place_id": place_id, "result": "still_valid"},
            headers=_auth(user["token"]),
        )
        codes.append(r.status_code)
        if r.status_code == 429:
            break
    assert 429 in codes, f"expected 429 within {max_calls + 1} calls, got {codes[-5:]}"
