"""Generate the human review packet for the 33 R1 RuleCandidates (GOV-01 support).

This script does **not** decide anything. It exists so that a named human
reviewer can finish the 33 sign-offs quickly, with every fact they need on one
screen per candidate. It produces three artefacts:

  * ``HUMAN_REVIEW_PACKET_R1.md``      — risk-ordered, one block per candidate
  * ``HUMAN_REVIEW_DECISIONS_R1.json`` — the blank decision template to fill in
  * ``HUMAN_REVIEW_QUICK_TABLE_R1.md`` — the one-line-per-candidate checklist

Hard rules (review *discipline*, not rulings):

  * ``final_decision`` / ``reviewer`` / ``reviewed_at`` are emitted **empty**.
    The AI never signs (ADR-005 / Master Goal §0.9).
  * Candidates are ordered by **risk**, not by id: REJECT → HOLD →
    CONFLICT/APPROVE_WITH_NOTE → LOW-RISK APPROVE.
  * The Manner 凯德虹口 attribution error is surfaced first as a REJECT
    recommendation; the two search-snippet-only candidates as HOLD.
  * LEGAL candidates carry their deterministic ``mandatory_level`` (ADR-023) and
    service-dog candidates carry the ADR-020 generalisation warning.

Requires a live PostgreSQL (ENV-01) for the evidence-bundle fields
(``quoted_fragment`` / ``place_match_evidence`` / ``content_hash`` /
``license_metadata``).

Usage: python scripts/gen_human_review_packet_r1.py
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

import psycopg

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "docs" / "reality_audit"
DECISIONS = AUDIT / "review_decisions_r1.json"
EVIDENCE = AUDIT / "real_pilot_evidence.json"

PACKET = REPO / "HUMAN_REVIEW_PACKET_R1.md"
DECISION_TEMPLATE = REPO / "HUMAN_REVIEW_DECISIONS_R1.json"
QUICK_TABLE = REPO / "HUMAN_REVIEW_QUICK_TABLE_R1.md"

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://petaccess:petaccess_dev_only@localhost:5432/petaccess",
).replace("postgresql+psycopg://", "postgresql://")

WEAK = {"search_snippet", "social_lead"}
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
    "primary_captured": "一手抓取",
    "secondary_reputable": "可靠二手（权威媒体直抓）",
    "search_snippet": "搜索摘要（未核验原文）",
    "social_lead": "社媒线索（仅线索）",
    "user_submitted": "用户提交",
}
SCOPE_ZH = {"dog": "犬（通用）", "ordinary_pet": "普通宠物", "service_dog": "服务犬", "cat": "猫"}
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
    "indoor_prohibited": "室内禁止",
    "designated_area_only": "仅限指定区域",
}


def load_rows() -> list[dict]:
    return json.loads(DECISIONS.read_text(encoding="utf-8"))["rows"]


def conflicts_by_candidate(rows: list[dict]) -> dict[str, list[str]]:
    """Same place + scope + action with a DIFFERENT effect ⇒ unresolved conflict."""
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
    if row["rule_id"] == ATTRIBUTION_ERROR_RULE:
        return "REJECT", "PLACE_ATTRIBUTION_ERROR —— 来源原文不支持该场所（错归因实锤）"
    if row["evidence_strength"] in WEAK:
        return "HOLD", "EVIDENCE_NOT_VERIFIED —— 证据仍仅为搜索摘要，未核验原文；不强行通过"
    return {
        "RECOMMEND_APPROVE": ("APPROVE", "EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许"),
        "RECOMMEND_APPROVE_WITH_NOTE": (
            "APPROVE_WITH_NOTE",
            "STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，"
            "建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认",
        ),
        "RECOMMEND_HOLD": ("HOLD", "结论为推断/法律解释或证据未证实，须补证或裁定"),
    }.get(row["proposed_decision"], ("HOLD", row["proposed_reason"]))


def risk_group(row: dict, rec: str, has_conflict: bool) -> int:
    if rec == "REJECT":
        return 1
    if rec == "HOLD":
        return 2
    if rec == "APPROVE_WITH_NOTE" or has_conflict:
        return 3
    return 4


def load_evidence_fields(candidate_ids: list[str]) -> dict[str, dict]:
    """quoted_fragment / place_match_evidence / content_hash / license per candidate."""
    with psycopg.connect(DB_URL, connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT rc.id, eb.quoted_fragment, eb.place_match_evidence, eb.content_hash,
                   eb.license_metadata, eb.extracted_fragment
              FROM rule_candidate rc
              LEFT JOIN evidence_bundle eb ON eb.id = rc.evidence_bundle_id
             WHERE rc.id = ANY(%s)
            """,
            (candidate_ids,),
        )
        out: dict[str, dict] = {}
        for cid, quote, place_match, content_hash, lic, extracted in cur.fetchall():
            out[cid] = {
                "quoted_fragment": quote,
                "place_match_evidence": place_match,
                "content_hash": content_hash,
                "license_metadata": lic,
                "extracted_fragment": extracted,
            }
        return out


