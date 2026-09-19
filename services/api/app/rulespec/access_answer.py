"""Unified AccessAnswer — the one answer model every consumer surface reads.

Why this module exists
----------------------
Design §10 (AGENT_MASTER_CONTINUE): 首页 / Search / Map Card / Place Detail /
H5 Share / Watch 必须消费**统一答案模型**，且「禁止页面自行算 Rule」。 A surface
that only receives `effect` has to re-derive everything else — scope, conditions,
what the evidence actually is — and then two surfaces disagree.

The Century Park release (2026-09-19) sharpened a second requirement: the answer
must be able to say **what the evidence is**, not just what the rule says. That
row is published from a government platform relaying the operator's own wording,
with no first-party operator source obtained (`FIRST_PARTY_OPERATOR_SOURCE_PENDING`).
A model that cannot express that would force every surface to either hide it or
invent a comforting sentence.

Three deliberate refusals, each an existing domain invariant:

1. **The model cannot express 「官方已确认」.** No field's value could mean it.
   `evidence_state` is *derived* from stored source facts (`source_type`,
   `directness`, `issuer_verification`) plus whether a first-party operator
   source exists at all. A claim you cannot fill is a claim you cannot fake.
2. **A zone rule is never flattened into a place verdict.** `scope_summary`
   states the level that actually governs, and there is no code path that turns
   "no rule in scope" into `allowed` (UNKNOWN ≠ ALLOWED).
3. **A withheld carve-out yields `conditional` + `missing_inputs`**, never a bare
   prohibition and never an unconditional allowance (ADR-031).

Pure by construction: every database fact arrives as an argument, so the builder
is exhaustively unit-testable and the HTTP layer holds no rule logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

#: Bump when the shape or the derivation rules change. Consumers key off this
#: instead of guessing from the presence of fields.
ACCESS_ANSWER_VERSION = "access-answer/1"

#: Human-adjudicated meaning of a ``source_type``. **Only values whose semantics a
#: named reviewer actually decided get an entry here.** Writing a plausible
#: sentence for the remaining enum values would be precisely the "helpful
#: paraphrase" this platform must not ship — and it would read, downstream, as
#: something the platform asserted.
#: `government_service` = B4 adjudication, 2026-09-19 (huangdi97):
#: 「接受政府发布来源作为可发布 Evidence，语义 = 政府平台转述园方口径」.
SOURCE_TYPE_SEMANTICS: dict[str, str] = {
    "government_service": "政府平台转述园方口径",
}

#: Sentences that assert a first-party/confirmed status. The model has no field
#: capable of carrying them when no first-party operator source exists, and
#: :func:`assert_no_unbacked_first_party_claim` keeps it that way.
#:
#: Note what is deliberately *absent*: `official_operator_policy` is a legitimate
#: `source_type` **value**, so banning the token would break the honest case
#: (the Shanghai Zoo source really is the operator's own page). The thing to
#: forbid is the *claim*, not the vocabulary.
FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "官方已确认",
    "官方确认",
    "运营方已确认",
    "operator first-party verified",
    "first-party verified",
    "一手来源已核验",
    "已核验一手来源",
)

#: effect value used when nothing governs. Spelled out rather than inlined so the
#: "unknown is not allowed" rule has exactly one spelling.
UNKNOWN_EFFECT = "unknown"


@dataclass(frozen=True)
class PlaceFacts:
    id: str
    canonical_name: str
    place_type: str


@dataclass(frozen=True)
class ZoneFacts:
    id: str
    name: str
    zone_type: str = "area"


@dataclass(frozen=True)
class RuleFacts:
    """Everything the answer needs about one governing rule, source included."""

    rule_id: str
    rule_layer: str | None = None
    mandatory_level: str | None = None
    source_id: str | None = None
    source_type: str | None = None
    issuer: str | None = None
    directness: str | None = None
    issuer_verification: str | None = None
    evidence_strength: str | None = None
    source_url: str | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    supersedes_rule_id: str | None = None
    source_scope_exact: str | None = None
    subject_scope_normalized: str | None = None
    normalization_type: str | None = None


def first_party_operator_source_exists(*, source_type: str | None, directness: str | None) -> bool:
    """Is the governing evidence the operator's **own** channel, captured directly?

    Deliberately narrow. A statute is direct evidence about the *law*, not
    first-party evidence about the *venue*; a government platform relaying the
    operator is exactly the case that must not count.
    """
    return source_type == "official_operator_policy" and directness == "direct"


def _evidence_entry(rule_id: str, facts: RuleFacts | None) -> dict[str, Any]:
    if facts is None:
        return {
            "rule_id": rule_id,
            "source_id": None,
            "source_type": None,
            "source_type_semantics": None,
            "issuer": None,
            "directness": None,
            "issuer_verification": None,
            "evidence_strength": None,
            "source_url": None,
            "first_party_operator_source_pending": True,
            "provenance_statement": "该规则没有可追溯来源 —— 来源缺失本身就是要显示的事实。",
        }
    pending = not first_party_operator_source_exists(
        source_type=facts.source_type, directness=facts.directness
    )
    semantics = SOURCE_TYPE_SEMANTICS.get(facts.source_type or "")
    parts = []
    if facts.issuer:
        parts.append(f"来源：{facts.issuer}")
    parts.append(f"source_type={facts.source_type or '未记录'}")
    if semantics:
        parts.append(f"（{semantics}）")
    if facts.directness:
        parts.append(f"directness={facts.directness}")
    if facts.evidence_strength:
        parts.append(f"evidence_strength={facts.evidence_strength}")
    if pending:
        parts.append("未取得运营方一手来源（first-party operator source pending）")
    return {
        "rule_id": rule_id,
        "source_id": facts.source_id,
        "source_type": facts.source_type,
        "source_type_semantics": semantics,
        "issuer": facts.issuer,
        "directness": facts.directness,
        "issuer_verification": facts.issuer_verification,
        "evidence_strength": facts.evidence_strength,
        "source_url": facts.source_url,
        "first_party_operator_source_pending": pending,
        "provenance_statement": "；".join(parts) + "。",
    }


def _scope_level(rule_set_governing: list[Any], zone_id: str | None) -> str:
    """Which level actually decided this answer — never a flattening."""
    if not rule_set_governing:
        return "none"
    layers = {getattr(r, "rule_layer", None) for r in rule_set_governing}
    if layers == {"LEGAL"}:
        return "jurisdiction"
    if zone_id and all(getattr(r, "zone_id", None) for r in rule_set_governing):
        return "zone"
    if all(getattr(r, "zone_id", None) is None for r in rule_set_governing):
        return "place"
    return "mixed"


def _next_actions(
    *,
    effect: str,
    missing_inputs: list[str],
    scope_level: str,
    zone_requested: bool,
) -> list[str]:
    actions: list[str] = []
    if missing_inputs:
        actions.append("补充 " + "、".join(missing_inputs) + " 后可得到更确定的结论。")
    if effect == UNKNOWN_EFFECT:
        actions.append("当前没有已发布规则覆盖这次查询 —— 未知不等于允许。")
        if not zone_requested:
            actions.append(
                "该场所的规则可能落在具体区域上。指定区域后重新求值，"
                "不要把场所整体读成任何一个结论。"
            )
        elif scope_level == "none":
            actions.append("可以现场拍摄规则牌提交核验。")
    if effect == "conditional":
        actions.append("结论附有条件，进入前请逐条确认。")
    return actions


def _normative_summary(
    *, effect: str, place_name: str, zone_name: str | None, governing: list[Any]
) -> str:
    where = f"{place_name}·{zone_name}" if zone_name else place_name
    if effect == "prohibited":
        return f"{where}：禁止。"
    if effect == "allowed":
        return f"{where}：允许。"
    if effect == "conditional":
        return f"{where}：有条件允许 —— 条件见 condition_evaluation。"
    return f"{where}：规则未知（未覆盖），不得据此认为允许。"


def build_access_answer(
    *,
    query: dict[str, Any],
    place: PlaceFacts,
    zone: ZoneFacts | None,
    rule_set: Any,
    rule_facts: dict[str, RuleFacts] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Assemble the unified answer from a canonical ``EffectiveRuleSet``.

    ``rule_set`` is the *resolver's* output object; this function never re-decides
    the effect. It arranges what the resolver decided, plus the provenance and
    validity facts a consumer surface needs to state honestly where the answer
    comes from.
    """
    now = now or datetime.now(UTC)
    facts = dict(rule_facts or {})
    governing = list(getattr(rule_set, "applicable_rules", []) or [])
    governing_ids = [str(getattr(r, "id", "")) for r in governing]

    effect = str(getattr(rule_set, "effect", UNKNOWN_EFFECT))
    raw_state = getattr(rule_set, "compliance_state", None)
    # StrEnum members stringify to their own value; a plain string passes through.
    compliance_state = str(getattr(raw_state, "value", raw_state) or "UNKNOWN")
    missing_inputs = list(getattr(rule_set, "missing_inputs", []) or [])
    unresolved = [
        [str(getattr(a, "id", a)), str(getattr(b, "id", b))]
        for a, b in (getattr(rule_set, "unresolved_conflicts", []) or [])
    ]
    suppressed = [
        {"rule": str(getattr(r, "id", r)), "reason": reason}
        for r, reason in (getattr(rule_set, "suppressed_rules", []) or [])
    ]

    scope_level = _scope_level(governing, zone.id if zone else None)

    evidence_entries = [_evidence_entry(rid, facts.get(rid)) for rid in governing_ids]
    pendings = [e["first_party_operator_source_pending"] for e in evidence_entries]

    normative_effects: list[str] = []
    for r in governing:
        value = getattr(r, "normative_effect", None)
        if value is not None and str(value) not in normative_effects:
            normative_effects.append(str(value))
    normative_effects.sort()
    obligations: list[str] = []
    for r in governing:
        for obligation in getattr(r, "operator_obligations", ()) or ():
            if obligation not in obligations:
                obligations.append(obligation)

    valid_untils = [f.effective_to for f in facts.values() if f.effective_to is not None]
    valid_froms = [f.effective_from for f in facts.values() if f.effective_from is not None]

    answer: dict[str, Any] = {
        "query_context": dict(query),
        "normative_result": {
            "effect": effect,
            "compliance_state": compliance_state,
            "summary": _normative_summary(
                effect=effect,
                place_name=place.canonical_name,
                zone_name=zone.name if zone else None,
                governing=governing,
            ),
            "governing_rule_ids": governing_ids,
            "governing_layer": sorted(
                {
                    str(getattr(r, "rule_layer", None))
                    for r in governing
                    if getattr(r, "rule_layer", None)
                }
            ),
            "mandatory_levels": sorted(
                {
                    str(getattr(r, "mandatory_level", None))
                    for r in governing
                    if getattr(r, "mandatory_level", None)
                }
            ),
        },
        "condition_evaluation": {
            "conditions": [
                dict(c) for r in governing for c in (getattr(r, "conditions", ()) or ())
            ],
            "unmet": [],  # the resolver reports unmet conditions on the v1 path only
            "missing_inputs": missing_inputs,
            "pending_exceptions": list(getattr(rule_set, "pending_exceptions", []) or []),
        },
        "scope_summary": {
            "place": {"id": place.id, "name": place.canonical_name, "place_type": place.place_type},
            "zone": (
                {"id": zone.id, "name": zone.name, "zone_type": zone.zone_type} if zone else None
            ),
            "zone_requested": bool(query.get("zone_id")),
            "scope_level": scope_level,
            "zone_scoped_rule_count": sum(1 for r in governing if getattr(r, "zone_id", None)),
            "animal_scope_requested": query.get("animal"),
            "declared_role": query.get("declared_role"),
        },
        "evidence_state": {
            "rules": evidence_entries,
            "first_party_operator_source_pending": any(pendings) if pendings else True,
            "first_party_operator_source_count": sum(1 for p in pendings if not p),
            "weakest_directness": _weakest([e["directness"] for e in evidence_entries]),
            "acceptance_required": any(
                e["evidence_strength"] in {"search_snippet", "social_lead"}
                for e in evidence_entries
            ),
        },
        "conflict_state": {
            "has_conflict": bool(unresolved) or compliance_state == "POTENTIAL_CONFLICT",
            "compliance_state": compliance_state,
            "unresolved_conflicts": unresolved,
            "suppressed": suppressed,
        },
        "rights_information": {
            "normative_effects": normative_effects,
            "operator_obligations": obligations,
            "facilitation_required": "facilitation_required" in normative_effects,
            "holder_scopes": sorted(
                {
                    getattr(r, "holder_scope", None)
                    for r in governing
                    if getattr(r, "holder_scope", None)
                }
            ),
        },
        "matched_rule_versions": [
            {
                "rule_id": rid,
                "rule_layer": getattr(r, "rule_layer", None),
                "mandatory_level": getattr(r, "mandatory_level", None),
                "zone_id": getattr(r, "zone_id", None),
                "source_scope_exact": getattr(r, "source_scope_exact", None),
                "subject_scope_normalized": getattr(r, "subject_scope_normalized", None),
                "normalization_type": getattr(r, "normalization_type", None),
                "normative_effect": getattr(r, "normative_effect", None),
                "effective_from": facts[rid].effective_from if rid in facts else None,
                "effective_to": facts[rid].effective_to if rid in facts else None,
                "supersedes_rule_id": facts[rid].supersedes_rule_id if rid in facts else None,
            }
            for rid, r in zip(governing_ids, governing, strict=False)
        ],
        "explanation_items": list(getattr(rule_set, "explanation_steps", []) or []),
        "next_actions": _next_actions(
            effect=effect,
            missing_inputs=missing_inputs,
            scope_level=scope_level,
            zone_requested=bool(query.get("zone_id")),
        ),
        "evaluated_at": now.isoformat(),
        "valid_until": min(valid_untils).isoformat() if valid_untils else None,
        "valid_from": min(valid_froms).isoformat() if valid_froms else None,
        "evaluation_version": ACCESS_ANSWER_VERSION,
    }
    assert_no_unbacked_first_party_claim(answer)
    return answer


