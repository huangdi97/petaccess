"""Resolve one auditable dispute target without conflating Rule and Reality."""

from typing import cast

from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import (
    AccessRule,
    AnimalFacility,
    ObservationClaim,
    ObservedPresence,
    StaffResponseObservation,
)
from app.models.enums import DisputeTargetType

_REALITY_TARGET_MODELS = {
    DisputeTargetType.OBSERVED_PRESENCE.value: ObservedPresence,
    DisputeTargetType.STAFF_RESPONSE_OBSERVATION.value: StaffResponseObservation,
    DisputeTargetType.ANIMAL_FACILITY.value: AnimalFacility,
}


def require_dispute_target(db: Session, target_type: str, target_id: str):
    target: (
        AccessRule
        | ObservationClaim
        | ObservedPresence
        | StaffResponseObservation
        | AnimalFacility
        | None
    )
    if target_type == DisputeTargetType.ACCESS_RULE.value:
        target = db.get(AccessRule, target_id)
    elif target_type == DisputeTargetType.OBSERVATION_CLAIM.value:
        target = db.get(ObservationClaim, target_id)
    else:
        model = _REALITY_TARGET_MODELS.get(target_type)
        # The registry contains only these immutable Reality record models.
        target = cast(
            ObservedPresence | StaffResponseObservation | AnimalFacility | None,
            db.get(model, target_id) if model is not None else None,
        )
    if target is None:
        raise NotFound("异议目标不存在")
    return target


def is_reality_dispute_target(target_type: str) -> bool:
    return target_type in _REALITY_TARGET_MODELS
