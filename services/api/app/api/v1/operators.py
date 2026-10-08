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
from app.models import Operator, OperatorClaim, Place, User
from app.models.enums import OperatorClaimStatus, UserRole
from app.schemas.civic import (
    OperatorClaimIn,
    OperatorClaimOut,
    OperatorClaimSelfServeIn,
    OperatorClaimReview,
    OperatorQuestionnaire,
)
from app.schemas.common import Page
from app.services.operator_policy import apply_operator_questionnaire

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


@router.get("/operator-claims/mine", response_model=list[OperatorClaimOut])
def my_operator_claims(
    place_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OperatorClaim]:
    """Return only the caller's own claim transactions, newest first."""
    stmt = (
        select(OperatorClaim)
        .where(OperatorClaim.claimant_user_id == user.id)
        .order_by(OperatorClaim.created_at.desc())
    )
    if place_id:
        stmt = stmt.where(OperatorClaim.place_id == place_id)
    return list(db.scalars(stmt.limit(50)).all())


@router.post("/operator-claims/self-serve", response_model=OperatorClaimOut, status_code=201)
def submit_self_serve_claim(
    body: OperatorClaimSelfServeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OperatorClaim:
    """Start a venue/operator claim without exposing internal operator IDs.

    Submission grants no authority. It creates or reuses an unverified
    Operator identity and leaves the claim in the normal moderator review
    workflow; rules remain untouched until a later approved questionnaire.
    """
    if not get_settings().feature_operator_claim:
        raise ApiError("管理方认领未开放", code="feature_disabled", status_code=403)

    place = db.get(Place, body.place_id)
    if place is None:
        raise NotFound("场所不存在")

    existing = db.scalar(
        select(OperatorClaim).where(
            OperatorClaim.place_id == body.place_id,
            OperatorClaim.status.in_(["submitted", "verifying", "approved"]),
        )
    )
    if existing:
        raise ApiError("该场所已有进行中的认领", code="claim_conflict", status_code=409)

    operator = db.get(Operator, place.operator_id) if place.operator_id else None
    if operator is None:
        normalized_name = body.operator_name.strip()
        operator = db.scalar(
            select(Operator).where(func.lower(Operator.name) == normalized_name.lower())
        )
        if operator is None:
            operator = Operator(
                name=normalized_name,
                org_type=body.org_type,
                contact_email=body.work_email,
                website=body.website,
                verified=False,
            )
            db.add(operator)
            db.flush()

    claim = OperatorClaim(
        place_id=body.place_id,
        operator_id=operator.id,
        claimant_user_id=user.id,
        verification_method=body.verification_method,
        evidence_refs={
            "work_email": body.work_email,
            "website": body.website,
            "verification_note": body.verification_note,
            "self_serve": True,
        },
    )
    db.add(claim)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.OPERATOR_CLAIM_CREATE.value,
        target_type="operator_claim",
        target_id=claim.id,
        after_state={
            "place_id": body.place_id,
            "operator_id": operator.id,
            "status": str(claim.status),
            "self_serve": True,
        },
    )
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

    return apply_operator_questionnaire(
        db,
        claim=claim,
        operator=operator,
        body=body,
        actor=user,
    )
