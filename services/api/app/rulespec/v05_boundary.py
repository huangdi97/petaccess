"""BoundaryMatcher (NEXT_GOAL §B9, COEXISTENCE_BOUNDARY_SPEC).

Matches a user's BoundaryProfile preferences against a place's structured
coexistence attributes (+ effective access). Returns per-item MATCH / CONFLICT
/ UNKNOWN with reasons — NEVER a total score, never a place rating.

Three permanently separated planes:
  Rule = what the operator states        (coexistence attributes / access rules)
  Observation = what users saw           (never an input here)
  Boundary = what this user accepts      (preferences input)
"""

from __future__ import annotations

from dataclasses import dataclass

# attributes where a missing value can be derived from the effective access
# rules (indoor/outdoor entry) instead of UNKNOWN-with-no-hint
_DERIVABLE = {
    "ordinary_pet_indoor_dining": "indoor",
    "ordinary_pet_outdoor_dining": "outdoor",
}


@dataclass(frozen=True)
class PreferenceResult:
    attribute: str
    stance: str
    verdict: str  # MATCH | CONFLICT | UNKNOWN
    reason: str


def _value_verdict_for_accept(value: str) -> str:
    if value in ("allowed", "available", "conditional"):
        return "MATCH"
    if value in ("prohibited", "not_available"):
        return "CONFLICT"
    return "UNKNOWN"


def match(
    *,
    effective_effect: str,
    coexistence: dict[str, str],
    preferences: list[tuple[str, str]],
) -> list[PreferenceResult]:
    """effective_effect: overall access effect ('allowed'|'conditional'|
    'prohibited'|'unknown') used only to derive the two dining attributes.
    coexistence: attribute -> value. preferences: (attribute, stance) pairs."""

    results: list[PreferenceResult] = []
    for attribute, stance in preferences:
        value = coexistence.get(attribute)

        if value is None and attribute in _DERIVABLE:
            if effective_effect == "allowed":
                value = "allowed"
            elif effective_effect == "prohibited":
                value = "prohibited"
            elif effective_effect == "conditional":
                value = "conditional"

        if value is None:
            results.append(
                PreferenceResult(
                    attribute, stance, "UNKNOWN", "场所未结构化记录该属性（信息不足，不猜测）"
                )
            )
            continue

        if stance == "accept":
            verdict = _value_verdict_for_accept(value)
            reason = f"属性={value}，你的边界=可接受"
        elif stance == "avoid":
            if value in ("prohibited", "not_available"):
                verdict, reason = "MATCH", f"属性={value}，你的边界=希望没有"
            elif value in ("allowed", "available"):
                verdict, reason = "CONFLICT", f"属性={value}，与你的边界冲突"
            else:
                verdict, reason = "UNKNOWN", f"属性={value}，需人工判断"
        elif stance == "require_prohibited":
            if value == "prohibited":
                verdict, reason = "MATCH", "场所明确禁止，符合你的要求"
            elif value == "allowed":
                verdict, reason = "CONFLICT", "场所允许，与你的硬性要求冲突"
            else:
                verdict, reason = "UNKNOWN", f"属性={value}，没有明确禁止（不当作禁止）"
        elif stance == "prefer":
            if value == "available":
                verdict, reason = "MATCH", "场所提供该条件"
            elif value == "not_available":
                verdict, reason = "CONFLICT", "场所明确没有该条件"
            else:
                verdict, reason = "UNKNOWN", f"属性={value}，偏好项信息不足"
        else:
            verdict, reason = "UNKNOWN", f"未知边界类型 {stance}"

        results.append(PreferenceResult(attribute, stance, verdict, reason))
    return results
