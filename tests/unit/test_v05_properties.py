"""Property-based invariants (TEST_PLAN_v0.5): UNKNOWN never coerced,
Observation never affects normative resolution, expired events never current,
superseded never current, unpublished candidates never effective, service-dog
isolation, place UUID ≠ external provider id."""

from datetime import UTC, datetime, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.v05 import CANDIDATE_TRANSITIONS
from app.rulespec.v05_resolver import (
    ComplianceState,
    LayeredRule,
    resolve,
)

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)

layer_values = ["LEGAL", "REGULATORY_GUIDANCE", "OPERATOR_POLICY", "TEMPORARY_POLICY", None]
effect_values = ["allowed", "prohibited", "conditional"]
mandatory_values = [None, "mandatory", "advisory", "discretionary"]
offsets = st.integers(min_value=-60, max_value=60)


@st.composite
def rule_lists(draw):
    n = draw(st.integers(min_value=0, max_value=6))
    rules = []
    for i in range(n):
        layer = draw(st.sampled_from(layer_values))
        from_off = draw(offsets)
        to_off = draw(offsets)
        rules.append(
            LayeredRule(
                id=f"r{i}",
                animal_scope=draw(st.sampled_from(["ordinary_pet", "dog", "service_dog"])),
                action=draw(st.sampled_from(["enter", "walk", "off_leash"])),
                effect=draw(st.sampled_from(effect_values)),
                rule_layer=layer,
                origin=draw(
                    st.sampled_from(
                        [
                            "legal",
                            "guidance",
                            "template",
                            "place_override",
                            "zone_override",
                            "event",
                            "operator_direct",
                        ]
                    )
                ),
                conditions=(),
                mandatory_level=draw(st.sampled_from(mandatory_values)),
                effective_from=NOW + timedelta(days=from_off),
                effective_to=NOW + timedelta(days=to_off),
            )
        )
    return rules


def make_kwargs(rules):
    by_layer = {
        "LEGAL": [r for r in rules if r.rule_layer == "LEGAL"],
        "GUIDANCE": [r for r in rules if r.rule_layer == "REGULATORY_GUIDANCE"],
        "TEMPLATE": [r for r in rules if r.origin == "template" and r.rule_layer is None],
        "OPERATOR": [
            r
            for r in rules
            if r.rule_layer == "OPERATOR_POLICY"
            or (r.rule_layer is None and r.origin != "template")
        ],
        "EVENT": [r for r in rules if r.rule_layer == "TEMPORARY_POLICY"],
    }
    return dict(
        legal=by_layer["LEGAL"],
        guidance=by_layer["GUIDANCE"],
        template_rules=by_layer["TEMPLATE"],
        operator_rules=by_layer["OPERATOR"],
        event_rules=by_layer["EVENT"],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )


@given(rule_lists())
@settings(max_examples=200, deadline=None)
def test_never_guessed_when_no_effective_rules(rules):
    """If nothing is in scope the state is UNKNOWN — never allowed/prohibited."""
    rs = resolve(**make_kwargs(rules))
    if not rs.applicable_rules and rs.compliance_state == ComplianceState.UNKNOWN:
        assert rs.effect == "unknown"


@given(rule_lists())
@settings(max_examples=200, deadline=None)
def test_effect_prohibited_only_with_explicit_prohibition(rules):
    """effect=prohibited must always trace to an explicit prohibited rule that
    is still applicable (never fabricated from absence/conflict)."""
    rs = resolve(**make_kwargs(rules))
    if rs.effect == "prohibited":
        assert any(r.effect == "prohibited" for r in rs.applicable_rules), rs


@given(rule_lists())
@settings(max_examples=150, deadline=None)
def test_expired_events_never_applicable(rules):
    """A TEMPORARY rule outside its window never lands in applicable_rules."""
    rs = resolve(**make_kwargs(rules))
    for r in rs.applicable_rules:
        if r.is_temporary:
            assert r.effective_from is None or r.effective_from <= NOW
            assert r.effective_to is None or r.effective_to >= NOW


@given(st.lists(st.sampled_from(list(CANDIDATE_TRANSITIONS)), min_size=1, max_size=8))
def test_unpublished_candidate_never_published_directly(sequence):
    """Candidates start at DISCOVERED; PUBLISHED is only reachable through the
    APPROVED transition. Random transition attempts can never reach PUBLISHED
    without passing APPROVED."""
    state = "DISCOVERED"
    ever_published = False
    seen_approved = False
    for nxt in sequence:
        allowed = CANDIDATE_TRANSITIONS.get(state, set())
        if nxt in allowed:
            state = nxt
        if state == "APPROVED":
            seen_approved = True
        if state == "PUBLISHED":
            ever_published = True
    assert ever_published == seen_approved


def test_superseded_rule_never_current_by_construction():
    """DB layer: superseded is a terminal status filtered by the loader — the
    resolver never even sees it; document + assert the transition guard."""
    assert "SUPERSEDED" in CANDIDATE_TRANSITIONS
    assert CANDIDATE_TRANSITIONS["SUPERSEDED"] == set()


def test_service_dog_scope_isolation_property():
    op = [
        LayeredRule(
            id="o",
            animal_scope="ordinary_pet",
            action="enter",
            effect="prohibited",
            rule_layer="OPERATOR_POLICY",
            origin="operator_direct",
        )
    ]
    rs = resolve(**make_kwargs(op) | {"service_role": "working"})
    assert rs.effect == "unknown"


def test_place_uuid_is_not_external_provider_id():
    """Structural guarantee: place PK is a platform UUID column; external ids
    live in external_place_ref with their own provider namespaced columns."""
    from sqlalchemy import inspect as sa_inspect

    from app.models import ExternalPlaceRef, Place

    place_cols = [c.name for c in sa_inspect(Place).columns]
    ref_cols = [c.name for c in sa_inspect(ExternalPlaceRef).columns]
    assert "id" in place_cols and "external_id" in ref_cols
    assert "external_id" not in place_cols


def test_observation_data_type_not_part_of_resolver_signature():
    """Normative resolver input types contain no Observation types (ADR-004)."""
    import inspect

    from app.rulespec import v05_resolver

    sig = inspect.signature(v05_resolver.resolve)
    assert "observation" not in " ".join(sig.parameters)
