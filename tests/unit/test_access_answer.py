"""The unified AccessAnswer must be structurally incapable of overstating.

Two classes of test live here, and the second is the point of the module:

* **Shape** — the thirteen fields design §10 requires are present, and the answer
  is a plain dict so every surface renders the same thing.
* **Refusals** — zone never flattens into a place verdict, "no rule in scope"
  never becomes `allowed`, a withheld carve-out becomes `conditional` with
  `missing_inputs`, and a *first-party / official* sentence cannot appear in an
  answer whose own evidence state says no first-party operator source exists.

The refusal tests use the real resolver dataclasses, not stand-ins, so a change
to `EffectiveRuleSet` that broke the derivation would fail here.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.rulespec.access_answer import (
    ACCESS_ANSWER_VERSION,
    FORBIDDEN_CLAIMS,
    PlaceFacts,
    RuleFacts,
    ZoneFacts,
    as_plain,
    assert_no_unbacked_first_party_claim,
    build_access_answer,
    first_party_operator_source_exists,
)
from app.rulespec.v05_resolver import ComplianceState, EffectiveRuleSet, LayeredRule

NOW = datetime(2026, 9, 19, 5, 0, tzinfo=UTC)

PLACE = PlaceFacts(id="p1", canonical_name="世纪公园", place_type="park")
ZONE_OTHER = ZoneFacts(id="z1", name="世纪公园其他区域", zone_type="area")
ZONE_PET_AREA = ZoneFacts(id="z2", name="世纪宠物乐园（芳花园区域）", zone_type="pet_area")

#: The real published row's provenance: a government platform relaying the
#: operator, captured as a search snippet, no first-party operator source.
GOV_RELAYED = RuleFacts(
    rule_id="r1",
    rule_layer="OPERATOR_POLICY",
    mandatory_level="operator_discretion",
    source_id="s1",
    source_type="government_service",
    issuer="上海市文化和旅游事业发展中心《又一新地标！这个周末，带「毛孩子」来放飞》（转述世纪公园官方口径）",
    directness="secondary",
    issuer_verification="verified",
    evidence_strength="search_snippet",
    source_url="https://example.test/news",
    source_scope_exact="宠物",
    subject_scope_normalized="ordinary_pet",
    normalization_type="exact",
)

REQUIRED_FIELDS = (
    "query_context",
    "normative_result",
    "condition_evaluation",
    "scope_summary",
    "evidence_state",
    "conflict_state",
    "rights_information",
    "matched_rule_versions",
    "explanation_items",
    "next_actions",
    "evaluated_at",
    "valid_until",
    "evaluation_version",
)


def _rule(rule_id: str = "r1", **kw) -> LayeredRule:
    base = dict(
        id=rule_id,
        animal_scope="ordinary_pet",
        action="enter",
        effect="prohibited",
        rule_layer="OPERATOR_POLICY",
        origin="zone_override",
        zone_id="z1",
        source_id="s1",
        normative_effect="prohibition",
    )
    base.update(kw)
    return LayeredRule(**base)


def _empty(effect: str = "unknown", state: ComplianceState = ComplianceState.UNKNOWN):
    return EffectiveRuleSet(effect=effect, compliance_state=state)


def _build(query: dict, zone: ZoneFacts | None, rule_set, facts=None):
    return build_access_answer(
        query=query,
        place=PLACE,
        zone=zone,
        rule_set=rule_set,
        rule_facts=facts if facts is not None else {"r1": GOV_RELAYED},
        now=NOW,
    )


def _effect_and_summary(answer: dict) -> str:
    """`effect` plus the human sentence — the two places a stray 'allowed' hides."""
    return f"{answer['normative_result']['effect']} {answer['normative_result']['summary']}"


# --------------------------------------------------------------- shape


def test_01_all_thirteen_fields_are_present_and_plain():
    rs = EffectiveRuleSet(
        applicable_rules=[_rule()],
        effect="prohibited",
        compliance_state=ComplianceState.CONSISTENT,
        explanation_steps=["operator layer considered (1 in scope)."],
    )
    answer = _build(
        {"place_id": "p1", "zone_id": "z1", "animal": "dog", "action": "enter"}, ZONE_OTHER, rs
    )
    for field in REQUIRED_FIELDS:
        assert field in answer, f"缺少 {field}"
    assert answer["evaluation_version"] == ACCESS_ANSWER_VERSION
    # Must survive json.dumps with no custom encoder — that is what "plain" means.
    import json

    json.dumps(as_plain(answer), ensure_ascii=False)


# --------------------------------------------------------------- refusals


def test_02_no_rule_in_scope_is_unknown_and_never_allowed():
    answer = _build(
        {"place_id": "p1", "zone_id": "z2", "animal": "dog", "action": "enter"},
        ZONE_PET_AREA,
        _empty(),
    )
    assert answer["normative_result"]["effect"] == "unknown"
    assert answer["scope_summary"]["scope_level"] == "none"
    assert any("未知不等于允许" in a for a in answer["next_actions"])
    assert "allowed" not in _effect_and_summary(answer)


def test_03_zone_rule_does_not_become_a_place_verdict():
    """A query without a zone must not inherit the zone rule's prohibition."""
    rs = EffectiveRuleSet(
        applicable_rules=[],
        effect="unknown",
        compliance_state=ComplianceState.UNKNOWN,
    )
    answer = _build({"place_id": "p1", "zone_id": None, "animal": "dog"}, None, rs)
    assert answer["normative_result"]["effect"] == "unknown"
    assert answer["scope_summary"]["zone"] is None
    assert answer["scope_summary"]["zone_requested"] is False


