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
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError, NotFound
from app.core.idempotency import check_inflight, get_cached, store
from app.core.ratelimit import check_rate_limit
from app.core.security import get_optional_user, require_role
from app.db.session import get_db
from app.models import (
    AnimalFacility,
    DisputeCase,
    ObservedPresence,
    Place,
    RealityCandidate,
    RealityReport,
    Source,
    StaffResponseObservation,
    User,
)
from app.models.enums import (
    DisputeCaseStatus,
    DisputeTargetType,
    ObservationOrigin,
    PlaceMatchState,
    RealityCandidateType,
    RealityVerificationStatus,
    UserRole,
)
from app.schemas.common import Page
from app.schemas.reality import RealityReportOut
from app.schemas.reality_reports import (
    ContributionActivityOut,
    RealityCandidateBrief,
    RealityCandidateDraft,
    RealityContributionIn,
    RealityContributionOut,
    RealityTraceOut,
    RealityTraceSection,
)
from app.services.contribution_activity import ContributionActivity, contribution_activity
from app.services.reality_contribution import (
    attach_candidate,
    create_confirmation,
    create_external_content_ref,
    create_observation_effort,
    create_report,
    materialize_report_evidence,
)
from app.services.reality_summary import freshness_for

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


FRESHNESS_LABELS: dict[str, str] = {
    "FRESH": "7 天内",
    "RECENT": "30 天内",
    "AGING": "30–90 天",
    "HISTORICAL": "历史记录",
    "EXPIRED_FOR_SUMMARY": "已超出近期摘要范围",
}

STAFF_RESPONSE_LABELS: dict[str, str] = {
    "proactive_accommodation": "主动提供便利",
    "provide_water": "提供饮水",
    "provide_container_or_stroller": "提供宠物箱或推车",
    "direct_to_allowed_zone": "引导到允许区域",
    "remind_leash": "提醒牵引",
    "require_carrier": "要求使用宠物箱或包",
    "request_relocation": "要求更换位置",
    "request_wait_outside": "要求在外等候",
    "deny_entry": "拒绝进入",
    "request_exit": "要求离开",
    "policy_explanation": "解释场所规则",
    "escalate_to_manager": "转交负责人处理",
    "no_intervention_observed": "未观察到处理",
    "unknown": "处理情况未知",
}

FACILITY_LABELS: dict[str, str] = {
    "outdoor_holding_cage": "户外安置笼",
    "kennel": "犬舍",
    "tether_point": "拴宠点",
    "pet_waiting_area": "携宠等候区",
    "pet_parking": "宠物暂放区",
    "water_bowl": "饮水碗",
    "pet_stroller": "宠物推车",
    "carrier_storage": "宠物箱寄存",
    "pet_entrance": "宠物入口",
    "pet_elevator": "宠物电梯",
    "dedicated_pet_zone": "独立携宠区",
    "waste_bag_station": "拾便袋站",
    "cleaning_station": "清洁站",
    "washing_point": "清洗点",
    "dedicated_pet_tableware": "专用宠物餐具",
    "other": "其他设施",
}

SOURCE_TYPE_LABELS: dict[str, str] = {
    "statute_or_regulation": "法规",
    "government_service": "政府服务",
    "official_operator_policy": "管理方发布",
    "onsite_signage": "现场标识",
    "certified_verifier": "认证核验方",
    "ordinary_user": "普通用户现场提交",
    "external_web_reference": "外部网页",
    "imported_dataset": "导入数据",
}


def _freshness_label(observed_at: datetime | None) -> str:
    if observed_at is None:
        return "时间未知"
    state = freshness_for(observed_at)
    return FRESHNESS_LABELS.get(state, "时间状态待确认")


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _staff_trace_label(row: StaffResponseObservation) -> str:
    action = _enum_value(row.response_action)
    awareness = _enum_value(row.staff_awareness_state)
    if action == "no_intervention_observed":
        if awareness == "awareness_confirmed":
            return "工作人员已注意到，本次未观察到进一步处理"
        return "本次记录未观察到工作人员处理"
    return STAFF_RESPONSE_LABELS.get(action, "工作人员处理情况待补充")


def _facility_trace_label(row: AnimalFacility) -> str:
    purpose = _enum_value(row.purpose_state)
    if purpose in {"purpose_user_inferred", "purpose_unknown"}:
        return "疑似动物相关设施，用途待核验"
    return FACILITY_LABELS.get(_enum_value(row.facility_type), "动物相关设施")


