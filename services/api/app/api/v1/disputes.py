"""Dispute lifecycle endpoints (design #26, GOAL #15).

Flow: submit → (admin) temporary action / forwarding → counter statement →
review → resolution → audit. The operator/observer dispute flow targets either
an access_rule or an observation_claim; user observations cannot be deleted by
operators — disputes go through this auditable pipeline instead.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.audit_events import AuditEvent
from app.core.config import get_settings
from app.core.errors import ApiError, NotFound
from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models import AccessRule, DisputeCase, ObservationClaim, User
from app.models.enums import (
    DisputeCaseStatus,
    ObservationDisputeStatus,
    RuleStatus,
    UserRole,
)
from app.schemas.civic import (
    CounterStatementIn,
    DisputeIn,
    DisputeOut,
    DisputeResolutionIn,
    DisputeReview,
)
from app.schemas.common import Page

router = APIRouter(tags=["disputes"])
admin = APIRouter(tags=["admin:disputes"])


@router.post("/disputes", response_model=DisputeOut, status_code=201)
def submit_dispute(
    body: DisputeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DisputeCase:
    if not get_settings().feature_dispute:
        raise ApiError("异议功能未开放", code="feature_disabled", status_code=403)
    # target must exist
    if body.target_type == "access_rule":
        if db.get(AccessRule, body.target_id) is None:
            raise NotFound("目标规则不存在")
    elif body.target_type == "observation_claim":
        if db.get(ObservationClaim, body.target_id) is None:
            raise NotFound("目标观察不存在")
    else:
        raise ApiError("不支持的异议目标类型")
    case = DisputeCase(
        target_type=body.target_type,
        target_id=body.target_id,
        claimant_user_id=user.id,
        reason_code=body.reason_code,
        notice_text=body.notice_text,
        evidence_refs=body.evidence_refs,
    )
    db.add(case)
    # mark the target as disputed (visible but flagged); content is preserved
    if body.target_type == "access_rule":
        rule = db.get(AccessRule, body.target_id)
        rule.status = RuleStatus.DISPUTED  # type: ignore[union-attr]
    else:
        obs = db.get(ObservationClaim, body.target_id)
        obs.dispute_status = ObservationDisputeStatus.OPEN  # type: ignore[union-attr]
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.DISPUTE_SUBMIT.value,
        target_type=body.target_type,
        target_id=body.target_id,
        after_state={"dispute_id": str(case.id), "reason_code": body.reason_code},
    )
    db.commit()
    db.refresh(case)
    return case


@router.get("/disputes/mine", response_model=Page[DisputeOut])
def my_disputes(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[DisputeOut]:
    rows = db.scalars(
        select(DisputeCase)
        .where(
            (DisputeCase.claimant_user_id == user.id)
            | (DisputeCase.counter_party_user_id == user.id)
        )
        .order_by(DisputeCase.created_at.desc())
    ).all()
    return Page(items=rows, total=len(rows), limit=len(rows), offset=0)


@router.post("/disputes/{case_id}/counter", response_model=DisputeOut)
def submit_counter_statement(
    case_id: str,
    body: CounterStatementIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DisputeCase:
    case = db.get(DisputeCase, case_id)
    if case is None:
        raise NotFound("异议不存在")
    case.counter_statement = body.counter_statement
    case.counter_party_user_id = user.id
    if case.status in (
        DisputeCaseStatus.SUBMITTED,
        DisputeCaseStatus.EVIDENCE_PENDING,
        DisputeCaseStatus.TEMPORARY_ACTION_APPLIED,
    ):
        case.status = DisputeCaseStatus.COUNTER_STATEMENT_RECEIVED
    db.commit()
    db.refresh(case)
    return case


@admin.get("/disputes", response_model=Page[DisputeOut])
def list_disputes(
    status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[DisputeOut]:
    stmt = select(DisputeCase).order_by(DisputeCase.created_at.desc())
    if status:
        stmt = stmt.where(DisputeCase.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


@admin.post("/disputes/{case_id}/review", response_model=DisputeOut)
def review_dispute(
    case_id: str,
    body: DisputeReview,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> DisputeCase:
    """Temporary action / forwarding while a dispute is open."""
    case = db.get(DisputeCase, case_id)
    if case is None:
        raise NotFound("异议不存在")
    if case.status == DisputeCaseStatus.RESOLVED:
        raise ApiError("异议已办结", code="already_resolved")
    changed: dict = {}
    if body.action is not None:
        case.temporary_action = body.action
        changed["temporary_action"] = body.action.value
        if body.action != "none":
            case.status = DisputeCaseStatus.TEMPORARY_ACTION_APPLIED
            changed["status"] = case.status.value
        # apply visible effects to the target
        if body.action == "mark_unverified":
            _apply_unverified(db, case)
    if body.forward_to:
        case.forwarded_to = body.forward_to
        case.status = DisputeCaseStatus.FORWARDED
        changed["forwarded_to"] = body.forward_to
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.DISPUTE_REVIEW.value,
        target_type="dispute_case",
        target_id=case_id,
        after_state=changed,
    )
    db.commit()
    db.refresh(case)
    return case


@admin.post("/disputes/{case_id}/resolve", response_model=DisputeOut)
def resolve_dispute(
    case_id: str,
    body: DisputeResolutionIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> DisputeCase:
    """Final resolution: restore / correct / archive / delete per design #26."""
    case = db.get(DisputeCase, case_id)
    if case is None:
        raise NotFound("异议不存在")
    applied: dict = {"resolution": body.resolution.value}
    if case.target_type == "access_rule":
        rule = db.get(AccessRule, case.target_id)
        if rule is not None:
            if body.resolution == "rule_restored":
                rule.status = RuleStatus.CURRENT
                applied["rule_status"] = "current"
            elif body.resolution in ("content_archived", "content_deleted"):
                rule.status = RuleStatus.ARCHIVED
                applied["rule_status"] = "archived"
            elif body.resolution == "no_change":
                rule.status = RuleStatus.CURRENT
    else:
        obs = db.get(ObservationClaim, case.target_id)
        if obs is not None:
            if body.resolution == "observation_upheld":
                obs.dispute_status = ObservationDisputeStatus.RESOLVED
            elif body.resolution in ("content_archived", "content_deleted"):
                obs.withdrawn_at = datetime.now(UTC)
                obs.dispute_status = ObservationDisputeStatus.RESOLVED
                applied["withdrawn"] = True
            else:
                obs.dispute_status = ObservationDisputeStatus.RESOLVED
    case.status = DisputeCaseStatus.RESOLVED
    case.resolution = body.resolution
    case.resolution_note = body.resolution_note
    case.reviewer_id = user.id
    case.resolved_at = datetime.now(UTC)
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.DISPUTE_RESOLVE.value,
        target_type="dispute_case",
        target_id=case_id,
        after_state=applied,
    )
    db.commit()
    db.refresh(case)
    return case


def _apply_unverified(db: Session, case: DisputeCase) -> None:
    if case.target_type == "access_rule":
        rule = db.get(AccessRule, case.target_id)
        if rule is not None:
            rule.last_verified_at = None
