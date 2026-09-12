"""EffectiveRuleResolver (NEXT_GOAL §B2, RULE_RESOLVER_SPEC).

Resolves layered rules into an EffectiveRuleSet:

    LEGAL constraints → REGULATORY_GUIDANCE → Organization PolicyTemplate
    → Place override → Zone override → Temporary/Event override

Deterministic, explainable, never last-write-wins:

- MANDATORY legal constraints are the floor: no operator/template/event rule
  may relax a mandatory legal prohibition, and mandatory legal conditions
  always stay in the effective set.
- Specificity shadows breadth: zone beats place beats inherited template at
  the same (animal_scope, action).
- An active TEMPORARY_POLICY (event) shadows the operator policy entry for its
  scope while it is within its validity window.
- allowed-vs-prohibited inside the SAME layer/specificity = unresolved
  conflict (compliance_state=POTENTIAL_CONFLICT) — never auto-picked.
- Rules with unknown layer (legacy NULL) force REVIEW_REQUIRED — never guessed.
- Observation data never enters this module (ADR-004).

Pure functions: no DB, no LLM, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class RuleLayer(StrEnum):
    LEGAL = "LEGAL"
    REGULATORY_GUIDANCE = "REGULATORY_GUIDANCE"
    OPERATOR_POLICY = "OPERATOR_POLICY"
    TEMPORARY_POLICY = "TEMPORARY_POLICY"


class MandatoryLevel(StrEnum):
    MANDATORY = "mandatory"
    ADVISORY = "advisory"
    DISCRETIONARY = "discretionary"


class ComplianceState(StrEnum):
    CONSISTENT = "CONSISTENT"
    POTENTIAL_CONFLICT = "POTENTIAL_CONFLICT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class LayeredRule:
    """Rule with layer/origin metadata for resolution."""

    id: str
    animal_scope: str
    action: str
    effect: str  # allowed | prohibited | conditional
    rule_layer: str | None  # RuleLayer value or None (legacy)
    # origin: legal | guidance | template | place_override | zone_override |
    #         event | operator_direct
    origin: str
    conditions: tuple[dict, ...] = ()
    zone_id: str | None = None
    place_id: str | None = None
    source_id: str | None = None
    mandatory_level: str | None = None  # for legal rules
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    supersedes_rule_id: str | None = None

    @property
    def is_temporary(self) -> bool:
        return self.rule_layer == RuleLayer.TEMPORARY_POLICY.value


@dataclass
class EffectiveRuleSet:
    applicable_rules: list[LayeredRule] = field(default_factory=list)
    suppressed_rules: list[tuple[LayeredRule, str]] = field(default_factory=list)
    unresolved_conflicts: list[tuple[LayeredRule, LayeredRule]] = field(default_factory=list)
    explanation_steps: list[str] = field(default_factory=list)
    compliance_state: ComplianceState = ComplianceState.UNKNOWN
    # synthesized answer
    effect: str = "unknown"  # allowed | conditional | prohibited | unknown
    obligations: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)


def _scope_matches(rule: LayeredRule, animal: str, service_role: str) -> bool:
    from app.rulespec.evaluator import _animal_scope_matches  # reuse v1 semantics
    from app.rulespec.model import AnimalInput, AnimalScope, RuleAction, RuleEffect
    from app.rulespec.model import Rule as SpecRule

    probe = SpecRule(
        id=rule.id,
        animal_scope=AnimalScope(rule.animal_scope),
        action=RuleAction(rule.action),
        effect=RuleEffect(rule.effect),
    )
    return _animal_scope_matches(probe, AnimalInput(species=animal, service_role=service_role))


def _action_matches(rule: LayeredRule, action: str) -> bool:
    return rule.action == action


def _in_time(rule: LayeredRule, now: datetime) -> bool:
    if rule.effective_from is not None and now < rule.effective_from:
        return False
    return not (rule.effective_to is not None and now > rule.effective_to)


def _by_specificity(rules: list[LayeredRule]) -> list[LayeredRule]:
    """zone_override > place_override > template > operator_direct."""
    rank = {"zone_override": 0, "place_override": 1, "template": 2, "operator_direct": 3}
    if not rules:
        return []
    best = min(rank.get(r.origin, 3) for r in rules)
    return [r for r in rules if rank.get(r.origin, 3) == best]


def resolve(
    *,
    legal: list[LayeredRule],
    guidance: list[LayeredRule],
    template_rules: list[LayeredRule],
    operator_rules: list[LayeredRule],
    event_rules: list[LayeredRule],
    animal: str,
    service_role: str,
    action: str,
    zone_id: str | None,
    now: datetime,
) -> EffectiveRuleSet:
    steps: list[str] = []
    suppressed: list[tuple[LayeredRule, str]] = []
    conflicts: list[tuple[LayeredRule, LayeredRule]] = []
    applicable: list[LayeredRule] = []

    def in_scope(layer: list[LayeredRule]) -> list[LayeredRule]:
        return [
            r
            for r in layer
            if _scope_matches(r, animal, service_role)
            and _action_matches(r, action)
            and _in_time(r, now)
            and (r.zone_id is None or r.zone_id == zone_id)
        ]

    scoped_legal = in_scope(legal)
    scoped_guidance = in_scope(guidance)
    scoped_template = in_scope(template_rules)
    scoped_operator = in_scope(operator_rules)
    scoped_events = in_scope(event_rules)

    if not (scoped_legal or scoped_guidance or scoped_template or scoped_operator or scoped_events):
        return EffectiveRuleSet(
            explanation_steps=["no in-scope rules in any layer"],
            compliance_state=ComplianceState.UNKNOWN,
            effect="unknown",
        )

    # --- 1. LEGAL layer -----------------------------------------------------
    legal_mandatory = [r for r in scoped_legal if r.mandatory_level == "mandatory"]
    legal_other = [r for r in scoped_legal if r.mandatory_level != "mandatory"]
    applicable.extend(legal_mandatory)
    if legal_mandatory:
        steps.append(
            f"LEGAL mandatory rules govern ({len(legal_mandatory)}); lower layers "
            "cannot relax them (RULE_RESOLVER_SPEC)."
        )
    if legal_other:
        applicable.extend(legal_other)
        steps.append(f"LEGAL non-mandatory rules included ({len(legal_other)}).")

    mandatory_prohibited = [r for r in legal_mandatory if r.effect == "prohibited"]
    mandatory_conditions = [
        c for r in legal_mandatory if r.effect == "conditional" for c in r.conditions
    ]

    # --- 2. lower layers: conflict-with-legal handling -----------------------
    for group, label in (
        (scoped_guidance, "REGULATORY_GUIDANCE"),
        (scoped_template, "template"),
        (scoped_operator, "operator"),
        (scoped_events, "event"),
    ):
        for r in group:
            if mandatory_prohibited and r.effect in ("allowed", "conditional"):
                suppressed.append(
                    (
                        r,
                        f"suppressed: MANDATORY legal prohibition (rule "
                        f"{mandatory_prohibited[0].id}) cannot be relaxed by {label}",
                    )
                )
            else:
                applicable.append(r)
        if group:
            steps.append(f"{label} layer considered ({len(group)} in scope).")

    # --- 3. active temporary policy shadows operator-side entries ------------
    # TEMPORARY_POLICY (active event) outranks OPERATOR_POLICY for the same
    # scope while inside its validity window (already filtered by _in_time).
    events_in_applicable = [r for r in applicable if r.is_temporary]
    operator_side = [
        r
        for r in applicable
        if not r.is_temporary
        and r.rule_layer != RuleLayer.LEGAL.value
        and r.rule_layer != RuleLayer.REGULATORY_GUIDANCE.value
    ]
    if events_in_applicable and operator_side:
        event_scope_keys = {(r.animal_scope, r.action) for r in events_in_applicable}
        shadowed = [r for r in operator_side if (r.animal_scope, r.action) in event_scope_keys]
        for r in shadowed:
            suppressed.append((r, "shadowed by active temporary policy (event overrides operator)"))
            applicable.remove(r)
        if shadowed:
            steps.append(
                f"active event shadows {len(shadowed)} operator-side rule(s) for the same scope."
            )

    # --- 4. specificity within operator-origin rules -------------------------
    operator_side = [
        r
        for r in applicable
        if not r.is_temporary
        and r.rule_layer != RuleLayer.LEGAL.value
        and r.rule_layer != RuleLayer.REGULATORY_GUIDANCE.value
    ]
    applicable = [r for r in applicable if r not in operator_side]
    if operator_side:
        # template inheritance vs explicit overrides compete in ONE pool:
        # zone_override > place_override > template > operator_direct
        chosen_operator = _by_specificity(operator_side)
        for r in operator_side:
            if r not in chosen_operator:
                suppressed.append((r, f"shadowed by more specific {chosen_operator[0].origin}"))
        applicable.extend(chosen_operator)
        steps.append(
            f"operator specificity resolved: kept {chosen_operator[0].origin} "
            f"({len(chosen_operator)} rules)."
        )

    # --- 5. same-scope conflicts among applicable lower-layer rules ----------
    allowed = [
        r for r in applicable if r.effect == "allowed" and r.rule_layer != RuleLayer.LEGAL.value
    ]
    prohibited = [
        r for r in applicable if r.effect == "prohibited" and r.rule_layer != RuleLayer.LEGAL.value
    ]
    if allowed and prohibited:
        conflicts.append((prohibited[0], allowed[0]))
        for r in allowed:
            suppressed.append((r, "unresolved conflict with explicit prohibition"))
            applicable.remove(r)
        steps.append(
            "allowed-vs-prohibited conflict inside lower layers: prohibition kept "
            "governing, allowed rule recorded as suppressed for review."
        )

    # --- 5. compliance state -------------------------------------------------
    unknown_layer_rules = [
        r
        for r in (
            scoped_legal + scoped_guidance + scoped_template + scoped_operator + scoped_events
        )
        if r.rule_layer is None
    ]
    relaxed_against_legal = [s for s in suppressed if "cannot be relaxed" in s[1]]
    if unknown_layer_rules:
        compliance = ComplianceState.REVIEW_REQUIRED
        steps.append(
            f"{len(unknown_layer_rules)} governing rule(s) have no rule_layer "
            "(legacy): REVIEW_REQUIRED, not guessed."
        )
    elif conflicts or relaxed_against_legal:
        compliance = ComplianceState.POTENTIAL_CONFLICT
        steps.append("conflict recorded for review; prohibition governs meanwhile.")
    else:
        compliance = ComplianceState.CONSISTENT

    # --- 6. synthesized effect ------------------------------------------------
    legal_conditions = [dict(c) for c in mandatory_conditions]
    governing = [r for r in applicable if r.rule_layer != RuleLayer.LEGAL.value] or applicable
    if mandatory_prohibited:
        effect = "prohibited"
        steps.append("effect: prohibited (legal floor).")
    elif applicable:
        effects = {r.effect for r in governing}
        if "prohibited" in effects:
            effect = "prohibited"
        elif effects == {"allowed"}:
            effect = "allowed"
        else:
            effect = "conditional"
        steps.append(f"effect from governing rules ({len(governing)}): {effect}.")
    else:
        effect = "unknown"
        steps.append("no governing rule after resolution: UNKNOWN, never guessed.")

    obligations = [str(c.get("condition_type", c)) for c in legal_conditions]
    return EffectiveRuleSet(
        applicable_rules=applicable,
        suppressed_rules=suppressed,
        unresolved_conflicts=conflicts,
        explanation_steps=steps,
        compliance_state=compliance,
        effect=effect,
        obligations=obligations,
    )


def _unused() -> None:  # pragma: no cover - keeps imports referenced for clarity
    _by_specificity([])
