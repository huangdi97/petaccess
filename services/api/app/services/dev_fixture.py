"""DEV_FIXTURE_MODE — demo-only fixture data for development / test / visual runs.

Purpose
-------
A developer or a visual-regression run needs to see the designed Home / Search
pages populated even when the live database has zero published places. This
module serves a small, clearly-labelled fixture dataset from the API layer
(never from the database — nothing is seeded into Postgres).

Fail-closed contract (V020 goal §H / isolation suite)
-----------------------------------------------------
The mode is active ONLY when:

  * ``DEV_FIXTURE_MODE`` is truthy in the environment, AND
  * ``APP_ENV`` is NOT production / prod / staging, AND
  * the classified database role is NOT PRODUCTION.

If any of those conditions fails, the mode is forced OFF — production can never
receive fixture payloads, even if somebody sets the env var by mistake. The
isolation suite (``tests/isolation/test_production_fail_closed.py``) asserts
this exactly.

The dataset is deliberately small and clearly fictional (names carry
``·演示``), so a fixture place can never be mistaken for a governed record.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.config import Settings, get_settings
from app.db.safety import DatabaseRole, classify_database_name, database_name_from_url
from app.models.enums import LifecycleStatus, PlaceType
from app.schemas.places import PlaceOut, PlaceSummary

#: Fixed fixture ids — stable across runs so visual baselines are reproducible.
_FIXTURE_PLACES: tuple[dict[str, object], ...] = (
    {
        "id": "00000000-0000-0000-0000-00000000f001",
        "canonical_name": "滨江公园 · 演示",
        "place_type": "park",
        "canonical_address": "上海市 · 滨江大道 100 号",
        "latitude": 31.2338,
        "longitude": 121.4936,
        "rule_count": 3,
        "last_verified_at": "2026-09-01T08:00:00Z",
    },
    {
        "id": "00000000-0000-0000-0000-00000000f002",
        "canonical_name": "栖霞咖啡 · 演示分店",
        "place_type": "cafe",
        "canonical_address": "上海市 · 栖霞路 45 号",
        "latitude": 31.2392,
        "longitude": 121.4864,
        "rule_count": 1,
        "last_verified_at": "2026-09-05T10:30:00Z",
    },
    {
        "id": "00000000-0000-0000-0000-00000000f003",
        "canonical_name": "云栖中心 · 演示商场",
        "place_type": "mall",
        "canonical_address": "上海市 · 云栖路 88 号",
        "latitude": 31.2259,
        "longitude": 121.4768,
        "rule_count": 2,
        "last_verified_at": "2026-09-10T12:00:00Z",
    },
)


def _role_for(settings: Settings) -> DatabaseRole:
    """Classify the configured database without ever connecting."""
    name = database_name_from_url(settings.database_url)
    return classify_database_name(name)


def dev_fixture_active(settings: Settings | None = None) -> bool:
    """Fail-closed gate: fixture mode is a dev/test/visual affordance only."""
    s = settings or get_settings()

    if s.app_env.strip().lower() in {"production", "prod", "staging"}:
        return False
    if not s.dev_fixture_mode:
        return False
    return _role_for(s) is not DatabaseRole.PRODUCTION


def fixture_place_summaries(q: str | None = None) -> list[PlaceSummary]:
    """Build PlaceSummary rows from the fixture dataset (never touches the DB)."""
    out: list[PlaceSummary] = []
    for row in _FIXTURE_PLACES:
        name = str(row["canonical_name"])
        if q and q.casefold() not in name.casefold():
            continue
        out.append(
            PlaceSummary(
                id=str(row["id"]),
                canonical_name=name,
                place_type=str(row["place_type"]),
                canonical_address=str(row["canonical_address"]) or None,
                latitude=float(str(row["latitude"])),
                longitude=float(str(row["longitude"])),
                parent_place_name=None,
                matched_alias=None,
                alias_names=[],
                rule_count=int(str(row["rule_count"])),
                last_verified_at=datetime.fromisoformat(str(row["last_verified_at"])).replace(
                    tzinfo=UTC
                ),
            )
        )
    return out


def is_fixture_place_id(place_id: str) -> bool:
    return any(str(row["id"]) == place_id for row in _FIXTURE_PLACES)


def fixture_place_out(place_id: str) -> PlaceOut | None:
    """A PlaceOut payload for a fixture id, else None."""
    for row in _FIXTURE_PLACES:
        if str(row["id"]) != place_id:
            continue
        now = datetime.now(UTC)
        return PlaceOut(
            id=str(row["id"]),
            canonical_name=str(row["canonical_name"]),
            place_type=PlaceType(str(row["place_type"])),
            parent_place_id=None,
            operator_id=None,
            canonical_address=str(row["canonical_address"]) or None,
            lifecycle_status=LifecycleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
    return None


__all__ = [
    "dev_fixture_active",
    "fixture_place_summaries",
    "is_fixture_place_id",
    "fixture_place_out",
]
