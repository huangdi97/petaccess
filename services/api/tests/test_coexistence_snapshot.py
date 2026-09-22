"""CoexistenceSnapshot unit tests — pure, no DB.

Covers AC9: the one aggregate bundles RuleAnswer + RealityAnswer +
StaffResponseSummary + FacilitySummary + RuleRealityDivergence + EvidenceSummary,
and surfaces must never recompute it. Also pins the red line that divergence
only *describes* — it never rewrites the rule or reality halves.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.services.coexistence_snapshot import (
    COEXISTENCE_SNAPSHOT_VERSION,
    CoexistenceSnapshot,
    build_coexistence_snapshot,
    to_plain,
)
from app.services.rule_reality_divergence import DivergenceState

NOW = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)

# A minimal AccessAnswer-shaped dict (only the fields the builder reads).
RULE_PROHIBITED = {
    "normative_result": {"effect": "prohibited"},
    "evidence_state": {
        "rules": [{"rule_id": "r1", "source_id": "s1"}],
        "first_party_operator_source_pending": False,
    },
}

REALITY_OBSERVED = {
    "state": "OBSERVED_RECENTLY",
    "evidence_count": 2,
    "distinct_source_count": 1,
    "verification_state": "human_verified",
    "staff_response_summary": [{"response_action": "asked", "count": 1}],
    "facility_summary": [{"facility_type": "water_station", "count": 1}],
}

REALITY_EMPTY = {
    "state": "NO_RECENT_RECORD",
    "evidence_count": 0,
    "distinct_source_count": 0,
    "verification_state": "human_verified",
    "staff_response_summary": [],
    "facility_summary": [],
}


def build(
    *,
    rule_answer=RULE_PROHIBITED,
    reality_answer=REALITY_OBSERVED,
    staff=None,
    facility=None,
) -> CoexistenceSnapshot:
    return build_coexistence_snapshot(
        place_id="place-1",
        rule_answer=rule_answer,
        reality_answer=reality_answer,
        staff_response_summary=(
            staff if staff is not None else reality_answer.get("staff_response_summary", [])
        ),
        facility_summary=(
            facility if facility is not None else reality_answer.get("facility_summary", [])
        ),
        now=NOW,
    )


# ---------------------------------------------------------------------------
# Bundle completeness (AC9)
# ---------------------------------------------------------------------------


def test_snapshot_bundles_all_six_parts():
    snap = build()
    assert snap.place_id == "place-1"
    assert snap.version == COEXISTENCE_SNAPSHOT_VERSION
    assert snap.rule_answer is RULE_PROHIBITED
    assert snap.reality_answer is REALITY_OBSERVED
    assert snap.staff_response_summary[0]["response_action"] == "asked"
    assert snap.facility_summary[0]["facility_type"] == "water_station"
    assert snap.evidence_summary.reality_evidence_count == 2
    assert snap.evidence_summary.reality_distinct_source_count == 1
    assert snap.evidence_summary.rule_evidence[0]["rule_id"] == "r1"
    assert not snap.evidence_summary.rule_first_party_pending


def test_divergence_derived_from_both_halves():
    # prohibited rule + observed reality -> divergence states the difference
    snap = build()
    assert snap.divergence.state == DivergenceState.RULE_PROHIBITS_BUT_OBSERVED
    assert snap.divergence.rule_effect == "prohibited"
    assert snap.divergence.reality_state == "OBSERVED_RECENTLY"


def test_divergence_never_rewrites_rule_answer():
    snap = build()
    before = snap.rule_answer["normative_result"]["effect"]
    assert before == "prohibited"
    assert snap.divergence.rule_effect == before  # echo, not a rewrite


def test_to_plain_is_json_safe_and_keeps_all_keys():
    snap = build()
    plain = to_plain(snap)
    assert set(plain) == {
        "place_id",
        "generated_at",
        "version",
        "rule_answer",
        "reality_answer",
        "staff_response_summary",
        "facility_summary",
        "divergence",
        "evidence_summary",
    }
    assert isinstance(plain["generated_at"], str)  # ISO, not datetime
    assert isinstance(plain["divergence"], dict)
    assert plain["divergence"]["state"] == "RULE_PROHIBITS_BUT_OBSERVED"


def test_snapshot_is_immutable():
    snap = build()
    with pytest.raises(AttributeError):
        snap.place_id = "place-2"  # type: ignore[misc, assignment]


def test_evidence_summary_keeps_reality_verification_state():
    snap = build(reality_answer=REALITY_EMPTY)
    assert snap.evidence_summary.reality_verification_state == "human_verified"


# ---------------------------------------------------------------------------
# Divergence flows through the snapshot (AC9: single source of truth)
# ---------------------------------------------------------------------------


def test_no_recent_record_reality_yields_allows_but_no_record_for_allowed_rule():
    rule_allowed = {
        "normative_result": {"effect": "allowed"},
        "evidence_state": {"rules": [], "first_party_operator_source_pending": True},
    }
    snap = build(rule_answer=rule_allowed, reality_answer=REALITY_EMPTY)
    assert snap.divergence.state == DivergenceState.RULE_ALLOWS_BUT_NO_RECENT_RECORD
    # absence of records is never "no animals"
    assert "没有动物" in snap.divergence.note


def test_unknown_rule_with_observations_flows_as_unknown_but_observed():
    rule_unknown = {
        "normative_result": {"effect": "unknown"},
        "evidence_state": {"rules": [], "first_party_operator_source_pending": True},
    }
    snap = build(rule_answer=rule_unknown, reality_answer=REALITY_OBSERVED)
    assert snap.divergence.state == DivergenceState.RULE_UNKNOWN_BUT_OBSERVED
    assert snap.divergence.rule_effect == "unknown"


def test_unknown_rule_never_becomes_allowance_in_snapshot():
    rule_unknown = {
        "normative_result": {"effect": "unknown"},
        "evidence_state": {"rules": [], "first_party_operator_source_pending": True},
    }
    snap = build(rule_answer=rule_unknown, reality_answer=REALITY_OBSERVED)
    assert snap.divergence.state not in (
        DivergenceState.RULE_REALITY_ALIGNED,
        DivergenceState.RULE_PROHIBITS_BUT_OBSERVED,
    )


def test_generated_at_is_honored():
    snap = build()
    assert snap.generated_at == NOW
