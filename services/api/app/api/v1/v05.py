"""v0.5 API: candidates, monitors, jobs, org/templates, events, amenities,
entrances, access paths, boundary, answerability, data licenses (NEXT_GOAL §B).

Old endpoints unchanged (additive). Admin review actions are audited.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.errors import ApiError, NotFound
from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models import AccessRule, Place, Source, User
from app.models.enums import UserRole
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
from app.rulespec.v05_boundary import match as boundary_match
from app.rulespec.v05_resolver import (
    LayeredRule,
    RuleLayer,
    resolve,
)
from app.schemas.common import Page
from app.services.answerability import compute_answerability
from app.services.candidate_service import create_from_extraction, publish, transition
from app.services.source_monitor import check_monitor

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
    proposed_conditions: list | None = None
    extraction_method: str
    extraction_provider: str | None = None
    internal_confidence: float | None = Field(default=None, ge=0, le=1)
    raw_text: str | None = None
    media_id: str | None = None


class CandidateReview(BaseModel):
    target: str  # next state
    note: str | None = None


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
    cand = create_from_extraction(
        db,
        source_id=body.source_id,
        place_id=body.place_id,
        zone_id=body.zone_id,
        animal_scope=body.animal_scope,
        action=body.action,
        effect=body.effect,
        proposed_conditions=body.proposed_conditions,
        extraction_method=body.extraction_method,
        extraction_provider=body.extraction_provider,
        internal_confidence=body.internal_confidence,
        raw_text=body.raw_text,
        media_id=body.media_id,
    )
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="candidate.create",
        target_type="rule_candidate",
        target_id=cand.id,
        after_state={"status": cand.review_status, "method": body.extraction_method},
    )
    db.commit()
    return _candidate_dict(cand)


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
        action="candidate.transition",
        target_type="rule_candidate",
        target_id=cand.id,
        before_state={"status": before},
        after_state={"status": cand.review_status, "note": body.note},
    )
    db.commit()
    return _candidate_dict(cand)


@admin.post("/candidates/{candidate_id}/publish")
def admin_publish_candidate(
    candidate_id: str,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
):

    cand = db.get(RuleCandidate, candidate_id)
    if cand is None:
        raise NotFound("候选不存在")
    rule = publish(db, cand, reviewer_id=user.id)
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="candidate.publish",
        target_type="access_rule",
        target_id=rule.id,
        after_state={"candidate_id": cand.id, "effect": rule.effect},
    )
    db.commit()
    return {
        "published_rule_id": rule.id,
        "candidate_id": cand.id,
        "candidate_status": cand.review_status,
    }


# ------------------------------------------------------------------ source monitors


class MonitorIn(BaseModel):
    source_id: str
    url: str = Field(min_length=10, max_length=500)
    schedule_minutes: int = Field(default=1440, ge=5)
    place_id: str | None = None


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
    )
    db.add(monitor)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="monitor.create",
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
    from app.services.evidence_service import record_monitor_change

    monitor = db.get(SourceMonitor, monitor_id)
    if monitor is None:
        raise NotFound("监控不存在")
    sweep = check_monitor(monitor)
    candidate_id = None
    bundle_id = None
    artifact_id = None
    if sweep.outcome == "changed":
        # source changed → diff artifact → EvidenceBundle (brief §6)
        recorded = record_monitor_change(
            db,
            monitor,
            fetch_result=sweep.fetch,
            previous_hash=sweep.previous_hash,
        )
        if recorded is not None:
            artifact, bundle = recorded
            artifact_id, bundle_id = artifact.id, bundle.id
        # diff artifact = raw excerpt kept on candidate for review
        cand = create_from_extraction(
            db,
            source_id=monitor.source_id,
            extraction_method="url_monitor",
            place_id=monitor.place_id,
            raw_text=monitor.last_excerpt or "source content changed",
        )
        candidate_id = cand.id
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="monitor.check",
        target_type="source_monitor",
        target_id=monitor.id,
        after_state={
            "outcome": sweep.outcome,
            "candidate_id": candidate_id,
            "evidence_bundle_id": bundle_id,
        },
    )
    db.commit()
    return {
        "outcome": sweep.outcome,
        "candidate_id": candidate_id,
        "artifact_id": artifact_id,
        "evidence_bundle_id": bundle_id,
        "content_hash": (monitor.content_hash or "")[:12],
        "failure_count": monitor.failure_count,
    }


# ------------------------------------------------------------------ org/templates


class TemplateRuleIn(BaseModel):
    animal_scope: str
    action: str
    effect: str
    conditions: list | None = None
    notes: str | None = None


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
        action="organization.create",
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
            )
        )
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="policy_template.create",
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
        action="place_binding.create",
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
        action="amenity.create",
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
        action="event_policy.create",
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
        action="data_license.create",
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
            .where(
                (AccessRule.place_id == place_id)
                | AccessRule.zone_id.in_(select(Zone.id).where(Zone.place_id == place_id))
            )
            .where(AccessRule.status == "current")
        ).all()
    )

    legal, guidance, template, operator, events = [], [], [], [], []
    for r in rules:
        lr = LayeredRule(
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
                c if isinstance(c, dict) else {"condition_type": c} for c in (r.conditions or [])
            ),
            zone_id=r.zone_id,
            place_id=r.place_id,
            source_id=r.source_id,
        )
        if r.rule_layer == RuleLayer.LEGAL.value:
            legal.append(lr)
        elif r.rule_layer == RuleLayer.REGULATORY_GUIDANCE.value:
            guidance.append(lr)
        elif r.rule_layer == RuleLayer.TEMPORARY_POLICY.value:
            events.append(lr)
        else:
            operator.append(lr)

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

    return {
        "legal": legal,
        "guidance": guidance,
        "template": template,
        "operator": operator,
        "events": events,
        "now": now,
    }


@router.post("/places/{place_id}/effective-rules")
def effective_rules(
    place_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """v0.5 resolution: layered rules → EffectiveRuleSet (explainable).

    Body: {"animal": "dog", "service_role": "none", "action": "enter",
           "zone_id": null}
    """
    if db.get(Place, place_id) is None:
        raise NotFound("场所不存在")
    grouped = _load_layered_rules(db, place_id)
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
    )
    return {
        "effect": rs.effect,
        "compliance_state": rs.compliance_state.value,
        "applicable_rules": [r.id for r in rs.applicable_rules],
        "suppressed": [{"rule": r.id, "reason": reason} for r, reason in rs.suppressed_rules],
        "unresolved_conflicts": [[a.id, b.id] for a, b in rs.unresolved_conflicts],
        "explanation_steps": rs.explanation_steps,
        "obligations": rs.obligations,
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
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="boundary_profile.upsert",
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
    data_source_job_id: str | None = None


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
    artifact = record_artifact(
        db,
        collected,
        source_id=body.source_id,
        data_source_job_id=body.data_source_job_id,
    )
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="artifact.create",
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
    )
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="evidence_bundle.create",
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
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action="observation_candidate.create",
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
        action="observation_candidate.transition",
        target_type="observation_candidate",
        target_id=cand.id,
        before_state={"status": before},
        after_state={"status": target},
    )
    db.commit()
    return _serialize_observation_candidate(cand)


# ------------------------------------------------------- evidence serializers


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
