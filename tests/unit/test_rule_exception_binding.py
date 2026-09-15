"""RuleException **layer faithfulness** (RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE).

What this guards against
------------------------

``rule_exception`` inherits the *base rule's* layer — the resolver synthesises the
carve-out rule with ``rule_layer=r.rule_layer``. That is the correct design, but
it means the entire safety of the mechanism rests on **which base rule the
carve-out is attached to**:

* bind a legal proviso to its own legal base  → the statute carves itself out, fine;
* bind an operator's "guide dogs are welcome" to a *legal* prohibition → the
  operator's sentence is now standing in the LEGAL layer, out-voting the statute.
  The resolver cannot tell the difference, because by the time it looks, the
  carve-out *is* a legal rule.

The earlier R2-FINAL plan did exactly the second thing (``dl-sd-op →
dl-legal-dog``, ``fp-sd-op-firstparty → fp-legal-dog``, ``lib-sd-op-* →
lib-legal-dog``, ``qt-sd-op → qt-indoor-legal``). These tests pin the fix:

* every configured binding stays inside one layer, and
* a correctly-bound operator carve-out still cannot relax the legal floor, and
* a legal exception can still carve out its own legal base, and
* an allowance asserted only by an operator, for a subject the law prohibits and
  the law does not except, is held rather than published.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
REGISTER = REPO / "docs" / "reality_audit" / "review_decisions_r2_final.json"
PACKET = REPO / "HUMAN_REVIEW_PACKET_R2_FINAL.md"

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)

OPERATOR_BASES = {
    # carve-out rule_id -> the operator base rule it must bind, and must not bind
    "dl-sd-op": ("dl-pet-ban", "dl-legal-dog"),
    "fp-sd-op-firstparty": ("fp-pets-op-firstparty", "fp-legal-dog"),
    "lib-sd-op-guide": ("lib-pets-op", "lib-legal-dog"),
    "qt-sd-op": ("qt-indoor-op", "qt-indoor-legal"),
}

LEGAL_BASES = {
    # legal carve-out rule_id -> its own legal base rule
    "mn-sd-legal": "mn-legal-dog",
    "lib-sd-legal": "lib-legal-dog",
    "fp-sd-legal": "fp-legal-dog",
    "gh-sd-legal": "gh-legal-dog",
    "qt-sd-legal": "qt-indoor-legal",
    "sb-sd-legal": "sb-legal-dog",
    "xm-sd-legal": "xm-legal-dog",
    "dl-sd-legal": "dl-legal-dog",
}


@pytest.fixture(scope="module")
def register() -> dict:
    assert REGISTER.exists(), "run scripts/gen_human_review_packet_r2_final.py"
    return json.loads(REGISTER.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rows(register: dict) -> list[dict]:
    return register["rows"]


@pytest.fixture(scope="module")
def by_id(rows: list[dict]) -> dict[str, dict]:
    return {r["rule_id"]: r for r in rows}


@pytest.fixture(scope="module")
def plan(register: dict) -> dict[str, dict]:
    return {e["rule_id"]: e for e in register["exception_plan"]}


# --------------------------------------------------------------- plan is safe


def test_no_binding_crosses_a_layer(plan):
    """Every configured binding stays inside its own layer."""
    offenders = [
        f"{e['rule_id']} -> {b['rule_id']}[{b['layer']}]"
        for e in plan.values()
        for b in e["bases"]
        if not b["same_layer"] or b["layer"] != e["layer"]
    ]
    assert offenders == [], f"跨层绑定不得进入发布计划：{offenders}"


def test_register_declares_the_binding_policy(register):
    policy = register["exception_binding"]
    assert policy["policy"] == "same-layer-only"
    assert policy["legal_exception_binds"] == "LEGAL"
    assert policy["operator_carve_out_binds"] == "OPERATOR_POLICY"
    assert policy["cross_layer_override_allowed"] is False


def test_the_generator_refuses_to_emit_a_cross_layer_binding(plan):
    """Closure: the validator is what makes the rule enforceable, not just
    documented. The real plan must pass it…"""
    import gen_human_review_packet_r2_final as gen

    gen.validate_exception_binding(list(plan.values()))

    # …and a plan that did cross layers must be refused outright.
    bad = [
        {
            "rule_id": "lib-sd-op-guide",
            "layer": "OPERATOR_POLICY",
            "bases": [
                {
                    "rule_id": "lib-legal-dog",
                    "layer": "LEGAL",
                    "decision": "RECOMMEND_APPROVE",
                    "same_layer": False,
                    "executable": True,
                }
            ],
        }
    ]
    with pytest.raises(SystemExit):
        gen.validate_exception_binding(bad)


def test_dl_sd_op_never_binds_dl_legal_dog(plan):
    """Disney's guide-dog allowance is the operator's own carve-out of its own
    pet ban — never an exception to the statutory dog prohibition."""
    entry = plan["dl-sd-op"]
    bound = {b["rule_id"] for b in entry["bases"]}
    assert bound == {"dl-pet-ban"}, bound
    assert "dl-legal-dog" not in bound
    # and the layer-blind algorithm really did point it at the statute once
    assert "dl-legal-dog" in entry["cross_layer_dropped"]


def test_fp_sd_op_firstparty_never_binds_fp_legal_dog(plan):
    entry = plan["fp-sd-op-firstparty"]
    bound = {b["rule_id"] for b in entry["bases"]}
    assert bound == {"fp-pets-op-firstparty"}, bound
    assert "fp-legal-dog" not in bound
    assert "fp-legal-dog" in entry["cross_layer_dropped"]


@pytest.mark.parametrize("rule_id", sorted(OPERATOR_BASES))
def test_operator_carve_outs_bind_the_operators_own_base(plan, rule_id):
    expected_base, forbidden_base = OPERATOR_BASES[rule_id]
    entry = plan[rule_id]
    assert entry["layer"] == "OPERATOR_POLICY"
    bound = {b["rule_id"] for b in entry["bases"]}
    assert bound == {expected_base}, f"{rule_id} 应绑定 {expected_base}，实为 {bound}"
    assert forbidden_base not in bound, f"{rule_id} 不得绑定高层的 {forbidden_base}"
    for b in entry["bases"]:
        assert b["layer"] == "OPERATOR_POLICY", b


@pytest.mark.parametrize(("rule_id", "expected_base"), sorted(LEGAL_BASES.items()))
def test_legal_carve_outs_bind_their_own_legal_base(plan, rule_id, expected_base):
    entry = plan[rule_id]
    assert entry["layer"] == "LEGAL"
    assert {b["rule_id"] for b in entry["bases"]} == {expected_base}
    for b in entry["bases"]:
        assert b["layer"] == "LEGAL", b


def test_hold_base_cannot_receive_an_executable_exception(plan, by_id):
    """A base that is itself held or refused is not being published, so nothing
    may be attached to it as a live exception."""
    for entry in plan.values():
        for b in entry["bases"]:
            if b["decision"] != "RECOMMEND_APPROVE":
                assert entry["executable"] is False, (
                    f"{entry['rule_id']} 的 base {b['rule_id']} 为 {b['decision']}，"
                    "不得标记为可执行"
                )
        if entry["executable"]:
            assert entry["decision"] == "RECOMMEND_APPROVE"
            assert all(b["decision"] == "RECOMMEND_APPROVE" for b in entry["bases"])


def test_exception_plan_preserves_layer_and_source_provenance(plan, by_id):
    """Principle E: a RuleException carries source / layer / mandatory_level /
    source_scope_exact / subject_scope_normalized / normalization_type."""
    for rule_id, entry in plan.items():
        row = by_id[rule_id]
        assert entry["layer"] == row["rule_layer"], f"{rule_id}.layer 不一致"
        for field in (
            "mandatory_level",
            "source_scope_exact",
            "subject_scope_normalized",
            "normalization_type",
            "source_id",
        ):
            assert entry[field] == row[field], f"{rule_id}.{field} 在计划与逐行间不一致"
            assert entry[field], f"{rule_id}.{field} 为空 —— 写入时会丢失 ADR-025 字段"


# ------------------------------------------------- library police / military


def test_library_police_and_military_are_held_for_want_of_a_legal_basis(by_id, plan):
    """The library notice excepts 军警犬; 第二十三条 excepts only 导盲犬. An
    operator's sentence does not create a legal allowance."""
    for rule_id in ("lib-sd-op-military", "lib-sd-op-police"):
        row = by_id[rule_id]
        assert row["rule_layer"] == "OPERATOR_POLICY", rule_id
        assert row["proposed_decision"] == "RECOMMEND_HOLD", rule_id
        assert row["proposed_reason"] == "LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED", rule_id
        # the evidence is kept — only the *allowance* is refused
        assert row["issuer"] and "上海图书馆" in row["issuer"]
        assert row["quoted_fragment"], "运营方证据必须保留"
        # and its binding is the operator's own base, never the statute
        bound = {b["rule_id"] for b in plan[rule_id]["bases"]}
        assert bound == {"lib-pets-op"}, bound
        assert plan[rule_id]["executable"] is False


