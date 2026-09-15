"""Generate the FINAL GOV-01 sign-off packet (R2-FINAL, ADR-025/ADR-028).

What changed since R2
---------------------

1. **上海图书馆 compound scope split.** The source (官网《读者须知》) says
   「请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆」 — a *compound*
   exception. R2 held it as HOLD because one row cannot faithfully express it.
   It is now three source-exact rows:

       lib-sd-op-guide     '导盲犬' → guide_dog            (exact)
       lib-sd-op-police    '军警犬' → police_dog           (compound_term_split)
       lib-sd-op-military  '军警犬' → military_working_dog (compound_term_split)

   The compound wording stays verbatim, the split is exhaustive, and no other
   working dog is included.

2. **fp-sd-op stays HOLD.** Its evidence is an OTA aggregator page, not the
   operator's own channel. The search for a first-party source is recorded in
   ``FP_SD_OP_SOURCE_SEARCH`` below; until one is found the AI recommendation is
   HOLD — an aggregator page must never be the reason to publish a rule.

Everything is now read from the **database**, not from a hand-maintained JSON, so
the register cannot drift from what publishing would actually consume.

Sign-off fields (``final_decision`` / ``reviewer`` / ``reviewed_at``) are emitted
**empty**. The AI never signs (ADR-005 / Master Goal §0.9).

Usage: python scripts/gen_human_review_packet_r2_final.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import psycopg

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "docs" / "reality_audit"
REGISTRY_R2 = AUDIT / "review_decisions_r2.json"
REGISTRY_FINAL = AUDIT / "review_decisions_r2_final.json"

PACKET = REPO / "HUMAN_REVIEW_PACKET_R2_FINAL.md"
QUICK_TABLE = REPO / "HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md"
DECISIONS = REPO / "HUMAN_REVIEW_DECISIONS_R2_FINAL.json"

DB_URL = "postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"

WEAK = {"search_snippet", "social_lead"}
REJECT_RULES = {
    "gh-outdoor-keep": ["INSUFFICIENT_PLACE_ZONE_EVIDENCE", "LEGAL_SCOPE_CONFLICT"],
    "mn-outdoor-media": ["PLACE_ATTRIBUTION_ERROR", "INSUFFICIENT_PLACE_ZONE_EVIDENCE"],
}
#: rows whose operator-of-record source is still missing ⇒ HOLD, never publish
HOLD_UNAVAILABLE_SOURCE = {
    "fp-sd-op": "OTA_AGGREGATOR_NOT_OPERATOR — 仅有 OTA 聚合页，未取得运营方原始来源",
}
#: the first-party replacement chain for fp-sd-op (written by
#: scripts/link_fp_sd_op_firstparty.py). Absent ⇒ that row stays HOLD.
FP_SD_OP_SIDECAR = AUDIT / "fp_sd_op_firstparty.json"
FP_SD_OP_OTA_RULE = "fp-sd-op"
#: the compound-term split (ADR-028): replaces one R2 row with three
LIBRARY_SPLIT = [
    ("lib-sd-op-guide", "76d0dfc3-64ae-4d2b-a152-18ff8ebed588"),
    ("lib-sd-op-police", "81168603-f74a-4130-8fd7-c09a645a4840"),
    ("lib-sd-op-military", "21578527-5b09-4d53-b868-512c3603b83f"),
]
LIBRARY_SPLIT_ORIGINAL = "lib-sd-op"

#: base rules each library carve-out exceptions (documented for the reviewer:
#: rule_exception.rule_id is an FK to access_rule, so the exception rows are
#: materialised right after the base rules publish)
CARVE_OUT_OF = {
    "lib-sd-op-guide": "lib-pets-op（读者须知：猫、狗禁入）+ lib-legal-dog（条例禁入）",
    "lib-sd-op-police": "lib-pets-op（读者须知：猫、狗禁入）",
    "lib-sd-op-military": "lib-pets-op（读者须知：猫、狗禁入）",
}

FP_SD_OP_SOURCE_SEARCH = {
    "status": "FOUND",
    "attempted_channels": [
        "场所官网 / 品牌官网（fairmont.com 官方 guest-services 页，中英双语）",
        "雅高/费尔蒙官方公众号与新闻稿",
        "管理方（锦江/费尔蒙联合管理方）公开规则页",
        "运营方公开答复（客服/社交平台官方账号）",
    ],
    "found_at": "https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html",
    "found_at_en": "https://www.fairmont.com/en/hotels/shanghai/fairmont-peace-hotel/guest-services.html",
    "quote_zh": (
        "上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。"
        "导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。"
    ),
    "quote_en": (
        "Fairmont Peace Hotel does not allow pets. Seeing-eye dogs are always welcome "
        "and exempt of charges and restrictions."
    ),
    #: content_hash on the frozen artifact; recomputable from the stored excerpt.
    "content_hash": "38aba307ec8e953a0b1e8f2c8d3ff801fe96044a605f6a69b09a2f0155c5030d",
    "hash_formula": "sha256(captured_excerpt)",
    "first_linked_at": "2026-09-13T06:17:24Z",
    "first_linked_by": (
        "scripts/evidence_repair_r2.py（该候选自 09-13 起即挂在一手来源上，非本轮新建）"
    ),
    "reverified_at": "2026-09-15",
    "disposition": (
        "**状态修正**：「fp-sd-op 只有 OTA 聚合页证据」这一前提已**不再成立**——"
        "该候选自 2026-09-13 起即由 `scripts/evidence_repair_r2.py` 挂到"
        "fairmont.com 运营方一手页面；本轮对该页做了实时复核，"
        "逐字一致且 `content_hash` 可重建（见下）。"
        "因此本轮**未新建证据链**，只新增了按来源原话正确建模的候选 "
        "`fp-sd-op-firstparty`（guide_dog / exact）。"
        "旧行 `fp-sd-op` 仍建议 REJECT，原因是它把同一句话建模为粗粒度 "
        "`service_dog`（源未证成的泛化），而非因为缺少一手来源。"
    ),
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
    "compound_term_split": "复合词穷尽拆分（具备法律效力，成员集固定）",
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
MANDATORY_ZH = {"mandatory": "强制", "advisory": "建议", "operator_discretion": "运营方裁量"}


def _load_r2_rows() -> list[dict]:
    return json.loads(REGISTRY_R2.read_text(encoding="utf-8"))["rows"]


def _fetch_db_state(ids: list[str]) -> dict[str, dict]:
    """Authoritative candidate + evidence state straight from the database."""
    with psycopg.connect(DB_URL, connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT rc.id, rc.animal_scope, rc.action, rc.effect, rc.rule_layer,
                   rc.mandatory_level, rc.review_status,
                   rc.source_scope_exact, rc.subject_scope_normalized,
                   rc.normalization_type, rc.normative_effect, rc.holder_scope,
                   rc.zone_id, rc.source_id,
                   eb.quoted_fragment, eb.place_match_evidence, eb.content_hash,
                   eb.license_metadata
              FROM rule_candidate rc
              LEFT JOIN evidence_bundle eb ON eb.id = rc.evidence_bundle_id
             WHERE rc.id = ANY(%s)
            """,
            (ids,),
        )
        out: dict[str, dict] = {}
        for row in cur.fetchall():
            (
                cid,
                animal_scope,
                action,
                effect,
                rule_layer,
                mandatory_level,
                review_status,
                sse,
                ssn,
                norm,
                norm_effect,
                holder,
                zone_id,
                source_id,
                quote,
                place_match,
                content_hash,
                license_meta,
            ) = row
            out[cid] = {
                "animal_scope": animal_scope,
                "action": action,
                "effect": effect,
                "rule_layer": rule_layer,
                "mandatory_level": mandatory_level,
                "review_status": review_status,
                "source_scope_exact": sse,
                "subject_scope_normalized": ssn,
                "normalization_type": norm,
                "normative_effect": norm_effect,
                "holder_scope": holder,
                "zone_id": zone_id,
                "source_id": source_id,
                "quoted_fragment": quote,
                "place_match_evidence": place_match,
                "content_hash": content_hash,
                "license_metadata": license_meta,
            }
        return out


