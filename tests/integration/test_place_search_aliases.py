"""Place search: alias matching and same-brand disambiguation.

The failure this guards is silent, and it is the worst one this product can
have. `GET /places?q=` used to match `canonical_name` only, so searching a
former name or a brand short form returned an empty list — and an empty list
reads as 「这里没有规则」, which is exactly the thing users come here to avoid.
A miss is indistinguishable from a "nothing to declare" on screen, so the miss
itself has to be a test failure.

Two properties are asserted:

1. An alias hit returns the place *and* names the alias it matched, so a place
   the user never named still explains why it came back.
2. Two branches of one brand return two labelled rows, never one ambiguous row.

Fixtures are created and removed by this module. `run_demo_seed` is not
idempotent, so tests must not depend on it, and they must not leave residue in
the development database either — a previous round of this suite left 45 places
behind by committing its fixtures.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.session import get_session_factory
from app.main import app
from app.models import Place

TAG = "别名测试"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def branches():
    """One brand, two branches, aliases on both. Removed on teardown."""
    session = get_session_factory()()
    flagship = Place(
        id=str(uuid.uuid4()),
        canonical_name=f"{TAG}·旗舰店",
        place_type="cafe",
        canonical_address=f"{TAG}主街 1 号",
        alias_names=[f"{TAG}咖啡", f"{TAG}老街旧址"],
    )
    sibling = Place(
        id=str(uuid.uuid4()),
        canonical_name=f"{TAG}·分店",
        place_type="cafe",
        canonical_address=f"{TAG}副街 2 号",
        alias_names=[f"{TAG}咖啡"],
    )
    session.add_all([flagship, sibling])
    session.flush()
    sibling.parent_place_id = flagship.id
    session.commit()
    ids = (flagship.id, sibling.id)
    session.close()
    try:
        yield ids
    finally:
        cleanup = get_session_factory()()
        cleanup.execute(delete(Place).where(Place.id.in_(ids)))
        cleanup.commit()
        cleanup.close()


def test_alias_hit_returns_the_place(client, branches):
    """Searching the old name must find the place, not an empty list."""
    flagship, _ = branches
    r = client.get("/api/v1/places", params={"q": f"{TAG}老街旧址"})
    assert r.status_code == 200, r.text
    ids = [i["id"] for i in r.json()["items"]]
    assert flagship in ids, "an alias-only match returned nothing"


def test_alias_hit_reports_which_alias_matched(client, branches):
    """The user never typed the canonical name, so the row must say why it is here."""
    r = client.get("/api/v1/places", params={"q": f"{TAG}老街旧址"})
    hit = next(i for i in r.json()["items"] if i["canonical_name"].endswith("旗舰店"))
    assert hit["matched_alias"] == f"{TAG}老街旧址"
    # The canonical name is still the name — an alias never replaces it.
    assert hit["canonical_name"].startswith(TAG)


def test_canonical_hit_reports_no_alias(client, branches):
    """A normal hit must not claim to have matched through an alias."""
    r = client.get("/api/v1/places", params={"q": f"{TAG}·旗舰店"})
    hit = next(i for i in r.json()["items"] if i["canonical_name"].endswith("旗舰店"))
    assert hit["matched_alias"] is None


def test_same_brand_returns_both_branches_labeled(client, branches):
    """Two branches, two rows, each identifiable by branch and address.

    Returning one row here would be worse than returning none: the user would
    read a branch's rules as the whole brand's rules.
    """
    flagship, sibling = branches
    r = client.get("/api/v1/places", params={"q": f"{TAG}咖啡"})
    assert r.status_code == 200, r.text
    items = {i["id"]: i for i in r.json()["items"]}
    assert flagship in items and sibling in items, "same-brand search collapsed the branches"

    assert items[flagship]["canonical_address"] != items[sibling]["canonical_address"]
    assert items[sibling]["parent_place_name"] == f"{TAG}·旗舰店"
    # The flagship is the parent, so it must not claim to belong to itself.
    assert items[flagship]["parent_place_name"] is None


def test_results_carry_freshness_and_rule_material(client, branches):
    """Every row can state how much rule material exists and how fresh it is."""
    r = client.get("/api/v1/places", params={"q": f"{TAG}咖啡"})
    for item in r.json()["items"]:
        assert "rule_count" in item
        assert "last_verified_at" in item
        assert isinstance(item["rule_count"], int)


def test_empty_query_still_lists_places(client, branches):
    """A blank `q` is not a search: it must not be filtered down to nothing."""
    r = client.get("/api/v1/places", params={"limit": 5})
    assert r.status_code == 200, r.text
    assert r.json()["total"] > 0
    for item in r.json()["items"]:
        assert item["matched_alias"] is None


def test_no_match_is_empty_and_matched_alias_is_absent(client):
    """A genuine miss is still allowed to be empty — it just cannot be silent."""
    r = client.get("/api/v1/places", params={"q": "不存在的场所zzzqqq"})
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 0


def test_aliases_are_trimmed_and_deduplicated(client):
    """Admin input cleaning: blank entries dropped, duplicates collapsed.

    Uses the ORM directly because the alias shape is enforced by the schema,
    and the point is that it is enforced *before* it reaches the column.
    """
    from app.schemas.places import PlaceUpdate

    cleaned = PlaceUpdate(alias_names=["  旧名  ", "旧名", "", "   ", "简称"]).alias_names
    assert cleaned == ["旧名", "简称"]


def test_place_alias_column_defaults_to_empty_list():
    """New places start with no aliases rather than NULL."""
    session = get_session_factory()()
    try:
        row = session.scalars(select(Place).limit(1)).first()
        if row is None:
            pytest.skip("no places in this database")
        assert isinstance(row.alias_names, list)
    finally:
        session.close()
