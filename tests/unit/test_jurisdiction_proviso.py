"""Regression locks for the jurisdiction-level statutory proviso (ADR-030).

The mechanism these tests lock is the fix for a specific, measured defect: a new
LEGAL dog prohibition with no per-venue ``rule_exception`` resolved ``prohibited``
for a guide dog, while citing the very statute whose 但书 exempts guide dogs. The
platform was narrower than the law it quoted, with a citation attached.

Each test is a refusal, not a description. The important ones are the contrasts:
a proviso that binds across two different ``source`` rows of one statute, and a
proviso that stays inert on an ``other``-scoped base — because applying *that*
one would turn "this rule says nothing about guide dogs" into "guide dogs are
allowed", which is inventing legal effect.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "services" / "api"))

from app.models.enums import HolderScope  # noqa: E402
from app.rulespec.animal_scope import rule_governs  # noqa: E402
from app.rulespec.guide_dog_safety import (  # noqa: E402
    REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE,
    probe_guide_dog_safety_path,
)
from app.rulespec.holder_scope import HolderContext  # noqa: E402
from app.rulespec.statutory_proviso import (  # noqa: E402
    JURISDICTION_EXCEPTION_INERT,
    BindingMode,
    bind_proviso_to_bases,
    proviso_subjects,
)
from app.rulespec.v05_resolver import (  # noqa: E402
    ComplianceState,
    LayeredException,
    LayeredRule,
    resolve,
)

NOW = datetime(2026, 9, 18, 12, 0, tzinfo=UTC)

# The same statute, two source rows — this is exactly why binding cannot be a
# single source_id. Different venues cite different ones.
STATUTE_A = "f20bdb2c-1ec4-445f-9a2f-a8e587c205a8"  # 公安网转载
STATUTE_B = "a11aff10-9658-478f-8c22-abb73485b7e4"  # 市政府门户全文
MUSEUM_POLICY = "17f4080a-72bf-4603-aff2-01d59e4db367"  # 上博东馆参观须知


def legal_dog_ban(
    rule_id: str,
    source_id: str = STATUTE_A,
    animal_scope: str = "dog",
    subject_scope: str | None = "dog",
    normalization: str = "exact",
    effect: str = "prohibited",
    layer: str = "LEGAL",
) -> LayeredRule:
    return LayeredRule(
        id=rule_id,
        animal_scope=animal_scope,
        action="enter",
        effect=effect,
        rule_layer=layer,
        origin="legal",
        source_id=source_id,
        mandatory_level="mandatory",
        subject_scope_normalized=subject_scope,
        normalization_type=normalization,
    )


def guide_dog_proviso(
    *,
    proviso_id: str = "prov-001",
    binding: str = BindingMode.INSTRUMENT,
    instrument_source_ids: tuple[str, ...] = (STATUTE_A, STATUTE_B),
    applies_to_layer: str | None = "LEGAL",
    applies_to_effects: tuple[str, ...] = ("prohibited",),
    subject_scope: str | None = "guide_dog",
    normalization: str = "exact",
    source_id: str | None = STATUTE_B,
    status: str = "current",
    effect: str = "allowed",
) -> LayeredException:
    return LayeredException(
        id=proviso_id,
        rule_id="",  # instrument-bound: no single base rule is named
        animal_scope="service_dog",
        effect=effect,
        source_id=source_id,
        status=status,
        source_scope_exact="导盲犬",
        subject_scope_normalized=subject_scope,
        normalization_type=normalization,
        normative_effect="exempt_from_prohibition",
        holder_scope="person_with_disability",
        binding=binding,
        instrument_source_ids=instrument_source_ids,
        applies_to_layer=applies_to_layer,
        applies_to_effects=applies_to_effects,
    )


def _resolve(
    bases,
    provisos,
    *,
    animal="dog",
    service_role="working",
    declared_role="guide_dog",
    holder_context=None,
):
    return resolve(
        legal=list(bases),
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal=animal,
        service_role=service_role,
        action="enter",
        zone_id=None,
        now=NOW,
        exceptions=list(provisos),
        declared_role=declared_role,
        holder_context=holder_context,
    )


#: the buts 但书 is 「盲人携带导盲犬」 — the handler the statute actually names.
MATCHING_HOLDER = HolderContext.of(HolderScope.PERSON_WITH_DISABILITY.value)
#: a handler who provably is not (context supplied, but empty).
NON_MATCHING_HOLDER = HolderContext.of()


# ---------------------------------------------------------------------------
# 1. the binding itself
# ---------------------------------------------------------------------------


def test_proviso_binds_both_source_rows_of_one_statute():
    """The defect being fixed: half the venues cite the other source row."""
    bases = [
        legal_dog_ban("r-police", source_id=STATUTE_A),
        legal_dog_ban("r-portal", source_id=STATUTE_B),
    ]
    bound, inert = bind_proviso_to_bases(guide_dog_proviso(), bases)
    assert sorted(bound) == ["r-police", "r-portal"]
    assert inert == []


def test_ordinary_rule_binding_is_the_default():
    """A plain RuleException must not silently become a jurisdiction-wide one."""
    exc = LayeredException(
        id="e1",
        rule_id="r1",
        animal_scope="service_dog",
        effect="allowed",
        source_id=STATUTE_A,
        subject_scope_normalized="guide_dog",
        normalization_type="exact",
    )
    assert exc.binding == BindingMode.RULE
    assert bind_proviso_to_bases(exc, [legal_dog_ban("r1")]) == ([], [])


def test_proviso_does_not_bind_a_different_instrument():
    """A museum's own 参观须知 is not the 条例 — its ban is not exempted."""
    bound, inert = bind_proviso_to_bases(
        guide_dog_proviso(), [legal_dog_ban("r-museum", source_id=MUSEUM_POLICY)]
    )
    assert (bound, inert) == ([], [])


