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
    """One monitor sweep: unchanged | changed | failed. On change a
    RuleCandidate (EXTRACTED) is created — never a direct rule mutation."""

    monitor = db.get(SourceMonitor, monitor_id)
    if monitor is None:
        raise NotFound("监控不存在")
    outcome = check_monitor(monitor)
    candidate_id = None
    if outcome == "changed":
        # diff artifact = raw excerpt kept on candidate for review
        cand = create_from_extraction(
            db,
            source_id=monitor.source_id,
            extraction_method="url_monitor",
            place_id=monitor.place_id,
            raw_text="source content changed",
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
        after_state={"outcome": outcome, "candidate_id": candidate_id},
    )
    db.commit()
    return {
        "outcome": outcome,
        "candidate_id": candidate_id,
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