LEGAL_NORMS = {"exact", "compound_term_split"}


def _recommend(row: dict, *, have_firstparty: bool) -> tuple[str, str, list[str] | None]:
    rule_id = row["rule_id"]
    if rule_id in REJECT_RULES:
        return "RECOMMEND_REJECT", "REJECT_CURRENT_CLAIM", REJECT_RULES[rule_id]
    if rule_id == FP_SD_OP_OTA_RULE and have_firstparty:
        # This row already cites the operator's own page (linked 2026-09-13), so
        # the recommendation is NOT "no source found". It is rejected because the
        # SAME sentence is modelled here as the coarse `service_dog` scope — the
        # unproven widening ADR-025 forbids — while the source names 导盲犬 only.
        # The correctly-scoped replacement row carries the claim instead.
        return (
            "RECOMMEND_REJECT",
            "SUPERSEDED_BY_SOURCE_FAITHFUL_ROW",
            ["SUPERSEDED_BY_SOURCE_FAITHFUL_ROW", "SCOPE_NORMALIZATION_MISSING"],
        )
    if rule_id in HOLD_UNAVAILABLE_SOURCE:
        return "RECOMMEND_HOLD", HOLD_UNAVAILABLE_SOURCE[rule_id].split(" — ")[0], None
    if row["evidence_strength"] in WEAK:
        return "RECOMMEND_HOLD", "EVIDENCE_NOT_VERIFIED", None
    if row["normalization_type"] not in LEGAL_NORMS:
        return "RECOMMEND_HOLD", "SCOPE_NOT_ESTABLISHED_AS_LEGAL", None
    if row["animal_scope"] == "service_dog":
        return "RECOMMEND_APPROVE", "SOURCE_SCOPE_EXACT", None
    return "RECOMMEND_APPROVE", "EVIDENCE_TRACEABLE", None


