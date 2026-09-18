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

from app.models.enums import MandatoryLevel, normalize_mandatory_level
from app.rulespec.holder_scope import (
    MISSING_CONTEXT_HOLDER_SCOPE,
    MISSING_CONTEXT_SERVICE_ROLE,
    HolderContext,
    HolderMatch,
    evaluate_holder,
)
from app.rulespec.statutory_proviso import (
    JURISDICTION_EXCEPTION_INERT,
    BindingMode,
    bind_proviso_to_bases,
)

__all__ = [
    "RuleLayer",
    "MandatoryLevel",
    "normalize_mandatory_level",
    "ComplianceState",
    "LayeredRule",
    "EffectiveRuleSet",
    "LayeredException",
    "BindingMode",
    "HolderContext",
    "HolderMatch",
    "resolve",
]

#: Order in which missing context is surfaced to a consumer: ask *what* the
#: animal is before asking *who* is handling it.
MISSING_CONTEXT_ORDER = (MISSING_CONTEXT_SERVICE_ROLE, MISSING_CONTEXT_HOLDER_SCOPE)


class RuleLayer(StrEnum):
    LEGAL = "LEGAL"
    REGULATORY_GUIDANCE = "REGULATORY_GUIDANCE"
    OPERATOR_POLICY = "OPERATOR_POLICY"
    TEMPORARY_POLICY = "TEMPORARY_POLICY"


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
    # mandatory | advisory | operator_discretion (or the legacy 'discretionary').
    # Only a LEGAL rule carrying 'mandatory' becomes the resolver floor
    # (ADR-023 / BLK-LAYER-02); NULL is never read as mandatory.
    mandatory_level: str | None = None
    # ---- ADR-025: source-faithful scope + normative effect ------------------
    #: what the source literally names (e.g. 'guide_dog')
    source_scope_exact: str | None = None
    #: the precise AnimalRole this rule governs (the legal matching unit)
    subject_scope_normalized: str | None = None
    #: exact | parent_group_for_query_only | legal_interpretation_required.
    #: Anything other than 'exact' means the stored scope is NOT a legal
    #: equivalent, so the rule confers no legal effect (see animal_scope.py).
    normalization_type: str | None = None
    #: permission | prohibition | conditional_permission |
    #: exempt_from_prohibition | facilitation_required
    normative_effect: str | None = None
    #: any_handler | person_with_disability (无障碍法第46条)
    holder_scope: str | None = None
    #: positive duties the venue owes; surfaced, never folded into `effect`
    operator_obligations: tuple[str, ...] = ()
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
    #: what the caller would have to supply for a withheld carve-out to fire
    #: (``service_role`` / ``holder_scope``). Empty ⇒ the answer is final.
    missing_inputs: list[str] = field(default_factory=list)
    applied_exceptions: list[str] = field(default_factory=list)
    #: carve-outs that matched but were **withheld** because their conditions
    #: could not be evaluated from the query as asked. Never applied.
    pending_exceptions: list[str] = field(default_factory=list)
    #: carve-outs that claimed a base already carved out with the same effect.
    #: Provenance only — the legal effect is computed exactly once (ADR-031 §17).
    duplicate_exceptions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LayeredException:
    """A carve-out attached to a base rule (SG-REAL-01).

    The same normative statement may govern a broad scope while exempting a
    narrower one (e.g. 条例23 prohibits dogs in malls, its 但书 exempts guide
    dogs). Generic mechanism: no hardcoded service_dog branch. source_id is
    required — an exception without provenance never applies.
    """

    id: str
    rule_id: str
    animal_scope: str  # the scope this exception governs (e.g. guide_dog)
    effect: str  # what applies to that scope instead of the base effect
    source_id: str | None  # None/empty => invalid, never applied
    status: str = "current"  # only "current" applies
    conditions: tuple[dict, ...] = ()
    # ---- ADR-025: the exception is a source-faithful carve-out ---------------
    #: what the source literally names (e.g. '导盲犬')
    source_scope_exact: str | None = None
    #: precise role the source names (e.g. 'guide_dog'); None ⇒ legacy row
    subject_scope_normalized: str | None = None
    #: exact | parent_group_for_query_only | legal_interpretation_required
    normalization_type: str | None = None
    #: exempt_from_prohibition | permission | …
    normative_effect: str | None = None
    #: any_handler | person_with_disability（无障碍法第46条）
    holder_scope: str | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    # ---- ADR-030: jurisdiction-level statutory proviso ----------------------
    #: How this carve-out finds its base rule. ``"rule"`` (the default) uses
    #: ``rule_id``; ``"instrument"`` is a statutory proviso that carves out of
    #: any in-scope prohibition grounded in the same instrument. See
    #: app.rulespec.statutory_proviso — the binding rule lives there so the
    #: resolver, the publish gate and the tests cannot drift apart.
    binding: str = BindingMode.RULE
    #: Reviewed declaration of which ``source`` rows are the same instrument.
    #: Empty ⇒ the proviso binds nothing (fail closed).
    instrument_source_ids: tuple[str, ...] = ()
    #: Layer the proviso carves out of (normally ``LEGAL``); None ⇒ binds nothing.
    applies_to_layer: str | None = None
    #: Effects carved out; a proviso exempts from a *prohibition* by default.
    applies_to_effects: tuple[str, ...] = ("prohibited",)

    def active_at(self, now: datetime) -> bool:
        if self.status != "current":
            return False
        if self.effective_from is not None and now < self.effective_from:
            return False
        return not (self.effective_to is not None and now > self.effective_to)

    def has_source(self) -> bool:
        return bool(self.source_id)


