"""RealityReport parent-flow endpoints (Master Goal v0.2.0 §15–§27).

One ``POST /places/{place_id}/reality/reports`` call carries a single user
Contribution: a parent ``RealityReport`` plus zero-or-more typed candidates
(observed_presence / staff_response / animal_facility) plus optional
ObservationEffort / RealityConfirmation / ExternalContentReference — all
sharing origin, place match, time evidence, media, source, privacy and
reporter context.

Hard rules enforced here on top of the service layer:

- ``ON_SITE_PAST`` must supply an explicit ``observed_at`` — the submission
  time is never used as the event time (Master Goal §19).
- ``EXTERNAL_ONLINE_CONTENT`` keeps ``content_published_at`` / ``claimed_event_at``
  / ``observed_at`` separate; an external report without any time evidence is
  rejected so the UI cannot silently invent an event date (§20).
- ``PARENT_PLACE_ONLY`` matches must not attach candidates to a tenant place;
  the candidate stays at container/subject level (§21).
- A candidate always lands REVIEW_PENDING with ``verification_status``
  UNVERIFIED — one-shot proximity never auto-verifies (§18).
- A confirmation is evidence, never a deletion; an effort never becomes a
  NO_ANIMAL_PRESENCE claim (service layer).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError, NotFound
from app.core.idempotency import check_inflight, get_cached, store
from app.core.ratelimit import check_rate_limit
from app.core.security import get_optional_user
from app.db.session import get_db
from app.models import (
    AnimalFacility,
    ObservedPresence,
    Place,
    RealityReport,
    StaffResponseObservation,
    User,
)
from app.models.enums import (
    ObservationOrigin,
    PlaceMatchState,
    RealityCandidateType,
    RealityVerificationStatus,
)
from app.schemas.common import Page
from app.schemas.reality import RealityReportOut
from app.schemas.reality_reports import (
    RealityCandidateBrief,
    RealityCandidateDraft,
    RealityContributionIn,
    RealityContributionOut,
    RealityTraceOut,
    RealityTraceSection,
)
from app.services.reality_contribution import (
    attach_candidate,
    create_confirmation,
    create_external_content_ref,
    create_observation_effort,
    create_report,
)
from app.services.reality_summary import _Row, freshness_for, summarize

router = APIRouter(tags=["reality"])

VERIFIED = [
    RealityVerificationStatus.HUMAN_VERIFIED.value,
    RealityVerificationStatus.HUMAN_VERIFIED_WITH_NOTE.value,
]

# Consumer copy for the six RealitySummary states — never the raw enum.
REALITY_STATE_LABELS: dict[str, str] = {
    "OBSERVED_RECENTLY": "近期现场有动物出现",
    "OBSERVED_HISTORICALLY": "仅有历史记录，未呈现为近期",
    "MULTI_EVIDENCE_OBSERVED": "多来源证实近期现场有动物",
    "NO_RECENT_RECORD": "暂无近期现场记录（≠ 没有动物）",
    "INSUFFICIENT_OBSERVATION": "现场记录不足或未完成人工核验",
    "DISPUTED": "现场记录存在争议",
}


def _freshness_label(observed_at: datetime | None) -> str:
    if observed_at is None:
        return "时间未知"
    return freshness_for(observed_at)


def _validate_report_times(body: RealityContributionIn) -> None:
    """Enforce origin-specific time rules before any row is written."""
    origin = body.report.origin
    if origin == ObservationOrigin.ON_SITE_PAST and body.report.observed_at is None:
        raise ApiError(
            "请选择你到场观察到的时间（提交时间不会自动成为事件时间）",
            code="on_site_past_time_required",
            status_code=422,
        )
    if origin == ObservationOrigin.EXTERNAL_ONLINE_CONTENT:
        has_any_time = any(
            (
                body.report.content_published_at is not None,
                body.report.claimed_event_at is not None,
                body.report.observed_at is not None,
            )
        )
        if not has_any_time:
            raise ApiError(
                "外部内容必须提供发布时间或事件时间（不得将提交时间当作事件时间）",
                code="external_time_required",
                status_code=422,
            )


def _candidate_place(
    body: RealityContributionIn, path_place_id: str, candidate: RealityCandidateDraft
) -> str:
    """Resolve the candidate's place, refusing place-match escalation.

    A PARENT_PLACE_ONLY report (e.g. mall-level) must never surface a
    candidate pinned to a tenant the reporter did not actually match.
    """
    report = body.report
    report_place = report.place_id or path_place_id
    if report.place_match_state == PlaceMatchState.PARENT_PLACE_ONLY:
        allowed = {report_place, report.container_place_id, report.subject_place_id}
        allowed.discard(None)
        if candidate.place_id not in allowed:
            raise ApiError(
                "仅匹配到上级场所（如商场）时，不能把记录挂在具体店铺上",
                code="parent_place_escalation",
                status_code=422,
            )
        return str(candidate.place_id or report.container_place_id or report_place)
    return str(candidate.place_id or report.subject_place_id or report_place)


@router.post(
    "/places/{place_id}/reality/reports",
    response_model=RealityContributionOut,
    status_code=201,
    tags=["consumer"],
)
def create_reality_report(
    place_id: str,
    body: RealityContributionIn,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> RealityContributionOut:
    """Create one parent-flow Contribution (report + candidates + optional extras)."""
    if db.get(Place, place_id) is None:
        raise NotFound("场所不存在")

    settings = get_settings()
    rate_key = user.id if user else f"anon:{request.client.host if request.client else 'unknown'}"
    check_rate_limit(
        "reality_reports",
        rate_key,
        settings.contribution_rate_max,
        settings.contribution_rate_window_seconds,
    )

    idem_key = request.headers.get("Idempotency-Key", "")
    if idem_key:
        cached = get_cached("reality_report", idem_key)
        if cached is not None:
            return RealityContributionOut.model_validate(cached)
        check_inflight("reality_report", idem_key)

    _validate_report_times(body)

    body.report.place_id = body.report.place_id or place_id
    report, flags = create_report(db, user, body.report, request=request)
    if user is None:
        # Privacy by design: one token per report, returned exactly once.
        report.anonymous_token = uuid.uuid4().hex
        db.flush()

    briefs: list[RealityCandidateBrief] = []
    for candidate in body.candidates:
        cand_place = _candidate_place(body, place_id, candidate)
        cand = attach_candidate(
            db,
            report=report,
            user=user,
            candidate_type=RealityCandidateType(candidate.candidate_type),
            place_id=cand_place,
            payload=candidate.payload or {},
            zone_id=candidate.zone_id,
            observed_at=candidate.observed_at or body.report.observed_at,
            request=request,
        )
        briefs.append(
            RealityCandidateBrief.model_validate(
                {
                    "id": cand.id,
                    "candidate_type": cand.candidate_type,
                    "place_id": cand.place_id,
                    "zone_id": cand.zone_id,
                    "animal_scope": cand.animal_scope,
                    "observed_at": cand.observed_at,
                    "review_status": cand.review_status,
                    "verification_status": cand.verification_status,
                }
            )
        )

    effort_id = None
    if body.effort is not None:
        effort = create_observation_effort(db, user, body.effort, request=request)
        effort_id = effort.id
    confirmation_id = None
    if body.confirmation is not None:
        confirmation = create_confirmation(db, user, body.confirmation, request=request)
        confirmation_id = confirmation.id

    external_id = None
    if body.external_content is not None:
        ref = create_external_content_ref(
            db, user, str(report.id), body.external_content, request=request
        )
        external_id = ref.id

    db.commit()
    db.refresh(report)

    out = RealityContributionOut(
        report=RealityReportOut.model_validate(report),
        candidates=briefs,
        effort_id=effort_id,
        confirmation_id=confirmation_id,
        external_content_id=external_id,
        abuse_flags=[f.value if hasattr(f, "value") else str(f) for f in flags],
        moderation_state=report.moderation_state,
    )
    if idem_key:
        store("reality_report", idem_key, out.model_dump(mode="json"))
    return out


@router.get("/places/{place_id}/reality/reports", response_model=Page[RealityReportOut])
def list_reality_reports(
    place_id: str,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> Page[RealityReportOut]:
    """List reports for a place (consumer Reality Trace surface)."""
    if db.get(Place, place_id) is None:
        raise NotFound("场所不存在")
    stmt = (
        select(RealityReport)
        .where(RealityReport.place_id == place_id)
        .order_by(RealityReport.created_at.desc())
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    return Page(
        items=[RealityReportOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/places/{place_id}/reality/trace", response_model=RealityTraceOut)
def reality_trace(
    place_id: str,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> RealityTraceOut:
    """Reality Trace — the fact, and how the platform verified it (§14).

    Fact sections describe what was observed; review sections describe the
    verification posture. The user can always tell the fact from the
    platform's verification work.
    """
    now = datetime.now(UTC)

    claims = db.scalars(
        select(ObservedPresence)
        .where(
            ObservedPresence.place_id == place_id,
            ObservedPresence.verification_status.in_(VERIFIED),
        )
        .order_by(ObservedPresence.observed_at.asc())
    ).all()
    staff_rows = db.scalars(
        select(StaffResponseObservation)
        .where(
            StaffResponseObservation.place_id == place_id,
            StaffResponseObservation.verification_status.in_(VERIFIED),
        )
        .order_by(StaffResponseObservation.observed_at.asc())
    ).all()
    facility_rows = db.scalars(
        select(AnimalFacility)
        .where(
            AnimalFacility.place_id == place_id,
            AnimalFacility.verification_status.in_(VERIFIED),
        )
        .order_by(AnimalFacility.created_at.asc())
    ).all()

    rows = [
        _Row(
            observed_at=c.observed_at,
            source_id=c.source_id,
            evidence_id=c.evidence_bundle_id,
            zone_name=None,
            action=c.observed_action if c.observed_action else None,
            human_verified=True,
        )
        for c in claims
    ]
    summary = summarize(rows, now=now)

    fact_sections = [
        RealityTraceSection(
            label="现场摘要",
            value=REALITY_STATE_LABELS.get(summary.state, summary.state),
        ),
        RealityTraceSection(
            label="最近记录",
            value=f"{summary.recent_count_30d} 条（近30天）"
            if summary.recent_count_30d
            else "暂无近期记录",
            note="暂无记录不代表现场没有动物（NO_RECENT_RECORD ≠ NO_ANIMAL_PRESENCE）",
        ),
        RealityTraceSection(
            label="来源类型",
            value=_source_type_label(claims, staff_rows, facility_rows),
        ),
        RealityTraceSection(
            label="时间",
            value="、".join(_freshness_label(c.observed_at) for c in claims[:3]) or "暂无明确日期",
        ),
        RealityTraceSection(
            label="工作人员处理",
            value="、".join(sorted({str(s.response_action) for s in staff_rows}))
            or "暂无经核验的处理记录",
        ),
        RealityTraceSection(
            label="动物相关设施",
            value="、".join(sorted({str(f.facility_type) for f in facility_rows}))
            or "暂无经核验的设施记录",
        ),
    ]
    review_sections = [
        RealityTraceSection(
            label="核验",
            value="经人工核验" if claims else "信息待核验",
            note="平台核验只说明事实被确认，不改变“未观察到”的含义",
        ),
        RealityTraceSection(
            label="一手来源", value="是" if any(c.source_id for c in claims) else "待补充"
        ),
        RealityTraceSection(label="是否存在争议", value="无已登记争议"),
    ]
    return RealityTraceOut(
        place_id=place_id,
        summary=REALITY_STATE_LABELS.get(summary.state, summary.state),
        fact_sections=fact_sections,
        review_sections=review_sections,
        evidence_count=summary.evidence_count,
    )


def _source_type_label(
    claims: Sequence[ObservedPresence],
    staff_rows: Sequence[StaffResponseObservation],
    facility_rows: Sequence[AnimalFacility],
) -> str:
    """Label the observed source contexts (facts only, no raw URLs)."""
    parts: list[str] = []
    if claims:
        parts.append("现场亲历")
    if staff_rows:
        parts.append("现场亲历（工作人员）")
    if facility_rows:
        parts.append("现场亲历（设施）")
    return "、".join(parts) or "暂无已发布记录"
