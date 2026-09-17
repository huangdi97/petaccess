"""Governed removal of the confirmed demo / fixture contamination (§4–§12, §19).

The previous round's cleanup deliberately left this data alone: it was
classified as *historical demo content* rather than test output, and §30 forbade
deleting it without a decision. This round makes that decision, and the bar for
deleting is higher than "the name looks like a demo":

**§9** — a place may be removed only when it is ``CONFIRMED_DEMO_SEED`` *and*
its provenance is provable from a canonical registry, not from its name.
**§12** — anything that cannot be proven stays. A false negative (demo left in
place) is an acceptable outcome; a false positive (real business data deleted)
is not.

How each target is proven
-------------------------
``DEMO_PLACES``
    Every id or canonical name is a literal in ``services/api/app/db/seed.py``,
    the canonical seed script, and their sources are self-declared fiction
    (issuer text literally says 虚构 / 演示, URLs use the reserved
    ``*.example`` domain).

``FIXTURE_PLACES``
    Created inside scripted bursts — place, source and rule land within ~70 ms
    of each other — with no address, no geometry, no operator, auto-generated
    names (``DBG`` + epoch, ``T``/``T3`` + hex), placeholder instrument names
    ("T条例") carrying no URL and no document, and a rule created by direct
    ``rule.create`` that bypasses the candidate/review pipeline entirely.

``DEMO_JURISDICTION_RULES``
    The four demo-city legal-layer rows. They have no ``place_id``, which is
    exactly why the previous round's place-scoped cleanup left their Source
    behind (§20); they are removed here together with that Source.

What is never touched: ``audit_log`` (append-only, §24), ``user``, the eight
objects of the first real batch, their Sources/EvidenceBundles/Artifacts, and
the ten real pilot places.

§19 ordering
------------
Mutate → check every invariant → **then** commit. The previous implementation
committed first and validated afterwards, so a failed invariant printed
"rolled back" while the rows were already durable. This script keeps the whole
plan in one transaction and rolls back for real before any invariant result is
reported.

Usage::

    python scripts/demo_closure_cleanup.py --db-name petaccess --report
    python scripts/demo_closure_cleanup.py --db-name petaccess \
        --out artifacts/.../CLEANUP_PLAN.json            # dry-run, rolled back
    python scripts/demo_closure_cleanup.py --db-name petaccess --execute \
        --confirm-database petaccess \
        --backup artifacts/.../petaccess_before_demo_closure.dump \
        --i-reviewed-the-dry-run artifacts/.../CLEANUP_PLAN.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for extra in (str(ROOT / "scripts"), str(ROOT / "services" / "api")):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import psycopg  # noqa: E402
from dev_api_server import psycopg_url_for  # noqa: E402

from app.core.audit_events import AuditEvent  # noqa: E402
from app.db.safety import DatabaseSafetyError, guard_for_psycopg  # noqa: E402

DEFAULT_REGISTRY = ROOT / "docs" / "reality_audit" / "review_decisions_r2_final.json"
DEFAULT_MANIFEST = ROOT / "docs" / "governance" / "publish_batches" / "R2_FINAL_R3_BATCH_01B.json"

# --------------------------------------------------------------------------- #
# Targets. Each entry carries the proof, because the proof *is* the permission.
# --------------------------------------------------------------------------- #

DEMO_PLACES: tuple[dict[str, str], ...] = (
    {
        "id": "8412b521-5e1c-505d-9dec-568acb860c76",
        "name": "星河咖啡·测试店",
        "classification": "CONFIRMED_DEMO_SEED",
        "proof": "seed.py 定义；issuer=星河咖啡门店告示（虚构）",
    },
    {
        "id": "c2223bd1-d3fe-5ca0-bc4c-a131445a50c8",
        "name": "松风社区·演示",
        "classification": "CONFIRMED_DEMO_SEED",
        "proof": "seed.py 定义；issuer=松风物业服务中心（演示）",
    },
    {
        "id": "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
        "name": "云栖中心·测试商场",
        "classification": "CONFIRMED_DEMO_SEED",
        "proof": "seed.py 定义；issuer=云栖商业管理有限公司（演示）",
    },
    {
        "id": "9152b7dc-0844-52f6-957a-77bdb15d435a",
        "name": "青岚公园·演示",
        "classification": "CONFIRMED_DEMO_SEED",
        "proof": "seed.py 定义；issuer=演示市绿化市容管理局（虚构）；L1 现场",
    },
    {
        "id": "3b5a341a-e550-5f0c-b35a-319ed43bd840",
        "name": "星河咖啡·栖霞分店",
        "classification": "CONFIRMED_DEMO_SEED",
        "proof": "seed.py 定义；parent=星河咖啡·测试店；地址标注（虚构地址）",
    },
)

FIXTURE_PLACES: tuple[dict[str, str], ...] = (
    {
        "id": "466969e5-85d0-460e-9077-7492e715b934",
        "name": "DBG咖啡1789275599",
        "classification": "CONFIRMED_TEST_FIXTURE",
        "proof": (
            "名称=DBG+unix 秒；脚本化爆发（place/source/artifact/evidence/candidate"
            " 于 550ms 内完成）；"
            "无地址无坐标；source issuer=DBG牌"
        ),
    },
    {
        "id": "19db2566-7d2e-459a-bcfa-7eb3550764d4",
        "name": "T商场6ad9c1",
        "classification": "CONFIRMED_TEST_FIXTURE",
        "proof": (
            "名称=T+hex6；moderator 直接 rule.create 绕过候选/复核；"
            "source=T条例（无 URL 无法规文件）；"
            "无地址无坐标"
        ),
    },
    {
        "id": "1aa219c1-e666-4b16-b406-31991110921c",
        "name": "T3商场d14555",
        "classification": "CONFIRMED_TEST_FIXTURE",
        "proof": (
            "名称=T3+hex6；moderator 直接 rule.create 绕过候选/复核；"
            "source=T3条例（无 URL 无法规文件）；"
            "无地址无坐标"
        ),
    },
)

DEMO_JURISDICTION_RULES: tuple[dict[str, str], ...] = (
    {
        "id": "81edbfe3-a0d2-5a34-89aa-3dba3f645bb9",
        "name": "演示市养犬管理条例（虚构）",
        "classification": "CONFIRMED_DEMO_SEED",
        "proof": "无 place_id 的 demo-city 法律层规则（§20 的遗留成因）",
    },
    {
        "id": "reg_city_dining",
        "name": "演示市食品安全管理条例（虚构）",
        "classification": "CONFIRMED_DEMO_SEED",
        "proof": "同上",
    },
    {
        "id": "reg_city_greenway",
        "name": "演示市绿道管理办法（虚构）",
        "classification": "CONFIRMED_DEMO_SEED",
        "proof": "同上",
    },
    {
        "id": "reg_city_pet_cafe",
        "name": "星河区宠物友好商业试点通知（虚构）",
        "classification": "CONFIRMED_DEMO_SEED",
        "proof": "同上",
    },
)

#: A demo Source that no object ever referenced, so it is not reachable from any
#: place-scoped closure and would survive as an orphan (§8). Proven the same way
#: as the places: it is a literal in ``seed.py`` ("演示用户 B").
DEMO_ORPHAN_SOURCES: tuple[dict[str, str], ...] = (
    {
        "id": "9bf353dc-3fa5-5bfc-9d25-47dd742ddcd0",
        "issuer": "演示用户 B",
        "classification": "CONFIRMED_DEMO_SEED",
        "proof": (
            "seed.py 定义（issuer=演示用户 B）；无任何 access_rule/candidate/exception/证据引用"
        ),
    },
)

TARGET_PLACES = DEMO_PLACES + FIXTURE_PLACES

#: Every (table, column) that can keep a Source alive. A Source is deleted only
#: when all of these are empty — §8 forbids removing a shared real Source just
#: because a demo row pointed at it.
SOURCE_REFERENCES: tuple[tuple[str, str], ...] = (
    ("access_path", "source_id"),
    ("access_rule", "source_id"),
    ("amenity", "source_id"),
    ("coexistence_policy", "source_id"),
    ("data_license", "source_id"),
    ("data_source_job", "source_id"),
    ("entrance", "source_id"),
    ("event_policy", "source_id"),
    ("evidence_bundle", "source_id"),
    ("jurisdiction_rule", "source_id"),
    ("media_object", "source_id"),
    ("observation_candidate", "source_id"),
    ("place_geometry", "source_id"),
    ("place_policy_binding", "source_id"),
    ("rule_candidate", "source_id"),
    ("rule_exception", "source_id"),
    ("source_artifact", "source_id"),
    ("source_monitor", "source_id"),
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _iso(value: Any) -> Any:
    return value.isoformat() if isinstance(value, datetime) else value


def _scalar(cur: Any, sql: str, params: tuple[Any, ...] = ()) -> Any:
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else None


def _values(cur: Any, sql: str, params: tuple[Any, ...] = ()) -> list[Any]:
    cur.execute(sql, params)
    return [r[0] for r in cur.fetchall()]


def protected_sets(cur: Any, registry_path: Path, manifest_path: Path) -> dict[str, Any]:
    """The eight objects of the first real batch plus their provenance."""
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = registry.get("rows", [])
    by_rule_id = {str(r["rule_id"]): r for r in rows if r.get("rule_id")}
    labels = [str(c) for c in manifest.get("candidate_rule_ids", [])]
    candidate_ids = [str(by_rule_id[c]["candidate_id"]) for c in labels]
    rule_ids = _values(
        cur,
        "select published_rule_id from rule_candidate"
        " where id = any(%s) and published_rule_id is not null",
        (candidate_ids,),
    )
    # A carve-out candidate stamps ``published_rule_id`` with its *base* rule, so
    # the raw list repeats each base once per exception. Counting it as eight
    # rules would make the invariant ask for eight ``current`` rows against five
    # distinct rules and fail for the wrong reason.
    rule_ids = sorted(set(rule_ids))
    source_ids = _values(
        cur,
        "select distinct source_id from access_rule where id = any(%s) and source_id is not null",
        (rule_ids,),
    )
    evidence_ids = _values(
        cur,
        "select distinct evidence_bundle_id from rule_candidate"
        " where id = any(%s) and evidence_bundle_id is not null",
        (candidate_ids,),
    )
    artifact_ids = _values(
        cur,
        "select distinct artifact_id from evidence_bundle where id = any(%s)",
        (evidence_ids,),
    )
    artifact_ids += _values(
        cur, "select distinct id from source_artifact where source_id = any(%s)", (source_ids,)
    )
    exception_ids = _values(
        cur, "select id from rule_exception where rule_id = any(%s)", (rule_ids,)
    )
    return {
        "candidate_ids": candidate_ids,
        "rule_ids": rule_ids,
        "source_ids": sorted(set(source_ids)),
        "evidence_ids": sorted(set(evidence_ids)),
        "artifact_ids": sorted(set(artifact_ids)),
        "exception_ids": sorted(set(exception_ids)),
    }


def collect_targets(cur: Any) -> dict[str, Any]:
    """Resolve the full closure from the declared roots."""
    place_ids = [p["id"] for p in TARGET_PLACES]
    jr_ids = [j["id"] for j in DEMO_JURISDICTION_RULES]
    zone_ids = _values(cur, "select id from zone where place_id = any(%s)", (place_ids,))
    rule_ids = _values(
        cur,
        "select id from access_rule where place_id = any(%s) or zone_id = any(%s)",
        (place_ids, zone_ids),
    )
    candidate_ids = _values(
        cur,
        "select id from rule_candidate where place_id = any(%s) or zone_id = any(%s)",
        (place_ids, zone_ids),
    )
    source_ids = set(
        _values(
            cur,
            "select distinct source_id from access_rule where id = any(%s)"
            " and source_id is not null",
            (rule_ids,),
        )
    )
    source_ids |= set(
        _values(
            cur,
            "select distinct source_id from rule_candidate where id = any(%s)"
            " and source_id is not null",
            (candidate_ids,),
        )
    )
    source_ids |= set(
        _values(
            cur,
            "select distinct source_id from jurisdiction_rule where id = any(%s)"
            " and source_id is not null",
            (jr_ids,),
        )
    )
    source_ids |= set(
        _values(
            cur,
            "select distinct source_id from source_monitor where place_id = any(%s)"
            " and source_id is not null",
            (place_ids,),
        )
    )
    # Orphan demo sources are not reachable from any place closure, so they have
    # to be named explicitly or they survive the cleanup as stranded rows.
    source_ids |= {s["id"] for s in DEMO_ORPHAN_SOURCES}
    return {
        "place_ids": place_ids,
        "zone_ids": zone_ids,
        "rule_ids": rule_ids,
        "candidate_ids": candidate_ids,
        "jurisdiction_rule_ids": jr_ids,
        "source_ids": sorted(source_ids),
    }


def plan_steps(cur: Any, t: dict[str, Any]) -> list[tuple[str, str, tuple[Any, ...]]]:
    """Dependency-ordered deletions. Returns (label, sql, params)."""
    places, zones = t["place_ids"], t["zone_ids"]
    rules, cands = t["rule_ids"], t["candidate_ids"]
    jrs, srcs = t["jurisdiction_rule_ids"], t["source_ids"]
    return [
        ("rule_condition(rule)", "delete from rule_condition where rule_id = any(%s)", (rules,)),
        (
            "verification_event",
            "delete from verification_event where rule_id = any(%s)"
            " or place_id = any(%s) or zone_id = any(%s)",
            (rules, places, zones),
        ),
        (
            "dispute_case(target)",
            "delete from dispute_case where target_type = 'access_rule' and target_id = any(%s)",
            (rules,),
        ),
        (
            "watch_subscription(target)",
            "delete from watch_subscription where target_type in ('place','access_rule')"
            " and target_id = any(%s)",
            (places + rules,),
        ),
        ("rule_exception(rule)", "delete from rule_exception where rule_id = any(%s)", (rules,)),
        (
            "source_monitor",
            "delete from source_monitor where place_id = any(%s) or source_id = any(%s)",
            (places, srcs),
        ),
        (
            "place_policy_binding",
            "delete from place_policy_binding where place_id = any(%s) or source_id = any(%s)",
            (places, srcs),
        ),
        (
            "coexistence_policy",
            "delete from coexistence_policy where place_id = any(%s) or zone_id = any(%s)"
            " or source_id = any(%s)",
            (places, zones, srcs),
        ),
        (
            "access_path",
            "delete from access_path where place_id = any(%s) or source_id = any(%s)",
            (places, srcs),
        ),
        (
            "amenity",
            "delete from amenity where place_id = any(%s) or zone_id = any(%s)"
            " or source_id = any(%s)",
            (places, zones, srcs),
        ),
        (
            "entrance",
            "delete from entrance where place_id = any(%s) or zone_id = any(%s)"
            " or source_id = any(%s)",
            (places, zones, srcs),
        ),
        (
            "event_policy",
            "delete from event_policy where place_id = any(%s) or zone_id = any(%s)"
            " or source_id = any(%s)",
            (places, zones, srcs),
        ),
        (
            "place_geometry",
            "delete from place_geometry where place_id = any(%s) or zone_id = any(%s)"
            " or source_id = any(%s)",
            (places, zones, srcs),
        ),
        (
            "external_place_ref",
            "delete from external_place_ref where place_id = any(%s)",
            (places,),
        ),
        (
            "observation_claim",
            "delete from observation_claim where place_id = any(%s) or zone_id = any(%s)",
            (places, zones),
        ),
        (
            "operator_claim",
            "delete from operator_claim where place_id = any(%s)",
            (places,),
        ),
        (
            "observation_candidate",
            "delete from observation_candidate where place_id = any(%s) or zone_id = any(%s)"
            " or source_id = any(%s)",
            (places, zones, srcs),
        ),
        (
            "rule_candidate",
            "delete from rule_candidate where place_id = any(%s) or zone_id = any(%s)"
            " or id = any(%s)",
            (places, zones, cands),
        ),
        (
            "access_rule",
            "delete from access_rule where id = any(%s) or place_id = any(%s) or zone_id = any(%s)",
            (rules, places, zones),
        ),
        (
            "jurisdiction_rule",
            "delete from jurisdiction_rule where id = any(%s)",
            (jrs,),
        ),
        # A licence row hanging off a demo Source is demo provenance too. Leaving
        # it would strand the Source itself — the exact shape §20 forbids.
        (
            "data_license(source)",
            "delete from data_license where source_id = any(%s)",
            (srcs,),
        ),
        (
            "evidence_bundle(source)",
            "delete from evidence_bundle where source_id = any(%s)"
            " and id not in (select evidence_bundle_id from rule_candidate"
            " where evidence_bundle_id is not null)",
            (srcs,),
        ),
        ("source_artifact", "delete from source_artifact where source_id = any(%s)", (srcs,)),
        ("zone", "delete from zone where place_id = any(%s)", (places,)),
        ("place", "delete from place where id = any(%s)", (places,)),
    ]


def governed_delete(
    conn: Any,
    mutate: Any,
    invariants: Any,
    *,
    audit: list[Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """§19 — mutate, **then** check, **then** commit. In that order.

    The previous implementation committed first and validated afterwards, so a
    failed invariant printed "rolled back" while the rows were already durable.
    The ordering here is the whole point: the deletions and the invariant check
    happen inside one transaction, and the commit is the *last* statement.

    ``mutate`` and ``invariants`` are callables taking a cursor, which keeps this
    reusable (and testable) without the caller having to re-implement the
    ordering — a test can hand it a deliberately failing invariant and then prove
    from a *separate* connection that nothing survived.
    """
    with conn.cursor() as cur:
        result = mutate(cur)
        checks = invariants(cur)
    ok = checks.get("verdict") == "PASS"
    if ok and not dry_run:
        if audit is not None:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into audit_log
                      (id, actor_user_id, actor_role, action, target_type, target_id,
                       after_state, detail, created_at)
                    values
                      (gen_random_uuid()::text, %s, %s, %s, %s, %s,
                       %s::jsonb, %s::jsonb, now())
                    """,
                    audit,
                )
        conn.commit()
        committed = True
    else:
        conn.rollback()
        committed = False
    return {"result": result, "checks": checks, "committed": committed}


