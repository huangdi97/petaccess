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
    FacilityAccessMode,
    FacilityOperationalState,
    ObservedAction,
    RealityDecision,
    RealityFreshnessState,
    RealityVerificationStatus,
    StaffActorRole,
    StaffResponseAction,
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
