"""``GET /places/{id}/extras`` — Place Detail sections 4/5/6 (spec §2.4).

Regression note: this endpoint shipped without a test and, against a real
database, raised ``AttributeError: type object 'AccessPath' has no attribute
'zone_id'``. The helper that scopes rows to a place assumed every model carried a
``zone_id``; ``AccessPath`` is scoped to the place only. The call executes every
branch unconditionally, so a plain 200 on any place is already enough to catch
that class of bug — the shape assertions below add the contract on top.

Needs a live PostgreSQL (ENV-01); the suite is expected to run against the real
stack now that the dependency services are up.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

EXTRAS_KEYS = {"coexistence", "amenities", "entrances", "access_paths", "event_policies"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _any_place(client) -> str:
    r = client.get("/api/v1/places", params={"limit": 1})
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    if not items:
        pytest.skip("no places seeded in this database")
    return items[0]["id"]


def test_unknown_place_is_404(client):
    r = client.get("/api/v1/places/00000000-0000-0000-0000-000000000000/extras")
    assert r.status_code == 404


def test_extras_returns_the_five_sections(client):
    """Every query branch runs, so this fails loudly if a model lacks a column."""
    r = client.get(f"/api/v1/places/{_any_place(client)}/extras")
    assert r.status_code == 200, r.text
    assert set(r.json()) == EXTRAS_KEYS
    for value in r.json().values():
        assert isinstance(value, list)


def test_extras_scopes_rows_to_the_place(client):
    """A place with no spatial extras must not inherit another place's rows."""
    r = client.get(f"/api/v1/places/{_any_place(client)}/extras")
    body = r.json()
    # rows, when present, always carry a source_id — they are sourced facts
    for section in ("coexistence", "amenities", "entrances", "access_paths"):
        for row in body[section]:
            assert row["source_id"], f"{section} row without a source"


def test_access_paths_carry_the_route_shape(client):
    """AccessPath has no zone_id; it is scoped by place and shaped by from/to."""
    r = client.get(f"/api/v1/places/{_any_place(client)}/extras")
    for path in r.json()["access_paths"]:
        assert {"id", "name", "from_node", "to_node", "source_id"} <= set(path)


def test_observations_are_never_part_of_extras(client):
    """A field record is not a venue policy (design #14) — it must not leak in."""
    r = client.get(f"/api/v1/places/{_any_place(client)}/extras")
    assert "observations" not in r.json()
    assert "rules" not in r.json()