def _weakest(directness: list[str | None]) -> str | None:
    order = {"direct": 0, "secondary": 1, "tertiary": 2}
    known = [d for d in directness if d in order]
    if not known:
        return None
    return max(known, key=lambda d: order[d])


def assert_no_unbacked_first_party_claim(answer: dict[str, Any]) -> None:
    """Fail loudly rather than ship a sentence the evidence cannot support.

    The rule: a "confirmed by the operator / first-party" claim requires a
    first-party operator source. When the answer's own `evidence_state` says none
    exists, no such sentence may appear anywhere in it.

    Called on every build. A field added carelessly later would either trip this
    or would not — and if it does not, the phrase was not there to begin with.
    """
    import json

    evidence = answer.get("evidence_state") or {}
    if evidence.get("first_party_operator_source_count"):
        return
    blob = json.dumps(answer, ensure_ascii=False, default=str)
    hits = [claim for claim in FORBIDDEN_CLAIMS if claim in blob]
    if hits:
        raise AssertionError(
            f"AccessAnswer 在无一手运营方来源时含越权表述 {hits} —— "
            "这正是本机制存在的目的：不得把『政府平台转述』读成『官方已确认』。"
        )


def as_plain(value: Any) -> Any:
    """JSON-safe copy — datetimes (including ones nested in facts) become ISO."""
    if isinstance(value, dict):
        return {k: as_plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [as_plain(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "__dataclass_fields__"):
        return as_plain(asdict(value))
    return value
