"""EffectiveRuleResolver unit tests (TEST_PLAN_v0.5 resolver section)."""

from datetime import UTC, datetime

from app.rulespec.v05_resolver import (
    ComplianceState,
    LayeredRule,
    resolve,
)

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
PLACE = "p1"
ZONE_A = "z-a"


def lr(
    id_,
    *,
    layer="OPERATOR_POLICY",
    origin="operator_direct",
    effect="allowed",
    animal="ordinary_pet",
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
        # ADR-025: a rule only speaks about a precise subject when the caller (or
        # the ingest pipeline) recorded the source-faithful normalisation.
        subject_scope_normalized=subject_scope,
        normalization_type=normalization,
    )


def base_kwargs(**overrides):
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


def test_legal_mandatory_prohibition_cannot_be_relaxed():
    legal = [lr("L1", layer="LEGAL", origin="legal", effect="prohibited", mandatory="mandatory")]
    op = [lr("O1", effect="allowed")]
    rs = resolve(**base_kwargs(legal=legal, operator_rules=op))
    assert rs.effect == "prohibited"
    assert any(s[0].id == "O1" for s in rs.suppressed_rules)
    assert rs.compliance_state == ComplianceState.POTENTIAL_CONFLICT
    assert any("cannot be relaxed" in s[1] for s in rs.suppressed_rules)


def test_operator_can_be_more_restrictive_than_legal():
    legal = [
        lr(
            "L1",
            layer="LEGAL",
            effect="conditional",
            mandatory="mandatory",
            conditions=[{"condition_type": "leash_required", "value_flag": True}],
        )
    ]
    op = [lr("O1", effect="prohibited")]
    rs = resolve(**base_kwargs(legal=legal, operator_rules=op))
    assert rs.effect == "prohibited"
    assert rs.compliance_state == ComplianceState.CONSISTENT
    # mandatory legal conditions stay in the effective set
    assert "leash_required" in rs.obligations


def test_guidance_layer_is_included():
    g = [
        lr(
            "G1",
            layer="REGULATORY_GUIDANCE",
            origin="guidance",
            effect="conditional",
            conditions=[{"condition_type": "leash_required", "value_flag": True}],
        )
    ]
    rs = resolve(**base_kwargs(guidance=[g[0]]))
    assert rs.effect == "conditional"
    assert any(r.id == "G1" for r in rs.applicable_rules)
    assert rs.compliance_state == ComplianceState.CONSISTENT


def test_template_inherited_and_place_override_wins():
    template = [lr("T1", origin="template", effect="prohibited")]
    place_override = [
        lr(
            "P1",
            origin="place_override",
            effect="conditional",
            conditions=[{"condition_type": "leash_required", "value_flag": True}],
        )
    ]
    rs = resolve(**base_kwargs(template_rules=template, operator_rules=place_override))
    # explicit place override beats the inherited template for the same scope
    assert any(r.id == "P1" for r in rs.applicable_rules)
    assert any(s[0].id == "T1" for s in rs.suppressed_rules)
    assert rs.effect == "conditional"


def test_zone_override_beats_place_override():
    place = [lr("P1", origin="place_override", effect="allowed")]
    zone = [lr("Z1", origin="zone_override", effect="prohibited", zone=ZONE_A)]
    rs = resolve(**base_kwargs(operator_rules=place + zone, zone_id=ZONE_A))
    assert rs.effect == "prohibited"
    assert any(s[0].id == "P1" for s in rs.suppressed_rules)
    # outside the zone, place rule governs
    rs2 = resolve(**base_kwargs(operator_rules=place + zone))
    assert rs2.effect == "allowed"


def test_active_event_overrides_operator():
    op = [lr("O1", effect="prohibited")]
    ev = [
        lr(
            "E1",
            layer="TEMPORARY_POLICY",
            origin="event",
            effect="allowed",
            from_=datetime(2026, 9, 12, 9, 0, tzinfo=UTC),
            to=datetime(2026, 9, 12, 18, 0, tzinfo=UTC),
        )
    ]
    rs = resolve(**base_kwargs(operator_rules=op, event_rules=ev))
    assert rs.effect == "allowed"


def test_expired_event_does_not_apply():
    op = [lr("O1", effect="prohibited")]
    ev = [
        lr(
            "E1",
            layer="TEMPORARY_POLICY",
            origin="event",
            effect="allowed",
            from_=datetime(2026, 9, 1, 9, 0, tzinfo=UTC),
            to=datetime(2026, 9, 2, 18, 0, tzinfo=UTC),
        )
    ]
    rs = resolve(**base_kwargs(operator_rules=op, event_rules=ev))
    assert rs.effect == "prohibited"
    assert all(r.id != "E1" for r in rs.applicable_rules)


def test_same_layer_allowed_vs_prohibited_is_unresolved_conflict():
    op = [lr("O1", effect="allowed"), lr("O2", effect="prohibited")]
    rs = resolve(**base_kwargs(operator_rules=op))
    assert rs.unresolved_conflicts
    assert rs.effect == "prohibited"  # prohibition governs meanwhile
    assert rs.compliance_state == ComplianceState.POTENTIAL_CONFLICT


def test_legacy_rule_without_layer_is_review_required():
    op = [lr("O1", layer=None, effect="allowed")]
    rs = resolve(**base_kwargs(operator_rules=op))
    assert rs.compliance_state == ComplianceState.REVIEW_REQUIRED
    assert rs.effect == "allowed"  # still readable, but flagged for review


def test_no_rules_anywhere_is_unknown():
    rs = resolve(**base_kwargs())
    assert rs.compliance_state == ComplianceState.UNKNOWN
    assert rs.effect == "unknown"


def test_service_dog_isolation_against_ordinary_pet_rules():
    op = [lr("O1", effect="prohibited", animal="ordinary_pet")]
    rs = resolve(**base_kwargs(operator_rules=op, service_role="working"))
    assert rs.effect == "unknown"  # ordinary-pet rule never governs a service dog
    # ADR-025: a rule governing service dogs must carry the precise subject scope
    # plus the normalisation that makes it a legal equivalent. A bare
    # `animal_scope="service_dog"` row would govern nothing.
    sd = [
        lr(
            "S1",
            animal="service_dog",
            effect="allowed",
            subject_scope="service_dog",
            normalization="exact",
        )
    ]
    rs2 = resolve(**base_kwargs(operator_rules=op + sd, service_role="working"))
    assert rs2.effect == "allowed"


def test_legacy_service_dog_scope_without_normalisation_confers_nothing():
    """ADR-025's whole point: `service_dog` with no declared normalisation is the
    unproven widening and must not govern any query."""
    legacy = [lr("S1", animal="service_dog", effect="allowed")]
    for role in ("working", "none"):
        rs = resolve(**base_kwargs(operator_rules=legacy, service_role=role))
        assert rs.effect == "unknown", role


def test_declared_role_does_not_inherit_another_roles_proviso():
    """A hearing-dog query must not inherit a guide-dog proviso (ADR-025)."""
    guide_only = [
        lr(
            "S1",
            animal="service_dog",
            effect="allowed",
            subject_scope="guide_dog",
            normalization="exact",
        )
    ]
    kw = base_kwargs(operator_rules=guide_only, service_role="working")
    assert resolve(**kw).effect == "allowed"
    assert resolve(**kw, declared_role="guide_dog").effect == "allowed"
    assert resolve(**kw, declared_role="hearing_dog").effect == "unknown"
    assert resolve(**kw, declared_role="assistance_dog").effect == "unknown"