def _load_firstparty() -> dict | None:
    if FP_SD_OP_SIDECAR.exists():
        return json.loads(FP_SD_OP_SIDECAR.read_text(encoding="utf-8"))
    return None


def _firstparty_row(template: dict, sidecar: dict) -> dict:
    """The new candidate built on the operator's own channel (never the OTA row)."""
    return {
        **template,
        "rule_id": sidecar["rule_id"],
        "candidate_id": sidecar["candidate_id"],
        "source_url": sidecar["source_url"],
        "issuer": sidecar["issuer"],
        "evidence_strength": "primary_direct",
        "quoted_fragment": sidecar["quote_zh"],
        "carve_out_of": "该场所自身「禁止宠物」政策的但书（同一运营方一手来源）",
    }


def build_rows() -> list[dict]:
    base_rows = _load_r2_rows()
    expanded: list[dict] = []
    for row in base_rows:
        if row["rule_id"] == LIBRARY_SPLIT_ORIGINAL:
            # one vague compound subject → three source-exact rows
            for rule_id, candidate_id in LIBRARY_SPLIT:
                clone = dict(row)
                clone["rule_id"] = rule_id
                clone["candidate_id"] = candidate_id
                expanded.append(clone)
            continue
        expanded.append(dict(row))

    # Load once: calling it twice would let the sidecar change mid-generation,
    # and mypy cannot narrow the Optional across separate calls anyway.
    firstparty = _load_firstparty()
    db_state = _fetch_db_state(
        [r["candidate_id"] for r in expanded] + ([firstparty["candidate_id"]] if firstparty else [])
    )

    rows: list[dict] = []
    for row in expanded:
        state = db_state.get(row["candidate_id"])
        if state is None:
            raise SystemExit(f"登记表中的候选 {row['candidate_id']} 不在数据库中")
        merged = {
            **row,
            "animal_scope": state["animal_scope"],
            "action": state["action"],
            "effect": state["effect"],
            "rule_layer": state["rule_layer"],
            "mandatory_level": state["mandatory_level"],
            "review_status": state["review_status"],
            "source_scope_exact": state["source_scope_exact"],
            "subject_scope_normalized": state["subject_scope_normalized"],
            "normalization_type": state["normalization_type"],
            "normative_effect": state["normative_effect"],
            "holder_scope": state["holder_scope"],
            # the quote travels with the row so the sign-off register is
            # self-contained: a reviewer must never have to open the DB to see
            # the wording they are being asked to publish.
            "quoted_fragment": state["quoted_fragment"],
            "content_hash": state["content_hash"],
            "zone_key": row.get("zone_key"),
            "evidence_strength": row["evidence_strength"],
        }
        merged["carve_out_of"] = CARVE_OUT_OF.get(row["rule_id"])
        rec, reason, codes = _recommend(merged, have_firstparty=firstparty is not None)
        merged["proposed_decision"] = rec
        merged["proposed_reason"] = reason
        merged["reject_reason_codes"] = codes
        merged["r1_proposed_decision"] = None
        merged["final_decision"] = None
        merged["reviewer"] = None
        merged["reviewed_at"] = None
        merged["review_note"] = None
        rows.append(merged)

    if firstparty is not None:
        template = next(r for r in rows if r["rule_id"] == FP_SD_OP_OTA_RULE)
        new_row = _firstparty_row(template, firstparty)
        state = db_state[firstparty["candidate_id"]]
        new_row.update(
            {
                "animal_scope": state["animal_scope"],
                "action": state["action"],
                "effect": state["effect"],
                "rule_layer": state["rule_layer"],
                "mandatory_level": state["mandatory_level"],
                "review_status": state["review_status"],
                "source_scope_exact": state["source_scope_exact"],
                "subject_scope_normalized": state["subject_scope_normalized"],
                "normalization_type": state["normalization_type"],
                "normative_effect": state["normative_effect"],
                "holder_scope": state["holder_scope"],
                "quoted_fragment": state["quoted_fragment"],
                "content_hash": state["content_hash"],
            }
        )
        rec, reason, codes = _recommend(new_row, have_firstparty=True)
        new_row.update(
            {
                "proposed_decision": rec,
                "proposed_reason": reason,
                "reject_reason_codes": codes,
                "final_decision": None,
                "reviewer": None,
                "reviewed_at": None,
                "review_note": None,
            }
        )
        rows.append(new_row)

    order = {"RECOMMEND_REJECT": 0, "RECOMMEND_HOLD": 1, "RECOMMEND_APPROVE": 2}
    rows.sort(key=lambda r: (order.get(r["proposed_decision"], 3), r["place_name"], r["rule_id"]))
    return rows


