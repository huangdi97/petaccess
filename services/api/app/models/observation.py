"""ObservationClaim and VerificationEvent entities (design #14, #15, #17).

Observations are parallel facts: they coexist with rules but never mutate them
and never feed the deterministic evaluator (ADR-004).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin, TimestampMixin

from .enums import (
    AnimalScope,
    ObservationDisputeStatus,
    ObservationStaffAction,
    OccurredPrecision,
    PlaceConfidence,
    RuleAction,
    VerificationEventType,
    VerificationResult,
)

if TYPE_CHECKING:
    from .user import User


class ObservationClaim(Base, PkMixin, TimestampMixin):
    __tablename__ = "observation_claim"
    __table_args__ = (
        Index("ix_observation_place_reported", "place_id", "reported_at"),
        Index("ix_observation_dispute", "dispute_status"),
    )

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    occurred_precision: Mapped[OccurredPrecision] = mapped_column(String(16), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    animal_scope: Mapped[AnimalScope] = mapped_column(String(20), nullable=False)
    observed_action: Mapped[RuleAction] = mapped_column(String(24), nullable=False)
    staff_action: Mapped[ObservationStaffAction] = mapped_column(String(32), nullable=False)
    place_confidence: Mapped[PlaceConfidence] = mapped_column(String(24), nullable=False)
    evidence_support: Mapped[str | None] = mapped_column(JSON, nullable=True)  # asset ids
    dispute_status: Mapped[ObservationDisputeStatus] = mapped_column(
        String(20), default=ObservationDisputeStatus.NONE, nullable=False
    )
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Raw GPS is never persisted; only bucketed on-site proximity (design #15, ADR-012)
    proximity_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    distance_bucket: Mapped[str | None] = mapped_column(String(16), nullable=True)
    accuracy_bucket: Mapped[str | None] = mapped_column(String(16), nullable=True)
    proximity_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User | None"] = relationship(back_populates="observation_claims")


class VerificationEvent(Base, PkMixin, TimestampMixin):
    """On-site confirmation/correction events (design #15, #17)."""

    __tablename__ = "verification_event"
    __table_args__ = (Index("ix_verification_place_created", "place_id", "created_at"),)

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="SET NULL"), nullable=True
    )
    rule_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("access_rule.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[VerificationEventType] = mapped_column(String(32), nullable=False)
    result: Mapped[VerificationResult] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_refs: Mapped[list | None] = mapped_column(JSON, nullable=True)

    proximity_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    distance_bucket: Mapped[str | None] = mapped_column(String(16), nullable=True)
    accuracy_bucket: Mapped[str | None] = mapped_column(String(16), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
