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
from app.models import AccessRule, RuleCandidate, RuleException, Source
from app.models.enums import RuleStatus
from app.models.v05 import CANDIDATE_TRANSITIONS
from app.services.condition_ingest import normalize_conditions


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
    rule_layer: str | None = None,
    mandatory_level: str | None = None,
    proposed_conditions: list | None = None,
    extraction_provider: str | None = None,
    internal_confidence: float | None = None,
    raw_text: str | None = None,
    media_id: str | None = None,
    evidence_bundle_id: str | None = None,
    # --- ADR-025 / ADR-028: source-faithful scope ---------------------------
    source_scope_exact: str | None = None,
    subject_scope_normalized: str | None = None,
    normalization_type: str | None = None,
    normative_effect: str | None = None,
    holder_scope: str | None = None,
    operator_obligations: list | None = None,
    # --- Wave 01 -------------------------------------------------------------
    expansion_run_id: str | None = None,
    dedup_key: str | None = None,
) -> RuleCandidate:
    """Entry point for OCR/AI/monitor/import outputs. Creates the candidate in
    MATCH_PENDING when extraction already produced structured fields (the next
    human step is REVIEW), else EXTRACTED.

    ``proposed_conditions`` arrives from *outside* the platform (an extractor, a
    spreadsheet import), so it is normalised to the canonical
    ``condition_type`` key here and nowhere else (ADR-029). A condition list the
    platform cannot read is refused at the door rather than discovered at
    publish time, long after a human approved it.
    """
    status = "MATCH_PENDING" if (animal_scope and action and effect) else "EXTRACTED"
    candidate = RuleCandidate(
        source_id=source_id,
        place_id=place_id,
        zone_id=zone_id,
        animal_scope=animal_scope,
        action=action,
        effect=effect,
        rule_layer=rule_layer or "OPERATOR_POLICY",
        mandatory_level=mandatory_level,
        proposed_conditions=normalize_conditions(proposed_conditions),
        extraction_method=extraction_method,
        extraction_provider=extraction_provider,
        internal_confidence=internal_confidence,
        raw_text=raw_text[:4000] if raw_text else None,
        media_id=media_id,
        evidence_bundle_id=evidence_bundle_id,
        review_status=status,
        # ADR-025 / ADR-028: what the source literally said, and how it was
        # turned into the stored subject. Publishing copies these verbatim, so a
        # candidate that never carried them would publish an unscoped rule.
        source_scope_exact=source_scope_exact,
        subject_scope_normalized=subject_scope_normalized,
        normalization_type=normalization_type,
        normative_effect=normative_effect,
        holder_scope=holder_scope,
        operator_obligations=operator_obligations,
        expansion_run_id=expansion_run_id,
        dedup_key=dedup_key,
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
        # The candidate's declared layer is carried through verbatim: the
        # resolver routes LEGAL / REGULATORY_GUIDANCE / TEMPORARY_POLICY /
        # OPERATOR_POLICY into different precedence pools, so flattening a
        # statutory prohibition to an operator policy would silently change
        # the answer. Pre-Publish Validation rejects unknown layer values.
        rule_layer=candidate.rule_layer or "OPERATOR_POLICY",
        # Normative force is carried through verbatim (BLK-LAYER-02 / ADR-023).
        # The publish gate refuses a LEGAL candidate without an explicit level,
        # so a statutory prohibition can never land as a relaxable rule.
        mandatory_level=candidate.mandatory_level,
        # ADR-025 / ADR-028: the source-faithful scope MUST survive publication.
        # Without this the published AccessRule keeps only the coarse
        # `animal_scope`, and the resolver then treats a bare `service_dog` row as
        # the unproven widening (governs nothing) — the 导盲犬 carve-out would
        # silently stop working the moment it went live.
        source_scope_exact=candidate.source_scope_exact,
        subject_scope_normalized=candidate.subject_scope_normalized,
        normalization_type=candidate.normalization_type,
        normative_effect=candidate.normative_effect,
        holder_scope=candidate.holder_scope,
        operator_obligations=candidate.operator_obligations,
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
                    "condition_type": cond["condition_type"],
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


def publish_exception(
    db: Session,
    candidate: RuleCandidate,
    *,
    base_rule_id: str,
    reviewer_id: str,
    note: str | None = None,
) -> RuleException:
    """APPROVED → PUBLISHED **as a carve-out on an existing base AccessRule**.

    Why this exists (P0-01 / POST_SIGNATURE_PUBLISHER_CLOSURE_R1)
    ------------------------------------------------------------
    Some candidates do not state a rule of their own — they state an *exception*
    to one: 《上海市养犬管理条例》第二十三条 prohibits dogs in 商场 while its
    但书 exempts guide dogs, and `RuleException`'s own docstring records what
    happens if that is modelled as a second standalone rule ("the resolver saw
    two same-layer rules and silently picked the strictest"). So a candidate
    that carves out of another rule must NOT be published as an AccessRule.

    Two invariants are enforced **here**, at the write boundary, rather than
    trusted to the caller's plan:

    1. **Same layer only.** ``rule_exception`` inherits its base rule's layer in
       the resolver, so an OPERATOR_POLICY carve-out attached to a LEGAL
       prohibition would launder an operator's "we allow it" into the statute
       layer and out-vote the law (RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE).
       A cross-layer binding is refused, never coerced.
    2. **Provenance is mandatory.** ``source_id`` is NOT NULL on the table, and
       the ADR-025 scope layer is copied from the candidate verbatim — publishing
       must not re-derive or widen the subject scope.

    The candidate is CAS-ed to PUBLISHED with ``published_rule_id`` pointing at
    the base rule it is now attached to, so the same signed row can never be
    planned twice.
    """
    if candidate.review_status != "APPROVED":
        raise ApiError("只有 APPROVED 的候选可发布", code="candidate_not_approved")

    base = db.get(AccessRule, base_rule_id)
    if base is None:
        raise ApiError("基础规则不存在，例外无法脱离 base 发布", code="exception_base_missing")

    candidate_layer = candidate.rule_layer or "OPERATOR_POLICY"
    if base.rule_layer != candidate_layer:
        raise ApiError(
            f"例外绑定必须层内一致：例外={candidate_layer!r} 基础规则={base.rule_layer!r}"
            "——运营方豁免不得挂到法规层禁令上（RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE）",
            code="cross_layer_exception_binding",
        )
    if base.status not in (RuleStatus.CURRENT.value, "current"):
        raise ApiError(
            f"基础规则状态为 {base.status!r}，不可作为例外的基础",
            code="exception_base_not_current",
        )
    if db.get(Source, candidate.source_id) is None:
        raise ApiError("来源不存在", code="source_missing")

    # Pre-Publish Validation still applies to a carve-out: it is a published
    # normative statement, not a note.
    from app.services.publish_gate import validate_for_publish

    validate_for_publish(db, candidate)

    exception = RuleException(
        rule_id=base.id,
        animal_scope=candidate.animal_scope,
        effect=candidate.effect,
        source_id=candidate.source_id,
        # ADR-025 / ADR-028: the source-faithful scope survives verbatim.
        source_scope_exact=candidate.source_scope_exact or candidate.animal_scope,
        subject_scope_normalized=candidate.subject_scope_normalized,
        normalization_type=candidate.normalization_type,
        normative_effect=candidate.normative_effect,
        holder_scope=candidate.holder_scope,
        status=RuleStatus.CURRENT,
        note=f"published as carve-out of rule {base.id} from candidate {candidate.id}",
    )
    db.add(exception)
    db.flush()

    # Same compare-and-set discipline as publish(): two writers producing one
    # carve-out is the failure this prevents, and a loser rolls the whole
    # transaction back rather than leaving a half-attached exception behind.
    updated = db.execute(
        update(RuleCandidate)
        .where(RuleCandidate.id == candidate.id, RuleCandidate.review_status == "APPROVED")
        .values(
            review_status="PUBLISHED",
            published_rule_id=base.id,
            reviewer_id=reviewer_id,
            review_note=(note or "")[:500] or None,
        )
    )
    if getattr(updated, "rowcount", None) != 1:
        db.rollback()
        raise ApiError("候选已被并发发布", code="candidate_already_published")

    candidate.review_status = "PUBLISHED"
    candidate.published_rule_id = base.id
    candidate.reviewer_id = reviewer_id
    if note:
        candidate.review_note = note[:500]
    return exception
