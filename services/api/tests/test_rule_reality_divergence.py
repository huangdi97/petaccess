"""RuleRealityDivergence unit tests — pin every state and every red line.

Pure, no DB. Covers AC8 (six divergence states) and the governance red lines
(Divergence describes only; never rewrites Rule/Reality; absence ≠ no animals).
"""

from __future__ import annotations

import pytest

from app.services.rule_reality_divergence import (
    Divergence,
    DivergenceState,
    RuleEffect,
    divergence,
)


def s(
    *,
    rule_effect: str,
    reality_state: str,
) -> Divergence:
    return divergence(rule_effect=rule_effect, reality_state=reality_state)


# ---------------------------------------------------------------------------
# Six divergence states — every one reachable
# ---------------------------------------------------------------------------


def test_aligned_allowed_observed():
    d = s(rule_effect="allowed", reality_state="OBSERVED_RECENTLY")
    assert d.state == DivergenceState.RULE_REALITY_ALIGNED
    assert d.note and "一致" in d.note


def test_prohibits_but_observed():
    d = s(rule_effect="prohibited", reality_state="OBSERVED_RECENTLY")
    assert d.state == DivergenceState.RULE_PROHIBITS_BUT_OBSERVED
    assert d.note and "差异" in d.note
    # the divergence must NOT weaken the rule effect
    assert d.rule_effect == "prohibited"


def test_allows_but_no_recent_record():
    d = s(rule_effect="allowed", reality_state="NO_RECENT_RECORD")
    assert d.state == DivergenceState.RULE_ALLOWS_BUT_NO_RECENT_RECORD
    # absence is never evidence of absence
    assert d.note and "≠" in d.note
    assert d.note and "没有动物" in d.note


def test_unknown_but_observed():
    d = s(rule_effect="unknown", reality_state="OBSERVED_RECENTLY")
    assert d.state == DivergenceState.RULE_UNKNOWN_BUT_OBSERVED
    assert d.note and "未知不等于允许" in d.note


def test_conditional_and_observed():
    d = s(rule_effect="conditional", reality_state="MULTI_EVIDENCE_OBSERVED")
    assert d.state == DivergenceState.RULE_CONDITIONAL_AND_OBSERVED
    assert d.note and "条件" in d.note


def test_insufficient_data_on_empty_reality():
    d = s(rule_effect="allowed", reality_state="INSUFFICIENT_OBSERVATION")
    assert d.state == DivergenceState.INSUFFICIENT_DATA
    assert d.note and "人工核验" in d.note


# ---------------------------------------------------------------------------
# Red lines
# ---------------------------------------------------------------------------


def test_divergence_never_rewrites_rule():
    """The difference description must not alter the rule effect value."""
    for effect in ("allowed", "prohibited", "conditional", "unknown"):
        d = s(rule_effect=effect, reality_state="OBSERVED_RECENTLY")
        assert d.rule_effect == effect


def test_divergence_is_read_only_plain_data():
    d = s(rule_effect="prohibited", reality_state="OBSERVED_RECENTLY")
    assert d.state is not None
    assert isinstance(d.rule_effect, str)
    assert isinstance(d.reality_state, str)
    # frozen dataclass — no mutation surface
    with pytest.raises(AttributeError):
        d.state = "RULE_REALITY_ALIGNED"  # type: ignore[misc, assignment]


def test_no_recent_record_never_reads_as_no_animals():
    for effect in ("allowed", "prohibited", "conditional"):
        d = s(rule_effect=effect, reality_state="NO_RECENT_RECORD")
        assert d.note and "≠" in d.note


def test_unknown_rule_with_observations_is_never_allowance():
    d = s(rule_effect="unknown", reality_state="OBSERVED_RECENTLY")
    assert d.state == DivergenceState.RULE_UNKNOWN_BUT_OBSERVED
    assert d.state not in (
        DivergenceState.RULE_REALITY_ALIGNED,
        DivergenceState.RULE_PROHIBITS_BUT_OBSERVED,
    )


def test_disputed_reality_downgrades_to_insufficient():
    d = s(rule_effect="prohibited", reality_state="DISPUTED")
    assert d.state == DivergenceState.INSUFFICIENT_DATA
    assert d.note and "争议" in d.note


def test_historical_observation_is_not_recent_evidence():
    # a long-ago sighting does not make a rule "aligned and confirmed":
    # for a prohibiting rule it cannot confirm coexistence either way, but it
    # must never be phrased as "recently observed".
    d = s(rule_effect="prohibited", reality_state="OBSERVED_HISTORICALLY")
    assert d.note and "近期" in d.note


@pytest.mark.parametrize(
    ("effect", "reality"),
    [
        ("allowed", "OBSERVED_RECENTLY"),
        ("allowed", "MULTI_EVIDENCE_OBSERVED"),
        ("allowed", "OBSERVED_HISTORICALLY"),
        ("allowed", "NO_RECENT_RECORD"),
        ("allowed", "INSUFFICIENT_OBSERVATION"),
        ("allowed", "DISPUTED"),
        ("prohibited", "OBSERVED_RECENTLY"),
        ("prohibited", "MULTI_EVIDENCE_OBSERVED"),
        ("prohibited", "OBSERVED_HISTORICALLY"),
        ("prohibited", "NO_RECENT_RECORD"),
        ("prohibited", "INSUFFICIENT_OBSERVATION"),
        ("prohibited", "DISPUTED"),
        ("conditional", "OBSERVED_RECENTLY"),
        ("conditional", "MULTI_EVIDENCE_OBSERVED"),
        ("conditional", "OBSERVED_HISTORICALLY"),
        ("conditional", "NO_RECENT_RECORD"),
        ("conditional", "INSUFFICIENT_OBSERVATION"),
        ("conditional", "DISPUTED"),
        ("unknown", "OBSERVED_RECENTLY"),
        ("unknown", "MULTI_EVIDENCE_OBSERVED"),
        ("unknown", "OBSERVED_HISTORICALLY"),
        ("unknown", "NO_RECENT_RECORD"),
        ("unknown", "INSUFFICIENT_OBSERVATION"),
        ("unknown", "DISPUTED"),
    ],
)
def test_cartesian_product_is_total_and_reproducible(effect, reality):
    """Every (rule, reality) pair yields exactly one of the six states."""
    d = s(rule_effect=effect, reality_state=reality)
    assert d.state in set(DivergenceState)
    d2 = s(rule_effect=effect, reality_state=reality)
    assert d == d2  # deterministic


def test_rule_effect_enum_values_match_access_answer_spelling():
    """The effect vocabulary must stay aligned with the rule layer's spelling."""
    assert RuleEffect.ALLOWED.value == "allowed"
    assert RuleEffect.PROHIBITED.value == "prohibited"
    assert RuleEffect.CONDITIONAL.value == "conditional"
    assert RuleEffect.UNKNOWN.value == "unknown"
