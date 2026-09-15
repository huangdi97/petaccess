"""Generate the R2 human review packet + machine register (GOV-01, ADR-025).

Why R2 exists
-------------

R1 was generated under the OLD animal-scope model: every 导盲犬 proviso was
stored as ``animal_scope='service_dog'``, and the packet asked the reviewer to
"confirm the ADR-020 generalisation". ADR-025 established that this is not a
generalisation at all — it is an ontology inference being used as a legal
argument. R1's AI recommendations therefore cannot be inherited: they were
computed against a scope claim the platform has now withdrawn.

This script recomputes every recommendation from scratch under the
source-faithful model, and never decides anything itself:

  * ``final_decision`` / ``reviewer`` / ``reviewed_at`` are emitted **empty**.
    The AI never signs (Master Goal §0.9 / ADR-005).
  * Rows whose source wording supports a single precise role carry
    ``subject_scope_normalized`` + ``normalization_type='exact'``.
  * Rows whose source names several roles at once (上海图书馆: 导盲犬、军警犬)
    are **held** — the register models one row per rule and the source requires
    three precise scopes; a human must split it.
  * ``gh-outdoor-keep`` is rejected with the two reason codes the Master Goal
    requires (INSUFFICIENT_PLACE_ZONE_EVIDENCE + LEGAL_SCOPE_CONFLICT).
  * The Manner 凯德虹口 attribution error stays rejected.

Outputs
-------

  * ``docs/reality_audit/review_decisions_r2.json`` — the machine register
  * ``HUMAN_REVIEW_PACKET_R2.md``                 — one block per candidate
  * ``HUMAN_REVIEW_QUICK_TABLE_R2.md``            — one line per candidate
  * ``HUMAN_REVIEW_DECISIONS_R2.json``            — the blank sign-off template

Usage: python scripts/gen_human_review_packet_r2.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "docs" / "reality_audit"
REGISTRY_R1 = AUDIT / "review_decisions_r1.json"
REGISTRY_R2 = AUDIT / "review_decisions_r2.json"

PACKET = REPO / "HUMAN_REVIEW_PACKET_R2.md"
DECISION_TEMPLATE = REPO / "HUMAN_REVIEW_DECISIONS_R2.json"
QUICK_TABLE = REPO / "HUMAN_REVIEW_QUICK_TABLE_R2.md"

WEAK = {"search_snippet", "social_lead"}
ATTRIBUTION_ERROR_RULE = "mn-outdoor-media"
OUTDOOR_KEEP_RULE = "gh-outdoor-keep"

STATUTE_SRC = "sh_dog_regulation"
GUIDE_DOG_PROVISO = "导盲犬"

#: rule_id → (source_scope_exact, subject_scope_normalized, normalization_type,
#:            normative_effect, holder_scope)
#:
#: Every entry is a *reading of the source*, not a platform convenience. Rows not
#: listed here inherit the conservative default for their coarse scope (dog /
#: ordinary_pet are exact; bare service_dog confers nothing).
PRECISE_SCOPE: dict[str, tuple[str | None, str | None, str, str | None, str | None]] = {
    # 《上海市养犬管理条例》第23条 但书: 「盲人携带导盲犬的，不受本条规定的限制。」
    # Sourced from the statute itself → 导盲犬, held by a person with a disability.
    "dl-sd-legal": (
        GUIDE_DOG_PROVISO,
        "guide_dog",
        "exact",
        "exempt_from_prohibition",
        "person_with_disability",
    ),
    "fp-sd-legal": (
        GUIDE_DOG_PROVISO,
        "guide_dog",
        "exact",
        "exempt_from_prohibition",
        "person_with_disability",
    ),
    "gh-sd-legal": (
        GUIDE_DOG_PROVISO,
        "guide_dog",
        "exact",
        "exempt_from_prohibition",
        "person_with_disability",
    ),
    "lib-sd-legal": (
        GUIDE_DOG_PROVISO,
        "guide_dog",
        "exact",
        "exempt_from_prohibition",
        "person_with_disability",
    ),
    "mn-sd-legal": (
        GUIDE_DOG_PROVISO,
        "guide_dog",
        "exact",
        "exempt_from_prohibition",
        "person_with_disability",
    ),
    "qt-sd-legal": (
        GUIDE_DOG_PROVISO,
        "guide_dog",
        "exact",
        "exempt_from_prohibition",
        "person_with_disability",
    ),
    "sb-sd-legal": (
        GUIDE_DOG_PROVISO,
        "guide_dog",
        "exact",
        "exempt_from_prohibition",
        "person_with_disability",
    ),
    "xm-sd-legal": (
        GUIDE_DOG_PROVISO,
        "guide_dog",
        "exact",
        "exempt_from_prohibition",
        "person_with_disability",
    ),
    # 上海迪士尼《游客须知》: names the guide dog only → guide_dog, leash kept.
    "dl-sd-op": (GUIDE_DOG_PROVISO, "guide_dog", "exact", None, None),
    # 前滩太古里《宠物友好》: 「除导盲犬外」→ guide_dog.
    "qt-sd-op": ("除导盲犬外", "guide_dog", "exact", None, None),
    # 上海图书馆《读者须知》: 「导盲犬、军警犬例外」— the source names THREE scopes
    # (guide / police / military working). One register row cannot say that
    # truthfully, so no legal scope is recorded and the row is held for splitting.
    "lib-sd-op": ("导盲犬、军警犬例外", None, "legal_interpretation_required", None, None),
    # OTA-aggregated hotel policy at 0.5 confidence: the wording never states a
    # scope, so nothing may be inferred.
    "fp-sd-op": (None, None, "legal_interpretation_required", None, None),
}

REJECT_REASONS: dict[str, list[str]] = {
    OUTDOOR_KEEP_RULE: ["INSUFFICIENT_PLACE_ZONE_EVIDENCE", "LEGAL_SCOPE_CONFLICT"],
    ATTRIBUTION_ERROR_RULE: ["PLACE_ATTRIBUTION_ERROR", "INSUFFICIENT_PLACE_ZONE_EVIDENCE"],
}

HOLD_REASONS: dict[str, str] = {
    OUTDOOR_KEEP_RULE: "REJECT_CURRENT_CLAIM —— 证据仅为搜索摘要，"
    "无法支撑「港汇恒隆 outdoor 普通宠物有条件允许」；且与同场所室内禁令的 scope 冲突。",
    "lib-sd-op": "PRECISE_SCOPE_SPLIT_REQUIRED —— 原文同时列出导盲犬与军警犬，"
    "必须拆分为 guide_dog / police_dog / military_working_dog 三条精确规则后逐条评审。",
    "fp-sd-op": "EVIDENCE_WEAK_FOR_SCOPE —— 聚合页未陈述 scope，不得推断；须取得运营方原文。",
}

LAYER_ZH = {
    "LEGAL": "法规",
    "REGULATORY_GUIDANCE": "监管指引",
    "OPERATOR_POLICY": "运营方政策",
    "TEMPORARY_POLICY": "临时/事件政策",
}
EFFECT_ZH = {"allowed": "允许", "prohibited": "禁止", "conditional": "有条件允许"}
SCOPE_ZH = {
    "dog": "犬（通用）",
    "ordinary_pet": "普通宠物",
    "service_dog": "服务犬（粗粒度 API scope）",
    "cat": "猫",
    "ordinary_dog": "普通犬",
    "guide_dog": "导盲犬",
    "hearing_dog": "助听犬",
    "assistance_dog": "辅助犬",
    "other_service_dog": "其他服务犬",
    "police_dog": "警犬",
    "military_working_dog": "军用工作犬",
}
NORM_ZH = {
    "exact": "精确（来源即此 scope，具备法律效力）",
    "parent_group_for_query_only": "仅用于查询分组（无法律效力）",
    "legal_interpretation_required": "需法律解释（当前无法律效力）",
}
STRENGTH_ZH = {
    "primary_direct": "官方一手直抓（逐字）",
    "primary_captured": "一手抓取",
    "secondary_reputable": "可靠二手（权威媒体直抓）",
    "search_snippet": "搜索摘要（未核验原文）",
    "social_lead": "社媒线索（仅线索）",
    "user_submitted": "用户提交",
}
MANDATORY_ZH = {
    "mandatory": "强制",
    "advisory": "建议",
    "operator_discretion": "运营方裁量",
}
CONDITION_ZH = {
    "leash_required": "需牵引",
    "carrier_required": "需装载（笼/包）",
    "stroller_required": "需推车",
    "muzzle_required": "需嘴套",
    "no_ground": "不可落地",
    "vaccination_required": "需免疫证明",
    "max_count": "数量上限",
}


def default_scope(row: dict) -> tuple[str | None, str | None, str, str | None, str | None]:
    """Conservative default: only the scopes the source literally named."""
    scope = row["animal_scope"]
    if scope in ("dog", "ordinary_pet"):
        return (scope, scope, "exact", None, None)
    return (scope, None, "legal_interpretation_required", None, None)


def enrich(row: dict) -> dict:
    out = dict(row)
    src_exact, subject, norm, norm_effect, holder = PRECISE_SCOPE.get(
        row["rule_id"], default_scope(row)
    )
    out["source_scope_exact"] = src_exact
    out["subject_scope_normalized"] = subject
    out["normalization_type"] = norm
    out["normative_effect"] = norm_effect
    out["holder_scope"] = holder
    # never inherit an R1 recommendation; clear it and recompute below
    out["r1_proposed_decision"] = row.get("proposed_decision")
    out["proposed_decision"] = None
    out["proposed_reason"] = None
    out["reject_reason_codes"] = None
    out["final_decision"] = None
    out["reviewer"] = None
    out["reviewed_at"] = None
    out["review_note"] = None
    return out


def recommend(row: dict) -> tuple[str, str, list[str] | None]:
    if row["rule_id"] in REJECT_REASONS:
        return "RECOMMEND_REJECT", "REJECT_CURRENT_CLAIM", REJECT_REASONS[row["rule_id"]]
    if row["evidence_strength"] in WEAK:
        return "RECOMMEND_HOLD", "EVIDENCE_NOT_VERIFIED", None
    if row["rule_id"] in HOLD_REASONS:
        return "RECOMMEND_HOLD", "SCOPE_REVIEW_REQUIRED", None
    if row["normalization_type"] != "exact":
        return "RECOMMEND_HOLD", "SCOPE_NOT_ESTABLISHED_AS_LEGAL", None
    if row["animal_scope"] == "service_dog":
        # the widening is gone; the reviewer confirms the precise source scope
        return "RECOMMEND_APPROVE", "SOURCE_SCOPE_EXACT", None
    return "RECOMMEND_APPROVE", "EVIDENCE_TRACEABLE", None


def build_rows() -> list[dict]:
    raw = json.loads(REGISTRY_R1.read_text(encoding="utf-8"))
    rows = []
    for r in raw["rows"]:
        e = enrich(r)
        dec, reason, codes = recommend(e)
        e["proposed_decision"] = dec
        e["proposed_reason"] = reason
        e["reject_reason_codes"] = codes
        rows.append(e)
    order = {"RECOMMEND_REJECT": 0, "RECOMMEND_HOLD": 1, "RECOMMEND_APPROVE": 2}
    rows.sort(key=lambda r: (order.get(r["proposed_decision"], 3), r["place_name"], r["rule_id"]))
    return rows


def write_registry(rows: list[dict]) -> None:
    raw = json.loads(REGISTRY_R1.read_text(encoding="utf-8"))
    doc = {
        "_readme": [
            "R2 review register (ADR-025 source-faithful animal scope).",
            "SUPERSEDES review_decisions_r1.json: R1 stored every 导盲犬 proviso as",
            "animal_scope='service_dog', an ontology inference used as a legal argument.",
            "Recommendations were RECOMPUTED, never inherited from R1.",
            "proposed_decision is a MACHINE PROPOSAL, not a ruling: a named human",
            "reviewer must set final_decision + reviewer + reviewed_at before publish.",
            "Allowed final_decision values: APPROVED | REJECTED | HOLD.",
        ],
        "revision": "R2",
        "supersedes": "docs/reality_audit/review_decisions_r1.json",
        "generated_from": raw.get("generated_from", []),
        "human_signoff_required": True,
        "rows": rows,
    }
    REGISTRY_R2.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def render_packet(rows: list[dict]) -> str:
    by = defaultdict(list)
    for r in rows:
        by[r["proposed_decision"]].append(r)
    L: list[str] = []
    a = L.append
    a("# HUMAN_REVIEW_PACKET_R2.md")
    a("")
    a("> GOV-01 支撑材料 · **R2**（ADR-025 源忠实 scope）")
    a("> 取代：`HUMAN_REVIEW_PACKET_R1.md`（R1 的 AI 建议建立在已被撤回的")
    a("> `service_dog` 泛化之上，**未被继承**，全部重新计算）")
    a(f"> 机器登记表：`docs/reality_audit/review_decisions_r2.json`（共 {len(rows)} 条）")
    a("")
    a("## 0. 纪律（不可协商）")
    a("")
    a("1. **AI 不做最终裁决**（ADR-005 / Master Goal §0.9）。本包只提供事实与建议。")
    a("2. 所有 `final_decision` / `reviewer` / `reviewed_at` **保持空白**，由具名人类评审员填写。")
    a("3. 未获签署，任何候选不得 APPROVED，更不得 Publish。")
    a("4. 弱证据（`search_snippet` / `social_lead`）不得 APPROVED（ADR-021）。")
    a("5. **ADR-025**：来源写「导盲犬」就只能是 `guide_dog`；写成 `service_dog` 属")
    a("   本体推断，不具法律效力，已在本轮全部修正。")
    a("6. 本包**不执行发布**。")
    a("")
    a("## 1. 摘要")
    a("")
    a("| 建议 | 条数 |")
    a("|---|---|")
    for dec in ("RECOMMEND_REJECT", "RECOMMEND_HOLD", "RECOMMEND_APPROVE"):
        a(f"| `{dec}` | **{len(by[dec])}** |")
    a(f"| **合计** | **{len(rows)}** |")
    a("")
    a("## 2. 逐条")
    a("")
    for i, r in enumerate(rows, 1):
        a(f"### R2-{i:02d} · `{r['rule_id']}` — {r['place_name']}")
        a("")
        a(f"- **candidate_id**：`{r['candidate_id']}`")
        a(f"- **place**：{r['place_name']}（`{r['place_key']}`）· zone：`{r['zone_key'] or '—'}`")
        a(f"- **action / effect**：{r['action']} · **{EFFECT_ZH.get(r['effect'], r['effect'])}**")
        a(
            f"- **coarse animal_scope**：`{r['animal_scope']}`"
            f"（{SCOPE_ZH.get(r['animal_scope'], r['animal_scope'])}）"
        )
        a(f"- **source_scope_exact（来源原话）**：{r['source_scope_exact'] or '（来源未陈述）'}")
        a(f"- **subject_scope_normalized（精确 scope）**：{r['subject_scope_normalized'] or '—'}")
        a(
            f"- **normalization_type**：`{r['normalization_type']}`"
            f"（{NORM_ZH.get(r['normalization_type'], r['normalization_type'])}）"
        )
        a(f"- **normative_effect**：`{r['normative_effect'] or '—'}`")
        a(f"- **holder_scope**：`{r['holder_scope'] or '—'}`")
        layer_zh = LAYER_ZH.get(r["rule_layer"], r["rule_layer"])
        a(f"- **RuleLayer**：`{r['rule_layer']}`（{layer_zh}）")
        ml = r.get("mandatory_level")
        a(f"- **MandatoryLevel**：`{ml}`（{MANDATORY_ZH.get(ml, ml or '—')}）")
        a(
            f"- **EvidenceStrength**：`{r['evidence_strength']}`"
            f"（{STRENGTH_ZH.get(r['evidence_strength'], r['evidence_strength'])}）"
        )
        a(f"- **Source URL**：{r['source_url']}")
        a(f"- **conditions**：{_conditions(r)}")
        a(f"- **R1 建议（仅供参考，已被取代）**：`{r['r1_proposed_decision']}`")
        a(f"- **AI recommendation（R2，重新计算）**：**{r['proposed_decision']}**")
        a(f"- **recommendation reason**：{r['proposed_reason']}")
        if r["reject_reason_codes"]:
            a(f"- **reject reason codes**：`{'`, `'.join(r['reject_reason_codes'])}`")
        a("- **final_decision**：`________`  ← 留空，由具名评审员填写")
        a("")
    a("---")
    a("")
    a("## 3. 签署")
    a("")
    a("1. 在 `HUMAN_REVIEW_DECISIONS_R2.json` 填 `reviewer` / `reviewed_at` 与逐条")
    a("   `final_decision`（`APPROVED` / `APPROVED_WITH_NOTE` / `HOLD` / `REJECTED`）。")
    a("2. 回填机器登记表 `docs/reality_audit/review_decisions_r2.json`。")
    a("3. 校验：`python scripts/publish_reviewed_r1.py --dry-run`（自动读取 R2 登记表）")
    a("   应返回 `signed=true` 且「登记表 ↔ 库」一致性校验通过。")
    a("")
    return "\n".join(L) + "\n"


def render_quick_table(rows: list[dict]) -> str:
    L: list[str] = []
    a = L.append
    a("# HUMAN_REVIEW_QUICK_TABLE_R2.md")
    a("")
    a("> GOV-01 速填表 · 一行一条。取代 R1 速填表。")
    a("> 「我的决定」列填：`APPROVE` / `APPROVE_WITH_NOTE` / `HOLD` / `REJECT`")
    a("")
    a("**图例**：🔴 建议拒绝 ｜ 🟠 建议挂起 ｜ ⚖️ 法定强制 ｜ 🦮 导盲犬精确 scope")
    a("")
    a("| 编号 | Place | Rule | 来源原话 | 精确 scope | 归一化 | Evidence | AI建议 | 我的决定 |")
    a("|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        flags = ""
        if r["proposed_decision"] == "RECOMMEND_REJECT":
            flags = "🔴"
        elif r["proposed_decision"] == "RECOMMEND_HOLD":
            flags = "🟠"
        if r["rule_layer"] == "LEGAL" and r.get("mandatory_level") == "mandatory":
            flags += "⚖️"
        if r["subject_scope_normalized"] == "guide_dog":
            flags += "🦮"
        a(
            f"| **R2-{i:02d}** {flags} | {r['place_name']} | `{r['rule_id']}`"
            f"：{EFFECT_ZH.get(r['effect'], r['effect'])} | {r['source_scope_exact'] or '—'}"
            f" | {r['subject_scope_normalized'] or '—'} | `{r['normalization_type']}`"
            f" | {r['evidence_strength']} | {r['proposed_decision']} |  |"
        )
    a("")
    a("## 签署")
    a("")
    a("| 字段 | 值 |")
    a("|---|---|")
    a("| reviewer（具名） |  |")
    a("| reviewer_role |  |")
    a("| reviewed_at |  |")
    a("| 是否确认 ADR-025 源忠实 scope（不再泛化为 service_dog） | ☐ 是 ☐ 否 |")
    a("| 首批批准条数（≤ `--max-approve`） |  |")
    a("| 签名 |  |")
    a("")
    return "\n".join(L) + "\n"


def render_decisions(rows: list[dict]) -> str:
    doc = {
        "revision": "R2",
        "reviewer": "",
        "reviewed_at": "",
        "decisions": [
            {"candidate_id": r["candidate_id"], "final_decision": "", "review_note": ""}
            for r in rows
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def _conditions(row: dict) -> str:
    conds = row.get("conditions") or []
    if not conds:
        return "无"
    parts = []
    for c in conds:
        if isinstance(c, dict):
            key = c.get("condition_type", "?")
            label = CONDITION_ZH.get(key, key)
            if c.get("value_numeric") is not None:
                label += f"（{c['value_numeric']}）"
            parts.append(label)
        else:
            parts.append(str(c))
    return "、".join(parts)


def main() -> int:
    rows = build_rows()
    write_registry(rows)
    PACKET.write_text(render_packet(rows), encoding="utf-8", newline="\n")
    QUICK_TABLE.write_text(render_quick_table(rows), encoding="utf-8", newline="\n")
    DECISION_TEMPLATE.write_text(render_decisions(rows), encoding="utf-8", newline="\n")

    by = defaultdict(int)
    for r in rows:
        by[r["proposed_decision"]] += 1
    print(
        json.dumps(
            {
                "written": [
                    str(REGISTRY_R2),
                    str(PACKET),
                    str(QUICK_TABLE),
                    str(DECISION_TEMPLATE),
                ],
                "total": len(rows),
                "by_recommendation": dict(by),
                "exact_scope": sum(1 for r in rows if r["normalization_type"] == "exact"),
                "not_legal_equivalent": sum(1 for r in rows if r["normalization_type"] != "exact"),
                "all_decisions_blank": all(not r.get("final_decision") for r in rows),
                "all_reviewers_blank": all(not r.get("reviewer") for r in rows),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