def _validate_report_times(body: RealityContributionIn) -> None:
    """Enforce origin-specific time and provenance order before any row is written."""
    origin = body.report.origin
    now = datetime.now(UTC)
    # Allow minor device clock drift; never admit observations or publications
    # that claim to have happened materially in the future.
    latest_permitted = now + timedelta(minutes=10)
    timestamps = {
        "observed_at": body.report.observed_at,
        "claimed_event_at": body.report.claimed_event_at,
        "content_published_at": body.report.content_published_at,
    }
    for candidate in body.candidates:
        if candidate.observed_at is not None:
            timestamps[f"candidate.{candidate.candidate_type}.observed_at"] = candidate.observed_at
    for raw_value in timestamps.values():
        if raw_value is None:
            continue
        recorded = raw_value if raw_value.tzinfo else raw_value.replace(tzinfo=UTC)
        if recorded > latest_permitted:
            raise ApiError(
                "事件、现场观察或内容发布时间不得晚于当前时间",
                code="reality_future_time_not_allowed",
                status_code=422,
            )
    published = body.report.content_published_at
    event = body.report.claimed_event_at
    if published is not None and event is not None:
        publication_time = published if published.tzinfo else published.replace(tzinfo=UTC)
        claimed_time = event if event.tzinfo else event.replace(tzinfo=UTC)
        if claimed_time > publication_time:
            raise ApiError(
                "来源声称的事件时间不能晚于该内容的发布时间",
                code="reality_event_after_publication",
                status_code=422,
            )
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
    """Resolve one candidate without upgrading place-match precision.

    RealityReport may legitimately exist with 0 candidates. AREA_ONLY /
    UNRESOLVED / CONFLICTED therefore stay report-level evidence until a
    reviewer resolves the place; they must never borrow the route's Place id.
    """

    report = body.report
    state = report.place_match_state

    if state in {
        PlaceMatchState.AREA_ONLY,
        PlaceMatchState.UNRESOLVED,
        PlaceMatchState.CONFLICTED,
    }:
        raise ApiError(
            "地点尚未精确匹配时只能提交线索报告，不能生成具体场所事实候选",
            code="reality_candidate_exact_place_required",
            status_code=422,
        )

    if state == PlaceMatchState.PARENT_PLACE_ONLY:
        target = report.container_place_id
        if not target:
            raise ApiError(
                "仅匹配到上级场所时必须明确上级场所",
                code="parent_place_required",
                status_code=422,
            )
        if candidate.place_id not in {None, target}:
            raise ApiError(
                "仅匹配到上级场所（如商场）时，不能把记录挂在具体店铺上",
                code="parent_place_escalation",
                status_code=422,
            )
        return target

    if state == PlaceMatchState.EXACT_SUBPLACE:
        target = report.subject_place_id
        if not target:
            raise ApiError(
                "精确子场所匹配必须明确具体子场所",
                code="exact_subplace_required",
                status_code=422,
            )
        if candidate.place_id not in {None, target}:
            raise ApiError(
                "候选地点与已确认的具体子场所不一致",
                code="exact_place_escalation",
                status_code=422,
            )
        return target

    # EXACT_PLACE: this endpoint is entered from one selected Place. An
    # arbitrary candidate.place_id must not escape that scoped context.
    target = report.subject_place_id or report.place_id or path_place_id
    if target != path_place_id or candidate.place_id not in {None, target}:
        raise ApiError(
            "候选地点与当前已确认场所不一致",
            code="exact_place_escalation",
            status_code=422,
        )
    return target