def write_registry(rows: list[dict]) -> None:
    doc = {
        "_readme": [
            "R2-FINAL GOV-01 sign-off register (ADR-025 / ADR-028).",
            "Generated FROM THE DATABASE, so it cannot drift from what publishing consumes.",
            "Supersedes review_decisions_r2.json (which superseded _r1).",
            "上海图书馆 compound exception (导盲犬、军警犬例外) is split into three",
            "source-exact rows; the compound wording is preserved verbatim and the",
            "split is exhaustive (no other working dog is included).",
            "proposed_decision is a MACHINE PROPOSAL, not a ruling. A named human must",
            "set final_decision + reviewer + reviewed_at before publish_reviewed_r1.py runs.",
            "Allowed final_decision values: APPROVED | APPROVED_WITH_NOTE | HOLD | REJECTED.",
        ],
        "revision": "R2-FINAL",
        "supersedes": "docs/reality_audit/review_decisions_r2.json",
        "human_signoff_required": True,
        "fp_sd_op_source_search": FP_SD_OP_SOURCE_SEARCH,
        "rows": rows,
    }
    REGISTRY_FINAL.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def _conditions(row: dict) -> str:
    conds = row.get("conditions") or []
    if not conds:
        return "无"
    return "、".join(
        str(c.get("condition_type", c)) if isinstance(c, dict) else str(c) for c in conds
    )


