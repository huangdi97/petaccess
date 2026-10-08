"""Unified consumer contribution activity.

The Consumer contribution entry exposes multiple transaction types that land in
different governed domains by design: RealityReport, RuleCandidate and
VerificationEvent. This read model reunifies those lanes for "我的贡献" without
collapsing their semantics or turning one domain into another.
"""

from __future__ import annotations

from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AuditLog,
    Place,
    RealityCandidate,
    RealityReport,
    RuleCandidate,
    VerificationEvent,
)


class ContributionActivity(TypedDict):
    id: str
    kind: str
    place_id: str | None
    place_name: str | None
    created_at: str | None
    status: str
    summary: str


def _enum_text(value: object | None) -> str:
    return str(getattr(value, "value", value or ""))


def _review_status_label(value: object | None) -> str:
    labels = {
        "DISCOVERED": "已收到",
        "EXTRACTED": "整理中",
        "MATCH_PENDING": "等待地点匹配",
        "REVIEW_PENDING": "等待人工复核",
        "APPROVED": "已通过复核",
        "PUBLISHED": "已发布为正式规则",
        "REJECTED": "未采纳",
        "SUPERSEDED": "已被后续版本替代",
    }
    raw = _enum_text(value)
    return labels.get(raw, "处理中" if raw else "已提交")


def _place_names(db: Session, place_ids: set[str]) -> dict[str, str]:
    if not place_ids:
        return {}
    rows = db.execute(select(Place.id, Place.canonical_name).where(Place.id.in_(place_ids))).all()
    return {place_id: name for place_id, name in rows}


def _reality_rows(db: Session, user_id: str) -> list[ContributionActivity]:
    reports = db.scalars(
        select(RealityReport)
        .where(RealityReport.reporter_id == user_id)
        .order_by(RealityReport.created_at.desc())
        .limit(80)
    ).all()
    place_names = _place_names(db, {r.place_id for r in reports if r.place_id})
    out: list[ContributionActivity] = []
    for report in reports:
        candidates = db.scalars(
            select(RealityCandidate)
            .where(RealityCandidate.report_id == report.id)
            .order_by(RealityCandidate.created_at.asc())
        ).all()
        labels = {
            "observed_presence": "现场出现记录",
            "staff_response": "工作人员处理记录",
            "animal_facility": "动物设施记录",
        }
        summary = (
            "、".join(
                labels.get(_enum_text(candidate.candidate_type), "现场信息")
                for candidate in candidates
            )
            or "现场信息"
        )
        if any(candidate.review_status == "REVIEW_PENDING" for candidate in candidates):
            status = "等待人工核验"
        elif candidates:
            status = _review_status_label(candidates[0].review_status)
        else:
            status = "已提交"
        out.append(
            {
                "id": report.id,
                "kind": "reality",
                "place_id": report.place_id,
                "place_name": place_names.get(report.place_id or ""),
                "created_at": report.created_at.isoformat() if report.created_at else None,
                "status": status,
                "summary": summary,
            }
        )
    return out


def _verification_rows(db: Session, user_id: str) -> list[ContributionActivity]:
    rows = db.scalars(
        select(VerificationEvent)
        .where(VerificationEvent.user_id == user_id)
        .order_by(VerificationEvent.created_at.desc())
        .limit(80)
    ).all()
    place_names = _place_names(db, {row.place_id for row in rows})
    labels = {
        "place_correction": "场所信息纠错",
        "field_check": "规则现场确认",
        "signage_uploaded": "规则牌证据",
        "rule_confirmed": "规则现场确认",
        "rule_changed": "规则变化线索",
    }
    return [
        {
            "id": row.id,
            "kind": "verification",
            "place_id": row.place_id,
            "place_name": place_names.get(row.place_id),
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "status": "等待人工核验" if _enum_text(row.result) == "uncertain" else "已提交核验",
            "summary": labels.get(_enum_text(row.event_type), "核验线索"),
        }
        for row in rows
    ]


def _rule_lead_rows(db: Session, user_id: str) -> list[ContributionActivity]:
    audits = db.scalars(
        select(AuditLog)
        .where(
            AuditLog.actor_user_id == user_id,
            AuditLog.target_type == "rule_candidate",
        )
        .order_by(AuditLog.created_at.desc())
        .limit(80)
    ).all()
    audits = [row for row in audits if (row.after_state or {}).get("consumer_rule_lead") is True]
    candidate_ids = {row.target_id for row in audits}
    candidate_rows = db.scalars(
        select(RuleCandidate).where(RuleCandidate.id.in_(candidate_ids))
    ).all()
    candidates = {row.id: row for row in candidate_rows}
    place_ids = {candidate.place_id for candidate in candidates.values() if candidate.place_id}
    place_names = _place_names(db, place_ids)
    out: list[ContributionActivity] = []
    for audit in audits:
        candidate = candidates.get(audit.target_id)
        if candidate is None:
            continue
        changed = bool(candidate.supersedes_rule_id)
        out.append(
            {
                "id": candidate.id,
                "kind": "rule_lead",
                "place_id": candidate.place_id,
                "place_name": place_names.get(candidate.place_id or ""),
                "created_at": audit.created_at.isoformat() if audit.created_at else None,
                "status": _review_status_label(candidate.review_status),
                "summary": "规则变化线索" if changed else "新规则线索",
            }
        )
    return out


def contribution_activity(db: Session, user_id: str) -> list[ContributionActivity]:
    rows = [
        *_reality_rows(db, user_id),
        *_verification_rows(db, user_id),
        *_rule_lead_rows(db, user_id),
    ]

    return sorted(rows, key=lambda row: row["created_at"] or "", reverse=True)[:100]
