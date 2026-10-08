"""Civic-domain DTOs: observations, verifications, disputes, regulations,
operator claims, watches, sources (design #13-14, #18, #24, #26)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    OperatorOrgType,
    PlaceConfidence,
    RuleAction,
    RuleConditionType,
    RuleEffect,
    SourceType,
    TemporaryAction,
    VerificationEventType,
    VerificationResult,
    WatchDomain,
    WatchStatus,
    WatchTargetType,
    normalize_mandatory_level,
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

    @field_validator("mandatory_level", mode="before")
    @classmethod
    def _normalise_legacy_mandatory_level(cls, value: object) -> object:
        """Accept the pre-ADR-023 spelling on read.

        `discretionary` is the legacy spelling of `operator_discretion`, and a
        single row carrying it used to take down `GET /regulations` with a 500:
        response validation runs per item, so one unconvertible value failed the
        whole list rather than that one row. Normalising here rather than in the
        endpoint means every construction path — list, place-scoped, create,
        review — inherits it, and a future endpoint cannot forget.
        """
        if isinstance(value, str):
            return normalize_mandatory_level(value)
        return value


# --- operator claims (design #16) ---
class OperatorClaimIn(BaseModel):
    place_id: str
    operator_id: str
    verification_method: str = Field(min_length=1, max_length=64)
    evidence_refs: dict | None = None


class OperatorClaimSelfServeIn(BaseModel):
    """Consumer-safe claim request; approval still belongs to moderators."""

    place_id: str
    operator_name: str = Field(min_length=2, max_length=160)
    org_type: OperatorOrgType = OperatorOrgType.COMPANY
    work_email: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=512)
    verification_method: str = Field(min_length=1, max_length=64)
    verification_note: str | None = Field(default=None, max_length=500)


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


class OperatorRuleConditionIn(BaseModel):
    """One structured condition in an operator-declared policy cell."""

    condition_type: RuleConditionType
    value_flag: bool | None = None
    value_numeric: float | None = None
    value_text: str | None = Field(default=None, max_length=200)
    value_json: dict | list | None = None


class OperatorRuleAnswerIn(BaseModel):
    """One versionable OPERATOR_POLICY cell from an approved venue representative."""

    zone_id: str | None = None
    animal_scope: AnimalScope
    action: RuleAction
    effect: RuleEffect
    conditions: list[OperatorRuleConditionIn] = Field(default_factory=list)
    review_due_at: datetime | None = None
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("conditions")
    @classmethod
    def conditional_requires_condition(
        cls,
        conditions: list[OperatorRuleConditionIn],
        info,
    ) -> list[OperatorRuleConditionIn]:
        effect = info.data.get("effect")
        if effect == RuleEffect.CONDITIONAL and not conditions:
            raise ValueError(
                "conditional operator policy requires at least one structured condition"
            )
        if effect != RuleEffect.CONDITIONAL and conditions:
            raise ValueError("only conditional operator policy may carry entry conditions")
        return conditions


class OperatorQuestionnaire(BaseModel):
    """Structured operator policy submission after an approved place claim.

    Each answer is one OPERATOR_POLICY cell. The service may version a matching
    prior operator cell, but it must never mutate LEGAL / REGULATORY_GUIDANCE.
    """

    effective_from: datetime | None = None
    answers: list[OperatorRuleAnswerIn] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_policy_cells(self) -> "OperatorQuestionnaire":
        keys = [(item.zone_id, item.animal_scope, item.action) for item in self.answers]
        if len(keys) != len(set(keys)):
            raise ValueError("operator questionnaire contains duplicate policy cells")
        return self


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
    watch_domain: WatchDomain = WatchDomain.RULE
    target_type: WatchTargetType
    target_id: str
    channels: list[str] = ["in_app"]


class WatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    watch_domain: WatchDomain
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
