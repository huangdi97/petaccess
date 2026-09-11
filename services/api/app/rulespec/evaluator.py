"""Deterministic rule evaluator (ADR-005, design #12).

Contract:
- pure functions; no DB, no I/O, no LLM
- input: QueryContext + iterable[Rule]
- output: ApplicabilityResult with status in {MATCH, CONDITIONAL, RESTRICTED,
  UNKNOWN, CONFLICT}

Status semantics (never guess, never treat unknown as allowed/prohibited):
- RESTRICTED wins over everything except explicit conflicts: a definitive
  prohibition anywhere in scope makes the result RESTRICTED.
- CONFLICT: two or more current rules in scope make directly opposing
  determinations (allowed vs prohibited) for the same action/animals, and the
  conflict cannot be resolved by specificity (zone-level beats place-level).
- UNKNOWN: no applicable rule found, or an applicable rule needs an input the
  query does not provide (e.g. max_weight_kg without weight).
- CONDITIONAL: applicable rule(s) allow but require unmet obligations, or the
  most specific applicable rule is conditional.
- MATCH: applicable rule(s) directly allow without missing inputs.
"""

from __future__ import annotations

from datetime import datetime

from .model import (
    AnimalInput,
    AnimalScope,
    ApplicabilityResult,
    Condition,
    QueryContext,
    ResultStatus,
    Rule,
    RuleAction,
    RuleEffect,
    RuleStatus,
    UnknownInput,
    UnmetCondition,
)

# A rule in any of these statuses does not govern current queries.
_NON_GOVERNING = {RuleStatus.SUPERSEDED, RuleStatus.WITHDRAWN, RuleStatus.ARCHIVED}

# Condition types whose semantics are "the animal/party must provide X".
_OBLIGATION_CONDITIONS = {
    "leash_required",
    "muzzle_required",
    "carrier_required",
    "stroller_required",
    "no_ground",
    "registration_required",
    "vaccination_required",
    "reservation_required",
    "advance_notice_required",
}

# Condition types whose numeric/threshold semantics need the query's animal data.
_THRESHOLD_CONDITIONS = {
    "max_weight_kg",
    "min_weight_kg",
    "max_shoulder_height_cm",
    "max_count",
}


def _animal_scope_matches(rule: Rule, animal: AnimalInput) -> bool:
    """Scope match with service_dog separated from ordinary pet (design #19)."""
    if rule.animal_scope == AnimalScope.SERVICE_DOG:
        # service dog rules only ever govern a service dog query; a working dog
        # still counts as a dog for ordinary-pet rules unless the rule is scoped
        # to ordinary_pet.
        return animal.service_role in ("working", "in_training", "unknown")
    if rule.animal_scope == AnimalScope.ORDINARY_PET:
        # ordinary_pet means the rule speaks about pets generally; a service dog
        # query is NOT governed by an ordinary-pet rule (service dog通行权独立).
        if animal.service_role in ("working", "in_training"):
            return False
        return animal.species in ("dog", "cat", "other")
    if rule.animal_scope == AnimalScope.DOG:
        return animal.species == "dog"
    if rule.animal_scope == AnimalScope.CAT:
        return animal.species == "cat"
    return True  # other


def _action_matches(rule: Rule, action: RuleAction) -> bool:
    """The evaluator treats a rule as governing the query when actions align."""
    return rule.action == action


def _rule_in_scope(rule: Rule, ctx: QueryContext, now: datetime) -> bool:
    if rule.status in _NON_GOVERNING:
        return False
    if not _animal_scope_matches(rule, ctx.animal):
        return False
    if not _action_matches(rule, ctx.intended_action):
        return False
    if rule.zone_id is not None and ctx.zone_id != rule.zone_id:
        return False
    if rule.place_id is not None and rule.place_id != ctx.place_id:
        return False
    if rule.zone_id is None and rule.place_id is None:
        # bare rule with no spatial owner cannot govern a place query
        return False
    if rule.effective_from is not None and now < rule.effective_from:
        return False
    return not (rule.effective_to is not None and now > rule.effective_to)


def _time_in_windows(now: datetime, windows: dict | list | None) -> bool:
    """time_windows value_json: [{"days":[0..6], "start":"21:00", "end":"23:30"}].

    Wraparound allowed (e.g. 22:00–02:00). Empty/invalid windows => not inside.
    """
    if not windows:
        return False
    if isinstance(windows, dict):
        windows = [windows]
    weekday = now.weekday()
    minutes = now.hour * 60 + now.minute
    for w in windows:
        days = w.get("days")
        if days is not None and weekday not in days:
            continue
        start = w.get("start")
        end = w.get("end")
        if not start or not end:
            continue
        try:
            sh, sm = (int(x) for x in start.split(":"))
            eh, em = (int(x) for x in end.split(":"))
        except ValueError:
            continue
        s, e = sh * 60 + sm, eh * 60 + em
        if s <= e:
            if s <= minutes < e:
                return True
        else:  # overnight window
            if minutes >= s or minutes < e:
                return True
    return False


