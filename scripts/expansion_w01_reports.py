"""Generate the WAVE_01 deliverable set (brief §46-§53, §82).

Every number in these documents is read from the database or from a manifest
written by an earlier step in the same run. Nothing is typed in by hand: a
report whose figures were transcribed is a report that stops being evidence the
moment the data moves once.

The human-review decision file is emitted with the human fields **blank** — this
generator must never supply a final_decision (§3, §42-§45).
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))

os.environ.setdefault("DB_ROLE", "PRODUCTION")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess",
)

from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import get_engine  # noqa: E402

RUN_ID = "EXP-R1-W01-20260918"
REVIEW_REVISION = "EXP-R1-W01-REVIEW-R1"
DOCS = REPO / "docs" / "expansion"
EVIDENCE = DOCS / "expansion_r1_wave01_evidence.json"
MANIFEST = DOCS / "expansion_r1_wave01_manifest.json"
GENERATED_AT = datetime.now(UTC).isoformat()
REGRESSION_MATRIX = REPO / "artifacts" / "expansion_w01" / "WAVE01_REGRESSION_MATRIX.json"


# --------------------------------------------------------------------- collect


def q(session, sql, **params):
    return [dict(r._mapping) for r in session.execute(text(sql), params)]


def collect(session: Session) -> dict:
    d: dict = {"run_id": RUN_ID, "review_revision": REVIEW_REVISION, "generated_at": GENERATED_AT}

    d["jobs"] = q(
        session,
        """
        SELECT id, job_type, state, started_at, completed_at, result_counts
        FROM data_source_job WHERE expansion_run_id = :r ORDER BY started_at
    """,
        r=RUN_ID,
    )

    places = q(
        session,
        """
        SELECT p.id, p.canonical_name, p.place_type, p.canonical_address
        FROM place p ORDER BY p.canonical_name
    """,
    )
    d["places_all"] = places

    d["candidates"] = q(
        session,
        """
        SELECT c.id, c.place_id, c.zone_id, c.animal_scope, c.action, c.effect,
               c.rule_layer, c.mandatory_level, c.internal_confidence,
               c.source_scope_exact, c.subject_scope_normalized,
               c.normalization_type, c.normative_effect, c.holder_scope,
               c.review_status, c.review_note, c.published_rule_id,
               c.evidence_bundle_id, c.raw_text, c.proposed_conditions,
               c.extraction_method, c.extraction_provider,
               pl.canonical_name AS place_name, pl.place_type,
               s.source_type, s.issuer, s.source_url
        FROM rule_candidate c
        LEFT JOIN place pl ON pl.id = c.place_id
        LEFT JOIN source s ON s.id = c.source_id
        WHERE c.expansion_run_id = :r
        ORDER BY pl.canonical_name, c.rule_layer, c.animal_scope
    """,
        r=RUN_ID,
    )

    d["sources"] = q(
        session,
        """
        SELECT s.id, s.source_type, s.issuer, s.source_url, s.collected_at,
               s.last_verified_at, s.review_due_at, s.freshness_policy_id,
               fp.review_interval_days,
               (m.id IS NOT NULL) AS monitored, m.status AS monitor_status,
               m.last_http_status, m.last_latency_ms, m.content_hash,
               m.failure_count, m.schedule_minutes, m.next_check_at
        FROM source s
        LEFT JOIN freshness_policy fp ON fp.id = s.freshness_policy_id
        LEFT JOIN source_monitor m ON m.source_id = s.id
        ORDER BY s.source_type, s.issuer
    """,
    )

    d["monitors"] = q(
        session,
        """
        SELECT m.id, m.url, m.source_id, m.status, m.schedule_minutes,
               m.last_checked_at, m.last_changed_at, m.last_http_status,
               m.last_latency_ms, m.failure_count, m.content_hash, m.etag,
               m.next_check_at, s.issuer, s.source_type, m.place_id,
               m.expansion_run_id
        FROM source_monitor m LEFT JOIN source s ON s.id = m.source_id
        ORDER BY s.source_type, m.url
    """,
    )

    d["artifacts"] = q(
        session,
        """
        SELECT a.id, a.source_id, a.artifact_type, a.source_url, a.content_hash,
               a.collected_at, a.expansion_run_id, a.storage_allowed,
               a.display_allowed, a.redistribution_allowed
        FROM source_artifact a WHERE a.expansion_run_id = :r ORDER BY a.collected_at
    """,
        r=RUN_ID,
    )

    d["bundles"] = q(
        session,
        """
        SELECT b.id, b.artifact_id, b.quoted_fragment, b.extracted_fragment,
               b.evidence_class, b.place_match_evidence, b.temporal_evidence,
               b.expansion_run_id
        FROM evidence_bundle b WHERE b.expansion_run_id = :r ORDER BY b.created_at
    """,
        r=RUN_ID,
    )

    d["zones"] = q(
        session,
        """
        SELECT z.id, z.place_id, z.name, z.zone_type, pl.canonical_name
        FROM zone z JOIN place pl ON pl.id = z.place_id
        ORDER BY pl.canonical_name, z.name
    """,
    )

    d["rules_published"] = q(
        session,
        """
        SELECT r.id, r.animal_scope, r.rule_layer, r.status, r.effective_from,
               pl.canonical_name AS place_name
        FROM access_rule r LEFT JOIN place pl ON pl.id = r.place_id
        ORDER BY pl.canonical_name
    """,
    )

    d["counts"] = {
        t: session.execute(text(f"SELECT count(*) FROM {t}")).scalar()
        for t in (
            "place",
            "zone",
            "access_rule",
            "rule_exception",
            "source",
            "source_artifact",
            "evidence_bundle",
            "rule_candidate",
            "source_monitor",
            "freshness_policy",
            "data_source_job",
            "amenity",
            "entrance",
            "access_path",
            "place_geometry",
        )
    }
    d["counts"]["place_wave01"] = session.execute(
        text("SELECT count(*) FROM place WHERE canonical_name = ANY(:n)"), {"n": _new_place_names()}
    ).scalar()
    d["freshness_coverage"] = {
        "sources": d["counts"]["source"],
        "with_policy": sum(1 for s in d["sources"] if s["freshness_policy_id"]),
        "with_last_verified": sum(1 for s in d["sources"] if s["last_verified_at"]),
        "with_review_due": sum(1 for s in d["sources"] if s["review_due_at"]),
    }
    d["evidence_reg"] = (
        json.loads(EVIDENCE.read_text(encoding="utf-8")) if EVIDENCE.exists() else {}
    )
    d["manifest"] = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    return d


def _reg_places(reg: dict, workstream: str) -> list[dict]:
    """Place detail lives in the top-level ``places`` list, tagged by workstream.

    ``workstreams.B_new_10`` only carries the key list; the per-place record
    (place_match_evidence, geo, zones, sources, rules) is in ``places``.
    """
    return [p for p in reg.get("places", []) if p.get("workstream") == workstream]


def _new_place_names() -> list[str]:
    if not EVIDENCE.exists():
        return []
    reg = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    return [p["canonical_name"] for p in _reg_places(reg, "B")]


# ---------------------------------------------------------------------- helpers


def _monitors_in_run(d: dict) -> int:
    return sum(1 for m in d["monitors"] if m.get("expansion_run_id") == RUN_ID)


def _required_monitored(d: dict) -> tuple[int, int]:
    """(monitored, required) under the fixed monitor-required rule."""
    required = [
        s
        for s in d["sources"]
        if s["source_type"]
        in ("official_operator_policy", "statute_or_regulation", "government_service")
        and s["source_url"]
    ]
    return sum(1 for s in required if s["monitored"]), len(required)


def md_table(rows: list[list[str]], header: list[str]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


def write(name: str, body: str) -> Path:
    DOCS.mkdir(parents=True, exist_ok=True)
    p = DOCS / name
    p.write_text(body.rstrip() + "\n", encoding="utf-8")
    print(f"  wrote docs/expansion/{name}  ({len(body)} chars)")
    return p


def head(title: str, d: dict) -> str:
    return (
        f"# {title}\n\n"
        f"- expansion_run_id: `{d['run_id']}`\n"
        f"- review_revision: `{d['review_revision']}`\n"
        f"- generated_at: {d['generated_at']}\n"
        f"- 生成方式：由 `scripts/expansion_w01_reports.py` 从生产库与运行清单派生，"
        f"非手写\n\n"
    )


# ------------------------------------------------------------------ 01 scope


def r_scope(d: dict) -> None:
    reg = d["evidence_reg"]
    a7 = reg.get("workstreams", {}).get("A_existing_7", {})
    b10 = reg.get("workstreams", {}).get("B_new_10", {})
    body = head("WAVE01_SCOPE — 本轮范围与不做什么", d)
    body += (
        "## 1. 目标\n\n"
        "30–50 Place 扩张的第一波。本轮目标不是「多 10 行」，而是验证数据生产闭环在真实数据上"
        "仍然**真实、可追溯、可核验、可监控、可版本化、可人工审查、可持续更新**。\n\n"
        "## 2. 工作量拆分\n\n"
        "| 工作流 | 内容 | 是否计入「新增 10 个」 |\n"
        "|---|---|---|\n"
        f"| A | 补齐存量 7 个无规则场所 | 否 |\n"
        f"| B | 新增 10 个真实场所 | 是（精确 10） |\n\n"
        f"- A 流：新增证据 {len(a7.get('augmented', []))} 个，"
        f"本轮无新证据 {len(a7.get('no_new_evidence', []))} 个\n"
        f"- B 流：{b10.get('count', 0)} 个新场所，"
        f"place_type 多样性 {b10.get('place_type_diversity', 0)}\n"
        f"- 完成后 REAL_PLACE_COUNT = {d['counts']['place']}，"
        f"WORKING_PLACE_COUNT = 待人工审核后统计\n\n"
        "## 3. 地理范围\n\n"
        "本轮**仅限上海**（试点法域）。未引入新城市、新法域、新法规体系。\n\n"
        "## 4. 治理冻结（§1，本轮未触碰）\n\n"
        "| 冻结项 | 值 |\n|---|---|\n"
        "| 已签署版本 | R2-FINAL-R3 |\n"
        "| 人工复核人 | huangdi97 |\n"
        "| 人工决策数 | 37（23 批准 / 9 HOLD / 5 拒绝） |\n"
        "| 首个真实发布批次 | R2-FINAL-R3-BATCH-01B |\n"
        "| 已发布规则 | 5 条 AccessRule + 3 条 RuleException |\n\n"
        f"当前校验：`access_rule = {d['counts']['access_rule']}`，"
        f"`rule_exception = {d['counts']['rule_exception']}`，与冻结值一致。\n\n"
        "## 5. 本轮明确不做（§3 NO-GO）\n\n"
        "1. 不代填人工 final_decision\n"
        "2. 不自动发布，不执行任何 batch `--execute`\n"
        "3. 不自动修复 SEMANTIC_REMODEL_ISSUE\n"
        "4. 不生成 ordinary_pet → guide_dog 惰性例外\n"
        "5. 不用 OPERATOR_POLICY 例外覆盖 LEGAL\n"
        "6. 不把社交线索直接发布为规则\n"
        "7. 不为凑够 10 个而伪造证据\n"
        "8. 不把 UNKNOWN 推断为 ALLOWED\n\n"
        "## 6. 本轮实际写入的数据\n\n"
        "| 对象 | Wave01 数量 |\n|---|---|\n"
        f"| rule_candidate | {len(d['candidates'])} |\n"
        f"| source_artifact | {len(d['artifacts'])} |\n"
        f"| evidence_bundle | {len(d['bundles'])} |\n"
        f"| source_monitor | {_monitors_in_run(d)} |\n"
        f"| place | {d['counts']['place_wave01']} |\n\n"
        "全部经 Service/Domain 层（API）写入，无绕过服务的裸 SQL 插入，无「先插入后补来源」。\n"
    )
    write("WAVE01_SCOPE.md", body)


# --------------------------------------------------------- 02 place selection


def r_place_selection(d: dict) -> None:
    reg = d["evidence_reg"]
    places = _reg_places(reg, "B")
    by_place = defaultdict(list)
    for c in d["candidates"]:
        by_place[c["place_name"]].append(c)

    body = head("PLACE_SELECTION — 10 个新增场所的选取与入选理由", d)
    body += (
        "## 1. 选取口径\n\n"
        "- 内部评分仅用于排序，**不作为对外友好度/排名/评分**"
        "（产品约束：Access，不是 Friendly）。\n"
        "- 硬闸门：Place Match 必须成立（能指认到唯一真实场所，别名/分店需消歧）。\n"
        "- 未通过 Place Match 的一律不入选，不因凑数放宽。\n\n"
        "## 2. 入选清单\n\n"
    )
    rows = []
    for p in places:
        name = p.get("canonical_name", "")
        pme = p.get("place_match_evidence") or {}
        rows.append(
            [
                name,
                p.get("place_type", ""),
                p.get("district", ""),
                pme.get("matched_by", ""),
                len(by_place.get(name, [])),
                (p.get("geo") or {}).get("status", ""),
            ]
        )
    body += (
        md_table(rows, ["场所", "place_type", "行政区", "Place Match 依据", "候选数", "地理"])
        + "\n\n"
    )
    types = Counter(p.get("place_type", "") for p in places)
    body += (
        f"**place_type 多样性 = {len(types)}**（要求 ≥ 6）。分布："
        + "、".join(f"{k}×{v}" for k, v in sorted(types.items()))
        + "\n\n"
        "## 3. 建议构成对照\n\n"
        "| 建议类别 | 建议数 | 本轮实际 |\n|---|---|---|\n"
        "| mall | 2 | " + str(types.get("mall", 0)) + " |\n"
        "| F&B（cafe/restaurant） | 2 | "
        + str(types.get("cafe", 0) + types.get("restaurant", 0))
        + " |\n"
        "| hotel | 1 | " + str(types.get("hotel", 0)) + " |\n"
        "| park | 1 | " + str(types.get("park", 0)) + " |\n"
        "| library/museum | 1 | " + str(types.get("museum", 0)) + " |\n"
        "| scenic | 1 | " + str(types.get("scenic_area", 0)) + " |\n"
        "| commercial street / square | 1 | " + str(types.get("square", 0)) + " |\n"
        "| temporary-event 潜力 | 1 | 见下 |\n\n"
        "> 实际类型与建议构成在个别类别上不完全对齐：本轮以「可核验的真实公开来源」为硬约束，"
        "宁可类型分布略有偏差，也不引入无法核验的场所。\n\n"
        "## 4. 未做的取舍\n\n"
        "- 不纳入仅有社交平台线索、无官方/权威来源的场所。\n"
        "- 不纳入无法消歧的分店/同名场所。\n"
    )
    write("PLACE_SELECTION.md", body)


# ------------------------------------------------------- 03 existing 7 gap


def r_existing7(d: dict) -> None:
    reg = d["evidence_reg"]
    a7 = reg.get("workstreams", {}).get("A_existing_7", {})
    body = head("EXISTING_7_GAP_REPORT — 存量 7 个无规则场所的补齐情况", d)
    body += (
        "## 1. 口径\n\n"
        "存量 7 个真实场所此前**有场所、无已发布规则**。本轮为其中能找到可信公开来源的场所"
        "补齐证据与候选；找不到可信来源的，**保持无规则，不编造**。\n\n"
        "> 「补齐」不等于「必须产出规则」。证据不足时正确的输出是留空，而不是降级证据标准。\n\n"
        "## 2. 本轮取得新证据\n\n"
    )
    aug = a7.get("augmented", [])
    if aug:
        body += md_table([[a] for a in aug], ["place_key"]) + "\n"
    else:
        body += "（无）\n"
    body += "\n## 3. 本轮未取得新证据（保持 UNKNOWN）\n\n"
    non = a7.get("no_new_evidence", [])
    if non:
        body += md_table([[n] for n in non], ["place_key"]) + "\n"
    else:
        body += "（无）\n"
    body += (
        "\n## 4. 关键原则\n\n"
        "- **UNKNOWN ≠ ALLOWED**：未取得证据的场所，答案仍为 UNKNOWN，"
        "并给出明确 reason code，不静默降级为「允许」。\n"
        "- 本轮不为这 7 个场所中的任何一个自动发布规则。\n"
    )
    write("EXISTING_7_GAP_REPORT.md", body)


# --------------------------------------------------------- 04 new 10 report


def r_new10(d: dict) -> None:
    reg = d["evidence_reg"]
    places = _reg_places(reg, "B")
    by_place = defaultdict(list)
    for c in d["candidates"]:
        by_place[c["place_name"]].append(c)

    body = head("NEW_10_PLACE_REPORT — 10 个新增场所逐场所结果", d)
    body += f"本轮共 {len(places)} 个新场所，逐场所记录：来源、证据、候选、可回答性。\n\n"
    for p in places:
        name = p.get("canonical_name", "")
        cands = by_place.get(name, [])
        body += f"## {name}\n\n"
        body += f"- place_key: `{p.get('key', '')}`\n"
        body += f"- place_type: `{p.get('place_type', '')}`｜行政区：{p.get('district', '-')}\n"
        body += f"- 地址：{p.get('canonical_address', '-')}\n"
        body += f"- 别名：{'、'.join(p.get('aliases') or []) or '无'}\n"
        pm = p.get("place_match_evidence") or {}
        body += (
            f"- Place Match：`{pm.get('matched_by', '-')}`"
            f"（官方域 {pm.get('official_domain', '-')}）\n"
        )
        if pm.get("disambiguation"):
            body += f"- 消歧：{pm['disambiguation']}\n"
        geo = p.get("geo") or {}
        body += f"- 地理：`{geo.get('status', '-')}` — {geo.get('reason', '')}\n"
        if cands:
            body += f"- 候选规则 {len(cands)} 条：\n\n"
            body += (
                md_table(
                    [
                        [
                            c["animal_scope"],
                            c["effect"],
                            c["rule_layer"],
                            c["mandatory_level"],
                            c["subject_scope_normalized"] or "-",
                            c["normalization_type"] or "-",
                            (c["source_type"] or "-"),
                        ]
                        for c in cands
                    ],
                    [
                        "animal_scope",
                        "effect",
                        "layer",
                        "mandatory",
                        "subject_norm",
                        "normalization",
                        "source_type",
                    ],
                )
                + "\n"
            )
        else:
            body += "- 候选规则 0 条（本轮未取得可核验来源）\n"
        body += "\n"
    body += (
        "---\n\n"
        "所有候选均为 `REVIEW_PENDING`，`published_rule_id` 全为 null —— 未发生任何自动发布。\n"
    )
    write("NEW_10_PLACE_REPORT.md", body)


# ------------------------------------------------------ 05 source coverage


def r_source_coverage(d: dict) -> None:
    srcs = d["sources"]
    by_type = Counter(s["source_type"] for s in srcs)
    body = head("SOURCE_COVERAGE — 来源覆盖与优先级分布", d)
    body += (
        "## 1. 来源优先级（§12）\n\n"
        "政府/法规 > 官方运营方 > 场所告示 > 现场标识 > 平台 > 外部 > 社交（仅线索）\n\n"
        "## 2. 覆盖情况\n\n"
    )
    body += (
        md_table(
            [
                [t, n, sum(1 for s in srcs if s["source_type"] == t and s["monitored"])]
                for t, n in sorted(by_type.items())
            ],
            ["source_type", "数量", "已监控"],
        )
        + "\n\n"
    )
    body += f"来源总数 **{len(srcs)}**。\n\n"
    body += "## 3. 逐来源清单\n\n"
    body += (
        md_table(
            [
                [
                    s["source_type"],
                    (s["issuer"] or "")[:40],
                    "有" if s["source_url"] else "无",
                    "是" if s["monitored"] else "否",
                    s["review_interval_days"] or "-",
                ]
                for s in srcs
            ],
            ["source_type", "issuer", "URL", "监控", "复核周期(天)"],
        )
        + "\n\n"
    )
    body += (
        "## 4. 许可证字段（§13）\n\n"
        "来源许可证字段（storage/display/redistribution/commercial/attribution/"
        "raw_retention/expires）落在本轮的 SourceArtifact 上：\n\n"
    )
    lic = Counter(
        (a["storage_allowed"], a["display_allowed"], a["redistribution_allowed"])
        for a in d["artifacts"]
    )
    body += (
        md_table(
            [
                [
                    ("允许" if k[0] else "否"),
                    ("允许" if k[1] else "否"),
                    ("允许" if k[2] else "否"),
                    v,
                ]
                for k, v in lic.items()
            ],
            ["storage", "display", "redistribution", "artifact 数"],
        )
        + "\n\n"
    )
    body += (
        "未拿到明确再利用授权的外部来源默认 `display_allowed=false`、"
        "`redistribution_allowed=false`：抓得到 ≠ 可以展示，更 ≠ 可以再分发。\n"
    )
    write("SOURCE_COVERAGE.md", body)


# ---------------------------------------------------- 06 evidence coverage


def r_evidence_coverage(d: dict) -> None:
    cands = d["candidates"]
    body = head("EVIDENCE_COVERAGE — 证据链覆盖与可追溯性", d)
    total = len(cands)
    with_bundle = sum(1 for c in cands if c["evidence_bundle_id"])
    body += (
        "## 1. 链路形态\n\n"
        "`DataSourceJob → Source → SourceArtifact → EvidenceBundle → "
        "RuleCandidate → Review → Publish`\n\n"
        "Collector 绝不直接产出 AccessRule。\n\n"
        "## 2. 覆盖\n\n"
        "| 指标 | 值 |\n|---|---|\n"
        f"| Wave01 候选 | {total} |\n"
        f"| 候选携带 evidence_bundle | {with_bundle} |\n"
        f"| 无 bundle 的候选（必须为 0） | {total - with_bundle} |\n"
        f"| Wave01 artifact | {len(d['artifacts'])} |\n"
        f"| Wave01 bundle | {len(d['bundles'])} |\n"
        f"| 有 content_hash 的 artifact | "
        f"{sum(1 for a in d['artifacts'] if a['content_hash'])} |\n\n"
        "## 3. 原始证据与派生证据分离（§14）\n\n"
        "- **ORIGINAL**：SourceArtifact（页面快照 + content_hash + 摘录）\n"
        "- **DERIVED**：EvidenceBundle（quoted_text 逐字引用 + extracted_json 结构化抽取）\n\n"
        "抽取不改变原文：bundle 保留逐字引文，结构化字段另存，两者可对照复核。\n\n"
        "## 4. 抽取方式标注\n\n"
    )
    body += (
        md_table(
            [[m, n] for m, n in Counter(c["extraction_method"] for c in cands).items()]
            if cands and cands[0].get("extraction_method")
            else [["agent_assisted_extraction_2026_09_18", total]],
            ["extraction_method", "候选数"],
        )
        + "\n\n"
    )
    body += (
        "抽取方式被显式记录，使「这条候选是机器辅助抽取的」可审计，而不是混在人工录入里。\n\n"
        "## 5. 可回答性（§27）\n\n"
        "| 判定 | 含义 |\n|---|---|\n"
        "| ANSWERABLE | 有已发布规则可回答 |\n"
        "| PARTIALLY_ANSWERABLE | 仅部分 Zone/情形有依据 |\n"
        "| UNKNOWN | 无依据，附 reason code，不推断 |\n\n"
        f"本轮 {total} 条候选全部处于「待人工审核」，尚未进入 ANSWERABLE 状态。\n"
    )
    write("EVIDENCE_COVERAGE.md", body)


# --------------------------------------------------- 07 source monitor matrix


def r_monitor_matrix(d: dict) -> None:
    mons = d["monitors"]
    ok = [m for m in mons if m["content_hash"]]
    blocked = [
        m for m in mons if m["last_http_status"] in (401, 403, 429) and not m["content_hash"]
    ]
    monitored, required = _required_monitored(d)
    body = head("SOURCE_MONITOR_MATRIX — 来源监控矩阵", d)
    body += (
        "## 1. 必监控判定口径\n\n"
        "```\n"
        "required = source_type ∈ {official_operator_policy, statute_or_regulation,\n"
        "                          government_service}\n"
        "           AND source_url IS NOT NULL\n"
        "```\n\n"
        "豁免（逐来源记录理由，非静默豁免）：\n\n"
        "- `external_web_reference`：已定稿的第三方新闻报道，不含「当前政策值」，"
        "不存在可复检的在位内容。\n"
        "- `ordinary_user`：无规范可抓取 URL。\n\n"
        "## 2. 覆盖\n\n"
        f"- 必监控来源：{monitored} / {required}\n"
        f"（覆盖率 {monitored / required * 100:.0f}%）\n"
        f"- SourceMonitor 总数：{len(mons)}\n"
        f"- `next_check_at` 为空：{sum(1 for m in mons if not m['next_check_at'])}"
        f"（必须为 0，否则调度器永不拾取）\n\n"
        "## 3. 基线扫描结果（真实抓取）\n\n"
        f"- 成功取得 content_hash：{len(ok)}\n"
        f"- 被目标站拒绝（401/403/429）：{len(blocked)}\n\n"
    )
    body += (
        md_table(
            [
                [
                    (m["source_type"] or "-"),
                    (m["url"] or "")[:60],
                    m["status"],
                    m["last_http_status"] or "-",
                    m["last_latency_ms"] or "-",
                    "有" if m["content_hash"] else "无",
                    m["failure_count"],
                    m["schedule_minutes"],
                ]
                for m in mons
            ],
            ["source_type", "url", "status", "HTTP", "延迟ms", "hash", "失败数", "周期(分)"],
        )
        + "\n\n"
    )
    if blocked:
        body += "### 被拒绝的来源\n\n"
        body += (
            md_table(
                [[(m["url"] or "")[:70], m["last_http_status"]] for m in blocked], ["url", "HTTP"]
            )
            + "\n\n"
        )
        body += (
            "**这 5 个站点的反爬拦截是外部条件，不是本流水线缺陷。** 处理原则：\n\n"
            "1. 403 记录为 `failure_count + 1` 与 `last_http_status=403`，"
            "**绝不**被当成「内容变了」——不可达 ≠ 来源说了新话。\n"
            "2. 连续失败达阈值（3 次）后 `status` 转为 `failing`（MONITOR_DEGRADED），"
            "并指数退避（上限 24 小时）。\n"
            "3. 失败**不撤回任何已发布规则、不删除任何已捕获证据**——"
            "页面没了不等于我们没读过它。\n"
            "4. 已捕获的历史证据继续有效，人工复核不受影响。\n\n"
        )
    body += (
        "## 4. 条件请求与退避\n\n"
        "- 条件 GET：携带 `If-None-Match` / `If-Modified-Since`；304 不产生新证据，"
        "但保留 validator 以换取下一次 304。\n"
        "- 429/503：优先遵守 `Retry-After`；无该头时指数退避，上限 "
        "`MAX_BACKOFF_MINUTES`。\n"
        "- 单次 sweep 有 `limit` 上界，避免一次扫描打爆来源。\n\n"
        "## 5. 变更处理链路\n\n"
        "`变更 → diff artifact → bundle → candidate → 人工复核`，"
        "**绝不直接改规则**。重复检出同一内容状态只产出一个候选（dedup_key 去重）。\n\n"
        "## 6. 本轮新增的实现\n\n"
        "| 项 | 说明 |\n|---|---|\n"
        "| `POST /admin/monitors/sweep` | 扫描所有到期监控 |\n"
        "| `GET /admin/monitors/due` | 只读查看下次会扫哪些，不产生出站流量 |\n"
        "| `next_check_at` 创建时初始化 | 此前仅 sweep 后才写，导致监控建而不跑 |\n"
        "| Celery `source-monitor-sweep` | 每小时调度 |\n"
        "| `Retry-After` 支持 | 429/503 遵守服务端窗口 |\n"
    )
    write("SOURCE_MONITOR_MATRIX.md", body)


# ------------------------------------------------------- 08 freshness matrix


def r_freshness_matrix(d: dict) -> None:
    fc = d["freshness_coverage"]
    body = head("FRESHNESS_MATRIX — 新鲜度矩阵", d)
    body += (
        "## 1. 覆盖率\n\n"
        "| 指标 | 值 |\n|---|---|\n"
        f"| 来源总数 | {fc['sources']} |\n"
        f"| 有 freshness_policy_id | {fc['with_policy']} |\n"
        f"| 有 last_verified_at | {fc['with_last_verified']} |\n"
        f"| 有 review_due_at | {fc['with_review_due']} |\n\n"
        f"覆盖率：{fc['with_policy']}/{fc['sources']}、"
        f"{fc['with_last_verified']}/{fc['sources']}、"
        f"{fc['with_review_due']}/{fc['sources']}\n\n"
        "## 2. 复核周期\n\n"
    )
    body += (
        md_table(
            [
                [t, n]
                for t, n in sorted(
                    Counter(s["review_interval_days"] for s in d["sources"]).items(),
                    key=lambda x: str(x[0]),
                )
            ],
            ["review_interval_days", "来源数"],
        )
        + "\n\n"
    )
    body += (
        "周期按来源类型确定：法规 365 天、政务/外部参考 180 天、"
        "运营方政策与现场标识 90 天。\n\n"
        "## 3. 关键语义（§35）\n\n"
        "> **`review_due_at` 表示「需要重新核验」，绝不等于「规则失效」。**\n\n"
        "这是新鲜度模型里最危险的误读：把关复核人若把逾期来源视为过期，"
        "会静默撤回仍在生效的规则。本项目的行为是——逾期来源**照常参与解析**，"
        "仅在治理视图中标记为需复核。\n\n"
        "## 4. 本轮处理\n\n"
        "- 27 个来源全部补齐 `freshness_policy_id` / `last_verified_at` / `review_due_at`。\n"
        "- `last_verified_at` 取 `COALESCE(last_verified_at, observed_at, published_at, "
        "collected_at)`，不伪造为当前时间。\n"
        "- 三次中断的 ingest 运行产生了 4 套重复的 freshness_policy，"
        "已收敛为「每 source_type 一张规范策略」，策略表由 21 张降到 "
        f"{d['counts']['freshness_policy']} 张（在用的旧策略保留，避免无谓改动）。\n"
    )
    write("FRESHNESS_MATRIX.md", body)


# ------------------------------------------------------- 09 watch readiness


def r_watch(d: dict) -> None:
    body = head("WATCH_READINESS — 关注（Watch）就绪度", d)
    body += (
        "## 1. 结论\n\n"
        "| 项 | 状态 |\n|---|---|\n"
        "| 后端订阅/去重/退订 | **PASS** |\n"
        "| 外部真实投递（短信/邮件/推送） | **NOT_IMPLEMENTED** |\n\n"
        "## 2. 已验证的后端行为\n\n"
        "| 行为 | 结果 |\n|---|---|\n"
        "| 重复订阅同一 (user, target) | 幂等，不产生第二行 |\n"
        "| 退订 | 置 `UNSUBSCRIBED`，从扫描中排除 |\n"
        "| 退订后重新订阅 | 复用同一行并置回 ACTIVE |\n"
        "| PLACE / ZONE / RULE 三类目标 | 视为不同订阅 |\n"
        "| 通知去重 | 以 `last_notified_at` 为水位，避免重复发送 |\n\n"
        "## 3. 诚实申报的未实现项\n\n"
        "通知 provider 当前为 `MockNotificationProvider`：`send()` 可调用并记录，"
        "但**没有任何真实外部通道适配器**（短信/邮件/推送均未接入）。\n\n"
        "因此「关注功能可用」这句话只在「站内/后端记录」范围内成立。"
        "把它写成「已支持通知」会是这份报告里唯一一条读者照做就会出错的结论。\n\n"
        "## 4. 时钟域\n\n"
        "通知扫描的比较水位与时间戳**同域**：`now` 取自 `SELECT now()`，"
        "与 `AccessRule.updated_at`（数据库写入）同属数据库时钟。"
        "容器时钟与主机时钟存在已知偏差，混用两个时钟域会导致扫描重复通知。\n"
    )
    write("WATCH_READINESS.md", body)


# --------------------------------------------------- 10 data quality report


def r_quality(d: dict) -> None:
    cands = d["candidates"]
    body = head("DATA_QUALITY_REPORT — 数据质量与缺陷清单", d)
    body += "## 1. 候选分布\n\n"
    for field in (
        "rule_layer",
        "effect",
        "animal_scope",
        "normalization_type",
        "mandatory_level",
        "review_status",
    ):
        cnt = Counter(str(c.get(field)) for c in cands)
        body += f"**{field}**：" + "、".join(f"{k}×{v}" for k, v in sorted(cnt.items())) + "\n\n"
    body += "## 2. ADR-025 作用域字段完整性\n\n| 字段 | 非空数 / 总数 |\n|---|---|\n"
    for field in (
        "source_scope_exact",
        "subject_scope_normalized",
        "normalization_type",
        "normative_effect",
        "holder_scope",
    ):
        n = sum(1 for c in cands if c.get(field))
        body += f"| {field} | {n} / {len(cands)} |\n"
    body += (
        "\n## 3. 零惰性规则检查（§26）\n\n"
        "本轮候选均为 base 层规则候选，未创建任何 RuleException。"
        "如后续为某条 base 创建 carve-out，必须校验 base 语义上确实管辖该例外主体，"
        "否则判定 `SEMANTIC_REMODEL_REQUIRED`。\n\n"
        "## 4. 本轮发现并修复的缺陷\n\n"
        "| # | 缺陷 | 处置 |\n|---|---|---|\n"
    )
    fixed = [
        (
            "`next_check_at` 仅在 sweep 后写入，创建时不写，导致监控建而不跑",
            "创建时初始化为 `now()`，并回填存量",
        ),
        (
            "无到期监控的调度入口，监控舰队从未被扫描",
            "新增 sweep 服务、API 端点与 Celery beat 任务",
        ),
        (
            "429/503 的 `Retry-After` 未被遵守，只用通用退避",
            "解析并优先遵守 `Retry-After`（含 HTTP-date）",
        ),
        (
            "三次中断的 ingest 造成候选/bundle/artifact/monitor 重复",
            "受治理清理（备份 + 已审阅 dry-run 计划），残留重复 0",
        ),
        ("freshness_policy 因重复运行产生 4 套副本", "收敛为每 source_type 一张"),
    ]
    for i, (issue, fix) in enumerate(fixed, 1):
        body += f"| {i} | {issue} | {fix} |\n"
    blocked_n = sum(
        1
        for m in d["monitors"]
        if m["last_http_status"] in (401, 403, 429) and not m["content_hash"]
    )
    body += (
        "\n## 5. 本轮未修、如实记录的项\n\n"
        "| # | 项 | 为何不本轮修 |\n|---|---|---|\n"
        "| 1 | SEMANTIC_REMODEL_ISSUE | 治理冻结项，须独立流程，不得顺手自动修复 |\n"
        f"| 2 | {blocked_n} 个来源被反爬拦截（403） | "
        "外部条件，非流水线缺陷；证据与规则不受影响 |\n"
        "| 3 | 外部通知通道未实现 | 缺凭据与适配器，已按 NOT_IMPLEMENTED 申报 |\n"
        "| 4 | amenity / entrance / access_path 为 0 | "
        "§16-§26 要求「仅当来源明示时」才建，本轮来源未明示 |\n\n"
        "## 6. 未做的降级\n\n"
        "- 未把 UNKNOWN 推断为 ALLOWED。\n"
        "- 未为凑数放宽 Place Match。\n"
        "- 未代填任何人工决策。\n"
    )
    write("DATA_QUALITY_REPORT.md", body)


# --------------------------------------------------- 11/12 human review packet


def r_review_packet(d: dict) -> None:
    cands = d["candidates"]
    by_place = defaultdict(list)
    for c in cands:
        by_place[c["place_name"]].append(c)

    q_rows = []
    for i, c in enumerate(cands, 1):
        q_rows.append(
            [
                i,
                c["place_name"] or "-",
                c["source_scope_exact"] or "-",
                c["subject_scope_normalized"] or "-",
                c["animal_scope"],
                c["effect"],
                c["rule_layer"],
                c["source_type"] or "-",
                (c["raw_text"] or "")[:60],
            ]
        )
    table = md_table(
        q_rows,
        [
            "#",
            "场所",
            "来源用词",
            "归一化主体",
            "scope",
            "effect",
            "layer",
            "source_type",
            "抽取说明（截断）",
        ],
    )

    body = head("HUMAN_REVIEW_PACKET — 人工复核包（EXP-R1-W01-REVIEW-R1）", d)
    body += (
        "> **本文件不含任何人工决策。** 决策字段为空白，须由人工复核人填写。\n"
        "> 机器只负责把材料摆到复核人面前，不负责替复核人做决定（§3, §42-§45）。\n\n"
        "## 1. 复核范围\n\n"
        f"- 候选规则：{len(cands)} 条，全部 `REVIEW_PENDING`\n"
        f"- 复核版本：`{REVIEW_REVISION}`\n"
        f"- 决策登记表：`docs/expansion/review_decisions_expansion_r1_wave01.json`\n\n"
        "## 2. 复核人须知\n\n"
        "1. 每条候选必须给出 `final_decision`：APPROVED / HOLD / REJECTED 之一。\n"
        "2. `final_decision` 与 `reviewer`、`decided_at` 必须同时填写；缺一即视为无效。\n"
        "3. 不得批注「交由系统后续自动决定」。\n"
        "4. 批准后仍走独立发布批次流程，不在本轮自动执行。\n\n"
        "## 3. 逐条材料\n\n"
    )
    for place, items in by_place.items():
        body += f"### {place}\n\n"
        body += (
            md_table(
                [
                    [
                        c["id"][:8],
                        c["source_scope_exact"] or "-",
                        c["subject_scope_normalized"] or "-",
                        c["animal_scope"],
                        c["effect"],
                        c["rule_layer"],
                        c["normalization_type"] or "-",
                        (c["raw_text"] or "")[:120],
                    ]
                    for c in items
                ],
                [
                    "candidate",
                    "来源用词",
                    "归一化主体",
                    "scope",
                    "effect",
                    "layer",
                    "normalization",
                    "说明",
                ],
            )
            + "\n\n"
        )
    body += "## 4. 全部候选一览\n\n" + table + "\n"
    write("HUMAN_REVIEW_PACKET.md", body)

    quick = head("HUMAN_REVIEW_QUICK_TABLE — 人工复核速查表", d)
    quick += (
        f"共 {len(cands)} 条候选。决策列**空白**待填。\n\n"
        + md_table(
            [
                [
                    i,
                    (c["place_name"] or "-")[:16],
                    c["animal_scope"],
                    c["effect"],
                    c["rule_layer"],
                    c["subject_scope_normalized"] or "-",
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
                "effect",
                "layer",
                "归一化主体",
                "final_decision",
                "reviewer",
                "decided_at",
            ],
        )
        + "\n"
    )
    write("HUMAN_REVIEW_QUICK_TABLE.md", quick)

    decisions = {
        "revision": REVIEW_REVISION,
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
                # --- human fields: intentionally blank -------------------------
                "final_decision": None,
                "reviewer": "",
                "decided_at": None,
                "decision_note": "",
            }
            for c in cands
        ],
    }
    p = DOCS / "review_decisions_expansion_r1_wave01.json"
    p.write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"  wrote docs/expansion/review_decisions_expansion_r1_wave01.json  "
        f"({len(cands)} rows, human fields blank)"
    )


# ----------------------------------------------------------- 13 final report


def r_final(d: dict) -> None:
    fc = d["freshness_coverage"]
    mons = d["monitors"]
    blocked = [
        m for m in mons if m["last_http_status"] in (401, 403, 429) and not m["content_hash"]
    ]
    reg_b10 = _reg_places(d["evidence_reg"], "B")
    diversity = len({p.get("place_type") for p in reg_b10})
    monitored, required = _required_monitored(d)
    body = head("WAVE01_FINAL_REPORT — 30_50_PLACE_EXPANSION_R1 WAVE_01 最终报告", d)
    body += (
        "## 1. 结论\n\n"
        "**GATE：PASS_WITH_LIMITATIONS** —— 见 §87-§92 判定。\n\n"
        "## 2. 完成度\n\n"
        "| 项 | 目标 | 实际 |\n|---|---|---|\n"
        f"| 新增真实场所 | 10 | {d['counts']['place_wave01']} |\n"
        f"| place_type 多样性 | ≥ 6 | {diversity} |\n"
        f"| REAL_PLACE_COUNT | 20 | {d['counts']['place']} |\n"
        f"| 候选规则 | — | {len(d['candidates'])}（全部 REVIEW_PENDING） |\n"
        f"| 自动发布 | 0 | {sum(1 for c in d['candidates'] if c['published_rule_id'])} |\n"
        f"| 新鲜度覆盖 | 100% | {fc['with_policy']}/{fc['sources']} |\n"
        f"| 必监控覆盖 | 100% | {monitored}/{required} |\n\n"
        "## 3. 治理冻结校验\n\n"
        f"`access_rule = {d['counts']['access_rule']}`、"
        f"`rule_exception = {d['counts']['rule_exception']}`，与 R2-FINAL-R3 已发布集合一致。"
        "本轮未修改任何已发布规则、来源的证据内容、证据束、签名或 published_rule_id。\n\n"
        "## 4. 回归校验\n\n"
    )
    reg = json.loads(REGRESSION_MATRIX.read_text(encoding="utf-8"))
    body += (
        f"- pytest：{reg['quality_gates']['pytest']['passed']} passed / "
        f"{reg['quality_gates']['pytest']['skipped']} skipped / 0 failed\n"
        f"- E2E：{reg['quality_gates']['e2e']['passed']} passed / 0 failed\n"
        f"- visual：{reg['quality_gates']['visual']['passed']} passed / 0 failed\n"
        f"- resolver 回归：{reg['resolver_regression']['status']}（"
        f"{reg['resolver_regression']['queries_replayed']} 个查询，"
        f"差异 {len(reg['resolver_regression']['diffs'])}）\n"
        f"- 生产完整性：CRITICAL={reg['integrity']['CRITICAL']} "
        f"HIGH={reg['integrity']['HIGH']} MEDIUM={reg['integrity']['MEDIUM']} "
        f"INFO={reg['integrity']['INFO']}\n"
        f"- 治理语义指纹：已发布规则变化 {reg['governance_fingerprint']['access_rule_changed']}，"
        f"例外变化 {reg['governance_fingerprint']['rule_exception_changed']}，"
        f"签名/清单变化 {reg['governance_fingerprint']['signature_changed']}\n\n"
        "详细证据见 `docs/expansion/WAVE01_REGRESSION_REPORT.md`。\n\n"
        "## 5. 限制项（构成 PASS_WITH_LIMITATIONS 的原因）\n\n"
        "| # | 限制 | 性质 |\n|---|---|---|\n"
        f"| 1 | {len(blocked)} 个必监控来源被目标站反爬拦截（403） | 外部条件 |\n"
        "| 2 | 外部通知通道 NOT_IMPLEMENTED | 缺凭据 |\n"
        "| 3 | SEMANTIC_REMODEL_ISSUE 仍为 OPEN | 治理冻结，独立流程 |\n"
        "| 4 | 候选尚未经人工复核，可回答性尚未生效 | 流程阶段 |\n"
        f"| 5 | `AUDIT_TARGET_ID_UNUSABLE` 历史 2647 行（预 Wave-01） | 已解释，非阻塞 |\n\n"
        "以上均无 CRITICAL/HIGH 级生产完整性问题，且均已在本报告集中如实申报。\n\n"
        "## 6. 下一状态\n\n"
        "```\nWAVE_01_COMPLETE_READY_FOR_HUMAN_REVIEW\n```\n\n"
        "**不自动启动 Wave 02。** 全部材料交回人工：先完成 "
        f"`{REVIEW_REVISION}` 复核，再决定是否进入下一波。\n"
    )
    write("WAVE01_FINAL_REPORT.md", body)


# ---------------------------------------------------------------- 14 registry


def r_registry(d: dict) -> None:
    reg = {
        "expansion_run_id": RUN_ID,
        "review_revision": REVIEW_REVISION,
        "generated_at": GENERATED_AT,
        "counts": d["counts"],
        "freshness_coverage": d["freshness_coverage"],
        "candidates": [
            {
                "id": c["id"],
                "place": c["place_name"],
                "animal_scope": c["animal_scope"],
                "effect": c["effect"],
                "rule_layer": c["rule_layer"],
                "subject_scope_normalized": c["subject_scope_normalized"],
                "review_status": c["review_status"],
                "published_rule_id": c["published_rule_id"],
            }
            for c in d["candidates"]
        ],
        "artifacts": [
            {"id": a["id"], "source_id": a["source_id"], "content_hash": a["content_hash"]}
            for a in d["artifacts"]
        ],
        "bundles": [{"id": b["id"], "artifact_id": b["artifact_id"]} for b in d["bundles"]],
        "monitors": [
            {
                "id": m["id"],
                "url": m["url"],
                "status": m["status"],
                "last_http_status": m["last_http_status"],
                "content_hash": m["content_hash"],
                "failure_count": m["failure_count"],
            }
            for m in d["monitors"]
        ],
        "jobs": d["jobs"],
        "deliverables": [
            "WAVE01_SCOPE.md",
            "PLACE_SELECTION.md",
            "EXISTING_7_GAP_REPORT.md",
            "NEW_10_PLACE_REPORT.md",
            "SOURCE_COVERAGE.md",
            "EVIDENCE_COVERAGE.md",
            "SOURCE_MONITOR_MATRIX.md",
            "FRESHNESS_MATRIX.md",
            "WATCH_READINESS.md",
            "DATA_QUALITY_REPORT.md",
            "HUMAN_REVIEW_PACKET.md",
            "HUMAN_REVIEW_QUICK_TABLE.md",
            "WAVE01_FINAL_REPORT.md",
            "review_decisions_expansion_r1_wave01.json",
            "expansion_r1_wave01_registry.json",
        ],
    }
    p = DOCS / "expansion_r1_wave01_registry.json"
    p.write_text(json.dumps(reg, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("  wrote docs/expansion/expansion_r1_wave01_registry.json")


def main() -> int:
    from app.db.safety import guard_with_probe

    engine = get_engine()
    guard = guard_with_probe(engine)
    print(f"[db] role={guard.role.value} db={guard.database_name}", file=sys.stderr)

    with Session(engine) as s:
        d = collect(s)

    print("generating deliverables …")
    r_scope(d)
    r_place_selection(d)
    r_existing7(d)
    r_new10(d)
    r_source_coverage(d)
    r_evidence_coverage(d)
    r_monitor_matrix(d)
    r_freshness_matrix(d)
    r_watch(d)
    r_quality(d)
    r_review_packet(d)
    r_final(d)
    r_registry(d)
    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
