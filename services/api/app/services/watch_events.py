"""Reviewed in-app Watch Event delivery.

v0.10-R1 §39:
    Source Change -> Candidate -> Human Review -> published Rule/Reality -> Watch Event

This service deliberately sits *after* publication. It never emits from raw
source changes, pending candidates, private RealityReports, or AI extraction.
External push delivery is out of scope here; the persisted event is the
truthful in-app ledger consumed by the Consumer notification centre.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models import (
    AccessRule,
    AnimalFacility,
    ObservedPresence,
    RealityCandidate,
    RuleException,
    StaffResponseObservation,
    WatchEvent,
    WatchSubscription,
    Zone,
)
from app.models.enums import (
    WatchDomain,
    WatchEventType,
    WatchStatus,
    WatchTargetType,
)


def _value(value: object) -> object:
    return value.value if isinstance(value, Enum) else value


def _string_value(value: str | Enum) -> str:
    """Normalize SQLAlchemy String-backed enums without assuming runtime coercion."""

    return str(value.value) if isinstance(value, Enum) else value


def _rule_place_id(db: Session, rule: AccessRule) -> str | None:
    if rule.place_id:
        return rule.place_id
    if rule.zone_id:
        zone = db.get(Zone, rule.zone_id)
        return zone.place_id if zone else None
    return None


def _deliver(
    db: Session,
    subscriptions: list[WatchSubscription],
    *,
    event_type: WatchEventType,
    subject_type: str,
    subject_id: str,
    place_id: str | None,
    payload: dict[str, object],
) -> list[WatchEvent]:
    """Create one idempotent in-app event per matching active subscription."""

    now = datetime.now(UTC)
    created: list[WatchEvent] = []
    for subscription in subscriptions:
        existing = db.scalar(
            select(WatchEvent.id).where(
                WatchEvent.subscription_id == subscription.id,
                WatchEvent.event_type == event_type,
                WatchEvent.subject_id == subject_id,
            )
        )
        if existing is not None:
            continue

        event = WatchEvent(
            subscription_id=subscription.id,
            user_id=subscription.user_id,
            watch_domain=subscription.watch_domain,
            target_type=subscription.target_type,
            target_id=subscription.target_id,
            event_type=event_type,
            subject_type=subject_type,
            subject_id=subject_id,
            place_id=place_id,
            occurred_at=now,
            payload=payload,
        )
        db.add(event)
        subscription.last_notified_at = now
        created.append(event)

    if created:
        # Assign IDs now and let the caller's existing publication transaction
        # commit Rule/Reality truth and Watch Event atomically.
        db.flush()
    return created


def emit_rule_published(
    db: Session,
    rule: AccessRule,
    *,
    superseded_rule_ids: tuple[str, ...] = (),
) -> list[WatchEvent]:
    """Deliver a reviewed AccessRule publication to matching Rule watches."""

    place_id = _rule_place_id(db, rule)
    specific_ids = tuple(dict.fromkeys((rule.id, *superseded_rule_ids)))

    clauses = []
    if place_id:
        clauses.append(
            and_(
                WatchSubscription.target_type == WatchTargetType.PLACE,
                WatchSubscription.target_id == place_id,
            )
        )
    if rule.zone_id:
        clauses.append(
            and_(
                WatchSubscription.target_type == WatchTargetType.ZONE,
                WatchSubscription.target_id == rule.zone_id,
            )
        )
    if specific_ids:
        clauses.append(
            and_(
                WatchSubscription.target_type == WatchTargetType.RULE,
                WatchSubscription.target_id.in_(specific_ids),
            )
        )
    if not clauses:
        return []

    subscriptions = list(
        db.scalars(
            select(WatchSubscription).where(
                WatchSubscription.watch_domain == WatchDomain.RULE,
                WatchSubscription.status == WatchStatus.ACTIVE,
                or_(*clauses),
            )
        ).all()
    )
    payload = {
        "action": _value(rule.action),
        "effect": _value(rule.effect),
        "rule_layer": _value(rule.rule_layer),
        "zone_id": rule.zone_id,
        "supersedes_rule_id": rule.supersedes_rule_id,
    }
    return _deliver(
        db,
        subscriptions,
        event_type=WatchEventType.RULE_VERSION_PUBLISHED,
        subject_type="access_rule",
        subject_id=rule.id,
        place_id=place_id,
        payload=payload,
    )


def emit_rule_exception_published(
    db: Session,
    base_rule: AccessRule,
    exception: RuleException,
) -> list[WatchEvent]:
    """Deliver a reviewed carve-out as a Rule Watch event on its base rule."""

    place_id = _rule_place_id(db, base_rule)
    clauses = [
        and_(
            WatchSubscription.target_type == WatchTargetType.RULE,
            WatchSubscription.target_id == base_rule.id,
        )
    ]
    if place_id:
        clauses.append(
            and_(
                WatchSubscription.target_type == WatchTargetType.PLACE,
                WatchSubscription.target_id == place_id,
            )
        )
    if base_rule.zone_id:
        clauses.append(
            and_(
                WatchSubscription.target_type == WatchTargetType.ZONE,
                WatchSubscription.target_id == base_rule.zone_id,
            )
        )

    subscriptions = list(
        db.scalars(
            select(WatchSubscription).where(
                WatchSubscription.watch_domain == WatchDomain.RULE,
                WatchSubscription.status == WatchStatus.ACTIVE,
                or_(*clauses),
            )
        ).all()
    )
    payload = {
        "base_rule_id": base_rule.id,
        "animal_scope": _value(exception.animal_scope),
        "effect": _value(exception.effect),
        "zone_id": base_rule.zone_id,
    }
    return _deliver(
        db,
        subscriptions,
        event_type=WatchEventType.RULE_EXCEPTION_PUBLISHED,
        subject_type="rule_exception",
        subject_id=exception.id,
        place_id=place_id,
        payload=payload,
    )


def emit_reality_published(
    db: Session,
    candidate: RealityCandidate,
    claim: ObservedPresence | StaffResponseObservation | AnimalFacility,
) -> list[WatchEvent]:
    """Deliver one human-verified published Reality fact to Reality watches."""

    event_type_by_candidate = {
        "observed_presence": WatchEventType.REALITY_OBSERVED_PRESENCE_PUBLISHED,
        "staff_response": WatchEventType.REALITY_STAFF_RESPONSE_PUBLISHED,
        "animal_facility": WatchEventType.REALITY_ANIMAL_FACILITY_PUBLISHED,
    }
    candidate_type = _string_value(candidate.candidate_type)
    event_type = event_type_by_candidate.get(candidate_type)
    if event_type is None:
        return []

    clauses = [
        and_(
            WatchSubscription.target_type == WatchTargetType.PLACE,
            WatchSubscription.target_id == candidate.place_id,
        )
    ]
    if candidate.zone_id:
        clauses.append(
            and_(
                WatchSubscription.target_type == WatchTargetType.ZONE,
                WatchSubscription.target_id == candidate.zone_id,
            )
        )

    subscriptions = list(
        db.scalars(
            select(WatchSubscription).where(
                WatchSubscription.watch_domain == WatchDomain.REALITY,
                WatchSubscription.status == WatchStatus.ACTIVE,
                or_(*clauses),
            )
        ).all()
    )
    payload = {
        "candidate_type": candidate_type,
        "zone_id": candidate.zone_id,
        "verification_status": _value(claim.verification_status),
    }
    return _deliver(
        db,
        subscriptions,
        event_type=event_type,
        subject_type=candidate_type,
        subject_id=str(claim.id),
        place_id=candidate.place_id,
        payload=payload,
    )
