"""Phase 2 Reality Layer unit tests (design v0.9 §7.4, §7.5, §9).

Pure tests — no DB. They pin the semantics the DB/API layers must preserve:

- freshness buckets are explicit thresholds, never vibes;
- empty records ≠ "no animal" (NO_RECENT_RECORD semantics);
- one observation never becomes "经常/高频" (frequency needs thresholds +
  distinct sources; until defined, summaries only say counts/last-seen);
- expired facts are never presented as recent;
- a single AI-derived input never reaches the consumer as certain;
- only human decisions (VERIFIED*) publish a claim — AI cannot verify.
"""

from datetime import UTC, datetime, timedelta

from app.models.enums import REALITY_VERIFIED_DECISIONS, RealityDecision
from app.services.reality_summary import (
    AGING,
    DISPUTED,
    EXPIRED_FOR_SUMMARY,
    FRESH,
    HISTORICAL,
    INSUFFICIENT_OBSERVATION,
    MULTI_EVIDENCE_OBSERVED,
    NO_RECENT_RECORD,
    OBSERVED_HISTORICALLY,
    OBSERVED_RECENTLY,
    RECENT,
    _Row,
    freshness_for,
    summarize,
)

NOW = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)


def row(
    *,
    days_ago: float,
    source: str = "src-1",
    evidence: str = "ev-1",
    zone: str | None = None,
    action: str | None = None,
    disputed: bool = False,
    human_verified: bool = True,
) -> _Row:
    return _Row(
        observed_at=NOW - timedelta(days=days_ago),
        source_id=source,
        evidence_id=evidence,
        zone_name=zone,
        action=action,
        disputed=disputed,
        human_verified=human_verified,
    )


# ---------------------------------------------------------------------------
# Freshness buckets (v0.9 §7.5) — explicit thresholds
# ---------------------------------------------------------------------------


def test_freshness_boundaries():
    assert freshness_for(NOW - timedelta(days=7), NOW) == FRESH
    assert freshness_for(NOW - timedelta(days=7, microseconds=1), NOW) == RECENT
    assert freshness_for(NOW - timedelta(days=30), NOW) == RECENT
    assert freshness_for(NOW - timedelta(days=30, microseconds=1), NOW) == AGING
    assert freshness_for(NOW - timedelta(days=90), NOW) == AGING
    assert freshness_for(NOW - timedelta(days=365), NOW) == HISTORICAL
    assert freshness_for(NOW - timedelta(days=366), NOW) == EXPIRED_FOR_SUMMARY


def test_future_dated_record_is_fresh_not_negative():
    assert freshness_for(NOW + timedelta(days=1), NOW) == FRESH


def test_naive_observed_at_assumed_utc():
    naive = NOW.replace(tzinfo=None)
    assert freshness_for(naive, NOW) == FRESH


# ---------------------------------------------------------------------------
# Summary state machine (v0.9 §9)
# ---------------------------------------------------------------------------


def test_empty_record_is_not_no_animal():
    s = summarize([], now=NOW)
    assert s.state == INSUFFICIENT_OBSERVATION
    assert s.state != NO_RECENT_RECORD
    # absence of a record is never evidence of absence
    assert s.note and "≠" in s.note  # 暂无记录（≠ 没有动物）


def test_single_recent_observation_does_not_become_recurrence():
    s = summarize([row(days_ago=1)], now=NOW)
    assert s.state == OBSERVED_RECENTLY
    assert s.recent_count_7d == 1
    # summary carries no frequency wording field at all
    assert not hasattr(s, "frequency")
    assert s.verification_state == "human_verified"


def test_multi_evidence_requires_two_distinct_sources():
    two_claims_one_source = [
        row(days_ago=1, source="src-1"),
        row(days_ago=2, source="src-1"),
    ]
    s = summarize(two_claims_one_source, now=NOW)
    assert s.state == OBSERVED_RECENTLY  # same source ≠ recurrence

    two_sources = [
        row(days_ago=1, source="src-1"),
        row(days_ago=2, source="src-2"),
    ]
    s2 = summarize(two_sources, now=NOW)
    assert s2.state == MULTI_EVIDENCE_OBSERVED
    assert s2.distinct_source_count == 2


def test_unverified_recent_row_downgrades_to_insufficient():
    rows = [
        row(days_ago=1, source="src-1"),
        row(days_ago=2, source="src-2", human_verified=False),
    ]
    s = summarize(rows, now=NOW)
    assert s.state == INSUFFICIENT_OBSERVATION
    assert s.verification_state == "derived_ai_only"
    assert s.note and "人工核验" in (s.note or "")


def test_dispute_downgrades_summary():
    s = summarize([row(days_ago=1, disputed=True)], now=NOW)
    assert s.state == DISPUTED
    assert s.note and "争议" in (s.note or "")


def test_historical_only_is_never_presented_as_recent():
    s = summarize([row(days_ago=200)], now=NOW)
    assert s.state == OBSERVED_HISTORICALLY
    assert s.last_seen_at is None
    assert s.recent_count_7d == 0
    assert s.recent_count_30d == 0
    assert s.note and "不呈现为近期" in (s.note or "")


def test_expired_facts_excluded_from_recent_counts():
    s = summarize([row(days_ago=1), row(days_ago=400)], now=NOW)
    assert s.state == OBSERVED_RECENTLY
    assert s.evidence_count == 1  # only in-window rows count as evidence
    assert s.recent_count_7d == 1


def test_zones_and_actions_collected_from_recent_rows():
    rows = [
        row(days_ago=1, zone="z-outdoor", action="walking"),
        row(days_ago=2, zone="z-indoor", action="asking"),
    ]
    s = summarize(rows, now=NOW)
    assert s.observed_zones == ("z-indoor", "z-outdoor")
    assert s.observed_actions == ("asking", "walking")


def test_days_since_last_seen_and_bucket_counts():
    s = summarize([row(days_ago=5), row(days_ago=20), row(days_ago=200)], now=NOW)
    assert s.days_since_last_seen == 5
    assert s.recent_count_7d == 1
    assert s.recent_count_30d == 2


# ---------------------------------------------------------------------------
# Human-only decision red line (v0.9 §7.4)
# ---------------------------------------------------------------------------


def test_only_human_verified_decisions_can_publish():
    assert {
        RealityDecision.VERIFIED.value,
        RealityDecision.VERIFIED_WITH_NOTE.value,
    } == REALITY_VERIFIED_DECISIONS
    assert RealityDecision.HOLD.value not in REALITY_VERIFIED_DECISIONS
    assert RealityDecision.REJECTED.value not in REALITY_VERIFIED_DECISIONS