def test_04_zone_scoped_rule_reports_level_zone_not_place():
    rs = EffectiveRuleSet(
        applicable_rules=[_rule()],
        effect="prohibited",
        compliance_state=ComplianceState.CONSISTENT,
    )
    answer = _build({"place_id": "p1", "zone_id": "z1", "animal": "dog"}, ZONE_OTHER, rs)
    assert answer["normative_result"]["effect"] == "prohibited"
    assert answer["scope_summary"]["scope_level"] == "zone"
    assert answer["scope_summary"]["zone_scoped_rule_count"] == 1


def test_05_withheld_carve_out_is_conditional_with_missing_inputs():
    rs = EffectiveRuleSet(
        applicable_rules=[_rule()],
        effect="conditional",
        compliance_state=ComplianceState.CONSISTENT,
        missing_inputs=["holder_scope"],
        pending_exceptions=["exc-1"],
    )
    answer = _build({"place_id": "p1", "zone_id": "z1", "animal": "dog"}, ZONE_OTHER, rs)
    assert answer["normative_result"]["effect"] == "conditional"
    assert answer["condition_evaluation"]["missing_inputs"] == ["holder_scope"]
    assert answer["condition_evaluation"]["pending_exceptions"] == ["exc-1"]
    assert any("补充" in a for a in answer["next_actions"])


# --------------------------------------------------------------- evidence


def test_06_government_relay_reports_semantics_and_pending_first_party():
    rs = EffectiveRuleSet(
        applicable_rules=[_rule()],
        effect="prohibited",
        compliance_state=ComplianceState.CONSISTENT,
    )
    answer = _build({"place_id": "p1", "zone_id": "z1", "animal": "dog"}, ZONE_OTHER, rs)
    ev = answer["evidence_state"]
    entry = ev["rules"][0]
    assert entry["source_type"] == "government_service"
    assert entry["source_type_semantics"] == "政府平台转述园方口径"
    assert entry["first_party_operator_source_pending"] is True
    assert ev["first_party_operator_source_pending"] is True
    assert ev["first_party_operator_source_count"] == 0
    assert ev["acceptance_required"] is True  # search_snippet
    assert "未取得运营方一手来源" in entry["provenance_statement"]


def test_07_no_forbidden_claim_survives_a_build():
    rs = EffectiveRuleSet(
        applicable_rules=[_rule()],
        effect="prohibited",
        compliance_state=ComplianceState.CONSISTENT,
    )
    answer = _build({"place_id": "p1", "zone_id": "z1", "animal": "dog"}, ZONE_OTHER, rs)
    blob = str(as_plain(answer))
    for claim in FORBIDDEN_CLAIMS:
        assert claim not in blob, f"答案里出现了越权表述 {claim!r}"


def test_08_guard_fires_when_a_first_party_claim_has_no_first_party_source():
    answer = {
        "evidence_state": {"first_party_operator_source_count": 0},
        "normative_result": {"summary": "世纪公园官方已确认禁止携带宠物。"},
    }
    with pytest.raises(AssertionError, match="越权表述"):
        assert_no_unbacked_first_party_claim(answer)


def test_09_guard_allows_the_claim_when_a_first_party_source_really_exists():
    answer = {
        "evidence_state": {"first_party_operator_source_count": 1},
        "normative_result": {"summary": "运营方已确认。"},
    }
    assert_no_unbacked_first_party_claim(answer)  # must not raise


def test_10_first_party_requires_both_operator_type_and_direct():
    assert first_party_operator_source_exists(
        source_type="official_operator_policy", directness="direct"
    )
    # The government's own statute is direct, but it is not the *operator's*.
    assert not first_party_operator_source_exists(
        source_type="statute_or_regulation", directness="direct"
    )
    assert not first_party_operator_source_exists(
        source_type="official_operator_policy", directness="secondary"
    )
    assert not first_party_operator_source_exists(
        source_type="government_service", directness="secondary"
    )


def test_11_rule_without_a_source_entry_reports_the_gap_not_a_default():
    rs = EffectiveRuleSet(
        applicable_rules=[_rule(rule_id="r-missing", source_id=None)],
        effect="prohibited",
        compliance_state=ComplianceState.CONSISTENT,
    )
    answer = _build({"place_id": "p1", "zone_id": "z1", "animal": "dog"}, ZONE_OTHER, rs, {})
    entry = answer["evidence_state"]["rules"][0]
    assert entry["source_id"] is None
    assert entry["source_type"] is None
    assert entry["first_party_operator_source_pending"] is True
    assert "没有可追溯来源" in entry["provenance_statement"]


def test_12_scope_summary_carries_the_zone_that_actually_governs():
    rs = EffectiveRuleSet(
        applicable_rules=[_rule()],
        effect="prohibited",
        compliance_state=ComplianceState.CONSISTENT,
    )
    answer = _build({"place_id": "p1", "zone_id": "z1", "animal": "dog"}, ZONE_OTHER, rs)
    assert answer["scope_summary"]["zone"]["id"] == "z1"
    assert answer["scope_summary"]["zone"]["name"] == "世纪公园其他区域"
    assert answer["scope_summary"]["place"]["name"] == "世纪公园"