def test_proviso_does_not_bind_operator_policy_layer():
    bound, inert = bind_proviso_to_bases(
        guide_dog_proviso(),
        [legal_dog_ban("r-op", layer="OPERATOR_POLICY", source_id=STATUTE_A)],
    )
    assert (bound, inert) == ([], [])


def test_proviso_does_not_bind_a_conditional_rule():
    bound, inert = bind_proviso_to_bases(
        guide_dog_proviso(), [legal_dog_ban("r-cond", effect="conditional")]
    )
    assert (bound, inert) == ([], [])


def test_empty_instrument_source_ids_binds_nothing():
    """Fail closed: an undeclared instrument is not an instrument."""
    bound, inert = bind_proviso_to_bases(
        guide_dog_proviso(instrument_source_ids=()), [legal_dog_ban("r1")]
    )
    assert (bound, inert) == ([], [])


def test_missing_applies_to_layer_binds_nothing():
    bound, inert = bind_proviso_to_bases(
        guide_dog_proviso(applies_to_layer=None), [legal_dog_ban("r1")]
    )
    assert (bound, inert) == ([], [])


def test_proviso_without_legal_equivalence_governs_nothing():
    """A bare `service_dog` proviso is the ADR-025 widening, not a proviso."""
    assert (
        proviso_subjects("service_dog", "service_dog", "parent_group_for_query_only") == frozenset()
    )


# ---------------------------------------------------------------------------
# 2. inert, never applied — the safety-critical contrast
# ---------------------------------------------------------------------------


def test_other_scoped_base_makes_the_proviso_inert():
    """`other` covers only {other_pet}; it is *silent* about guide dogs."""
    base = legal_dog_ban("r-other", animal_scope="other", subject_scope="other")
    assert not rule_governs(frozenset({"guide_dog"}), "other", "other", "exact")
    bound, inert = bind_proviso_to_bases(guide_dog_proviso(), [base])
    assert bound == []
    assert inert == ["r-other"]


def test_inert_proviso_never_turns_unknown_into_allowed():
    """Applying it would manufacture legal effect. It must stay `unknown`."""
    base = legal_dog_ban("r-other", animal_scope="other", subject_scope="other")
    rs = _resolve([base], [guide_dog_proviso()])
    assert rs.effect == "unknown", rs.explanation_steps
    assert rs.applied_exceptions == []
    assert any(JURISDICTION_EXCEPTION_INERT in s for s in rs.explanation_steps)


def test_reachable_proviso_does_fire():
    """The contrast: a `dog` base *does* govern guide dogs, so it is exempted.

    Fires only with the holder the 但书 names — 「盲人携带导盲犬」. The two
    halves of that condition are tested in ``test_adr030_holder_scope.py``.
    """
    base = legal_dog_ban("r-dog")
    rs = _resolve([base], [guide_dog_proviso()], holder_context=MATCHING_HOLDER)
    assert rs.effect == "allowed", rs.explanation_steps
    assert rs.applied_exceptions == ["prov-001"]
    assert rs.compliance_state == ComplianceState.CONSISTENT


def test_reachable_proviso_is_withheld_without_any_holder_context():
    """No holder context ⇒ CONDITIONAL, never an unconditional allowance.

    Both wrong answers are refusals here: ``allowed`` would apply a condition
    that was never evaluated, and ``prohibited`` would hide a statutory right
    behind a missing input (ADR-031 §7).
    """
    base = legal_dog_ban("r-dog")
    rs = _resolve([base], [guide_dog_proviso()])
    assert rs.effect == "conditional", rs.explanation_steps
    assert rs.applied_exceptions == []
    assert rs.pending_exceptions == ["prov-001"]
    assert rs.missing_inputs == ["holder_scope"]


def test_reachable_proviso_does_not_fire_for_a_non_matching_holder():
    """A handler the statute does not name falls back to the base prohibition."""
    base = legal_dog_ban("r-dog")
    rs = _resolve([base], [guide_dog_proviso()], holder_context=NON_MATCHING_HOLDER)
    assert rs.effect == "prohibited", rs.explanation_steps
    assert rs.applied_exceptions == []