def _normalize_report_place(db: Session, path_place: Place, body: RealityContributionIn) -> None:
    """Bind a contribution to exactly the place precision its evidence supports."""
    place_id = path_place.id
    report = body.report
    state = report.place_match_state

    if state == PlaceMatchState.EXACT_PLACE:
        if report.place_id not in {None, place_id} or report.subject_place_id not in {
            None,
            place_id,
        }:
            raise ApiError(
                "精确地点与当前场所不一致",
                code="exact_place_escalation",
                status_code=422,
            )
        report.place_id = place_id
        report.subject_place_id = place_id
        return

    if state == PlaceMatchState.PARENT_PLACE_ONLY:
        if not report.container_place_id:
            raise ApiError(
                "仅匹配到上级场所时必须明确上级场所",
                code="parent_place_required",
                status_code=422,
            )
        container = db.get(Place, report.container_place_id)
        if container is None:
            raise NotFound("上级场所不存在")
        if path_place.parent_place_id != container.id:
            raise ApiError(
                "上级场所必须是当前场所已收录的直接父场所，不能用任意已存在场所提升地点匹配",
                code="parent_place_relationship_mismatch",
                status_code=422,
            )
        report.place_id = container.id
        report.container_place_id = container.id
        report.subject_place_id = None
        return

    if state == PlaceMatchState.EXACT_SUBPLACE:
        if not report.subject_place_id:
            raise ApiError(
                "精确子场所匹配必须明确具体子场所",
                code="exact_subplace_required",
                status_code=422,
            )
        subject = db.get(Place, report.subject_place_id)
        if subject is None:
            raise NotFound("具体子场所不存在")
        if subject.parent_place_id != place_id:
            raise ApiError(
                "具体子场所必须属于当前场所，不能跨场所提升地点匹配",
                code="exact_subplace_relationship_mismatch",
                status_code=422,
            )
        report.place_id = subject.id
        report.container_place_id = place_id
        report.subject_place_id = subject.id
        return

    if state in {
        PlaceMatchState.AREA_ONLY,
        PlaceMatchState.UNRESOLVED,
        PlaceMatchState.CONFLICTED,
    }:
        # The launch Place is UI context, not proof that external content depicts it.
        report.place_id = None
        report.subject_place_id = None


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
    place = db.get(Place, place_id)
    if place is None:
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

    _normalize_report_place(db, place, body)

    report, flags = create_report(db, user, body.report, request=request)
    if user is None:
        # Privacy by design: one token per report, returned exactly once.
        report.anonymous_token = uuid.uuid4().hex
        db.flush()

    evidence_bundle = materialize_report_evidence(db, report)

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
            evidence_bundle_id=evidence_bundle.id,
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
        effort = create_observation_effort(
            db,
            user,
            body.effort,
            report_id=str(report.id),
            evidence_bundle_id=evidence_bundle.id,
            request=request,
        )
        effort_id = effort.id
    confirmation_id = None
    if body.confirmation is not None:
        confirmation = create_confirmation(
            db,
            user,
            body.confirmation,
            report_id=str(report.id),
            evidence_bundle_id=evidence_bundle.id,
            request=request,
        )
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


@router.get(
    "/places/{place_id}/reality/reports",
    response_model=Page[RealityReportOut],
    tags=["admin:reality"],
)
def list_reality_reports(
    place_id: str,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_role(UserRole.MODERATOR)),
    db: Session = Depends(get_db),
) -> Page[RealityReportOut]:
    """Review-only report parent rows.

    RealityReport contains private provenance, media references and the
    one-time anonymous receipt token. Consumer surfaces must use published
    Reality events/claims instead; pending/private report parents are never
    exposed as a public trace.
    """
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

    from app.api.v1.reality import _presence_summary

    summary, _, _, _ = _presence_summary(db, place_id, now)
    published_rows: list[ObservedPresence | StaffResponseObservation | AnimalFacility] = [
        *claims,
        *staff_rows,
        *facility_rows,
    ]
    evidence_ids = {
        row.evidence_bundle_id for row in published_rows if getattr(row, "evidence_bundle_id", None)
    }
    candidate_ids = {
        row.candidate_id for row in published_rows if getattr(row, "candidate_id", None)
    }
    report_origins = (
        list(
            db.scalars(
                select(RealityReport.origin)
                .join(RealityCandidate, RealityCandidate.report_id == RealityReport.id)
                .where(RealityCandidate.id.in_(candidate_ids))
            )
        )
        if candidate_ids
        else []
    )
    source_ids = {row.source_id for row in published_rows if getattr(row, "source_id", None)}
    directness_values = (
        list(db.scalars(select(Source.directness).where(Source.id.in_(source_ids))))
        if source_ids
        else []
    )
    has_first_hand_source = any(
        _enum_value(origin)
        in {"on_site_now", "on_site_past", "operator_provided", "official_public_content"}
        for origin in report_origins
    ) or any(_enum_value(value) == "direct" for value in directness_values)

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
            note="暂无记录不代表现场没有动物。",
        ),
        RealityTraceSection(
            label="来源类型",
            value=_source_type_label(db, claims, staff_rows, facility_rows, report_origins),
        ),
        RealityTraceSection(
            label="时间",
            value="、".join(_freshness_label(c.observed_at) for c in claims[:3]) or "暂无明确日期",
        ),
        RealityTraceSection(
            label="工作人员处理",
            value="、".join(sorted({_staff_trace_label(row) for row in staff_rows}))
            or "暂无经核验的处理记录",
        ),
        RealityTraceSection(
            label="动物相关设施",
            value="、".join(sorted({_facility_trace_label(row) for row in facility_rows}))
            or "暂无经核验的设施记录",
        ),
    ]
    open_dispute_count = _open_reality_dispute_count(db, claims, staff_rows, facility_rows)
    review_sections = [
        RealityTraceSection(
            label="核验",
            value="经人工核验" if published_rows else "信息待核验",
            note="平台核验只说明事实被确认，不改变“未观察到”的含义",
        ),
        RealityTraceSection(label="一手来源", value="是" if has_first_hand_source else "待补充"),
        RealityTraceSection(
            label="争议 / 纠错",
            value=f"{open_dispute_count} 条处理中" if open_dispute_count else "暂无待处理异议",
            note="异议只触发复核，不会由提交者直接删除记录，也不会改写正式规则。",
        ),
    ]
    return RealityTraceOut(
        place_id=place_id,
        summary=REALITY_STATE_LABELS.get(summary.state, summary.state),
        fact_sections=fact_sections,
        review_sections=review_sections,
        evidence_count=len(evidence_ids),
    )