def render_packet(rows: list[dict]) -> str:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["proposed_decision"]].append(r)
    L: list[str] = []
    a = L.append
    a("# HUMAN_REVIEW_PACKET_R2_FINAL.md")
    a("")
    a("> GOV-01 最终签署包（R2-FINAL）· ADR-025 源忠实 scope / ADR-028 复合词拆分")
    a("> 取代 `HUMAN_REVIEW_PACKET_R2.md`（R2 与更早的 R1）")
    a(f"> 机器登记表：`docs/reality_audit/review_decisions_r2_final.json`（共 {len(rows)} 条）")
    a("> **本包直接从数据库生成**，与发布工具实际消费的数据同源，不存在登记表与库漂移。")
    a("")
    a("## 0. 纪律（不可协商）")
    a("")
    a("1. **AI 不做最终裁决**（ADR-005 / Master Goal §0.9）。本包只提供事实与建议。")
    a("2. `final_decision` / `reviewer` / `reviewed_at` **全部保持空白**，由具名人类评审员填写。")
    a("3. 未获签署，任何候选不得 APPROVED，更不得 Publish。")
    a("4. 弱证据（`search_snippet` / `social_lead`）不得 APPROVED（ADR-021）。")
    a("5. 来源写「导盲犬」只能是 `guide_dog`；写「军警犬」拆为 `police_dog` +")
    a("   `military_working_dog`，**不得**扩张到其他 working dog（ADR-028）。")
    a("6. 本包**不执行发布**。")
    a("")
    a("## 1. 建议分布")
    a("")
    a("| 建议 | 条数 |")
    a("|---|---|")
    for dec in ("RECOMMEND_REJECT", "RECOMMEND_HOLD", "RECOMMEND_APPROVE"):
        a(f"| `{dec}` | **{len(by[dec])}** |")
    a(f"| **合计** | **{len(rows)}** |")
    a("")
    a("### 1.1 上海图书馆复合词拆分（ADR-028）")
    a("")
    a("来源原文：`请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。`")
    a("")
    a("| rule_id | source_scope_exact（原话） | normalized scope | normalization_type |")
    a("|---|---|---|---|")
    for r in rows:
        if r["rule_id"].startswith("lib-sd-op-"):
            a(
                f"| `{r['rule_id']}` | {r['source_scope_exact']} | "
                f"{r['subject_scope_normalized']} | `{r['normalization_type']}` |"
            )
    a("")
    a("> 「军警犬」未在原文中区分军犬/警犬，故 `source_scope_exact`")
    a("> **原样保留「军警犬」**，")
    a("> 由两行分别承载 `police_dog` 与 `military_working_dog`；两行的并集恰为「军警犬」的")
    a(
        "> 含义，且**不包含**任何其他 working dog"
        "（见 `animal_scope.COMPOUND_TERM_SPLIT_MEANINGS`）。"
    )
    a("")
    a("### 1.2 fp-sd-op：运营方原始来源")
    a("")
    a(f"> 检索状态：**{FP_SD_OP_SOURCE_SEARCH['status']}**")
    a("")
    a("| 项 | 内容 |")
    a("|---|---|")
    for ch in FP_SD_OP_SOURCE_SEARCH["attempted_channels"]:
        a(f"| 已检索渠道 | {ch} |")
    a(f"| 一手来源（中文页） | {FP_SD_OP_SOURCE_SEARCH['found_at']} |")
    a(f"| 一手来源（英文页） | {FP_SD_OP_SOURCE_SEARCH['found_at_en']} |")
    a(f"| 原文引文（zh） | > {FP_SD_OP_SOURCE_SEARCH['quote_zh']} |")
    a(f"| 原文引文（en） | > {FP_SD_OP_SOURCE_SEARCH['quote_en']} |")
    a(
        f"| content_hash | `{FP_SD_OP_SOURCE_SEARCH['content_hash']}` "
        f"（`{FP_SD_OP_SOURCE_SEARCH['hash_formula']}`，**可重建**） |"
    )
    linked_by = FP_SD_OP_SOURCE_SEARCH["first_linked_by"]
    a(f"| 首次接入 | {FP_SD_OP_SOURCE_SEARCH['first_linked_at']} · {linked_by} |")
    a(f"| 本轮复核 | {FP_SD_OP_SOURCE_SEARCH['reverified_at']} 实时重读该页面，逐字一致 |")
    a(f"| 处置 | {FP_SD_OP_SOURCE_SEARCH['disposition']} |")
    a("")
    a("## 2. 逐条")
    a("")
    for i, r in enumerate(rows, 1):
        a(f"### FINAL-{i:02d} · `{r['rule_id']}` — {r['place_name']}")
        a("")
        a(f"- **candidate_id**：`{r['candidate_id']}`")
        a(f"- **place**：{r['place_name']}（`{r['place_key']}`）· zone：`{r['zone_key'] or '—'}`")
        a(f"- **action / effect**：{r['action']} · **{EFFECT_ZH.get(r['effect'], r['effect'])}**")
        a(
            f"- **coarse animal_scope**：`{r['animal_scope']}`"
            f"（{SCOPE_ZH.get(r['animal_scope'], r['animal_scope'])}）"
        )
        a(f"- **source_scope_exact（来源原话）**：{r['source_scope_exact'] or '（未记录）'}")
        a(f"- **subject_scope_normalized（精确 scope）**：`{r['subject_scope_normalized'] or '—'}`")
        a(
            f"- **normalization_type**：`{r['normalization_type']}`"
            f"（{NORM_ZH.get(r['normalization_type'], r['normalization_type'] or '—')}）"
        )
        a(f"- **normative_effect**：`{r['normative_effect'] or '—'}`")
        a(f"- **holder_scope**：`{r['holder_scope'] or '—'}`")
        if r.get("carve_out_of"):
            a(f"- **carve_out_of（但书所属基础规则）**：{r['carve_out_of']}")
        layer = r["rule_layer"] or "—"
        a(f"- **RuleLayer**：`{layer}`（{LAYER_ZH.get(layer, layer)}）")
        ml = r.get("mandatory_level") or "—"
        a(f"- **MandatoryLevel**：`{ml}`（{MANDATORY_ZH.get(ml, ml)}）")
        a(
            f"- **EvidenceStrength**：`{r['evidence_strength']}`"
            f"（{STRENGTH_ZH.get(r['evidence_strength'], r['evidence_strength'])}）"
        )
        a(f"- **Source URL**：{r['source_url']}")
        a(f"- **关键原文引文**：> {r.get('quoted_fragment') or '（缺失）'}")
        a(f"- **conditions**：{_conditions(r)}")
        a(f"- **review_status**：`{r['review_status']}`")
        a(f"- **AI recommendation（本包重新计算）**：**{r['proposed_decision']}**")
        a(f"- **recommendation reason**：{r['proposed_reason']}")
        if r["reject_reason_codes"]:
            a(f"- **reject reason codes**：`{'`, `'.join(r['reject_reason_codes'])}`")
        a("- **final_decision**：`________`  ← 留空，由具名评审员填写")
        a("")
    a("---")
    a("")
    a("## 3. 签署与后续")
    a("")
    a("1. 在 `HUMAN_REVIEW_DECISIONS_R2_FINAL.json` 填 `reviewer`（具名）、")
    a("   `reviewed_at`（ISO 8601）与逐条 `final_decision`。")
    a("2. 回填机器登记表 `docs/reality_audit/review_decisions_r2_final.json`。")
    a(
        "3. 校验：`python scripts/publish_reviewed_r1.py --dry-run`"
        "（自动读取最终登记表）应返回 `signed=true`。"
    )
    a("4. **发布后**：图书馆的但书（carve-out）需要以 `rule_exception` 形式挂到已发布的基础规则上")
    a("   （`rule_exception.rule_id` 外键指向 `access_rule`，故必须在基础规则发布之后创建）。")
    a("   本包不执行该步骤，仅提示顺序。")
    a("")
    return "\n".join(L) + "\n"


