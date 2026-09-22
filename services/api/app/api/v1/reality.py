"""v0.9-R1 Reality endpoints (design v0.9 §7, §9, §13).

Two surfaces on the same data:

- consumer  : ``GET /places/{place_id}/reality`` — the RealityAnswer aggregate,
              human-verified published claims only, freshness shown as facts.
- admin     : candidate queue + human-only VERIFIED/HOLD/REJECTED decisions.
              ``reality_decision`` is NEVER written by AI; the endpoint requires
              a role and records the reviewer identity.

Hard rules enforced here (and by the schema):

- only VERIFIED / VERIFIED_WITH_NOTE candidates publish a claim;
- a claim never exposes ordinary staff identity (actor_role only);
- expired facts are excluded from "recent" summaries (see reality_summary);
- AI-derived (unverified) rows never appear in consumer aggregates.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.audit_events import AuditEvent
from app.core.errors import ApiError, NotFound
from app.core.security import get_optional_user, require_role
from app.db.session import get_db
from app.models import (
    AnimalFacility,
    ObservedPresence,
    Place,
    RealityCandidate,
    StaffResponseObservation,
    User,
)
from app.models.enums import (
    REALITY_VERIFIED_DECISIONS,
    RealityFreshnessState,
    RealityVerificationStatus,
    UserRole,
)
from app.schemas.common import Page
from app.schemas.reality import (
    AnimalFacilityOut,
    FacilitySummaryItem,
    ObservedPresenceOut,
    RealityAnswer,
    RealityCandidateIn,
    RealityCandidateOut,
    RealityDecisionIn,
    StaffResponseObservationOut,
    StaffResponseSummaryItem,
)
from app.services.reality_summary import (
    _Row,
    freshness_for,
    summarize,
)

router = APIRouter(tags=["reality"])
admin = APIRouter(tags=["admin:reality"])


def _freshness_state(observed_at: datetime | None) -> RealityFreshnessState | None:
    """Map a summary-bucket string onto the stored enum value."""
    if observed_at is None:
        return None
    return RealityFreshnessState(freshness_for(observed_at).lower())


# ---------------------------------------------------------------------------
# Consumer — RealityAnswer (v0.9 §9)
# ---------------------------------------------------------------------------


@router.get("/places/{place_id}/reality", response_model=RealityAnswer)
def place_reality(
    place_id: str,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> RealityAnswer:
    """The reality half of a CoexistenceSnapshot, per place (v0.9 §9)."""
    if db.get(Place, place_id) is None:
        raise NotFound("场所不存在")

    now = datetime.now(UTC)

    # Published, human-verified observed-presence claims (oldest first).
    claims = db.scalars(
        select(ObservedPresence)
        .where(
            ObservedPresence.place_id == place_id,
            ObservedPresence.verification_status.in_(
                [
                    RealityVerificationStatus.HUMAN_VERIFIED.value,
                    RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE.value,
                ]
            ),
        )
        .order_by(ObservedPresence.observed_at.asc())
    ).all()

    rows = [
        _Row(
            observed_at=c.observed_at,
            source_id=c.source_id,
            evidence_id=c.evidence_bundle_id,
            zone_name=None,  # zone name resolved by caller if needed
            action=c.observed_action.value if c.observed_action else None,
            human_verified=True,
        )
        for c in claims
    ]
    summary = summarize(rows, now=now)

    # Staff response summary (facts only: action counts).
    srows = db.execute(
        select(StaffResponseObservation.response_action, func.count())
        .where(
            StaffResponseObservation.place_id == place_id,
            StaffResponseObservation.verification_status.in_(
                [
                    RealityVerificationStatus.HUMAN_VERIFIED.value,
                    RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE.value,
                ]
            ),
        )
        .group_by(StaffResponseObservation.response_action)
    ).all()
    staff_summary = [
        StaffResponseSummaryItem(response_action=a, count=n)
        for a, n in sorted(srows, key=lambda x: str(x[0]))
        if a
    ]

    # Facility summary (facts only).
    frows = db.execute(
        select(
            AnimalFacility.facility_type,
            AnimalFacility.operational_state,
            func.count(),
            func.max(AnimalFacility.last_verified_at),
        )
        .where(
            AnimalFacility.place_id == place_id,
            AnimalFacility.verification_status.in_(
                [
                    RealityVerificationStatus.HUMAN_VERIFIED.value,
                    RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE.value,
                ]
            ),
            AnimalFacility.operational_state != "removed",
        )
        .group_by(AnimalFacility.facility_type, AnimalFacility.operational_state)
    ).all()
    facility_summary = [
        FacilitySummaryItem(
            facility_type=ft,
            count=n,
            operational_state=st,
            last_verified_at=maxv,
        )
        for ft, st, n, maxv in frows
    ]

    return RealityAnswer(
        state=summary.state,
        last_seen_at=summary.last_seen_at,
        evidence_count=summary.evidence_count,
        distinct_source_count=summary.distinct_source_count,
        observed_zones=list(summary.observed_zones),
        observed_actions=list(summary.observed_actions),
        staff_response_summary=staff_summary,
        facility_summary=facility_summary,
        freshness_state=summary.freshness_state,
        verification_state=summary.verification_state,
        recent_count_7d=summary.recent_count_7d,
        recent_count_30d=summary.recent_count_30d,
        days_since_last_seen=summary.days_since_last_seen,
        note=summary.note,
    )


# ---------------------------------------------------------------------------
# Consumer — Reality contribution (v0.9 §25.2, AC10)
# ---------------------------------------------------------------------------


@router.post(
    "/places/{place_id}/reality/contributions",
    response_model=RealityCandidateOut,
    status_code=201,
)
def contribute_reality(
    place_id: str,
    body: RealityCandidateIn,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> RealityCandidate:
    """A signed-in visitor contributes an on-site reality fact (v0.9 §25.2).

    Three structured branches map onto the three candidate types:

    - ``observed_presence`` — 「我刚刚看到动物」 (animal, where, count, action)
    - ``staff_response``    — 「我看到工作人员怎么处理」
    - ``animal_facility``   — 「我发现这里有动物相关设施」

    The entry lands as a REVIEW_PENDING candidate with ``reality_decision``
    untouched — AI never sets it. Reviewer role lives on the admin endpoint.
    Unknown never becomes allowed; a contribution never becomes a rule.
    """
    if user is None:
        raise ApiError("请先登录再贡献现场情况", code="auth_required", status_code=401)
    if db.get(Place, place_id) is None:
        raise NotFound("场所不存在")

    cand = RealityCandidate(
        candidate_type=body.candidate_type,
        place_id=place_id,
        zone_id=body.zone_id,
        source_id=body.source_id,
        evidence_bundle_id=body.evidence_bundle_id,
        animal_scope=body.animal_scope.value if body.animal_scope else None,
        observed_at=body.observed_at,
        captured_at=body.captured_at,
        payload=body.payload,
        review_status="REVIEW_PENDING",
        verification_status=RealityVerificationStatus.UNVERIFIED,
    )
    if cand.observed_at is not None:
        cand.freshness_state = _freshness_state(cand.observed_at)
    db.add(cand)
    db.flush()
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.REALITY_CANDIDATE_CREATE.value,
        target_type="reality_candidate",
        target_id=str(cand.id),
        after_state={
            "candidate_type": cand.candidate_type,
            "place_id": cand.place_id,
            "review_status": cand.review_status,
            "verification_status": cand.verification_status.value,
            "submitted_by_contributor": True,
        },
    )
    db.commit()
    db.refresh(cand)
    return cand


# ---------------------------------------------------------------------------
# Admin — candidate queue + human decision (v0.9 §7.4, §13)
# ---------------------------------------------------------------------------


@admin.get("/reality/candidates", response_model=Page[RealityCandidateOut])
def list_reality_candidates(
    candidate_type: str | None = None,
    review_status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[RealityCandidateOut]:
    stmt = select(RealityCandidate)
    if candidate_type:
        stmt = stmt.where(RealityCandidate.candidate_type == candidate_type)
    if review_status:
        stmt = stmt.where(RealityCandidate.review_status == review_status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(RealityCandidate.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


@admin.post("/reality/candidates", response_model=RealityCandidateOut, status_code=201)
def create_reality_candidate(
    body: RealityCandidateIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> RealityCandidate:
    """Ingest a candidate (AI-derivable). Decision remains empty; AI never VERIFIES."""
    if db.get(Place, body.place_id) is None:
        raise NotFound("场所不存在")
    cand = RealityCandidate(
        candidate_type=body.candidate_type,
        place_id=body.place_id,
        zone_id=body.zone_id,
        source_id=body.source_id,
        evidence_bundle_id=body.evidence_bundle_id,
        animal_scope=body.animal_scope.value if body.animal_scope else None,
        observed_at=body.observed_at,
        captured_at=body.captured_at,
        payload=body.payload,
        review_status="REVIEW_PENDING",
        verification_status=RealityVerificationStatus.DERIVED_AI_ONLY,
    )
    if cand.observed_at is not None:
        cand.freshness_state = _freshness_state(cand.observed_at)
    db.add(cand)
    db.flush()  # PkMixin id is a DB-side default; record_audit refuses a bare "None" target_id
    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.REALITY_CANDIDATE_CREATE.value,
        target_type="reality_candidate",
        target_id=str(cand.id),
        after_state={
            "candidate_type": cand.candidate_type,
            "place_id": cand.place_id,
            "review_status": cand.review_status,
            "verification_status": cand.verification_status.value,
        },
    )
    db.commit()
    db.refresh(cand)
    return cand


@admin.post(
    "/reality/candidates/{candidate_id}/decision",
    response_model=RealityCandidateOut,
)
def decide_reality_candidate(
    candidate_id: str,
    body: RealityDecisionIn,
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> RealityCandidate:
    """Human-only reality decision (v0.9 §7.4). AI may never call this.

    VERIFIED / VERIFIED_WITH_NOTE publish the claim; HOLD / REJECTED keep it
    unpublished. The reviewer is recorded; ordinary staff identity is never
    exposed to consumers.
    """
    cand = db.get(RealityCandidate, candidate_id)
    if cand is None:
        raise NotFound("Reality 候选不存在")

    cand.reality_decision = body.reality_decision
    cand.decision_note = body.decision_note
    cand.reviewer = user.display_name or user.email or user.phone or "unknown"
    cand.decided_at = datetime.now(UTC)
    cand.review_status = "REVIEWED"

    if body.reality_decision.value in REALITY_VERIFIED_DECISIONS:
        claim = _publish_claim(db, cand)
        if claim is not None:
            cand.published_claim_id = claim.id
            cand.published_at = datetime.now(UTC)

    record_audit(
        db,
        request=None,
        actor_user_id=user.id,
        actor_role=str(user.role),
        action=AuditEvent.REALITY_DECISION.value,
        target_type="reality_candidate",
        target_id=str(cand.id),
        after_state={
            "reality_decision": body.reality_decision.value,
            "published_claim_id": cand.published_claim_id,
        },
    )
    db.commit()
    db.refresh(cand)
    return cand


def _publish_claim(db: Session, cand: RealityCandidate):
    """Project a VERIFIED candidate into its published claim table (v0.9 §7.4).

    Consumer-visible reality claims must carry Evidence + Review + Freshness.
    The claim copies the source/evidence linkage and verification posture from
    the candidate; it never asserts anything the candidate review did not.
    """
    payload = cand.payload or {}
    status = (
        RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE
        if cand.decision_note
        else RealityVerificationStatus.HUMAN_VERIFIED
    )
    claim: ObservedPresence | StaffResponseObservation | AnimalFacility
    if cand.candidate_type == "observed_presence":
        claim = ObservedPresence(
            candidate_id=cand.id,
            place_id=cand.place_id,
            zone_id=cand.zone_id,
            animal_scope=cand.animal_scope,
            animal_count_estimate=payload.get("animal_count_estimate"),
            observed_action=payload.get("observed_action"),
            observed_context=payload.get("observed_context"),
            observed_at=cand.observed_at,
            captured_at=cand.captured_at,
            source_id=cand.source_id,
            evidence_bundle_id=cand.evidence_bundle_id,
            verification_status=status,
            freshness_state=_freshness_state(cand.observed_at),
            last_verified_at=cand.decided_at,
        )
    elif cand.candidate_type == "staff_response":
        claim = StaffResponseObservation(
            candidate_id=cand.id,
            place_id=cand.place_id,
            zone_id=cand.zone_id,
            actor_role=payload.get("actor_role", "unknown_staff"),
            trigger_context=payload.get("trigger_context"),
            response_action=payload.get("response_action"),
            response_outcome=payload.get("response_outcome"),
            policy_statement_verbatim=payload.get("policy_statement_verbatim"),
            observed_at=cand.observed_at,
            captured_at=cand.captured_at,
            source_id=cand.source_id,
            evidence_bundle_id=cand.evidence_bundle_id,
            verification_status=status,
            freshness_state=_freshness_state(cand.observed_at),
            last_verified_at=cand.decided_at,
        )
    elif cand.candidate_type == "animal_facility":
        claim = AnimalFacility(
            candidate_id=cand.id,
            place_id=cand.place_id,
            zone_id=cand.zone_id,
            facility_type=payload.get("facility_type"),
            operator_provided=payload.get("operator_provided", False),
            access_mode=payload.get("access_mode", "unknown"),
            capacity=payload.get("capacity"),
            size_limit=payload.get("size_limit"),
            weather_protection=payload.get("weather_protection"),
            shade=payload.get("shade"),
            ventilation=payload.get("ventilation"),
            water_available=payload.get("water_available"),
            supervision_state=payload.get("supervision_state"),
            security_or_lock_state=payload.get("security_or_lock_state"),
            operational_state=payload.get("operational_state", "active"),
            observed_at=cand.observed_at,
            last_verified_at=cand.decided_at,
            source_id=cand.source_id,
            evidence_bundle_id=cand.evidence_bundle_id,
            verification_status=status,
            freshness_state=_freshness_state(cand.observed_at),
        )
    else:
        raise ValueError(f"unknown candidate_type: {cand.candidate_type}")
    db.add(claim)
    db.flush()
    return claim


# ---------------------------------------------------------------------------
# Admin — published claim reads (evidence viewer support)
# ---------------------------------------------------------------------------


@admin.get("/places/{place_id}/reality/observed", response_model=Page[ObservedPresenceOut])
def admin_list_observed(
    place_id: str,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[ObservedPresenceOut]:
    stmt = (
        select(ObservedPresence)
        .where(ObservedPresence.place_id == place_id)
        .order_by(ObservedPresence.observed_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


@admin.get(
    "/places/{place_id}/reality/staff-responses",
    response_model=Page[StaffResponseObservationOut],
)
def admin_list_staff_responses(
    place_id: str,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[StaffResponseObservationOut]:
    stmt = (
        select(StaffResponseObservation)
        .where(StaffResponseObservation.place_id == place_id)
        .order_by(StaffResponseObservation.observed_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


@admin.get(
    "/places/{place_id}/reality/facilities",
    response_model=Page[AnimalFacilityOut],
)
def admin_list_facilities(
    place_id: str,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[AnimalFacilityOut]:
    stmt = (
        select(AnimalFacility)
        .where(AnimalFacility.place_id == place_id)
        .order_by(AnimalFacility.created_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(items=rows, total=total, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# CoexistenceSnapshot — the one aggregate every consumer surface reads (v0.9 §9, AC9)
# ---------------------------------------------------------------------------


@router.post("/places/{place_id}/coexistence")
def coexistence_snapshot(place_id: str, body: dict, db: Session = Depends(get_db)) -> dict:
    """Assemble the single CoexistenceSnapshot for a place (v0.9 §9 / AC9).

    Body is the same shape as ``POST /places/{place_id}/access-answer``:

        {"animal": "dog", "service_role": "none", "action": "enter",
         "zone_id": null, "declared_role": "guide_dog" (optional),
         "holder_scopes": [...] (optional)}

    The response bundles, in one object:

    - ``rule_answer``           — full AccessAnswer (unified rule model)
    - ``reality_answer``        — RealityAnswer (six-state reality summary)
    - ``staff_response_summary``— action counts (facts only)
    - ``facility_summary``      — facility facts with verified freshness
    - ``divergence``            — RuleRealityDivergence (describes only)
    - ``evidence_summary``      — rule evidence + reality evidence side by side

    Home / Search / Map / Place must all read this endpoint instead of
    recomputing rule or reality themselves (「禁止页面自行算 Rule」).
    """
    from app.models import Zone
    from app.rulespec.access_answer import (
        PlaceFacts,
        ZoneFacts,
        as_plain,
        build_access_answer,
    )
    from app.rulespec.holder_scope import HolderContext
    from app.rulespec.v05_resolver import resolve
    from app.services.coexistence_snapshot import build_coexistence_snapshot, to_plain

    place = db.get(Place, place_id)
    if place is None:
        raise NotFound("场所不存在")

    zone: Zone | None = None
    if body.get("zone_id"):
        zone = db.get(Zone, body["zone_id"])
        if zone is not None and zone.place_id != place_id:
            raise NotFound("区域不属于该场所")

    from app.api.v1.v05 import _load_layered_rules, _load_rule_facts

    grouped = _load_layered_rules(db, place_id)
    holder_scopes = body.get("holder_scopes")
    now = datetime.now(UTC)
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
        now=now,
        exceptions=grouped["exceptions"],
        declared_role=body.get("declared_role"),
        holder_context=HolderContext.of(*holder_scopes) if holder_scopes is not None else None,
    )
    rule_facts = _load_rule_facts(db, [str(r.id) for r in rs.applicable_rules])
    rule_answer = as_plain(
        build_access_answer(
            query={
                "place_id": place_id,
                "zone_id": body.get("zone_id"),
                "animal": body.get("animal", "dog"),
                "service_role": body.get("service_role", "none"),
                "declared_role": body.get("declared_role"),
                "action": body.get("action", "enter"),
                "holder_scopes_supplied": holder_scopes,
            },
            place=PlaceFacts(
                id=place.id, canonical_name=place.canonical_name, place_type=place.place_type
            ),
            zone=ZoneFacts(id=zone.id, name=zone.name, zone_type=zone.zone_type) if zone else None,
            rule_set=rs,
            rule_facts=rule_facts,
        )
    )

    reality_answer = _reality_answer_for_place(db, place_id, now)

    snapshot = build_coexistence_snapshot(
        place_id=place_id,
        rule_answer=rule_answer,
        reality_answer=reality_answer,
        staff_response_summary=reality_answer.get("staff_response_summary", []),
        facility_summary=reality_answer.get("facility_summary", []),
        now=now,
    )
    return to_plain(snapshot)


def _reality_answer_for_place(db: Session, place_id: str, now: datetime) -> dict:
    """Build the consumer RealityAnswer dict (same logic as GET /reality)."""
    from app.services.reality_summary import _Row, summarize

    claims = db.scalars(
        select(ObservedPresence)
        .where(
            ObservedPresence.place_id == place_id,
            ObservedPresence.verification_status.in_(
                [
                    RealityVerificationStatus.HUMAN_VERIFIED.value,
                    RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE.value,
                ]
            ),
        )
        .order_by(ObservedPresence.observed_at.asc())
    ).all()
    rows = [
        _Row(
            observed_at=c.observed_at,
            source_id=c.source_id,
            evidence_id=c.evidence_bundle_id,
            zone_name=None,
            action=c.observed_action.value if c.observed_action else None,
            human_verified=True,
        )
        for c in claims
    ]
    summary = summarize(rows, now=now)

    srows = db.execute(
        select(StaffResponseObservation.response_action, func.count())
        .where(
            StaffResponseObservation.place_id == place_id,
            StaffResponseObservation.verification_status.in_(
                [
                    RealityVerificationStatus.HUMAN_VERIFIED.value,
                    RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE.value,
                ]
            ),
        )
        .group_by(StaffResponseObservation.response_action)
    ).all()
    staff_summary = [
        {"response_action": a, "count": n} for a, n in sorted(srows, key=lambda x: str(x[0])) if a
    ]

    frows = db.execute(
        select(
            AnimalFacility.facility_type,
            AnimalFacility.operational_state,
            func.count(),
            func.max(AnimalFacility.last_verified_at),
        )
        .where(
            AnimalFacility.place_id == place_id,
            AnimalFacility.verification_status.in_(
                [
                    RealityVerificationStatus.HUMAN_VERIFIED.value,
                    RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE.value,
                ]
            ),
            AnimalFacility.operational_state != "removed",
        )
        .group_by(AnimalFacility.facility_type, AnimalFacility.operational_state)
    ).all()
    facility_summary = [
        {
            "facility_type": ft,
            "count": n,
            "operational_state": st,
            "last_verified_at": maxv,
        }
        for ft, st, n, maxv in frows
    ]

    return {
        "state": summary.state,
        "last_seen_at": summary.last_seen_at,
        "evidence_count": summary.evidence_count,
        "distinct_source_count": summary.distinct_source_count,
        "observed_zones": list(summary.observed_zones),
        "observed_actions": list(summary.observed_actions),
        "staff_response_summary": staff_summary,
        "facility_summary": facility_summary,
        "freshness_state": summary.freshness_state,
        "verification_state": summary.verification_state,
        "recent_count_7d": summary.recent_count_7d,
        "recent_count_30d": summary.recent_count_30d,
        "days_since_last_seen": summary.days_since_last_seen,
        "note": summary.note,
    }
