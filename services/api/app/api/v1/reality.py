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

from datetime import UTC, datetime, timedelta
from typing import TypedDict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select, union_all
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.audit_events import AuditEvent
from app.core.errors import ApiError, NotFound
from app.core.security import get_optional_user, require_role
from app.db.session import get_db
from app.models import (
    AnimalFacility,
    DisputeCase,
    EvidenceBundle,
    ObservedPresence,
    Place,
    RealityCandidate,
    RealityConfirmation,
    RealityReport,
    SourceArtifact,
    StaffResponseObservation,
    User,
    Zone,
)
from app.models.enums import (
    REALITY_VERIFIED_DECISIONS,
    DisputeCaseStatus,
    DisputeTargetType,
    RealityVerificationStatus,
    UserRole,
)
from app.schemas.common import Page
from app.schemas.reality import (
    AnimalFacilityOut,
    ObservedPresenceOut,
    RealityAnswer,
    RealityCandidateIn,
    RealityCandidateOut,
    RealityDecisionIn,
    RealityEventOut,
    StaffResponseObservationOut,
)
from app.services.reality_freshness import freshness_state
from app.services.reality_summary import _Row, summarize

router = APIRouter(tags=["reality"])
admin = APIRouter(tags=["admin:reality"])

VERIFIED_STATUS_VALUES = [
    RealityVerificationStatus.HUMAN_VERIFIED.value,
    RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE.value,
]


class _EventReportMeta(TypedDict):
    submitted_at: datetime | None
    time_evidence_state: str | None
    origin: str | None
    fact_evidence_state: str | None
    place_match_state: str | None
    content_published_at: datetime | None
    claimed_event_at: datetime | None


class _EventEvidenceMeta(TypedDict):
    material_type: str | None
    source_platform: str | None
    publisher_type: str | None
    evidence_class: str | None
    display_allowed: bool | None


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
    return RealityAnswer(**_reality_answer_for_place(db, place_id, datetime.now(UTC)))



def _enum_text(value: object | None) -> str | None:
    """Return the stable string value of a SQLAlchemy enum/string field."""
    if value is None:
        return None
    return str(getattr(value, "value", value))


def _presence_event(
    row: ObservedPresence,
    report_meta: _EventReportMeta | None = None,
    evidence_meta: _EventEvidenceMeta | None = None,
    *,
    confirmation_count: int = 0,
    dispute_open: bool = False,
) -> RealityEventOut:
    report_meta = report_meta or {}
    evidence_meta = evidence_meta or {}
    return RealityEventOut(
        id=row.id,
        event_type="observed_presence",
        place_id=row.place_id,
        zone_id=row.zone_id,
        event_at=row.observed_at,
        time_basis="observed",
        time_evidence_state=report_meta.get("time_evidence_state"),
        origin=report_meta.get("origin"),
        fact_evidence_state=report_meta.get("fact_evidence_state"),
        place_match_state=report_meta.get("place_match_state"),
        content_published_at=report_meta.get("content_published_at"),
        claimed_event_at=report_meta.get("claimed_event_at"),
        animal_scope=_enum_text(row.animal_scope),
        observed_action=_enum_text(row.observed_action),
        observed_context=row.observed_context,
        source_id=row.source_id,
        evidence_bundle_id=row.evidence_bundle_id,
        evidence_material_type=evidence_meta.get("material_type"),
        evidence_source_platform=evidence_meta.get("source_platform"),
        evidence_publisher_type=evidence_meta.get("publisher_type"),
        evidence_class=evidence_meta.get("evidence_class"),
        evidence_display_allowed=evidence_meta.get("display_allowed"),
        submitted_at=report_meta.get("submitted_at"),
        confirmation_count=confirmation_count,
        dispute_open=dispute_open,
        verification_status=_enum_text(row.verification_status) or "unverified",
        freshness_state=_enum_text(row.freshness_state),
        last_verified_at=row.last_verified_at,
    )


