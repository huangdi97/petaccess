"""Pre-Publish Validation (PILOT-REVIEW-AND-SCHEMA-FIX-01 S8).

Six checks that must ALL pass before a RuleCandidate may be published:

  1. evidence        — candidate cites a traceable anchor: an EvidenceBundle
                       whose artifact exists (quote/hash), OR a media anchor
                       (upload with sha256) for legacy OCR/signage chains
  2. place match     — the bundle carries place_match_evidence (or the
                       candidate is zone-scoped onto its place)
  3. schema support  — scope/action/effect/conditions/zone are valid and the
                       zone belongs to the candidate's place
  4. unresolved conflict — a current rule with the same scope/action and an
                       opposite effect already governs the same owner
  5. freshness       — evidence captured within STALE_DAYS (review hint made
                       hard gate at the publish boundary)
  6. data license    — lead-only / non-storage artifacts never publish

Deliberately NO composite trust score: each check is a named, auditable
gate. Violations raise ApiError with a stable code on the first failed check
in the order above (deterministic for tests and review UX).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import AccessRule, RuleCandidate, Source, Zone
from app.models.enums import (
    AnimalScope,
    EvidenceStrength,
    RuleAction,
    RuleConditionType,
    RuleEffect,
    SourceType,
)
from app.models.evidence import EvidenceBundle, SourceArtifact
from app.services.answerability import STALE_DAYS

CONDITION_TYPES = {e.value for e in RuleConditionType}
SCOPE_VALUES = {e.value for e in AnimalScope}
ACTION_VALUES = {e.value for e in RuleAction}
EFFECT_VALUES = {e.value for e in RuleEffect}

#: source types whose artifacts are leads at best — never publishable as rules
_LEAD_ONLY_SOURCE_TYPES = {SourceType.ORDINARY_USER.value}


def _first_violation(checks: list[tuple[str, bool, str]]) -> None:
    for code, failed, message in checks:
        if failed:
            raise ApiError(message, code=code)


def validate_for_publish(
    db: Session, candidate: RuleCandidate, *, now: datetime | None = None
) -> None:
    """Raise ApiError on the first failed pre-publish check; return when clean."""
    now = now or datetime.now(UTC)

    # ---- 1. evidence: traceable anchor (bundle chain or media) --------------
    bundle: EvidenceBundle | None = None
    artifact: SourceArtifact | None = None
    media = None
    if candidate.evidence_bundle_id:
        bundle = db.get(EvidenceBundle, candidate.evidence_bundle_id)
        if bundle is None:
            raise ApiError("证据包不存在", code="evidence_bundle_missing")
        artifact = db.get(SourceArtifact, bundle.artifact_id)
        if artifact is None:
            raise ApiError("证据原件不存在", code="evidence_missing")
        traceable = bool(bundle.quoted_fragment) or bool(bundle.content_hash) or bool(
            artifact.content_hash
        )
        _first_violation(
            [("evidence_not_traceable", not traceable, "证据缺少原文片段或内容哈希，无法追溯")]
        )
    elif candidate.media_id:
        from app.models.media import MediaObject

        media = db.get(MediaObject, candidate.media_id)
        if media is None or not media.sha256:
            raise ApiError("媒体证据不存在或缺少哈希，无法追溯", code="evidence_missing")
    else:
        raise ApiError("候选未引用证据包，无法追溯（先补证据链）", code="evidence_missing")

    # ---- 2. data license (lead-only artifacts never publish) ----------------
    source = db.get(Source, candidate.source_id)
    source_type = source.source_type if source else None
    weak_strength = {EvidenceStrength.SOCIAL_LEAD.value, EvidenceStrength.SEARCH_SNIPPET.value}
    lead_only = bundle is not None and artifact is not None and (
        artifact.storage_allowed is False
        or (source_type in _LEAD_ONLY_SOURCE_TYPES)
        or (artifact.evidence_strength in weak_strength)
    )
    _first_violation(
        [
            (
                "lead_only_source_not_publishable",
                lead_only,
                "lead-only 来源仅作线索，不得发布正式规则",
            )
        ]
    )

    # ---- 3. place match -------------------------------------------------------
    zone: Zone | None = None
    if candidate.zone_id:
        zone = db.get(Zone, candidate.zone_id)
    zone_ok = zone is not None and zone.place_id == candidate.place_id
    place_ok = candidate.place_id is not None and (zone_ok or candidate.zone_id is None)
    matched = (
        bool(bundle.place_match_evidence) if bundle is not None else False
    ) or place_ok
    _first_violation(
        [("place_match_missing", not matched, "证据缺少 place_match_evidence，无法确认归属")]
    )

    # ---- 4. schema support ------------------------------------------------------
    scope_ok = candidate.animal_scope in SCOPE_VALUES
    action_ok = candidate.action in ACTION_VALUES
    effect_ok = candidate.effect in EFFECT_VALUES
    conditions = candidate.proposed_conditions or []
    conditions_ok = all(
        isinstance(c, dict) and c.get("condition_type") in CONDITION_TYPES for c in conditions
    )
    _first_violation(
        [
            (
                "schema_unsupported",
                not (
                    scope_ok
                    and action_ok
                    and effect_ok
                    and conditions_ok
                    and place_ok
                ),
                "候选字段超出 schema 支持（scope/action/effect/conditions/zone 归属）",
            )
        ]
    )

    # ---- 5. unresolved conflict ---------------------------------------------
    conflict = _has_unresolved_conflict(db, candidate)
    _first_violation(
        [
            (
                "unresolved_conflict",
                conflict,
                "同一归属上已有同 scope/action 且效果相反的现行规则，须先解决冲突",
            )
        ]
    )

    # ---- 6. freshness ----------------------------------------------------------
    captured = (
        artifact.collected_at if artifact is not None else (media.created_at if media else None)
    )
    stale = captured is None or (now - captured).days > STALE_DAYS
    _first_violation(
        [("evidence_stale", stale, f"证据超过 {STALE_DAYS} 天未核验，须先复核来源")]
    )


def _has_unresolved_conflict(db: Session, candidate: RuleCandidate) -> bool:
    """Same owner + same (animal_scope, action) + current + different effect.

    Same-issuer updates (the source itself changed its policy — monitor flow)
    are resolvable by supersession at publish and therefore NOT unresolved;
    opposite effects from a DIFFERENT source need explicit human resolution.
    """
    if candidate.effect not in EFFECT_VALUES:
        return False
    owner = (
        AccessRule.zone_id == candidate.zone_id
        if candidate.zone_id
        else AccessRule.place_id == candidate.place_id
    )
    rows = db.scalars(
        select(AccessRule).where(
            owner,
            AccessRule.status == "current",
            AccessRule.animal_scope == candidate.animal_scope,
            AccessRule.action == candidate.action,
        )
    ).all()
    return any(
        r.effect != candidate.effect and r.source_id != candidate.source_id for r in rows
    )
