"""RuleCandidate pipeline service (NEXT_GOAL §B3, DATA_PIPELINE_SPEC).

Hard boundary: every candidate MUST walk the state machine to APPROVED and be
PUBLISHED before any AccessRule exists. OCR/AI/monitor/import outputs can only
create candidates — never rules.

DISCOVERED → EXTRACTED → MATCH_PENDING → REVIEW_PENDING → APPROVED → PUBLISHED
(any state except PUBLISHED/SUPERSEDED can be REJECTED)
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import AccessRule, RuleCandidate, Source
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

    candidate.review_status = "PUBLISHED"
    candidate.published_rule_id = rule.id
    candidate.reviewer_id = reviewer_id
    if note:
        candidate.review_note = note[:500]
    return rule