def test_ordinary_dog_still_prohibited_with_the_proviso_live():
    """The proviso exempts guide dogs; it must not relax the ban for everyone."""
    base = legal_dog_ban("r-dog")
    rs = _resolve([base], [guide_dog_proviso()], service_role="none", declared_role=None)
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


def test_hearing_dog_does_not_inherit_the_guide_dog_proviso():
    """declared_role pins the query: ADR-025, no role inheritance."""
    base = legal_dog_ban("r-dog")
    rs = _resolve([base], [guide_dog_proviso()], declared_role="hearing_dog")
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


# ---------------------------------------------------------------------------
# 3. governance: activation is a human act
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", ["proposed", "draft", "superseded"])
def test_unactivated_proviso_never_applies(status):
    base = legal_dog_ban("r-dog")
    rs = _resolve([base], [guide_dog_proviso(status=status)])
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


def test_proviso_without_provenance_never_applies():
    base = legal_dog_ban("r-dog")
    rs = _resolve([base], [guide_dog_proviso(source_id=None)])
    assert rs.effect == "prohibited"


def test_two_conflicting_provisos_force_review_not_a_guess():
    bases = [legal_dog_ban("r-dog")]
    rs = _resolve(
        bases,
        [
            guide_dog_proviso(proviso_id="p-allow", applies_to_effects=("prohibited",)),
            guide_dog_proviso(
                proviso_id="p-cond", effect="conditional", applies_to_effects=("prohibited",)
            ),
        ],
    )
    assert rs.compliance_state == ComplianceState.REVIEW_REQUIRED
    assert rs.effect == "prohibited"


# ---------------------------------------------------------------------------
# 4. the publish gate's path C
# ---------------------------------------------------------------------------


def test_guide_dog_safety_path_c_accepts_an_instrument_bound_proviso():
    base = {
        "rule_id": "r-dog",
        "place_name": "任意商场",
        "animal_scope": "dog",
        "effect": "prohibited",
        "rule_layer": "LEGAL",
        "source_id": STATUTE_A,
        "mandatory_level": "mandatory",
        "subject_scope_normalized": "dog",
        "normalization_type": "exact",
    }
    proviso = {
        "id": "prov-001",
        "rule_id": "",
        "animal_scope": "service_dog",
        "effect": "allowed",
        "source_id": STATUTE_B,
        "status": "current",
        "subject_scope_normalized": "guide_dog",
        "normalization_type": "exact",
        "normative_effect": "exempt_from_prohibition",
        "rule_layer": "LEGAL",
        "binding": BindingMode.INSTRUMENT,
        "instrument_source_ids": [STATUTE_A, STATUTE_B],
        "applies_to_layer": "LEGAL",
        "applies_to_effects": ["prohibited"],
    }
    probe = probe_guide_dog_safety_path(
        base=base, candidate_exceptions=[], jurisdiction_exceptions=[proviso], now=NOW
    )
    assert probe.safe_to_publish, probe.explanation
    assert probe.exception_source == "jurisdiction"
    assert probe.guide_dog_effect == "allowed"


def test_guide_dog_safety_still_blocks_when_no_proviso_exists():
    base = {
        "rule_id": "r-dog",
        "place_name": "任意商场",
        "animal_scope": "dog",
        "effect": "prohibited",
        "rule_layer": "LEGAL",
        "source_id": STATUTE_A,
        "mandatory_level": "mandatory",
        "subject_scope_normalized": "dog",
        "normalization_type": "exact",
    }
    probe = probe_guide_dog_safety_path(base=base, candidate_exceptions=[], now=NOW)
    assert not probe.safe_to_publish
    assert probe.block_reason == REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE


def test_proviso_for_another_instrument_is_not_a_path():
    base = {
        "rule_id": "r-museum",
        "place_name": "博物馆",
        "animal_scope": "dog",
        "effect": "prohibited",
        "rule_layer": "LEGAL",
        "source_id": MUSEUM_POLICY,
        "mandatory_level": "mandatory",
        "subject_scope_normalized": "dog",
        "normalization_type": "exact",
    }
    proviso = {
        "id": "prov-001",
        "rule_id": "",
        "animal_scope": "service_dog",
        "effect": "allowed",
        "source_id": STATUTE_B,
        "status": "current",
        "subject_scope_normalized": "guide_dog",
        "normalization_type": "exact",
        "rule_layer": "LEGAL",
        "binding": BindingMode.INSTRUMENT,
        "instrument_source_ids": [STATUTE_A, STATUTE_B],
        "applies_to_layer": "LEGAL",
        "applies_to_effects": ["prohibited"],
    }
    probe = probe_guide_dog_safety_path(
        base=base, candidate_exceptions=[], jurisdiction_exceptions=[proviso], now=NOW
    )
    assert not probe.safe_to_publish