def load_active_exceptions(rows: list[dict]) -> dict[str, list[str]]:
    """Active (status=current) RuleException carve-outs touching the same place+scope.

    Keyed by place_key so a candidate can be told whether a carve-out already
    governs its scope — relevant to every service-dog candidate (ADR-020).
    """
    place_keys = {r["place_key"]: r["place_name"] for r in rows}
    with psycopg.connect(DB_URL, connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT p.canonical_name, re.animal_scope, re.effect, re.status
              FROM rule_exception re
              JOIN access_rule ar ON ar.id = re.rule_id
              JOIN place p ON p.id = ar.place_id
             WHERE re.status = 'current'
            """
        )
        found: dict[str, list[str]] = defaultdict(list)
        for place_name, scope, effect, status in cur.fetchall():
            for key, name in place_keys.items():
                if name == place_name:
                    found[key].append(f"`{scope}` → {effect}（{status}）")
        return found


def completeness(ev: dict) -> tuple[str, list[str]]:
    checks = {
        "原文引文": bool(ev.get("quoted_fragment")),
        "content_hash": bool(ev.get("content_hash")),
        "许可元数据": bool(ev.get("license_metadata")),
        "归属匹配证据": bool(ev.get("place_match_evidence")),
    }
    missing = [k for k, ok in checks.items() if not ok]
    return f"{sum(checks.values())}/{len(checks)}", missing


def render_conditions(row: dict) -> str:
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
            elif c.get("value_text"):
                label += f"（{c['value_text']}）"
            parts.append(label)
        else:
            parts.append(str(c))
    return "、".join(parts)


def render_place_match(pm) -> str:
    if not pm:
        return "（缺失）"
    if isinstance(pm, str):
        return pm
    bits = [f"{k}={v}" for k, v in pm.items() if v not in (None, "")]
    return " · ".join(bits) or "（缺失）"


def render_license(lic) -> str:
    if not lic:
        return "（未记录）"
    marks = []
    for key, label in (
        ("display_allowed", "展示"),
        ("storage_allowed", "存储"),
        ("redistribution_allowed", "再分发"),
    ):
        if key in lic:
            marks.append(f"{label} {'✓' if lic[key] else '✗'}")
    return " · ".join(marks) or json.dumps(lic, ensure_ascii=False)


def truncate(text: str | None, limit: int = 260) -> str:
    if not text:
        return "（缺失）"
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "…"


def build_context(rows: list[dict]) -> dict:
    evidence = load_evidence_fields([r["candidate_id"] for r in rows])
    conflicts = conflicts_by_candidate(rows)
    exceptions = load_active_exceptions(rows)

    enriched = []
    for r in rows:
        rec, reason = recommended(r)
        conf = conflicts.get(r["candidate_id"]) or []
        ev = evidence.get(r["candidate_id"], {})
        comp, missing = completeness(ev)
        enriched.append(
            {
                "row": r,
                "rec": rec,
                "reason": reason,
                "conflicts": conf,
                "exceptions": exceptions.get(r["place_key"]) or [],
                "ev": ev,
                "completeness": comp,
                "missing": missing,
                "group": risk_group(r, rec, bool(conf)),
            }
        )
    enriched.sort(key=lambda e: (e["group"], e["row"]["place_name"], e["row"]["rule_id"]))
    return {"items": enriched}


def render_packet(ctx: dict) -> str:
    items = ctx["items"]
    groups: dict[int, list[dict]] = defaultdict(list)
    for e in items:
        groups[e["group"]].append(e)

    n_mandatory = sum(1 for e in items if e["row"].get("mandatory_level") == "mandatory")

    L: list[str] = []
    a = L.append
    a("# HUMAN_REVIEW_PACKET_R1.md")
    a("")
    a("> GOV-01 支撑材料 · 33 条真实 RuleCandidate 的**人工签署包**（按风险排序）")
    a("> 数据来源：`docs/reality_audit/review_decisions_r1.json`（机器登记表）+ 数据库证据包")
    a(
        "> 配套：`HUMAN_REVIEW_DECISIONS_R1.json`（待填模板）、"
        "`HUMAN_REVIEW_QUICK_TABLE_R1.md`（速填表）"
    )
    a("")
    a("## 0. 纪律（不可协商）")
    a("")
    a("1. **AI 不做最终裁决**（ADR-005 / Master Goal §0.9）。本包只提供事实与建议。")
    a("2. 所有 `final_decision` / `reviewer` / `reviewed_at` **保持空白**，由具名人类评审员填写。")
    a("3. 未获签署，任何候选不得 APPROVED，更不得 Publish（`publish_reviewed_r1.py` 硬门禁）。")
    a(
        "4. 弱证据（`search_snippet` / `social_lead`）**不得 APPROVED**"
        "（ADR-021 + Pre-Publish Validation）。"
    )
    a(
        "5. LEGAL 候选的 `mandatory_level` 由 layer 确定性映射（ADR-023），"
        "可逐行覆盖；留空将被拒绝发布。"
    )
    a("6. 本包**不执行发布**。")
    a("")
    a("## 1. 摘要")
    a("")
    a("| 风险分组 | 含义 | 条数 |")
    a("|---|---|---|")
    a(f"| **Group 1** | REJECT 推荐（错归因实锤） | **{len(groups.get(1, []))}** |")
    a(f"| **Group 2** | HOLD 推荐（证据未核验 / 需裁定） | **{len(groups.get(2, []))}** |")
    a(
        f"| **Group 3** | CONFLICT / APPROVE_WITH_NOTE（须额外确认） | "
        f"**{len(groups.get(3, []))}** |"
    )
    a(f"| **Group 4** | LOW-RISK APPROVE（无冲突、证据可追溯） | **{len(groups.get(4, []))}** |")
    a(f"| **合计** | | **{len(items)}** |")
    a("")
    a("## 2. 特别标记索引")
    a("")
    a("| 标记 | 条数 | 候选（`rule_id`） |")
    a("|---|---|---|")
    manner = [e for e in items if e["row"]["rule_id"] == ATTRIBUTION_ERROR_RULE]
    weak = [e for e in items if e["row"]["evidence_strength"] in WEAK]
    conf = [e for e in items if e["conflicts"]]
    legal = [e for e in items if e["row"]["rule_layer"] == "LEGAL"]
    sd = [e for e in items if e["row"]["animal_scope"] == "service_dog"]
    a(
        f"| 🔴 **Manner 错归因 → REJECT 推荐** | {len(manner)} | "
        + "、".join(f"`{e['row']['rule_id']}`" for e in manner)
        + " |"
    )
    weak_hold = [e for e in weak if e["row"]["rule_id"] != ATTRIBUTION_ERROR_RULE]
    weak_reject = [e for e in weak if e["row"]["rule_id"] == ATTRIBUTION_ERROR_RULE]
    a(
        f"| 🟠 **弱 search-snippet** | {len(weak)} | "
        + "、".join(f"`{e['row']['rule_id']}`" for e in weak)
        + " |"
    )
    a(
        f"| 🟠→🟢 其中按弱证据 → **HOLD 推荐** | {len(weak_hold)} | "
        + ("、".join(f"`{e['row']['rule_id']}`" for e in weak_hold) or "—")
        + " |"
    )
    a(
        f"| 🟠→🔴 其中同时是错归因 → **REJECT 优先** | {len(weak_reject)} | "
        + ("、".join(f"`{e['row']['rule_id']}`" for e in weak_reject) or "—")
        + " |"
    )
    a(
        f"| ⚠️ **存在 conflict** | {len(conf)} | "
        + "、".join(f"`{e['row']['rule_id']}`" for e in conf)
        + " |"
    )
    a(
        f"| ⚖️ **LEGAL + Mandatory（法定强制，构成 resolver 下限）** | {len(legal)}"
        f"（其中 mandatory {n_mandatory}） | "
        + "、".join(f"`{e['row']['rule_id']}`" for e in legal)
        + " |"
    )
    a(
        f"| 🦮 **service-dog / RuleException 相关** | {len(sd)} | "
        + "、".join(f"`{e['row']['rule_id']}`" for e in sd)
        + " |"
    )
    a("")
    a("> **优先级说明**：错归因（事实性缺陷）**优先于**弱证据。`mn-outdoor-media` 同时命中两项，")
    a(
        "> 因此归入 Group 1（REJECT）而非 Group 2 —— 这就是「2 条弱证据」但 Group 2 中"
        "只有 1 条源自弱证据的原因。"
    )
    a(
        f"> Group 2 共 {len(groups.get(2, []))} 条 = 弱证据 HOLD {len(weak_hold)} 条"
        f" + 结论为推断/法律解释 HOLD "
        f"{len(groups.get(2, [])) - len(weak_hold)} 条。"
    )
    a("> **service-dog 说明**：法条原文为「盲人携带导盲犬」，平台按 ADR-020 泛化为 `service_dog`。")
    a("> 该泛化是平台级决策，须评审员逐条确认（Group 3 的 APPROVE_WITH_NOTE 即为此类）。")
    a(
        "> 当前数据库内**无** `status=current` 的 RuleException 覆盖本批任何场所"
        "（现有 6 条例外均为测试产物、状态 `withdrawn`）。"
    )
    a("")
    a("---")
    a("")

    titles = {
        1: "Group 1 — REJECT（建议拒绝）",
        2: "Group 2 — HOLD（建议挂起）",
        3: "Group 3 — CONFLICT / APPROVE_WITH_NOTE（须额外确认）",
        4: "Group 4 — LOW-RISK APPROVE（低风险建议批准）",
    }
    for g in (1, 2, 3, 4):
        members = groups.get(g, [])
        if not members:
            continue
        a(f"## {titles[g]}")
        a("")
        for i, e in enumerate(members, 1):
            r, ev = e["row"], e["ev"]
            a(f"### G{g}-{i:02d} · `{r['rule_id']}` — {r['place_name']}")
            a("")
            a(f"- **candidate_id**：`{r['candidate_id']}`")
            a(
                f"- **place**：{r['place_name']}（`{r['place_key']}`）"
                f" · zone：`{r['zone_key'] or '—'}`"
            )
            a(
                "- **proposed subject/action/effect**："
                f"{SCOPE_ZH.get(r['animal_scope'], r['animal_scope'])}"
                f" · {r['action']} · **{EFFECT_ZH.get(r['effect'], r['effect'])}**"
            )
            a(f"- **conditions**：{render_conditions(r)}")
            a(
                f"- **RuleLayer**：`{r['rule_layer']}`"
                f"（{LAYER_ZH.get(r['rule_layer'], r['rule_layer'])}）"
            )
            ml = r.get("mandatory_level")
            a(f"- **MandatoryLevel**：`{ml}`（{MANDATORY_ZH.get(ml, ml or '—')}）")
            a(
                f"- **EvidenceStrength**：`{r['evidence_strength']}`"
                f"（{STRENGTH_ZH.get(r['evidence_strength'], r['evidence_strength'])}）"
            )
            a(f"- **Source issuer**：{r['issuer']}")
            a(f"- **Source URL**：{r['source_url']}")
            a(f"- **关键原文引文**：> {truncate(ev.get('quoted_fragment'))}")
            a(f"- **place match evidence**：{render_place_match(ev.get('place_match_evidence'))}")
            miss = f"（缺：{'、'.join(e['missing'])}）" if e["missing"] else ""
            a(f"- **evidence completeness**：{e['completeness']}{miss}")
            lic = render_license(ev.get("license_metadata") or r.get("license"))
            a(f"- **DataLicense status**：{lic}")
            a(
                "- **conflict / exception**：conflict "
                + ("；".join(e["conflicts"]) if e["conflicts"] else "无")
                + " ｜ exception "
                + (
                    "；".join(e["exceptions"])
                    if e["exceptions"]
                    else "无（本场所无 active RuleException）"
                )
            )
            a(f"- **AI recommendation**：**{e['rec']}**")
            a(f"- **recommendation reason**：{e['reason']}")
            a("- **final_decision**：`________`  ← 留空，由具名评审员填写")
            a("")

    a("---")
    a("")
    a("## 3. 填写与提交方式")
    a("")
    a("1. 在 `HUMAN_REVIEW_DECISIONS_R1.json` 中填写：")
    a("   - 顶层 `reviewer`（具名）与 `reviewed_at`（ISO 8601）；")
    a("   - 每条 `decisions[]` 的 `final_decision` 与 `review_note`。")
    a(
        "   - `final_decision` 取值：`APPROVED` / `APPROVED_WITH_NOTE` / `HOLD` / `REJECTED`"
        "（须与发布脚本的 `EXECUTABLE` 口径一致）。"
    )
    a("2. 或直接在 `HUMAN_REVIEW_QUICK_TABLE_R1.md` 的「我的决定」列勾填。")
    a("3. 随后把结果回填到机器登记表 `docs/reality_audit/review_decisions_r1.json` 的")
    a("   `final_decision` / `reviewer` / `reviewed_at` 三列（发布脚本读的是该文件）。")
    a("4. 校验：`python scripts/publish_reviewed_r1.py --dry-run` 应返回 `signed=true`，")
    a("   且「登记表 ↔ 库」一致性校验通过（ADR-024）。")
    a("5. 首批建议条数 ≤ `--max-approve`（默认 20），禁止盲批。")
    a("")
    a("> **本包不执行任何发布。** `--execute` 必须由人类评审员在签署后手动触发。")
    a("")
    return "\n".join(L) + "\n"


def render_decision_template(ctx: dict) -> str:
    doc = {
        "reviewer": "",
        "reviewed_at": "",
        "decisions": [
            {
                "candidate_id": e["row"]["candidate_id"],
                "final_decision": "",
                "review_note": "",
            }
            for e in ctx["items"]
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def render_quick_table(ctx: dict) -> str:
    L: list[str] = []
    a = L.append
    a("# HUMAN_REVIEW_QUICK_TABLE_R1.md")
    a("")
    a("> GOV-01 速填表 · 一行一条，**按风险排序**。")
    a("> 「我的决定」列填：`APPROVE` / `APPROVE_WITH_NOTE` / `HOLD` / `REJECT`")
    a("> 详细依据见 `HUMAN_REVIEW_PACKET_R1.md` 对应编号。")
    a("")
    a("**图例**：🔴 错归因 ｜ 🟠 弱证据 ｜ ⚠️ 存在冲突 ｜ ⚖️ 法定强制")
    a("")
    a("| 编号 | Place | Rule 摘要 | Evidence | Conflict | AI建议 | 我的决定 |")
    a("|---|---|---|---|---|---|---|")
    # numbering matches the packet exactly: per-group, two digits
    counters: dict[int, int] = defaultdict(int)
    for e in ctx["items"]:
        r = e["row"]
        g = e["group"]
        counters[g] += 1
        ref = f"G{g}-{counters[g]:02d}"
        flags = []
        if r["rule_id"] == ATTRIBUTION_ERROR_RULE:
            flags.append("🔴")
        if r["evidence_strength"] in WEAK:
            flags.append("🟠")
        if e["conflicts"]:
            flags.append("⚠️")
        if r["rule_layer"] == "LEGAL" and r.get("mandatory_level") == "mandatory":
            flags.append("⚖️")
        flag = "".join(flags)
        summary = (
            f"{SCOPE_ZH.get(r['animal_scope'], r['animal_scope'])} · "
            f"{EFFECT_ZH.get(r['effect'], r['effect'])}"
        )
        if r["zone_key"]:
            summary += f" · {r['zone_key']}"
        a(
            f"| **{ref}** {flag} | {r['place_name']} | "
            f"`{r['rule_id']}`：{summary} | {r['evidence_strength']} | "
            f"{'有' if e['conflicts'] else '无'} | {e['rec']} |  |"
        )
    a("")
    a("## 签署")
    a("")
    a("| 字段 | 值 |")
    a("|---|---|")
    a("| reviewer（具名） |  |")
    a("| reviewer_role |  |")
    a("| reviewed_at |  |")
    a("| 是否接受 service_dog scope 泛化（ADR-020） | ☐ 是 ☐ 否 |")
    a("| 首批批准条数（≤ `--max-approve`） |  |")
    a("| 签名 |  |")
    a("")
    return "\n".join(L) + "\n"


def main() -> int:
    rows = load_rows()
    ctx = build_context(rows)

    # newline="\n" is required: Path.write_text defaults to os.linesep on Windows,
    # which would emit CRLF and fail the repo's prettier check (endOfLine: lf).
    PACKET.write_text(render_packet(ctx), encoding="utf-8", newline="\n")
    DECISION_TEMPLATE.write_text(render_decision_template(ctx), encoding="utf-8", newline="\n")
    QUICK_TABLE.write_text(render_quick_table(ctx), encoding="utf-8", newline="\n")

    groups: dict[int, int] = defaultdict(int)
    for e in ctx["items"]:
        groups[e["group"]] += 1
    print(
        json.dumps(
            {
                "written": [str(PACKET), str(DECISION_TEMPLATE), str(QUICK_TABLE)],
                "total": len(ctx["items"]),
                "by_risk_group": {f"G{k}": groups[k] for k in sorted(groups)},
                "with_conflict": sum(1 for e in ctx["items"] if e["conflicts"]),
                "legal": sum(1 for e in ctx["items"] if e["row"]["rule_layer"] == "LEGAL"),
                "service_dog": sum(
                    1 for e in ctx["items"] if e["row"]["animal_scope"] == "service_dog"
                ),
                "all_decisions_blank": all(
                    not e["row"].get("final_decision") for e in ctx["items"]
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