def _staff_event(
    row: StaffResponseObservation,
    report_meta: _EventReportMeta | None = None,
    *,
    confirmation_count: int = 0,
    dispute_open: bool = False,
) -> RealityEventOut:
    report_meta = report_meta or {}
    evidence_meta = evidence_meta or {}
    return RealityEventOut(
        id=row.id,
        event_type="staff_response",
        place_id=row.place_id,
        zone_id=row.zone_id,
        event_at=row.observed_at,
        time_basis="observed",
        time_evidence_state=report_meta.get("time_evidence_state"),
        origin=report_meta.get("origin"),
        fact_evidence_state=report_meta.get("fact_evidence_state"),
        place_match_state=report_meta.get("place_match_state"),
        content_published_at=report_meta.get("content_published_at"),
        claimed_event_at=report_meta.get("claimed_event_at"),
        observed_context=row.trigger_context,
        staff_actor_role=_enum_text(row.actor_role),
        staff_action=_enum_text(row.response_action),
        staff_awareness_state=_enum_text(row.staff_awareness_state),
        staff_outcome=row.response_outcome,
        staff_policy_statement_verbatim=row.policy_statement_verbatim,
        source_id=row.source_id,
        evidence_bundle_id=row.evidence_bundle_id,
        evidence_material_type=evidence_meta.get("material_type"),
        evidence_source_platform=evidence_meta.get("source_platform"),
        evidence_publisher_type=evidence_meta.get("publisher_type"),
        evidence_class=evidence_meta.get("evidence_class"),
        evidence_display_allowed=evidence_meta.get("display_allowed"),
        submitted_at=report_meta.get("submitted_at"),
        confirmation_count=confirmation_count,
        dispute_open=dispute_open,
        verification_status=_enum_text(row.verification_status) or "unverified",
        freshness_state=_enum_text(row.freshness_state),
        last_verified_at=row.last_verified_at,
    )


def _facility_event(
    row: AnimalFacility,
    report_meta: _EventReportMeta | None = None,
    *,
    confirmation_count: int = 0,
    dispute_open: bool = False,
) -> RealityEventOut:
    report_meta = report_meta or {}
    evidence_meta = evidence_meta or {}
    event_at = row.observed_at or row.last_verified_at or row.created_at
    basis = "observed" if row.observed_at else "verified" if row.last_verified_at else "recorded"
    return RealityEventOut(
        id=row.id,
        event_type="animal_facility",
        place_id=row.place_id,
        zone_id=row.zone_id,
        event_at=event_at,
        time_basis=basis,
        time_evidence_state=report_meta.get("time_evidence_state"),
        origin=report_meta.get("origin"),
        fact_evidence_state=report_meta.get("fact_evidence_state"),
        place_match_state=report_meta.get("place_match_state"),
        content_published_at=report_meta.get("content_published_at"),
        claimed_event_at=report_meta.get("claimed_event_at"),
        facility_type=_enum_text(row.facility_type),
        facility_state=_enum_text(row.operational_state),
        facility_purpose_state=_enum_text(row.purpose_state),
        facility_access_mode=_enum_text(row.access_mode),
        facility_capacity=row.capacity,
        facility_size_limit=row.size_limit,
        facility_weather_protection=row.weather_protection,
        facility_shade=row.shade,
        facility_ventilation=row.ventilation,
        facility_water_available=row.water_available,
        facility_supervision_state=row.supervision_state,
        facility_security_or_lock_state=row.security_or_lock_state,
        facility_operator_provided=row.operator_provided,
        source_id=row.source_id,
        evidence_bundle_id=row.evidence_bundle_id,
        evidence_material_type=evidence_meta.get("material_type"),
        evidence_source_platform=evidence_meta.get("source_platform"),
        evidence_publisher_type=evidence_meta.get("publisher_type"),
        evidence_class=evidence_meta.get("evidence_class"),
        evidence_display_allowed=evidence_meta.get("display_allowed"),
        submitted_at=report_meta.get("submitted_at"),
        confirmation_count=confirmation_count,
        dispute_open=dispute_open,
        verification_status=_enum_text(row.verification_status) or "unverified",
        freshness_state=_enum_text(row.freshness_state),
        last_verified_at=row.last_verified_at,
    )


