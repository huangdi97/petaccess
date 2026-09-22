"""v0.9-R1 RealitySummaryEngine — pure, deterministic reality semantics (design v0.9 §7.5, §9).

The engine is deliberately *pure*: it takes plain data (datetimes, counts) and
returns plain values. It never touches the DB, never reads a Rule, and never
mutates anything. The API layer feeds it rows; the admin layer feeds it the same
function — there is exactly one definition of "recent" and one definition of a
summary state.

Freshness buckets (v0.9 §7.5) — first version uses explicit thresholds, so
"近期/经常/高频" can never be vibes:

    FRESH                  age <= 7  days   (shown as recent in summaries)
    RECENT                 7 <  age <= 30 days
    AGING                  30 < age <= 90 days
    HISTORICAL             90 < age <= 365 days
    EXPIRED_FOR_SUMMARY    age > 365 days    (excluded from "recent" summaries)

Invariants this module enforces:

- One observation != recurrence: frequency wording requires explicit thresholds
  AND a distinct-source requirement; until defined, summaries only report
  counts and last-seen.
- No observation != no animal: NO_RECENT_RECORD and INSUFFICIENT_OBSERVATION
  are distinct states; neither may be phrased as "没有动物".
- Expired facts are never shown as recent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

#: Thresholds in days — first-version explicit buckets (v0.9 §7.5).
FRESH_DAYS = 7
RECENT_DAYS = 30
AGING_DAYS = 90
HISTORICAL_DAYS = 365

#: Frozen vocabulary — summary state machine.
OBSERVED_RECENTLY = "OBSERVED_RECENTLY"
OBSERVED_HISTORICALLY = "OBSERVED_HISTORICALLY"
MULTI_EVIDENCE_OBSERVED = "MULTI_EVIDENCE_OBSERVED"
NO_RECENT_RECORD = "NO_RECENT_RECORD"
INSUFFICIENT_OBSERVATION = "INSUFFICIENT_OBSERVATION"
DISPUTED = "DISPUTED"

#: Frozen vocabulary — freshness buckets.
FRESH = "FRESH"
RECENT = "RECENT"
AGING = "AGING"
HISTORICAL = "HISTORICAL"
EXPIRED_FOR_SUMMARY = "EXPIRED_FOR_SUMMARY"

#: Days that still count as "recent" for consumer summaries.
RECENT_WINDOW_DAYS = RECENT_DAYS


def freshness_for(observed_at: datetime, now: datetime | None = None) -> str:
    """Bucket a single observed timestamp into a freshness state (v0.9 §7.5).

    ``observed_at`` is the *occurrence* time, never the ingestion time. A row
    whose occurrence is a year old is HISTORICAL even if it was ingested today.
    """
    now = now or datetime.now(UTC)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    age = now - observed_at
    if age < timedelta(days=0):  # future-dated record: treat as fresh, flag for review
        return FRESH
    if age <= timedelta(days=FRESH_DAYS):
        return FRESH
    if age <= timedelta(days=RECENT_DAYS):
        return RECENT
    if age <= timedelta(days=AGING_DAYS):
        return AGING
    if age <= timedelta(days=HISTORICAL_DAYS):
        return HISTORICAL
    return EXPIRED_FOR_SUMMARY


@dataclass(frozen=True)
class RealitySummary:
    """Consumer-facing reality answer for one place (v0.9 §9).

    Fields are facts, never vibes. ``state`` is one of the frozen vocabulary
    above; frequency phrasing is only emitted once explicit thresholds and a
    distinct-source requirement exist (never today).
    """

    state: str
    last_seen_at: datetime | None = None
    evidence_count: int = 0
    distinct_source_count: int = 0
    observed_zones: tuple[str, ...] = ()
    observed_actions: tuple[str, ...] = ()
    staff_response_summary: tuple[dict, ...] = ()
    facility_summary: tuple[dict, ...] = ()
    freshness_state: str | None = None
    verification_state: str | None = None
    recent_count_7d: int = 0
    recent_count_30d: int = 0
    days_since_last_seen: int | None = None
    note: str | None = None


@dataclass(frozen=True)
class _Row:
    observed_at: datetime
    source_id: str | None
    evidence_id: str | None
    zone_name: str | None = None
    action: str | None = None
    disputed: bool = False
    human_verified: bool = False

    def expired(self, now: datetime | None = None) -> bool:
        """A row is expired when it can no longer appear in a recent summary."""
        return freshness_for(self.observed_at, now) in (HISTORICAL, EXPIRED_FOR_SUMMARY)


def summarize(
    rows: list[_Row],
    *,
    now: datetime | None = None,
    window_days: int = RECENT_WINDOW_DAYS,
) -> RealitySummary:
    """Aggregate observed-presence rows into a RealitySummary.

    Contract (v0.9 §5, §9):
    - rows visible here must already be human-verified published claims; the
      caller filters. ``human_verified`` marks claims whose verification is
      human; if ANY visible row is not human-verified the summary must say
      INSUFFICIENT_OBSERVATION rather than imply certainty.
    - an empty row set must NOT mean "no animals" — it means no recent record.
    - one observation never becomes "经常/高频".
    """
    now = now or datetime.now(UTC)
    window = timedelta(days=window_days)
    cutoff = now - window

    recent = [r for r in rows if r.observed_at >= cutoff and not r.expired(now)]
    in_window = [r for r in rows if r.observed_at >= cutoff]
    expired = [r for r in rows if r.expired(now)]

    # all observed rows considered for last-seen
    all_rows = sorted(rows, key=lambda r: r.observed_at, reverse=True)

    if not rows:
        return RealitySummary(
            state=INSUFFICIENT_OBSERVATION,
            note="暂无记录（≠ 没有动物）",
        )

    last = all_rows[0]
    last_expired = last.expired(now)
    days_since = None
    if not last_expired:
        days_since = max(0, int((now - last.observed_at).total_seconds() // 86400))
    buckets = {FRESH: 0, RECENT: 0, AGING: 0, HISTORICAL: 0, EXPIRED_FOR_SUMMARY: 0}
    for r in rows:
        buckets[freshness_for(r.observed_at, now)] += 1

    distinct_sources = {r.source_id for r in in_window if r.source_id}
    zones = tuple(sorted({r.zone_name for r in recent if r.zone_name}))
    actions = tuple(sorted({r.action for r in recent if r.action}))
    any_unverified = any(not r.human_verified for r in recent)
    any_disputed = any(r.disputed for r in recent)

    state: str
    note: str | None = None
    if any_disputed:
        state = DISPUTED
        note = "存在争议记录，摘要降级"
    elif not recent and expired:
        state = OBSERVED_HISTORICALLY
        note = "仅历史记录，不呈现为近期"
    elif not recent:
        state = NO_RECENT_RECORD
        note = "暂无近期记录（≠ 没有动物）"
    elif any_unverified:
        state = INSUFFICIENT_OBSERVATION
        note = "近期记录尚未完成人工核验"
    elif buckets[FRESH] + buckets[RECENT] >= 2 and len(distinct_sources) >= 2:
        state = MULTI_EVIDENCE_OBSERVED
    else:
        state = OBSERVED_RECENTLY

    return RealitySummary(
        state=state,
        last_seen_at=last.observed_at if not last_expired else None,
        evidence_count=len(in_window),
        distinct_source_count=len(distinct_sources),
        observed_zones=zones,
        observed_actions=actions,
        freshness_state=freshness_for(last.observed_at, now),
        verification_state="human_verified" if not any_unverified else "derived_ai_only",
        recent_count_7d=buckets[FRESH],
        recent_count_30d=buckets[FRESH] + buckets[RECENT],
        days_since_last_seen=days_since if not last_expired else None,
        note=note,
    )