def _eval_condition(cond: Condition, ctx: QueryContext, now: datetime) -> tuple[bool, str | None]:
    """Return (satisfied, unknown_input_key)."""
    animal = ctx.animal
    ct = cond.condition_type
    if ct in _OBLIGATION_CONDITIONS:
        # An obligation like leash_required is satisfied only when the query
        # states the animal is prepared for it. Not stated => not satisfied.
        if cond.value_flag is False:
            return True, None
        # obligations are unmet unless the query explicitly affirms capability
        return False, None
    if ct in _THRESHOLD_CONDITIONS:
        numeric = cond.value_numeric
        if numeric is None:
            # malformed condition; never fabricate a verdict from it
            return True, None
        if ct == "max_weight_kg":
            if animal.weight_kg is None:
                return False, "weight_kg"
            return animal.weight_kg <= numeric, None
        if ct == "min_weight_kg":
            if animal.weight_kg is None:
                return False, "weight_kg"
            return animal.weight_kg >= numeric, None
        if ct == "max_shoulder_height_cm":
            if animal.shoulder_height_cm is None:
                return False, "shoulder_height_cm"
            return animal.shoulder_height_cm <= numeric, None
        if ct == "max_count":
            if animal.count is None:
                return False, "count"
            return animal.count <= (numeric or 1), None
    if ct == "time_windows":
        inside = _time_in_windows(now, cond.value_json)
        if not inside:
            return False, None
        return True, None
    if ct == "date_windows":
        inside = _time_in_windows(now, cond.value_json)
        return inside, None
    # free-text / note-only conditions never block by themselves
    return True, None


def evaluate(ctx: QueryContext, rules: list[Rule]) -> ApplicabilityResult:
    now = ctx.date_time
    in_scope = [r for r in rules if _rule_in_scope(r, ctx, now)]
    if not in_scope:
        return ApplicabilityResult(
            status=ResultStatus.UNKNOWN,
            reason_codes=["no_rule_in_scope"],
        )

    # Specificity resolution: for a zone query, zone-level rules shadow
    # place-level rules on the same (scope, action) so a zone's explicit rule
    # always wins over the place's blanket rule (design #12 "Zone 覆盖 Place").
    resolved = _resolve_specificity(in_scope, ctx)

    prohibited = [r for r in resolved if r.effect == RuleEffect.PROHIBITED]
    allowed = [r for r in resolved if r.effect == RuleEffect.ALLOWED]
    conditional = [r for r in resolved if r.effect == RuleEffect.CONDITIONAL]

    # CONFLICT detection among governing (post-specificity) rules.
    if prohibited and allowed:
        return ApplicabilityResult(
            status=ResultStatus.CONFLICT,
            matched_rules=[r.id for r in prohibited] + [r.id for r in allowed],
            reason_codes=["conflicting_rules_allowed_vs_prohibited"],
            source_refs=_source_refs(resolved),
        )

    source_refs = _source_refs(resolved)
    matched_ids = [r.id for r in resolved]

    if prohibited:
        return ApplicabilityResult(
            status=ResultStatus.RESTRICTED,
            matched_rules=matched_ids,
            reason_codes=["explicit_prohibition"],
            source_refs=source_refs,
        )

    if conditional:
        unmet: list[UnmetCondition] = []
        unknown: list[UnknownInput] = []
        for r in conditional:
            for cond in r.conditions:
                satisfied, unknown_key = _eval_condition(cond, ctx, now)
                if not satisfied:
                    if unknown_key is not None:
                        # threshold condition whose input is missing → UNKNOWN
                        unknown.append(
                            UnknownInput(
                                input=unknown_key, reason=f"rule {r.id} requires {unknown_key}"
                            )
                        )
                        continue
                    unmet.append(
                        UnmetCondition(
                            rule_id=r.id, condition_type=cond.condition_type, kind="obligation"
                        )
                    )
        if unknown:
            return ApplicabilityResult(
                status=ResultStatus.UNKNOWN,
                matched_rules=matched_ids,
                unmet_conditions=unmet,
                unknown_inputs=unknown,
                reason_codes=["missing_query_input"],
                source_refs=source_refs,
            )
        if unmet:
            return ApplicabilityResult(
                status=ResultStatus.CONDITIONAL,
                matched_rules=matched_ids,
                unmet_conditions=unmet,
                reason_codes=["conditions_unmet"],
                source_refs=source_refs,
            )
        return ApplicabilityResult(
            status=ResultStatus.MATCH,
            matched_rules=matched_ids,
            reason_codes=["conditional_conditions_met"],
            source_refs=source_refs,
        )

    if allowed:
        return ApplicabilityResult(
            status=ResultStatus.MATCH,
            matched_rules=matched_ids,
            reason_codes=["explicitly_allowed"],
            source_refs=source_refs,
        )

    return ApplicabilityResult(
        status=ResultStatus.UNKNOWN,
        reason_codes=["no_rule_in_scope"],
    )


def _source_refs(rules: list[Rule]) -> list[str]:
    return sorted({r.source_id for r in rules if r.source_id})


def _resolve_specificity(in_scope: list[Rule], ctx: QueryContext) -> list[Rule]:
    """Zone-level rules shadow place-level rules when a zone is targeted.

    Group by (animal_scope, action); if any zone-level rule exists in the group,
    drop place-level rules from that group. This implements 'Zone 覆盖 Place'
    without ever fabricating a result.
    """
    groups: dict[tuple[AnimalScope, RuleAction], list[Rule]] = {}
    for r in in_scope:
        groups.setdefault((r.animal_scope, r.action), []).append(r)

    resolved: list[Rule] = []
    for _key, members in groups.items():
        zone_rules = [m for m in members if m.zone_id is not None]
        if ctx.zone_id is not None and zone_rules:
            resolved.extend(m for m in members if m.zone_id is not None)
        else:
            resolved.extend(members)
    return resolved
