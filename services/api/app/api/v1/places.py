"""Place / Zone / Geometry endpoints (design #9, #22, #23, #31).

Search: pg_trgm fuzzy + PostGIS nearby/bbox. Third-party POI ids only live in
external_place_ref — every place here is identified by platform UUID (ADR-003).
"""

import uuid

from fastapi import APIRouter, Depends, Query
from geoalchemy2 import WKTElement
from sqlalchemy import case, func, or_, select, text
from sqlalchemy.orm import Session, aliased

from app.core.audit import record_audit
from app.core.errors import NotFound
from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models import AccessRule, ExternalPlaceRef, Place, PlaceGeometry, User, Zone
from app.models.enums import UserRole
from app.schemas.common import Page
from app.schemas.places import (
    ExternalRefIn,
    GeometryIn,
    GeometryOut,
    PlaceIn,
    PlaceOut,
    PlaceSummary,
    PlaceUpdate,
    ZoneIn,
    ZoneOut,
    ZoneUpdate,
)

router = APIRouter(tags=["places"])
admin = APIRouter(tags=["admin:places"])


# --- public read endpoints ---


def _disambiguation_projection():
    """Correlated columns that let one list row stand on its own.

    Kept as a single projected select rather than a property on `Place` so the
    extra subqueries only cost anything on the endpoints that need them.
    """
    parent = aliased(Place)
    parent_place_name = (
        select(parent.canonical_name)
        .where(parent.id == Place.parent_place_id)
        .scalar_subquery()
        .label("parent_place_name")
    )
    rule_count = (
        select(func.count(AccessRule.id))
        .where(AccessRule.place_id == Place.id, AccessRule.status == "current")
        .scalar_subquery()
        .label("rule_count")
    )
    last_verified_at = (
        select(func.max(AccessRule.last_verified_at))
        .where(AccessRule.place_id == Place.id, AccessRule.status == "current")
        .scalar_subquery()
        .label("last_verified_at")
    )
    return parent_place_name, rule_count, last_verified_at


def _search_order(q: str, rule_count, last_verified_at):
    """Rank a name search the way the question was asked.

    Plain alphabetical ordering was not neutral in practice: it put a brand-new
    branch with zero rules above the verified flagship, so the first thing the
    user saw was "尚未收录规则" when the very next row had the answer. Three
    tiers, each only breaking ties the previous one left open:

      1. match quality — exact canonical name, then prefix, then substring,
         then alias-only hits;
      2. can it answer — a place with current rules outranks one without;
      3. freshness — newer `last_verified_at` first, NULLs last.

    Name is the final tiebreak so the order stays stable across pages. This
    ranks rows; it never decides what the rules mean.
    """
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    match_rank = case(
        (Place.canonical_name == q, 0),
        (Place.canonical_name.ilike(f"{escaped}%", escape="\\"), 1),
        (Place.canonical_name.ilike(f"%{escaped}%", escape="\\"), 2),
        else_=3,
    )
    has_rules = case((rule_count > 0, 0), else_=1)
    return (
        match_rank,
        has_rules,
        last_verified_at.desc().nullslast(),
        Place.canonical_name,
    )


def _matched_alias(place: Place, q: str) -> str | None:
    """Which alias produced this hit, if the canonical name did not.

    Reported back to the client so a place the user never named still explains
    itself. Fuzzy on the same rule the SQL used, mirrored here.
    """
    needle = q.casefold()
    if needle in place.canonical_name.casefold():
        return None
    for alias in place.alias_names or []:
        if needle in alias.casefold():
            return alias
    return None


def _to_summary(row, q: str | None = None) -> PlaceSummary:
    place, parent_place_name, rule_count, last_verified_at = row
    return PlaceSummary(
        id=place.id,
        canonical_name=place.canonical_name,
        place_type=place.place_type,
        canonical_address=place.canonical_address,
        parent_place_name=parent_place_name,
        matched_alias=_matched_alias(place, q) if q else None,
        alias_names=list(place.alias_names or []),
        rule_count=rule_count or 0,
        last_verified_at=last_verified_at,
    )


