"""Place/Zone/Geometry DTOs (design #9, #22)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
    """Map card / list item: evaluation-relevant projection."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_name: str
    place_type: PlaceType
    canonical_address: str | None
    distance_m: float | None = None


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
