"""v0.9-R1 Reality Layer entities (design v0.9 §7) + RealityReport parent and
the ten state models from the 2026-09-22 contribution-deepening addendum.

Reality = what is *observed* on site. RealityReport is the parent context of a
contribution; RealityCandidate is the reviewable unit under it; when a human
VERIFIES a candidate, a RealityClaim row (ObservedPresence /
StaffResponseObservation / AnimalFacility) is published. The two layers stay
separate: a candidate can be HOLD / REJECTED without touching the published
claim, and a published claim never leaves an observation un-sourced.

Hard separations enforced by the schema shape (and by tests):

- Observation != Rule: these tables never join the deterministic evaluator.
- StaffResponse != OperatorPolicy: a response documents one behaviour.
- Facility != EntryPolicy: a facility implies nothing about access.
- AI is DERIVED only: ``verification_status=derived_ai_only`` can never be
  shown as human-verified, and ``reality_decision`` is written by a human only.
- A RealityReport is a parent; it may produce several candidates (presence /
  staff response / facility). ``reporter_id`` is nullable — anonymous token
  reports are allowed.
- Time evidence keeps content_published_at / claimed_event_at / observed_at /
  time_certainty separate: publication time is never event time.
- A RealityConfirmation is evidence, never a deletion: NOT_SEEN_NOW adds a
  record and must not remove an older Observation.
- ObservationEffort with animal_observed=false forms ONLY an effort row — it
  never becomes a NO_ANIMAL_PRESENCE claim.
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
    ExternalContentPlatform,
    FacilityAccessMode,
    FacilityOperationalState,
    FactEvidenceState,
    ObservationEffortDurationBucket,
    ObservationOrigin,
    ObservedAction,
    PlaceMatchState,
    RealityCandidateType,
    RealityConfirmationType,
    RealityDecision,
    RealityFreshnessState,
    RealityReportModerationState,
    RealityReportPrivacyState,
    RealityVerificationStatus,
    StaffActorRole,
    StaffResponseAction,
    TimeCertainty,
    TimeEvidenceState,
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
    report_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("reality_report.id", ondelete="SET NULL"), nullable=True
    )
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
        String(36),
        ForeignKey(
            "evidence_bundle.id",
            ondelete="SET NULL",
            # R-01: the convention-generated name
            # fk_staff_response_observation_evidence_bundle_id_evidence_bundle
            # exceeds PostgreSQL's 63-char identifier limit and gets truncated
            # non-deterministically. Migration c3a9e5f7d1b2 renames it to this
            # deterministic name; naming it here keeps alembic autogenerate clean.
            name="fk_staff_response_observation_evidence_bundle",
        ),
        nullable=True,
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


# ---------------------------------------------------------------------------
# RealityReport parent (addendum PHASE 3) + ten state models (PHASE 4-11)
#
# A RealityReport is the parent context of one contribution; it may produce
# several RealityCandidates (observed_presence / staff_response /
# animal_facility). All columns are additive; FK names are explicit and kept
# ≤63 chars (R-01 lesson).
# ---------------------------------------------------------------------------


class RealityReport(Base, PkMixin, TimestampMixin):
    """Parent context of a reality contribution (addendum PHASE 3).

    One report may carry several candidates. ``reporter_id`` is nullable —
    anonymous-token contributions are allowed. Media defaults to private.
    """

    __tablename__ = "reality_report"
    __table_args__ = (
        Index("ix_reality_report_origin_moderation", "origin", "moderation_state"),
        Index("ix_reality_report_reporter", "reporter_id"),
    )

    # — reporter (either logged-in user or anonymous token) ---------------
    reporter_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    anonymous_token: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # — origin (addendum PHASE 4) — the UI never exposes this enum ---------
    origin: Mapped[ObservationOrigin] = mapped_column(String(32), nullable=False)

    # — place match (addendum PHASE 5) --------------------------------------
    # ``place_id`` is the primary place the report concerns; container /
    # subject carry the PARENT_PLACE_ONLY precision.
    place_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="SET NULL"), nullable=True
    )
    container_place_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    subject_place_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    place_match_state: Mapped[PlaceMatchState] = mapped_column(
        String(24), nullable=False, default=PlaceMatchState.UNRESOLVED
    )
    place_match_evidence_types: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # — time evidence (addendum PHASE 6) — publication time != event time ---
    time_evidence_state: Mapped[TimeEvidenceState] = mapped_column(
        String(32), nullable=False, default=TimeEvidenceState.UNKNOWN
    )
    content_published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    claimed_event_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_certainty: Mapped[TimeCertainty] = mapped_column(
        String(16), nullable=False, default=TimeCertainty.UNKNOWN
    )

    # — fact evidence (addendum PHASE 7) — never a single credibility number --
    fact_evidence_state: Mapped[FactEvidenceState] = mapped_column(
        String(32), nullable=False, default=FactEvidenceState.INSUFFICIENT
    )

    # — media (addendum P7) — private by default ----------------------------
    privacy_state: Mapped[RealityReportPrivacyState] = mapped_column(
        String(16), nullable=False, default=RealityReportPrivacyState.PRIVATE
    )
    media_refs: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # — source / external content (addendum P8) -----------------------------
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_platform: Mapped[ExternalContentPlatform | None] = mapped_column(
        String(24), nullable=True
    )
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    media_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_keyframe_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # — moderation / anti-abuse (addendum PHASE 12-13) ----------------------
    moderation_state: Mapped[RealityReportModerationState] = mapped_column(
        String(16), nullable=False, default=RealityReportModerationState.PENDING
    )
    abuse_flags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # — lifecycle ------------------------------------------------------------
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ObservationEffort(Base, PkMixin, TimestampMixin):
    """Structured "I was there and did not see an animal" record (addendum PHASE 8).

    animal_observed=false forms ONLY an ObservationEffort — it NEVER becomes a
    NO_ANIMAL_PRESENCE claim (no observation != no animal presence).
    """

    __tablename__ = "observation_effort"
    __table_args__ = (
        Index("ix_observation_effort_place_time", "place_id", "observed_at"),
        Index("ix_observation_effort_animal", "animal_observed"),
    )

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    duration_bucket: Mapped[ObservationEffortDurationBucket] = mapped_column(
        String(16), nullable=False, default=ObservationEffortDurationBucket.UNKNOWN
    )
    covered_zone_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    animal_observed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reporter_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )


class RealityConfirmation(Base, PkMixin, TimestampMixin):
    """Lightweight on-site confirmation of a published reality fact (addendum PHASE 11).

    A confirmation is evidence, never a deletion: ``NOT_SEEN_NOW`` adds a row
    and must not remove the older Observation.
    """

    __tablename__ = "reality_confirmation"
    __table_args__ = (
        Index("ix_reality_confirmation_place_type", "place_id", "confirmation_type"),
        Index("ix_reality_confirmation_target", "target_claim_id"),
    )

    confirmation_type: Mapped[RealityConfirmationType] = mapped_column(String(24), nullable=False)
    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    target_claim_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    target_candidate_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("reality_candidate.id", ondelete="SET NULL"), nullable=True
    )
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reporter_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )


class ExternalContentReference(Base, PkMixin, TimestampMixin):
    """A referenced external post/video with dedup-relevant metadata (addendum P8).

    content_hash / media_hash feed dedup, near-duplicate and recycled-content
    checks. A title like "宠物友好" never produces a Rule by itself.
    """

    __tablename__ = "external_content_reference"
    __table_args__ = (
        Index("ix_external_content_ref_report", "report_id"),
        Index("ix_external_content_ref_hash", "content_hash"),
    )

    report_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("reality_report.id", ondelete="CASCADE"), nullable=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[ExternalContentPlatform | None] = mapped_column(String(24), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    place_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    keyframe_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    media_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
