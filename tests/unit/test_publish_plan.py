"""The publication plan: authority, classification, dependencies, refusals.

These tests exist because the dry-run used to be a printout. It read the
register, counted the rows and announced a plan — while (a) planning from the
machine's ``proposed_decision`` rather than the human's ruling, (b) never running
the pre-publish gate, and (c) having no concept of a carve-out, so all 11
``RuleException`` candidates would have been created as ordinary rules.

Each test below pins one of those, in the shape of the assertion that would have
caught it::

    Human > AI            an APPROVED the machine wanted to HOLD publishes;
                          a HOLD the machine wanted to approve does not
    APPROVED != publishable
                          passing the signature is not passing the gate
    HOLD / REJECTED never publish
    RuleException != AccessRule
    base before exception
    LEGAL cannot be relaxed by OPERATOR
    dry-run is deterministic
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "publish_reviewed_r1.py"
REGISTER = REPO / "docs" / "reality_audit" / "review_decisions_r2_final.json"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("publish_reviewed_r1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def register() -> dict:
    return json.loads(REGISTER.read_text(encoding="utf-8"))


def _row(rule_id="r-base", **over):
    row = {
        "candidate_id": f"cand-{rule_id}",
        "rule_id": rule_id,
        "place_key": "place-1",
        "place_name": "测试场所",
        "zone_key": None,
        "zone_name": None,
        "source_key": "src-1",
        "source_id": "source-1",
        "animal_scope": "ordinary_pet",
        "action": "enter",
        "effect": "prohibited",
        "subject_scope_normalized": "ordinary_pet",
        "rule_layer": "OPERATOR_POLICY",
        "mandatory_level": "operator_discretion",
        "final_decision": "APPROVED",
        "reviewer": "huangdi97",
        "reviewed_at": "2026-09-16T19:25:26.093664+08:00",
        "proposed_decision": "RECOMMEND_APPROVE",
        "evidence_strength": "primary_direct",
    }
    row.update(over)
    return row


def _binding(mod, rule_id, bases, layer="LEGAL"):
    return mod.ExceptionBinding(rule_id=rule_id, bases=tuple(bases), layer=layer)


def _plan(mod, rows, *, bindings=None, gate=None, **kw):
    return mod.build_plan(rows, bindings=bindings, gate=gate, **kw)


def _by_rule(plan):
    return {s.rule_id: s for s in plan.steps}


# ---------------------------------------------------------------- Human > AI


def test_ai_recommended_hold_but_human_approved_is_publishable(mod):
    """The reviewer overrules the machine — and the machine does not get a veto."""
    rows = [_row("r-1", proposed_decision="RECOMMEND_HOLD", final_decision="APPROVED")]
    plan = _plan(mod, rows, gate=mod.MappingGate())
    step = _by_rule(plan)["r-1"]
    assert step.publication_type == mod.CREATE_ACCESS_RULE
    assert step.publishable
    assert step.human_overrides_ai is True


def test_ai_recommended_approve_but_human_hold_is_not_publishable(mod):
    rows = [_row("r-1", proposed_decision="RECOMMEND_APPROVE", final_decision="HOLD")]
    plan = _plan(mod, rows, gate=mod.MappingGate())
    step = _by_rule(plan)["r-1"]
    assert step.publication_type == mod.HOLD_NOT_PUBLISHABLE
    assert not step.publishable
    assert step.human_overrides_ai is True


def test_ai_recommended_approve_but_human_rejected_is_not_publishable(mod):
    rows = [_row("r-1", proposed_decision="RECOMMEND_APPROVE", final_decision="REJECTED")]
    plan = _plan(mod, rows, gate=mod.MappingGate())
    step = _by_rule(plan)["r-1"]
    assert step.publication_type == mod.REJECTED_NOT_PUBLISHABLE
    assert not step.publishable


def test_the_machine_proposal_is_never_consulted_for_permission(mod):
    """Every AI opinion pointing at approval, every human ruling refusing it."""
    rows = [
        _row("r-hold", final_decision="HOLD", proposed_decision="RECOMMEND_APPROVE"),
        _row("r-reject", final_decision="REJECTED", proposed_decision="RECOMMEND_APPROVE"),
    ]
    plan = _plan(mod, rows, gate=mod.MappingGate(default=mod.GATE_PASS))
    assert plan.writable == []
    assert plan.summary()["hold_publishable"] == 0
    assert plan.summary()["rejected_publishable"] == 0


def test_unsigned_rows_cannot_be_planned(mod):
    rows = [_row("r-1", final_decision=None)]
    plan = _plan(mod, rows, gate=mod.MappingGate())
    step = _by_rule(plan)["r-1"]
    assert step.publication_type == mod.BLOCKED
    assert not step.publishable


# ------------------------------------------------------- APPROVED != publishable


def test_approved_but_gate_blocked_is_not_publishable(mod):
    """Passing the human review is not passing the gate — two different facts."""
    gate = mod.MappingGate(
        {"r-1": mod.GateOutcome(mod.GATE_BLOCKED, ("证据超过 90 天未核验，须先复核来源",))}
    )
    rows = [_row("r-1")]
    plan = _plan(mod, rows, gate=gate)
    step = _by_rule(plan)["r-1"]
    assert step.human_decision == "APPROVED", "Human Decision 不得因为闸门失败而被改写"
    assert step.publication_type == mod.BLOCKED
    assert not step.publishable
    assert step.blocked_reasons == ("证据超过 90 天未核验，须先复核来源",)
    assert plan.summary()["prepublish_blocked"] == 1


@pytest.mark.parametrize(
    "code",
    [
        "evidence_not_traceable",
        "place_match_missing",
        "schema_unsupported",
        "unresolved_conflict",
        "evidence_stale",
        "lead_only_source_not_publishable",
    ],
)
def test_every_gate_failure_blocks_with_its_own_reason(mod, code):
    gate = mod.MappingGate({"r-1": mod.GateOutcome(mod.GATE_BLOCKED, (f"gate:{code}",))})
    plan = _plan(mod, [_row("r-1")], gate=gate)
    step = _by_rule(plan)["r-1"]
    assert step.publication_type == mod.BLOCKED
    assert step.gate_reasons == (f"gate:{code}",)


def test_a_gate_that_did_not_run_is_never_reported_as_pass(mod):
    """NOT_RUN is its own state: an offline dry-run must not look like a green gate."""
    plan = _plan(mod, [_row("r-1")], gate=mod.NullGate())
    step = _by_rule(plan)["r-1"]
    assert step.gate_status == mod.GATE_NOT_RUN
    assert plan.gate_ran is False
    assert plan.summary()["prepublish_pass"] == 0
    assert plan.summary()["prepublish_evaluated"] == 0


def test_no_gate_at_all_also_reports_not_run(mod):
    plan = _plan(mod, [_row("r-1")])
    assert _by_rule(plan)["r-1"].gate_status == mod.GATE_NOT_RUN
    assert plan.gate_ran is False


# ------------------------------------------------- RuleException is not an AccessRule


def test_an_exception_candidate_is_not_planned_as_an_access_rule(mod):
    bindings = {"r-exc": _binding(mod, "r-exc", ["r-base"], layer="OPERATOR_POLICY")}
    rows = [
        _row("r-base", rule_layer="OPERATOR_POLICY"),
        _row("r-exc", rule_layer="OPERATOR_POLICY", animal_scope="service_dog"),
    ]
    plan = _plan(mod, rows, bindings=bindings, gate=mod.MappingGate())
    steps = _by_rule(plan)
    assert steps["r-base"].publication_type == mod.CREATE_ACCESS_RULE
    assert steps["r-exc"].publication_type == mod.CREATE_RULE_EXCEPTION
    assert steps["r-exc"].depends_on == ("r-base",)
    assert plan.summary()["access_rule_create_count"] == 1
    assert plan.summary()["rule_exception_create_count"] == 1


def test_base_is_planned_before_its_exception(mod):
    bindings = {"r-exc": _binding(mod, "r-exc", ["r-base"], layer="OPERATOR_POLICY")}
    rows = [
        # the exception is listed FIRST; the plan must still publish the base first
        _row("r-exc", rule_layer="OPERATOR_POLICY"),
        _row("r-base", rule_layer="OPERATOR_POLICY"),
    ]
    plan = _plan(mod, rows, bindings=bindings, gate=mod.MappingGate())
    writable = [s.rule_id for s in plan.writable]
    assert writable == ["r-base", "r-exc"]
    assert _by_rule(plan)["r-exc"].order > _by_rule(plan)["r-base"].order


def test_exception_with_a_missing_base_is_blocked(mod):
    bindings = {"r-exc": _binding(mod, "r-exc", ["r-absent"], layer="LEGAL")}
    rows = [_row("r-exc", rule_layer="LEGAL")]
    plan = _plan(mod, rows, bindings=bindings, gate=mod.MappingGate())
    step = _by_rule(plan)["r-exc"]
    assert step.publication_type == mod.BLOCKED
    assert any("r-absent" in reason for reason in step.blocked_reasons)


def test_exception_is_blocked_when_its_base_is_blocked(mod):
    """A blocked base must not be able to smuggle its carve-out into the plan."""
    bindings = {"r-exc": _binding(mod, "r-exc", ["r-base"], layer="LEGAL")}
    gate = mod.MappingGate({"r-base": mod.GateOutcome(mod.GATE_BLOCKED, ("证据不可追溯",))})
    rows = [
        _row("r-base", rule_layer="LEGAL", mandatory_level="mandatory"),
        _row("r-exc", rule_layer="LEGAL", mandatory_level="mandatory"),
    ]
    plan = _plan(mod, rows, bindings=bindings, gate=gate)
    step = _by_rule(plan)["r-exc"]
    assert step.publication_type == mod.BLOCKED
    assert any("不可发布" in reason for reason in step.blocked_reasons)
    assert plan.summary()["rule_exception_create_count"] == 0


def test_exception_whose_base_is_held_is_blocked(mod):
    """§8 verbatim: an approved carve-out must not ride in on an approved base
    when the base is fine but the carve-out's own human ruling is HOLD — and the
    reverse: a HOLD base must not be resurrected by an approved carve-out."""
    bindings = {"r-exc": _binding(mod, "r-exc", ["r-base"], layer="OPERATOR_POLICY")}
    rows = [
        _row("r-base", rule_layer="OPERATOR_POLICY", final_decision="HOLD"),
        _row("r-exc", rule_layer="OPERATOR_POLICY", final_decision="APPROVED"),
    ]
    plan = _plan(mod, rows, bindings=bindings, gate=mod.MappingGate())
    assert _by_rule(plan)["r-exc"].publication_type == mod.BLOCKED
    assert plan.summary()["rule_exception_create_count"] == 0
    assert plan.summary()["hold_publishable"] == 0


def test_library_style_hold_carve_outs_never_enter_the_plan(mod):
    """上海图书馆 军警犬: HOLD. The approved operator base must not drag them in."""
    bindings = {
        "lib-sd-op-military": _binding(
            mod, "lib-sd-op-military", ["lib-pets-op"], layer="OPERATOR_POLICY"
        ),
        "lib-sd-op-police": _binding(
            mod, "lib-sd-op-police", ["lib-pets-op"], layer="OPERATOR_POLICY"
        ),
    }
    rows = [
        _row("lib-pets-op", rule_layer="OPERATOR_POLICY", final_decision="APPROVED"),
        _row("lib-sd-op-military", rule_layer="OPERATOR_POLICY", final_decision="HOLD"),
        _row("lib-sd-op-police", rule_layer="OPERATOR_POLICY", final_decision="HOLD"),
    ]
    plan = _plan(mod, rows, bindings=bindings, gate=mod.MappingGate())
    assert [s.rule_id for s in plan.writable] == ["lib-pets-op"]
    assert plan.summary()["hold_publishable"] == 0


# ------------------------------------------------------- layer closure (§8)


def test_a_cross_layer_binding_is_refused_by_the_plan(mod):
    """LEGAL base + OPERATOR carve-out would let an operator out-vote a statute."""
    bindings = {"r-op": _binding(mod, "r-op", ["r-legal"], layer="OPERATOR_POLICY")}
    rows = [
        _row("r-legal", rule_layer="LEGAL", mandatory_level="mandatory"),
        _row("r-op", rule_layer="OPERATOR_POLICY", animal_scope="service_dog"),
    ]
    plan = _plan(mod, rows, bindings=bindings, gate=mod.MappingGate())
    rows_by_rule = {r["rule_id"]: r for r in rows}
    integrity = mod.plan_integrity(plan, rows_by_rule=rows_by_rule)
    assert integrity["CROSS_LAYER_EXCEPTION"] >= 1
    assert integrity["details"]["cross_layer_exception"]


def test_a_same_layer_operator_carve_out_is_accepted(mod):
    bindings = {"r-op": _binding(mod, "r-op", ["r-base"], layer="OPERATOR_POLICY")}
    rows = [
        _row("r-base", rule_layer="OPERATOR_POLICY"),
        _row("r-op", rule_layer="OPERATOR_POLICY", animal_scope="service_dog"),
    ]
    plan = _plan(mod, rows, bindings=bindings, gate=mod.MappingGate())
    integrity = mod.plan_integrity(plan, rows_by_rule={r["rule_id"]: r for r in rows})
    assert integrity["CROSS_LAYER_EXCEPTION"] == 0
    assert _by_rule(plan)["r-op"].publication_type == mod.CREATE_RULE_EXCEPTION


def test_the_register_binding_table_is_layer_closed(register):
    """The artefact the plan trusts must itself be closed under same-layer."""
    spec = importlib.util.spec_from_file_location("publish_reviewed_r1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.binding_closure_problems(register) == []


def test_bindings_come_from_the_register_not_a_hardcoded_id_list(mod, register):
    """Every carve-out in the plan is one the register's metadata names.

    If a future batch adds a carve-out, it is recognised because it carries
    binding metadata — not because someone remembered to add its rule_id here.
    """
    bindings = mod.canonical_exception_bindings(register)
    expected = {
        str(e["rule_id"]) for e in register["exception_plan"] if e.get("mode") == "rule_exception"
    }
    assert set(bindings) == expected
    assert len(bindings) >= 11
    for binding in bindings.values():
        assert binding.bases, f"{binding.rule_id} 没有同层 base"
        assert binding.layer


# ------------------------------------------------------- refusals in the integrity set


def test_self_supersede_is_detected(mod):
    step = mod.PlanStep(
        order=1,
        candidate_id="c-1",
        rule_id="r-1",
        place_name="p",
        zone_name=None,
        layer="LEGAL",
        mandatory_level="mandatory",
        human_decision="APPROVED",
        proposed_decision="RECOMMEND_APPROVE",
        human_overrides_ai=False,
        publication_type=mod.CREATE_ACCESS_RULE,
    )
    assert mod.self_supersede_violations([step]) == []
    assert (
        mod.self_supersede_violations([step], created_ids=["r-1"]) == []
    )  # supersedes is empty here
    step.supersedes = ("r-1",)
    problems = mod.self_supersede_violations([step])
    assert problems and "把自己列为 supersedes 目标" in problems[0]
    step.supersedes = ("r-9",)
    problems = mod.self_supersede_violations([step], created_ids=["r-9"])
    assert problems and "本批正在创建的规则" in problems[0]


def test_duplicate_publication_plan_is_detected(mod):
    """Two steps writing one identity is a duplicate, not two publications.

    Distinct places are legitimately distinct; the same (place, source, scope,
    action, layer, effect) twice is not.
    """
    rows = [_row("r-1"), _row("r-2", place_key="place-2")]
    plan = _plan(mod, rows, gate=mod.MappingGate())
    rows_by_rule = {r["rule_id"]: r for r in rows}
    assert mod.duplicate_plan_violations(plan.steps, rows_by_rule) == []

    rows_by_rule["r-2"] = dict(rows_by_rule["r-1"], rule_id="r-2")
    problems = mod.duplicate_plan_violations(plan.steps, rows_by_rule)
    assert problems and "同一写入目标被计划多次" in problems[0]


def test_the_same_candidate_twice_is_a_duplicate(mod):
    rows = [_row("r-1"), _row("r-2", place_key="place-2")]
    plan = _plan(mod, rows, gate=mod.MappingGate())
    for step in plan.steps:
        step.candidate_id = "cand-r-1"
    problems = mod.duplicate_plan_violations(plan.steps, {r["rule_id"]: r for r in rows})
    assert problems and "在计划中出现 2 次" in problems[0]


def test_supersession_cycle_is_detected(mod):
    assert mod.supersession_cycles({}) == []
    assert mod.supersession_cycles({"a": "b", "b": "c"}) == []
    cycles = mod.supersession_cycles({"a": "b", "b": "a"})
    assert cycles, "a -> b -> a 必须被检出"


def test_plan_integrity_reports_all_zero_for_a_clean_plan(mod):
    rows = [_row("r-1"), _row("r-2", place_key="place-2")]
    plan = _plan(mod, rows, gate=mod.MappingGate())
    integrity = mod.plan_integrity(plan, rows_by_rule={r["rule_id"]: r for r in rows})
    assert integrity["SELF_SUPERSEDE"] == 0
    assert integrity["DUPLICATE_PUBLICATION_PLAN"] == 0
    assert integrity["CROSS_LAYER_EXCEPTION"] == 0
    assert integrity["SUPERSESSION_CYCLE"] == 0


# ------------------------------------------------------- determinism


def test_the_plan_is_deterministic(mod):
    rows = [_row("r-z"), _row("r-a"), _row("r-m")]
    first = _plan(mod, rows, gate=mod.MappingGate())
    second = _plan(mod, list(reversed(rows)), gate=mod.MappingGate())
    assert [(s.order, s.rule_id) for s in first.steps] == [
        (s.order, s.rule_id) for s in second.steps
    ]


def test_the_real_register_plans_deterministically(mod, register):
    first = _plan(
        mod,
        [dict(r) for r in register["rows"]],
        bindings=mod.canonical_exception_bindings(register),
        gate=mod.MappingGate(),
    )
    second = _plan(
        mod,
        [dict(r) for r in register["rows"]],
        bindings=mod.canonical_exception_bindings(register),
        gate=mod.MappingGate(),
    )
    assert [vars(s) for s in first.steps] == [vars(s) for s in second.steps]


# ------------------------------------------------------- the real register, end to end


def test_the_signed_register_plans_twelve_rules_and_eleven_carve_outs(mod, register):
    plan = _plan(
        mod,
        [dict(r) for r in register["rows"]],
        bindings=mod.canonical_exception_bindings(register),
        gate=mod.MappingGate(),
        revision=register["revision"],
        reviewer="huangdi97",
    )
    summary = plan.summary()
    assert summary["total"] == 37
    assert summary["human_decisions"] == {
        "APPROVED": 23,
        "APPROVED_WITH_NOTE": 0,
        "HOLD": 9,
        "REJECTED": 5,
    }
    assert summary["access_rule_create_count"] + summary["rule_exception_create_count"] == 23
    assert summary["rule_exception_create_count"] == 11
    assert summary["hold_publishable"] == 0
    assert summary["rejected_publishable"] == 0
    assert summary["blocked_count"] == 0


def test_the_signed_register_has_no_integrity_violations(mod, register):
    plan = _plan(
        mod,
        [dict(r) for r in register["rows"]],
        bindings=mod.canonical_exception_bindings(register),
        gate=mod.MappingGate(),
    )
    integrity = mod.plan_integrity(plan, rows_by_rule={r["rule_id"]: r for r in register["rows"]})
    assert integrity["SELF_SUPERSEDE"] == 0
    assert integrity["DUPLICATE_PUBLICATION_PLAN"] == 0
    assert integrity["CROSS_LAYER_EXCEPTION"] == 0
    assert integrity["SUPERSESSION_CYCLE"] == 0


def test_every_carve_out_in_the_real_plan_depends_on_an_earlier_step(mod, register):
    plan = _plan(
        mod,
        [dict(r) for r in register["rows"]],
        bindings=mod.canonical_exception_bindings(register),
        gate=mod.MappingGate(),
    )
    order = {s.rule_id: s.order for s in plan.steps}
    for step in plan.of(mod.CREATE_RULE_EXCEPTION):
        assert step.depends_on, step.rule_id
        for base in step.depends_on:
            assert base in order, f"{step.rule_id} 的 base {base} 不在计划中"
            assert order[base] < step.order, f"{step.rule_id} 排在 base {base} 之前"


def test_no_hold_or_rejected_candidate_is_reachable_from_the_write_path(mod, register):
    """Belt and braces over the execution entry point itself."""
    plan = _plan(
        mod,
        [dict(r) for r in register["rows"]],
        bindings=mod.canonical_exception_bindings(register),
        gate=mod.MappingGate(),
    )
    writable = {s.rule_id for s in plan.writable}
    refused = {
        r["rule_id"] for r in register["rows"] if r["final_decision"] in ("HOLD", "REJECTED")
    }
    assert writable & refused == set()
