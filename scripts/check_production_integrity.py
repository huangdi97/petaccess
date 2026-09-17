"""Read-only production integrity scan (§31–§33).

`pytest` proves the code does what the tests say; this proves the *data* is
internally consistent. Both matter, and only one of them existed.

Every check below is a question the schema can answer about itself: is there a
place with two competing current rules, an exception whose base is gone, a
published candidate with no published object, a `current` rule that supersedes
itself, a monitor nobody will ever run again. The script never writes; it prints
the findings, and records them to `artifacts/production_integrity_baseline.json`.

A baseline that says `PASS` and nothing else is not a baseline. This records the
actual findings — including the ones we have decided not to fix this round — with
severity, count and examples, so the next round can see whether they got better or
worse.

Severities (§32):

===========  ====================================================================
CRITICAL     a governed answer is wrong or unowned: HOLD/REJECTED published,
             exception with no base, two current rules fighting over the same
             resolver input
HIGH         lineage broken, or test data sitting in production: duplicate
             current rules, missing Evidence / Source / Audit, orphan exception,
             test fixtures present
MEDIUM       hygiene that will bite later: stale monitor, missing metadata,
             unusable audit target ids
LOW / INFO   observations
===========  ====================================================================

Usage::

    python scripts/check_production_integrity.py --db-name petaccess
    python scripts/check_production_integrity.py --db-name petaccess \\
        --out artifacts/production_integrity_baseline.json --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for extra in (str(ROOT / "scripts"), str(ROOT / "services" / "api")):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import psycopg  # noqa: E402
from dev_api_server import psycopg_url_for  # noqa: E402

from app.db.safety import DatabaseSafetyError, guard_for_psycopg  # noqa: E402

DEFAULT_OUT = ROOT / "artifacts" / "production_integrity_baseline.json"

#: Reused verbatim from the publish tooling so "test fixture" means the same
#: thing in both places. Kept as SQL regexes over `place.canonical_name` and
#: `source.issuer`.
FIXTURE_PLACE_PATTERNS = (
    r"^E2E-[A-D] .*",
    r"^回滚测试场所[0-9a-f]{6}$",
    r"^强制级别测试场所[0-9a-f]{6}$",
    r"^例外隔离商场[0-9a-f]{8}$",
    r"^例外测试商场[0-9a-f]{6}$",
    r"^证据测试场所-[0-9a-f]{6}$",
    r"^认领演示商店$",
    r"^质量基线测试咖啡$",
)
FIXTURE_SOURCE_PATTERNS = (
    r"^测试条例（",
    r"^测试法规来源$",
    r"^社区初版$",
    r"^quality-baseline$",
    r"^证据来源-[0-9a-f]{6}$",
    r"^回滚测试来源（[0-9a-f]{6}）$",
    r"^E2E-[A-D] .*",
)
TEST_ACTOR_EMAIL = (
    r"^(v05mod|evmod|mand|rb|exc|media|bnd|it|e2e|verif|ramod|rapl|rbac|plain|adm|adm2|dbg"
    r"|exc2|exc3|provenance|perf|[^@]*用户|[^@]*复核|[^@]*运营)-?[0-9a-f]{0,8}@example\.com$"
)


@dataclass(frozen=True)
class Check:
    code: str
    severity: str
    question: str
    sql: str
    detail_sql: str | None = None


CHECKS: tuple[Check, ...] = (
    # ---------------------------------------------------------------- CRITICAL
    Check(
        "HOLD_OR_REJECTED_PUBLISHED",
        "CRITICAL",
        "是否有 HOLD / REJECTED 的候选被发布出去了？",
        """
        select c.id, c.review_status, c.published_rule_id
        from rule_candidate c
        where c.published_rule_id is not null
          and c.review_status in ('HOLD', 'REJECTED', 'REVIEW_PENDING', 'MATCH_PENDING')
        """,
    ),
    Check(
        "ORPHAN_RULE_EXCEPTION",
        "CRITICAL",
        "是否存在 RuleException 指向不存在的 base AccessRule？",
        """
        select e.id, e.rule_id, e.status
        from rule_exception e
        left join access_rule r on r.id = e.rule_id
        where e.status = 'current' and (e.rule_id is null or r.id is null)
        """,
    ),
    Check(
        "CROSS_LAYER_EXCEPTION",
        "CRITICAL",
        "是否存在挂在无层级 base 上的 current 例外（层级绑定不成立）？",
        """
        select e.id, e.rule_id, coalesce(r.rule_layer, '<NULL>') as base_layer
        from rule_exception e
        join access_rule r on r.id = e.rule_id
        where e.status = 'current' and r.rule_layer is null
        """,
    ),
    Check(
        "SELF_SUPERSEDE",
        "CRITICAL",
        "是否有规则 supersede 自己？",
        """
        select id, supersedes_rule_id from access_rule
        where supersedes_rule_id is not null and supersedes_rule_id = id
        """,
    ),
    Check(
        "SUPERSESSION_CYCLE",
        "CRITICAL",
        "是否存在 supersession 环？",
        """
        with recursive walk as (
          select id as start_id, supersedes_rule_id as next_id, 1 as depth
          from access_rule where supersedes_rule_id is not null
          union all
          select w.start_id, r.supersedes_rule_id, w.depth + 1
          from walk w join access_rule r on r.id = w.next_id
          where w.depth < 32 and r.supersedes_rule_id is not null
        )
        select distinct start_id from walk where next_id = start_id
        """,
    ),
    Check(
        "CONFLICTING_CURRENT_RULES",
        "CRITICAL",
        "是否有两条 current 规则争抢同一个 resolver 输入"
        "（同 place/zone/layer/scope/action 但 effect 不同）？",
        """
        select place_id, coalesce(zone_id, '<none>') as zone_id,
               coalesce(rule_layer, '<NULL>') as rule_layer, animal_scope, action,
               count(distinct effect) as distinct_effects, count(*) as n,
               array_agg(distinct effect) as effects, array_agg(id order by id) as rule_ids
        from access_rule
        where status = 'current'
        group by place_id, zone_id, rule_layer, animal_scope, action
        having count(distinct effect) > 1
        """,
    ),
    # -------------------------------------------------------------------- HIGH
    Check(
        "DUPLICATE_CURRENT_RULE",
        "HIGH",
        "同一 (place, zone, layer, scope, action) 上是否有多条 current 规则？",
        """
        select place_id, coalesce(zone_id, '<none>') as zone_id,
               coalesce(rule_layer, '<NULL>') as rule_layer, animal_scope, action,
               count(*) as n, array_agg(id order by recorded_at, id) as rule_ids,
               min(recorded_at) as first_recorded_at, max(recorded_at) as last_recorded_at
        from access_rule
        where status = 'current'
        group by place_id, zone_id, rule_layer, animal_scope, action
        having count(*) > 1
        """,
    ),
    Check(
        "PUBLISHED_WITHOUT_EVIDENCE",
        "HIGH",
        "已发布候选是否缺 EvidenceBundle？",
        """
        select id, review_status, published_rule_id from rule_candidate
        where published_rule_id is not null and evidence_bundle_id is null
        """,
    ),
    Check(
        "PUBLISHED_WITHOUT_SOURCE",
        "HIGH",
        "已发布对象是否缺 Source？",
        """
        select 'candidate' as kind, c.id, c.review_status as state
        from rule_candidate c
        where c.published_rule_id is not null and c.source_id is null
        union all
        select 'access_rule', r.id, r.status
        from access_rule r
        where r.source_id is null and r.rule_layer is not null
        """,
    ),
    Check(
        "PUBLISHED_WITHOUT_AUDIT",
        "HIGH",
        "已发布候选是否缺 candidate.publish 审计？",
        """
        -- The publish audit records `target_type = 'access_rule'` with
        -- `target_id` = the published rule, not the candidate. Matching on the
        -- candidate id reports 251 false positives.
        select c.id, c.review_status, c.published_rule_id
        from rule_candidate c
        where c.published_rule_id is not null
          and not exists (
            select 1 from audit_log a
            where a.action = 'candidate.publish' and a.target_id = c.published_rule_id
          )
        """,
    ),
    Check(
        "PUBLISHED_OBJECT_WITHOUT_CANDIDATE",
        "HIGH",
        "是否存在没有任何候选引用的已发布 AccessRule（血缘断头）？",
        """
        select r.id, r.rule_layer, r.status, r.created_at
        from access_rule r
        where r.rule_layer is not null
          and not exists (select 1 from rule_candidate c where c.published_rule_id = r.id)
          and r.origin_authority is not null
        """,
    ),
    Check(
        "ORPHAN_ZONE",
        "HIGH",
        "是否存在 zone 指向不存在的 place？",
        """
        select z.id, z.place_id from zone z
        left join place p on p.id = z.place_id
        where p.id is null
        """,
    ),
    Check(
        "ORPHAN_PLACE_RELATION",
        "HIGH",
        "是否存在 place.parent_place_id / zone.parent_zone_id 悬空？",
        """
        select 'place' as kind, p.id, p.parent_place_id as parent
        from place p left join place q on q.id = p.parent_place_id
        where p.parent_place_id is not null and q.id is null
        union all
        select 'zone', z.id, z.parent_zone_id
        from zone z left join zone w on w.id = z.parent_zone_id
        where z.parent_zone_id is not null and w.id is null
        """,
    ),
    Check(
        "TEST_FIXTURE_PLACE_IN_PRODUCTION",
        "HIGH",
        "正式库里是否还残留测试夹具场所？",
        """
        select p.id, p.canonical_name, p.created_at,
               (select count(*) from access_rule r where r.place_id = p.id) as rules
        from place p
        where p.canonical_name ~ any(%(fixture_places)s::text[])
        """,
        detail_sql="select canonical_name, count(*) from place "
        "where canonical_name ~ any(%(fixture_places)s::text[]) group by 1 order by 2 desc",
    ),
    Check(
        "TEST_FIXTURE_SOURCE_IN_PRODUCTION",
        "HIGH",
        "正式库里是否还残留测试夹具 Source？",
        """
        select s.id, s.issuer, s.created_at from source s
        where s.issuer ~ any(%(fixture_sources)s::text[])
        """,
        detail_sql="select issuer, count(*) from source "
        "where issuer ~ any(%(fixture_sources)s::text[]) group by 1 order by 2 desc",
    ),
    Check(
        "TEST_ACCOUNT_IN_PRODUCTION",
        "HIGH",
        "正式库里是否还残留每轮测试创建的一次性账号？",
        """
        select u.id, u.email, u.created_at from "user" u
        where u.email ~ %(test_actor)s
        """,
        detail_sql='select split_part(email, $$-$$, 1) as family, count(*) from "user" '
        "where email ~ %(test_actor)s group by 1 order by 2 desc",
    ),
    # ------------------------------------------------------------------ MEDIUM
    Check(
        "AUDIT_TARGET_ID_UNUSABLE",
        "MEDIUM",
        "审计记录的 target_id 是否可以用于血缘追溯？",
        """
        select target_type, count(*) as rows_with_broken_target_id
        from audit_log where target_id = 'None' group by 1 order by 2 desc
        """,
    ),
    Check(
        "INVALID_CURRENT_STATUS",
        "MEDIUM",
        "是否存在状态值不在枚举内的 current 规则？",
        """
        select id, status from access_rule
        where status is not null and status not in ('current', 'superseded', 'withdrawn', 'draft')
        """,
    ),
    Check(
        "INVALID_FRESHNESS_METADATA",
        "MEDIUM",
        "是否存在 review_due_at 早于 last_verified_at 这类自相矛盾的时效字段？",
        """
        select id, last_verified_at, review_due_at, effective_from, effective_to
        from access_rule
        where (review_due_at is not null and last_verified_at is not null
               and review_due_at < last_verified_at)
           or (effective_to is not null and effective_from is not null
               and effective_to < effective_from)
        """,
    ),
    Check(
        "DUPLICATE_MONITOR",
        "MEDIUM",
        "是否存在同一 source 上重复的 SourceMonitor？",
        """
        select source_id, coalesce(url, '<null>') as url, count(*) as n
        from source_monitor group by 1, 2 having count(*) > 1
        """,
    ),
    Check(
        "STALE_MONITOR",
        "MEDIUM",
        "是否存在长期未检查但仍标记为 active 的 SourceMonitor？",
        """
        select id, source_id, status, last_checked_at, next_check_at
        from source_monitor
        where status = 'active'
          and coalesce(last_checked_at, created_at) < now() - interval '30 days'
        """,
    ),
    # -------------------------------------------------------------------- INFO
    Check(
        "RULES_WITHOUT_PLACE",
        "INFO",
        "有多少规则不挂在任何场所上（平台/法条层）？",
        """
        select coalesce(rule_layer, '<NULL>') as rule_layer, count(*) as n
        from access_rule where place_id is null group by 1 order by 2 desc
        """,
    ),
    Check(
        "ORPHAN_SOURCE",
        "INFO",
        "有多少 Source 已无任何对象引用？",
        """
        select count(*) as orphan_sources from source s
        where not exists (select 1 from evidence_bundle b where b.source_id = s.id)
          and not exists (select 1 from source_artifact a where a.source_id = s.id)
          and not exists (select 1 from rule_candidate c where c.source_id = s.id)
          and not exists (select 1 from access_rule r where r.source_id = s.id)
          and not exists (select 1 from rule_exception e where e.source_id = s.id)
        """,
    ),
)

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def _rows(cur: Any, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    cur.execute(sql, params or {})
    cols = [d.name for d in cur.description]
    out: list[dict[str, Any]] = []
    for row in cur.fetchall():
        rec: dict[str, Any] = {}
        for name, value in zip(cols, row, strict=False):
            if isinstance(value, datetime):
                rec[name] = value.isoformat()
            elif isinstance(value, list):
                rec[name] = [
                    str(v) if not isinstance(v, datetime) else v.isoformat() for v in value
                ]
            else:
                rec[name] = value
        out.append(rec)
    return out


def _one(cur: Any, sql: str) -> Any:
    cur.execute(sql)
    row = cur.fetchone()
    return row[0] if row else None


def scan(conn: Any) -> dict[str, Any]:
    params = {
        "fixture_places": list(FIXTURE_PLACE_PATTERNS),
        "fixture_sources": list(FIXTURE_SOURCE_PATTERNS),
        "test_actor": TEST_ACTOR_EMAIL,
    }
    with conn.cursor() as cur:
        identity = {
            "current_database": _one(cur, "select current_database()"),
            "alembic_head": _one(cur, "select version_num from alembic_version"),
            "server_version": _one(cur, "show server_version"),
        }
        findings: list[dict[str, Any]] = []
        for check in CHECKS:
            try:
                rows = _rows(cur, check.sql, params)
            except Exception as exc:  # noqa: BLE001 - a broken check must be visible, not fatal
                findings.append(
                    {
                        "code": check.code,
                        "severity": "CRITICAL",
                        "question": check.question,
                        "count": -1,
                        "status": "CHECK_FAILED",
                        "error": f"{type(exc).__name__}: {exc}",
                        "examples": [],
                    }
                )
                continue
            count = int(rows[0]["n"]) if len(rows) == 1 and "n" in rows[0] else len(rows)
            finding: dict[str, Any] = {
                "code": check.code,
                "severity": check.severity,
                "question": check.question,
                "count": count,
                "status": "FOUND" if count else "CLEAN",
                "examples": rows[:5],
            }
            if check.detail_sql and rows:
                finding["breakdown"] = _rows(cur, check.detail_sql, params)
            findings.append(finding)

    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 9), f["code"]))
    counts: dict[str, int] = {}
    for finding in findings:
        if finding["status"] == "CLEAN":
            continue
        counts[finding["severity"]] = counts.get(finding["severity"], 0) + 1

    return {
        "at": datetime.now(UTC).isoformat(),
        "identity": identity,
        "checks_total": len(CHECKS),
        "findings": findings,
        "severity_counts": counts,
        "unresolved_critical": [
            f["code"] for f in findings if f["severity"] == "CRITICAL" and f["status"] != "CLEAN"
        ],
        "unresolved_high": [
            f["code"] for f in findings if f["severity"] == "HIGH" and f["status"] != "CLEAN"
        ],
    }


def render(doc: dict[str, Any]) -> str:
    lines = [
        f"PRODUCTION_INTEGRITY_SCAN = {'PASS' if not doc['unresolved_critical'] else 'FAIL'}",
        f"  database       = {doc['identity']['current_database']}",
        f"  alembic_head   = {doc['identity']['alembic_head']}",
        f"  checks         = {doc['checks_total']}",
    ]
    for finding in doc["findings"]:
        mark = "OK  " if finding["status"] == "CLEAN" else "FOUND"
        lines.append(
            f"  [{mark}] {finding['severity']:<8} {finding['code']:<38} {finding['count']}"
        )
    lines.append(f"  severity_counts = {doc['severity_counts']}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--replace", action="store_true")
    args = ap.parse_args()

    out_path = Path(args.out)
    if out_path.exists() and not args.replace and args.json:
        print(f"REFUSED — {out_path} 已存在；基线的价值在于不可覆盖，确需重跑请加 --replace")
        return 2

    with psycopg.connect(psycopg_url_for(args.db_name)) as conn:
        try:
            guard = guard_for_psycopg(conn)
        except DatabaseSafetyError as exc:
            print(f"DATABASE_SAFETY_REFUSED: {exc}", file=sys.stderr)
            return 3
        doc = scan(conn)

    doc["database"] = guard.database_name
    doc["role"] = guard.role.value
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(render(doc))
    print(f"WROTE {out_path}")
    return 0 if not doc["unresolved_critical"] else 1


if __name__ == "__main__":
    sys.exit(main())
