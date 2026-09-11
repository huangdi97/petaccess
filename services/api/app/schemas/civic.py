"""Civic-domain DTOs: observations, verifications, disputes, regulations,
operator claims, watches, sources (design #13-14, #18, #24, #26)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AnimalScope,
    DisputeCaseStatus,
    DisputeResolution,
    DisputeTargetType,
    JurisdictionLevel,
    JurisdictionReviewStatus,
    MandatoryLevel,
    ObservationDisputeStatus,
    ObservationStaffAction,
    OccurredPrecision,
    PlaceConfidence,
    RuleAction,
    RuleEffect,
    RuleStatus,
    SourceType,
    TemporaryAction,
    VerificationEventType,
    VerificationResult,
    WatchStatus,
    WatchTargetType,
)


# --- sources (design #13) ---
class SourceIn(BaseModel):
    source_type: SourceType
    issuer: str = Field(min_length=1, max_length=200)
    issuer_verification: str = "unverified"
    source_url: str | None = None
    observed_at: datetime | None = None
    published_at: datetime | None = None
    directness: str = "secondary"
    spatial_precision: str = "unknown"
    notes: str | None = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: SourceType
    issuer: str
    issuer_verification: str
    source_url: str | None
    collected_at: datetime
    observed_at: datetime | None
    published_at: datetime | None
    source_availability: str
    directness: str
    spatial_precision: str
    notes: str | None
    created_at: datetime


# --- observations (design #14) ---
class ObservationIn(BaseModel):
    place_id: str
    zone_id: str | None = None
    occurred_at: datetime
    occurred_precision: OccurredPrecision
    animal_scope: AnimalScope
    observed_action: RuleAction
    staff_action: ObservationStaffAction
    place_confidence: PlaceConfidence
    note: str | None = Field(default=None, max_length=1000)
    evidence_refs: list | None = None
    # on-site proximity is bucketed client-side; raw GPS never persisted (ADR-012)
    proximity_verified: bool = False
    distance_bucket: str | None = Field(default=None, max_length=16)
    accuracy_bucket: str | None = Field(default=None, max_length=16)


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    place_id: str
    zone_id: str | None
    user_id: str | None
    occurred_at: datetime
    occurred_precision: OccurredPrecision
    reported_at: datetime
    animal_scope: AnimalScope
    observed_action: RuleAction
    staff_action: ObservationStaffAction
    place_confidence: PlaceConfidence
    evidence_support: list | None
    dispute_status: ObservationDisputeStatus
    withdrawn_at: datetime | None
    note: str | None
    proximity_verified: bool
    distance_bucket: str | None
    accuracy_bucket: str | None


# --- verifications (design #15) ---
class VerificationIn(BaseModel):
    place_id: str
    zone_id: str | None = None
    rule_id: str | None = None
    event_type: VerificationEventType = VerificationEventType.RULE_CONFIRMED
    result: VerificationResult
    note: str | None = Field(default=None, max_length=1000)
    evidence_refs: list | None = None
    proximity_verified: bool = False
    distance_bucket: str | None = None
    accuracy_bucket: str | None = None


class VerificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    place_id: str
    zone_id: str | None
    rule_id: str | None
    user_id: str | None
    event_type: VerificationEventType
    result: VerificationResult
    note: str | None
    evidence_refs: list | None
    proximity_verified: bool
    distance_bucket: str | None
    accuracy_bucket: str | None
    occurred_at: datetime
    created_at: datetime


# --- regulations (design #18) ---
class RegulationIn(BaseModel):
    jurisdiction_level: JurisdictionLevel
    jurisdiction_id: str = Field(min_length=1, max_length=64)
    authority: str = Field(min_length=1, max_length=200)
    instrument_type: str = Field(min_length=1, max_length=64)
    document_name: str = Field(min_length=1, max_length=300)
    clause_ref: str | None = None
    clause_text_ref: str | None = None
    animal_scope: AnimalScope
    venue_scope: str | None = None
    action: RuleAction | None = None
    effect: RuleEffect | None = None
    conditions: list | None = None
    mandatory_level: MandatoryLevel = MandatoryLevel.MANDATORY
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    source_id: str
    review_status: JurisdictionReviewStatus = JurisdictionReviewStatus.NOT_REVIEWED


class RegulationUpdate(BaseModel):
    review_status: JurisdictionReviewStatus | None = None
    action: RuleAction | None = None
    effect: RuleEffect | None = None
    conditions: list | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class RegulationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    jurisdiction_level: JurisdictionLevel
    jurisdiction_id: str
    authority: str
    instrument_type: str
    document_name: str
    clause_ref: str | None
    animal_scope: AnimalScope
    venue_scope: str | None
    action: RuleAction | None
    effect: RuleEffect | None
    conditions: list | None
    mandatory_level: MandatoryLevel
    effective_from: datetime | None
    effective_to: datetime | None
    source_id: str
    status: str
    review_status: JurisdictionReviewStatus
    reviewed_at: datetime | None
    created_at: datetime


# --- operator claims (design #16) ---
class OperatorClaimIn(BaseModel):
    place_id: str
    operator_id: str
    verification_method: str = Field(min_length=1, max_length=64)
    evidence_refs: dict | None = None


class OperatorClaimReview(BaseModel):
    approve: bool
    rejection_reason: str | None = None


class OperatorClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    place_id: str
    operator_id: str
    claimant_user_id: str
    status: str
    verification_method: str | None
    evidence_refs: dict | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    rejection_reason: str | None
    created_at: datetime


class OperatorQuestionnaire(BaseModel):
    """Spokin-style structured questionnaire answers → operator-declared rules
    (design #16). Answers are converted into AccessRule rows versioned by
    superseding the previous operator rules."""

    effective_from: datetime | None = None
    answers: list[dict] = Field(min_length=1)


# --- disputes (design #26) ---
class DisputeIn(BaseModel):
    target_type: DisputeTargetType
    target_id: str
    reason_code: str = Field(min_length=1, max_length=64)
    notice_text: str = Field(min_length=1, max_length=4000)
    evidence_refs: list | None = None


class CounterStatementIn(BaseModel):
    counter_statement: str = Field(min_length=1, max_length=4000)


class DisputeReview(BaseModel):
    action: TemporaryAction | None = None
    forward_to: str | None = None


class DisputeResolutionIn(BaseModel):
    resolution: DisputeResolution
    resolution_note: str | None = Field(default=None, max_length=4000)


class DisputeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    target_type: DisputeTargetType
    target_id: str
    claimant_user_id: str | None
    reason_code: str
    notice_text: str
    evidence_refs: list | None
    temporary_action: TemporaryAction
    counter_statement: str | None
    counter_party_user_id: str | None
    status: DisputeCaseStatus
    resolution: DisputeResolution | None
    resolution_note: str | None
    forwarded_to: str | None
    reviewer_id: str | None
    resolved_at: datetime | None
    created_at: datetime


# --- watches (design #24) ---
class WatchIn(BaseModel):
    target_type: WatchTargetType
    target_id: str
    channels: list[str] = ["in_app"]


class WatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    target_type: WatchTargetType
    target_id: str
    channels: list
    status: WatchStatus
    last_notified_at: datetime | None
    created_at: datetime


# --- audit ---
class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_user_id: str | None
    actor_role: str | None
    action: str
    target_type: str
    target_id: str
    before_state: dict | None
    after_state: dict | None
    request_id: str | None
    created_at: datetime


class RuleStatusChange(BaseModel):
    """Admin conflict-resolution / lifecycle action on a rule."""

    status: RuleStatus
    note: str | None = None