@router.get("/places/{place_id}/reality/events", response_model=list[RealityEventOut])
def consumer_reality_events(
    place_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[RealityEventOut]:
    """Published human-verified Reality facts as one consumer timeline."""
    if db.get(Place, place_id) is None:
        raise NotFound("场所不存在")
    presence = db.scalars(
        select(ObservedPresence)
        .where(
            ObservedPresence.place_id == place_id,
            ObservedPresence.verification_status.in_(VERIFIED_STATUS_VALUES),
        )
        .order_by(ObservedPresence.observed_at.desc())
        .limit(limit)
    ).all()
    staff = db.scalars(
        select(StaffResponseObservation)
        .where(
            StaffResponseObservation.place_id == place_id,
            StaffResponseObservation.verification_status.in_(VERIFIED_STATUS_VALUES),
        )
        .order_by(StaffResponseObservation.observed_at.desc())
        .limit(limit)
    ).all()
    facilities = db.scalars(
        select(AnimalFacility)
        .where(
            AnimalFacility.place_id == place_id,
            AnimalFacility.verification_status.in_(VERIFIED_STATUS_VALUES),
        )
        .order_by(AnimalFacility.created_at.desc())
        .limit(limit)
    ).all()
    candidate_ids = {
        row.candidate_id
        for row in [*presence, *staff, *facilities]
        if row.candidate_id
    }

    evidence_bundle_ids = {
        row.evidence_bundle_id
        for row in [*presence, *staff, *facilities]
        if row.evidence_bundle_id
    }
    evidence_meta_by_bundle: dict[str, _EventEvidenceMeta] = {}
    if evidence_bundle_ids:
        evidence_rows = db.execute(
            select(
                EvidenceBundle.id,
                SourceArtifact.artifact_type,
                EvidenceBundle.source_platform,
                EvidenceBundle.publisher_type,
                EvidenceBundle.evidence_class,
                SourceArtifact.display_allowed,
            )
            .join(SourceArtifact, SourceArtifact.id == EvidenceBundle.artifact_id)
            .where(EvidenceBundle.id.in_(evidence_bundle_ids))
        ).all()
        evidence_meta_by_bundle = {
            bundle_id: {
                "material_type": material_type,
                "source_platform": source_platform,
                "publisher_type": publisher_type,
                "evidence_class": evidence_class,
                "display_allowed": bool(display_allowed),
            }
            for (
                bundle_id,
                material_type,
                source_platform,
                publisher_type,
                evidence_class,
                display_allowed,
            ) in evidence_rows
        }
    report_meta_by_candidate: dict[str, _EventReportMeta] = {}
    if candidate_ids:
        report_rows = db.execute(
            select(
                RealityCandidate.id,
                RealityReport.submitted_at,
                RealityReport.time_evidence_state,
                RealityReport.origin,
                RealityReport.fact_evidence_state,
                RealityReport.place_match_state,
                RealityReport.content_published_at,
                RealityReport.claimed_event_at,
            )
            .outerjoin(RealityReport, RealityReport.id == RealityCandidate.report_id)
            .where(RealityCandidate.id.in_(candidate_ids))
        ).all()
        report_meta_by_candidate = {
            candidate_id: {
                "submitted_at": submitted_at,
                "time_evidence_state": time_evidence_state,
                "origin": origin,
                "fact_evidence_state": fact_evidence_state,
                "place_match_state": place_match_state,
                "content_published_at": content_published_at,
                "claimed_event_at": claimed_event_at,
            }
            for (
                candidate_id,
                submitted_at,
                time_evidence_state,
                origin,
                fact_evidence_state,
                place_match_state,
                content_published_at,
                claimed_event_at,
            ) in report_rows
        }

    reality_targets = {
        *(("observed_presence", row.id) for row in presence),
        *(("staff_response_observation", row.id) for row in staff),
        *(("animal_facility", row.id) for row in facilities),
    }

    confirmation_counts: dict[str, int] = {}
    if reality_targets:
        target_ids = {target_id for _, target_id in reality_targets}
        direct_rows = db.execute(
            select(RealityConfirmation.target_claim_id, func.count())
            .where(
                RealityConfirmation.place_id == place_id,
                RealityConfirmation.target_claim_id.in_(target_ids),
            )
            .group_by(RealityConfirmation.target_claim_id)
        ).all()
        for target_id, count in direct_rows:
            if target_id:
                confirmation_counts[target_id] = confirmation_counts.get(target_id, 0) + int(count)

        # Confirmations may be submitted before/without the caller knowing the
        # published claim id and therefore target the reviewed candidate. Map
        # those confirmations back to the published claim so the consumer
        # evidence rail counts both valid linkage forms.
        claim_id_by_candidate = {
            row.candidate_id: row.id
            for row in [*presence, *staff, *facilities]
            if row.candidate_id
        }
        candidate_confirmation_rows = db.execute(
            select(RealityConfirmation.target_candidate_id, func.count())
            .where(
                RealityConfirmation.place_id == place_id,
                RealityConfirmation.target_candidate_id.in_(candidate_ids),
            )
            .group_by(RealityConfirmation.target_candidate_id)
        ).all()
        for candidate_id, count in candidate_confirmation_rows:
            claim_id = claim_id_by_candidate.get(candidate_id)
            if claim_id:
                confirmation_counts[claim_id] = confirmation_counts.get(claim_id, 0) + int(count)
    open_disputes: set[tuple[str, str]] = set()
    if reality_targets:
        target_ids = {target_id for _, target_id in reality_targets}
        dispute_rows = db.execute(
            select(DisputeCase.target_type, DisputeCase.target_id).where(
                DisputeCase.target_id.in_(target_ids),
                DisputeCase.target_type.in_(
                    [
                        DisputeTargetType.OBSERVED_PRESENCE.value,
                        DisputeTargetType.STAFF_RESPONSE_OBSERVATION.value,
                        DisputeTargetType.ANIMAL_FACILITY.value,
                    ]
                ),
                DisputeCase.status.notin_(
                    [DisputeCaseStatus.RESOLVED.value, DisputeCaseStatus.WITHDRAWN.value]
                ),
            )
        ).all()
        open_disputes = {(str(target_type), target_id) for target_type, target_id in dispute_rows}

    events = [
        *[
            _presence_event(
                row,
                report_meta_by_candidate.get(row.candidate_id),
                evidence_meta_by_bundle.get(row.evidence_bundle_id or ""),
                confirmation_count=confirmation_counts.get(row.id, 0),
                dispute_open=("observed_presence", row.id) in open_disputes,
            )
            for row in presence
        ],
        *[
            _staff_event(
                row,
                report_meta_by_candidate.get(row.candidate_id),
                confirmation_count=confirmation_counts.get(row.id, 0),
                dispute_open=("staff_response_observation", row.id) in open_disputes,
            )
            for row in staff
        ],
        *[
            _facility_event(
                row,
                report_meta_by_candidate.get(row.candidate_id),
                confirmation_count=confirmation_counts.get(row.id, 0),
                dispute_open=("animal_facility", row.id) in open_disputes,
            )
            for row in facilities
        ],
    ]
    return sorted(events, key=lambda item: item.event_at, reverse=True)[:limit]


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
        cand.freshness_state = freshness_state(cand.observed_at)
    db.add(cand)
    db.flush()
    from app.services.reality_contribution import materialize_legacy_candidate_evidence

    evidence_bundle = materialize_legacy_candidate_evidence(db, cand)
    cand.evidence_bundle_id = evidence_bundle.id
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
        cand.freshness_state = freshness_state(cand.observed_at)
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


def _candidate_event_anchor(
    db: Session, cand: RealityCandidate
) -> tuple[datetime | None, bool]:
    """Return a display anchor and whether it is a real event-time anchor.

    Publication-only external content may use content_published_at to place a
    record on the timeline, but that timestamp must never feed Reality
    freshness or "recent现场" aggregation.
    """
    if cand.observed_at is not None:
        return cand.observed_at, True
    if not cand.report_id:
        return None, False
    report = db.get(RealityReport, cand.report_id)
    if (
        report is not None
        and report.time_evidence_state == "publication_time_only"
        and report.content_published_at is not None
    ):
        return report.content_published_at, False
    return None, False


def _publish_claim(db: Session, cand: RealityCandidate):
    """Project a VERIFIED candidate into its published claim table (v0.9 §7.4).

    Consumer-visible reality claims must carry Evidence + Review + Freshness.
    The claim copies the source/evidence linkage and verification posture from
    the candidate; it never asserts anything the candidate review did not.

    Report-backed candidates may publish only when the report matches an exact
    place/subplace. AREA_ONLY / PARENT_PLACE_ONLY / UNRESOLVED / CONFLICTED are
    valuable review leads, but the current public claim schema cannot express
    that spatial uncertainty without falsely pinning the fact to one Place.
    """
    if cand.report_id:
        report = db.get(RealityReport, cand.report_id)
        if report is not None and report.place_match_state not in {
            "exact_place",
            "exact_subplace",
        }:
            raise ApiError(
                "地点尚未精确匹配到具体场所，不能发布为场所现场事实",
                code="reality_exact_place_required",
            )
    if not cand.evidence_bundle_id:
        raise ApiError(
            "现场候选缺少可追溯证据包，不能发布",
            code="reality_evidence_required",
        )

    payload = cand.payload or {}
    event_anchor, event_time_known = _candidate_event_anchor(db, cand)
    if cand.candidate_type in {"observed_presence", "staff_response"} and event_anchor is None:
        raise ApiError(
            "缺少可展示的事件时间或内容发布时间，不能发布现场事实",
            code="reality_time_required",
        )
    status = (
        RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE
        if cand.decision_note
        else RealityVerificationStatus.HUMAN_VERIFIED
    )
    captured_at = cand.captured_at or event_anchor
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
            observed_at=event_anchor,
            captured_at=captured_at,
            source_id=cand.source_id,
            evidence_bundle_id=cand.evidence_bundle_id,
            verification_status=status,
            freshness_state=freshness_state(event_anchor) if event_time_known else None,
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
            staff_awareness_state=payload.get("staff_awareness_state", "awareness_unknown"),
            response_outcome=payload.get("response_outcome"),
            policy_statement_verbatim=payload.get("policy_statement_verbatim"),
            observed_at=event_anchor,
            captured_at=captured_at,
            source_id=cand.source_id,
            evidence_bundle_id=cand.evidence_bundle_id,
            verification_status=status,
            freshness_state=freshness_state(event_anchor) if event_time_known else None,
            last_verified_at=cand.decided_at,
        )
    elif cand.candidate_type == "animal_facility":
        claim = AnimalFacility(
            candidate_id=cand.id,
            place_id=cand.place_id,
            zone_id=cand.zone_id,
            facility_type=payload.get("facility_type"),
            purpose_state=payload.get("purpose_state", "purpose_unknown"),
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
            observed_at=event_anchor,
            last_verified_at=cand.decided_at,
            source_id=cand.source_id,
            evidence_bundle_id=cand.evidence_bundle_id,
            verification_status=status,
            freshness_state=freshness_state(event_anchor) if event_time_known else None,
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

    reality_evidence_count, reality_source_count, reality_verification = (
        _reality_evidence_stats(db, place_id)
    )
    snapshot = build_coexistence_snapshot(
        place_id=place_id,
        rule_answer=rule_answer,
        reality_answer=reality_answer,
        staff_response_summary=reality_answer.get("staff_response_summary", []),
        facility_summary=reality_answer.get("facility_summary", []),
        reality_evidence_count=reality_evidence_count,
        reality_distinct_source_count=reality_source_count,
        reality_verification_state=reality_verification,
        now=now,
    )
    return to_plain(snapshot)


VERIFIED_REALITY_STATUSES = (
    RealityVerificationStatus.HUMAN_VERIFIED.value,
    RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE.value,
)


def _presence_summary(db: Session, place_id: str, now: datetime):
    """Summarize verified presence and preserve names + spatial zone facets."""
    claims = db.execute(
        select(ObservedPresence, Zone.name, Zone.zone_type, Zone.indoor_outdoor)
        .outerjoin(Zone, Zone.id == ObservedPresence.zone_id)
        .outerjoin(RealityCandidate, RealityCandidate.id == ObservedPresence.candidate_id)
        .outerjoin(RealityReport, RealityReport.id == RealityCandidate.report_id)
        .where(
            ObservedPresence.place_id == place_id,
            ObservedPresence.verification_status.in_(VERIFIED_REALITY_STATUSES),
            or_(
                RealityReport.id.is_(None),
                RealityReport.time_evidence_state != "publication_time_only",
            ),
        )
        .order_by(ObservedPresence.observed_at.asc())
    ).all()

    claim_ids = {claim.id for claim, _, _, _ in claims}
    disputed_ids: set[str] = set()
    if claim_ids:
        disputed_ids = set(
            db.scalars(
                select(DisputeCase.target_id).where(
                    DisputeCase.target_type == DisputeTargetType.OBSERVED_PRESENCE.value,
                    DisputeCase.target_id.in_(claim_ids),
                    DisputeCase.status.notin_(
                        [DisputeCaseStatus.RESOLVED.value, DisputeCaseStatus.WITHDRAWN.value]
                    ),
                )
            )
        )

    def enum_text(value: object | None) -> str | None:
        if value is None:
            return None
        return str(getattr(value, "value", value))

    summary = summarize(
        [
            _Row(
                observed_at=claim.observed_at,
                source_id=claim.source_id
                or (f"evidence:{claim.evidence_bundle_id}" if claim.evidence_bundle_id else None),
                evidence_id=claim.evidence_bundle_id,
                zone_name=zone_name,
                action=claim.observed_action if claim.observed_action else None,
                disputed=claim.id in disputed_ids,
                human_verified=True,
            )
            for claim, zone_name, _, _ in claims
        ],
        now=now,
    )
    zone_facts = [
        {
            "name": zone_name,
            "zone_type": enum_text(zone_type),
            "indoor_outdoor": enum_text(spatial),
        }
        for _, zone_name, zone_type, spatial in claims
        if zone_name
    ]
    # Preserve one row per semantic zone tuple; multiple observations in the
    # same zone must not turn the consumer lens into a frequency score.
    zone_facts = list(
        {
            (item["name"], item["zone_type"], item["indoor_outdoor"]): item
            for item in zone_facts
        }.values()
    )
    zone_types = sorted(
        {value for _, _, zone_type, _ in claims if (value := enum_text(zone_type)) is not None}
    )
    indoor_outdoor = sorted(
        {
            value
            for _, _, _, spatial in claims
            if (value := enum_text(spatial)) is not None
        }
    )
    return summary, zone_facts, zone_types, indoor_outdoor


def _staff_response_summary(
    db: Session, place_id: str, now: datetime | None = None
) -> list[dict]:
    """Summarize recent staff handling and keep open disputes visible."""
    cutoff = (now or datetime.now(UTC)) - timedelta(days=30)
    rows = db.execute(
        select(
            StaffResponseObservation.response_action,
            StaffResponseObservation.staff_awareness_state,
            func.count(func.distinct(StaffResponseObservation.id)),
            func.count(func.distinct(DisputeCase.target_id)),
        )
        .outerjoin(
            RealityCandidate,
            RealityCandidate.id == StaffResponseObservation.candidate_id,
        )
        .outerjoin(RealityReport, RealityReport.id == RealityCandidate.report_id)
        .outerjoin(
            DisputeCase,
            and_(
                DisputeCase.target_id == StaffResponseObservation.id,
                DisputeCase.target_type == DisputeTargetType.STAFF_RESPONSE_OBSERVATION.value,
                DisputeCase.status.notin_(
                    [DisputeCaseStatus.RESOLVED.value, DisputeCaseStatus.WITHDRAWN.value]
                ),
            ),
        )
        .where(
            StaffResponseObservation.place_id == place_id,
            StaffResponseObservation.verification_status.in_(VERIFIED_REALITY_STATUSES),
            StaffResponseObservation.observed_at >= cutoff,
            or_(
                RealityReport.id.is_(None),
                RealityReport.time_evidence_state != "publication_time_only",
            ),
        )
        .group_by(
            StaffResponseObservation.response_action,
            StaffResponseObservation.staff_awareness_state,
        )
    ).all()
    return [
        {
            "response_action": action,
            "staff_awareness_state": awareness,
            "count": count,
            "disputed_count": disputed_count,
        }
        for action, awareness, count, disputed_count in sorted(
            rows,
            key=lambda item: (str(item[0]), str(item[1])),
        )
        if action
    ]


def _facility_summary(db: Session, place_id: str) -> list[dict]:
    """Current facility summary excludes publication-only facts and exposes disputes."""
    rows = db.execute(
        select(
            AnimalFacility.facility_type,
            AnimalFacility.purpose_state,
            AnimalFacility.zone_id,
            Zone.name,
            AnimalFacility.operational_state,
            func.count(func.distinct(AnimalFacility.id)),
            func.count(func.distinct(DisputeCase.target_id)),
            func.max(AnimalFacility.last_verified_at),
        )
        .outerjoin(Zone, Zone.id == AnimalFacility.zone_id)
        .outerjoin(RealityCandidate, RealityCandidate.id == AnimalFacility.candidate_id)
        .outerjoin(RealityReport, RealityReport.id == RealityCandidate.report_id)
        .outerjoin(
            DisputeCase,
            and_(
                DisputeCase.target_id == AnimalFacility.id,
                DisputeCase.target_type == DisputeTargetType.ANIMAL_FACILITY.value,
                DisputeCase.status.notin_(
                    [DisputeCaseStatus.RESOLVED.value, DisputeCaseStatus.WITHDRAWN.value]
                ),
            ),
        )
        .where(
            AnimalFacility.place_id == place_id,
            AnimalFacility.verification_status.in_(VERIFIED_REALITY_STATUSES),
            AnimalFacility.operational_state != "removed",
            or_(
                RealityReport.id.is_(None),
                RealityReport.time_evidence_state != "publication_time_only",
            ),
        )
        .group_by(
            AnimalFacility.facility_type,
            AnimalFacility.purpose_state,
            AnimalFacility.zone_id,
            Zone.name,
            AnimalFacility.operational_state,
        )
    ).all()
    return [
        {
            "facility_type": facility_type,
            "purpose_state": purpose_state,
            "zone_id": zone_id,
            "zone_name": zone_name,
            "count": count,
            "disputed_count": disputed_count,
            "operational_state": state,
            "last_verified_at": last_verified_at,
        }
        for (
            facility_type,
            purpose_state,
            zone_id,
            zone_name,
            state,
            count,
            disputed_count,
            last_verified_at,
        ) in rows
    ]


def _reality_evidence_stats(db: Session, place_id: str) -> tuple[int, int, str | None]:
    """Count distinct published Reality evidence/source anchors across all fact types."""
    rows = union_all(
        select(ObservedPresence.source_id, ObservedPresence.evidence_bundle_id).where(
            ObservedPresence.place_id == place_id,
            ObservedPresence.verification_status.in_(VERIFIED_REALITY_STATUSES),
        ),
        select(
            StaffResponseObservation.source_id,
            StaffResponseObservation.evidence_bundle_id,
        ).where(
            StaffResponseObservation.place_id == place_id,
            StaffResponseObservation.verification_status.in_(VERIFIED_REALITY_STATUSES),
        ),
        select(AnimalFacility.source_id, AnimalFacility.evidence_bundle_id).where(
            AnimalFacility.place_id == place_id,
            AnimalFacility.verification_status.in_(VERIFIED_REALITY_STATUSES),
        ),
    ).subquery()
    values = db.execute(select(rows.c.source_id, rows.c.evidence_bundle_id)).all()
    evidence_ids = {evidence_id for _, evidence_id in values if evidence_id}
    source_anchors = {
        source_id or (f"evidence:{evidence_id}" if evidence_id else None)
        for source_id, evidence_id in values
    }
    source_anchors.discard(None)
    verification = "human_verified" if values else None
    return len(evidence_ids), len(source_anchors), verification


def _reality_answer_for_place(db: Session, place_id: str, now: datetime) -> dict:
    """Build the one consumer RealityAnswer used by GET and CoexistenceSnapshot."""
    summary, observed_zone_facts, observed_zone_types, observed_indoor_outdoor = (
        _presence_summary(db, place_id, now)
    )
    return {
        "state": summary.state,
        "last_seen_at": summary.last_seen_at,
        "evidence_count": summary.evidence_count,
        "distinct_source_count": summary.distinct_source_count,
        "observed_zones": list(summary.observed_zones),
        "observed_zone_facts": observed_zone_facts,
        "observed_zone_types": observed_zone_types,
        "observed_indoor_outdoor": observed_indoor_outdoor,
        "observed_actions": list(summary.observed_actions),
        "staff_response_summary": _staff_response_summary(db, place_id, now),
        "facility_summary": _facility_summary(db, place_id),
        "freshness_state": summary.freshness_state,
        "verification_state": summary.verification_state,
        "recent_count_7d": summary.recent_count_7d,
        "recent_count_30d": summary.recent_count_30d,
        "days_since_last_seen": summary.days_since_last_seen,
        "note": summary.note,
    }

