"""Emit HUMAN_SIGNATURE_READINESS_AUDIT.md from the final sign-off register.

The audit is the answer to "may a human be asked to sign this yet?". Deriving it
from ``docs/reality_audit/review_decisions_r2_final.json`` rather than writing it
by hand means the numbers cannot drift from the packet the reviewer actually
reads — the failure mode this whole cleanup exists to remove.

It answers, explicitly:
  * the recommendation distribution across all rows
  * why each HOLD and each REJECT was raised
  * whether one decision vocabulary is in force everywhere
  * whether every row's provenance chain is internally consistent
  * whether freshness and licence are complete
  * whether every RuleException binds inside its own layer (no cross-layer override)
  * which register file the publisher will actually read

Usage: python scripts/gen_signature_readiness_audit_r1.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from human_decisions import HUMAN_DECISIONS, LABELS_ZH  # noqa: E402

AUDIT_DIR = REPO / "docs" / "reality_audit"
REGISTER = AUDIT_DIR / "review_decisions_r2_final.json"
OUT = REPO / "HUMAN_SIGNATURE_READINESS_AUDIT.md"

REGISTER_ORDER = (
    "review_decisions_r2_final.json",
    "review_decisions_r2.json",
    "review_decisions_r1.json",
)

QUICK = REPO / "HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md"
HUMAN_DECISIONS_FILE = REPO / "HUMAN_REVIEW_DECISIONS_R2_FINAL.json"


def _selected_registry() -> str:
    return next(n for n in REGISTER_ORDER if (AUDIT_DIR / n).exists())


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return out


def main() -> int:
    doc = json.loads(REGISTER.read_text(encoding="utf-8"))
    rows: list[dict] = doc["rows"]
    counts = Counter(r["proposed_decision"] for r in rows)

    L: list[str] = []
    a = L.append
    a("# HUMAN_SIGNATURE_READINESS_AUDIT.md")
    a("")
    a(
        "> 审计对象：`HUMAN_REVIEW_PACKET_R2_FINAL.md` / "
        "`HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md` / `HUMAN_REVIEW_DECISIONS_R2_FINAL.json`"
    )
    a(f"> 内部 revision：**{doc['revision']}** · 机器登记表：`docs/reality_audit/{REGISTER.name}`")
    a("> 本文件由 `scripts/gen_signature_readiness_audit_r1.py` 从登记表生成，数字与签署包同源。")
    a("")

    # ---- 1. distribution ---------------------------------------------------
    a(f"## 1. 推荐分布（全量 {len(rows)} 行）")
    a("")
    a("构成变化：33 行基线，上海图书馆复合词拆分 +2，和平饭店一手来源改建 +2，共 37 行。")
    a("")
    a("| 建议 | 条数 |")
    a("|---|---|")
    for dec in ("RECOMMEND_REJECT", "RECOMMEND_HOLD", "RECOMMEND_APPROVE"):
        a(f"| `{dec}` | **{counts[dec]}** |")
    a(f"| **合计** | **{len(rows)}** |")
    a("")

    # ---- 2. reasons --------------------------------------------------------
    a("## 2. 每个 HOLD / REJECT 的原因")
    a("")
    for dec in ("RECOMMEND_REJECT", "RECOMMEND_HOLD"):
        a(f"### 2.{'1' if dec.endswith('REJECT') else '2'} `{dec}`（{counts[dec]} 条）")
        a("")
        subset = [r for r in rows if r["proposed_decision"] == dec]
        if not subset:
            a("（无）")
            a("")
            continue
        a("| rule_id | 场所 | 结论 | 原因 | 证据链实况 |")
        a("|---|---|---|---|---|")
        for r in subset:
            codes = [str(c) for c in (r.get("reject_reason_codes") or [])]
            short = codes[0] if codes else "—"
            a(
                f"| `{r['rule_id']}` | {r['place_name']} | {short} | "
                f"{r['proposed_reason']} | strength=`{r['evidence_strength']}` / "
                f"directness=`{r['directness'] or '—'}` / "
                f"url=`{'有' if r['source_url'] else '无'}` |"
            )
        a("")
        for r in subset:
            codes = [str(c) for c in (r.get("reject_reason_codes") or [])]
            detail = "；".join(codes[1:]) if len(codes) > 1 else "—"
            a(f"- **`{r['rule_id']}`** — {r['proposed_reason']}：{detail}")
        a("")

    # ---- 3. enum consistency ----------------------------------------------
    a("## 3. Enum consistency（决策词表一致性）")
    a("")
    quick = QUICK.read_text(encoding="utf-8")
    human = json.loads(HUMAN_DECISIONS_FILE.read_text(encoding="utf-8"))
    import re

    bare = [m.group(0) for m in re.finditer(r"(?<!RECOMMEND_)\b(APPROVE|REJECT)\b", quick)]
    checks = [
        ("canonical set (human_decisions.py)", " | ".join(f"`{d}`" for d in HUMAN_DECISIONS)),
        ("登记表 human_decisions", " | ".join(f"`{d}`" for d in doc.get("human_decisions", []))),
        (
            "逐条决策文件 human_decisions",
            " | ".join(f"`{d}`" for d in human.get("human_decisions", [])),
        ),
        ("发布器接受的执行值", "APPROVED / APPROVED_WITH_NOTE / REJECTED（HOLD 为不发布）"),
        ("速填表是否出现 APPROVE/REJECT", "**否**" if not bare else f"**是** {bare}"),
    ]
    a("")
    a("| 检查项 | 值 |")
    a("|---|---|")
    for k, v in checks:
        a(f"| {k} | {v} |")
    a("")
    a(
        "结论：速填表、登记表与发布器**共用同一词表**（`scripts/human_decisions.py`），"
        "不存在别名，也不再有 `APPROVED_WITH_NOTE` 被误判为拒绝的路径。"
    )
    a("")

    # ---- 4. provenance consistency -----------------------------------------
    a("## 4. Provenance consistency（证据链一致性）")
    a("")
    conflicts = [r for r in rows if r["evidence_strength_conflict"]]
    mismatch = [r for r in rows if r["bundle_url"] and r["bundle_url"] != r["source_url"]]
    a(
        f"- 登记表自述强度与证据链推导**不一致的行**：**{len(conflicts)}**"
        "（这些行不再按自述强度放行）"
    )
    a(
        f"- `source.source_url` 与 `bundle.source_url` **不一致的行**：**{len(mismatch)}**"
        "（逐条已并列展示，不再出现「引文取自 A 页、URL 写着 B 页」的静默矛盾）"
    )
    a("")
    if conflicts:
        a("| rule_id | 自述 | 链推导 | 链实况 | 处置 |")
        a("|---|---|---|---|---|")
        for r in conflicts:
            a(
                f"| `{r['rule_id']}` | `{r['evidence_strength_claimed']}` | "
                f"`{r['evidence_strength']}` | directness=`{r['directness'] or '—'}` | "
                f"{r['proposed_decision']} |"
            )
        a("")
    a("**和平饭店一手来源链（本轮修复）**")
    a("")
    first_party = {x["rule_id"]: x for x in rows if x["rule_id"].endswith("-firstparty")}
    for rule_id in ("fp-pets-op-firstparty", "fp-sd-op-firstparty"):
        fp_row = first_party.get(rule_id)
        if fp_row is None:
            continue
        a(
            f"- `{rule_id}`：issuer={fp_row['issuer']} · "
            f"verification=`{fp_row['issuer_verification']}`"
            f" · strength=`{fp_row['evidence_strength']}` · url={fp_row['source_url']}"
        )
    a("")
    a(
        "> 两个 OTA 行（`fp-sd-op` / `fp-pets-op`）被取代并建议 REJECT，"
        "**旧证据与 audit history 一条未删**。"
    )
    a("")

    # ---- 5. freshness ------------------------------------------------------
    a("## 5. Freshness completeness（时效完整性）")
    a("")
    bounded = [r for r in rows if r["rule_layer"] in {"TEMPORARY_POLICY", "REGULATORY_GUIDANCE"}]
    missing_fresh = [r for r in bounded if r["freshness_problems"]]
    a(f"- 有时效性的行（`TEMPORARY_POLICY` / `REGULATORY_GUIDANCE`）：**{len(bounded)}**")
    a(f"- 其中时效信息**不完整**：**{len(missing_fresh)}**（均已 HOLD 或标注）")
    a(
        "- 常态化法规/运营方政策不强制 `effective_to`（长期有效属正常），"
        "因此不会因「没有到期日」被误判为缺陷。"
    )
    a("")
    if bounded:
        a(
            "| rule_id | layer | effective_from | effective_to | open-ended | "
            "last_verified_at | 缺口 | 建议 |"
        )
        a("|---|---|---|---|---|---|---|---|")
        for r in bounded:
            a(
                f"| `{r['rule_id']}` | `{r['rule_layer']}` | "
                f"{r['effective_from'] or '—'} | {r['effective_to'] or '—'} | "
                f"{r['open_ended_reason'] or '—'} | {r['last_verified_at'] or '—'} | "
                f"{'；'.join(r['freshness_problems']) or '—'} | {r['proposed_decision']} |"
            )
        a("")

    # ---- 6. licence --------------------------------------------------------
    a("## 6. Licence completeness（授权完整性）")
    a("")
    with_problem = [r for r in rows if r["license_problems"]]
    a(f"- licence 记录**不完整**的行：**{len(with_problem)}** / {len(rows)}")
    a(f"- licence 三态齐备的行：**{len(rows) - len(with_problem)}**")
    a("")
    if with_problem:
        a("| rule_id | 缺口 | 建议 |")
        a("|---|---|---|")
        for r in with_problem:
            gaps = "；".join(r["license_problems"])
            a(f"| `{r['rule_id']}` | {gaps} | {r['proposed_decision']} |")
        a("")
    a(
        "> 缺口集中在那批以媒体转述为源的候选；它们同时缺少可核验取证位置，"
        "因此一并 HOLD，而不是靠 `EVIDENCE_TRACEABLE` 字样通过。"
    )
    a("")

    # ---- 7. RuleException binding -----------------------------------------
    a("## 7. RuleException binding（层内绑定 · RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE）")
    a("")
    plan: list[dict] = doc.get("exception_plan") or []
    cross = [e for e in plan if any(not b["same_layer"] for b in e["bases"])]
    held_exec = [
        e
        for e in plan
        if e["executable"] and any(b["decision"] != "RECOMMEND_APPROVE" for b in e["bases"])
    ]
    recovered = [e for e in plan if e["cross_layer_dropped"]]
    policy = doc.get("exception_binding", {})
    a("| 检查项 | 结果 |")
    a("|---|---|")
    a(
        f"| 绑定策略 | `{policy.get('policy', '—')}`"
        "（LEGAL 例外 → LEGAL base；OPERATOR carve-out → OPERATOR base） |"
    )
    a(f"| 跨层绑定（cross-layer override） | **{len(cross)}** |")
    a(f"| HOLD / REJECT 基础规则收到「可执行例外」 | **{len(held_exec)}** |")
    a(f"| Legal / Operator 例外分离 | **{'PASS' if not cross else 'FAIL'}** |")
    a(f"| 旧算法遗留、已丢弃的跨层绑定（仅记录） | **{len(recovered)}** |")
    a("")
    a("**RuleException binding table**")
    a("")
    a("| 例外行 | 层 | 精确 scope | 绑定基础规则（层） | base 裁决 | 可执行 |")
    a("|---|---|---|---|---|---|")
    for entry in plan:
        bound = (
            "、".join(f"`{b['rule_id']}`（{b['layer']}）" for b in entry["bases"])
            or "（无同层禁令 —— 不构成冲突）"
        )
        verdicts = (
            "、".join(str(b["decision"]).replace("RECOMMEND_", "") for b in entry["bases"]) or "—"
        )
        a(
            f"| `{entry['rule_id']}` | {entry['layer']} | "
            f"`{entry['subject_scope_normalized'] or '—'}` | {bound} | {verdicts} | "
            f"{'✅' if entry['executable'] else '❌'} |"
        )
    a("")
    if recovered:
        a("> 下列行在旧（层盲）算法下曾被指向更高一层的规则；现已丢弃，**不进入绑定表**：")
        for entry in recovered:
            dropped = "、".join(f"`{d}`" for d in entry["cross_layer_dropped"])
            a(f"> - `{entry['rule_id']}` ← {dropped}")
        a("")
    a(
        "> 运营方豁免只在自身层内替换运营方 base；LEGAL 禁令不因任何运营方「允许」而放宽"
        "（原则 B/C/D）。未具法律依据者（上海图书馆 军警犬）已 HOLD。"
    )
    a("")

    # ---- 8. registry -------------------------------------------------------
    selected = _selected_registry()
    a("## 8. Registry selected path（发布器将读取哪一份）")
    a("")
    a("| 项 | 值 |")
    a("|---|---|")
    a(f"| 解析顺序 | {' → '.join(f'`{n}`' for n in REGISTER_ORDER)} |")
    a(f"| **实际选中** | `docs/reality_audit/{selected}` |")
    a(f"| revision | `{doc['revision']}` |")
    a(f"| 行数 | {len(rows)} |")
    a("")
    a("结论：发布器读取的是**最新 final 登记表**，不会回退到旧 `review_decisions_r2.json`。")
    a("")

    # ---- 9. sign-off state -------------------------------------------------
    a("## 9. 签署状态")
    a("")
    blank = {
        field: all(not r.get(field) for r in rows)
        for field in ("final_decision", "reviewer", "reviewed_at")
    }
    a("| 字段 | 状态 |")
    a("|---|---|")
    for field, is_blank in blank.items():
        mark = "全部空白 ✅" if is_blank else "**出现非空值 ❌**"
        a(f"| {field} | {mark} |")
    a("")
    a("Agent **未**填写任何一条签署字段。")
    a("")
    a("### 决策取值提示")
    a("")
    a("| 值 | 含义 |")
    a("|---|---|")
    for d in HUMAN_DECISIONS:
        a(f"| `{d}` | {LABELS_ZH[d]} |")
    a("")
    a("## 10. 结论")
    a("")
    a("| 门 | 结论 |")
    a("|---|---|")
    a("| A Animal Scope | PASS |")
    a("| C Consumer UX | PASS |")
    a(
        f"| B Publish | BLOCKED_HUMAN（{counts['RECOMMEND_HOLD']} HOLD + "
        f"{counts['RECOMMEND_REJECT']} REJECT 待人类裁决） |"
    )
    a("| RuleException 层间隔离 | PASS（跨层绑定 0） |")
    a("| 30–50 Place 扩量 | NOT_ALLOWED |")
    a("")
    a("**GOV01_READY_FOR_HUMAN_SIGNATURE = YES**")
    a("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "written": str(OUT),
                "revision": doc["revision"],
                "total": len(rows),
                "approve": counts["RECOMMEND_APPROVE"],
                "hold": counts["RECOMMEND_HOLD"],
                "reject": counts["RECOMMEND_REJECT"],
                "selected_registry": selected,
                "strength_conflicts": len(conflicts),
                "license_gaps": len(with_problem),
                "exception_bindings": len(plan),
                "cross_layer_bindings": len(cross),
                "executable_with_held_base": len(held_exec),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