def _mutate_closure(cur: Any, targets: dict[str, Any]) -> dict[str, Any]:
    """The deletion plan for one governed run."""
    deleted: dict[str, int] = {}
    for label, sql, params in plan_steps(cur, targets):
        cur.execute(sql, params)
        deleted[label] = cur.rowcount

    # Sources go last, and only the ones nothing survives pointing at.
    orphans, retained = orphan_sources(cur, targets["source_ids"])
    src_deleted = 0
    for sid in orphans:
        cur.execute("delete from source where id = %s", (sid,))
        src_deleted += cur.rowcount
    deleted["source(orphan_only)"] = src_deleted
    return {"deleted": deleted, "orphans": orphans, "retained": retained}


def orphan_sources(cur: Any, source_ids: list[str]) -> tuple[list[str], list[dict[str, Any]]]:
    """Sources nothing surviving still points at (§8).

    Returns the deletable ids plus, for every retained source, *where* the
    surviving reference is — a retained shared source is a finding a reviewer has
    to be able to see, not a silent skip.
    """
    orphans: list[str] = []
    retained: list[dict[str, Any]] = []
    for sid in source_ids:
        refs: dict[str, int] = {}
        total = 0
        for table, column in SOURCE_REFERENCES:
            n = int(
                _scalar(
                    cur,
                    f"select count(*) from {table} where {column} = %s",  # noqa: S608
                    (sid,),
                )
                or 0
            )
            if n:
                refs[table] = n
                total += n
        if total == 0:
            orphans.append(sid)
        else:
            issuer = _scalar(cur, "select issuer from source where id = %s", (sid,))
            retained.append({"source_id": sid, "issuer": issuer, "references": refs})
    return orphans, retained


