"""Composable builders for the admin data-quality dashboard."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.models import (
    AccessRule,
    DisputeCase,
    EvidenceBundle,
    ObservationClaim,
    OperatorClaim,
    Place,
    RuleCandidate,
    Source,
    SourceArtifact,
    VerificationEvent,
)
from app.models.evidence import SourcePlatform
from app.services.quality_metrics import (
    age_days,
    distribution,
    is_overdue,
    median_age_days,
    ratio,
)

CANDIDATE_STATUSES = [
    "DISCOVERED",
    "EXTRACTED",
    "MATCH_PENDING",
    "REVIEW_PENDING",
    "APPROVED",
    "REJECTED",
    "PUBLISHED",
]
RULE_LAYERS = ["LEGAL", "REGULATORY_GUIDANCE", "OPERATOR_POLICY", "TEMPORARY_POLICY"]
RULE_EFFECTS = ["allowed", "conditional", "prohibited"]
OFFICIAL_SOURCE_TYPES = [
    "statute_or_regulation",
    "government_service",
    "official_operator_policy",
]


def _count(db: Session, model: type, *predicates: ColumnElement[bool]) -> int:
    stmt = select(func.count()).select_from(model)
    if predicates:
        stmt = stmt.where(*predicates)
    return db.scalar(stmt) or 0


def _rule_metrics(db: Session, now: datetime) -> tuple[dict, dict]:
    total = _count(db, AccessRule)
    current = _count(db, AccessRule, AccessRule.status == "current")
    with_source = _count(db, AccessRule, AccessRule.source_id.isnot(None))
    places_total = _count(db, Place)
    places_with_rules = (
        db.scalar(
            select(func.count()).select_from(select(AccessRule.place_id).distinct().subquery())
        )
        or 0
    )
    due_rows = db.execute(
        select(AccessRule.review_due_at, AccessRule.status).where(
            AccessRule.review_due_at.isnot(None)
        )
    ).all()
    ages = db.scalars(select(AccessRule.recorded_at).where(AccessRule.status == "current")).all()
    effects = db.scalars(select(AccessRule.effect)).all()

    coverage = {
        "places_total": places_total,
        "places_with_rules": places_with_rules,
        "coverage_ratio": ratio(places_with_rules, places_total),
    }
    rules = {
        "total": total,
        "current": current,
        "with_source": with_source,
        "source_coverage": ratio(with_source, total),
        "review_overdue": sum(1 for due_at, status in due_rows if is_overdue(due_at, status, now)),
        "never_verified": _count(
            db,
            AccessRule,
            AccessRule.status == "current",
            AccessRule.last_verified_at.is_(None),
        ),
        "by_effect": distribution(RULE_EFFECTS, effects),
        "age_days": {
            "median": median_age_days(ages, now),
            "oldest": max((age_days(value, now) or 0 for value in ages), default=None),
            "newest": min((age_days(value, now) or 0 for value in ages), default=None),
        },
    }
    return coverage, rules


def _candidate_metrics(db: Session) -> dict:
    status_rows = db.scalars(select(RuleCandidate.review_status)).all()
    layer_rows = db.scalars(select(RuleCandidate.rule_layer)).all()
    total = len(status_rows)
    without_evidence = _count(db, RuleCandidate, RuleCandidate.evidence_bundle_id.is_(None))
    return {
        "total": total,
        "by_status": distribution(CANDIDATE_STATUSES, status_rows),
        "by_layer": distribution(RULE_LAYERS, layer_rows),
        "without_evidence": without_evidence,
        "evidence_coverage": ratio(total - without_evidence, total),
        "published": _count(db, RuleCandidate, RuleCandidate.published_rule_id.isnot(None)),
    }


def _evidence_metrics(db: Session) -> dict:
    bundles_total = _count(db, EvidenceBundle)
    with_hash = _count(db, EvidenceBundle, EvidenceBundle.content_hash.isnot(None))
    with_license = _count(db, EvidenceBundle, EvidenceBundle.license_metadata.isnot(None))
    return {
        "artifacts_total": _count(db, SourceArtifact),
        "bundles_total": bundles_total,
        "with_content_hash": with_hash,
        "hash_coverage": ratio(with_hash, bundles_total),
        "with_license_metadata": with_license,
        "license_coverage": ratio(with_license, bundles_total),
        "lead_only": _count(
            db,
            EvidenceBundle,
            EvidenceBundle.source_platform.in_(SourcePlatform.LEAD_ONLY),
        ),
    }


def _provenance_metrics(db: Session) -> dict:
    total = _count(db, Source)
    official = _count(db, Source, Source.source_type.in_(OFFICIAL_SOURCE_TYPES))
    return {"sources_total": total, "official_ratio": ratio(official, total)}


def _operational_metrics(db: Session) -> tuple[dict, dict]:
    contributions = {
        "observations": _count(db, ObservationClaim),
        "verifications": _count(db, VerificationEvent),
    }
    queues = {
        "operator_claims_pending": _count(
            db,
            OperatorClaim,
            OperatorClaim.status.in_(["submitted", "verifying"]),
        ),
        "disputes_open": _count(
            db,
            DisputeCase,
            DisputeCase.status.notin_(["resolved", "withdrawn"]),
        ),
    }
    return contributions, queues


def build_quality_dashboard(db: Session, now: datetime) -> dict:
    coverage, rules = _rule_metrics(db, now)
    contributions, queues = _operational_metrics(db)
    return {
        "generated_at": now.isoformat(),
        "rule_coverage": coverage,
        "rules": rules,
        "candidates": _candidate_metrics(db),
        "evidence": _evidence_metrics(db),
        "provenance": _provenance_metrics(db),
        "contributions": contributions,
        "queues": queues,
    }