def _query_subjects(animal: str, service_role: str, declared_role: str | None) -> frozenset[str]:
    from app.rulespec.animal_scope import QuerySubject, query_subjects

    return query_subjects(
        QuerySubject(species=animal, service_role=service_role, declared_role=declared_role)
    )


def _scope_matches(
    rule: LayeredRule, animal: str, service_role: str, declared_role: str | None = None
) -> bool:
    """Match on the precise subject scope, never on an ontology parent (ADR-025).

    A rule whose stored scope is not a legal equivalent
    (``normalization_type != 'exact'``) governs nothing — that is precisely what
    stops a 导盲犬 proviso from being applied to every service dog.

    The query side still expands a generic "service dog" query to the four
    assistance roles, so a statute written of 「犬」 still governs an
    underspecified service-dog question. When the user *declares* the role
    (``declared_role``), no expansion happens: a hearing-dog query must not
    inherit a guide-dog proviso.
    """
    from app.rulespec.animal_scope import rule_governs

    query = _query_subjects(animal, service_role, declared_role)
    return rule_governs(
        query,
        rule.animal_scope,
        rule.subject_scope_normalized,
        rule.normalization_type,
    )


def _carve_out_covers(
    exc: LayeredException, animal: str, service_role: str, declared_role: str | None
) -> bool:
    """Does this carve-out answer the whole query? (ADR-031 §10-§12)

    Stricter than ``_scope_matches`` on purpose. A prohibition written of 「犬」
    legitimately governs an underspecified question, but an exemption written of
    「导盲犬」 does not: it covers one of the four roles the question could be
    about, so applying it would answer a question the source never answered —
    the existence semantics "a child of the parent scope hits an exception, so
    the parent query is allowed".
    """
    from app.rulespec.animal_scope import carve_out_covers

    return carve_out_covers(
        _query_subjects(animal, service_role, declared_role),
        exc.animal_scope,
        exc.subject_scope_normalized,
        exc.normalization_type,
    )


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
    exceptions: list[LayeredException] | None = None,
    declared_role: str | None = None,
    holder_context: HolderContext | None = None,
) -> EffectiveRuleSet:
    """Resolve one access question.

    ``holder_context`` (ADR-031) is the ephemeral, query-time statement about
    who is handling the animal. It is never persisted and never defaulted: with
    no context supplied, a carve-out that names a holder condition is *withheld*
    and the answer becomes ``conditional`` with ``missing_inputs`` — never an
    unconditional ``allowed``, and never a bare ``prohibited`` that would hide a
    statutory right behind a missing input.
    """
    steps: list[str] = []
    suppressed: list[tuple[LayeredRule, str]] = []
    conflicts: list[tuple[LayeredRule, LayeredRule]] = []
    applicable: list[LayeredRule] = []
    applied_exceptions: list[str] = []
    #: carve-out id → (the context that would have to be supplied for it to
    #: fire, the base rules it claims). Never applied while pending.
    pending: dict[str, tuple[str, tuple[str, ...]]] = {}
    duplicates: list[str] = []
    #: base rule id → every carve-out claiming it, before any is applied
    claims: dict[str, list[LayeredException]] = {}
    #: carve-outs that cover only *part* of the query (underspecified role)
    role_ambiguous: set[str] = set()
    #: carve-out id → base rule ids it claims (computed once, in phase A)
    targets_by_exc: dict[str, tuple[str, ...]] = {}

    def _missing_inputs() -> list[str]:
        """What a consumer must supply, ordered: what the animal is, then who."""
        wanted = {token for token, _targets in pending.values()}
        return [token for token in MISSING_CONTEXT_ORDER if token in wanted]

    def _pending_on_governing_bases(governing_ids: set[str]) -> list[str]:
        """Withheld carve-outs that claim a base currently producing the answer.

        A carve-out withheld for a base that is *not* governing cannot change
        this answer, so it must not soften a prohibition into a conditional —
        that is how an operator-side carve-out would otherwise appear to reopen
        a mandatory legal ban (ADR-031 §14).
        """
        return [
            exc_id for exc_id, (_token, targets) in pending.items() if set(targets) & governing_ids
        ]

    def in_scope(layer: list[LayeredRule]) -> list[LayeredRule]:
        return [
            r
            for r in layer
            if _scope_matches(r, animal, service_role, declared_role)
            and _action_matches(r, action)
            and _in_time(r, now)
            and (r.zone_id is None or r.zone_id == zone_id)
        ]

    # --- 0. rule exceptions (SG-REAL-01): a matched exception replaces its
    # base rule for this query. Invalid exceptions (no source / not active)
    # never apply; conflicting matching exceptions force review, not a guess.
    matched: dict[str, LayeredException] = {}
    conflicted_rule_ids: set[str] = set()

    def _targets(exc: LayeredException) -> tuple[str, ...]:
        """Which base rules this carve-out claims (ADR-030: by instrument)."""
        if exc.binding == BindingMode.INSTRUMENT:
            bound, inert = bind_proviso_to_bases(exc, all_rules)
            for base_id in inert:
                steps.append(
                    f"jurisdiction proviso {exc.id} inert for rule {base_id} "
                    f"({JURISDICTION_EXCEPTION_INERT}): the base does not govern "
                    f"{exc.subject_scope_normalized or exc.animal_scope}; not applied."
                )
            return tuple(bound)
        return (exc.rule_id,)

    all_rules: list[LayeredRule] = [
        *legal,
        *guidance,
        *template_rules,
        *operator_rules,
        *event_rules,
    ]

    for exc in exceptions or []:
        if not exc.has_source():
            continue
        if not exc.active_at(now):
            continue
        probe = LayeredRule(
            id=f"exc-probe-{exc.id}",
            animal_scope=exc.animal_scope,
            action="enter",
            effect="allowed",
            rule_layer=None,
            origin="operator_direct",
            # ADR-025: a carve-out matches on the precise role the source named.
            # An exception stored as the generic `service_dog` (the unproven
            # widening) therefore matches nothing until it is re-modelled.
            subject_scope_normalized=exc.subject_scope_normalized,
            normalization_type=exc.normalization_type,
        )
        targets = _targets(exc)
        targets_by_exc[exc.id] = targets
        if not _carve_out_covers(exc, animal, service_role, declared_role) and _scope_matches(
            probe, animal, service_role, declared_role
        ):
            # A carve-out that covers *part* of an underspecified group query is
            # not irrelevant — it is unanswerable as asked. It still *claims*
            # its base, so a contradiction with another carve-out of that base
            # is recorded: that dispute is a governance fact and must not be
            # hidden by the asker's underspecification (ADR-031 §12).
            role_ambiguous.add(exc.id)
        # A carve-out that neither covers the query nor touches any of its
        # subjects is simply off-topic: it must not claim the base at all, or
        # an ordinary-dog question would be exempted by a guide-dog proviso.
        if _carve_out_covers(exc, animal, service_role, declared_role) or exc.id in role_ambiguous:
            for base_id in targets:
                claims.setdefault(base_id, []).append(exc)

    # --- phase B: per base, decide which carve-out (if any) governs --------
    for base_id, excs in claims.items():
        if len({e.effect for e in excs}) > 1:
            # Two carve-outs of one base disagreeing is a governance fact and
            # outranks the context withholding below: it is recorded before any
            # holder evaluation so a missing holder context cannot hide it.
            steps.append(
                f"exceptions {excs[0].id} vs {excs[1].id} conflict on rule "
                f"{base_id}: REVIEW_REQUIRED, not guessed."
            )
            conflicted_rule_ids.add(base_id)
            continue
        exc = excs[0]
        for duplicate in excs[1:]:
            # Same effect: a legacy venue row and the jurisdiction proviso say
            # the same thing. Provenance only — the effect is computed once.
            duplicates.append(duplicate.id)
        if exc.id in role_ambiguous:
            steps.append(
                f"exception {exc.id} withheld: it governs "
                f"{exc.subject_scope_normalized or exc.animal_scope} only, and the query "
                f"did not name a role ({MISSING_CONTEXT_SERVICE_ROLE} missing)."
            )
            pending[exc.id] = (MISSING_CONTEXT_SERVICE_ROLE, targets_by_exc.get(exc.id, ()))
            continue
        holder_match = evaluate_holder(exc.holder_scope, holder_context)
        if exc.holder_scope:
            steps.append(
                f"exception {exc.id} holder condition '{exc.holder_scope}' "
                f"({exc.subject_scope_normalized or exc.animal_scope}) evaluated: "
                f"{holder_match.value}."
            )
        if holder_match is HolderMatch.DOES_NOT_MATCH:
            steps.append(
                f"exception {exc.id} not applied for rule {base_id}: the holder "
                f"condition is not satisfied — the base rule governs."
            )
            continue
        if holder_match is HolderMatch.UNKNOWN:
            pending[exc.id] = (MISSING_CONTEXT_HOLDER_SCOPE, (base_id,))
            steps.append(
                f"exception {exc.id} withheld: it is conditional on the holder "
                f"({exc.holder_scope}) and no holder context was supplied "
                f"({MISSING_CONTEXT_HOLDER_SCOPE} missing) — not allowed, not prohibited."
            )
            continue
        if base_id in conflicted_rule_ids:
            continue
        matched[base_id] = exc

    def apply_exceptions(layer: list[LayeredRule]) -> list[LayeredRule]:
        out: list[LayeredRule] = []
        for r in layer:
            exc = matched.get(r.id)
            if exc is None:
                out.append(r)
                continue
            if r.id in conflicted_rule_ids:
                out.append(r)  # keep base governing; compliance flips below
                continue
            precise = exc.subject_scope_normalized or exc.animal_scope
            carve_out = " · carve-out" if exc.normative_effect == "exempt_from_prohibition" else ""
            suppressed.append(
                (
                    r,
                    f"exempted by exception {exc.id} (scope {precise}{carve_out}, "
                    f"source {exc.source_id})",
                )
            )
            applicable.append(
                LayeredRule(
                    id=f"exc-{exc.id}",
                    animal_scope=exc.animal_scope,
                    action=r.action,
                    effect=exc.effect,
                    rule_layer=r.rule_layer,
                    origin="exception",
                    conditions=exc.conditions,
                    zone_id=r.zone_id,
                    place_id=r.place_id,
                    source_id=exc.source_id,
                    mandatory_level=r.mandatory_level,
                )
            )
            applied_exceptions.append(exc.id)
        return out

    scoped_legal = apply_exceptions(in_scope(legal))
    scoped_guidance = apply_exceptions(in_scope(guidance))
    scoped_template = apply_exceptions(in_scope(template_rules))
    scoped_operator = apply_exceptions(in_scope(operator_rules))
    scoped_events = apply_exceptions(in_scope(event_rules))

    if not (
        scoped_legal
        or scoped_guidance
        or scoped_template
        or scoped_operator
        or scoped_events
        or applicable
    ):
        # applicable may hold exception-derived rules even when every base rule
        # was exempted for this query — those still govern.
        return EffectiveRuleSet(
            # ADR-030: keep the accumulated steps. A proviso judged inert for
            # this query is the *reason* nothing is in scope, and dropping it
            # would make "why is this unknown" unanswerable.
            explanation_steps=[*steps, "no in-scope rules in any layer"],
            compliance_state=ComplianceState.UNKNOWN,
            effect="unknown",
            applied_exceptions=applied_exceptions,
            pending_exceptions=sorted(pending),
            duplicate_exceptions=sorted(duplicates),
        )

    # --- 1. LEGAL layer -----------------------------------------------------
    # mandatory_level is normalised on read so the legacy 'discretionary'
    # spelling cannot hide a binding constraint (or invent one).
    def _is_mandatory(r: LayeredRule) -> bool:
        return normalize_mandatory_level(r.mandatory_level) == MandatoryLevel.MANDATORY.value

    legal_mandatory = [r for r in scoped_legal if _is_mandatory(r)]
    legal_other = [r for r in scoped_legal if not _is_mandatory(r)]
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
    mandatory_conditional = [r for r in legal_mandatory if r.effect == "conditional"]
    mandatory_conditions = [c for r in mandatory_conditional for c in r.conditions]

    # --- 2. lower layers: conflict-with-legal handling -----------------------
    # A lower layer may never silently relax the mandatory legal floor: neither
    # by outvoting a mandatory prohibition with an allowance, nor by dropping
    # the obligations of a mandatory legal condition.
    for group, label in (
        (scoped_guidance, "REGULATORY_GUIDANCE"),
        (scoped_template, "template"),
        (scoped_operator, "operator"),
        (scoped_events, "event"),
    ):
        for r in group:
            relaxes_prohibition = bool(mandatory_prohibited) and r.effect in (
                "allowed",
                "conditional",
            )
            drops_obligation = (
                bool(mandatory_conditional) and not mandatory_prohibited and r.effect == "allowed"
            )
            if relaxes_prohibition:
                suppressed.append(
                    (
                        r,
                        f"suppressed: MANDATORY legal prohibition (rule "
                        f"{mandatory_prohibited[0].id}) cannot be relaxed by {label}",
                    )
                )
            elif drops_obligation:
                suppressed.append(
                    (
                        r,
                        f"suppressed: MANDATORY legal condition (rule "
                        f"{mandatory_conditional[0].id}) cannot be dropped by {label}",
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

    if applied_exceptions:
        steps.append(
            f"{len(applied_exceptions)} rule exception(s) applied: "
            + ", ".join(sorted(applied_exceptions))
            + " (base rules exempted for this query)."
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
    if unknown_layer_rules or conflicted_rule_ids:
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
    # exception conditions are explicit normative content too: a conditional
    # statutory exemption (e.g. guide dogs must be leashed) surfaces as an
    # obligation exactly like the base rule's would.
    for r in applicable:
        if r.origin == "exception":
            legal_conditions.extend(dict(c) for c in r.conditions)
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
        if effect == "allowed" and mandatory_conditional:
            # a mandatory legal condition is not relaxable: an operator's plain
            # "allowed" cannot erase the statutory obligation.
            effect = "conditional"
            steps.append(
                "effect raised to conditional: MANDATORY legal condition "
                f"({mandatory_conditional[0].id}) cannot be dropped."
            )
        steps.append(f"effect from governing rules ({len(governing)}): {effect}.")
    else:
        effect = "unknown"
        steps.append("no governing rule after resolution: UNKNOWN, never guessed.")

    # --- 7. withheld carve-outs --------------------------------------------
    # A carve-out that could fire once the caller supplies a role or a holder
    # status is *not* a prohibition. Answering `prohibited` here would hide a
    # statutory right behind a missing input; answering `allowed` would apply a
    # condition that was never evaluated. CONDITIONAL + missing context is the
    # only honest third option (ADR-031 §7/§12).
    # Only a carve-out that claims a base *actually producing the prohibition*
    # can soften it. One withheld for an unrelated base cannot, and saying so
    # would look like that carve-out had reopened a ban it never touched.
    relevant = _pending_on_governing_bases({r.id for r in applicable if r.effect == "prohibited"})
    if (
        effect == "prohibited"
        and relevant
        and not conflicts
        and not conflicted_rule_ids
        and not unknown_layer_rules
    ):
        effect = "conditional"
        steps.append(
            f"effect raised to conditional: {len(relevant)} carve-out(s) withheld "
            f"pending {', '.join(_missing_inputs())} — supplying them can change "
            "this answer, so it is not reported as a final prohibition."
        )

    obligations = [str(c.get("condition_type", c)) for c in legal_conditions]
    return EffectiveRuleSet(
        applicable_rules=applicable,
        suppressed_rules=suppressed,
        unresolved_conflicts=conflicts,
        explanation_steps=steps,
        compliance_state=compliance,
        effect=effect,
        obligations=obligations,
        missing_inputs=_missing_inputs() if effect == "conditional" else [],
        applied_exceptions=applied_exceptions,
        pending_exceptions=sorted(pending),
        duplicate_exceptions=sorted(duplicates),
    )


def _unused() -> None:  # pragma: no cover - keeps imports referenced for clarity
    _by_specificity([])
