"""Generate the signable human Review Sheet for the 33 R1 RuleCandidates.

Reads ``docs/reality_audit/review_decisions_r1.json`` (the machine register) and
emits ``RULE_REVIEW_SHEET_R1.md`` — one block per candidate carrying exactly the
fields a reviewer must confirm, plus a signable table.

Hard rules encoded here (they are review *discipline*, not rulings):

  * the AI never fills ``final_decision`` / ``reviewer`` / ``reviewed_at`` —
    those stay blank for the named human reviewer (ADR-005 / Master Goal §0.9);
  * the Manner 凯德虹口 candidate (rule ``mn-outdoor-media``) is a proven place
    attribution error → AI recommendation is REJECT, never forced through;
  * a candidate whose evidence is still only a ``search_snippet`` and is not the
    attribution error stays HOLD (pending) — it is never forced to APPROVE;
  * a LEGAL candidate carries its deterministic ``mandatory_level`` (ADR-023).

Usage: python scripts/gen_review_sheet_r1.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "docs" / "reality_audit"
DECISIONS = AUDIT / "review_decisions_r1.json"
OUT = REPO / "RULE_REVIEW_SHEET_R1.md"

WEAK = {"search_snippet", "social_lead"}

#: proven place-attribution error (CBNData article does not cover this venue)
ATTRIBUTION_ERROR_RULE = "mn-outdoor-media"

LAYER_ZH = {
    "LEGAL": "法规",
    "REGULATORY_GUIDANCE": "监管指引",
    "OPERATOR_POLICY": "运营方政策",
    "TEMPORARY_POLICY": "临时/事件政策",
}
EFFECT_ZH = {"allowed": "允许", "prohibited": "禁止", "conditional": "有条件允许"}
STRENGTH_ZH = {
    "primary_direct": "官方/一手直抓（逐字）",
    "secondary_reputable": "可靠二手（权威媒体直抓）",
    "search_snippet": "搜索摘要（未核验原文）",
    "social_lead": "社媒线索（仅线索）",
}


def load_rows() -> list[dict]:
    return json.loads(DECISIONS.read_text(encoding="utf-8"))["rows"]


def conflicts_by_candidate(rows: list[dict]) -> dict[str, list[str]]:
    """Same place + same animal_scope + same action + a DIFFERENT effect.

    Different-source opposite effects on the same owner/scope/action are exactly
    what the resolver reports as an unresolved conflict (it never auto-picks).
    """
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["place_key"], r["animal_scope"], r["action"])].append(r)
    out: dict[str, list[str]] = defaultdict(list)
    for members in groups.values():
        if len({m["effect"] for m in members}) < 2:
            continue
        for m in members:
            for other in members:
                if other is m or other["effect"] == m["effect"]:
                    continue
                out[m["candidate_id"]].append(
                    f"`{other['rule_id']}`（{other['rule_layer']} · {other['effect']}"
                    f" · {other['evidence_strength']}）"
                )
    return out


def recommended(row: dict) -> tuple[str, str]:
    """AI recommendation + reason. Never a ruling; never forced through."""
    if row["rule_id"] == ATTRIBUTION_ERROR_RULE:
        return "REJECT", "PLACE_ATTRIBUTION_ERROR —— 来源原文不支持该场所（错归因实锤）"
    if row["evidence_strength"] in WEAK:
        return (
            "HOLD（pending）",
            "EVIDENCE_NOT_VERIFIED —— 证据仍仅为搜索摘要，未核验原文；不强行通过",
        )
    return {
        "RECOMMEND_APPROVE": ("APPROVE", "EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许"),
        "RECOMMEND_APPROVE_WITH_NOTE": (
            "APPROVE_WITH_NOTE",
            "STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，"
            "建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认",
        ),
        "RECOMMEND_HOLD": ("HOLD（pending）", "结论为推断/法律解释或证据未证实，须补证或裁定"),
    }.get(row["proposed_decision"], ("HOLD（pending）", row["proposed_reason"]))


def render_rule(row: dict) -> str:
    conds = "、".join(c.get("condition_type", str(c)) for c in (row.get("conditions") or []))
    base = (
        f"{row['animal_scope']} · {row['action']} · {EFFECT_ZH.get(row['effect'], row['effect'])}"
    )
    return f"{base}（{conds}）" if conds else base


def main() -> int:
    rows = load_rows()
    conflicts = conflicts_by_candidate(rows)

    counts: dict[str, int] = defaultdict(int)
    for r in rows:
        counts[recommended(r)[0]] += 1

    lines: list[str] = []
    a = lines.append
    a("# RULE_REVIEW_SHEET_R1.md")
    a("")
    a("> P0-PUBLISH-CLOSURE · 33 条真实 RuleCandidate 的可签署人工审核工作表。")
    a("> 生成来源：`docs/reality_audit/review_decisions_r1.json`（机器登记表）。")
    a(f"> 候选总数：**{len(rows)}**。")
    a("")
    a("## 纪律（不可协商）")
    a("")
    a("1. **AI 不做最终裁决**（ADR-005 / Master Goal §0.9）。`AI 建议` 与 `理由` 仅为建议；")
    a("   `final_decision` / `reviewer` / `reviewed_at` 三列由**具名人类评审员**填写。")
    a("2. 未获签署，任何候选不得进入 APPROVED，更不得 Publish（`publish_reviewed_r1.py` 硬门禁）。")
    a(
        "3. 弱证据（`search_snippet` / `social_lead`）不得 APPROVED"
        "（ADR-021 + Pre-Publish Validation）。"
    )
    a("4. 3 条 ObservationCandidate 保持 lead-only，永不进入规则发布（不在本表内）。")
    a(
        "5. LEGAL 候选的 `mandatory_level` 由 layer 确定性映射（ADR-023），"
        "评审员可逐行覆盖；留空将导致发布被拒。"
    )
    a("")
    a("## 建议汇总")
    a("")
    a("| AI 建议 | 数量 |")
    a("|---|---|")
    for k in ("APPROVE", "APPROVE_WITH_NOTE", "HOLD（pending）", "REJECT"):
        a(f"| {k} | {counts.get(k, 0)} |")
    a(f"| **合计** | **{len(rows)}** |")
    a("")
    a("> `HOLD（pending）` 含两类：结论为推断/法律解释，或证据仍仅为搜索摘要。**均不强行通过。**")
    a("")
    a("---")
    a("")
    a("## 逐条审核表")
    a("")

    for i, r in enumerate(rows, 1):
        rec, reason = recommended(r)
        conf = conflicts.get(r["candidate_id"]) or []
        a(f"### {i}. `{r['rule_id']}` — {r['place_name']}")
        a("")
        a(f"- **candidate**：`{r['candidate_id']}`")
        a(f"- **place**：{r['place_name']}（`{r['place_key']}`）· zone：`{r['zone_key']}`")
        a(
            f"- **proposed rule**：{render_rule(r)} · layer：`{r['rule_layer']}`"
            f"（{LAYER_ZH.get(r['rule_layer'], r['rule_layer'])}）"
            f" · mandatory_level：`{r.get('mandatory_level')}`"
        )
        a(f"- **evidence**：{STRENGTH_ZH.get(r['evidence_strength'], r['evidence_strength'])}")
        a(f"- **source**：{r['issuer']}")
        a(f"  - URL：{r['source_url']}")
        a(
            f"  - license：display={r['license']['display_allowed']} · "
            f"redistribution={r['license']['redistribution_allowed']} · "
            f"storage={r['license']['storage_allowed']}"
        )
        a(f"- **evidence strength**：`{r['evidence_strength']}`")
        conflict_text = "；".join(conf) if conf else "无（同归属同 scope/action 无相反效果）"
        a(f"- **conflicts**：{conflict_text}")
        a(f"- **AI recommendation**：**{rec}**")
        a(f"- **reason**：{reason}")
        a("- **final_decision**：`________`（APPROVED / REJECTED / HOLD）")
        a("- **reviewer**：`________`")
        a("- **reviewed_at**：`________`")
        a("")

    a("---")
    a("")
    a("## 签署表（汇总）")
    a("")
    a(
        "| # | candidate | place | rule_id | proposed rule | AI 建议 "
        "| final_decision | reviewer | reviewed_at |"
    )
    a("|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        rec, _ = recommended(r)
        a(
            f"| {i} | `{r['candidate_id'][:8]}` | {r['place_name']} | `{r['rule_id']}` | "
            f"{render_rule(r)} | {rec} | | | |"
        )
    a("")
    a("## 评审员声明（必填）")
    a("")
    a("| 字段 | 值 |")
    a("|---|---|")
    a("| reviewer（具名） |  |")
    a("| reviewer_role |  |")
    a("| reviewed_at |  |")
    a("| 是否接受 APPROVE_WITH_NOTE 的 service_dog scope 泛化（ADR-020） | ☐ 是 ☐ 否 |")
    a("| 首批批准条数（≤ `--max-approve`） |  |")
    a("| 签名 |  |")
    a("")
    a("> 签署后，将各行 `final_decision` / `reviewer` / `reviewed_at` 回填到")
    a("> `docs/reality_audit/review_decisions_r1.json`，再执行")
    a('> `python scripts/publish_reviewed_r1.py --execute --reviewer "<具名>"`。')
    a("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "written": str(OUT),
                "total": len(rows),
                "recommended": dict(counts),
                "candidates_with_conflicts": len(conflicts),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