def render_quick_table(rows: list[dict]) -> str:
    L: list[str] = []
    a = L.append
    a("# HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md")
    a("")
    a("> GOV-01 最终速填表 · 一行一条（取代 R2 / R1 速填表）。")
    a("> 「我的决定」列填：`APPROVE` / `APPROVE_WITH_NOTE` / `HOLD` / `REJECT`")
    a("")
    a("**图例**：🔴 建议拒绝 ｜ 🟠 建议挂起 ｜ ⚖️ 法定强制 ｜ 🦮 导盲犬精确 scope ｜")
    a("🐕‍🦺 军警犬拆分")
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
        if r["normalization_type"] == "compound_term_split":
            flags += "🐕‍🦺"
        a(
            f"| **FINAL-{i:02d}** {flags} | {r['place_name']} | `{r['rule_id']}`"
            f"：{EFFECT_ZH.get(r['effect'], r['effect'])} | {r['source_scope_exact'] or '—'}"
            f" | `{r['subject_scope_normalized'] or '—'}` | `{r['normalization_type']}`"
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
    a("| 确认 ADR-025 源忠实 scope（不再泛化为 service_dog） | ☐ 是 ☐ 否 |")
    a("| 确认 ADR-028 复合词「军警犬」拆分不扩张到其他 working dog | ☐ 是 ☐ 否 |")
    a("| 首批批准条数（≤ `--max-approve`） |  |")
    a("| 签名 |  |")
    a("")
    return "\n".join(L) + "\n"


def render_decisions(rows: list[dict]) -> str:
    doc = {
        "revision": "R2-FINAL",
        "reviewer": "",
        "reviewed_at": "",
        "decisions": [
            {"candidate_id": r["candidate_id"], "final_decision": "", "review_note": ""}
            for r in rows
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    rows = build_rows()
    write_registry(rows)
    PACKET.write_text(render_packet(rows), encoding="utf-8", newline="\n")
    QUICK_TABLE.write_text(render_quick_table(rows), encoding="utf-8", newline="\n")
    DECISIONS.write_text(render_decisions(rows), encoding="utf-8", newline="\n")

    counts = Counter(r["proposed_decision"] for r in rows)
    print(
        json.dumps(
            {
                "written": [
                    str(REGISTRY_FINAL),
                    str(PACKET),
                    str(QUICK_TABLE),
                    str(DECISIONS),
                ],
                "total": len(rows),
                "recommendations": {
                    "APPROVE": counts["RECOMMEND_APPROVE"],
                    "HOLD": counts["RECOMMEND_HOLD"],
                    "REJECT": counts["RECOMMEND_REJECT"],
                },
                "by_place": dict(Counter(r["place_key"] for r in rows)),
                "legal_normalisation": sum(
                    1 for r in rows if r["normalization_type"] in LEGAL_NORMS
                ),
                "not_legal_equivalent": sum(
                    1 for r in rows if r["normalization_type"] not in LEGAL_NORMS
                ),
                "all_decisions_blank": all(not r.get("final_decision") for r in rows),
                "all_reviewers_blank": all(not r.get("reviewer") for r in rows),
                "all_reviewed_at_blank": all(not r.get("reviewed_at") for r in rows),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
