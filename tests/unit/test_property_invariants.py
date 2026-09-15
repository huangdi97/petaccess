"""Property-based invariants (§24).

These are properties, not examples: they must hold for *any* generated input.
They target the drift that is invisible in a hand-written fixture — a resolver
whose answer depends on list ordering, a normalisation that is not idempotent,
a serialisation that loses a field on the way back.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.enums import MandatoryLevel, normalize_mandatory_level
from app.rulespec import petaccessjson
from app.rulespec.v05_resolver import (
    LayeredException,
    LayeredRule,
    RuleLayer,
    resolve,
)

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)

EFFECTS = ("allowed", "prohibited", "conditional")
LAYERS = tuple(layer.value for layer in RuleLayer)


def _rule(id_, effect, layer, subject=None):
    return LayeredRule(
        id=id_,
        animal_scope="dog",
        action="enter",
        effect=effect,
        rule_layer=layer,
        origin="operator_direct",
        subject_scope_normalized=subject or "ordinary_dog",
        normalization_type="exact",
    )


@st.composite
def rule_lists(draw):
    n = draw(st.integers(min_value=1, max_value=4))
    return [
        _rule(f"r{i}", draw(st.sampled_from(EFFECTS)), draw(st.sampled_from(LAYERS)))
        for i in range(n)
    ]


def _resolve_all(rules, **extra):
    kw = dict(
        legal=[r for r in rules if r.rule_layer == RuleLayer.LEGAL.value],
        guidance=[r for r in rules if r.rule_layer == RuleLayer.REGULATORY_GUIDANCE.value],
        template_rules=[],
        operator_rules=[r for r in rules if r.rule_layer == RuleLayer.OPERATOR_POLICY.value],
        event_rules=[r for r in rules if r.rule_layer == RuleLayer.TEMPORARY_POLICY.value],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )
    kw.update(extra)
    return resolve(**kw)


@settings(max_examples=60, deadline=None)
@given(rule_lists())
def test_resolution_is_independent_of_input_ordering(rules):
    """A permutation of the input must not change the answer."""
    baseline = _resolve_all(rules)
    for permutation in itertools.islice(itertools.permutations(rules), 4):
        other = _resolve_all(list(permutation))
        assert other.effect == baseline.effect
        assert sorted(r.id for r in other.applicable_rules) == sorted(
            r.id for r in baseline.applicable_rules
        )
        assert other.compliance_state == baseline.compliance_state


@settings(max_examples=40, deadline=None)
@given(rule_lists())
def test_applying_the_same_exception_twice_is_idempotent(rules):
    base_rule = LayeredRule(
        id="B",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer=RuleLayer.OPERATOR_POLICY.value,
        origin="operator_direct",
        subject_scope_normalized="dog",
        normalization_type="exact",
    )
    exc = LayeredException(
        id="E",
        rule_id="B",
        animal_scope="dog",
        effect="allowed",
        source_id="s1",
        subject_scope_normalized="ordinary_dog",
        normalization_type="exact",
    )
    once = _resolve_all([*rules, base_rule], exceptions=[exc])
    twice = _resolve_all([*rules, base_rule], exceptions=[exc, exc])
    assert once.effect == twice.effect
    assert len(once.applied_exceptions) == len(twice.applied_exceptions)


@settings(max_examples=40, deadline=None)
@given(
    st.one_of(
        st.none(),
        st.sampled_from(sorted({m.value for m in MandatoryLevel} | {"discretionary"})),
        st.text(min_size=1, max_size=12),
    )
)
def test_mandatory_level_normalisation_is_idempotent(value):
    once = normalize_mandatory_level(value)
    assert normalize_mandatory_level(once) == once


@settings(max_examples=40, deadline=None)
@given(
    st.sampled_from(EFFECTS),
    st.sampled_from(LAYERS),
    st.sampled_from(["mandatory", "advisory", "operator_discretion"]),
)
def test_petaccessjson_roundtrip_preserves_every_field(effect, layer, level):
    doc = petaccessjson.dump(
        species="dog",
        role="ordinary_pet",
        place_id="p1",
        zone_id=None,
        action="enter",
        effect=effect,
        rule_layer=layer,
        mandatory_level=level,
        conditions=[{"condition_type": "leash_required"}],
        effective_from="2026-09-01T00:00:00Z",
        source_id="s1",
    )
    loaded = petaccessjson.load(doc)
    assert loaded == doc
    assert loaded["effect"] == effect
    assert loaded["rule_layer"] == layer
    assert loaded["mandatory_level"] == level


@settings(max_examples=40, deadline=None)
@given(st.text(min_size=1, max_size=32))
def test_petaccessjson_rejects_an_unknown_version_without_guessing(version):
    doc = petaccessjson.dump(
        species="dog",
        role="ordinary_pet",
        place_id="p1",
        zone_id=None,
        action="enter",
        effect="allowed",
        rule_layer="OPERATOR_POLICY",
        mandatory_level="advisory",
        source_id="s1",
    )
    doc["petaccessjson_version"] = version
    if version == petaccessjson.PETACCESSJSON_VERSION:
        petaccessjson.load(doc)
    else:
        try:
            petaccessjson.load(doc)
        except petaccessjson.PetAccessJSONError:
            return
        raise AssertionError("an unknown version must be refused, not coerced")


def test_legal_layer_always_declares_its_normative_force():
    """A LEGAL rule without mandatory_level is refused, never defaulted."""
    try:
        petaccessjson.dump(
            species="dog",
            role="ordinary_pet",
            place_id="p1",
            zone_id=None,
            action="enter",
            effect="prohibited",
            rule_layer="LEGAL",
            mandatory_level=None,
            source_id="s1",
        )
    except petaccessjson.PetAccessJSONError:
        return
    raise AssertionError("LEGAL without mandatory_level must be refused (ADR-023)")
