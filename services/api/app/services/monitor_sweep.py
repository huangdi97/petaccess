"""Due-monitor sweep (Wave 01 brief §28-§33, §79).

Why this module exists
----------------------
``SourceMonitor`` rows existed and ``/admin/monitors/{id}/check`` could sweep one
of them, but **nothing ever selected a monitor as due**: ``next_check_at`` was
only written *after* a sweep, and no scheduler read it. A monitor fleet that is
never swept is indistinguishable from no monitor fleet — it records intent, not
observation. This module is the missing selection step.

Shared by the admin endpoint and the Celery beat task so that "sweep what is
due" has exactly one implementation; two implementations would drift the moment
one of them learned about backoff.
"""

from __future__ import annotations

import hashlib

from sqlalchemy import func, or_, select

from app.models import RuleCandidate, SourceMonitor
from app.services.source_monitor import check_monitor


def _monitor_dedup_key(*, source_id: str, content_hash: str | None, place_id: str | None) -> str:
    """Deterministic key for "this exact source content was already ingested".

    Deliberately narrow: same source, same bytes, same place. Two different
    statements extracted from one changed page are different candidates and must
    stay different — dedup must never collapse real content (§79).
    """
    raw = f"monitor:{source_id}:{content_hash or ''}:{place_id or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def apply_monitor_change(db, monitor) -> dict:
    """Route a detected change into evidence + candidate (never a rule).

    Returns the ids so the caller can write a single audit row. A change that
    repeats content we already ingested is reported with ``duplicate=True`` and
    creates nothing — re-detecting the same bytes is not a new fact (§79).
    """
    from app.services.candidate_service import create_from_extraction
    from app.services.evidence_service import record_monitor_change

    sweep = check_monitor(monitor)
    candidate_id: str | None = None
    artifact_id: str | None = None
    bundle_id: str | None = None
    duplicate = False
    out: dict[str, object] = {"outcome": sweep.outcome}
    if sweep.outcome == "changed":
        dedup_key = _monitor_dedup_key(
            source_id=monitor.source_id,
            content_hash=monitor.content_hash,
            place_id=monitor.place_id,
        )
        existing = db.scalar(select(RuleCandidate).where(RuleCandidate.dedup_key == dedup_key))
        if existing is not None:
            # re-detecting the same bytes is not a new fact (§79)
            candidate_id, duplicate = existing.id, True
        else:
            recorded = record_monitor_change(
                db,
                monitor,
                fetch_result=sweep.fetch,
                previous_hash=sweep.previous_hash,
                expansion_run_id=monitor.expansion_run_id,
            )
            if recorded is not None:
                artifact, bundle = recorded
                artifact.expansion_run_id = monitor.expansion_run_id
                artifact_id, bundle_id = artifact.id, bundle.id
            cand = create_from_extraction(
                db,
                source_id=monitor.source_id,
                extraction_method="url_monitor",
                place_id=monitor.place_id,
                raw_text=monitor.last_excerpt or "source content changed",
                evidence_bundle_id=bundle_id,
                expansion_run_id=monitor.expansion_run_id,
                dedup_key=dedup_key,
            )
            candidate_id = cand.id
    out["candidate_id"] = candidate_id
    out["artifact_id"] = artifact_id
    out["evidence_bundle_id"] = bundle_id
    out["duplicate_change"] = duplicate
    return out


def sweep_due_monitors(db, *, limit: int = 50) -> dict:
    """Sweep every monitor whose ``next_check_at`` has come due.

    Selection rule: ``next_check_at IS NULL`` counts as due, because a freshly
    created monitor must capture its baseline hash before it can ever claim a
    change. Monitors in backoff carry a future ``next_check_at`` and are skipped
    naturally — that is what stops a 429 from being hammered (§33).

    A per-sweep ``limit`` keeps one run bounded: an unbounded sweep against a
    large fleet is how a monitor becomes the thing that takes the source down.
    """
    now = db.execute(select(func.now())).scalar_one()
    due = db.scalars(
        select(SourceMonitor)
        .where(
            SourceMonitor.status.in_(("active", "failing")),
            or_(SourceMonitor.next_check_at.is_(None), SourceMonitor.next_check_at <= now),
        )
        .order_by(SourceMonitor.next_check_at.asc().nullsfirst())
        .limit(limit)
    ).all()
    results = []
    for monitor in due:
        res = apply_monitor_change(db, monitor)
        res["monitor_id"] = monitor.id
        res["url"] = monitor.url[:120]
        res["failure_count"] = monitor.failure_count
        res["last_http_status"] = monitor.last_http_status
        res["content_hash"] = (monitor.content_hash or "")[:12]
        results.append(res)
    return {
        "swept": len(results),
        "changed": sum(1 for r in results if r["outcome"] == "changed"),
        "unchanged": sum(1 for r in results if r["outcome"] == "unchanged"),
        "failed": sum(1 for r in results if r["outcome"] == "failed"),
        "duplicates": sum(1 for r in results if r.get("duplicate_change")),
        "results": results,
    }


def select_due_monitors(db, *, limit: int = 50):
    """Read-only view of what the next sweep would touch.

    Kept separate from :func:`sweep_due_monitors` so an operator can inspect the
    queue without causing any outbound traffic.
    """
    now = db.execute(select(func.now())).scalar_one()
    return db.scalars(
        select(SourceMonitor)
        .where(
            SourceMonitor.status.in_(("active", "failing")),
            or_(SourceMonitor.next_check_at.is_(None), SourceMonitor.next_check_at <= now),
        )
        .order_by(SourceMonitor.next_check_at.asc().nullsfirst())
        .limit(limit)
    ).all()