def test_library_guide_dog_carve_out_survives_because_the_law_also_excepts_it(by_id, plan):
    """The same notice, the same operator base — but 导盲犬 has a statutory
    proviso, so this one may stand."""
    row = by_id["lib-sd-op-guide"]
    assert row["proposed_decision"] == "RECOMMEND_APPROVE"
    assert row["proposed_reason"] == "EVIDENCE_TRACEABLE"
    assert plan["lib-sd-op-guide"]["executable"] is True


def test_packet_reports_a_zero_cross_layer_count():
    packet = PACKET.read_text(encoding="utf-8")
    section = packet.split("### 1.7 RuleException")[1].split("**发布顺序")[0]
    assert "| 跨层绑定（cross-layer override，实际绑定表内） | **0** |" in section
    assert "| HOLD 基础规则收到「可执行例外」 | **0** |" in section
    assert "| Legal / Operator 例外分离 | **PASS** |" in section


# ------------------------------------------------------------- resolver acts


def _resolve(rules, exceptions, *, animal="dog", service_role="none", declared_role=None):
    from app.rulespec.v05_resolver import resolve

    return resolve(
        legal=[r for r in rules if r.rule_layer == "LEGAL"],
        guidance=[r for r in rules if r.rule_layer == "REGULATORY_GUIDANCE"],
        template_rules=[],
        operator_rules=[r for r in rules if r.rule_layer == "OPERATOR_POLICY"],
        event_rules=[],
        animal=animal,
        service_role=service_role,
        action="enter",
        zone_id="indoor",
        now=NOW,
        exceptions=list(exceptions),
        declared_role=declared_role,
    )


