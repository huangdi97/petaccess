"""Operator claim + structured questionnaire endpoints (design #16, GOAL #13).

Flow: community creates place → operator claims → admin approves → operator
submits questionnaire → operator-declared rules (versioned by superseding).
Operators can edit their own declarations but can NEVER delete user
observations (design #16) — there is no such endpoint.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.audit_events import AuditEvent
from app.core.config import get_settings
from app.core.errors import ApiError, NotFound, PermissionDenied
from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models import AccessRule, Operator, OperatorClaim, Place, RuleCondition, Source, User
from app.models.enums import OperatorClaimStatus, RuleOrigin, RuleStatus, UserRole
from app.schemas.civic import (
    OperatorClaimIn,
    OperatorClaimOut,
    OperatorClaimReview,
    OperatorQuestionnaire,
)
from app.schemas.common import Page

router = APIRouter(tags=["operators"])
admin = APIRouter(tags=["admin:operators"])


@router.post("/operator-claims", response_model=OperatorClaimOut, status_code=201)
def submit_claim(
    body: OperatorClaimIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OperatorClaim:
    if not get_settings().feature_operator_claim:
        raise ApiError("管理方认领未开放", code="feature_disabled", status_code=403)
    if db.get(Place, body.place_id) is None:
        raise NotFound("场所不存在")
    if db.get(Operator, body.operator_id) is None:
        raise NotFound("管理方不存在")
    existing = db.scalar(
        select(OperatorClaim).where(
            OperatorClaim.place_id == body.place_id,
            OperatorClaim.status.in_(["submitted", "verifying", "approved"]),
        )
    )
    if existing:
        raise ApiError("该场所已有进行中的认领", code="claim_conflict", status_code=409)
    claim = OperatorClaim(
        place_id=body.place_id,
        operator_id=body.operator_id,
        claimant_user_id=user.id,
        verification_method=body.verification_method,
        evidence_refs=body.evidence_refs,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


@admin.get("/operator-claims", response_model=Page[OperatorClaimOut])
def list_claims(
    status: str | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[OperatorClaimOut]:
    stmt = select(OperatorClaim).order_by(OperatorClaim.created_at.desc())
    if status:
        stmt = stmt.where(OperatorClaim.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


@admin.post("/operator-claims/{claim_id}/review", response_model=OperatorClaimOut)
def review_claim(
    claim_id: str,
    body: OperatorClaimReview,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> OperatorClaim:
    claim = db.get(OperatorClaim, claim_id)
    if claim is None:
        raise NotFound("认领不存在")
    if claim.status == OperatorClaimStatus.APPROVED and not body.approve:
        raise ApiError("已批准的认领需先撤销", code="invalid_transition")
    before_status = claim.status
    claim.status = OperatorClaimStatus.APPROVED if body.approve else OperatorClaimStatus.REJECTED
    claim.reviewed_by = user.id
    claim.reviewed_at = datetime.now(UTC)
    if body.approve:
        operator = db.get(Operator, claim.operator_id)
        if operator:
            operator.verified = True
        place = db.get(Place, claim.place_id)
        if place:
            place.operator_id = claim.operator_id
    else:
        claim.rejection_reason = body.rejection_reason
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.OPERATOR_CLAIM_REVIEW.value,
        target_type="operator_claim",
        target_id=claim_id,
        before_state={"status": str(before_status)},
        after_state={"status": str(claim.status)},
    )
    db.commit()
    db.refresh(claim)
    return claim


@router.post("/operator-claims/{claim_id}/questionnaire", status_code=201)
def submit_questionnaire(
    claim_id: str,
    body: OperatorQuestionnaire,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Convert structured questionnaire answers into operator-declared rules.

    Each answer: {zone_id|place scope, animal_scope, action, effect, conditions[]}
    Creates a new operator source if needed and supersedes prior operator rules.
    """
    claim = db.get(OperatorClaim, claim_id)
    if claim is None:
        raise NotFound("认领不存在")
    if claim.claimant_user_id != user.id and user.role not in ("admin", "moderator"):
        raise PermissionDenied("只有认领人可提交问卷")
    if claim.status != OperatorClaimStatus.APPROVED:
        raise ApiError("认领尚未批准", code="claim_not_approved")
    operator = db.get(Operator, claim.operator_id)
    if operator is None:
        raise NotFound("管理方不存在")

    source = db.scalar(
        select(Source).where(
            Source.source_type == "official_operator_policy",
            Source.issuer == operator.name,
        )
    )
    if source is None:
        source = Source(
            source_type="official_operator_policy",
            issuer=operator.name,
            issuer_verification="verified",
            directness="direct",
            collected_at=datetime.now(UTC),
        )
        db.add(source)
        db.flush()

    created_rules: list[str] = []
    # operator declaration is authoritative: supersede ALL current rules on
    # the place regardless of origin (community/signage rules are archived as history)
    prior_rules = db.scalars(
        select(AccessRule).where(
            AccessRule.place_id == claim.place_id,
            AccessRule.status == "current",
        )
    ).all()
    for prior in prior_rules:
        prior.status = RuleStatus.SUPERSEDED
        prior.effective_to = datetime.now(UTC)

    for ans in body.answers:
        rule = AccessRule(
            place_id=claim.place_id,
            zone_id=ans.get("zone_id"),
            animal_scope=ans["animal_scope"],
            action=ans["action"],
            effect=ans["effect"],
            source_id=source.id,
            rule_origin=RuleOrigin.OPERATOR_DECLARED,
            recorded_at=datetime.now(UTC),
            effective_from=body.effective_from or datetime.now(UTC),
            review_due_at=ans.get("review_due_at"),
            status="current",
            note=ans.get("note"),
        )
        db.add(rule)
        db.flush()
        for c in ans.get("conditions", []):
            db.add(RuleCondition(rule_id=rule.id, **c))
        created_rules.append(rule.id)

    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.OPERATOR_QUESTIONNAIRE_SUBMIT.value,
        target_type="place",
        target_id=claim.place_id,
        after_state={"created_rules": created_rules, "superseded": [r.id for r in prior_rules]},
    )
    db.commit()
    return {"created_rules": created_rules, "source_id": source.id}
