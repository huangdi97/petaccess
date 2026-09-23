"""v0.9-R1 Reality Layer DTOs (design v0.9 §7, §9).

Consumer-visible reality claims always carry Evidence + Review + Freshness;
these schemas keep the three together so a handler cannot assemble a claim
that hides its verification posture.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AnimalFacilityType,
    AnimalScope,
    ContributionAbuseFlag,
    ExternalContentPlatform,
    FacilityAccessMode,
    FacilityOperationalState,
    FactEvidenceState,
    ObservationEffortDurationBucket,
    ObservationOrigin,
    ObservedAction,
    PlaceMatchEvidenceType,
    PlaceMatchState,
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

# ---------------------------------------------------------------------------
# Candidate (reviewable) layer
# ---------------------------------------------------------------------------


class RealityCandidateIn(BaseModel):
    candidate_type: str = Field(min_length=1, max_length=32)
    place_id: str
    zone_id: str | None = None
    source_id: str | None = None
    evidence_bundle_id: str | None = None
    animal_scope: AnimalScope | None = None
    observed_at: datetime | None = None
    captured_at: datetime | None = None
    payload: dict | None = None


class RealityDecisionIn(BaseModel):
    """Human-only reality review decision (v0.9 §7.4)."""

    reality_decision: RealityDecision
    decision_note: str | None = Field(default=None, max_length=2000)


class RealityCandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_type: str
    place_id: str
    zone_id: str | None
    source_id: str | None
    evidence_bundle_id: str | None
    animal_scope: str | None
    observed_at: datetime | None
    captured_at: datetime | None
    review_status: str
    reality_decision: RealityDecision | None
    reviewer: str | None
    decided_at: datetime | None
    decision_note: str | None
    freshness_state: RealityFreshnessState | None
    verification_status: RealityVerificationStatus
    payload: dict | None
    published_claim_id: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Published claims (consumer-visible, human-verified only)
# ---------------------------------------------------------------------------


class ObservedPresenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    place_id: str
    zone_id: str | None
    animal_scope: AnimalScope
    animal_count_estimate: int | None
    observed_action: ObservedAction
    observed_context: str | None
    observed_at: datetime
    captured_at: datetime
    source_id: str | None
    evidence_bundle_id: str | None
    verification_status: RealityVerificationStatus
    freshness_state: RealityFreshnessState | None
    last_verified_at: datetime | None


class StaffResponseObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    place_id: str
    zone_id: str | None
    # role only — ordinary staff identity is never exposed
    actor_role: StaffActorRole
    trigger_context: str | None
    response_action: StaffResponseAction
    response_outcome: str | None
    policy_statement_verbatim: str | None
    observed_at: datetime
    captured_at: datetime
    source_id: str | None
    evidence_bundle_id: str | None
    verification_status: RealityVerificationStatus
    freshness_state: RealityFreshnessState | None
    last_verified_at: datetime | None


class AnimalFacilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    place_id: str
    zone_id: str | None
    facility_type: AnimalFacilityType
    operator_provided: bool
    access_mode: FacilityAccessMode
    capacity: int | None
    size_limit: str | None
    weather_protection: bool | None
    shade: bool | None
    ventilation: bool | None
    water_available: bool | None
    supervision_state: str | None
    security_or_lock_state: str | None
    operational_state: FacilityOperationalState
    observed_at: datetime | None
    last_verified_at: datetime | None
    source_id: str | None
    evidence_bundle_id: str | None
    verification_status: RealityVerificationStatus
    freshness_state: RealityFreshnessState | None


# ---------------------------------------------------------------------------
# Consumer aggregate — RealityAnswer (v0.9 §9, §11 CoexistenceSnapshot part)
# ---------------------------------------------------------------------------


class StaffResponseSummaryItem(BaseModel):
    """Counts of one observed staff response action (facts only)."""

    response_action: StaffResponseAction
    count: int


class FacilitySummaryItem(BaseModel):
    """One animal facility, with its verified freshness (facts only)."""

    facility_type: AnimalFacilityType
    count: int
    operational_state: FacilityOperationalState
    last_verified_at: datetime | None


class RealityAnswer(BaseModel):
    """RealityAnswer — the reality half of a CoexistenceSnapshot (v0.9 §9)."""

    state: str
    last_seen_at: datetime | None = None
    evidence_count: int = 0
    distinct_source_count: int = 0
    observed_zones: list[str] = []
    observed_actions: list[str] = []
    staff_response_summary: list[StaffResponseSummaryItem] = []
    facility_summary: list[FacilitySummaryItem] = []
    freshness_state: str | None = None
    verification_state: str | None = None
    recent_count_7d: int = 0
    recent_count_30d: int = 0
    days_since_last_seen: int | None = None
    note: str | None = None


# ---------------------------------------------------------------------------
# RealityReport parent + state models (addendum PHASE 3-11)
# ---------------------------------------------------------------------------


class RealityReportIn(BaseModel):
    """User contribution payload — one report, possibly several candidates.

    ``origin`` is set from the UI branch, never exposed as a raw enum to the
    user. Media defaults to private; a no-media first-hand report is
    ``FIRST_HAND_NO_MEDIA`` and stays review-pending (never auto-rejected).
    """

    origin: ObservationOrigin
    place_id: str | None = None
    container_place_id: str | None = None
    subject_place_id: str | None = None
    place_match_state: PlaceMatchState = PlaceMatchState.UNRESOLVED
    place_match_evidence_types: list[PlaceMatchEvidenceType] | None = None
    time_evidence_state: TimeEvidenceState = TimeEvidenceState.UNKNOWN
    content_published_at: datetime | None = None
    claimed_event_at: datetime | None = None
    observed_at: datetime | None = None
    time_certainty: TimeCertainty = TimeCertainty.UNKNOWN
    fact_evidence_state: FactEvidenceState = FactEvidenceState.INSUFFICIENT
    privacy_state: RealityReportPrivacyState = RealityReportPrivacyState.PRIVATE
    media_refs: list[dict] | None = None
    source_url: str | None = None
    source_platform: ExternalContentPlatform | None = None
    content_hash: str | None = None
    media_hash: str | None = None
    external_keyframe_ref: str | None = None
    ocr_text: str | None = None
    abuse_flags: list[ContributionAbuseFlag] | None = None


class RealityReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reporter_id: str | None
    anonymous_token: str | None
    origin: ObservationOrigin
    place_id: str | None
    container_place_id: str | None
    subject_place_id: str | None
    place_match_state: PlaceMatchState
    place_match_evidence_types: list | None
    time_evidence_state: TimeEvidenceState
    content_published_at: datetime | None
    claimed_event_at: datetime | None
    observed_at: datetime | None
    time_certainty: TimeCertainty
    fact_evidence_state: FactEvidenceState
    privacy_state: RealityReportPrivacyState
    media_refs: list | None
    source_url: str | None
    source_platform: ExternalContentPlatform | None
    content_hash: str | None
    media_hash: str | None
    moderation_state: RealityReportModerationState
    abuse_flags: list | None
    created_at: datetime
    submitted_at: datetime | None


class ObservationEffortIn(BaseModel):
    """\"Was on site and did not see an animal\" — effort only, never a claim."""

    place_id: str
    duration_bucket: ObservationEffortDurationBucket
    covered_zone_ids: list[str] | None = None
    animal_observed: bool = False
    observed_at: datetime | None = None
    source_id: str | None = None


class RealityConfirmationIn(BaseModel):
    """Lightweight on-site confirmation — evidence, never a deletion."""

    confirmation_type: RealityConfirmationType
    place_id: str
    target_claim_id: str | None = None
    target_candidate_id: str | None = None
    observed_at: datetime | None = None


class RealityConfirmationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    confirmation_type: RealityConfirmationType
    place_id: str
    target_claim_id: str | None
    target_candidate_id: str | None
    observed_at: datetime | None
    created_at: datetime


class ExternalContentReferenceIn(BaseModel):
    """External post/video reference with dedup-relevant metadata (addendum P8)."""

    source_url: str
    platform: ExternalContentPlatform | None = None
    published_at: datetime | None = None
    place_metadata: dict | None = None
    keyframe_ref: str | None = None
    ocr_text: str | None = None
    content_hash: str | None = None
    media_hash: str | None = None