@router.get("/places", response_model=Page[PlaceSummary])
def list_places(
    q: str | None = Query(default=None, max_length=100, description="fuzzy name search"),
    place_type: str | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Page[PlaceSummary]:
    parent_place_name, rule_count, last_verified_at = _disambiguation_projection()
    stmt = select(Place, parent_place_name, rule_count, last_verified_at).where(
        Place.lifecycle_status == "active"
    )
    if q:
        # pg_trgm similarity + ILIKE fallback in one OR for CJK friendliness.
        # Aliases get the same treatment: a hit on a former name or a brand
        # short form is as real as a hit on the canonical name, and returning
        # nothing here would read as "this place has no rules".
        alias_hit = text(
            "EXISTS (SELECT 1 FROM jsonb_array_elements_text(place.alias_names) AS alias_name "
            "WHERE alias_name % :q OR alias_name ILIKE :like)"
        ).params(q=q, like=f"%{q}%")
        stmt = stmt.where(
            or_(
                text("place.canonical_name % :q OR place.canonical_name ILIKE :like").params(
                    q=q, like=f"%{q}%"
                ),
                alias_hit,
            )
        )
    if place_type:
        stmt = stmt.where(Place.place_type == place_type)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    order = _search_order(q, rule_count, last_verified_at) if q else (Place.canonical_name,)
    rows = db.execute(stmt.order_by(*order).limit(limit).offset(offset)).all()
    items = [_to_summary(row, q) for row in rows]
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/places/nearby", response_model=Page[PlaceSummary])
def nearby_places(
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    radius_m: int = Query(default=1000, ge=10, le=50000),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Page[PlaceSummary]:
    """PostGIS ST_DWithin nearby search ordered by distance (GIST-indexed)."""
    point = text("ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography")
    parent_place_name, rule_count, last_verified_at = _disambiguation_projection()
    base = (
        select(
            Place,
            func.ST_Distance(Place.location, point).label("distance_m"),
            parent_place_name,
            rule_count,
            last_verified_at,
        )
        .where(
            Place.lifecycle_status == "active",
            Place.location.isnot(None),
            func.ST_DWithin(Place.location, point, radius_m),
        )
        .params(lng=lng, lat=lat)
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.execute(base.order_by(text("distance_m")).limit(limit).offset(offset)).all()
    items = []
    for row in rows:
        summary = _to_summary((row[0], row[2], row[3], row[4]))
        summary.distance_m = round(float(row[1] or 0), 1)
        items.append(summary)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/places/{place_id}", response_model=PlaceOut)
def get_place(place_id: str, db: Session = Depends(get_db)) -> Place:
    place = db.get(Place, place_id)
    if place is None:
        raise NotFound("场所不存在")
    return place


@router.get("/places/{place_id}/zones", response_model=list[ZoneOut])
def list_place_zones(place_id: str, db: Session = Depends(get_db)) -> list[Zone]:
    if db.get(Place, place_id) is None:
        raise NotFound("场所不存在")
    return list(db.scalars(select(Zone).where(Zone.place_id == place_id)).all())


@router.get("/places/{place_id}/geometries", response_model=list[GeometryOut])
def list_place_geometries(place_id: str, db: Session = Depends(get_db)) -> list[GeometryOut]:
    rows = db.execute(
        select(PlaceGeometry, func.ST_AsGeoJSON(PlaceGeometry.geom).label("geojson")).where(
            PlaceGeometry.place_id == place_id
        )
    ).all()
    out = []
    for geom, geojson in rows:
        item = GeometryOut.model_validate(geom)
        item.geojson = json_loads_safe(geojson)
        out.append(item)
    return out


@router.get("/zones/{zone_id}/geometries", response_model=list[GeometryOut])
def list_zone_geometries(zone_id: str, db: Session = Depends(get_db)) -> list[GeometryOut]:
    rows = db.execute(
        select(PlaceGeometry, func.ST_AsGeoJSON(PlaceGeometry.geom).label("geojson")).where(
            PlaceGeometry.zone_id == zone_id
        )
    ).all()
    out = []
    for geom, geojson in rows:
        item = GeometryOut.model_validate(geom)
        item.geojson = json_loads_safe(geojson)
        out.append(item)
    return out


def json_loads_safe(raw: str | None) -> dict | None:
    import json

    return json.loads(raw) if raw else None


# --- admin write endpoints ---


@admin.post("/places", response_model=PlaceOut, status_code=201)
def create_place(
    body: PlaceIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Place:
    place = Place(
        canonical_name=body.canonical_name,
        place_type=body.place_type,
        parent_place_id=body.parent_place_id,
        operator_id=body.operator_id,
        canonical_address=body.canonical_address,
        lifecycle_status=body.lifecycle_status,
    )
    if body.location_wkt:
        place.location = WKTElement(body.location_wkt, srid=4326)
    db.add(place)
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="place.create",
        target_type="place",
        target_id=str(place.id),
        after_state={"canonical_name": body.canonical_name},
    )
    db.commit()
    db.refresh(place)
    return place


@admin.patch("/places/{place_id}", response_model=PlaceOut)
def update_place(
    place_id: str,
    body: PlaceUpdate,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Place:
    place = db.get(Place, place_id)
    if place is None:
        raise NotFound("场所不存在")
    before = {"canonical_name": place.canonical_name, "lifecycle_status": place.lifecycle_status}
    data = body.model_dump(exclude_unset=True)
    wkt = data.pop("location_wkt", None)
    for k, v in data.items():
        setattr(place, k, v)
    if wkt:
        place.location = WKTElement(wkt, srid=4326)
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="place.update",
        target_type="place",
        target_id=place_id,
        before_state=before,
        after_state=data,
    )
    db.commit()
    db.refresh(place)
    return place


@admin.post("/places/{place_id}/external-refs", status_code=201)
def attach_external_ref(
    place_id: str,
    body: ExternalRefIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    if db.get(Place, place_id) is None:
        raise NotFound("场所不存在")
    ref = ExternalPlaceRef(
        place_id=place_id,
        provider=body.provider,
        external_id=body.external_id,
        persistence_permission=body.persistence_permission,
        last_resolved_at=func.now(),
    )
    db.add(ref)
    db.commit()
    return {"id": ref.id, "place_id": place_id, "provider": body.provider}


@admin.post("/zones", response_model=ZoneOut, status_code=201)
def create_zone(
    body: ZoneIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Zone:
    zone = Zone(**body.model_dump())
    db.add(zone)
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="zone.create",
        target_type="zone",
        target_id=str(zone.id),
        after_state={"name": body.name, "place_id": body.place_id},
    )
    db.commit()
    db.refresh(zone)
    return zone


@admin.patch("/zones/{zone_id}", response_model=ZoneOut)
def update_zone(
    zone_id: str,
    body: ZoneUpdate,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Zone:
    zone = db.get(Zone, zone_id)
    if zone is None:
        raise NotFound("区域不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(zone, k, v)
    db.commit()
    db.refresh(zone)
    return zone


@admin.post("/geometries", response_model=GeometryOut, status_code=201)
def create_geometry(
    body: GeometryIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> GeometryOut:
    if body.place_id is None and body.zone_id is None:
        from app.core.errors import ApiError

        raise ApiError("geometry 需要 place_id 或 zone_id")
    geom = PlaceGeometry(
        id=str(uuid.uuid4()),
        place_id=body.place_id,
        zone_id=body.zone_id,
        geometry_type=body.geometry_type,
        geom=WKTElement(body.wkt, srid=4326),
        source_id=body.source_id,
        precision=body.precision,
    )
    db.add(geom)
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="geometry.create",
        target_type="place_geometry",
        target_id=str(geom.id),
        after_state={"place_id": body.place_id, "zone_id": body.zone_id},
    )
    db.commit()
    db.refresh(geom)
    row = db.execute(
        select(PlaceGeometry, func.ST_AsGeoJSON(PlaceGeometry.geom)).where(
            PlaceGeometry.id == geom.id
        )
    ).one()
    out = GeometryOut.model_validate(row[0])
    out.geojson = json_loads_safe(row[1])
    return out


def current_user_dep():
    return get_current_user
