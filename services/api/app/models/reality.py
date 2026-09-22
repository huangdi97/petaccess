"""v0.9-R1 Reality Layer entities (design v0.9 §7).

Reality = what is *observed* on site. RealityCandidate is the reviewable unit;
when a human VERIFIES it, a RealityClaim row (ObservedPresence /
StaffResponseObservation / AnimalFacility) is published. The two layers stay
separate: a candidate can be HOLD / REJECTED without touching the published
claim, and a published claim never leaves an observation un-sourced.

Hard separations enforced by the schema shape (and by tests):

- Observation != Rule: these tables never join the deterministic evaluator.
- StaffResponse != OperatorPolicy: a response documents one behaviour.
- Facility != EntryPolicy: a facility implies nothing about access.
- AI is DERIVED only: ``verification_status=derived_ai_only`` can never be
  shown as human-verified, and ``reality_decision`` is written by a human only.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PkMixin, TimestampMixin

from .enums import (
    AnimalFacilityType,
    AnimalScope,
    FacilityAccessMode,
    FacilityOperationalState,
    ObservedAction,
    RealityCandidateType,
    RealityDecision,
    RealityFreshnessState,
    RealityVerificationStatus,
    StaffActorRole,
    StaffResponseAction,
)


class RealityCandidate(Base, PkMixin, TimestampMixin):
    """Reviewable reality fact, any subtype (v0.9 §7.1, §7.4).

    Review is independent of rule review: ``reality_decision`` is one of
    VERIFIED / VERIFIED_WITH_NOTE / HOLD / REJECTED and is written by a human
    only — an AI never sets it.
    """

    __tablename__ = "reality_candidate"
    __table_args__ = (
        Index("ix_reality_candidate_place_status", "place_id", "review_status"),
        Index("ix_reality_candidate_type_status", "candidate_type", "review_status"),
    )

    candidate_type: Mapped[RealityCandidateType] = mapped_column(String(32), nullable=False)
    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="SET NULL"), nullable=True
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )
    evidence_bundle_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evidence_bundle.id", ondelete="SET NULL"), nullable=True
    )

    # — shared fact fields (subset relevant to this candidate) --------------
    animal_scope: Mapped[AnimalScope | None] = mapped_column(String(20), nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # — human review (v0.9 §7.4) — never machine-written -------------------
    review_status: Mapped[str] = mapped_column(String(24), nullable=False, default="REVIEW_PENDING")
    reality_decision: Mapped[RealityDecision | None] = mapped_column(String(24), nullable=True)
    reviewer: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # — freshness / verification (v0.9 §7.5) --------------------------------
    freshness_state: Mapped[RealityFreshnessState | None] = mapped_column(String(24), nullable=True)
    verification_status: Mapped[RealityVerificationStatus] = mapped_column(
        String(24), nullable=False, default=RealityVerificationStatus.UNVERIFIED
    )

    # — subtype payload (AI extraction + human complement) ------------------
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # — publication linkage --------------------------------------------------
    published_claim_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ObservedPresence(Base, PkMixin, TimestampMixin):
    """Published, human-verified animal presence fact (v0.9 §7.1)."""

    __tablename__ = "observed_presence"
    __table_args__ = (
        Index("ix_observed_presence_place_time", "place_id", "observed_at"),
        Index("ix_observed_presence_freshness", "freshness_state"),
    )

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reality_candidate.id", ondelete="RESTRICT"), nullable=False
    )
    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="SET NULL"), nullable=True
    )
    animal_scope: Mapped[AnimalScope] = mapped_column(String(20), nullable=False)
    animal_count_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observed_action: Mapped[ObservedAction] = mapped_column(String(32), nullable=False)
    observed_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )
    evidence_bundle_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evidence_bundle.id", ondelete="SET NULL"), nullable=True
    )
    verification_status: Mapped[RealityVerificationStatus] = mapped_column(
        String(24), nullable=False, default=RealityVerificationStatus.UNVERIFIED
    )
    freshness_state: Mapped[RealityFreshnessState | None] = mapped_column(String(24), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class StaffResponseObservation(Base, PkMixin, TimestampMixin):
    """Published, human-verified staff behaviour in one event (v0.9 §7.2).

    Stores the actor's *role* only — ordinary staff identity is never exposed
    to consumers. Never an attitude score, never an operator policy.
    """

    __tablename__ = "staff_response_observation"
    __table_args__ = (
        Index("ix_staff_response_place_time", "place_id", "observed_at"),
        Index("ix_staff_response_freshness", "freshness_state"),
    )

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reality_candidate.id", ondelete="RESTRICT"), nullable=False
    )
    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="SET NULL"), nullable=True
    )
    actor_role: Mapped[StaffActorRole] = mapped_column(String(24), nullable=False)
    trigger_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_action: Mapped[StaffResponseAction] = mapped_column(String(48), nullable=False)
    response_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_statement_verbatim: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )
    evidence_bundle_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evidence_bundle.id", ondelete="SET NULL"), nullable=True
    )
    verification_status: Mapped[RealityVerificationStatus] = mapped_column(
        String(24), nullable=False, default=RealityVerificationStatus.UNVERIFIED
    )
    freshness_state: Mapped[RealityFreshnessState | None] = mapped_column(String(24), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AnimalFacility(Base, PkMixin, TimestampMixin):
    """Published, human-verified animal-related facility (v0.9 §7.3)."""

    __tablename__ = "animal_facility"
    __table_args__ = (
        Index("ix_animal_facility_place_type", "place_id", "facility_type"),
        Index("ix_animal_facility_state", "operational_state"),
    )

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reality_candidate.id", ondelete="RESTRICT"), nullable=False
    )
    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="SET NULL"), nullable=True
    )
    facility_type: Mapped[AnimalFacilityType] = mapped_column(String(40), nullable=False)
    operator_provided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    access_mode: Mapped[FacilityAccessMode] = mapped_column(
        String(24), nullable=False, default=FacilityAccessMode.UNKNOWN
    )
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_limit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    weather_protection: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    shade: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ventilation: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    water_available: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    supervision_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    security_or_lock_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operational_state: Mapped[FacilityOperationalState] = mapped_column(
        String(24), nullable=False, default=FacilityOperationalState.ACTIVE
    )
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )
    evidence_bundle_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evidence_bundle.id", ondelete="SET NULL"), nullable=True
    )
    verification_status: Mapped[RealityVerificationStatus] = mapped_column(
        String(24), nullable=False, default=RealityVerificationStatus.UNVERIFIED
    )
    freshness_state: Mapped[RealityFreshnessState | None] = mapped_column(String(24), nullable=True)