def _rules_and_exceptions():
    from app.rulespec.v05_resolver import LayeredException, LayeredRule

    legal_ban = LayeredRule(
        id="lib-legal-dog",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer="LEGAL",
        origin="legal",
        zone_id="indoor",
        source_id="src-statute",
        mandatory_level="mandatory",
    )
    operator_ban = LayeredRule(
        id="lib-pets-op",
        animal_scope="ordinary_pet",
        action="enter",
        effect="prohibited",
        rule_layer="OPERATOR_POLICY",
        origin="operator_direct",
        zone_id="indoor",
        source_id="src-operator",
    )
    # the operator's own carve-out, bound (correctly) to the OPERATOR base
    operator_carve_out = LayeredException(
        id="exc-lib-guide-op",
        rule_id="lib-pets-op",
        animal_scope="guide_dog",
        effect="allowed",
        source_id="src-operator",
        subject_scope_normalized="guide_dog",
        normalization_type="exact",
        normative_effect="exempt_from_prohibition",
    )
    return [legal_ban, operator_ban], operator_carve_out


def test_operator_exception_cannot_override_higher_layer_legal_prohibition():
    """Even correctly bound, the operator carve-out only replaces its own layer's
    base rule — the mandatory statutory prohibition still governs."""
    rules, operator_carve_out = _rules_and_exceptions()
    for service_role in ("working",):
        rs = _resolve(rules, [operator_carve_out], animal="dog", service_role=service_role)
        assert rs.effect == "prohibited", "运营方豁免不得放宽 LEGAL 层禁令（原则 B/D）"
    # and explicitly for a declared guide dog
    rs = _resolve(rules, [operator_carve_out], animal="dog", declared_role="guide_dog")
    assert rs.effect == "prohibited"


def test_legal_exception_can_override_its_own_legal_base_rule():
    """The mirror case: a carve-out bound to its own legal base does exempt —
    that is the only way a legal prohibition is ever relaxed."""
    from app.rulespec.v05_resolver import LayeredException

    rules, _ = _rules_and_exceptions()
    legal_exception = LayeredException(
        id="exc-lib-guide-legal",
        rule_id="lib-legal-dog",
        animal_scope="guide_dog",
        effect="allowed",
        source_id="src-statute",
        subject_scope_normalized="guide_dog",
        normalization_type="exact",
        normative_effect="exempt_from_prohibition",
    )
    rs = _resolve(rules, [legal_exception], animal="dog", declared_role="guide_dog")
    assert rs.effect == "allowed"
    assert "exc-lib-guide-legal" in rs.applied_exceptions


def test_resolver_still_returns_correct_ordinary_dog_and_guide_dog_results():
    """The full picture: ordinary dogs blocked by both layers, guide dogs exempted
    by the legal proviso only, and the operator carve-out never standing in for
    it."""
    from app.rulespec.v05_resolver import LayeredException

    rules, operator_carve_out = _rules_and_exceptions()
    legal_exception = LayeredException(
        id="exc-lib-guide-legal",
        rule_id="lib-legal-dog",
        animal_scope="guide_dog",
        effect="allowed",
        source_id="src-statute",
        subject_scope_normalized="guide_dog",
        normalization_type="exact",
        normative_effect="exempt_from_prohibition",
    )
    both = [legal_exception, operator_carve_out]

    ordinary = _resolve(rules, both, animal="dog", service_role="none")
    assert ordinary.effect == "prohibited"
    assert ordinary.applied_exceptions == []

    guide = _resolve(rules, both, animal="dog", declared_role="guide_dog")
    assert guide.effect == "allowed"
    assert "exc-lib-guide-legal" in guide.applied_exceptions
