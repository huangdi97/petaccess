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
    MandatoryLevel,
    NormalizationType,
    RuleAction,
    RuleConditionType,
    RuleEffect,
    SourceType,
)
from app.models.evidence import EvidenceBundle, SourceArtifact
from app.rulespec.animal_scope import SCOPE_SUBJECTS, normalization_confers_legal_effect
from app.rulespec.v05_resolver import RuleLayer, normalize_mandatory_level
from app.services.answerability import STALE_DAYS

CONDITION_TYPES = {e.value for e in RuleConditionType}
SCOPE_VALUES = {e.value for e in AnimalScope}
ACTION_VALUES = {e.value for e in RuleAction}
EFFECT_VALUES = {e.value for e in RuleEffect}
LAYER_VALUES = {e.value for e in RuleLayer}
#: canonical mandatory levels plus the tolerated legacy spelling (ADR-023)
MANDATORY_LEVEL_VALUES = {e.value for e in MandatoryLevel} | {"discretionary"}
#: subject scopes a rule may legally be normalised onto (ADR-025 / ADR-028)
SUBJECT_SCOPE_VALUES = set(SCOPE_SUBJECTS)
NORMALIZATION_VALUES = {e.value for e in NormalizationType}

#: source types whose artifacts are leads at best — never publishable as rules
_LEAD_ONLY_SOURCE_TYPES = {SourceType.ORDINARY_USER.value}


def _first_violation(checks: list[tuple[str, bool, str]]) -> None:
    for code, failed, message in checks:
        if failed:
            raise ApiError(message, code=code)


def scope_violations(candidate) -> list[tuple[str, bool, str]]:
    """Check 4c as a pure function (ADR-025 / ADR-028).

    Publishing copies the normalisation onto the AccessRule, so whatever the
    candidate declares is what the resolver will see in production. Two ways that
    can go wrong are refused rather than discovered later:

      (a) a precise subject scope with no declared normalisation — the platform
          would have to guess whether it is a legal equivalent;
      (b) the coarse ``service_dog`` scope with no legal normalisation — that is
          precisely the ADR-025 widening, which governs nothing.
    """
    scope_precise_ok = (
        candidate.subject_scope_normalized is None
        or candidate.subject_scope_normalized in SUBJECT_SCOPE_VALUES
    )
    normalization_ok = (
        candidate.normalization_type is None or candidate.normalization_type in NORMALIZATION_VALUES
    )
    pairing_ok = not (
        candidate.subject_scope_normalized is not None and candidate.normalization_type is None
    )
    coarse_scope_unproven = (
        candidate.animal_scope == AnimalScope.SERVICE_DOG.value
        and not normalization_confers_legal_effect(candidate.normalization_type)
    )
    return [
        (
            "scope_normalization_incomplete",
            not (scope_precise_ok and normalization_ok and pairing_ok),
            "候选的 subject_scope_normalized / normalization_type 不完整或超出词表——"
            "精确 scope 必须同时声明归一化类型（平台不猜测其是否有法律效力，ADR-025）",
        ),
        (
            "service_dog_scope_unproven",
            coarse_scope_unproven,
            "animal_scope='service_dog' 未声明具备法律效力的归一化"
            "（exact 或 compound_term_split）——这正是「导盲犬→全部服务犬」的"
            "未经证成的泛化，不得发布（ADR-025 / ADR-028）",
        ),
    ]


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
        traceable = (
            bool(bundle.quoted_fragment) or bool(bundle.content_hash) or bool(artifact.content_hash)
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
    lead_only = (
        bundle is not None
        and artifact is not None
        and (
            artifact.storage_allowed is False
            or (source_type in _LEAD_ONLY_SOURCE_TYPES)
            or (artifact.evidence_strength in weak_strength)
        )
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
    matched = (bool(bundle.place_match_evidence) if bundle is not None else False) or place_ok
    _first_violation(
        [("place_match_missing", not matched, "证据缺少 place_match_evidence，无法确认归属")]
    )

    # ---- 4. schema support ------------------------------------------------------
    scope_ok = candidate.animal_scope in SCOPE_VALUES
    action_ok = candidate.action in ACTION_VALUES
    effect_ok = candidate.effect in EFFECT_VALUES
    # the declared normative layer must be a known layer: an unknown value would
    # fall through to the operator pool in the resolver (silent mis-layering)
    layer_ok = (candidate.rule_layer or "OPERATOR_POLICY") in LAYER_VALUES
    # mandatory_level must be a known value when present (BLK-LAYER-02/ADR-023)
    mandatory_ok = (
        candidate.mandatory_level is None or candidate.mandatory_level in MANDATORY_LEVEL_VALUES
    )
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
                    and layer_ok
                    and mandatory_ok
                    and conditions_ok
                    and place_ok
                ),
                "候选字段超出 schema 支持"
                "（scope/action/effect/rule_layer/mandatory_level/conditions/zone 归属）",
            )
        ]
    )

    # ---- 4b. mandatory legal floor (BLK-LAYER-02 / ADR-023) -------------------
    # A LEGAL rule without an explicit mandatory_level cannot be the resolver's
    # floor: the resolver never reads NULL as mandatory (unknown ≠ binding), so
    # publishing it would let a venue's "allowed" rule outvote a statute. The
    # level must be declared, not guessed — so we refuse rather than default it.
    legal_without_level = (
        candidate.rule_layer or "OPERATOR_POLICY"
    ) == RuleLayer.LEGAL.value and normalize_mandatory_level(candidate.mandatory_level) is None
    _first_violation(
        [
            (
                "legal_requires_mandatory_level",
                legal_without_level,
                "LEGAL 规则必须声明 mandatory_level"
                "（mandatory/advisory/operator_discretion），不得留空——"
                "否则法定约束无法成为 resolver 地板（ADR-023）",
            )
        ]
    )

    # ---- 4c. source-faithful scope completeness (ADR-025 / ADR-028) -----------
    # Publishing copies the normalisation onto the AccessRule, so whatever the
    # candidate declares is what the resolver will see in production. The checks
    # live in one place (`scope_violations`) so tests and the gate cannot drift.
    _first_violation(scope_violations(candidate))

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
    _first_violation([("evidence_stale", stale, f"证据超过 {STALE_DAYS} 天未核验，须先复核来源")])


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
    return any(r.effect != candidate.effect and r.source_id != candidate.source_id for r in rows)
