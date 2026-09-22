"""v0.9-R1 Rule–Reality Divergence — pure, deterministic difference description.

Design v0.9 §9: the platform carries two fact layers — the published **rule**
(what the operator/legal layer says) and the **reality** (what was observed on
site). Divergence states only describe the *difference* between the two; they
never rewrite either layer, never turn absence of a record into "no animals",
and never inflate one observation into a recurrence.

Why a separate module
---------------------
Rule logic lives in ``app.rulespec``; reality semantics live in
``app.services.reality_summary``. This module is the only place allowed to
compare them, so Home / Search / Map / Place all get the same divergence value
for the same inputs (AC9: no surface recomputes it).

The state vocabulary (frozen, one spelling):

- ``RULE_REALITY_ALIGNED``           rule effect and recent reality agree
- ``RULE_PROHIBITS_BUT_OBSERVED``    rule prohibits, animals were seen recently
- ``RULE_ALLOWS_BUT_NO_RECENT_RECORD`` rule allows, no recent on-site record
- ``RULE_UNKNOWN_BUT_OBSERVED``      no published rule, animals were seen
- ``RULE_CONDITIONAL_AND_OBSERVED``  rule is conditional, animals were seen
- ``INSUFFICIENT_DATA``              cannot compare honestly (no recent record,
                                     unverified inputs, dispute, unknown)

Invariants enforced by tests:

- Divergence is derived and read-only; it never mutates a rule or a claim.
- ``NO_RECENT_RECORD`` cases never read as "没有动物" (absence ≠ evidence of
  absence); the emitted note keeps the distinction.
- A disputed or unverified reality layer downgrades to ``INSUFFICIENT_DATA``.
- An ``unknown`` rule with recent observations is ``RULE_UNKNOWN_BUT_OBSERVED``,
  never an allowance and never a prohibition.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RuleEffect(StrEnum):
    """The effect vocabulary used by the rule layer (access_answer)."""

    ALLOWED = "allowed"
    PROHIBITED = "prohibited"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"


class DivergenceState(StrEnum):
    """Frozen vocabulary — exactly these six values describe the difference."""

    RULE_REALITY_ALIGNED = "RULE_REALITY_ALIGNED"
    RULE_PROHIBITS_BUT_OBSERVED = "RULE_PROHIBITS_BUT_OBSERVED"
    RULE_ALLOWS_BUT_NO_RECENT_RECORD = "RULE_ALLOWS_BUT_NO_RECENT_RECORD"
    RULE_UNKNOWN_BUT_OBSERVED = "RULE_UNKNOWN_BUT_OBSERVED"
    RULE_CONDITIONAL_AND_OBSERVED = "RULE_CONDITIONAL_AND_OBSERVED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


#: Reality summary states that mean "we have no trustworthy recent view".
#: Reality summary states that mean "we have no trustworthy view at all".
#: ``NO_RECENT_RECORD`` is deliberately NOT here: "no recent records" is itself a
#: trustworthy statement (absence of *records*, not absence of animals), so it can
#: be compared against a rule — yielding RULE_ALLOWS_BUT_NO_RECENT_RECORD etc.
UNTRUSTWORTHY_REALITY_STATES = frozenset({"INSUFFICIENT_OBSERVATION", "DISPUTED"})
OBSERVED_RECENTLY_STATES = frozenset({"OBSERVED_RECENTLY", "MULTI_EVIDENCE_OBSERVED"})


@dataclass(frozen=True)
class Divergence:
    """One divergence verdict, facts only.

    ``rule_effect`` and ``reality_state`` echo the inputs so a consumer can
    render its own nuance without re-deriving anything; ``note`` is the one
    sentence the platform is honest enough to ship.
    """

    state: DivergenceState
    rule_effect: str
    reality_state: str
    note: str


def divergence(
    *,
    rule_effect: str,
    reality_state: str,
) -> Divergence:
    """Describe the difference between one rule effect and one reality summary.

    Arguments
    ---------
    rule_effect:
        ``allowed | prohibited | conditional | unknown`` — the *resolved*
        normative result, never a raw candidate status.
    reality_state:
        one of the six ``RealitySummary`` states
        (``OBSERVED_RECENTLY / OBSERVED_HISTORICALLY / MULTI_EVIDENCE_OBSERVED /
        NO_RECENT_RECORD / INSUFFICIENT_OBSERVATION / DISPUTED``).

    Returns
    -------
    A frozen :class:`Divergence`. It never rewrites a rule or a reality claim.
    """
    rule = _normalize_effect(rule_effect)
    reality = _normalize_reality(reality_state)

    # ---- untrustworthy reality: we cannot describe a difference ----
    if reality in UNTRUSTWORTHY_REALITY_STATES:
        return Divergence(
            state=DivergenceState.INSUFFICIENT_DATA,
            rule_effect=rule,
            reality_state=reality,
            note=_insufficient_note(rule, reality),
        )

    # ---- no published rule at all ----
    if rule == RuleEffect.UNKNOWN:
        if reality in OBSERVED_RECENTLY_STATES:
            return Divergence(
                state=DivergenceState.RULE_UNKNOWN_BUT_OBSERVED,
                rule_effect=rule,
                reality_state=reality,
                note="没有已发布规则覆盖这次查询，但现场近期有动物出现 —— "
                "未知不等于允许，也不等于禁止。",
            )
        return Divergence(
            state=DivergenceState.INSUFFICIENT_DATA,
            rule_effect=rule,
            reality_state=reality,
            note="规则未知且现实层只有历史记录 —— 两者都无法给出现状判断。",
        )

    # ---- rule explicitly prohibits ----
    if rule == RuleEffect.PROHIBITED:
        if reality in OBSERVED_RECENTLY_STATES:
            return Divergence(
                state=DivergenceState.RULE_PROHIBITS_BUT_OBSERVED,
                rule_effect=rule,
                reality_state=reality,
                note="规则禁止，但现场近期确实出现过动物 —— 规则与现场存在差异，"
                "差异本身不改变规则效力。",
            )
        return Divergence(
            state=DivergenceState.RULE_REALITY_ALIGNED,
            rule_effect=rule,
            reality_state=reality,
            note="规则禁止；现实层没有与之矛盾的近期记录（没有近期记录 ≠ 没有动物）。",
        )

    # ---- rule explicitly allows ----
    if rule == RuleEffect.ALLOWED:
        if reality in OBSERVED_RECENTLY_STATES:
            return Divergence(
                state=DivergenceState.RULE_REALITY_ALIGNED,
                rule_effect=rule,
                reality_state=reality,
                note="规则允许，现场近期也确有动物活动 —— 规则与现实一致。",
            )
        return Divergence(
            state=DivergenceState.RULE_ALLOWS_BUT_NO_RECENT_RECORD,
            rule_effect=rule,
            reality_state=reality,
            note="规则允许，但近期没有现场记录可参照 —— 没有近期记录 ≠ 没有动物，"
            "只是现在没有证据。",
        )

    # ---- rule is conditional ----
    return Divergence(
        state=(
            DivergenceState.RULE_CONDITIONAL_AND_OBSERVED
            if reality in OBSERVED_RECENTLY_STATES
            else DivergenceState.RULE_REALITY_ALIGNED
        ),
        rule_effect=rule,
        reality_state=reality,
        note=(
            "规则有条件；现场近期确有动物活动 —— 差异仅在于条件是否满足，"
            "具体条件见 condition_evaluation。"
            if reality in OBSERVED_RECENTLY_STATES
            else "规则附条件；现实层无近期相反记录（无近期记录 ≠ 没有动物）。"
        ),
    )


def _normalize_effect(value: str) -> RuleEffect:
    if value is None:
        return RuleEffect.UNKNOWN
    text = str(value).strip().lower()
    for effect in RuleEffect:
        if text in (effect.value, effect.name.lower()):
            return effect
    return RuleEffect.UNKNOWN


def _normalize_reality(value: str) -> str:
    text = str(value or "").strip().upper()
    known = {
        "OBSERVED_RECENTLY",
        "OBSERVED_HISTORICALLY",
        "MULTI_EVIDENCE_OBSERVED",
        "NO_RECENT_RECORD",
        "INSUFFICIENT_OBSERVATION",
        "DISPUTED",
    }
    return text if text in known else "INSUFFICIENT_OBSERVATION"


def _insufficient_note(rule: str, reality: str) -> str:
    if reality == "DISPUTED":
        return "现实记录存在争议 —— 在争议解决前不做规则与现实对比。"
    if reality == "INSUFFICIENT_OBSERVATION":
        return "现实层证据不足或尚未完成人工核验 —— 无法可靠对比。"
    if reality == "NO_RECENT_RECORD":
        return "没有近期现场记录（≠ 没有动物）—— 无法把规则与现场对比。"
    return f"现实层状态 {reality} 无法与规则 {rule} 对比。"