@router.get("/me/contribution-activity", response_model=list[ContributionActivityOut])
def my_contribution_activity(
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ContributionActivity]:
    """All of the caller's governed Consumer contribution lanes in one read model."""
    if not user:
        raise ApiError(
            "登录后才能查看贡献历史",
            code="auth_required",
            status_code=401,
        )
    return contribution_activity(db, user.id)


@router.get("/me/reality-contributions")
def my_reality_contributions(
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """The signed-in user's own reality reports + candidate statuses (M7 B1).

    Returns only the caller's own data (deny-by-default); candidates link to
    their report. Review/verification states are exposed as stable machine
    codes — the UI maps them through the shared dictionary.
    """
    if not user:
        raise ApiError(
            "登录后才能查看贡献历史",
            code="auth_required",
            status_code=401,
        )
    reports = db.scalars(
        select(RealityReport)
        .where(RealityReport.reporter_id == user.id)
        .order_by(RealityReport.created_at.desc())
        .limit(50)
    ).all()
    out: list[dict] = []
    for r in reports:
        candidates = db.scalars(
            select(RealityCandidate)
            .where(RealityCandidate.report_id == r.id)
            .order_by(RealityCandidate.created_at.asc())
        ).all()
        out.append(
            {
                "report_id": r.id,
                "place_id": r.place_id,
                "origin": str(r.origin),
                "moderation_state": r.moderation_state,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "candidates": [
                    {
                        "candidate_type": str(c.candidate_type),
                        "review_status": c.review_status,
                        "verification_status": str(c.verification_status),
                        "reality_decision": str(c.reality_decision) if c.reality_decision else None,
                        "observed_at": c.observed_at.isoformat() if c.observed_at else None,
                    }
                    for c in candidates
                ],
            }
        )
    return out


def _open_reality_dispute_count(
    db: Session,
    claims: Sequence[ObservedPresence],
    staff_rows: Sequence[StaffResponseObservation],
    facility_rows: Sequence[AnimalFacility],
) -> int:
    targets = {
        *(("observed_presence", row.id) for row in claims),
        *(("staff_response_observation", row.id) for row in staff_rows),
        *(("animal_facility", row.id) for row in facility_rows),
    }
    if not targets:
        return 0
    ids = {target_id for _, target_id in targets}
    rows = db.execute(
        select(DisputeCase.target_type, DisputeCase.target_id).where(
            DisputeCase.target_id.in_(ids),
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
    return len({(str(target_type), target_id) for target_type, target_id in rows})


def _source_type_label(
    db: Session,
    claims: Sequence[ObservedPresence],
    staff_rows: Sequence[StaffResponseObservation],
    facility_rows: Sequence[AnimalFacility],
    report_origins: Sequence[object] = (),
) -> str:
    """Describe explicit Source rows and RealityReport origins without guessing."""
    published_source_rows: list[ObservedPresence | StaffResponseObservation | AnimalFacility] = [
        *claims,
        *staff_rows,
        *facility_rows,
    ]
    source_ids = {row.source_id for row in published_source_rows if getattr(row, "source_id", None)}
    source_types = (
        db.scalars(select(Source.source_type).where(Source.id.in_(source_ids))).all()
        if source_ids
        else []
    )
    labels = {
        SOURCE_TYPE_LABELS.get(_enum_value(source_type), "其他来源") for source_type in source_types
    }
    origin_labels = {
        "on_site_now": "现场亲历",
        "on_site_past": "过往现场亲历",
        "external_online_content": "公开内容线索",
        "operator_provided": "场所方提供",
        "official_public_content": "官方公开内容",
    }
    labels.update(
        origin_labels[_enum_value(origin)]
        for origin in report_origins
        if _enum_value(origin) in origin_labels
    )
    if labels:
        return "、".join(sorted(labels))
    return "来源待补充" if (claims or staff_rows or facility_rows) else "暂无已发布记录"
