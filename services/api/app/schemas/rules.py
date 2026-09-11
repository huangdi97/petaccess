"""Rule + evaluation DTOs (design #10-12)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AnimalScope,
    RuleAction,
    RuleConditionType,
    RuleEffect,
    RuleOrigin,
    RuleStatus,
)


class ConditionIn(BaseModel):
    condition_type: RuleConditionType
    value_flag: bool | None = None
    value_numeric: float | None = None
    value_text: str | None = Field(default=None, max_length=200)
    value_json: dict | list | None = None


class ConditionOut(ConditionIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    rule_id: str


class RuleIn(BaseModel):
    place_id: str | None = None
    zone_id: str | None = None
    animal_scope: AnimalScope
    action: RuleAction
    effect: RuleEffect
    source_id: str
    rule_origin: RuleOrigin
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    review_due_at: datetime | None = None
    note: str | None = Field(default=None, max_length=2000)
    conditions: list[ConditionIn] = []


class RuleUpdate(BaseModel):
    effect: RuleEffect | None = None
    review_due_at: datetime | None = None
    note: str | None = None
    status: RuleStatus | None = None
    conditions: list[ConditionIn] | None = None


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    place_id: str | None
    zone_id: str | None
    animal_scope: AnimalScope
    action: RuleAction
    effect: RuleEffect
    source_id: str
    rule_origin: RuleOrigin
    effective_from: datetime | None
    effective_to: datetime | None
    recorded_at: datetime
    last_verified_at: datetime | None
    review_due_at: datetime | None
    status: RuleStatus
    supersedes_rule_id: str | None
    note: str | None
    conditions: list[ConditionOut] = []


class AnimalIn(BaseModel):
    species: str
    service_role: str = "none"
    weight_kg: float | None = None
    shoulder_height_cm: float | None = None
    count: int | None = None
    registration_status: str | None = None
    vaccination_status: str | None = None


class EvaluateIn(BaseModel):
    """Evaluate against DB rules for a place/zone (design #12)."""

    animal: AnimalIn
    place_id: str
    zone_id: str | None = None
    date_time: datetime | None = None
    intended_action: RuleAction = RuleAction.ENTER


class EvaluateOut(BaseModel):
    status: str
    matched_rules: list[str]
    unmet_conditions: list[dict]
    unknown_inputs: list[dict]
    reason_codes: list[str]
    source_refs: list[str]
