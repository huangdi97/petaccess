"""User coexistence boundary over the real API (brief §8).

The boundary is the *user's own* requirement set. These tests pin three
behaviours that matter: the profile is user-scoped and replace-on-write, only
the matcher's stance vocabulary is accepted, and matching is per-item with no
total score and no coercion of missing data into a verdict.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _new_user(client, *, role: str | None = None) -> str:
    """Register a user and optionally elevate the role for place-creation."""
    email = f"bnd-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"display_name": "边界用户", "email": email, "password": "passw0rd123"},
    )
    assert r.status_code == 201, r.text
    if role is not None:
        from app.db.session import get_session_factory
        from app.models import User

        s = get_session_factory()()
        u = s.query(User).filter(User.email == email).one()
        u.role = role
        s.commit()
        s.close()
        return client.post(
            "/api/v1/auth/login", json={"email": email, "password": "passw0rd123"}
        ).json()["access_token"]
    return r.json()["access_token"]


def _auth(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}"}


def _any_place(client, tok: str) -> str:
    """Reuse a seeded place so an ordinary user needs no create permission."""
    items = client.get("/api/v1/places", params={"limit": 1}, headers=_auth(tok)).json()["items"]
    assert items, "需要至少一个已收录场所（先跑 seed --demo）"
    return items[0]["id"]


def test_default_profile_is_null_before_setup(client):
    """A user with no profile gets `profile: null`, not a 404."""
    tok = _new_user(client)
    r = client.get("/api/v1/boundary-profiles/default", headers=_auth(tok))
    assert r.status_code == 200
    assert r.json()["profile"] is None


def test_profile_round_trip(client):
    tok = _new_user(client)
    saved = client.put(
        "/api/v1/boundary-profiles/default",
        json={
            "name": "我的共处边界",
            "is_default": True,
            "preferences": [
                {"attribute": "indoor_access", "stance": "require_prohibited"},
                {"attribute": "off_leash", "stance": "avoid"},
            ],
        },
        headers=_auth(tok),
    )
    assert saved.status_code == 200, saved.text
    body = saved.json()
    assert body["name"] == "我的共处边界"
    assert {(p["attribute"], p["stance"]) for p in body["preferences"]} == {
        ("indoor_access", "require_prohibited"),
        ("off_leash", "avoid"),
    }

    fetched = client.get("/api/v1/boundary-profiles/default", headers=_auth(tok)).json()["profile"]
    assert fetched is not None
    assert fetched["id"] == body["id"]


def test_profile_write_replaces_rather_than_merges(client):
    """Clearing a stance in the UI must actually remove it server-side."""
    tok = _new_user(client)
    client.put(
        "/api/v1/boundary-profiles/default",
        json={
            "name": "v1",
            "preferences": [
                {"attribute": "indoor_access", "stance": "require_prohibited"},
                {"attribute": "off_leash", "stance": "avoid"},
            ],
        },
        headers=_auth(tok),
    )
    client.put(
        "/api/v1/boundary-profiles/default",
        json={
            "name": "v2",
            "preferences": [{"attribute": "muzzle_required", "stance": "accept"}],
        },
        headers=_auth(tok),
    )
    after = client.get("/api/v1/boundary-profiles/default", headers=_auth(tok)).json()["profile"]
    assert [p["attribute"] for p in after["preferences"]] == ["muzzle_required"]
    assert after["name"] == "v2"
    # exactly one default profile is kept, not two
    assert len(client.get("/api/v1/boundary-profiles", headers=_auth(tok)).json()["items"]) == 1


def test_unknown_stance_is_rejected(client):
    """Only the matcher's vocabulary is accepted — no silently-unknown stances."""
    tok = _new_user(client)
    for bad in ("bogus", "acceptable", "prefer_avoid", ""):
        r = client.put(
            "/api/v1/boundary-profiles/default",
            json={"name": "x", "preferences": [{"attribute": "off_leash", "stance": bad}]},
            headers=_auth(tok),
        )
        assert r.status_code == 422, f"stance {bad!r} should be rejected, got {r.status_code}"


def test_profiles_are_user_scoped(client):
    """One user's boundary must never leak into another's."""
    a = _new_user(client)
    b = _new_user(client)
    client.put(
        "/api/v1/boundary-profiles/default",
        json={
            "name": "A 的边界",
            "preferences": [{"attribute": "off_leash", "stance": "avoid"}],
        },
        headers=_auth(a),
    )
    assert (
        client.get("/api/v1/boundary-profiles/default", headers=_auth(b)).json()["profile"] is None
    )


def test_match_is_per_item_and_never_coerces_unknown(client):
    """Unrecorded attributes stay UNKNOWN; no total score is produced."""
    tok = _new_user(client)
    place_id = _any_place(client, tok)
    client.put(
        "/api/v1/boundary-profiles/default",
        json={
            "name": "边界",
            "preferences": [
                {"attribute": "indoor_access", "stance": "require_prohibited"},
                {"attribute": "dog_park_nonexistent", "stance": "prefer"},
            ],
        },
        headers=_auth(tok),
    )
    r = client.get(f"/api/v1/places/{place_id}/boundary-match", headers=_auth(tok))
    assert r.status_code == 200, r.text
    body = r.json()

    assert set(body["summary"]) == {"match", "conflict", "unknown", "note"}
    assert "无总分" in body["summary"]["note"]
    # every result carries a verdict from the closed vocabulary
    for item in body["results"]:
        assert item["verdict"] in {"MATCH", "CONFLICT", "UNKNOWN"}
        assert item["reason"]
    # an attribute the venue does not record is UNKNOWN, not CONFLICT
    unrecorded = [i for i in body["results"] if i["attribute"] == "dog_park_nonexistent"]
    assert unrecorded and unrecorded[0]["verdict"] == "UNKNOWN"


def test_match_requires_a_profile(client):
    """Without a profile the matcher cannot run and says so explicitly."""
    tok = _new_user(client)
    place_id = _any_place(client, tok)
    r = client.get(f"/api/v1/places/{place_id}/boundary-match", headers=_auth(tok))
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "no_boundary_profile"
