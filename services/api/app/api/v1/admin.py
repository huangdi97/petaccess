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
from app.services.quality_metrics import (
    age_days,
    distribution,
    is_overdue,
    median_age_days,
    ratio,
)

router = APIRouter(prefix="/admin", tags=["admin"])

#: Candidate pipeline states, in the order the state machine allows them.
CANDIDATE_STATUSES = [
    "DISCOVERED",
    "EXTRACTED",
    "MATCH_PENDING",
    "REVIEW_PENDING",
    "APPROVED",
    "REJECTED",
    "PUBLISHED",
]

#: Rule layers, so the dashboard can show mis-routing at a glance.
RULE_LAYERS = ["LEGAL", "REGULATORY_GUIDANCE", "OPERATOR_POLICY", "TEMPORARY_POLICY"]

RULE_EFFECTS = ["allowed", "conditional", "prohibited"]


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
    """Operational KPIs (design #37; Master Goal P4 "data quality metrics").

    Deliberately reports raw, decomposable numbers — coverage ratios, pipeline
    distribution, freshness backlog — and no composite quality index. A blended
    score would be exactly the kind of unfalsifiable number this product refuses
    to show about places, so it refuses to show one about itself.
    """
    now = datetime.now(UTC)

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
    # Freshness backlog: only *current* rules past their review date need action.
    # Counting superseded rows here would inflate the queue with work nobody has
    # to do, so the decision lives in a unit-tested helper rather than inline SQL.
    due_rows = db.execute(
        select(AccessRule.review_due_at, AccessRule.status).where(
            AccessRule.review_due_at.isnot(None)
        )
    ).all()
    overdue = sum(1 for due_at, status in due_rows if is_overdue(due_at, status, now))
    places_total = db.scalar(select(func.count()).select_from(Place)) or 0
    places_with_rules = (
        db.scalar(
            select(func.count()).select_from(select(AccessRule.place_id).distinct().subquery())
        )
        or 0
    )

    # --- rule composition / freshness -------------------------------------
    effect_rows = db.scalars(select(AccessRule.effect)).all()
    rule_ages = db.scalars(
        select(AccessRule.recorded_at).where(AccessRule.status == "current")
    ).all()
    never_verified = (
        db.scalar(
            select(func.count())
            .select_from(AccessRule)
            .where(AccessRule.status == "current", AccessRule.last_verified_at.is_(None))
        )
        or 0
    )

    # --- candidate pipeline ------------------------------------------------
    candidate_status_rows = db.scalars(select(RuleCandidate.review_status)).all()
    candidate_layer_rows = db.scalars(select(RuleCandidate.rule_layer)).all()
    candidates_total = len(candidate_status_rows)
    candidates_without_evidence = (
        db.scalar(
            select(func.count())
            .select_from(RuleCandidate)
            .where(RuleCandidate.evidence_bundle_id.is_(None))
        )
        or 0
    )
    published_candidates = (
        db.scalar(
            select(func.count())
            .select_from(RuleCandidate)
            .where(RuleCandidate.published_rule_id.isnot(None))
        )
        or 0
    )

    # --- evidence integrity ------------------------------------------------
    bundles_total = db.scalar(select(func.count()).select_from(EvidenceBundle)) or 0
    bundles_with_hash = (
        db.scalar(
            select(func.count())
            .select_from(EvidenceBundle)
            .where(EvidenceBundle.content_hash.isnot(None))
        )
        or 0
    )
    bundles_with_license = (
        db.scalar(
            select(func.count())
            .select_from(EvidenceBundle)
            .where(EvidenceBundle.license_metadata.isnot(None))
        )
        or 0
    )
    lead_only_bundles = (
        db.scalar(
            select(func.count())
            .select_from(EvidenceBundle)
            .where(EvidenceBundle.source_platform.in_(SourcePlatform.LEAD_ONLY))
        )
        or 0
    )
    artifacts_total = db.scalar(select(func.count()).select_from(SourceArtifact)) or 0

    return {
        "generated_at": now.isoformat(),
        "rule_coverage": {
            "places_total": places_total,
            "places_with_rules": places_with_rules,
            "coverage_ratio": ratio(places_with_rules, places_total),
        },
        "rules": {
            "total": total_rules,
            "current": current_rules,
            "with_source": rules_with_source,
            "source_coverage": ratio(rules_with_source, total_rules),
            "review_overdue": overdue,
            "never_verified": never_verified,
            "by_effect": distribution(RULE_EFFECTS, effect_rows),
            "age_days": {
                "median": median_age_days(rule_ages, now),
                "oldest": max((age_days(a, now) or 0 for a in rule_ages), default=None),
                "newest": min((age_days(a, now) or 0 for a in rule_ages), default=None),
            },
        },
        "candidates": {
            "total": candidates_total,
            "by_status": distribution(CANDIDATE_STATUSES, candidate_status_rows),
            "by_layer": distribution(RULE_LAYERS, candidate_layer_rows),
            "without_evidence": candidates_without_evidence,
            "evidence_coverage": ratio(
                candidates_total - candidates_without_evidence, candidates_total
            ),
            "published": published_candidates,
        },
        "evidence": {
            "artifacts_total": artifacts_total,
            "bundles_total": bundles_total,
            "with_content_hash": bundles_with_hash,
            "hash_coverage": ratio(bundles_with_hash, bundles_total),
            "with_license_metadata": bundles_with_license,
            "license_coverage": ratio(bundles_with_license, bundles_total),
            "lead_only": lead_only_bundles,
        },
        "provenance": {
            "sources_total": total_sources,
            "official_ratio": ratio(official_sources, total_sources),
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
