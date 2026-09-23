"""RealityReport contribution + Anti-Abuse governance (addendum PHASE 3, 12-13).

A contribution flow in one place:

1. ``create_report``      — build the RealityReport parent (origin / place
   match / time evidence / fact evidence / media / source / privacy).
2. ``attach_candidates``  — one report may produce several RealityCandidates
   (observed_presence / staff_response / animal_facility), all REVIEW_PENDING,
   reality_decision untouched (AI never writes it).
3. Anti-abuse checks      — rate limit, duplicate/near-duplicate suppression
   (content_hash / media_hash), place mismatch, old-video, recycled content,
   media manipulation flag. Contributions earn credit only AFTER verification
   passes; no 避雷/反宠 leaderboards are ever built.
4. ObservationEffort     — animal_observed=false forms ONLY an effort row,
   never a NO_ANIMAL_PRESENCE claim.

Invariants pinned by tests: UNKNOWN != ALLOWED, Observation != Rule,
Publication Time != Event Time (content_published_at never becomes
observed_at), FIRST_HAND_NO_MEDIA stays review-pending (never auto-rejected).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_audit
from app.core.audit_events import AuditEvent
from app.models import (
    ExternalContentReference,
    ObservationEffort,
    RealityCandidate,
    RealityConfirmation,
    RealityReport,
    User,
)
from app.models.enums import (
    ContributionAbuseFlag,
    RealityCandidateType,
    RealityReportModerationState,
    RealityVerificationStatus,
)
from app.schemas.reality import (
    ExternalContentReferenceIn,
    ObservationEffortIn,
    RealityConfirmationIn,
    RealityReportIn,
)

#: A first-hand report without media stays REVIEW_PENDING; never auto-rejected.
NO_MEDIA_REVIEW_PENDING = True

#: Duplicate/near-duplicate suppression window (same content hash).
DEDUP_WINDOW_HOURS = 24

#: A report whose claimed event is older than this is flagged old-video.
OLD_VIDEO_MAX_AGE_DAYS = 365


def normalize_http_url(url: str) -> str:
    """Normalise a source URL for dedup (strip fragments, lowercase scheme/host)."""
    try:
        from urllib.parse import urlsplit, urlunsplit

        parts = urlsplit(url.strip())
        netloc = parts.netloc.lower()
        # drop trailing slash on empty path for stability
        path = parts.path or "/"
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        return urlunsplit((parts.scheme.lower() or "https", netloc, path, parts.query, ""))
    except ValueError:
        return url.strip()


def content_fingerprint(source_url: str | None, content_hash: str | None) -> str | None:
    """Deterministic fingerprint for duplicate suppression.

    Priority: explicit content hash > URL hash. Media hash is compared
    separately (same media posted by two accounts).
    """
    if content_hash:
        return f"content:{content_hash}"
    if source_url:
        return f"url:{sha256(normalize_http_url(source_url).encode()).hexdigest()}"
    return None


def find_duplicate_report(
    db: Session, source_url: str | None, content_hash: str | None, media_hash: str | None
) -> RealityReport | None:
    """Return an existing report that looks like a duplicate of this one.

    Checks content fingerprint (URL or content hash) and media hash within the
    dedup window. Near-duplicate/recycled detection is a flag, not a delete:
    the new report still lands REVIEW_PENDING with the flag attached.
    """
    fp = content_fingerprint(source_url, content_hash)
    if fp is None:
        return None
    since = datetime.now(UTC) - timedelta(hours=DEDUP_WINDOW_HOURS)
    stmt = select(RealityReport).where(
        RealityReport.created_at >= since,
        RealityReport.moderation_state.in_(
            [
                RealityReportModerationState.PENDING.value,
                RealityReportModerationState.FLAGGED.value,
                RealityReportModerationState.APPROVED.value,
            ]
        ),
    )
    for report in db.scalars(stmt):
        if media_hash and report.media_hash == media_hash:
            return report
        rfp = content_fingerprint(report.source_url, report.content_hash)
        if rfp is not None and rfp == fp:
            return report
    return None


def check_place_match_consistency(report: RealityReportIn) -> ContributionAbuseFlag | None:
    """A report claiming an exact place must carry place-match evidence."""
    if (
        report.place_match_state.value in ("exact_place", "exact_subplace")
        and not report.place_match_evidence_types
    ):
        return ContributionAbuseFlag.PLACE_MISMATCH
    return None


def check_old_video(
    report: RealityReportIn, now: datetime | None = None
) -> ContributionAbuseFlag | None:
    """External content claiming an event older than the threshold is old-video."""
    now = now or datetime.now(UTC)
    if report.origin.value == "external_online_content":
        claimed = report.claimed_event_at or report.observed_at
        if claimed is not None and (now - claimed).days > OLD_VIDEO_MAX_AGE_DAYS:
            return ContributionAbuseFlag.OLD_VIDEO
    return None


def _collect_abuse_flags(
    db: Session, report: RealityReportIn, duplicate: RealityReport | None
) -> list[str]:
    flags: list[str] = []
    if duplicate is not None:
        flags.append(ContributionAbuseFlag.DUPLICATE.value)
        flags.append(ContributionAbuseFlag.NEAR_DUPLICATE.value)
    if report.media_hash and not report.content_hash and not report.source_url:
        # media with no source context is a common recycled-content pattern
        flags.append(ContributionAbuseFlag.RECYCLED_CONTENT.value)
    pm = check_place_match_consistency(report)
    if pm is not None:
        flags.append(pm.value)
    ov = check_old_video(report)
    if ov is not None:
        flags.append(ov.value)
    return flags


def create_report(
    db: Session,
    user: User | None,
    body: RealityReportIn,
    *,
    request=None,
) -> tuple[RealityReport, list[str]]:
    """Create the RealityReport parent and return it with abuse flags.

    ``reporter_id`` is set when a user is signed in; anonymous token flows are
    handled by the caller (token persisted separately, never the raw value).
    Media defaults to private (``privacy_state`` default in schema).
    """
    duplicate = find_duplicate_report(db, body.source_url, body.content_hash, body.media_hash)
    flags = _collect_abuse_flags(db, body, duplicate)

    report = RealityReport(
        reporter_id=user.id if user else None,
        origin=body.origin.value,
        place_id=body.place_id,
        container_place_id=body.container_place_id,
        subject_place_id=body.subject_place_id,
        place_match_state=body.place_match_state.value,
        place_match_evidence_types=(
            [t.value for t in body.place_match_evidence_types]
            if body.place_match_evidence_types
            else None
        ),
        time_evidence_state=body.time_evidence_state.value,
        content_published_at=body.content_published_at,
        claimed_event_at=body.claimed_event_at,
        observed_at=body.observed_at,
        time_certainty=body.time_certainty.value,
        fact_evidence_state=body.fact_evidence_state.value,
        privacy_state=body.privacy_state.value,
        media_refs=body.media_refs,
        source_url=body.source_url,
        source_platform=body.source_platform.value if body.source_platform else None,
        content_hash=body.content_hash,
        media_hash=body.media_hash,
        external_keyframe_ref=body.external_keyframe_ref,
        ocr_text=body.ocr_text,
        moderation_state=(
            RealityReportModerationState.FLAGGED.value
            if flags
            else RealityReportModerationState.PENDING.value
        ),
        abuse_flags=flags or None,
        submitted_at=datetime.now(UTC),
    )
    db.add(report)
    db.flush()
    record_audit(
        db,
        request=request,
        actor_user_id=user.id if user else None,
        actor_role=str(user.role) if user else "anonymous",
        action=AuditEvent.REALITY_REPORT_CREATE.value,
        target_type="reality_report",
        target_id=str(report.id),
        after_state={
            "origin": report.origin,
            "place_match_state": report.place_match_state,
            "time_evidence_state": report.time_evidence_state,
            "fact_evidence_state": report.fact_evidence_state,
            "moderation_state": report.moderation_state,
            "abuse_flags": flags,
        },
    )
    return report, flags


def attach_candidate(
    db: Session,
    report: RealityReport,
    user: User | None,
    *,
    candidate_type: RealityCandidateType,
    place_id: str,
    payload: dict[str, Any],
    zone_id: str | None = None,
    observed_at: datetime | None = None,
    request=None,
) -> RealityCandidate:
    """Attach one REVIEW_PENDING candidate to a report.

    The candidate copies the report's place/time evidence and always lands
    with ``reality_decision=None`` — AI never writes it. Verification stays
    UNVERIFIED until a human decides.
    """
    cand = RealityCandidate(
        report_id=str(report.id),
        candidate_type=candidate_type.value,
        place_id=place_id,
        zone_id=zone_id,
        animal_scope=payload.get("animal_scope"),
        observed_at=observed_at or report.observed_at,
        captured_at=observed_at or report.observed_at,
        payload=payload,
        review_status="REVIEW_PENDING",
        verification_status=RealityVerificationStatus.UNVERIFIED,
    )
    if cand.observed_at is not None:
        from app.api.v1.reality import _freshness_state

        cand.freshness_state = _freshness_state(cand.observed_at)
    db.add(cand)
    db.flush()
    record_audit(
        db,
        request=request,
        actor_user_id=user.id if user else None,
        actor_role=str(user.role) if user else "anonymous",
        action=AuditEvent.REALITY_CANDIDATE_CREATE.value,
        target_type="reality_candidate",
        target_id=str(cand.id),
        after_state={
            "report_id": str(report.id),
            "candidate_type": cand.candidate_type,
            "review_status": cand.review_status,
            "verification_status": cand.verification_status.value,
        },
    )
    return cand


def create_observation_effort(
    db: Session,
    user: User | None,
    body: ObservationEffortIn,
    *,
    request=None,
) -> ObservationEffort:
    """Record a no-animal-observed effort row.

    animal_observed=false creates ONLY an ObservationEffort; it never creates
    a RealityCandidate/claim and never implies NO_ANIMAL_PRESENCE.
    """
    effort = ObservationEffort(
        place_id=body.place_id,
        duration_bucket=body.duration_bucket.value,
        covered_zone_ids=body.covered_zone_ids,
        animal_observed=body.animal_observed,
        observed_at=body.observed_at,
        reporter_id=user.id if user else None,
        source_id=body.source_id,
    )
    db.add(effort)
    db.flush()
    record_audit(
        db,
        request=request,
        actor_user_id=user.id if user else None,
        actor_role=str(user.role) if user else "anonymous",
        action=AuditEvent.OBSERVATION_EFFORT_CREATE.value,
        target_type="observation_effort",
        target_id=str(effort.id),
        after_state={
            "place_id": effort.place_id,
            "animal_observed": effort.animal_observed,
            "duration_bucket": effort.duration_bucket,
        },
    )
    return effort


def create_confirmation(
    db: Session,
    user: User | None,
    body: RealityConfirmationIn,
    *,
    request=None,
) -> RealityConfirmation:
    """Add a confirmation row.

    A confirmation is evidence, never a deletion: NOT_SEEN_NOW never touches
    the older Observation (the row is simply appended; nothing is deleted).
    """
    conf = RealityConfirmation(
        confirmation_type=body.confirmation_type.value,
        place_id=body.place_id,
        target_claim_id=body.target_claim_id,
        target_candidate_id=body.target_candidate_id,
        observed_at=body.observed_at,
        reporter_id=user.id if user else None,
    )
    db.add(conf)
    db.flush()
    record_audit(
        db,
        request=request,
        actor_user_id=user.id if user else None,
        actor_role=str(user.role) if user else "anonymous",
        action=AuditEvent.REALITY_CONFIRMATION_CREATE.value,
        target_type="reality_confirmation",
        target_id=str(conf.id),
        after_state={
            "confirmation_type": conf.confirmation_type,
            "place_id": conf.place_id,
            "target_claim_id": conf.target_claim_id,
        },
    )
    return conf


def create_external_content_ref(
    db: Session,
    user: User | None,
    report_id: str | None,
    body: ExternalContentReferenceIn,
    *,
    request=None,
) -> ExternalContentReference:
    """Persist an external content reference with dedup metadata (addendum P8)."""
    ref = ExternalContentReference(
        report_id=report_id,
        source_url=body.source_url,
        platform=body.platform.value if body.platform else None,
        published_at=body.published_at,
        place_metadata=body.place_metadata,
        keyframe_ref=body.keyframe_ref,
        ocr_text=body.ocr_text,
        content_hash=body.content_hash,
        media_hash=body.media_hash,
    )
    db.add(ref)
    db.flush()
    record_audit(
        db,
        request=request,
        actor_user_id=user.id if user else None,
        actor_role=str(user.role) if user else "anonymous",
        action=AuditEvent.EXTERNAL_CONTENT_REF_CREATE.value,
        target_type="external_content_reference",
        target_id=str(ref.id),
        after_state={"report_id": report_id, "platform": ref.platform},
    )
    return ref
