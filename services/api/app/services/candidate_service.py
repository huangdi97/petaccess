"""RuleCandidate pipeline service (NEXT_GOAL §B3, DATA_PIPELINE_SPEC).

Hard boundary: every candidate MUST walk the state machine to APPROVED and be
PUBLISHED before any AccessRule exists. OCR/AI/monitor/import outputs can only
create candidates — never rules.

DISCOVERED → EXTRACTED → MATCH_PENDING → REVIEW_PENDING → APPROVED → PUBLISHED
(any state except PUBLISHED/SUPERSEDED can be REJECTED)
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import AccessRule, RuleCandidate, Source
from app.models.enums import RuleStatus
from app.models.v05 import CANDIDATE_TRANSITIONS


def transition(
    candidate: RuleCandidate, target: str, reviewer_id: str | None = None, note: str | None = None
) -> RuleCandidate:
    current = candidate.review_status
    if target not in CANDIDATE_TRANSITIONS.get(current, set()):
        raise ApiError(
            f"非法状态迁移 {current} → {target}",
            code="invalid_candidate_transition",
        )
    candidate.review_status = target
    if reviewer_id:
        candidate.reviewer_id = reviewer_id
    if note:
        candidate.review_note = note[:500]
    return candidate


def create_from_extraction(
    db: Session,
    *,
    source_id: str,
    extraction_method: str,
    place_id: str | None = None,
    zone_id: str | None = None,
    animal_scope: str | None = None,
    action: str | None = None,
    effect: str | None = None,
    proposed_conditions: list | None = None,
    extraction_provider: str | None = None,
    internal_confidence: float | None = None,
    raw_text: str | None = None,
    media_id: str | None = None,
    evidence_bundle_id: str | None = None,
) -> RuleCandidate:
    """Entry point for OCR/AI/monitor/import outputs. Creates the candidate in
    MATCH_PENDING when extraction already produced structured fields (the next
    human step is REVIEW), else EXTRACTED."""
    status = "MATCH_PENDING" if (animal_scope and action and effect) else "EXTRACTED"
    candidate = RuleCandidate(
        source_id=source_id,
        place_id=place_id,
        zone_id=zone_id,
        animal_scope=animal_scope,
        action=action,
        effect=effect,
        proposed_conditions=proposed_conditions,
        extraction_method=extraction_method,
        extraction_provider=extraction_provider,
        internal_confidence=internal_confidence,
        raw_text=raw_text[:4000] if raw_text else None,
        media_id=media_id,
        evidence_bundle_id=evidence_bundle_id,
        review_status=status,
    )
    db.add(candidate)
    db.flush()
    return candidate


def publish(
    db: Session, candidate: RuleCandidate, reviewer_id: str, note: str | None = None
) -> AccessRule:
    """APPROVED → PUBLISHED: creates the AccessRule with a non-null rule_layer.

    Candidate fields were matched to place/zone in MATCH_PENDING; publishing
    here is the single bridge into the normative rule set.
    """
    if candidate.review_status != "APPROVED":
        raise ApiError("只有 APPROVED 的候选可发布", code="candidate_not_approved")
    if not candidate.place_id and not candidate.zone_id:
        raise ApiError("候选缺少 place/zone 归属", code="candidate_unmatched")
    source = db.get(Source, candidate.source_id)
    if source is None:
        raise ApiError("来源不存在", code="source_missing")
    # Pre-Publish Validation (S8): evidence / place match / schema support /
    # unresolved conflict / freshness / data license — all must pass.
    from app.services.publish_gate import validate_for_publish

    validate_for_publish(db, candidate)
    if candidate.evidence_bundle_id:
        # Publish boundary for the evidence chain (brief §5/§10): a lead-only
        # platform bundle without a redistribution licence can be reviewed but
        # never published, and rule evidence must stay traceable to its quote/hash.
        from app.models.evidence import EvidenceBundle
        from app.services.evidence_service import ClaimKind, assert_publishable

        bundle = db.get(EvidenceBundle, candidate.evidence_bundle_id)
        if bundle is None:
            raise ApiError("证据包不存在", code="evidence_bundle_missing")
        assert_publishable(bundle, kind=ClaimKind.RULE)

    rule = AccessRule(
        place_id=candidate.place_id,
        zone_id=candidate.zone_id,
        animal_scope=candidate.animal_scope,
        action=candidate.action,
        effect=candidate.effect,
        source_id=candidate.source_id,
        rule_origin="onsite_signage"
        if candidate.extraction_method in ("ocr", "user_upload")
        else "imported",
        recorded_at=datetime.now(UTC),
        status="current",
        rule_layer="OPERATOR_POLICY",
        note=f"published from candidate {candidate.id} ({candidate.extraction_method})",
    )
    db.add(rule)
    db.flush()

    # Same-issuer policy change: the source updated its own rule, so current
    # rules from THAT source with the same owner+scope+action are superseded
    # here (history preserved via supersedes_rule_id). Cross-source conflicts
    # never reach this point — the publish gate blocks them as unresolved.
    superseded_same_source = db.scalars(
        select(AccessRule).where(
            AccessRule.place_id == candidate.place_id
            if candidate.zone_id is None
            else AccessRule.zone_id == candidate.zone_id,
            AccessRule.status == "current",
            AccessRule.source_id == candidate.source_id,
            AccessRule.animal_scope == candidate.animal_scope,
            AccessRule.action == candidate.action,
            AccessRule.id != rule.id,  # never supersede the rule just created
        )
    ).all()
    for old_rule in superseded_same_source:
        old_rule.status = RuleStatus.SUPERSEDED
        rule.supersedes_rule_id = old_rule.id

    # Atomic compare-and-set on the candidate status: two reviewers publishing
    # the same APPROVED candidate must yield exactly one AccessRule. The loser's
    # CAS matches 0 rows, the whole transaction (rule included) rolls back.
    updated = db.execute(
        update(RuleCandidate)
        .where(RuleCandidate.id == candidate.id, RuleCandidate.review_status == "APPROVED")
        .values(
            review_status="PUBLISHED",
            published_rule_id=rule.id,
            reviewer_id=reviewer_id,
            review_note=(note or "")[:500] or None,
        )
    )
    updated_rowcount: int | None = getattr(updated, "rowcount", None)
    if updated_rowcount != 1:
        db.rollback()
        raise ApiError("候选已被并发发布", code="candidate_already_published")

    from app.models import RuleCondition

    for cond in candidate.proposed_conditions or []:
        db.add(
            RuleCondition(
                rule_id=rule.id,
                **{
                    "condition_type": cond.get("condition_type") or cond.get("type"),
                    "value_flag": cond.get(
                        "value_flag",
                        cond.get("value") if isinstance(cond.get("value"), bool) else None,
                    ),
                    "value_numeric": cond.get(
                        "value_numeric",
                        cond.get("value")
                        if isinstance(cond.get("value"), (int, float))
                        and not isinstance(cond.get("value"), bool)
                        else None,
                    ),
                    "value_text": cond.get("value_text"),
                    "value_json": cond.get("value_json"),
                },
            )
        )

    # mirror the CAS result onto the ORM object the caller holds
    candidate.review_status = "PUBLISHED"
    candidate.published_rule_id = rule.id
    candidate.reviewer_id = reviewer_id
    if note:
        candidate.review_note = note[:500]
    return rule
