"""Pure data model for the deterministic rule evaluator.

These dataclasses mirror packages/rule-spec schemas and are the only objects
the evaluator touches: it never reads the database and never calls an LLM
(ADR-005, design #12).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class AnimalScope(StrEnum):
    DOG = "dog"
    CAT = "cat"
    ORDINARY_PET = "ordinary_pet"
    SERVICE_DOG = "service_dog"
    OTHER = "other"


class RuleAction(StrEnum):
    ENTER = "enter"
    PASS_THROUGH = "pass_through"
    STAY = "stay"
    WALK = "walk"
    OFF_LEASH = "off_leash"
    GROUND_CONTACT = "ground_contact"
    RIDE_ELEVATOR = "ride_elevator"
    RIDE_TRANSPORT = "ride_transport"
    USE_FACILITY = "use_facility"
    DINE = "dine"
    STAY_OVERNIGHT = "stay_overnight"


class RuleEffect(StrEnum):
    ALLOWED = "allowed"
    PROHIBITED = "prohibited"
    CONDITIONAL = "conditional"


class RuleStatus(StrEnum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    DISPUTED = "disputed"
    ARCHIVED = "archived"
    PENDING_REVIEW = "pending_review"


class ResultStatus(StrEnum):
    MATCH = "MATCH"
    CONDITIONAL = "CONDITIONAL"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class Condition:
    condition_type: str
    value_flag: bool | None = None
    value_numeric: float | None = None
    value_text: str | None = None
    value_json: dict | list | None = None


@dataclass(frozen=True)
class Rule:
    id: str
    animal_scope: AnimalScope
    action: RuleAction
    effect: RuleEffect
    status: RuleStatus = RuleStatus.CURRENT
    zone_id: str | None = None
    place_id: str | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    conditions: tuple[Condition, ...] = ()
    source_id: str | None = None
    supersedes_rule_id: str | None = None


@dataclass(frozen=True)
class AnimalInput:
    species: str
    service_role: str = "none"
    weight_kg: float | None = None
    shoulder_height_cm: float | None = None
    count: int | None = None
    registration_status: str | None = None
    vaccination_status: str | None = None


@dataclass(frozen=True)
class QueryContext:
    animal: AnimalInput
    place_id: str
    date_time: datetime
    intended_action: RuleAction
    zone_id: str | None = None


@dataclass(frozen=True)
class UnmetCondition:
    rule_id: str
    condition_type: str
    kind: str  # obligation | failed_check | outside_window
    detail: str | None = None


@dataclass(frozen=True)
class UnknownInput:
    input: str
    reason: str


@dataclass(frozen=True)
class ApplicabilityResult:
    status: ResultStatus
    matched_rules: list[str] = field(default_factory=list)
    unmet_conditions: list[UnmetCondition] = field(default_factory=list)
    unknown_inputs: list[UnknownInput] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
