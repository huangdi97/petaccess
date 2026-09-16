"""Place/Zone/Geometry DTOs (design #9, #22)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    GeometryType,
    IndoorOutdoor,
    LifecycleStatus,
    PersistencePermission,
    PlaceType,
    SpatialPrecision,
    ZoneType,
)


class PlaceIn(BaseModel):
    canonical_name: str = Field(min_length=1, max_length=200)
    place_type: PlaceType
    parent_place_id: str | None = None
    operator_id: str | None = None
    canonical_address: str | None = None
    lifecycle_status: LifecycleStatus = LifecycleStatus.ACTIVE
    # WKT POINT(lng lat) in EPSG:4326, optional at creation
    location_wkt: str | None = None


class PlaceUpdate(BaseModel):
    canonical_name: str | None = Field(default=None, min_length=1, max_length=200)
    place_type: PlaceType | None = None
    operator_id: str | None = None
    canonical_address: str | None = None
    lifecycle_status: LifecycleStatus | None = None
    location_wkt: str | None = None
    # Search keys only — never a name the place is displayed under. Each entry
    # is trimmed and de-duplicated; an empty list clears the aliases.
    alias_names: list[str] | None = None

    @field_validator("alias_names")
    @classmethod
    def _clean_aliases(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        seen: dict[str, None] = {}
        for raw in value:
            alias = raw.strip()
            if not alias or len(alias) > 200:
                continue
            seen.setdefault(alias, None)
        return list(seen)


class PlaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_name: str
    place_type: PlaceType
    parent_place_id: str | None
    operator_id: str | None
    canonical_address: str | None
    lifecycle_status: LifecycleStatus
    created_at: datetime
    updated_at: datetime


class PlaceSummary(BaseModel):
    """Map card / list item: evaluation-relevant projection.

    Carries enough to disambiguate two same-brand branches without a second
    request: the branch, the address, the alias that produced the hit, and how
    much rule material (and how fresh) sits behind the place. The *verdict* is
    deliberately not here — that comes from the resolver, and duplicating it in
    a list projection is how a list and a detail page end up disagreeing.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_name: str
    place_type: PlaceType
    canonical_address: str | None
    distance_m: float | None = None
    # Parent place's name when this is a branch (e.g. a store inside a mall).
    # Named for what it *is*, not for what it usually means: the value is the
    # parent's canonical name, so calling it `branch_name` made the flagship
    # look like a branch of the branch.
    parent_place_name: str | None = None
    # Non-empty only on a `q=` search, and only when the hit came from an alias
    # rather than the canonical name — so the user can see why it matched.
    matched_alias: str | None = None
    alias_names: list[str] = Field(default_factory=list)
    # Freshness of the rule material behind this place.
    rule_count: int = 0
    last_verified_at: datetime | None = None


class ZoneIn(BaseModel):
    place_id: str
    name: str = Field(min_length=1, max_length=160)
    zone_type: ZoneType
    parent_zone_id: str | None = None
    floor_ref: str | None = Field(default=None, max_length=32)
    indoor_outdoor: IndoorOutdoor = IndoorOutdoor.UNKNOWN


class ZoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    zone_type: ZoneType | None = None
    floor_ref: str | None = None
    indoor_outdoor: IndoorOutdoor | None = None


class ZoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    place_id: str
    parent_zone_id: str | None
    name: str
    zone_type: ZoneType
    floor_ref: str | None
    indoor_outdoor: IndoorOutdoor
    created_at: datetime


class GeometryIn(BaseModel):
    place_id: str | None = None
    zone_id: str | None = None
    geometry_type: GeometryType
    # WKT geometry in EPSG:4326
    wkt: str = Field(min_length=1)
    source_id: str
    precision: SpatialPrecision = SpatialPrecision.APPROXIMATE


class GeometryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    place_id: str | None
    zone_id: str | None
    geometry_type: GeometryType
    # GeoJSON representation returned by ST_AsGeoJSON
    geojson: dict | None = None
    source_id: str
    precision: SpatialPrecision
    coordinate_system_internal: str
    created_at: datetime


class ExternalRefIn(BaseModel):
    place_id: str
    provider: str = Field(min_length=1, max_length=40)
    external_id: str = Field(min_length=1, max_length=128)
    persistence_permission: PersistencePermission = PersistencePermission.RESTRICTED
