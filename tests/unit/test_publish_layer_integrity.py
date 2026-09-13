"""P0-REVIEW-PUBLISH-01 regression: the normative layer must survive publish.

Two findings from the P0 publish-path review, pinned here as tests:

F1 (fixed) — ``candidate_service.publish()`` hard-coded
``AccessRule.rule_layer = "OPERATOR_POLICY"`` and ``RuleCandidate`` had no
``rule_layer`` field, so the layer recorded in the evidence register (LEGAL /
TEMPORARY_POLICY / …) was dropped at ingest and flattened at publish. The
resolver routes rules into the legal / guidance / event / operator pools on this
value, so flattening changes the published answer. The fix carries the layer
through (migration d1a4f7c93b28).

F2 (open, recorded as BLK-LAYER-02) — ``AccessRule`` has no ``mandatory_level``
column, so a DB-backed LEGAL rule can never be ``mandatory``. The resolver's
"LEGAL mandatory rules govern; lower layers cannot relax them" branch is
therefore unreachable for published rules, and a statutory prohibition can be
outvoted by an operator ``allowed`` rule. Pinned below so the behaviour cannot
change silently; the fix needs a human decision (schema + ADR), not a patch.
"""

from datetime import UTC, datetime

from app.rulespec.v05_resolver import LayeredRule, RuleLayer, resolve
from app.services.publish_gate import LAYER_VALUES

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
PLACE = "p1"
ZONE = "z-indoor"


def _rule(id_, *, layer, effect, zone=None, animal="dog", mandatory=None):
    return LayeredRule(
        id=id_,
        animal_scope=animal,
        action="enter",
        effect=effect,
        rule_layer=layer,
        origin="legal" if layer == RuleLayer.LEGAL.value else "operator_direct",
        zone_id=zone,
        place_id=PLACE,
        mandatory_level=mandatory,
    )


def _resolve(**over):
    kw = dict(
        legal=[],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=ZONE,
        now=NOW,
    )
    kw.update(over)
    return resolve(**kw)


def _ids(rule_set):
    return {r.id for r in rule_set.applicable_rules}


# --- F1: layer vocabulary and the semantic weight of rule_layer -------------


def test_layer_vocabulary_is_exactly_the_four_normative_layers():
    assert {
        "LEGAL",
        "REGULATORY_GUIDANCE",
        "OPERATOR_POLICY",
        "TEMPORARY_POLICY",
    } == LAYER_VALUES


def test_mislaying_a_rule_changes_the_answer():
    """Identical rule text, different layer ⇒ different resolved effect.

    A place-level prohibition and a zone-specific allowance: at OPERATOR layer
    the two compete in the specificity pool and resolve one way; promoting the
    prohibition to LEGAL changes which set governs. That is why the publish
    boundary may not rewrite the layer.
    """
    operator_only = _resolve(
        operator_rules=[
            _rule("L1", layer=RuleLayer.OPERATOR_POLICY.value, effect="prohibited"),
            _rule("O1", layer=RuleLayer.OPERATOR_POLICY.value, effect="allowed", zone=ZONE),
        ]
    )
    with_legal = _resolve(
        legal=[_rule("L1", layer=RuleLayer.LEGAL.value, effect="prohibited")],
        operator_rules=[
            _rule("O1", layer=RuleLayer.OPERATOR_POLICY.value, effect="allowed", zone=ZONE)
        ],
    )
    assert operator_only.effect != with_legal.effect


def test_temporary_policy_is_distinguished_by_its_layer():
    """TEMPORARY_POLICY is the only layer that carries ``is_temporary``."""
    temp = _rule("E1", layer=RuleLayer.TEMPORARY_POLICY.value, effect="conditional")
    op = _rule("O1", layer=RuleLayer.OPERATOR_POLICY.value, effect="conditional")
    assert temp.is_temporary is True
    assert op.is_temporary is False


# --- F2: the mandatory_level gap (open finding, recorded for the review Gate) -


def test_legal_prohibition_without_mandatory_level_does_not_govern():
    """BLK-LAYER-02: a non-mandatory LEGAL prohibition is outvoted by operator.

    ``AccessRule`` stores no ``mandatory_level``, so every published LEGAL rule
    lands in the resolver's ``legal_other`` bucket and is excluded from the
    governing set whenever any non-legal rule applies. A venue operator rule
    saying "allowed" therefore wins against 《上海市养犬管理条例》第23条.
    """
    rs = _resolve(
        legal=[_rule("L1", layer=RuleLayer.LEGAL.value, effect="prohibited")],
        operator_rules=[
            _rule("O1", layer=RuleLayer.OPERATOR_POLICY.value, effect="allowed", zone=ZONE)
        ],
    )
    assert rs.effect == "allowed"


def test_legal_prohibition_with_mandatory_level_does_govern():
    """The designed behaviour the DB path cannot currently reach (see F2)."""
    rs = _resolve(
        legal=[
            _rule(
                "L1",
                layer=RuleLayer.LEGAL.value,
                effect="prohibited",
                mandatory="mandatory",
            )
        ],
        operator_rules=[
            _rule("O1", layer=RuleLayer.OPERATOR_POLICY.value, effect="allowed", zone=ZONE)
        ],
    )
    assert rs.effect == "prohibited"
    assert "L1" in _ids(rs)
