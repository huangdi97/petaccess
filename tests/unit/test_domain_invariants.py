"""Domain invariants that must survive every refactor (§8 / §9 / §11).

These tests exist because each invariant below was, at some point, violated by
code that looked reasonable:

* a guide-dog proviso stored as ``service_dog`` silently exempted *every*
  assistance dog (ADR-025);
* 军警犬 was read as "working dogs" and pulled police and military dogs into a
  service-dog bucket (ADR-028);
* ``UNKNOWN`` was rendered as "no rule, so probably fine".

They are deliberately written against the *pure* functions so a failure points
at the domain module rather than at a fixture.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.models.enums import AnimalRole, NormalizationType
from app.rulespec.animal_scope import (
    COMPOUND_TERM_SPLIT_MEANINGS,
    ORDINARY_PET_SUBJECTS,
    SERVICE_DOG_QUERY_ROLES,
    QuerySubject,
    compound_split_is_exhaustive,
    legal_subjects,
    parent_expansion_is_legal,
    query_subjects,
    rule_governs,
)
from app.rulespec.v05_resolver import (
    ComplianceState,
    LayeredException,
    LayeredRule,
    RuleLayer,
    resolve,
)
from app.services.publish_gate import scope_violations

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
PLACE = "p-inv"
ZONE = "z-inv"

GUIDE = AnimalRole.GUIDE_DOG.value
HEARING = AnimalRole.HEARING_DOG.value
ASSISTANCE = AnimalRole.ASSISTANCE_DOG.value
POLICE = AnimalRole.POLICE_DOG.value
MILITARY = AnimalRole.MILITARY_WORKING_DOG.value
ORDINARY_DOG = AnimalRole.ORDINARY_DOG.value


def lr(
    id_,
    *,
    layer=RuleLayer.OPERATOR_POLICY.value,
    origin="operator_direct",
    effect="allowed",
    animal="dog",
    action="enter",
    zone=None,
    place=PLACE,
    mandatory=None,
    conditions=(),
    from_=None,
    to=None,
    subject_scope=None,
    normalization=None,
):
    return LayeredRule(
        id=id_,
        animal_scope=animal,
        action=action,
        effect=effect,
        rule_layer=layer,
        origin=origin,
        conditions=tuple(conditions),
        zone_id=zone,
        place_id=place,
        mandatory_level=mandatory,
        effective_from=from_,
        effective_to=to,
        subject_scope_normalized=subject_scope,
        normalization_type=normalization,
    )


def base(**overrides):
    kw = dict(
        legal=[],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )
    kw.update(overrides)
    return kw


# --------------------------------------------------------------------------
# §8 animal scope invariants
# --------------------------------------------------------------------------


def test_guide_dog_proviso_governs_guide_dogs_only():
    """《上海市养犬管理条例》第二十三条 但书 names 导盲犬 and nothing wider."""
    subjects = legal_subjects("dog", GUIDE, NormalizationType.EXACT.value)
    assert subjects == frozenset({GUIDE})
    for other in (HEARING, ASSISTANCE, POLICE, MILITARY, ORDINARY_DOG):
        assert other not in subjects


def test_guide_dog_exception_is_not_the_hearing_dog_exception():
    """A declared hearing-dog query must not inherit a guide-dog proviso."""
    assert not rule_governs(
        query_subjects(QuerySubject(species="dog", declared_role=HEARING)),
        "dog",
        GUIDE,
        NormalizationType.EXACT.value,
    )
    assert rule_governs(
        query_subjects(QuerySubject(species="dog", declared_role=GUIDE)),
        "dog",
        GUIDE,
        NormalizationType.EXACT.value,
    )


def test_guide_dog_exception_is_not_the_assistance_dog_exception():
    assert not rule_governs(
        query_subjects(QuerySubject(species="dog", declared_role=ASSISTANCE)),
        "dog",
        GUIDE,
        NormalizationType.EXACT.value,
    )


def test_police_and_military_dogs_are_never_service_dogs():
    """Working dogs are not assistance dogs — this is the ADR-028 line."""
    assert POLICE not in SERVICE_DOG_QUERY_ROLES
    assert MILITARY not in SERVICE_DOG_QUERY_ROLES
    assert {POLICE, MILITARY} & SERVICE_DOG_QUERY_ROLES == set()


def test_ordinary_pet_scope_excludes_service_dogs():
    assert GUIDE not in ORDINARY_PET_SUBJECTS
    assert set() == SERVICE_DOG_QUERY_ROLES & ORDINARY_PET_SUBJECTS


def test_compound_term_军警犬_splits_into_exactly_police_and_military():
    assert compound_split_is_exhaustive("军警犬", {POLICE, MILITARY}) is True
    # a superset is not a faithful split: 军警犬 says nothing about guide dogs
    assert compound_split_is_exhaustive("军警犬", {POLICE, MILITARY, GUIDE}) is False
    # nor is a subset — one member of the compound term would go unmodelled
    assert compound_split_is_exhaustive("军警犬", {POLICE}) is False
    assert COMPOUND_TERM_SPLIT_MEANINGS["军警犬"] == frozenset({POLICE, MILITARY})


def test_compound_split_members_do_not_widen_to_other_working_dogs():
    """Each split row governs its own member, never the whole working-dog set."""
    for member, sibling in ((POLICE, MILITARY), (MILITARY, POLICE)):
        assert (
            rule_governs(
                query_subjects(QuerySubject(species="dog", declared_role=sibling)),
                "dog",
                member,
                NormalizationType.COMPOUND_TERM_SPLIT.value,
            )
            is False
        )


def test_ontology_parent_never_expands_the_normative_effect():
    """`service_dog` stored as a query-only parent group confers nothing."""
    assert (
        legal_subjects("dog", "service_dog", NormalizationType.PARENT_GROUP_FOR_QUERY_ONLY.value)
        is None
    )
    assert (
        legal_subjects("dog", "service_dog", NormalizationType.LEGAL_INTERPRETATION_REQUIRED.value)
        is None
    )


def test_source_scope_exact_cannot_be_silently_replaced_by_a_parent_scope():
    assert parent_expansion_is_legal("导盲犬", "service_dog") is False
    assert parent_expansion_is_legal("导盲犬", "导盲犬") is True


def test_publish_refuses_the_unproven_service_dog_widening():
    """The widening is refused at the publish boundary, not merely documented."""
    candidate = SimpleNamespace(
        animal_scope="service_dog",
        subject_scope_normalized="service_dog",
        normalization_type=NormalizationType.PARENT_GROUP_FOR_QUERY_ONLY.value,
    )
    codes = [code for code, failed, _ in scope_violations(candidate) if failed]
    assert "service_dog_scope_unproven" in codes


# --------------------------------------------------------------------------
# §9 rule layer invariants
# --------------------------------------------------------------------------


def test_legal_mandatory_prohibition_is_the_floor():
    legal = [
        lr(
            "L1",
            layer=RuleLayer.LEGAL.value,
            origin="legal",
            effect="prohibited",
            subject_scope=ORDINARY_DOG,
            normalization="exact",
            mandatory="mandatory",
        )
    ]
    operator = [lr("O1", effect="allowed", subject_scope=ORDINARY_DOG, normalization="exact")]
    rs = resolve(**base(legal=legal, operator_rules=operator))
    assert rs.effect == "prohibited"
    assert any("cannot be relaxed" in s[1] for s in rs.suppressed_rules)


def test_operator_policy_cannot_override_a_legal_prohibition_for_guide_dogs_either():
    """A venue's "guide dogs welcome" is not a statutory exemption.

    A LEGAL mandatory prohibition scoped to ``dog`` covers guide dogs too. An
    operator rule allowing guide dogs is a *lower* layer, so it is suppressed —
    the guide-dog exemption has to come from a LEGAL carve-out (or not at all).
    """
    legal = [
        LayeredRule(
            id="L-dogs",
            animal_scope="dog",
            action="enter",
            effect="prohibited",
            rule_layer=RuleLayer.LEGAL.value,
            origin="legal",
            mandatory_level="mandatory",
            subject_scope_normalized="dog",
            normalization_type="exact",
        )
    ]
    operator = [lr("O1", effect="allowed", subject_scope=GUIDE, normalization="exact")]
    rs = resolve(**base(legal=legal, operator_rules=operator, declared_role=GUIDE))
    assert rs.effect == "prohibited"
    assert any(s[0].id == "O1" for s in rs.suppressed_rules)


def test_same_layer_carve_out_replaces_its_own_base_rule():
    """A LEGAL 但书 may exempt its own LEGAL base — that is what RuleException is for."""
    # a dog-level prohibition: the base covers guide dogs via the `dog` scope
    base_rule = LayeredRule(
        id="L-dog",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer=RuleLayer.LEGAL.value,
        origin="legal",
        mandatory_level="mandatory",
        subject_scope_normalized="dog",
        normalization_type="exact",
    )
    exc = LayeredException(
        id="E-guide",
        rule_id="L-dog",
        animal_scope="dog",
        effect="allowed",
        source_id="src-1",
        subject_scope_normalized=GUIDE,
        normalization_type="exact",
        normative_effect="exempt_from_prohibition",
    )
    rs = resolve(**base(legal=[base_rule], exceptions=[exc], declared_role=GUIDE, animal="dog"))
    assert rs.effect == "allowed"
    assert rs.applied_exceptions == ["E-guide"]


def test_exception_derived_rule_inherits_the_base_rule_layer():
    """Why binding must be same-layer: the resolver re-labels by base layer.

    An OPERATOR carve-out attached to a LEGAL base would therefore be applied
    *as* a legal rule and would outrank every operator rule — the exact defect
    RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE removed at generation time.
    """
    base_rule = LayeredRule(
        id="L-dog",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer=RuleLayer.LEGAL.value,
        origin="legal",
        mandatory_level="mandatory",
        subject_scope_normalized="dog",
        normalization_type="exact",
    )
    exc = LayeredException(
        id="E-guide",
        rule_id="L-dog",
        animal_scope="dog",
        effect="allowed",
        source_id="src-1",
        subject_scope_normalized=GUIDE,
        normalization_type="exact",
    )
    rs = resolve(**base(legal=[base_rule], exceptions=[exc], declared_role=GUIDE))
    synthesised = [r for r in rs.applicable_rules if r.origin == "exception"]
    assert synthesised
    assert all(r.rule_layer == RuleLayer.LEGAL.value for r in synthesised)


def test_temporary_policy_shadows_operator_policy_while_active():
    operator = [lr("O1", effect="allowed", subject_scope=ORDINARY_DOG, normalization="exact")]
    event = [
        lr(
            "E1",
            layer=RuleLayer.TEMPORARY_POLICY.value,
            origin="event",
            effect="prohibited",
            subject_scope=ORDINARY_DOG,
            normalization="exact",
        )
    ]
    rs = resolve(**base(operator_rules=operator, event_rules=event))
    assert rs.effect == "prohibited"
    assert any("temporary policy" in s[1] for s in rs.suppressed_rules)


def test_expired_temporary_policy_does_not_shadow_operator_policy():
    operator = [lr("O1", effect="allowed", subject_scope=ORDINARY_DOG, normalization="exact")]
    event = [
        lr(
            "E1",
            layer=RuleLayer.TEMPORARY_POLICY.value,
            origin="event",
            effect="prohibited",
            subject_scope=ORDINARY_DOG,
            normalization="exact",
            to=datetime(2026, 9, 1, tzinfo=UTC),
        )
    ]
    rs = resolve(**base(operator_rules=operator, event_rules=event))
    assert rs.effect == "allowed"


def test_same_layer_conflict_is_recorded_not_silently_answered():
    """allowed vs prohibited in one layer is never auto-picked."""
    rules = [
        lr(
            "O1",
            effect="allowed",
            origin="operator_direct",
            subject_scope=ORDINARY_DOG,
            normalization="exact",
        ),
        lr(
            "O2",
            effect="prohibited",
            origin="operator_direct",
            subject_scope=ORDINARY_DOG,
            normalization="exact",
        ),
    ]
    rs = resolve(**base(operator_rules=rules))
    assert rs.compliance_state == ComplianceState.POTENTIAL_CONFLICT
    assert rs.unresolved_conflicts
    # the prohibition governs meanwhile, and the allowance is on the record
    assert rs.effect == "prohibited"
    assert any(s[0].id == "O1" for s in rs.suppressed_rules)


# --------------------------------------------------------------------------
# §11 UNKNOWN semantics
# --------------------------------------------------------------------------


def test_no_governing_rule_is_unknown_and_never_allowed():
    rs = resolve(**base())
    assert rs.effect == "unknown"
    assert rs.compliance_state == ComplianceState.UNKNOWN


def test_unknown_is_not_prohibited():
    rs = resolve(**base())
    assert rs.effect != "prohibited"


def test_a_rule_whose_scope_is_not_a_legal_equivalent_yields_unknown():
    """Absence of evidence is not a permission and not a prohibition."""
    rule = lr(
        "O1",
        effect="allowed",
        animal="service_dog",
        subject_scope="service_dog",
        normalization=NormalizationType.PARENT_GROUP_FOR_QUERY_ONLY.value,
    )
    rs = resolve(**base(operator_rules=[rule], service_role="working"))
    assert rs.effect == "unknown"


def test_withdrawn_exception_does_not_restore_an_allowance():
    base_rule = LayeredRule(
        id="L-dog",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer=RuleLayer.LEGAL.value,
        origin="legal",
        mandatory_level="mandatory",
        subject_scope_normalized="dog",
        normalization_type="exact",
    )
    withdrawn = LayeredException(
        id="E-old",
        rule_id="L-dog",
        animal_scope="dog",
        effect="allowed",
        source_id="src-1",
        status="withdrawn",
        subject_scope_normalized=GUIDE,
        normalization_type="exact",
    )
    rs = resolve(**base(legal=[base_rule], exceptions=[withdrawn], declared_role=GUIDE))
    assert rs.applied_exceptions == []
    assert rs.effect == "prohibited"


def test_expired_exception_window_falls_back_to_the_base_rule():
    base_rule = LayeredRule(
        id="L-dog",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer=RuleLayer.LEGAL.value,
        origin="legal",
        mandatory_level="mandatory",
        subject_scope_normalized="dog",
        normalization_type="exact",
    )
    expired = LayeredException(
        id="E-expired",
        rule_id="L-dog",
        animal_scope="dog",
        effect="allowed",
        source_id="src-1",
        subject_scope_normalized=GUIDE,
        normalization_type="exact",
        effective_to=datetime(2026, 1, 1, tzinfo=UTC),
    )
    rs = resolve(**base(legal=[base_rule], exceptions=[expired], declared_role=GUIDE))
    assert rs.effect == "prohibited"


def test_exception_without_source_never_applies():
    base_rule = LayeredRule(
        id="L-dog",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer=RuleLayer.LEGAL.value,
        origin="legal",
        mandatory_level="mandatory",
        subject_scope_normalized="dog",
        normalization_type="exact",
    )
    sourceless = LayeredException(
        id="E-nosrc",
        rule_id="L-dog",
        animal_scope="dog",
        effect="allowed",
        source_id=None,
        subject_scope_normalized=GUIDE,
        normalization_type="exact",
    )
    rs = resolve(**base(legal=[base_rule], exceptions=[sourceless], declared_role=GUIDE))
    assert rs.effect == "prohibited"


@pytest.mark.parametrize(
    "status",
    ["pending_review", "superseded", "withdrawn", "archived"],
)
def test_only_current_exceptions_apply(status):
    exc = LayeredException(
        id="E-x",
        rule_id="L-dog",
        animal_scope="dog",
        effect="allowed",
        source_id="src-1",
        status=status,
        subject_scope_normalized=GUIDE,
        normalization_type="exact",
    )
    assert exc.active_at(NOW) is False
