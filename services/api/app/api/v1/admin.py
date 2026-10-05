"""Admin endpoints: audit log, data quality, users, queues (design #25, #31)."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.session import get_db
from app.models import (
    AccessRule,
    AuditLog,
    DisputeCase,
    EvidenceBundle,
    ObservationClaim,
    OperatorClaim,
    Place,
    RuleCandidate,
    Source,
    SourceArtifact,
    User,
    VerificationEvent,
)
from app.models.enums import UserRole
from app.models.evidence import SourcePlatform
from app.schemas.civic import AuditOut
from app.schemas.common import Page
from app.services.admin_quality_dashboard import build_quality_dashboard

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
    """Operational KPIs with decomposable metrics and no composite score."""
    return build_quality_dashboard(db, datetime.now(UTC))


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


@router.get("/worker/jobs", response_model=dict)
def worker_job_visibility(
    limit: int = Query(default=50, le=200),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> dict:
    """Failed-job visibility + worker liveness (NEXT_GOAL §A5)."""
    from app.core.observability import list_failed_jobs
    from app.worker.celery_app import celery_app as celery

    try:
        pings = celery.control.ping(timeout=2)
        workers = list(pings[0].keys()) if pings else []
    except Exception:
        workers = []
    return {"workers_online": workers, "failed_jobs": list_failed_jobs(limit)}
