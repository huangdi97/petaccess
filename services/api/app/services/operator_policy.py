"""Approved operator-policy versioning.

This service is deliberately separate from claim identity review. An approved
venue representative may version only OPERATOR_POLICY cells; legal/regulatory
rules remain immutable from this lane.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.audit_events import AuditEvent
from app.models import AccessRule, Operator, OperatorClaim, RuleCondition, Source, User
from app.models.enums import RuleOrigin, RuleStatus
from app.schemas.civic import OperatorQuestionnaire


def _operator_source(db: Session, operator: Operator, now: datetime) -> Source:
    source = db.scalar(
        select(Source).where(
            Source.source_type == "official_operator_policy",
            Source.issuer == operator.name,
        )
    )
    if source is not None:
        return source

    source = Source(
        source_type="official_operator_policy",
        issuer=operator.name,
        issuer_verification="verified",
        directness="direct",
        collected_at=now,
    )
    db.add(source)
    db.flush()
    return source


def _matching_operator_rules(db: Session, claim: OperatorClaim, answer) -> list[AccessRule]:
    zone_predicate = (
        AccessRule.zone_id.is_(None)
        if answer.zone_id is None
        else AccessRule.zone_id == answer.zone_id
    )
    return list(
        db.scalars(
            select(AccessRule).where(
                AccessRule.place_id == claim.place_id,
                AccessRule.status == RuleStatus.CURRENT,
                zone_predicate,
                AccessRule.animal_scope == answer.animal_scope,
                AccessRule.action == answer.action,
                (
                    (AccessRule.rule_layer == "OPERATOR_POLICY")
                    | (AccessRule.rule_origin == RuleOrigin.OPERATOR_DECLARED)
                ),
            )
        ).all()
    )


def apply_operator_questionnaire(
    db: Session,
    *,
    claim: OperatorClaim,
    operator: Operator,
    body: OperatorQuestionnaire,
    actor: User,
) -> dict:
    """Version approved operator policy cells without touching higher Rule layers."""
    now = datetime.now(UTC)
    source = _operator_source(db, operator, now)
    created_rules: list[str] = []
    superseded_rules: list[str] = []

    for answer in body.answers:
        prior_rules = _matching_operator_rules(db, claim, answer)
        predecessor = max(
            prior_rules,
            key=lambda item: item.effective_from or item.recorded_at,
            default=None,
        )
        for prior in prior_rules:
            prior.status = RuleStatus.SUPERSEDED
            prior.effective_to = now
            superseded_rules.append(prior.id)

        rule = AccessRule(
            place_id=claim.place_id,
            zone_id=answer.zone_id,
            animal_scope=answer.animal_scope,
            action=answer.action,
            effect=answer.effect,
            source_id=source.id,
            rule_origin=RuleOrigin.OPERATOR_DECLARED,
            rule_layer="OPERATOR_POLICY",
            mandatory_level="operator_discretion",
            origin_authority=operator.name,
            recorded_at=now,
            effective_from=body.effective_from or now,
            last_verified_at=now,
            review_due_at=answer.review_due_at,
            status=RuleStatus.CURRENT,
            supersedes_rule_id=predecessor.id if predecessor else None,
            note=answer.note,
        )
        db.add(rule)
        db.flush()
        for condition in answer.conditions:
            db.add(RuleCondition(rule_id=rule.id, **condition.model_dump()))
        created_rules.append(rule.id)

    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=actor.id,
        actor_role=str(actor.role),
        action=AuditEvent.OPERATOR_QUESTIONNAIRE_SUBMIT.value,
        target_type="place",
        target_id=claim.place_id,
        after_state={"created_rules": created_rules, "superseded": superseded_rules},
    )
    db.commit()
    return {"created_rules": created_rules, "source_id": source.id}
