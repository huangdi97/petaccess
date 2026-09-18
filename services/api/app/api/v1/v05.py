"""v0.5 API: candidates, monitors, jobs, org/templates, events, amenities,
entrances, access paths, boundary, answerability, data licenses (NEXT_GOAL §B).

Old endpoints unchanged (additive). Admin review actions are audited.
"""

from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import record_audit
from app.core.audit_events import AuditEvent
from app.core.errors import ApiError, NotFound
from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models import (
    AccessRule,
    JurisdictionException,
    Place,
    RuleException,
    Source,
    User,
    Zone,
)
from app.models.enums import (
    AnimalScope,
    HolderScope,
    NormalizationType,
    NormativeEffect,
    RuleStatus,
    UserRole,
)
from app.models.v05 import (
    AccessPath,
    Amenity,
    CoexistencePolicy,
    DataLicense,
    Entrance,
    EventPolicy,
    Organization,
    PlacePolicyBinding,
    PolicyTemplate,
    PolicyTemplateRule,
    RuleCandidate,
    SourceMonitor,
)
from app.rulespec.animal_scope import (
    SCOPE_SUBJECTS,
    normalization_confers_legal_effect,
)
from app.rulespec.holder_scope import HolderContext
from app.rulespec.v05_boundary import match as boundary_match
from app.rulespec.v05_resolver import (
    LayeredException,
    LayeredRule,
    RuleLayer,
    resolve,
)
from app.schemas.common import Page
from app.services.answerability import compute_answerability
from app.services.candidate_service import (
    create_from_extraction,
    publish,
    publish_exception,
    transition,
)
from app.services.publish_gate import LAYER_VALUES, MANDATORY_LEVEL_VALUES

router = APIRouter(tags=["v05"])
admin = APIRouter(prefix="/admin", tags=["admin:v05"])


# ------------------------------------------------------------------- candidates


class CandidateIn(BaseModel):
    source_id: str
    place_id: str | None = None
    zone_id: str | None = None
    animal_scope: str | None = None
    action: str | None = None
    effect: str | None = None
    rule_layer: str | None = None
    mandatory_level: str | None = None
    proposed_conditions: list | None = None
    extraction_method: str
    extraction_provider: str | None = None
    internal_confidence: float | None = Field(default=None, ge=0, le=1)
    raw_text: str | None = None
    media_id: str | None = None
    evidence_bundle_id: str | None = None
    # --- ADR-025 / ADR-028: source-faithful scope ---------------------------
    source_scope_exact: str | None = Field(default=None, max_length=64)
    subject_scope_normalized: str | None = Field(default=None, max_length=32)
    normalization_type: str | None = Field(default=None, max_length=32)
    normative_effect: str | None = Field(default=None, max_length=32)
    holder_scope: str | None = Field(default=None, max_length=32)
    operator_obligations: list | None = None
    # --- Wave 01 -------------------------------------------------------------
    #: which expansion run produced this candidate
    expansion_run_id: str | None = Field(default=None, max_length=64)
    #: deterministic ingestion guard; a repeat of the same statement must not
    #: become a second candidate (it is not an identity claim about the rule)
    dedup_key: str | None = Field(default=None, max_length=128)


#: subject scopes a rule may legally be normalised onto
SUBJECT_SCOPE_VALUES = set(SCOPE_SUBJECTS)
NORMALIZATION_VALUES = {e.value for e in NormalizationType}
NORMATIVE_EFFECT_VALUES = {e.value for e in NormativeEffect}
HOLDER_SCOPE_VALUES = {e.value for e in HolderScope}
ANIMAL_SCOPE_VALUES = {e.value for e in AnimalScope}


def _validate_scope_fields(
    *,
    animal_scope: str | None,
    subject_scope_normalized: str | None,
    normalization_type: str | None,
    normative_effect: str | None,
    holder_scope: str | None,
) -> None:
    """Never guess whether a stored scope is a legal equivalent (ADR-025).

    Two things are refused:
      * a precise subject scope with no declared normalisation (ambiguous);
      * the coarse ``service_dog`` scope with no *legal* normalisation — that is
        exactly the 「导盲犬 → 全部服务犬」 widening and governs nothing.
    """
    if subject_scope_normalized is not None:
        if subject_scope_normalized not in SUBJECT_SCOPE_VALUES:
            raise ApiError(
                f"非法 subject_scope_normalized {subject_scope_normalized}"
                f"（允许：{sorted(SUBJECT_SCOPE_VALUES)}）",
                code="invalid_subject_scope",
            )
        if normalization_type is None:
            raise ApiError(
                "subject_scope_normalized 需要同时提供 normalization_type"
                "（exact / compound_term_split / parent_group_for_query_only / "
                "legal_interpretation_required）；平台不猜测该 scope 是否具有法律效力。",
                code="scope_normalization_ambiguous",
                status_code=422,
            )
    if normalization_type is not None and normalization_type not in NORMALIZATION_VALUES:
        raise ApiError(
            f"非法 normalization_type {normalization_type}（允许：{sorted(NORMALIZATION_VALUES)}）",
            code="invalid_normalization_type",
        )
    if normative_effect is not None and normative_effect not in NORMATIVE_EFFECT_VALUES:
        raise ApiError(
            f"非法 normative_effect {normative_effect}",
            code="invalid_normative_effect",
        )
    if holder_scope is not None and holder_scope not in HOLDER_SCOPE_VALUES:
        raise ApiError(f"非法 holder_scope {holder_scope}", code="invalid_holder_scope")
    if animal_scope == AnimalScope.SERVICE_DOG.value and not normalization_confers_legal_effect(
        normalization_type
    ):
        raise ApiError(
            "animal_scope='service_dog' 必须声明具备法律效力的 normalization_type"
            "（exact 或 compound_term_split）——否则它就是「导盲犬→全部服务犬」的"
            "未经证成的泛化，不得入库。",
            code="service_dog_scope_unproven",
        )


class CandidateScopeIn(BaseModel):
    """Reviewer-controlled re-modelling of a candidate's animal scope.

    Used to split a compound source term (e.g. 军警犬) into one row per member
    without touching the candidate's evidence — the split rows share the exact
    same EvidenceBundle, so provenance stays intact (ADR-028).
    """

    source_scope_exact: str | None = Field(default=None, max_length=64)
    subject_scope_normalized: str | None = Field(default=None, max_length=32)
    normalization_type: str | None = Field(default=None, max_length=32)
    normative_effect: str | None = Field(default=None, max_length=32)
    holder_scope: str | None = Field(default=None, max_length=32)
    operator_obligations: list | None = None
    reason: str | None = None


class CandidateReview(BaseModel):
    target: str  # next state
    note: str | None = None


class CandidateLayerIn(BaseModel):
    rule_layer: str  # LEGAL | REGULATORY_GUIDANCE | OPERATOR_POLICY | TEMPORARY_POLICY
    reason: str | None = None


class CandidateMandatoryIn(BaseModel):
    # mandatory | advisory | operator_discretion (ADR-023)
    mandatory_level: str
    reason: str | None = None


