"""WAVE02_HUMAN_REVIEW_PACKET — generator (production DB derived, read-only).

Produces, under docs/expansion/:
  * WAVE02_HUMAN_REVIEW_PACKET.md
  * WAVE02_HUMAN_REVIEW_QUICK_TABLE.md
  * review_decisions_expansion_r1_wave02.json   (all human fields null/blank)

Everything is re-measured from the live petaccess DB for run
EXP-R1-W02-20260919 — never from this script's memory. The human fields
(final_decision / reviewer / decided_at) are intentionally blank; this
generator must never supply a decision (§3, §42-§45).

Read-only: no session.commit(), no DML.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import get_session_factory  # noqa: E402

RUN_ID = "EXP-R1-W02-20260919"
REVISION = "EXP-R1-W02-REVIEW-R1"
DOCS = REPO / "docs" / "expansion"
GENERATED_AT = datetime.now(UTC).isoformat()

LAYER_ZH = {"LEGAL": "法律层", "OPERATOR_POLICY": "运营层"}
EFFECT_ZH = {"allowed": "允许", "prohibited": "禁止", "conditional": "有条件允许"}
NORM_ZH = {
    "exact": "exact",
    "compound_term_split": "声明拆分",
    "legal_interpretation_required": "需法律解释",
    "parent_group_for_query_only": "仅查询父组",
}
STRENGTH_ZH = {
    "primary_direct": "一手直接",
    "search_snippet": "搜索摘录",
    "social_lead": "社媒线索",
    "web_page_text": "网页原文",
    "official_direct": "官方一手",
}
MANDATORY_ZH = {"mandatory": "强制", "advisory": "建议", "operator_discretion": "运营方裁量"}


def q(session: Session, sql: str, **params) -> list:
    return session.execute(text(sql), params).fetchall()


def md_table(rows: list[list[str]], header: list[str]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out) + "\n"


def write(name: str, body: str) -> Path:
    p = DOCS / name
    p.write_text(body, encoding="utf-8")
    print(f"  wrote {p.relative_to(REPO)}")
    return p


def collect(session: Session) -> dict:
    cands = q(
        session,
        """
        select rc.id, rc.place_id, rc.zone_id, rc.animal_scope,
               rc.action, rc.effect, rc.rule_layer, rc.mandatory_level,
               rc.source_scope_exact, rc.subject_scope_normalized,
               rc.normalization_type, rc.normative_effect, rc.holder_scope,
               rc.review_status, rc.proposed_conditions, rc.raw_text,
               rc.internal_confidence, rc.evidence_bundle_id,
               p.canonical_name as place_name, p.place_type,
               z.name as zone_name,
               s.source_type, s.issuer, s.directness, s.source_url,
               eb.quoted_fragment, eb.captured_at
        from rule_candidate rc
        join place p on p.id = rc.place_id
        left join zone z on z.id = rc.zone_id
        left join source s on s.id = rc.source_id
        left join evidence_bundle eb on eb.id = rc.evidence_bundle_id
        left join source_artifact sa on sa.id = eb.artifact_id
        where rc.expansion_run_id = :run
        order by p.canonical_name, rc.id
        """,
        run=RUN_ID,
    )
    cands = [
        dict(
            zip(
                (
                    "id",
                    "place_id",
                    "zone_id",
                    "animal_scope",
                    "action",
                    "effect",
                    "rule_layer",
                    "mandatory_level",
                    "source_scope_exact",
                    "subject_scope_normalized",
                    "normalization_type",
                    "normative_effect",
                    "holder_scope",
                    "review_status",
                    "proposed_conditions",
                    "raw_text",
                    "internal_confidence",
                    "evidence_bundle_id",
                    "place_name",
                    "place_type",
                    "zone_name",
                    "source_type",
                    "issuer",
                    "directness",
                    "source_url",
                    "quoted_fragment",
                    "captured_at",
                ),
                r,
                strict=True,
            )
        )
        for r in cands
    ]

    place_types = q(session, "select place_type, count(*) from place group by 1 order by 2 desc")
    monitors = q(
        session,
        """
        select m.id, m.url, m.schedule_minutes, m.last_http_status,
               m.failure_count, m.next_check_at, m.content_hash,
               s.issuer, s.source_type
        from source_monitor m join source s on s.id = m.source_id
        where m.expansion_run_id = :run order by s.issuer
        """,
        run=RUN_ID,
    )
    monitors = [
        dict(
            zip(
                (
                    "id",
                    "url",
                    "schedule_minutes",
                    "last_http_status",
                    "failure_count",
                    "next_check_at",
                    "content_hash",
                    "issuer",
                    "source_type",
                ),
                r,
                strict=True,
            )
        )
        for r in monitors
    ]

    counts = {
        "place": q(session, "select count(*) from place")[0][0],
        "place_geo": q(session, "select count(*) from place where location is not null")[0][0],
        "access_rule": q(session, "select count(*) from access_rule")[0][0],
        "rule_exception": q(session, "select count(*) from rule_exception")[0][0],
        "rule_candidate": q(session, "select count(*) from rule_candidate")[0][0],
    }
    return {"candidates": cands, "monitors": monitors, "place_types": place_types, "counts": counts}


def head(title: str, d: dict) -> str:
    return (
        f"# {title}\n\n"
        f"- expansion_run_id: `{RUN_ID}`\n"
        f"- review_revision: `{REVISION}`\n"
        f"- generated_at: {GENERATED_AT}\n"
        f"- 生成方式：由 `scripts/wave02_review_packet.py` 从生产库与证据文件派生，非手写\n\n"
        "> **本文件不含任何人工决策。** 决策字段为空白，须由人工复核人填写。\n"
        "> 机器只负责把材料摆到复核人面前，不负责替复核人做决定（§3, §42-§45）。\n\n"
    )


def render_packet(d: dict) -> None:
    cands = d["candidates"]
    by_place: dict[str, list] = defaultdict(list)
    for c in cands:
        by_place[c["place_name"]].append(c)

    body = head("WAVE02_HUMAN_REVIEW_PACKET — 人工复核包（EXP-R1-W02-REVIEW-R1）", d)
    body += (
        "## 1. 复核范围\n\n"
        f"- 候选规则：{len(cands)} 条，全部 `REVIEW_PENDING`\n"
        f"- 复核版本：`{REVISION}`\n"
        f"- 决策登记表：`docs/expansion/review_decisions_expansion_r1_wave02.json`\n\n"
        "## 2. 复核人须知\n\n"
        "1. 每条候选必须给出 `final_decision`：APPROVED / HOLD / REJECTED 之一。\n"
        "2. `final_decision` 与 `reviewer`、`decided_at` 必须同时填写；缺一即视为无效。\n"
        "3. 不得批注「交由系统后续自动决定」。\n"
        "4. 批准后仍走独立发布批次流程，不在本轮自动执行。\n"
        "5. `动物` 拆分行（dog/cat/other）是同一个来源术语的声明拆分，应成组审阅。\n\n"
        "## 3. 逐条材料（按场所分组）\n\n"
    )
    for place, items in sorted(by_place.items()):
        body += f"### {place}\n\n"
        rows = []
        for c in items:
            conds = c["proposed_conditions"] or []
            cond_txt = (
                "; ".join(
                    f"{x.get('condition_type')}("
                    f"{x.get('value_flag') or x.get('value_note') or x.get('value') or ''})"
                    for x in conds
                )
                if conds
                else "-"
            )
            rows.append(
                [
                    c["id"][:8],
                    c["source_scope_exact"] or "-",
                    c["subject_scope_normalized"] or "-",
                    c["animal_scope"],
                    EFFECT_ZH.get(c["effect"], c["effect"]),
                    LAYER_ZH.get(c["rule_layer"], c["rule_layer"]),
                    NORM_ZH.get(c["normalization_type"] or "", c["normalization_type"] or "-"),
                    cond_txt,
                    (c["raw_text"] or "-")[:110],
                ]
            )
        body += (
            md_table(
                rows,
                [
                    "candidate",
                    "来源用词",
                    "归一化主体",
                    "scope",
                    "effect",
                    "layer",
                    "normalization",
                    "条件",
                    "说明",
                ],
            )
            + "\n"
        )
    body += "## 4. 全部候选一览\n\n"
    all_rows = [
        [
            i,
            c["place_name"] or "-",
            c["source_scope_exact"] or "-",
            c["subject_scope_normalized"] or "-",
            c["animal_scope"],
            EFFECT_ZH.get(c["effect"], c["effect"]),
            LAYER_ZH.get(c["rule_layer"], c["rule_layer"]),
            c["source_type"] or "-",
        ]
        for i, c in enumerate(cands, 1)
    ]
    body += (
        md_table(
            all_rows,
            ["#", "场所", "来源用词", "归一化主体", "scope", "effect", "layer", "source_type"],
        )
        + "\n"
    )
    body += "## 5. 监控与新鲜度\n\n"
    body += (
        md_table(
            [
                [
                    m["issuer"] or "-",
                    m["source_type"] or "-",
                    m["url"] or "-",
                    m["last_http_status"] if m["last_http_status"] is not None else "-",
                    m["failure_count"] or 0,
                    "已设" if m["content_hash"] else "未比对",
                ]
                for m in d["monitors"]
            ],
            ["issuer", "source_type", "url", "last_http_status", "failure_count", "已哈希"],
        )
        + "\n"
    )
    write("WAVE02_HUMAN_REVIEW_PACKET.md", body)


def render_quick(d: dict) -> None:
    cands = d["candidates"]
    quick = head("WAVE02_HUMAN_REVIEW_QUICK_TABLE — 人工复核速查表", d)
    quick += f"共 {len(cands)} 条候选。决策列**空白**待填。\n\n"
    quick += (
        md_table(
            [
                [
                    i,
                    (c["place_name"] or "-")[:16],
                    c["animal_scope"],
                    c["subject_scope_normalized"] or "-",
                    EFFECT_ZH.get(c["effect"], c["effect"]),
                    LAYER_ZH.get(c["rule_layer"], c["rule_layer"]),
                    c["source_type"] or "-",
                    "",
                    "",
                    "",
                ]
                for i, c in enumerate(cands, 1)
            ],
            [
                "#",
                "场所",
                "scope",
                "归一化主体",
                "effect",
                "layer",
                "source_type",
                "final_decision",
                "reviewer",
                "decided_at",
            ],
        )
        + "\n"
    )
    write("WAVE02_HUMAN_REVIEW_QUICK_TABLE.md", quick)


def render_decisions(d: dict) -> None:
    cands = d["candidates"]
    decisions = {
        "revision": REVISION,
        "expansion_run_id": RUN_ID,
        "generated_at": GENERATED_AT,
        "reviewer": "",
        "decided_at": "",
        "note": (
            "人工决策字段必须留空由复核人填写；本文件由生成器产出，"
            "不得预填 final_decision（§3, §42-§45）。"
        ),
        "rows": [
            {
                "candidate_id": c["id"],
                "place_name": c["place_name"],
                "place_id": c["place_id"],
                "zone_id": c["zone_id"],
                "animal_scope": c["animal_scope"],
                "subject_scope_normalized": c["subject_scope_normalized"],
                "source_scope_exact": c["source_scope_exact"],
                "normalization_type": c["normalization_type"],
                "normative_effect": c["normative_effect"],
                "effect": c["effect"],
                "rule_layer": c["rule_layer"],
                "mandatory_level": c["mandatory_level"],
                "evidence_bundle_id": c["evidence_bundle_id"],
                "source_type": c["source_type"],
                # --- human fields: intentionally blank ---------------------
                "final_decision": None,
                "reviewer": "",
                "decided_at": None,
                "decision_note": "",
            }
            for c in cands
        ],
    }
    p = DOCS / "review_decisions_expansion_r1_wave02.json"
    p.write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote {p.relative_to(REPO)}  ({len(cands)} rows, human fields blank)")


def main() -> int:
    session = get_session_factory()()
    d = collect(session)
    print(f"CANDIDATES = {len(d['candidates'])}  MONITORS = {len(d['monitors'])}")
    render_packet(d)
    render_quick(d)
    render_decisions(d)
    session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
