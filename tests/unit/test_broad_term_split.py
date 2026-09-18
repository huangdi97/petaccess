"""Regression locks for the broad-source-term decomposition (Phase B).

Two Wave01 rows stored a source term broader than any single scope:

    「动物」               (上海动物园)        → stored as other/exact
    「动物（导盲犬除外）」 (上海迪士尼乐园)    → stored as other/exact

``other`` covers exactly ``{other_pet}``. The consequence of that narrowing is
*silence*, not a wrong answer: a dog query against an ``other``-scoped base
matches nothing, so the platform reports ``unknown`` for a venue whose own
notice prohibits animals.

These tests pin three things: the decomposition is declared and well-formed, the
compatibility gate accepts split rows (an equivalence test would refuse them
all), and the resolver contrast is real — the fix turns silence into the
prohibition the source states, and makes the Disney guide-dog carve-out
reachable instead of inert.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.models.enums import AnimalRole
from app.rulespec.animal_scope import SCOPE_SUBJECTS
from app.rulespec.broad_term_split import (
    BROAD_TERM_SPLITS,
    declared_split,
    propose_split_rows,
    split_subjects,
    validate_split_group,
    validate_split_row,
)
from app.rulespec.source_scope_semantics import (
    validate_source_scope_semantic_compatibility,
)
from app.rulespec.v05_resolver import (
    LayeredException,
    LayeredRule,
    resolve,
)

NOW = datetime.now(UTC)
DOG = AnimalRole.ORDINARY_DOG.value
GUIDE = AnimalRole.GUIDE_DOG.value


def base_rule(*, scope: str, norm: str, source_scope: str = "动物", eid: str = "r1") -> LayeredRule:
    return LayeredRule(
        id=eid,
        animal_scope=scope,
        action="enter",
        effect="prohibited",
        rule_layer="OPERATOR_POLICY",
        origin="operator_direct",
        source_id="s1",
        effective_from=None,
        effective_to=None,
        mandatory_level="operator_discretion",
        zone_id=None,
        source_scope_exact=source_scope,
        subject_scope_normalized=scope,
        normalization_type=norm,
    )


def carve_out(base_id: str, subject: str = GUIDE) -> LayeredException:
    return LayeredException(
        id="e1",
        rule_id=base_id,
        animal_scope="service_dog",
        effect="conditional",
        source_id="s1",
        status="current",
        effective_from=None,
        effective_to=None,
        source_scope_exact="导盲犬",
        subject_scope_normalized=subject,
        normalization_type="exact",
    )


def effect_for(
    rules: list[LayeredRule],
    exceptions: list[LayeredException],
    *,
    animal: str,
    declared_role: str | None = None,
):
    res = resolve(
        legal=[],
        guidance=[],
        template_rules=[],
        operator_rules=rules,
        event_rules=[],
        animal=animal,
        service_role="working" if declared_role else "none",
        action="enter",
        zone_id=None,
        now=NOW,
        exceptions=exceptions,
        declared_role=declared_role,
    )
    return res


# --------------------------------------------------------------------------
# 1. the declaration itself
# --------------------------------------------------------------------------


@pytest.mark.parametrize("term", ["动物", "动物（导盲犬除外）"])
def test_broad_terms_have_a_declared_split(term):
    split = declared_split(term)
    assert split is not None, f"{term} must be declared, or the remodel cannot proceed"
    assert split.members


def test_undeclared_term_is_not_assumed_to_need_no_split():
    """Fail closed: an unknown term yields no declaration and no proposal."""
    assert declared_split("宠物们") is None
    assert propose_split_rows("宠物们") == []


def test_split_members_are_pairwise_disjoint():
    """Overlapping atoms would double-count a subject and break exhaustiveness."""
    for term, split in BROAD_TERM_SPLITS.items():
        seen: set[str] = set()
        for member in split.members:
            subjects = set(SCOPE_SUBJECTS[member])
            assert not (subjects & seen), f"{term}: {member} overlaps another atom"
            seen |= subjects


def test_split_covers_the_whole_modelled_animal_domain():
    """dog roles + ordinary_cat + other_pet = every subject the model knows."""
    expected = (
        set(SCOPE_SUBJECTS["dog"]) | set(SCOPE_SUBJECTS["cat"]) | set(SCOPE_SUBJECTS["other"])
    )
    for term in ("动物", "动物（导盲犬除外）"):
        assert split_subjects(declared_split(term)) == expected


# --------------------------------------------------------------------------
# 2. per-row validation
# --------------------------------------------------------------------------


def test_split_row_is_accepted_when_it_is_a_declared_member():
    verdict = validate_split_row("动物", "dog", "compound_term_split")
    assert verdict.ok
    assert set(verdict.declared_members) == {"dog", "cat", "other"}


def test_split_row_marked_exact_is_refused():
    """`exact` claims equivalence; a decomposition is not an equivalence."""
    verdict = validate_split_row("动物", "dog", "exact")
    assert not verdict.ok


def test_split_row_with_a_non_member_scope_is_refused():
    verdict = validate_split_row("动物", "ordinary_pet", "compound_term_split")
    assert not verdict.ok


def test_split_row_for_an_undeclared_term_is_refused():
    verdict = validate_split_row("飞禽走兽", "dog", "compound_term_split")
    assert not verdict.ok


# --------------------------------------------------------------------------
# 3. group completeness — an incomplete split silently drops meaning
# --------------------------------------------------------------------------


def test_incomplete_split_is_refused():
    verdict = validate_split_group("动物", ["cat", "other"])
    assert not verdict.ok
    assert verdict.missing_members == ("dog",)


def test_extra_member_is_refused():
    """A member outside the declared meaning would widen the source."""
    verdict = validate_split_group("动物", ["dog", "cat", "other", "service_dog"])
    assert not verdict.ok
    assert verdict.extra_members == ("service_dog",)


def test_inline_proviso_must_be_modelled():
    """「动物（导盲犬除外）」 without the carve-out states the opposite of the source."""
    incomplete = validate_split_group("动物（导盲犬除外）", ["dog", "cat", "other"])
    assert not incomplete.ok
    assert incomplete.missing_proviso == (GUIDE,)

    complete = validate_split_group(
        "动物（导盲犬除外）", ["dog", "cat", "other"], carve_out_subjects=(GUIDE,)
    )
    assert complete.ok


def test_bare_animal_term_needs_no_proviso():
    """「动物」 carries no exception in the source; none may be implied."""
    assert validate_split_group("动物", ["dog", "cat", "other"]).ok


# --------------------------------------------------------------------------
# 4. the gate must accept split rows (an equivalence test would refuse them all)
# --------------------------------------------------------------------------


def test_gate_rejects_the_current_narrowing_row():
    verdict = validate_source_scope_semantic_compatibility("动物", "other", "exact")
    assert not verdict.compatible
    assert verdict.change == "narrowing"


@pytest.mark.parametrize("member", ["dog", "cat", "other"])
def test_gate_accepts_each_proposed_split_row(member):
    verdict = validate_source_scope_semantic_compatibility(
        "动物（导盲犬除外）", member, "compound_term_split"
    )
    assert verdict.compatible, verdict.reason
    assert verdict.change == "compound_term_split"


def test_gate_still_refuses_a_split_row_that_is_not_a_member():
    verdict = validate_source_scope_semantic_compatibility(
        "动物（导盲犬除外）", "ordinary_pet", "compound_term_split"
    )
    assert not verdict.compatible


# --------------------------------------------------------------------------
# 5. the answer difference the remodel actually buys
# --------------------------------------------------------------------------


def test_narrowed_base_goes_silent_for_a_dog():
    """The defect: an `other` base does not govern dogs, so it says nothing."""
    res = effect_for([base_rule(scope="other", norm="exact")], [], animal="dog")
    assert res.effect == "unknown"
    assert res.applicable_rules == []


def test_split_base_states_the_prohibition_the_source_makes():
    res = effect_for([base_rule(scope="dog", norm="compound_term_split")], [], animal="dog")
    assert res.effect == "prohibited"


def test_disney_carve_out_is_inert_before_the_remodel():
    """The approved carve-out currently fires on nothing — the base never matches."""
    base = base_rule(scope="other", norm="exact", source_scope="动物（导盲犬除外）")
    res = effect_for([base], [carve_out(base.id)], animal="dog", declared_role=GUIDE)
    assert res.effect == "unknown"
    assert list(res.applied_exceptions) == []


def test_disney_carve_out_fires_after_the_remodel():
    """Same carve-out, reachable base: guide dog exempt, base suppressed."""
    base = base_rule(scope="dog", norm="compound_term_split", source_scope="动物（导盲犬除外）")
    res = effect_for([base], [carve_out(base.id)], animal="dog", declared_role=GUIDE)
    assert res.effect != "prohibited"
    assert list(res.applied_exceptions) == ["e1"]


def test_remodel_does_not_widen_the_ordinary_dog_answer():
    """The proviso is narrow: an ordinary dog stays prohibited throughout."""
    base = base_rule(scope="dog", norm="compound_term_split", source_scope="动物（导盲犬除外）")
    res = effect_for([base], [carve_out(base.id)], animal="dog")
    assert res.effect == "prohibited"


def test_zoo_remodel_does_not_invent_a_guide_dog_proviso():
    """「动物」 has no exception in the source; the model must not add one."""
    base = base_rule(scope="dog", norm="compound_term_split", source_scope="动物")
    res = effect_for([base], [], animal="dog", declared_role=GUIDE)
    assert res.effect == "prohibited"
