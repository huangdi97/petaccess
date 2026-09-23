"""Place, Zone, Geometry, ExternalPlaceRef, Operator entities (design #9, #22)."""

from datetime import datetime
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin, TimestampMixin

from .enums import (
    GeometryType,
    IndoorOutdoor,
    LifecycleStatus,
    OperatorClaimStatus,
    OperatorOrgType,
    PersistencePermission,
    PlaceType,
    SpatialPrecision,
    ZoneType,
)

if TYPE_CHECKING:
    from .rule import AccessRule


class Operator(Base, PkMixin, TimestampMixin):
    __tablename__ = "operator"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    org_type: Mapped[OperatorOrgType] = mapped_column(String(32), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verification_method: Mapped[str | None] = mapped_column(String(64), nullable=True)

    places: Mapped[list["Place"]] = relationship(back_populates="operator")


class Place(Base, PkMixin, TimestampMixin):
    __tablename__ = "place"
    __table_args__ = (
        CheckConstraint("parent_place_id != id", name="parent_not_self"),
        # Denormalized representative point for PostGIS nearby queries;
        # full geometry lives in place_geometry (ADR-017).
        Index("ix_place_location_gist", "location", postgresql_using="gist"),
        # CJK-friendly fuzzy name search (pg_trgm) — created in
        # 864ffcfc7ccb as a hand-written functional index. Declared here so
        # alembic autogenerate reports no drift (F1 "Alembic no drift").
        Index(
            "ix_place_canonical_name_trgm",
            "canonical_name",
            postgresql_using="gin",
            postgresql_ops={"canonical_name": "gin_trgm_ops"},
        ),
        # JSONB alias-name lookup (a7c4e1b90d33), hand-written GIN index.
        Index("ix_place_alias_names_gin", "alias_names", postgresql_using="gin"),
    )

    canonical_name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Alternate names the public actually searches with (former name, brand
    # short form, colloquial mall name). A lookup key only: never rendered as
    # the place's name and never carrying source/verification semantics.
    # See migration a7c4e1b90d33.
    alias_names: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    place_type: Mapped[PlaceType] = mapped_column(String(32), nullable=False, index=True)
    parent_place_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="SET NULL"), nullable=True
    )
    operator_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("operator.id", ondelete="SET NULL"), nullable=True
    )
    lifecycle_status: Mapped[LifecycleStatus] = mapped_column(
        String(32), default=LifecycleStatus.ACTIVE, nullable=False, index=True
    )
    canonical_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    # geography(Point, 4326) representative point; nullable until geometry known
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True
    )

    operator: Mapped["Operator | None"] = relationship(back_populates="places")
    zones: Mapped[list["Zone"]] = relationship(back_populates="place", foreign_keys="Zone.place_id")
    rules: Mapped[list["AccessRule"]] = relationship(
        back_populates="place", foreign_keys="AccessRule.place_id"
    )


class Zone(Base, PkMixin, TimestampMixin):
    __tablename__ = "zone"

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    zone_type: Mapped[ZoneType] = mapped_column(String(32), nullable=False, index=True)
    floor_ref: Mapped[str | None] = mapped_column(String(32), nullable=True)
    indoor_outdoor: Mapped[IndoorOutdoor] = mapped_column(
        String(16), default=IndoorOutdoor.UNKNOWN, nullable=False
    )

    place: Mapped["Place"] = relationship(back_populates="zones", foreign_keys=[place_id])
    rules: Mapped[list["AccessRule"]] = relationship(
        back_populates="zone", foreign_keys="AccessRule.zone_id"
    )


class PlaceGeometry(Base, PkMixin, TimestampMixin):
    """All real spatial data lives here; supports Point/LineString/Polygon/MultiPolygon."""

    __tablename__ = "place_geometry"
    __table_args__ = (
        CheckConstraint("(place_id IS NOT NULL) OR (zone_id IS NOT NULL)", name="needs_owner"),
        Index("ix_place_geometry_geom_gist", "geom", postgresql_using="gist"),
    )

    place_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=True, index=True
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="CASCADE"), nullable=True, index=True
    )
    geometry_type: Mapped[GeometryType] = mapped_column(String(16), nullable=False)
    geom = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False), nullable=False
    )
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
    )
    precision: Mapped[SpatialPrecision] = mapped_column(
        String(16), default=SpatialPrecision.APPROXIMATE, nullable=False
    )
    coordinate_system_internal: Mapped[str] = mapped_column(
        String(16), default="EPSG:4326", nullable=False
    )


class ExternalPlaceRef(Base, PkMixin, TimestampMixin):
    """Third-party POI ids are references only, never primary keys (ADR-003)."""

    __tablename__ = "external_place_ref"
    __table_args__ = (
        Index("uq_external_ref_provider_ext", "provider", "external_id", unique=True),
    )

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    persistence_permission: Mapped[PersistencePermission] = mapped_column(
        String(16), default=PersistencePermission.RESTRICTED, nullable=False
    )
    last_resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class OperatorClaim(Base, PkMixin, TimestampMixin):
    __tablename__ = "operator_claim"
    __table_args__ = (Index("ix_operator_claim_place_status", "place_id", "status"),)

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    operator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("operator.id", ondelete="RESTRICT"), nullable=False
    )
    claimant_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[OperatorClaimStatus] = mapped_column(
        String(32), default=OperatorClaimStatus.SUBMITTED, nullable=False, index=True
    )
    verification_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_refs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
