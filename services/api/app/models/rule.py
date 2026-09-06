"""AccessRule, RuleCondition, Source entities (design #10-13, #40)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin, TimestampMixin

from .enums import (
    AnimalScope,
    Directness,
    IssuerVerification,
    RuleAction,
    RuleConditionType,
    RuleEffect,
    RuleOrigin,
    RuleStatus,
    SourceAvailability,
    SourceType,
    SpatialPrecision,
)

if TYPE_CHECKING:
    from .place import Place, Zone

CONDITION_TYPES = [e.value for e in RuleConditionType]


class Source(Base, PkMixin, TimestampMixin):
    """Multi-dimensional provenance; no single trust score (design #13, ADR-006)."""

    __tablename__ = "source"

    source_type: Mapped[SourceType] = mapped_column(String(40), nullable=False, index=True)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer_verification: Mapped[IssuerVerification] = mapped_column(
        String(20), default=IssuerVerification.UNVERIFIED, nullable=False
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_snapshot_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_availability: Mapped[SourceAvailability] = mapped_column(
        String(24), default=SourceAvailability.AVAILABLE_ONLINE, nullable=False
    )
    directness: Mapped[Directness] = mapped_column(String(16), nullable=False)
    spatial_precision: Mapped[SpatialPrecision] = mapped_column(
        String(16), default=SpatialPrecision.UNKNOWN, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    rules: Mapped[list["AccessRule"]] = relationship(back_populates="source")


class AccessRule(Base, PkMixin, TimestampMixin):
    """What a source says SHOULD happen; observations never become rules (ADR-004)."""

    __tablename__ = "access_rule"
    __table_args__ = (
        CheckConstraint("(place_id IS NOT NULL) OR (zone_id IS NOT NULL)", name="needs_owner"),
        CheckConstraint("supersedes_rule_id != id", name="supersedes_not_self"),
        Index("ix_access_rule_place_status", "place_id", "status"),
        Index("ix_access_rule_zone_status", "zone_id", "status"),
        Index("ix_access_rule_scope_action", "animal_scope", "action"),
        Index("ix_access_rule_review_due", "review_due_at"),
    )

    place_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=True, index=True
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="CASCADE"), nullable=True, index=True
    )
    animal_scope: Mapped[AnimalScope] = mapped_column(String(20), nullable=False)
    action: Mapped[RuleAction] = mapped_column(String(24), nullable=False)
    effect: Mapped[RuleEffect] = mapped_column(String(16), nullable=False)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
    )
    rule_origin: Mapped[RuleOrigin] = mapped_column(String(40), nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[RuleStatus] = mapped_column(
        String(20), default=RuleStatus.PENDING_REVIEW, nullable=False
    )
    supersedes_rule_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("access_rule.id", ondelete="SET NULL"), nullable=True
    )
    # Free text may only supplement, never drive matching (design #11)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    place: Mapped["Place | None"] = relationship(back_populates="rules", foreign_keys=[place_id])
    zone: Mapped["Zone | None"] = relationship(back_populates="rules", foreign_keys=[zone_id])
    source: Mapped["Source"] = relationship(back_populates="rules")
    conditions: Mapped[list["RuleCondition"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )


class RuleCondition(Base, PkMixin, TimestampMixin):
    """Structured condition attached to a rule (design #11).

    value semantics by condition type:
      - flags (leash_required etc.): value_flag
      - numeric (max_weight_kg etc.): value_numeric
      - windows (time_windows/date_windows/season): value_json
      - text refs (designated_entrance etc.): value_text
    """

    __tablename__ = "rule_condition"
    __table_args__ = (Index("ix_rule_condition_rule", "rule_id"),)

    rule_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("access_rule.id", ondelete="CASCADE"), nullable=False
    )
    condition_type: Mapped[RuleConditionType] = mapped_column(String(40), nullable=False)
    value_flag: Mapped[bool | None] = mapped_column(nullable=True)
    value_numeric: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    value_text: Mapped[str | None] = mapped_column(String(200), nullable=True)
    value_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    rule: Mapped["AccessRule"] = relationship(back_populates="conditions")