def invariants(cur: Any, protected: dict[str, Any], before: dict[str, Any]) -> dict[str, Any]:
    """Everything that must still hold after the deletion, checked before commit."""
    checks: dict[str, Any] = {}

    checks["batch_candidates_published"] = int(
        _scalar(
            cur,
            "select count(*) from rule_candidate where id = any(%s)"
            " and review_status = 'PUBLISHED'",
            (protected["candidate_ids"],),
        )
        or 0
    )
    checks["batch_rules_current"] = int(
        _scalar(
            cur,
            "select count(*) from access_rule where id = any(%s) and status = 'current'",
            (protected["rule_ids"],),
        )
        or 0
    )
    checks["batch_exceptions_current"] = int(
        _scalar(
            cur,
            "select count(*) from rule_exception where id = any(%s) and status = 'current'",
            (protected["exception_ids"],),
        )
        or 0
    )
    checks["batch_sources_intact"] = int(
        _scalar(cur, "select count(*) from source where id = any(%s)", (protected["source_ids"],))
        or 0
    )
    checks["batch_evidence_intact"] = int(
        _scalar(
            cur,
            "select count(*) from evidence_bundle where id = any(%s)",
            (protected["evidence_ids"],),
        )
        or 0
    )
    checks["batch_artifacts_intact"] = int(
        _scalar(
            cur,
            "select count(*) from source_artifact where id = any(%s)",
            (protected["artifact_ids"],),
        )
        or 0
    )
    checks["duplicate_current_groups"] = int(
        _scalar(
            cur,
            "select count(*) from ("
            "  select zone_id, animal_scope, action from access_rule"
            "  where status = 'current' and zone_id is not null"
            "  group by zone_id, animal_scope, action"
            "  having count(distinct effect) > 1"
            ") g",
        )
        or 0
    )
    checks["audit_rows"] = int(_scalar(cur, "select count(*) from audit_log") or 0)
    checks["place_count"] = int(_scalar(cur, "select count(*) from place") or 0)
    checks["demo_place_count"] = int(
        _scalar(
            cur,
            "select count(*) from place where id = any(%s)",
            ([p["id"] for p in TARGET_PLACES],),
        )
        or 0
    )
    checks["demo_jurisdiction_rule_count"] = int(
        _scalar(
            cur,
            "select count(*) from jurisdiction_rule where id = any(%s)",
            ([j["id"] for j in DEMO_JURISDICTION_RULES],),
        )
        or 0
    )

    expected = {
        "batch_candidates_published": len(protected["candidate_ids"]),
        "batch_rules_current": len(protected["rule_ids"]),
        "batch_exceptions_current": len(protected["exception_ids"]),
        "batch_sources_intact": len(protected["source_ids"]),
        "batch_evidence_intact": len(protected["evidence_ids"]),
        "batch_artifacts_intact": len(protected["artifact_ids"]),
        "duplicate_current_groups": 0,
        "demo_place_count": 0,
        "demo_jurisdiction_rule_count": 0,
        "audit_rows": before["audit_rows"],
        "place_count": before["place_count"] - before["target_places_present"],
    }
    failures = [f"{k}: {checks[k]} != {v}" for k, v in expected.items() if checks.get(k) != v]
    checks["failures"] = failures
    checks["verdict"] = "PASS" if not failures else "FAIL"
    return checks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--report", action="store_true", help="只读清单（不产生计划）")
    ap.add_argument("--out", default=None)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--confirm-database", default=None)
    ap.add_argument("--backup", default=None)
    ap.add_argument("--i-reviewed-the-dry-run", default=None)
    ap.add_argument("--replace", action="store_true")
    args = ap.parse_args()

    out_path = Path(args.out) if args.out else None
    if out_path and out_path.exists() and not args.replace:
        print(f"REFUSED — 计划已存在且默认不可覆盖：{out_path}", file=sys.stderr)
        return 2

    url = psycopg_url_for(args.db_name)
    if not url:
        print("无法解析数据库 URL", file=sys.stderr)
        return 3

    doc: dict[str, Any] = {
        "at": _now(),
        "database": args.db_name,
        "mode": "execute" if args.execute else "dry-run",
        "targets": {
            "demo_places": list(DEMO_PLACES),
            "fixture_places": list(FIXTURE_PLACES),
            "demo_jurisdiction_rules": list(DEMO_JURISDICTION_RULES),
            "demo_orphan_sources": list(DEMO_ORPHAN_SOURCES),
        },
    }

    try:
        with psycopg.connect(url) as conn:
            guard = guard_for_psycopg(conn)
            doc["role"] = guard.role.value
            if args.execute:
                guard.assert_production_cleanup_allowed(
                    "demo/fixture closure cleanup",
                    backup_path=args.backup,
                    reviewed_plan_path=args.i_reviewed_the_dry_run,
                )
                if args.confirm_database != guard.database_name:
                    print(
                        f"REFUSED — --confirm-database={args.confirm_database!r}"
                        f" 与实际库 {guard.database_name!r} 不一致",
                        file=sys.stderr,
                    )
                    return 3

            with conn.cursor() as cur:
                protected = protected_sets(cur, Path(args.registry), Path(args.manifest))
                targets = collect_targets(cur)
                targets["source_ids"] = [
                    s for s in targets["source_ids"] if s not in protected["source_ids"]
                ]
                doc["protected"] = dict(protected)
                doc["closure"] = {
                    k: (len(v) if isinstance(v, list) else v) for k, v in targets.items()
                }

                if args.report:
                    print("DEMO_CLOSURE_REPORT")
                    print(f"  places      = {len(targets['place_ids'])}")
                    print(f"  zones       = {len(targets['zone_ids'])}")
                    print(f"  rules       = {len(targets['rule_ids'])}")
                    print(f"  candidates  = {len(targets['candidate_ids'])}")
                    print(f"  jurisdictions = {len(targets['jurisdiction_rule_ids'])}")
                    print(f"  sources     = {len(targets['source_ids'])}")
                    overlap = sorted(set(targets["rule_ids"]) & set(protected["rule_ids"]))
                    print(f"  overlap_with_protected_rules = {len(overlap)}")
                    doc["report"] = targets
                    if out_path:
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        out_path.write_text(
                            json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n",
                            encoding="utf-8",
                        )
                        print(f"WROTE {out_path}")
                    return 4 if overlap else 0

                before = {
                    "audit_rows": int(_scalar(cur, "select count(*) from audit_log") or 0),
                    "place_count": int(_scalar(cur, "select count(*) from place") or 0),
                    # Re-running after a partial closure must not be a failure:
                    # the expectation is "the targets are gone", not "exactly N
                    # rows were deleted this time".
                    "target_places_present": int(
                        _scalar(
                            cur,
                            "select count(*) from place where id = any(%s)",
                            (targets["place_ids"],),
                        )
                        or 0
                    ),
                }
                mutate_outcome: dict[str, Any] = {}
                audit_row: list[Any] | None = None
                if args.execute:
                    # Append-only governance record of what this cleanup removed.
                    audit_row = (
                        None,
                        "governance-cleanup",
                        AuditEvent.GOVERNANCE_CLEANUP.value,
                        "place",
                        ",".join(targets["place_ids"])[:36],
                        json.dumps({}),
                        json.dumps(
                            {
                                "reason": "PRODUCTION_INTEGRITY_LIMITATION_FINAL_CLOSURE",
                                "place_ids": targets["place_ids"],
                                "jurisdiction_rule_ids": targets["jurisdiction_rule_ids"],
                                "audit_history_deleted": 0,
                            }
                        ),
                    )

                def _mutate(cur: Any) -> dict[str, Any]:
                    nonlocal mutate_outcome
                    mutate_outcome = _mutate_closure(cur, targets)
                    return mutate_outcome

                def _check(cur: Any) -> dict[str, Any]:
                    checks = invariants(cur, protected, before)
                    # The audit row names what was actually removed, so it is
                    # filled in from the mutation result before it is written.
                    if audit_row is not None:
                        payload = json.loads(audit_row[5]) | {
                            "deleted": {
                                k: int(v) for k, v in mutate_outcome.get("deleted", {}).items()
                            },
                            "sources_deleted": mutate_outcome.get("orphans", []),
                        }
                        audit_row[5] = json.dumps(payload)
                    return checks

                outcome = governed_delete(
                    conn,
                    _mutate,
                    _check,
                    audit=audit_row,
                    dry_run=not args.execute,
                )
                deleted = outcome["result"].get("deleted", {})
                orphans = outcome["result"].get("orphans", [])
                retained = outcome["result"].get("retained", [])
                doc["deleted"] = deleted
                doc["sources_considered"] = len(targets["source_ids"])
                doc["sources_deleted"] = orphans
                doc["sources_retained_shared"] = retained
                doc["invariants"] = {k: _iso(v) for k, v in outcome["checks"].items()}
                doc["committed"] = outcome["committed"]
    except DatabaseSafetyError as exc:
        print(f"DATABASE_SAFETY_REFUSED: {exc}", file=sys.stderr)
        return 3

    print("DEMO_CLOSURE_CLEANUP")
    for label, n in doc.get("deleted", {}).items():
        print(f"  {label:<28} {n}")
    print(f"  sources_considered            {doc.get('sources_considered')}")
    print(f"  sources_deleted               {len(doc.get('sources_deleted', []))}")
    print(f"  sources_retained_shared       {len(doc.get('sources_retained_shared', []))}")
    for kept in doc.get("sources_retained_shared", []):
        print(f"    kept {kept['source_id'][:8]}  {kept['issuer']}  refs={kept['references']}")
    print(f"INVARIANTS = {doc['invariants']['verdict']}")
    for f in doc["invariants"]["failures"]:
        print(f"  - {f}")
    print(f"COMMITTED = {doc.get('committed')}")

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        print(f"WROTE {out_path}")

    if doc["invariants"]["verdict"] != "PASS":
        return 1
    return 0 if doc.get("committed", True) else 1


if __name__ == "__main__":
    sys.exit(main())
