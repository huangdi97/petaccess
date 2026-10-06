"""Verification endpoint integration tests (PART A A3/A5).

Covers the HTTP verification flow that the G10-era docs claimed but tests
never exercised: create (rate limit, not-found, idempotent replay) + list.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from sqlalchemy import select

from app.db.session import get_session_factory
from app.main import app
from app.models import AccessRule


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


def test_user_confirmation_does_not_refresh_governed_rule_freshness(client, user):
    factory = get_session_factory()
    with factory() as db:
        rule = db.scalars(
            select(AccessRule).where(AccessRule.status == "current").limit(1)
        ).first()
        assert rule is not None
        rule_id = rule.id
        place_id = rule.place_id
        before = rule.last_verified_at
        assert place_id

    response = client.post(
        "/api/v1/verifications",
        json={
            "place_id": place_id,
            "rule_id": rule_id,
            "event_type": "rule_confirmed",
            "result": "still_valid",
            "note": "用户现场确认，仅作为待治理证据。",
        },
        headers=_auth(user["token"]),
    )
    assert response.status_code == 201, response.text

    with factory() as db:
        refreshed = db.get(AccessRule, rule_id)
        assert refreshed is not None
        assert refreshed.last_verified_at == before


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


def test_place_correction_is_not_exposed_in_public_verification_feed(client, user):
    place_id = _some_place_id(client)
    created = client.post(
        "/api/v1/verifications",
        json={
            "place_id": place_id,
            "event_type": "place_correction",
            "result": "uncertain",
            "note": "地址楼层需要人工复核",
        },
        headers=_auth(user["token"]),
    )
    assert created.status_code == 201, created.text
    correction_id = created.json()["id"]

    public = client.get(f"/api/v1/places/{place_id}/verifications")
    assert public.status_code == 200, public.text
    assert all(item["id"] != correction_id for item in public.json()["items"])


def test_place_correction_queue_requires_moderator(client, user):
    response = client.get(
        "/api/v1/admin/place-corrections",
        headers=_auth(user["token"]),
    )
    assert response.status_code == 403


def test_signage_evidence_is_not_exposed_before_rule_review(client, user):
    place_id = _some_place_id(client)
    created = client.post(
        "/api/v1/verifications",
        json={
            "place_id": place_id,
            "event_type": "signage_uploaded",
            "result": "uncertain",
            "note": "规则牌证据待人工审核",
        },
        headers=_auth(user["token"]),
    )
    assert created.status_code == 201, created.text
    event_id = created.json()["id"]

    public = client.get(f"/api/v1/places/{place_id}/verifications")
    assert public.status_code == 200, public.text
    assert all(item["id"] != event_id for item in public.json()["items"])


