"""Contract tests for the jurisdiction-regulation list.

Regression: `GET /regulations` returned **500 for the entire list** because one
`jurisdiction_rule` row still carried `discretionary`, the pre-ADR-023 spelling
of `operator_discretion`. FastAPI validates each item separately, so a single
unconvertible value failed the whole response — the other 51 rows never reached
the client, and the admin page rendered an internal error.

The read path is now tolerant (`RegulationOut` normalises before validation) and
the stored vocabulary has been backfilled. These tests pin both halves: a legacy
row must be *served*, normalised, and must never take the list down with it.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.session import get_session_factory
from app.main import app
from app.models import JurisdictionRule
from app.models.enums import MandatoryLevel, normalize_mandatory_level

TAG = "法规测试"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def legacy_row():
    """A regulation carrying the legacy spelling, exactly as old data did."""
    from app.models import Source

    session = get_session_factory()()
    # `source_id` is a real FK, so borrow an existing source rather than
    # inventing one; creating one would leave more residue than the test needs.
    existing_source = session.scalars(select(Source.id).limit(1)).first()
    if existing_source is None:
        session.close()
        pytest.skip("no sources in this database to attach the fixture to")
    row = JurisdictionRule(
        id=str(uuid.uuid4()),
        jurisdiction_level="municipal",
        jurisdiction_id=f"legacy-test-{uuid.uuid4().hex[:8]}",
        authority=TAG,
        instrument_type="regulation",
        document_name=f"{TAG}·历史值行",
        animal_scope="ordinary_pet",
        mandatory_level="discretionary",  # the legacy spelling
        source_id=existing_source,
        status="current",
        review_status="not_reviewed",
    )
    session.add(row)
    session.commit()
    row_id = row.id
    session.close()
    try:
        yield row_id
    finally:
        cleanup = get_session_factory()()
        cleanup.execute(delete(JurisdictionRule).where(JurisdictionRule.id == row_id))
        cleanup.commit()
        cleanup.close()


def test_list_survives_a_legacy_mandatory_level(client, legacy_row):
    """The whole list must not 500 because one row uses the old spelling."""
    r = client.get("/api/v1/regulations", params={"limit": 100})
    assert r.status_code == 200, r.text


def test_legacy_row_is_served_with_the_canonical_value(client, legacy_row):
    """The row comes back — normalised, not dropped and not 500."""
    r = client.get("/api/v1/regulations", params={"limit": 100})
    assert r.status_code == 200, r.text
    match = next((i for i in r.json()["items"] if i["id"] == legacy_row), None)
    assert match is not None, "the legacy row disappeared from the response"
    assert match["mandatory_level"] == MandatoryLevel.OPERATOR_DISCRETION.value


def test_no_response_item_carries_a_legacy_value(client):
    """Whatever is in the database, the wire vocabulary stays canonical."""
    r = client.get("/api/v1/regulations", params={"limit": 100})
    assert r.status_code == 200, r.text
    seen = {i["mandatory_level"] for i in r.json()["items"]}
    assert "discretionary" not in seen
    assert seen <= {"mandatory", "advisory", "operator_discretion"}


def test_place_scoped_regulations_also_survive(client):
    """The second endpoint shares the projection, so it shares the fix."""
    places = client.get("/api/v1/places", params={"limit": 1}).json()["items"]
    if not places:
        pytest.skip("no places in this database")
    r = client.get(f"/api/v1/places/{places[0]['id']}/regulations")
    assert r.status_code == 200, r.text


def test_normaliser_maps_the_legacy_spelling():
    assert normalize_mandatory_level("discretionary") == "operator_discretion"
    assert normalize_mandatory_level("mandatory") == "mandatory"


def test_normaliser_does_not_invent_a_level():
    """An unknown level is passed through, never coerced to a real one.

    Coercing would silently upgrade a value the platform does not understand —
    the same class of error as rendering UNKNOWN as allowed.
    """
    assert normalize_mandatory_level("something_new") == "something_new"
    assert normalize_mandatory_level(None) is None