@router.get("/places/{place_id}/candidates", response_model=Page[dict])
def list_place_candidates(
    place_id: str,
    review_status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    stmt = select(RuleCandidate).where(RuleCandidate.place_id == place_id)
    if review_status:
        stmt = stmt.where(RuleCandidate.review_status == review_status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(RuleCandidate.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return Page(items=[_candidate_dict(c) for c in rows], total=total, limit=limit, offset=offset)


def _candidate_dict(c) -> dict:
    return {
        "id": c.id,
        "source_id": c.source_id,
        "place_id": c.place_id,
        "zone_id": c.zone_id,
        "animal_scope": c.animal_scope,
        "action": c.action,
        "effect": c.effect,
        "rule_layer": c.rule_layer,
        "mandatory_level": c.mandatory_level,
        "proposed_conditions": c.proposed_conditions,
        "extraction_method": c.extraction_method,
        "extraction_provider": c.extraction_provider,
        "internal_confidence": c.internal_confidence,
        "raw_text": c.raw_text,
        "review_status": c.review_status,
        "reviewer_id": c.reviewer_id,
        "review_note": c.review_note,
        "published_rule_id": c.published_rule_id,
        "media_id": c.media_id,
        "evidence_bundle_id": c.evidence_bundle_id,
        # --- ADR-025 / ADR-028 scope layer ---
        "source_scope_exact": c.source_scope_exact,
        "subject_scope_normalized": c.subject_scope_normalized,
        "normalization_type": c.normalization_type,
        "normative_effect": c.normative_effect,
        "holder_scope": c.holder_scope,
        "operator_obligations": c.operator_obligations,
        "created_at": c.created_at,
    }


@admin.get("/candidates", response_model=Page[dict])
def admin_list_candidates(
    review_status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):

    stmt = select(RuleCandidate)
    if review_status:
        stmt = stmt.where(RuleCandidate.review_status == review_status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(RuleCandidate.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return Page(items=[_candidate_dict(c) for c in rows], total=total, limit=limit, offset=offset)


@admin.post("/candidates", status_code=201)
def admin_create_candidate(
    body: CandidateIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    if db.get(Source, body.source_id) is None:
        raise NotFound("来源不存在")
    if body.mandatory_level is not None and body.mandatory_level not in MANDATORY_LEVEL_VALUES:
        allowed = sorted(MANDATORY_LEVEL_VALUES)
        raise ApiError(
            f"非法 mandatory_level {body.mandatory_level}（允许：{allowed}）",
            code="invalid_mandatory_level",
        )
    if body.evidence_bundle_id:
        from app.models.evidence import EvidenceBundle

        if db.get(EvidenceBundle, body.evidence_bundle_id) is None:
            raise NotFound("证据包不存在")
    # ADR-025 / ADR-028: refuse an ambiguous or unproven animal scope at ingest
    # time, so a widening can never reach the review queue in the first place.
    _validate_scope_fields(
        animal_scope=body.animal_scope,
        subject_scope_normalized=body.subject_scope_normalized,
        normalization_type=body.normalization_type,
        normative_effect=body.normative_effect,
        holder_scope=body.holder_scope,
    )
    cand = create_from_extraction(
        db,
        source_id=body.source_id,
        place_id=body.place_id,
        zone_id=body.zone_id,
        animal_scope=body.animal_scope,
        action=body.action,
        effect=body.effect,
        rule_layer=body.rule_layer,
        mandatory_level=body.mandatory_level,
        proposed_conditions=body.proposed_conditions,
        extraction_method=body.extraction_method,
        extraction_provider=body.extraction_provider,
        internal_confidence=body.internal_confidence,
        raw_text=body.raw_text,
        media_id=body.media_id,
        evidence_bundle_id=body.evidence_bundle_id,
        source_scope_exact=body.source_scope_exact,
        subject_scope_normalized=body.subject_scope_normalized,
        normalization_type=body.normalization_type,
        normative_effect=body.normative_effect,
        holder_scope=body.holder_scope,
        operator_obligations=body.operator_obligations,
        expansion_run_id=body.expansion_run_id,
        dedup_key=body.dedup_key,
    )
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.CANDIDATE_CREATE.value,
        target_type="rule_candidate",
        target_id=cand.id,
        after_state={
            "status": cand.review_status,
            "method": body.extraction_method,
            "rule_layer": cand.rule_layer,
            "mandatory_level": cand.mandatory_level,
            "source_scope_exact": cand.source_scope_exact,
            "subject_scope_normalized": cand.subject_scope_normalized,
            "normalization_type": cand.normalization_type,
        },
    )
    db.commit()
    return _candidate_dict(cand)


@admin.post("/candidates/{candidate_id}/scope")
def admin_set_candidate_scope(
    candidate_id: str,
    body: CandidateScopeIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Re-model a candidate's source-faithful animal scope before review (ADR-028).

    This is how a *compound* source term is split: 「军警犬」 names exactly
    police + military working dogs, and the platform refuses to collapse that
    into one vague subject. Each member gets its own candidate, all sharing the
    original EvidenceBundle — provenance is never duplicated or weakened.

    Published candidates are frozen: changing the scope of an in-force rule would
    silently rewrite the answer, so that path requires a new candidate +
    supersession.
    """
    cand = db.get(RuleCandidate, candidate_id)
    if cand is None:
        raise NotFound("候选不存在")
    if cand.review_status in ("PUBLISHED", "SUPERSEDED"):
        raise ApiError(
            "已发布候选的 scope 不可原地修改（须走 supersession）", code="candidate_frozen"
        )

    _validate_scope_fields(
        animal_scope=cand.animal_scope,
        subject_scope_normalized=body.subject_scope_normalized,
        normalization_type=body.normalization_type,
        normative_effect=body.normative_effect,
        holder_scope=body.holder_scope,
    )

    before = {
        "source_scope_exact": cand.source_scope_exact,
        "subject_scope_normalized": cand.subject_scope_normalized,
        "normalization_type": cand.normalization_type,
        "normative_effect": cand.normative_effect,
        "holder_scope": cand.holder_scope,
        "operator_obligations": cand.operator_obligations,
    }
    cand.source_scope_exact = body.source_scope_exact
    cand.subject_scope_normalized = body.subject_scope_normalized
    cand.normalization_type = body.normalization_type
    cand.normative_effect = body.normative_effect
    cand.holder_scope = body.holder_scope
    if body.operator_obligations is not None:
        cand.operator_obligations = body.operator_obligations
    after = {
        "source_scope_exact": cand.source_scope_exact,
        "subject_scope_normalized": cand.subject_scope_normalized,
        "normalization_type": cand.normalization_type,
        "normative_effect": cand.normative_effect,
        "holder_scope": cand.holder_scope,
        "operator_obligations": cand.operator_obligations,
    }
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.CANDIDATE_SET_SCOPE.value,
        target_type="rule_candidate",
        target_id=cand.id,
        before_state=before,
        after_state={**after, "reason": body.reason},
    )
    db.commit()
    return {"id": cand.id, **after}


@admin.post("/candidates/{candidate_id}/transition")
def admin_transition_candidate(
    candidate_id: str,
    body: CandidateReview,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):

    cand = db.get(RuleCandidate, candidate_id)
    if cand is None:
        raise NotFound("候选不存在")
    before = cand.review_status
    transition(cand, body.target, reviewer_id=user.id, note=body.note)
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.CANDIDATE_TRANSITION.value,
        target_type="rule_candidate",
        target_id=cand.id,
        before_state={"status": before},
        after_state={"status": cand.review_status, "note": body.note},
    )
    db.commit()
    return _candidate_dict(cand)


@admin.post("/candidates/{candidate_id}/rule-layer")
def admin_set_candidate_layer(
    candidate_id: str,
    body: CandidateLayerIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Correct a candidate's normative layer before review/publish (BLK-LAYER-01).

    The layer decides which resolver pool the published rule lands in, so it is
    reviewer-controlled data, not a client hint. Published candidates are frozen:
    changing the layer of a rule already in force would silently rewrite the
    answer, so that path requires a new candidate + supersession instead.
    """
    cand = db.get(RuleCandidate, candidate_id)
    if cand is None:
        raise NotFound("候选不存在")
    if cand.review_status in ("PUBLISHED", "SUPERSEDED"):
        raise ApiError("已发布候选的分层不可原地修改（须走 supersession）", code="candidate_frozen")
    if body.rule_layer not in LAYER_VALUES:
        raise ApiError(
            f"非法 rule_layer {body.rule_layer}（允许：{sorted(LAYER_VALUES)}）",
            code="invalid_rule_layer",
        )
    before = cand.rule_layer
    if before == body.rule_layer:
        return {"id": cand.id, "rule_layer": cand.rule_layer, "changed": False}
    cand.rule_layer = body.rule_layer
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.CANDIDATE_SET_RULE_LAYER.value,
        target_type="rule_candidate",
        target_id=cand.id,
        before_state={"rule_layer": before},
        after_state={"rule_layer": cand.rule_layer, "reason": body.reason},
    )
    db.commit()
    return {"id": cand.id, "rule_layer": cand.rule_layer, "changed": True}


@admin.post("/candidates/{candidate_id}/mandatory-level")
def admin_set_candidate_mandatory_level(
    candidate_id: str,
    body: CandidateMandatoryIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Set a candidate's normative force before review/publish (BLK-LAYER-02).

    mandatory_level decides whether a published LEGAL rule becomes the
    resolver's floor. It is reviewer-controlled data: the publish gate refuses
    a LEGAL candidate that leaves it blank, so it can never be defaulted by the
    client. Published candidates are frozen — a change in force of an in-force
    rule must go through a new candidate + supersession.
    """
    cand = db.get(RuleCandidate, candidate_id)
    if cand is None:
        raise NotFound("候选不存在")
    if cand.review_status in ("PUBLISHED", "SUPERSEDED"):
        raise ApiError(
            "已发布候选的强制级别不可原地修改（须走 supersession）", code="candidate_frozen"
        )
    if body.mandatory_level not in MANDATORY_LEVEL_VALUES:
        raise ApiError(
            f"非法 mandatory_level {body.mandatory_level}"
            f"（允许：{sorted(MANDATORY_LEVEL_VALUES)}）",
            code="invalid_mandatory_level",
        )
    before = cand.mandatory_level
    if before == body.mandatory_level:
        return {"id": cand.id, "mandatory_level": cand.mandatory_level, "changed": False}
    cand.mandatory_level = body.mandatory_level
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.CANDIDATE_SET_MANDATORY_LEVEL.value,
        target_type="rule_candidate",
        target_id=cand.id,
        before_state={"mandatory_level": before},
        after_state={"mandatory_level": cand.mandatory_level, "reason": body.reason},
    )
    db.commit()
    return {"id": cand.id, "mandatory_level": cand.mandatory_level, "changed": True}


class PublishIn(BaseModel):
    """Optional publish mode.

    Absent (or empty) means "publish this candidate as an AccessRule", which is
    the historical behaviour. ``exception_of_rule_id`` means "this candidate is a
    carve-out of that base rule", and the publish becomes a ``RuleException``
    instead — see ``candidate_service.publish_exception``. The caller states the
    base explicitly because a candidate row carries no base-rule pointer of its
    own; the API will not guess one, and it refuses a cross-layer binding.
    """

    exception_of_rule_id: str | None = Field(default=None, max_length=36)


@admin.post("/candidates/{candidate_id}/publish")
def admin_publish_candidate(
    candidate_id: str,
    body: PublishIn | None = None,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):

    cand = db.get(RuleCandidate, candidate_id)
    if cand is None:
        raise NotFound("候选不存在")
    if body is not None and body.exception_of_rule_id:
        exc = publish_exception(
            db, cand, base_rule_id=body.exception_of_rule_id, reviewer_id=user.id
        )
        record_audit(
            db,
            request=None,
            actor_user_id=user.id,
            actor_role=str(user.role),
            action=AuditEvent.CANDIDATE_PUBLISH_EXCEPTION.value,
            target_type="rule_exception",
            target_id=exc.id,
            after_state={
                "candidate_id": cand.id,
                "base_rule_id": exc.rule_id,
                "effect": exc.effect,
                "animal_scope": exc.animal_scope,
                "source_scope_exact": exc.source_scope_exact,
                "subject_scope_normalized": exc.subject_scope_normalized,
                "normalization_type": exc.normalization_type,
                "normative_effect": exc.normative_effect,
                "holder_scope": exc.holder_scope,
            },
        )
        db.commit()
        return {
            "published_rule_id": exc.rule_id,
            "rule_exception_id": exc.id,
            "candidate_id": cand.id,
            "candidate_status": cand.review_status,
            "publication_type": "rule_exception",
        }
    rule = publish(db, cand, reviewer_id=user.id)
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.CANDIDATE_PUBLISH.value,
        target_type="access_rule",
        target_id=rule.id,
        after_state={
            "candidate_id": cand.id,
            "effect": rule.effect,
            "rule_layer": rule.rule_layer,
            "mandatory_level": rule.mandatory_level,
        },
    )
    db.commit()
    return {
        "published_rule_id": rule.id,
        "candidate_id": cand.id,
        "candidate_status": cand.review_status,
        "rule_layer": rule.rule_layer,
        "mandatory_level": rule.mandatory_level,
    }


# ------------------------------------------------------------------ source monitors


class MonitorIn(BaseModel):
    source_id: str
    url: str = Field(min_length=10, max_length=500)
    schedule_minutes: int = Field(default=1440, ge=5)
    place_id: str | None = None
    #: Wave 01: which expansion run initialized this monitor
    expansion_run_id: str | None = Field(default=None, max_length=64)


class RuleExceptionIn(BaseModel):
    rule_id: str
    animal_scope: str = Field(pattern="^(dog|cat|ordinary_pet|service_dog|other)$")
    effect: str = Field(pattern="^(allowed|prohibited|conditional)$")
    source_id: str
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    note: str | None = Field(default=None, max_length=500)
    # --- ADR-025: source-faithful carve-out ---------------------------------
    #: the precise role/scope the source itself names (e.g. 'guide_dog').
    source_scope_exact: str | None = Field(default=None, max_length=64)
    #: the precise subject the exception governs (the legal matching unit).
    subject_scope_normalized: str | None = Field(
        default=None,
        pattern=(
            "^(dog|ordinary_pet|service_dog|cat|other|ordinary_dog|guide_dog|"
            "hearing_dog|assistance_dog|other_service_dog|police_dog|"
            "military_working_dog)$"
        ),
    )
    #: exact | parent_group_for_query_only | legal_interpretation_required.
    #: Omit it and the carve-out is stored as NOT a legal equivalent — a
    #: `service_dog` carve-out never applies until a reviewer declares `exact`.
    normalization_type: str | None = Field(
        default=None,
        pattern=(
            "^(exact|parent_group_for_query_only|legal_interpretation_required"
            "|compound_term_split)$"
        ),
    )
    #: exempt_from_prohibition | permission | prohibition |
    #: conditional_permission | facilitation_required
    normative_effect: str | None = Field(
        default=None,
        pattern=(
            "^(permission|prohibition|conditional_permission|"
            "exempt_from_prohibition|facilitation_required)$"
        ),
    )
    holder_scope: str | None = Field(default=None, pattern="^(any_handler|person_with_disability)$")


class RuleExceptionTransition(BaseModel):
    target: str = Field(pattern="^(superseded|withdrawn|current|disputed|archived)$")
    note: str | None = Field(default=None, max_length=500)


def _serialize_rule_exception(e: RuleException) -> dict:
    return {
        "id": e.id,
        "rule_id": e.rule_id,
        "animal_scope": e.animal_scope,
        "effect": e.effect,
        "source_id": e.source_id,
        "status": e.status,
        "effective_from": e.effective_from.isoformat() if e.effective_from else None,
        "effective_to": e.effective_to.isoformat() if e.effective_to else None,
        "note": e.note,
        # --- ADR-025 scope layer (additive) ---
        "source_scope_exact": e.source_scope_exact,
        "subject_scope_normalized": e.subject_scope_normalized,
        "normalization_type": e.normalization_type,
        "normative_effect": e.normative_effect,
        "holder_scope": e.holder_scope,
    }


@admin.post("/rule-exceptions", status_code=201)
def admin_create_rule_exception(
    body: RuleExceptionIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Attach a scope carve-out to a base rule (SG-REAL-01).

    Generic mechanism — no hardcoded scope branch. An exception without a
    source is invalid (column is NOT NULL); the base rule must exist.
    """
    from app.models import RuleException as RuleExceptionModel

    rule = db.get(AccessRule, body.rule_id)
    if rule is None:
        raise NotFound("规则不存在")
    if db.get(Source, body.source_id) is None:
        raise NotFound("来源不存在")

    # ADR-025: a precise subject scope without a declared normalisation is
    # ambiguous — never guess whether it is a legal equivalent. Reject it so the
    # reviewer states their intent explicitly.
    if body.subject_scope_normalized is not None and body.normalization_type is None:
        raise ApiError(
            "subject_scope_normalized 需要同时提供 normalization_type"
            "（exact / parent_group_for_query_only / legal_interpretation_required）；"
            "平台不猜测该 scope 是否具有法律效力。",
            code="scope_normalization_ambiguous",
            status_code=422,
        )

    normative_effect = body.normative_effect
    if normative_effect is None and body.normalization_type == "exact":
        # Mirror the migration backfill: only derive a normative effect where the
        # normalisation is exact, otherwise it would encode the inference under
        # review (ADR-025).
        normative_effect = {
            "allowed": "permission",
            "prohibited": "prohibition",
            "conditional": "conditional_permission",
        }.get(body.effect)

    exc = RuleExceptionModel(
        rule_id=body.rule_id,
        animal_scope=body.animal_scope,
        effect=body.effect,
        source_id=body.source_id,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
        note=body.note,
        source_scope_exact=body.source_scope_exact or body.animal_scope,
        subject_scope_normalized=body.subject_scope_normalized,
        normalization_type=body.normalization_type,
        normative_effect=normative_effect,
        holder_scope=body.holder_scope,
    )
    db.add(exc)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.RULE_EXCEPTION_CREATE.value,
        target_type="rule_exception",
        target_id=exc.id,
        after_state={
            "rule_id": exc.rule_id,
            "animal_scope": exc.animal_scope,
            "effect": exc.effect,
            "source_id": exc.source_id,
            "source_scope_exact": exc.source_scope_exact,
            "subject_scope_normalized": exc.subject_scope_normalized,
            "normalization_type": exc.normalization_type,
            "normative_effect": exc.normative_effect,
            "holder_scope": exc.holder_scope,
        },
    )
    db.commit()
    return _serialize_rule_exception(exc)


@admin.get("/rule-exceptions", response_model=Page[dict])
def admin_list_rule_exceptions(
    rule_id: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    from app.models import RuleException as RuleExceptionModel

    stmt = select(RuleExceptionModel).order_by(RuleExceptionModel.created_at.desc())
    if rule_id:
        stmt = stmt.where(RuleExceptionModel.rule_id == rule_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(
        items=[_serialize_rule_exception(e) for e in rows], total=total, limit=limit, offset=offset
    )


@admin.post("/rule-exceptions/{exception_id}/transition")
def admin_transition_rule_exception(
    exception_id: str,
    body: RuleExceptionTransition,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Lifecycle: only `current` exceptions apply (expired/superseded fall back
    to the base rule). Transitions are audited."""
    from app.models import RuleException as RuleExceptionModel

    exc = db.get(RuleExceptionModel, exception_id)
    if exc is None:
        raise NotFound("规则例外不存在")
    before = exc.status
    exc.status = RuleStatus(body.target)
    if body.note:
        exc.note = body.note[:500]
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.RULE_EXCEPTION_TRANSITION.value,
        target_type="rule_exception",
        target_id=exc.id,
        before_state={"status": before},
        after_state={"status": exc.status, "note": body.note},
    )
    db.commit()
    return _serialize_rule_exception(exc)


class FreshnessPolicyIn(BaseModel):
    """A named re-verification interval (brief §34).

    review_due means "check this again", NOT "this is invalid". Nothing in the
    resolver may read an overdue policy as permission to drop evidence or flip
    a conclusion to allowed/prohibited.
    """

    name: str = Field(min_length=1, max_length=80)
    venue_scope: str | None = Field(default=None, max_length=40)
    rule_layer: str | None = Field(default=None, max_length=30)
    review_interval_days: int = Field(default=90, ge=1, le=3650)


class DataSourceJobIn(BaseModel):
    """A bounded, auditable production run (brief §39).

    Every Wave 01 collection runs inside one of these so the system — not just
    the operator's memory — knows where a batch of rows came from.
    """

    job_type: str = Field(min_length=1, max_length=30)
    target_scope: dict | None = None
    provider: str | None = Field(default=None, max_length=60)
    source_id: str | None = None
    expansion_run_id: str | None = Field(default=None, max_length=64)


class SourceFreshnessIn(BaseModel):
    """Assign a freshness policy to a source and set its review window."""

    freshness_policy_id: str
    last_verified_at: datetime | None = None
    review_due_at: datetime | None = None


@admin.post("/freshness-policies", status_code=201)
def admin_create_freshness_policy(
    body: FreshnessPolicyIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    from app.models.v05 import FreshnessPolicy

    policy = FreshnessPolicy(
        name=body.name,
        venue_scope=body.venue_scope,
        rule_layer=body.rule_layer,
        review_interval_days=body.review_interval_days,
    )
    db.add(policy)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.FRESHNESS_POLICY_CREATE.value,
        target_type="freshness_policy",
        target_id=policy.id,
        after_state={"name": body.name, "review_interval_days": body.review_interval_days},
    )
    db.commit()
    return {
        "id": policy.id,
        "name": policy.name,
        "review_interval_days": policy.review_interval_days,
    }


@admin.get("/freshness-policies", response_model=Page[dict])
def admin_list_freshness_policies(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    from app.models.v05 import FreshnessPolicy

    stmt = select(FreshnessPolicy).order_by(FreshnessPolicy.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(
        items=[
            {
                "id": p.id,
                "name": p.name,
                "venue_scope": p.venue_scope,
                "rule_layer": p.rule_layer,
                "review_interval_days": p.review_interval_days,
            }
            for p in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin.post("/sources/{source_id}/freshness")
def admin_assign_source_freshness(
    source_id: str,
    body: SourceFreshnessIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    from app.models.v05 import FreshnessPolicy

    src = db.get(Source, source_id)
    if src is None:
        raise NotFound("来源不存在")
    if db.get(FreshnessPolicy, body.freshness_policy_id) is None:
        raise NotFound("新鲜度策略不存在")
    src.freshness_policy_id = body.freshness_policy_id
    if body.last_verified_at is not None:
        src.last_verified_at = body.last_verified_at
    if body.review_due_at is not None:
        src.review_due_at = body.review_due_at
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.SOURCE_FRESHNESS_ASSIGN.value,
        target_type="source",
        target_id=src.id,
        after_state={
            "freshness_policy_id": body.freshness_policy_id,
            "review_due_at": str(body.review_due_at),
        },
    )
    db.commit()
    return {
        "source_id": src.id,
        "freshness_policy_id": src.freshness_policy_id,
        "last_verified_at": src.last_verified_at,
        "review_due_at": src.review_due_at,
    }


@admin.post("/data-source-jobs", status_code=201)
def admin_create_data_source_job(
    body: DataSourceJobIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Open a bounded production run. The caller closes it via the PATCH below."""
    from app.models.v05 import DataSourceJob

    job = DataSourceJob(
        job_type=body.job_type,
        state="RUNNING",
        target_scope=body.target_scope,
        actor_user_id=user.id,
        provider=body.provider,
        source_id=body.source_id,
        started_at=datetime.now(UTC),
        expansion_run_id=body.expansion_run_id,
    )
    db.add(job)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.DATA_SOURCE_JOB_CREATE.value,
        target_type="data_source_job",
        target_id=job.id,
        after_state={"job_type": body.job_type, "expansion_run_id": body.expansion_run_id},
    )
    db.commit()
    return {"id": job.id, "job_type": job.job_type, "state": job.state}


class DataSourceJobFinishIn(BaseModel):
    state: str = Field(pattern="^(COMPLETED|FAILED|PARTIAL)$")
    result_counts: dict | None = None
    errors: list | None = None


@admin.post("/data-source-jobs/{job_id}/finish")
def admin_finish_data_source_job(
    job_id: str,
    body: DataSourceJobFinishIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    from app.models.v05 import DataSourceJob

    job = db.get(DataSourceJob, job_id)
    if job is None:
        raise NotFound("采集任务不存在")
    job.state = body.state
    job.completed_at = datetime.now(UTC)
    job.result_counts = body.result_counts
    job.errors = body.errors
    db.commit()
    return {"id": job.id, "state": job.state, "completed_at": job.completed_at}


@admin.get("/data-source-jobs", response_model=Page[dict])
def admin_list_data_source_jobs(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    from app.models.v05 import DataSourceJob

    stmt = select(DataSourceJob).order_by(DataSourceJob.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(
        items=[
            {
                "id": j.id,
                "job_type": j.job_type,
                "state": j.state,
                "expansion_run_id": j.expansion_run_id,
                "started_at": j.started_at,
                "completed_at": j.completed_at,
                "result_counts": j.result_counts,
            }
            for j in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin.post("/monitors", status_code=201)
def admin_create_monitor(
    body: MonitorIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    if db.get(Source, body.source_id) is None:
        raise NotFound("来源不存在")
    monitor = SourceMonitor(
        source_id=body.source_id,
        url=body.url,
        schedule_minutes=body.schedule_minutes,
        place_id=body.place_id,
        expansion_run_id=body.expansion_run_id,
        # A monitor with no next_check_at is never due, so the fleet would sit
        # idle until someone swept it by hand. Scheduling starts at creation.
        next_check_at=db.execute(select(func.now())).scalar_one(),
    )
    db.add(monitor)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.MONITOR_CREATE.value,
        target_type="source_monitor",
        target_id=monitor.id,
        after_state={"url": body.url[:120]},
    )
    db.commit()
    return {"id": monitor.id, "url": monitor.url, "status": monitor.status}


@admin.get("/monitors", response_model=Page[dict])
def admin_list_monitors(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    stmt = select(SourceMonitor).order_by(SourceMonitor.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [
        {
            "id": m.id,
            "source_id": m.source_id,
            "url": m.url[:120],
            "status": m.status,
            "failure_count": m.failure_count,
            "content_hash": (m.content_hash or "")[:12],
            "last_checked_at": m.last_checked_at,
            "last_changed_at": m.last_changed_at,
            "place_id": m.place_id,
        }
        for m in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@admin.post("/monitors/{monitor_id}/check")
def admin_check_monitor(
    monitor_id: str,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """One monitor sweep: unchanged | changed | failed.

    On change the captured page becomes traceable evidence
    (SourceArtifact → EvidenceBundle) and then a RuleCandidate. A rule is never
    written directly — it still has to pass review.
    """
    from app.services.monitor_sweep import apply_monitor_change

    monitor = db.get(SourceMonitor, monitor_id)
    if monitor is None:
        raise NotFound("监控不存在")
    res = apply_monitor_change(db, monitor)
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.MONITOR_CHECK.value,
        target_type="source_monitor",
        target_id=monitor.id,
        after_state={
            "outcome": res["outcome"],
            "candidate_id": res["candidate_id"],
            "evidence_bundle_id": res["evidence_bundle_id"],
            "duplicate_change": res["duplicate_change"],
        },
    )
    db.commit()
    return {
        "outcome": res["outcome"],
        "candidate_id": res["candidate_id"],
        "artifact_id": res["artifact_id"],
        "evidence_bundle_id": res["evidence_bundle_id"],
        "content_hash": (monitor.content_hash or "")[:12],
        "failure_count": monitor.failure_count,
        "last_http_status": monitor.last_http_status,
        "duplicate_change": res["duplicate_change"],
    }


@admin.post("/monitors/sweep")
def admin_sweep_due_monitors(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Sweep every monitor that is due (§28-§33).

    Without this, ``SourceMonitor`` rows only move when an operator names one
    explicitly — which is fine for a handful and useless for a fleet.
    """
    from app.services.monitor_sweep import sweep_due_monitors

    summary = sweep_due_monitors(db, limit=limit)
    # One audit row per monitor, not one for the sweep: a sweep-level row would
    # have no target_id, and an audit event with an empty target is useless when
    # someone later asks "who changed this source's state and when".
    for res in summary["results"]:
        record_audit(
            db,
            request=None,
            actor_user_id=user.id,
            actor_role=str(user.role),
            action=AuditEvent.MONITOR_CHECK.value,
            target_type="source_monitor",
            target_id=str(res["monitor_id"]),
            after_state={
                "outcome": res["outcome"],
                "candidate_id": res["candidate_id"],
                "evidence_bundle_id": res["evidence_bundle_id"],
                "duplicate_change": res["duplicate_change"],
                "sweep": True,
            },
        )
    db.commit()
    return summary


@admin.get("/monitors/due", response_model=Page[dict])
def admin_list_due_monitors(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """What the next sweep would touch, without causing any outbound traffic."""
    from app.services.monitor_sweep import select_due_monitors

    rows = select_due_monitors(db, limit=limit)
    items = [
        {
            "id": m.id,
            "source_id": m.source_id,
            "url": m.url[:120],
            "status": m.status,
            "next_check_at": m.next_check_at,
            "last_checked_at": m.last_checked_at,
            "failure_count": m.failure_count,
            "content_hash": (m.content_hash or "")[:12],
        }
        for m in rows
    ]
    return Page(items=items, total=len(items), limit=limit, offset=offset)


# ------------------------------------------------------------------ org/templates


class TemplateRuleIn(BaseModel):
    animal_scope: str
    action: str
    effect: str
    conditions: list | None = None
    notes: str | None = None
    # --- ADR-025: source-faithful scope for inherited entries -----------------
    source_scope_exact: str | None = Field(default=None, max_length=64)
    subject_scope_normalized: str | None = Field(
        default=None,
        pattern=(
            "^(dog|ordinary_pet|service_dog|cat|other|ordinary_dog|guide_dog|"
            "hearing_dog|assistance_dog|other_service_dog|police_dog|"
            "military_working_dog)$"
        ),
    )
    normalization_type: str | None = Field(
        default=None,
        pattern=(
            "^(exact|parent_group_for_query_only|legal_interpretation_required"
            "|compound_term_split)$"
        ),
    )
    normative_effect: str | None = Field(
        default=None,
        pattern=(
            "^(permission|prohibition|conditional_permission|"
            "exempt_from_prohibition|facilitation_required)$"
        ),
    )
    holder_scope: str | None = Field(default=None, pattern="^(any_handler|person_with_disability)$")


class TemplateIn(BaseModel):
    organization_id: str
    name: str = Field(min_length=1, max_length=160)
    venue_scope: str | None = None
    rules: list[TemplateRuleIn] = []


@admin.post("/organizations", status_code=201)
def admin_create_org(
    body: dict,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    org = Organization(name=body.get("name", ""), kind=body.get("kind", "brand"))
    db.add(org)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.ORGANIZATION_CREATE.value,
        target_type="organization",
        target_id=org.id,
        after_state={"name": org.name},
    )
    db.commit()
    return {"id": org.id, "name": org.name}


@admin.post("/policy-templates", status_code=201)
def admin_create_template(
    body: TemplateIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    if db.get(Organization, body.organization_id) is None:
        raise NotFound("组织不存在")
    template = PolicyTemplate(
        organization_id=body.organization_id,
        name=body.name,
        venue_scope=body.venue_scope,
        status="current",
    )
    db.add(template)
    db.flush()
    for r in body.rules:
        db.add(
            PolicyTemplateRule(
                template_id=template.id,
                animal_scope=r.animal_scope,
                action=r.action,
                effect=r.effect,
                conditions=r.conditions,
                rule_layer="OPERATOR_POLICY",
                notes=r.notes,
                source_scope_exact=r.source_scope_exact or r.animal_scope,
                subject_scope_normalized=r.subject_scope_normalized,
                normalization_type=r.normalization_type,
                normative_effect=r.normative_effect,
                holder_scope=r.holder_scope,
            )
        )
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.POLICY_TEMPLATE_CREATE.value,
        target_type="policy_template",
        target_id=template.id,
        after_state={"name": body.name, "rules": len(body.rules)},
    )
    db.commit()
    return {"id": template.id, "name": template.name, "rules": len(body.rules)}


class BindingIn(BaseModel):
    place_id: str
    template_id: str | None = None
    overrides: list | None = None
    source_id: str | None = None


@admin.post("/place-policy-bindings", status_code=201)
def admin_create_binding(
    body: BindingIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    if db.get(Place, body.place_id) is None:
        raise NotFound("场所不存在")
    if body.template_id and db.get(PolicyTemplate, body.template_id) is None:
        raise NotFound("模板不存在")
    # deactivate previous bindings (history preserved)
    for old in db.scalars(
        select(PlacePolicyBinding).where(
            PlacePolicyBinding.place_id == body.place_id, PlacePolicyBinding.is_active.is_(True)
        )
    ).all():
        old.is_active = False
    binding = PlacePolicyBinding(
        place_id=body.place_id,
        template_id=body.template_id,
        overrides=body.overrides,
        source_id=body.source_id,
    )
    db.add(binding)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.PLACE_BINDING_CREATE.value,
        target_type="place_policy_binding",
        target_id=binding.id,
        after_state={"place_id": body.place_id, "template_id": body.template_id},
    )
    db.commit()
    return {"id": binding.id, "place_id": binding.place_id}


# ------------------------------------------------------------------ spatial extras


@admin.post("/amenities", status_code=201)
def admin_create_amenity(
    body: dict,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    amenity = Amenity(
        place_id=body["place_id"],
        zone_id=body.get("zone_id"),
        amenity_type=body["amenity_type"],
        status=body.get("status", "available"),
        source_id=body["source_id"],
        verified_at=datetime.now(UTC),
    )
    db.add(amenity)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.AMENITY_CREATE.value,
        target_type="amenity",
        target_id=amenity.id,
        after_state={"type": amenity.amenity_type},
    )
    db.commit()
    return {"id": amenity.id}


@admin.post("/entrances", status_code=201)
def admin_create_entrance(
    body: dict,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    entrance = Entrance(
        place_id=body["place_id"],
        zone_id=body.get("zone_id"),
        name=body["name"],
        entrance_type=body.get("entrance_type", "GENERAL"),
        location_wkt=body.get("location_wkt"),
        access_notes=body.get("access_notes"),
        source_id=body["source_id"],
    )
    db.add(entrance)
    db.commit()
    return {"id": entrance.id}


@admin.post("/access-paths", status_code=201)
def admin_create_access_path(
    body: dict,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    path = AccessPath(
        place_id=body["place_id"],
        name=body["name"],
        from_node=body["from_node"],
        to_node=body["to_node"],
        steps=body.get("steps"),
        animal_scope=body.get("animal_scope"),
        conditions=body.get("conditions"),
        time_window=body.get("time_window"),
        source_id=body["source_id"],
    )
    db.add(path)
    db.commit()
    return {"id": path.id}


@admin.post("/event-policies", status_code=201)
def admin_create_event(
    body: dict,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    event = EventPolicy(
        place_id=body["place_id"],
        zone_id=body.get("zone_id"),
        name=body["name"],
        animal_scope=body["animal_scope"],
        action=body["action"],
        effect=body["effect"],
        conditions=body.get("conditions"),
        time_window=body.get("time_window"),
        effective_from=body["effective_from"],
        effective_to=body["effective_to"],
        source_id=body["source_id"],
    )
    db.add(event)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.EVENT_POLICY_CREATE.value,
        target_type="event_policy",
        target_id=event.id,
        after_state={"name": body["name"]},
    )
    db.commit()
    return {"id": event.id}


@admin.post("/data-licenses", status_code=201)
def admin_create_license(
    body: dict,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    license_ = DataLicense(
        source_id=body["source_id"],
        display_allowed=body.get("display_allowed", True),
        storage_allowed=body.get("storage_allowed", True),
        redistribution_allowed=body.get("redistribution_allowed", False),
        commercial_use_allowed=body.get("commercial_use_allowed", False),
        attribution_required=body.get("attribution_required", True),
        license_name=body.get("license_name"),
    )
    db.add(license_)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.DATA_LICENSE_CREATE.value,
        target_type="data_license",
        target_id=license_.id,
        after_state={"source_id": body["source_id"]},
    )
    db.commit()
    return {"id": license_.id}


# ------------------------------------------------------------------ effective rules


def _load_layered_rules(db: Session, place_id: str) -> dict:
    """Load all rule sources for a place and map them into LayeredRules."""
    import uuid as _uuid

    from app.models import Zone

    rules = list(
        db.scalars(
            select(AccessRule)
            .options(selectinload(AccessRule.conditions))
            .where(
                (AccessRule.place_id == place_id)
                | AccessRule.zone_id.in_(select(Zone.id).where(Zone.place_id == place_id))
            )
            .where(AccessRule.status == "current")
        ).all()
    )

    legal, guidance, template, operator, events = [], [], [], [], []

    def _to_layered(r: AccessRule) -> LayeredRule:
        return LayeredRule(
            id=r.id,
            animal_scope=r.animal_scope,
            action=r.action,
            effect=r.effect,
            rule_layer=r.rule_layer,
            origin=(
                "legal"
                if r.rule_layer == RuleLayer.LEGAL.value
                else "guidance"
                if r.rule_layer == RuleLayer.REGULATORY_GUIDANCE.value
                else "event"
                if r.rule_layer == RuleLayer.TEMPORARY_POLICY.value
                else "zone_override"
                if r.zone_id
                else "operator_direct"
            ),
            conditions=tuple(
                {
                    "condition_type": c.condition_type,
                    "value_flag": c.value_flag,
                    "value_numeric": (
                        float(c.value_numeric) if c.value_numeric is not None else None
                    ),
                    "value_text": c.value_text,
                    "value_json": c.value_json,
                }
                for c in r.conditions
            ),
            zone_id=r.zone_id,
            place_id=r.place_id,
            source_id=r.source_id,
            mandatory_level=r.mandatory_level,
            # ADR-025: source-faithful scope + normative effect layer
            source_scope_exact=r.source_scope_exact,
            subject_scope_normalized=r.subject_scope_normalized,
            normalization_type=r.normalization_type,
            normative_effect=r.normative_effect,
            holder_scope=r.holder_scope,
            operator_obligations=tuple(r.operator_obligations or ()),
        )

    def _bucket(lr: LayeredRule) -> None:
        if lr.rule_layer == RuleLayer.LEGAL.value:
            legal.append(lr)
        elif lr.rule_layer == RuleLayer.REGULATORY_GUIDANCE.value:
            guidance.append(lr)
        elif lr.rule_layer == RuleLayer.TEMPORARY_POLICY.value:
            events.append(lr)
        else:
            operator.append(lr)

    for r in rules:
        _bucket(_to_layered(r))

    # ADR-025: jurisdiction-level rules are the source of truth. They are stored
    # once (no place_id) and apply by place_type, so 《上海市养犬管理条例》第23条
    # is not copied into one row per venue. Per-place rows, when they exist, are
    # projections — the jurisdiction rule is what governs.
    place = db.get(Place, place_id)
    if place is not None:
        jurisdiction_rules = db.scalars(
            select(AccessRule)
            .options(selectinload(AccessRule.conditions))
            .where(AccessRule.jurisdiction_code.is_not(None))
            .where(AccessRule.status == "current")
        ).all()
        seen = {r.id for r in rules}
        for r in jurisdiction_rules:
            if r.id in seen:
                continue
            applies = r.applies_to_place_types or []
            if applies and place.place_type not in applies:
                continue
            _bucket(_to_layered(r))

    # template rules via active binding
    binding = db.scalar(
        select(PlacePolicyBinding)
        .where(PlacePolicyBinding.place_id == place_id, PlacePolicyBinding.is_active.is_(True))
        .order_by(PlacePolicyBinding.created_at.desc())
    )
    if binding and binding.template_id:
        tmpl = db.get(PolicyTemplate, binding.template_id)
        if tmpl:
            for tr in tmpl.rules:
                template.append(
                    LayeredRule(
                        id=f"tmpl-{tr.id}",
                        animal_scope=tr.animal_scope,
                        action=tr.action,
                        effect=tr.effect,
                        rule_layer="OPERATOR_POLICY",
                        origin="template",
                        conditions=tuple(tr.conditions or ()),
                        place_id=place_id,
                        source_id=None,
                        # ADR-025: an inherited entry keeps its source-faithful
                        # scope — bare `service_dog` never governs.
                        source_scope_exact=tr.source_scope_exact,
                        subject_scope_normalized=tr.subject_scope_normalized,
                        normalization_type=tr.normalization_type,
                        normative_effect=tr.normative_effect,
                        holder_scope=tr.holder_scope,
                    )
                )
    # explicit place/zone overrides from binding
    if binding and binding.overrides:
        for ov in binding.overrides:
            lr = LayeredRule(
                id=f"ovr-{ov.get('id', _uuid.uuid4().hex[:8])}",
                animal_scope=ov.get("animal_scope", "ordinary_pet"),
                action=ov.get("action", "enter"),
                effect=ov.get("effect", "allowed"),
                rule_layer="OPERATOR_POLICY",
                origin="zone_override" if ov.get("zone_id") else "place_override",
                conditions=tuple(ov.get("conditions") or ()),
                zone_id=ov.get("zone_id"),
                place_id=place_id,
            )
            operator.append(lr)

    # event policies table
    now = datetime.now(UTC)
    for ev in db.scalars(
        select(EventPolicy).where(EventPolicy.place_id == place_id, EventPolicy.status == "current")
    ).all():
        events.append(
            LayeredRule(
                id=f"ev-{ev.id}",
                animal_scope=ev.animal_scope,
                action=ev.action,
                effect=ev.effect,
                rule_layer="TEMPORARY_POLICY",
                origin="event",
                conditions=tuple(ev.conditions or ()),
                zone_id=ev.zone_id,
                place_id=place_id,
                source_id=ev.source_id,
                effective_from=ev.effective_from,
                effective_to=ev.effective_to,
            )
        )

    # exceptions attach to base rules by id (SG-REAL-01); only current ones load
    rule_ids = [r.id for r in rules]
    exceptions = (
        [
            LayeredException(
                id=e.id,
                rule_id=e.rule_id,
                animal_scope=e.animal_scope,
                effect=e.effect,
                source_id=e.source_id,
                status=e.status,
                effective_from=e.effective_from,
                effective_to=e.effective_to,
                # ADR-025: the carve-out matches on the precise role it names
                source_scope_exact=e.source_scope_exact,
                subject_scope_normalized=e.subject_scope_normalized,
                normalization_type=e.normalization_type,
                normative_effect=e.normative_effect,
                holder_scope=e.holder_scope,
            )
            for e in db.scalars(
                select(RuleException).where(RuleException.rule_id.in_(rule_ids))
            ).all()
        ]
        if rule_ids
        else []
    )

    # ADR-030: statutory provisos are stored once and bind by instrument, so the
    # 条例第二十三条但书 is not copied into one row per venue. Only a reviewed
    # AND current proviso is ever applied — an unactivated one binds nothing.
    for p in db.scalars(
        select(JurisdictionException).where(
            JurisdictionException.status == "current",
            JurisdictionException.review_status == "reviewed_active",
        )
    ).all():
        exceptions.append(
            LayeredException(
                id=p.id,
                rule_id="",  # instrument-bound: no single base rule is named
                animal_scope=p.animal_scope,
                effect=p.effect or "allowed",
                source_id=p.source_id,
                status=p.status,
                effective_from=p.effective_from,
                effective_to=p.effective_to,
                subject_scope_normalized=p.subject_scope_normalized,
                normalization_type=p.normalization_type or "exact",
                normative_effect=p.normative_effect,
                holder_scope=p.holder_scope,
                binding=p.binding,
                instrument_source_ids=tuple(p.instrument_source_ids or ()),
                applies_to_layer=p.applies_to_layer,
                applies_to_effects=tuple(p.applies_to_effects or ("prohibited",)),
            )
        )

    return {
        "legal": legal,
        "guidance": guidance,
        "template": template,
        "operator": operator,
        "events": events,
        "now": now,
        "exceptions": exceptions,
    }


@router.post("/places/{place_id}/effective-rules")
def effective_rules(
    place_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """v0.5 resolution: layered rules → EffectiveRuleSet (explainable).

    Body: {"animal": "dog", "service_role": "none", "action": "enter",
           "zone_id": null, "declared_role": "guide_dog" (optional),
           "holder_scopes": ["person_with_disability"] (optional)}

    ``declared_role`` (ADR-025) pins the query to one precise animal role, so a
    hearing-dog question does not inherit a guide-dog proviso.

    ``holder_scopes`` (ADR-031) is the **ephemeral** statement of who is
    handling the animal. It is read for this request and never stored:
    disability status is a sensitive attribute and there is no column for it.
    Omitting it does not mean "no" — a carve-out that names a holder condition
    is withheld and the answer becomes conditional with ``missing_inputs``,
    rather than an unconditional allowance or a bare prohibition.
    """
    if db.get(Place, place_id) is None:
        raise NotFound("场所不存在")
    grouped = _load_layered_rules(db, place_id)
    holder_scopes = body.get("holder_scopes")
    rs = resolve(
        legal=grouped["legal"],
        guidance=grouped["guidance"],
        template_rules=grouped["template"],
        operator_rules=grouped["operator"],
        event_rules=grouped["events"],
        animal=body.get("animal", "dog"),
        service_role=body.get("service_role", "none"),
        action=body.get("action", "enter"),
        zone_id=body.get("zone_id"),
        now=datetime.now(UTC),
        exceptions=grouped["exceptions"],
        declared_role=body.get("declared_role"),
        # None ⇔ not supplied. An explicit empty list means "supplied, and the
        # handler holds no statutory status", which is a different state.
        holder_context=HolderContext.of(*holder_scopes) if holder_scopes is not None else None,
    )
    # ADR-025: the normative-effect layer is additive — `effect` keeps its
    # 3-value contract for existing clients, while these fields carry what the
    # 3-value vocabulary cannot express (a carve-out, or a duty to accommodate).
    normative_effects = sorted(
        {r.normative_effect for r in rs.applicable_rules if r.normative_effect}
    )
    operator_obligations: list[str] = []
    for r in rs.applicable_rules:
        for obligation in r.operator_obligations:
            if obligation not in operator_obligations:
                operator_obligations.append(obligation)
    return {
        "effect": rs.effect,
        "compliance_state": rs.compliance_state.value,
        "applicable_rules": [r.id for r in rs.applicable_rules],
        "suppressed": [{"rule": r.id, "reason": reason} for r, reason in rs.suppressed_rules],
        "unresolved_conflicts": [[a.id, b.id] for a, b in rs.unresolved_conflicts],
        "explanation_steps": rs.explanation_steps,
        "obligations": rs.obligations,
        "applied_exceptions": rs.applied_exceptions,
        # --- ADR-031: conditional answers carry what is missing -------------
        # Progressive-question hook (no UI yet): the backend contract exposes
        # the context a consumer would have to collect, never the attribute
        # itself. `pending_exceptions` is provenance for what was *withheld*.
        "missing_inputs": rs.missing_inputs,
        "pending_exceptions": rs.pending_exceptions,
        "duplicate_exceptions": rs.duplicate_exceptions,
        # --- normative effect layer (ADR-025, additive) ---
        "normative_effects": normative_effects,
        "operator_obligations": operator_obligations,
        "facilitation_required": "facilitation_required" in normative_effects,
        "holder_scopes": sorted({r.holder_scope for r in rs.applicable_rules if r.holder_scope}),
    }


@router.get("/places/{place_id}/extras")
def place_extras(place_id: str, db: Session = Depends(get_db)):
    """Public read-only extras for the Place Detail page (spec §2.4 §4/§5/§6).

    Coexistence attributes (共处边界), amenities (设施), entrances + access paths
    (怎么进入) and the current event policies. These are spatial/structured facts
    from a source — never judgments about people (ADR-014), and observations are
    deliberately NOT included here: a field record is not a venue policy.
    """
    if db.get(Place, place_id) is None:
        raise NotFound("场所不存在")
    zone_ids = select(Zone.id).where(Zone.place_id == place_id)

    def _in_place(model, *, zoned: bool = True):
        """Rows attached to this place, plus its zones when the model has one.

        ``AccessPath`` is scoped to the place only (a route between entrances is
        not owned by a single zone), so it opts out of the zone branch — the
        column simply does not exist there.
        """
        cond = model.place_id == place_id
        if zoned:
            cond = cond | model.zone_id.in_(zone_ids)
        return select(model).where(cond)

    coex = db.scalars(_in_place(CoexistencePolicy)).all()
    amenities = db.scalars(_in_place(Amenity)).all()
    entrances = db.scalars(_in_place(Entrance)).all()
    paths = db.scalars(_in_place(AccessPath, zoned=False)).all()
    events = db.scalars(_in_place(EventPolicy)).all()

    return {
        "coexistence": [
            {
                "id": c.id,
                "zone_id": c.zone_id,
                "attribute": c.attribute,
                "value": c.value,
                "conditions": c.conditions,
                "source_id": c.source_id,
                "verified_at": c.verified_at,
            }
            for c in coex
        ],
        "amenities": [
            {
                "id": a.id,
                "zone_id": a.zone_id,
                "amenity_type": a.amenity_type,
                "status": a.status,
                "source_id": a.source_id,
                "verified_at": a.verified_at,
            }
            for a in amenities
        ],
        "entrances": [
            {
                "id": e.id,
                "zone_id": e.zone_id,
                "name": e.name,
                "entrance_type": e.entrance_type,
                "access_notes": e.access_notes,
                "source_id": e.source_id,
            }
            for e in entrances
        ],
        "access_paths": [
            {
                "id": p.id,
                "name": p.name,
                "from_node": p.from_node,
                "to_node": p.to_node,
                "steps": p.steps,
                "animal_scope": p.animal_scope,
                "time_window": p.time_window,
                "source_id": p.source_id,
            }
            for p in paths
        ],
        "event_policies": [
            {
                "id": e.id,
                "zone_id": e.zone_id,
                "name": e.name,
                "animal_scope": e.animal_scope,
                "action": e.action,
                "effect": e.effect,
                "conditions": e.conditions,
                "effective_from": e.effective_from,
                "effective_to": e.effective_to,
                "source_id": e.source_id,
            }
            for e in events
        ],
    }


# ----------------------------------------------------- user boundary profile
# The H5 "共处边界" screen needs to persist the caller's own preferences.
# These are user-scoped (not admin), so they live on `router`, not `admin`.
# A profile describes *the user's* requirement; matching is per-item and never
# produces a single score (brief §8).


class BoundaryPreferenceIn(BaseModel):
    attribute: str = Field(min_length=1, max_length=60)
    stance: str = Field(min_length=1, max_length=30)
    note: str | None = Field(default=None, max_length=300)


class BoundaryProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    is_default: bool = True
    preferences: list[BoundaryPreferenceIn] = []


#: Stances the matcher understands (app.rulespec.v05_boundary.match).
_BOUNDARY_STANCES = {"accept", "avoid", "require_prohibited", "prefer"}


def _serialize_boundary_profile(profile) -> dict:
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "name": profile.name,
        "is_default": profile.is_default,
        "preferences": [
            {
                "id": p.id,
                "attribute": p.attribute,
                "stance": p.stance,
                "note": p.note,
            }
            for p in profile.preferences
        ],
        "created_at": profile.created_at,
    }


@router.get("/boundary-profiles")
def list_my_boundary_profiles(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.v05 import BoundaryProfile

    rows = db.scalars(
        select(BoundaryProfile)
        .where(BoundaryProfile.user_id == user.id)
        .order_by(BoundaryProfile.is_default.desc())
    ).all()
    return {"items": [_serialize_boundary_profile(p) for p in rows]}


@router.get("/boundary-profiles/default")
def get_default_boundary_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns 404-free shape: `profile: null` when the user has none yet."""
    from app.models.v05 import BoundaryProfile

    profile = db.scalar(
        select(BoundaryProfile)
        .where(BoundaryProfile.user_id == user.id)
        .order_by(BoundaryProfile.is_default.desc())
    )
    return {"profile": _serialize_boundary_profile(profile) if profile else None}


@router.put("/boundary-profiles/default")
def upsert_default_boundary_profile(
    body: BoundaryProfileIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Replace the caller's default profile wholesale.

    Replacing rather than patching keeps the UI simple and avoids stale
    preferences lingering after a user clears a stance.
    """
    from app.models.v05 import BoundaryPreference, BoundaryProfile

    for pref in body.preferences:
        if pref.stance not in _BOUNDARY_STANCES:
            raise ApiError(
                f"未知边界类型 {pref.stance}",
                code="invalid_boundary_stance",
                status_code=422,
            )

    existing = db.scalar(
        select(BoundaryProfile).where(
            BoundaryProfile.user_id == user.id, BoundaryProfile.is_default.is_(True)
        )
    )
    if existing is not None:
        for old in db.scalars(
            select(BoundaryPreference).where(BoundaryPreference.profile_id == existing.id)
        ).all():
            db.delete(old)
        db.flush()
        existing.name = body.name
    else:
        existing = BoundaryProfile(user_id=user.id, name=body.name, is_default=True)
        db.add(existing)
        db.flush()

    seen: set[str] = set()
    for pref in body.preferences:
        if pref.attribute in seen:
            continue
        seen.add(pref.attribute)
        db.add(
            BoundaryPreference(
                profile_id=existing.id,
                attribute=pref.attribute,
                stance=pref.stance,
                note=pref.note,
            )
        )
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.BOUNDARY_PROFILE_UPSERT.value,
        target_type="boundary_profile",
        target_id=existing.id,
        after_state={"name": body.name, "preferences": len(seen)},
    )
    db.commit()
    db.refresh(existing)
    return _serialize_boundary_profile(existing)


@router.get("/places/{place_id}/boundary-match")
def boundary_match_endpoint(
    place_id: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Per-item MATCH/CONFLICT/UNKNOWN against the caller's boundary profile.

    Never returns a score.
    """
    from app.models.v05 import BoundaryPreference, BoundaryProfile

    place = db.get(Place, place_id)
    if place is None:
        raise NotFound("场所不存在")
    profile = db.scalar(
        select(BoundaryProfile)
        .where(BoundaryProfile.user_id == user.id)
        .order_by(BoundaryProfile.is_default.desc())
    )
    if profile is None:
        raise ApiError("尚未设置共处边界", code="no_boundary_profile", status_code=400)
    prefs = [
        (p.attribute, p.stance)
        for p in db.scalars(
            select(BoundaryPreference).where(BoundaryPreference.profile_id == profile.id)
        ).all()
    ]

    coex_rows = db.scalars(
        select(CoexistencePolicy).where(CoexistencePolicy.place_id == place_id)
    ).all()
    coexistence = {c.attribute: c.value for c in coex_rows}

    grouped = _load_layered_rules(db, place_id)
    rs = resolve(
        legal=grouped["legal"],
        guidance=grouped["guidance"],
        template_rules=grouped["template"],
        operator_rules=grouped["operator"],
        event_rules=grouped["events"],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=datetime.now(UTC),
        exceptions=grouped["exceptions"],
    )
    results = boundary_match(effective_effect=rs.effect, coexistence=coexistence, preferences=prefs)
    return {
        "profile_id": profile.id,
        "results": [
            {"attribute": r.attribute, "stance": r.stance, "verdict": r.verdict, "reason": r.reason}
            for r in results
        ],
        "summary": {
            "match": sum(1 for r in results if r.verdict == "MATCH"),
            "conflict": sum(1 for r in results if r.verdict == "CONFLICT"),
            "unknown": sum(1 for r in results if r.verdict == "UNKNOWN"),
            "note": "逐项判定，无总分",
        },
    }


@router.get("/places/{place_id}/answerability")
def place_answerability(place_id: str, db: Session = Depends(get_db)):
    if db.get(Place, place_id) is None:
        raise NotFound("场所不存在")
    from app.models import Zone

    rules = list(
        db.scalars(
            select(AccessRule)
            .options(selectinload(AccessRule.conditions))
            .where(
                (AccessRule.place_id == place_id)
                | AccessRule.zone_id.in_(select(Zone.id).where(Zone.place_id == place_id))
            )
            .where(AccessRule.status == "current")
        ).all()
    )
    serialized = [
        {
            "status": r.status,
            "effect": r.effect,
            "animal_scope": r.animal_scope,
            "zone_id": r.zone_id,
            "source_id": r.source_id,
            "last_verified_at": r.last_verified_at,
            "conditions": [
                {"condition_type": c.condition_type} for c in getattr(r, "conditions", [])
            ],
        }
        for r in rules
    ]
    coex_rows = db.scalars(
        select(CoexistencePolicy).where(CoexistencePolicy.place_id == place_id)
    ).all()
    coexistence = {c.attribute: c.value for c in coex_rows}
    cells = compute_answerability(rules=serialized, coexistence=coexistence, now=datetime.now(UTC))
    return {
        "place_id": place_id,
        "cells": [{"question": c.question, "state": c.state, "detail": c.detail} for c in cells],
    }


# ------------------------------------------------- v0.5 registry read surface
# The v0.5 domain objects below were originally write-only (create endpoints).
# An operator cannot review what they cannot list, so each gains a paged reader.
# Additive only — no existing endpoint shape changes.


@admin.get("/organizations", response_model=Page[dict])
def admin_list_organizations(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    stmt = select(Organization).order_by(Organization.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [
        {
            "id": o.id,
            "name": o.name,
            "kind": o.kind,
            "status": getattr(o, "status", None),
            "created_at": o.created_at,
        }
        for o in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@admin.get("/policy-templates", response_model=Page[dict])
def admin_list_templates(
    organization_id: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    stmt = select(PolicyTemplate)
    if organization_id:
        stmt = stmt.where(PolicyTemplate.organization_id == organization_id)
    stmt = stmt.order_by(PolicyTemplate.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = []
    for t in rows:
        rules = db.scalars(
            select(PolicyTemplateRule).where(PolicyTemplateRule.template_id == t.id)
        ).all()
        items.append(
            {
                "id": t.id,
                "organization_id": t.organization_id,
                "name": t.name,
                "venue_scope": t.venue_scope,
                "status": t.status,
                "rule_count": len(rules),
                "rules": [
                    {
                        "animal_scope": r.animal_scope,
                        "action": r.action,
                        "effect": r.effect,
                        "rule_layer": r.rule_layer,
                        "notes": r.notes,
                    }
                    for r in rules
                ],
                "created_at": t.created_at,
            }
        )
    return Page(items=items, total=total, limit=limit, offset=offset)


@admin.get("/place-policy-bindings", response_model=Page[dict])
def admin_list_bindings(
    place_id: str | None = None,
    active_only: bool = False,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    stmt = select(PlacePolicyBinding)
    if place_id:
        stmt = stmt.where(PlacePolicyBinding.place_id == place_id)
    if active_only:
        stmt = stmt.where(PlacePolicyBinding.is_active.is_(True))
    stmt = stmt.order_by(PlacePolicyBinding.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [
        {
            "id": b.id,
            "place_id": b.place_id,
            "template_id": b.template_id,
            "source_id": b.source_id,
            "is_active": b.is_active,
            "overrides": b.overrides,
            "created_at": b.created_at,
        }
        for b in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@admin.get("/amenities", response_model=Page[dict])
def admin_list_amenities(
    place_id: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    stmt = select(Amenity)
    if place_id:
        stmt = stmt.where(Amenity.place_id == place_id)
    stmt = stmt.order_by(Amenity.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [
        {
            "id": a.id,
            "place_id": a.place_id,
            "zone_id": a.zone_id,
            "amenity_type": a.amenity_type,
            "status": a.status,
            "source_id": a.source_id,
            "verified_at": a.verified_at,
        }
        for a in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@admin.get("/entrances", response_model=Page[dict])
def admin_list_entrances(
    place_id: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    stmt = select(Entrance)
    if place_id:
        stmt = stmt.where(Entrance.place_id == place_id)
    stmt = stmt.order_by(Entrance.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [
        {
            "id": e.id,
            "place_id": e.place_id,
            "zone_id": e.zone_id,
            "name": e.name,
            "entrance_type": e.entrance_type,
            "access_notes": e.access_notes,
            "source_id": e.source_id,
        }
        for e in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@admin.get("/access-paths", response_model=Page[dict])
def admin_list_access_paths(
    place_id: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    stmt = select(AccessPath)
    if place_id:
        stmt = stmt.where(AccessPath.place_id == place_id)
    stmt = stmt.order_by(AccessPath.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [
        {
            "id": p.id,
            "place_id": p.place_id,
            "name": p.name,
            "from_node": p.from_node,
            "to_node": p.to_node,
            "animal_scope": p.animal_scope,
            "time_window": p.time_window,
            "source_id": p.source_id,
        }
        for p in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@admin.get("/event-policies", response_model=Page[dict])
def admin_list_event_policies(
    place_id: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    stmt = select(EventPolicy)
    if place_id:
        stmt = stmt.where(EventPolicy.place_id == place_id)
    stmt = stmt.order_by(EventPolicy.effective_from.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    now = datetime.now(UTC)
    items = []
    for ev in rows:
        items.append(
            {
                "id": ev.id,
                "place_id": ev.place_id,
                "zone_id": ev.zone_id,
                "name": ev.name,
                "animal_scope": ev.animal_scope,
                "action": ev.action,
                "effect": ev.effect,
                "time_window": ev.time_window,
                "effective_from": ev.effective_from,
                "effective_to": ev.effective_to,
                "is_effective_now": bool(
                    ev.effective_from
                    and ev.effective_to
                    and ev.effective_from <= now <= ev.effective_to
                ),
                "source_id": ev.source_id,
            }
        )
    return Page(items=items, total=total, limit=limit, offset=offset)


@admin.get("/data-licenses", response_model=Page[dict])
def admin_list_data_licenses(
    source_id: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    stmt = select(DataLicense)
    if source_id:
        stmt = stmt.where(DataLicense.source_id == source_id)
    stmt = stmt.order_by(DataLicense.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [
        {
            "id": lic.id,
            "source_id": lic.source_id,
            "license_name": lic.license_name,
            "display_allowed": lic.display_allowed,
            "storage_allowed": lic.storage_allowed,
            "redistribution_allowed": lic.redistribution_allowed,
            "commercial_use_allowed": lic.commercial_use_allowed,
            "attribution_required": lic.attribution_required,
        }
        for lic in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


@admin.get("/coexistence-policies", response_model=Page[dict])
def admin_list_coexistence(
    place_id: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    stmt = select(CoexistencePolicy)
    if place_id:
        stmt = stmt.where(CoexistencePolicy.place_id == place_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [
        {
            "id": c.id,
            "place_id": c.place_id,
            "zone_id": c.zone_id,
            "attribute": c.attribute,
            "value": c.value,
            "source_id": c.source_id,
            "notes": getattr(c, "notes", None),
        }
        for c in rows
    ]
    return Page(items=items, total=total, limit=limit, offset=offset)


# ============================================================ evidence-first
# SourceArtifact → EvidenceBundle → Claim → Candidate (brief §5).
# Admin surface for the evidence chain; publication stays behind the guard rails.


class ArtifactIn(BaseModel):
    source_id: str | None = None
    collector_type: str
    artifact_type: str
    source_url: str | None = Field(default=None, max_length=1000)
    source_content_id: str | None = None
    media_id: str | None = None
    snapshot_ref: str | None = None
    content_hash: str | None = Field(default=None, max_length=64)
    publisher_type: str = "unknown"
    published_at: datetime | None = None
    captured_excerpt: str | None = None
    storage_allowed: bool = True
    display_allowed: bool = False
    redistribution_allowed: bool = False
    evidence_strength: str | None = Field(default=None, max_length=24)
    data_source_job_id: str | None = None
    #: Wave 01: which expansion run collected this artifact
    expansion_run_id: str | None = Field(default=None, max_length=64)


class BundleIn(BaseModel):
    artifact_id: str
    quoted_fragment: str | None = None
    extracted_fragment: str | None = None
    evidence_class: str = "original"
    derived_from_bundle_id: str | None = None
    extraction_method: str | None = None
    extraction_model: str | None = None
    extraction_model_version: str | None = None
    place_match_evidence: dict | None = None
    temporal_evidence: dict | None = None
    privacy_notes: str | None = None
    #: Wave 01: which expansion run produced this bundle
    expansion_run_id: str | None = Field(default=None, max_length=64)


class ObservationCandidateIn(BaseModel):
    evidence_bundle_id: str
    place_id: str | None = None
    zone_id: str | None = None
    animal_scope: str | None = None
    observed_action: str | None = None
    spatial_context: str | None = None
    occurred_at: datetime | None = None
    extraction_method: str | None = None
    raw_text: str | None = None
    derivation_confidence: float | None = None
    #: Wave 01: which expansion run produced this observation
    expansion_run_id: str | None = Field(default=None, max_length=64)
    #: deterministic ingestion guard — a repeat of the same observation must not
    #: become a second candidate
    dedup_key: str | None = Field(default=None, max_length=128)


@admin.post("/source-artifacts", status_code=201)
def admin_create_artifact(
    body: ArtifactIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Freeze one collector output as original evidence."""
    from app.models.evidence import SourceArtifact
    from app.services.evidence_service import CollectedArtifact, record_artifact

    if body.source_id and db.get(Source, body.source_id) is None:
        raise NotFound("来源不存在")
    collected = CollectedArtifact(
        source_platform=_platform_for_collector(body.collector_type),
        artifact_type=body.artifact_type,
        collector_type=body.collector_type,
        source_url=body.source_url,
        source_content_id=body.source_content_id,
        media_id=body.media_id,
        snapshot_ref=body.snapshot_ref,
        content_hash=body.content_hash,
        publisher_type=body.publisher_type,
        published_at=body.published_at,
        captured_excerpt=body.captured_excerpt,
        storage_allowed=body.storage_allowed,
        display_allowed=body.display_allowed,
        redistribution_allowed=body.redistribution_allowed,
    )
    strength = body.evidence_strength
    if strength is None and body.source_id:
        src = db.get(Source, body.source_id)
        if src is not None:
            from app.services.evidence_service import strength_for_artifact

            collected_probe = SimpleNamespace(collector_type=body.collector_type)
            strength = strength_for_artifact(collected_probe, src)
    artifact = record_artifact(
        db,
        collected,
        source_id=body.source_id,
        data_source_job_id=body.data_source_job_id,
        evidence_strength=strength,
        expansion_run_id=body.expansion_run_id,
    )
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.ARTIFACT_CREATE.value,
        target_type="source_artifact",
        target_id=artifact.id,
        after_state={"platform": artifact.source_platform, "type": artifact.artifact_type},
    )
    db.commit()
    _ = SourceArtifact
    return _serialize_artifact(artifact)


@admin.get("/source-artifacts", response_model=Page[dict])
def admin_list_artifacts(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    from app.models.evidence import SourceArtifact

    stmt = select(SourceArtifact).order_by(SourceArtifact.collected_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(
        items=[_serialize_artifact(a) for a in rows], total=total, limit=limit, offset=offset
    )


@admin.post("/evidence-bundles", status_code=201)
def admin_create_bundle(
    body: BundleIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Create the attributable statement a candidate will cite."""
    from app.models.evidence import SourceArtifact
    from app.services.evidence_service import create_bundle

    artifact = db.get(SourceArtifact, body.artifact_id)
    if artifact is None:
        raise NotFound("证据原件不存在")
    bundle = create_bundle(
        db,
        artifact,
        quoted_fragment=body.quoted_fragment,
        extracted_fragment=body.extracted_fragment,
        evidence_class=body.evidence_class,
        derived_from_bundle_id=body.derived_from_bundle_id,
        extraction_method=body.extraction_method,
        extraction_model=body.extraction_model,
        extraction_model_version=body.extraction_model_version,
        place_match_evidence=body.place_match_evidence,
        temporal_evidence=body.temporal_evidence,
        privacy_notes=body.privacy_notes,
        expansion_run_id=body.expansion_run_id,
    )
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.EVIDENCE_BUNDLE_CREATE.value,
        target_type="evidence_bundle",
        target_id=bundle.id,
        after_state={"class": bundle.evidence_class, "artifact_id": artifact.id},
    )
    db.commit()
    return _serialize_bundle(bundle)


@admin.get("/evidence-bundles", response_model=Page[dict])
def admin_list_bundles(
    artifact_id: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    from app.models.evidence import EvidenceBundle

    stmt = select(EvidenceBundle).order_by(EvidenceBundle.captured_at.desc())
    if artifact_id:
        stmt = stmt.where(EvidenceBundle.artifact_id == artifact_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=[_serialize_bundle(b) for b in rows], total=total, limit=limit, offset=offset)


@admin.post("/evidence/classify")
def admin_classify(
    body: dict,
    user: User = Depends(require_role(UserRole.MODERATOR)),
):
    """Preview which lane (rule / observation) captured text belongs to."""
    from app.services.evidence_service import ClaimDraft, classify

    draft = ClaimDraft(
        kind=body.get("kind") or "",
        quoted_fragment=body.get("quoted_fragment"),
        extracted_fragment=body.get("extracted_fragment"),
    )
    if not draft.kind:
        draft.kind = classify(body.get("text") or draft.quoted_fragment or "")
    else:
        draft.kind = classify(draft)
    return {"kind": draft.kind}


@admin.post("/observation-candidates", status_code=201)
def admin_create_observation_candidate(
    body: ObservationCandidateIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Observation lane: a sighting, never a rule."""
    from app.models.evidence import EvidenceBundle
    from app.services.evidence_service import ClaimDraft, create_observation_candidate

    bundle = db.get(EvidenceBundle, body.evidence_bundle_id)
    if bundle is None:
        raise NotFound("证据包不存在")
    cand = create_observation_candidate(
        db,
        bundle,
        draft=ClaimDraft(
            kind="observation",
            animal_scope=body.animal_scope,
            observed_action=body.observed_action,
            spatial_context=body.spatial_context,
            derivation_confidence=body.derivation_confidence,
        ),
        place_id=body.place_id,
        zone_id=body.zone_id,
        occurred_at=body.occurred_at,
        raw_text=body.raw_text,
    )
    # Wave 01 traceability is set after creation: the service signature is
    # shared with the AI lane, which has no run context.
    if body.expansion_run_id:
        cand.expansion_run_id = body.expansion_run_id
    if body.dedup_key:
        cand.dedup_key = body.dedup_key
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.OBSERVATION_CANDIDATE_CREATE.value,
        target_type="observation_candidate",
        target_id=cand.id,
        after_state={"status": cand.review_status},
    )
    db.commit()
    return _serialize_observation_candidate(cand)


@admin.get("/observation-candidates", response_model=Page[dict])
def admin_list_observation_candidates(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    from app.models.evidence import ObservationCandidate

    stmt = select(ObservationCandidate).order_by(ObservationCandidate.created_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(
        items=[_serialize_observation_candidate(c) for c in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin.post("/observation-candidates/{candidate_id}/transition")
def admin_transition_observation_candidate(
    candidate_id: str,
    body: dict,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):
    """Walk the observation state machine. Approval never writes an AccessRule."""
    from app.models.evidence import OBSERVATION_CANDIDATE_TRANSITIONS, ObservationCandidate

    cand = db.get(ObservationCandidate, candidate_id)
    if cand is None:
        raise NotFound("观察候选不存在")
    target = body.get("target")
    allowed = OBSERVATION_CANDIDATE_TRANSITIONS.get(cand.review_status, set())
    if target not in allowed:
        raise ApiError(
            f"非法状态迁移 {cand.review_status} → {target}",
            code="invalid_observation_transition",
        )
    if target == "PUBLISHED" and cand.evidence_bundle_id:
        # Publishing an observation claim derived from a lead-only platform is
        # redistribution: the same licence gate as the rule lane applies.
        from app.models.evidence import EvidenceBundle
        from app.services.evidence_service import ClaimKind, assert_publishable

        bundle = db.get(EvidenceBundle, cand.evidence_bundle_id)
        if bundle is not None:
            assert_publishable(bundle, kind=ClaimKind.OBSERVATION)
    before = cand.review_status
    cand.review_status = target
    cand.reviewer_id = user.id
    if body.get("note"):
        cand.review_note = str(body["note"])[:500]
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.OBSERVATION_CANDIDATE_TRANSITION.value,
        target_type="observation_candidate",
        target_id=cand.id,
        before_state={"status": before},
        after_state={"status": target},
    )
    db.commit()
    return _serialize_observation_candidate(cand)


# ------------------------------------------------------- evidence serializers


@admin.post("/reality-audit")
def admin_reality_audit(
    body: dict,
    user: User = Depends(require_role(UserRole.MODERATOR)),
):
    """Reality Audit over submitted samples (REALITY_AUDIT_PLAN, NEXT_GOAL C2).

    Same pure engine as the CLI (`python -m app.tools.reality_audit`). No DB
    writes: the samples stay request-scoped, so synthetic fixtures can be
    audited without touching production tables.
    """
    from app.tools.reality_audit import audit_samples

    samples = body.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ApiError("需要非空 samples 数组", code="samples_required")
    if len(samples) > 200:
        raise ApiError("单次审计样本过多（≤200）", code="too_many_samples")
    return audit_samples(samples)


def _platform_for_collector(collector_type: str) -> str:
    """Map a collector to its platform; unknown collectors fall back safely."""
    from app.models.evidence import CollectorType, SourcePlatform
    from app.services.evidence_service import COLLECTORS

    cls = COLLECTORS.get(collector_type)
    if cls is not None:
        return cls().source_platform
    _ = (CollectorType, SourcePlatform)
    return "platform_upload"


def _serialize_artifact(a) -> dict:
    return {
        "id": a.id,
        "source_id": a.source_id,
        "source_platform": a.source_platform,
        "collector_type": a.collector_type,
        "artifact_type": a.artifact_type,
        "source_url": a.source_url,
        "media_id": a.media_id,
        "snapshot_ref": a.snapshot_ref,
        "content_hash": (a.content_hash or "")[:12] or None,
        "collected_at": a.collected_at,
        "publisher_type": a.publisher_type,
        "published_at": a.published_at,
        "captured_excerpt": (a.captured_excerpt or "")[:500] or None,
        "storage_allowed": a.storage_allowed,
        "display_allowed": a.display_allowed,
        "redistribution_allowed": a.redistribution_allowed,
        "retention_until": a.retention_until,
        "evidence_strength": a.evidence_strength,
    }


def _serialize_bundle(b) -> dict:
    return {
        "id": b.id,
        "artifact_id": b.artifact_id,
        "source_id": b.source_id,
        "source_platform": b.source_platform,
        "source_url": b.source_url,
        "publisher_type": b.publisher_type,
        "published_at": b.published_at,
        "captured_at": b.captured_at,
        "quoted_fragment": b.quoted_fragment,
        "extracted_fragment": b.extracted_fragment,
        "evidence_class": b.evidence_class,
        "content_hash": (b.content_hash or "")[:12] or None,
        "screenshot_ref": b.screenshot_ref,
        "extraction_method": b.extraction_method,
        "extraction_model": b.extraction_model,
        "extraction_model_version": b.extraction_model_version,
        "derived_from_bundle_id": b.derived_from_bundle_id,
        "place_match_evidence": b.place_match_evidence,
        "license_metadata": b.license_metadata,
    }


def _serialize_observation_candidate(c) -> dict:
    return {
        "id": c.id,
        "evidence_bundle_id": c.evidence_bundle_id,
        "source_id": c.source_id,
        "place_id": c.place_id,
        "zone_id": c.zone_id,
        "animal_scope": c.animal_scope,
        "observed_action": c.observed_action,
        "spatial_context": c.spatial_context,
        "occurred_at": c.occurred_at,
        "extraction_method": c.extraction_method,
        "raw_text": (c.raw_text or "")[:500] or None,
        "review_status": c.review_status,
        "review_note": c.review_note,
        "published_claim_id": c.published_claim_id,
        "derivation_confidence": c.derivation_confidence,
    }
