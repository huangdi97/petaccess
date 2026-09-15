"""AccessRule endpoints + deterministic evaluation (design #10-12, #31)."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import record_audit
from app.core.errors import ApiError, NotFound
from app.core.security import require_role
from app.db.session import get_db
from app.models import AccessRule, Place, RuleException, Source, User, Zone
from app.models.enums import UserRole
from app.rulespec.evaluator import evaluate as spec_evaluate
from app.rulespec.model import (
    AnimalInput,
    AnimalScope,
    Condition,
    QueryContext,
    RuleAction,
    RuleEffect,
    RuleStatus,
)
from app.rulespec.model import (
    Rule as SpecRule,
)
from app.schemas.common import Page
from app.schemas.rules import EvaluateIn, EvaluateOut, RuleIn, RuleOut, RuleUpdate

router = APIRouter(tags=["rules"])
admin = APIRouter(tags=["admin:rules"])


def to_spec_rule(r: AccessRule) -> SpecRule:
    return SpecRule(
        id=r.id,
        animal_scope=AnimalScope(r.animal_scope),
        action=RuleAction(r.action),
        effect=RuleEffect(r.effect),
        status=RuleStatus(r.status),
        zone_id=r.zone_id,
        place_id=r.place_id,
        effective_from=r.effective_from,
        effective_to=r.effective_to,
        conditions=tuple(
            Condition(
                condition_type=c.condition_type,
                value_flag=c.value_flag,
                value_numeric=float(c.value_numeric) if c.value_numeric is not None else None,
                value_text=c.value_text,
                value_json=c.value_json,
            )
            for c in r.conditions
        ),
        source_id=r.source_id,
        supersedes_rule_id=r.supersedes_rule_id,
    )


def load_rules_for_place(db: Session, place_id: str) -> list[AccessRule]:
    return list(
        db.scalars(
            select(AccessRule)
            .options(selectinload(AccessRule.conditions))
            .where(AccessRule.place_id == place_id)
        ).all()
    ) + list(
        db.scalars(
            select(AccessRule)
            .options(selectinload(AccessRule.conditions))
            .where(AccessRule.zone_id.in_(select(Zone.id).where(Zone.place_id == place_id)))
        ).all()
    )


# --- public read ---


@router.get("/places/{place_id}/rules", response_model=Page[RuleOut])
def list_place_rules(
    place_id: str,
    status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Page[RuleOut]:
    """Rules directly on the place plus rules on any of its zones."""
    stmt = (
        select(AccessRule)
        .options(selectinload(AccessRule.conditions))
        .where(
            (AccessRule.place_id == place_id)
            | AccessRule.zone_id.in_(select(Zone.id).where(Zone.place_id == place_id))
        )
    )
    if status:
        stmt = stmt.where(AccessRule.status == status)
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=len(rows), limit=limit, offset=offset)


@router.get("/zones/{zone_id}/rules", response_model=Page[RuleOut])
def list_zone_rules(
    zone_id: str,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Page[RuleOut]:
    stmt = (
        select(AccessRule)
        .options(selectinload(AccessRule.conditions))
        .where(AccessRule.zone_id == zone_id)
    )
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=len(rows), limit=limit, offset=offset)


@router.post("/rules/evaluate", response_model=EvaluateOut)
def evaluate_rules(body: EvaluateIn, db: Session = Depends(get_db)) -> EvaluateOut:
    """Deterministic evaluation only — no LLM, no inference from observations."""
    if db.get(Place, body.place_id) is None:
        raise NotFound("场所不存在")
    db_rules = load_rules_for_place(db, body.place_id)
    spec_rules = [to_spec_rule(r) for r in db_rules]
    # SG-REAL-01: active exceptions on these rules participate in evaluation
    db_exceptions = (
        db.scalars(
            select(RuleException).where(RuleException.rule_id.in_([r.id for r in db_rules]))
        ).all()
        if db_rules
        else []
    )
    exceptions = [
        {
            "id": e.id,
            "rule_id": e.rule_id,
            "animal_scope": e.animal_scope,
            "effect": e.effect,
            "source_id": e.source_id,
            "status": e.status,
            "effective_from": e.effective_from,
            "effective_to": e.effective_to,
        }
        for e in db_exceptions
    ]
    ctx = QueryContext(
        animal=AnimalInput(**body.animal.model_dump()),
        place_id=body.place_id,
        zone_id=body.zone_id,
        date_time=body.date_time or datetime.now(UTC),
        intended_action=RuleAction(body.intended_action.value),
    )
    result = spec_evaluate(ctx, spec_rules, exceptions)
    return EvaluateOut(
        status=result.status.value,
        matched_rules=result.matched_rules,
        unmet_conditions=[
            {
                "rule_id": u.rule_id,
                "condition_type": u.condition_type,
                "kind": u.kind,
                "detail": u.detail,
            }
            for u in result.unmet_conditions
        ],
        unknown_inputs=[{"input": u.input, "reason": u.reason} for u in result.unknown_inputs],
        reason_codes=result.reason_codes,
        source_refs=result.source_refs,
    )


# --- admin / operator write ---


@admin.post("/rules", response_model=RuleOut, status_code=201)
def create_rule(
    body: RuleIn,
    user: User = Depends(require_role(UserRole.OPERATOR)),
    db: Session = Depends(get_db),
) -> AccessRule:
    if body.place_id is None and body.zone_id is None:
        raise ApiError("规则需要 place_id 或 zone_id")
    if body.zone_id:
        zone = db.get(Zone, body.zone_id)
        if zone is None:
            raise NotFound("区域不存在")
        owner_place = zone.place_id
    else:
        if db.get(Place, body.place_id) is None:
            raise NotFound("场所不存在")
        owner_place = None
    if db.get(Source, body.source_id) is None:
        raise NotFound("来源不存在")
    rule = AccessRule(
        place_id=body.place_id or owner_place,
        zone_id=body.zone_id,
        animal_scope=body.animal_scope,
        action=body.action,
        effect=body.effect,
        source_id=body.source_id,
        rule_origin=body.rule_origin,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
        recorded_at=datetime.now(UTC),
        review_due_at=body.review_due_at,
        status="current",
        # BLK-LAYER-02 / ADR-023: layer + normative force are first-class and
        # never defaulted here — a LEGAL rule must declare its mandatory_level.
        rule_layer=body.rule_layer,
        mandatory_level=body.mandatory_level.value if body.mandatory_level else None,
        note=body.note,
    )
    db.add(rule)
    db.flush()
    for c in body.conditions:
        db.add(type(rule).conditions.property.mapper.class_(rule_id=rule.id, **c.model_dump()))
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="rule.create",
        target_type="access_rule",
        target_id=str(rule.id),
        after_state={
            "effect": body.effect.value,
            "animal_scope": body.animal_scope.value,
            "action": body.action.value,
            "rule_layer": rule.rule_layer,
            "mandatory_level": rule.mandatory_level,
        },
    )
    db.commit()
    db.refresh(rule)
    return rule


@admin.patch("/rules/{rule_id}", response_model=RuleOut)
def update_rule(
    rule_id: str,
    body: RuleUpdate,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> AccessRule:
    rule = db.get(AccessRule, rule_id)
    if rule is None:
        raise NotFound("规则不存在")
    before = {"status": rule.status, "effect": rule.effect}
    data = body.model_dump(exclude_unset=True, exclude={"conditions"})
    for k, v in data.items():
        setattr(rule, k, v)
    if body.conditions is not None:
        rule.conditions.clear()
        db.flush()
        mapper = type(rule).conditions.property.mapper.class_
        for c in body.conditions:
            db.add(mapper(rule_id=rule.id, **c.model_dump()))
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="rule.update",
        target_type="access_rule",
        target_id=rule_id,
        before_state=before,
        after_state=data,
    )
    db.commit()
    db.refresh(rule)
    return rule
