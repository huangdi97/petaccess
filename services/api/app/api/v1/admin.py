"""Admin endpoints: audit log, data quality, users, queues (design #25, #31)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.models import (
    AccessRule,
    AuditLog,
    DisputeCase,
    ObservationClaim,
    OperatorClaim,
    Place,
    Source,
    User,
    VerificationEvent,
)
from app.models.enums import UserRole
from app.schemas.civic import AuditOut
from app.schemas.common import Page

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit", response_model=Page[AuditOut])
def list_audit(
    target_type: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[AuditOut]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if target_type:
        stmt = stmt.where(AuditLog.target_type == target_type)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


@router.get("/users", response_model=Page[dict])
def list_users(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> Page[dict]:
    stmt = select(User).order_by(User.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [
        {
            "id": u.id,
            "display_name": u.display_name,
            "email": u.email,
            "role": str(u.role),
            "status": u.status,
            "created_at": u.created_at,
        }
        for u in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/quality", response_model=dict)
def quality_dashboard(
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    """KPI skeleton from design #37 (Rule Coverage, Median Rule Age, etc.)."""
    total_rules = db.scalar(select(func.count()).select_from(AccessRule)) or 0
    current_rules = (
        db.scalar(
            select(func.count()).select_from(AccessRule).where(AccessRule.status == "current")
        )
        or 0
    )
    rules_with_source = (
        db.scalar(
            select(func.count()).select_from(AccessRule).where(AccessRule.source_id.isnot(None))
        )
        or 0
    )
    official_sources = (
        db.scalar(
            select(func.count())
            .select_from(Source)
            .where(
                Source.source_type.in_(
                    ["statute_or_regulation", "government_service", "official_operator_policy"]
                )
            )
        )
        or 0
    )
    total_sources = db.scalar(select(func.count()).select_from(Source)) or 0
    now = func.now()
    overdue = (
        db.scalar(
            select(func.count())
            .select_from(AccessRule)
            .where(AccessRule.review_due_at.isnot(None), AccessRule.review_due_at < now)
        )
        or 0
    )
    places_total = db.scalar(select(func.count()).select_from(Place)) or 0
    places_with_rules = (
        db.scalar(
            select(func.count()).select_from(select(AccessRule.place_id).distinct().subquery())
        )
        or 0
    )
    return {
        "rule_coverage": {
            "places_total": places_total,
            "places_with_rules": places_with_rules,
            "coverage_ratio": round(places_with_rules / places_total, 3) if places_total else 0,
        },
        "rules": {
            "total": total_rules,
            "current": current_rules,
            "with_source": rules_with_source,
            "source_coverage": round(rules_with_source / total_rules, 3) if total_rules else 0,
            "review_overdue": overdue,
        },
        "provenance": {
            "sources_total": total_sources,
            "official_ratio": round(official_sources / total_sources, 3) if total_sources else 0,
        },
        "contributions": {
            "observations": db.scalar(select(func.count()).select_from(ObservationClaim)) or 0,
            "verifications": db.scalar(select(func.count()).select_from(VerificationEvent)) or 0,
        },
        "queues": {
            "operator_claims_pending": db.scalar(
                select(func.count())
                .select_from(OperatorClaim)
                .where(OperatorClaim.status.in_(["submitted", "verifying"]))
            )
            or 0,
            "disputes_open": db.scalar(
                select(func.count())
                .select_from(DisputeCase)
                .where(DisputeCase.status.notin_(["resolved", "withdrawn"]))
            )
            or 0,
        },
    }


@router.get("/observations", response_model=Page[dict])
def list_all_observations(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[dict]:
    """All observations for moderation (design #25 Contributions queue)."""
    stmt = select(ObservationClaim).order_by(ObservationClaim.reported_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [
        {
            "id": o.id,
            "place_id": o.place_id,
            "occurred_at": o.occurred_at,
            "animal_scope": o.animal_scope,
            "observed_action": o.observed_action,
            "staff_action": o.staff_action,
            "place_confidence": o.place_confidence,
            "dispute_status": o.dispute_status,
            "withdrawn_at": o.withdrawn_at,
            "note": o.note,
            "proximity_verified": o.proximity_verified,
        }
        for o in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/ai-queue", response_model=Page[dict])
def ai_extraction_queue(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[dict]:
    """Observations with evidence awaiting OCR/extraction review (mock queue)."""
    stmt = (
        select(ObservationClaim)
        .where(ObservationClaim.evidence_support.isnot(None))
        .order_by(ObservationClaim.reported_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [
        {
            "id": o.id,
            "place_id": o.place_id,
            "reported_at": o.reported_at,
            "evidence_support": o.evidence_support,
            "state": "pending_extraction",
        }
        for o in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/conflicts", response_model=Page[dict])
def conflict_review(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[dict]:
    """Places with disputed rules or operator-vs-signage effect conflicts."""
    disputed = db.scalars(select(AccessRule).where(AccessRule.status == "disputed")).all()
    items = [
        {
            "rule_id": r.id,
            "place_id": r.place_id,
            "zone_id": r.zone_id,
            "effect": r.effect,
            "status": r.status,
            "source_id": r.source_id,
        }
        for r in disputed
    ]
    return Page(items=items[offset : offset + limit], total=len(items), limit=limit, offset=offset)
