"""Read-only semantic fingerprint of a governed database.

The point of this script is one sentence (§51):

    run the whole QA suite, then prove production is byte-for-byte where it was.

A row *count* cannot prove that. `delete one audit row + insert one audit row`
leaves every count identical while the data has changed, and a suite that
truncates-and-reseeds a table would look perfectly clean. So the fingerprint
digests **content**, not just cardinality:

* every table in `public` gets `row_count` plus an order-independent-but-stable
  digest of every row's `::text`,
* the governed objects get explicit key sets (id + updated_at) so a rename or a
  status flip is visible even if the row count is unchanged,
* the first real publish batch gets its own section, because those eight objects
  are the assets this whole round exists to protect,
* the human signature file is hashed by content.

Two snapshots taken around a full QA run are compared with ``--compare``, which
exits non-zero on any difference. Nothing here writes to the database: the only
side effect is one JSON file, and it refuses to overwrite an existing one unless
``--replace`` is passed.

Usage::

    python scripts/production_fingerprint.py --db-name petaccess \\
        --label A --out artifacts/production_isolation/PROD_FINGERPRINT_A.json
    python scripts/production_fingerprint.py --compare \\
        artifacts/production_isolation/PROD_FINGERPRINT_A.json \\
        artifacts/production_isolation/PROD_FINGERPRINT_B.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for extra in (str(ROOT / "scripts"), str(ROOT / "services" / "api")):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import psycopg  # noqa: E402
from dev_api_server import psycopg_url_for  # noqa: E402

from app.db.safety import (  # noqa: E402
    DatabaseSafetyError,
    DatabaseSafetyGuard,
    guard_for_psycopg,
)

DEFAULT_REGISTRY = ROOT / "docs" / "reality_audit" / "review_decisions_r2_final.json"
DEFAULT_MANIFEST = ROOT / "docs" / "governance" / "publish_batches" / "R2_FINAL_R3_BATCH_01B.json"

#: Tables whose content is copied verbatim into a separate key set. Everything
#: else is covered by the all-tables digest; these are the ones a reviewer will
#: want to eyeball in a diff.
GOVERNED_TABLES: tuple[str, ...] = (
    "access_rule",
    "rule_exception",
    "rule_candidate",
    "source",
    "evidence_bundle",
    "source_artifact",
    "source_monitor",
    "watch_subscription",
    "audit_log",
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rows(cur: Any, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    cur.execute(sql, params)
    cols = [d.name for d in cur.description]
    out: list[dict[str, Any]] = []
    for row in cur.fetchall():
        rec: dict[str, Any] = {}
        for name, value in zip(cols, row, strict=False):
            rec[name] = value.isoformat() if isinstance(value, datetime) else value
        out.append(rec)
    return out


def _scalar(cur: Any, sql: str, params: Sequence[Any] = ()) -> Any:
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else None


def _iso(value: Any) -> Any:
    return value.isoformat() if isinstance(value, datetime) else value


def table_fingerprints(cur: Any) -> dict[str, dict[str, Any]]:
    """Row count + content digest for every user table.

    The digest is computed by Postgres (`md5(string_agg(row::text, E'\\x1e' order by row::text))`),
    which keeps the whole table out of Python's memory and makes the result
    independent of how the rows come back.
    """
    names = [
        r["tablename"]
        for r in _rows(
            cur,
            "select tablename from pg_tables where schemaname = 'public' order by tablename",
        )
    ]
    out: dict[str, dict[str, Any]] = {}
    for name in names:
        count = _scalar(cur, f'select count(*) from "{name}"')  # noqa: S608 - name from pg_tables
        digest = _scalar(
            cur,
            f"select md5(coalesce(string_agg(t::text, E'\\x1e' order by t::text), '')) "  # noqa: S608
            f'from "{name}" t',
        )
        out[name] = {"rows": count, "digest": digest}
    return out


def governed_section(cur: Any, selected: Sequence[str], registry: dict[str, Any]) -> dict[str, Any]:
    by_rule = {str(r["rule_id"]): r for r in registry.get("rows", [])}
    candidate_ids = [by_rule[r]["candidate_id"] for r in selected if r in by_rule]

    key_sets: dict[str, list[dict[str, Any]]] = {}
    for table in GOVERNED_TABLES:
        cols = [
            r["column_name"]
            for r in _rows(
                cur,
                "select column_name from information_schema.columns "
                "where table_name = %s and table_schema = 'public' "
                "order by ordinal_position",
                (table,),
            )
        ]
        wanted = [c for c in ("id", "status", "updated_at", "created_at") if c in cols]
        if "id" not in wanted:
            continue
        key_sets[table] = _rows(
            cur,
            f'select {", ".join(wanted)} from "{table}" order by id',  # noqa: S608
        )

    published_rules = _rows(
        cur,
        "select id, place_id, zone_id, rule_layer, animal_scope, action, effect, status, "
        "source_id, supersedes_rule_id, origin_authority, mandatory_level, "
        "subject_scope_normalized, normalization_type, normative_effect, holder_scope, "
        "recorded_at, created_at, updated_at "
        "from access_rule where id in (select published_rule_id from rule_candidate "
        "where id = any(%s)) order by id",
        (list(candidate_ids),),
    )
    published_exceptions = _rows(
        cur,
        "select id, rule_id, animal_scope, effect, status, source_id, "
        "subject_scope_normalized, normalization_type, normative_effect, holder_scope, "
        "created_at, updated_at "
        "from rule_exception where rule_id in (select published_rule_id from rule_candidate "
        "where id = any(%s)) order by id",
        (list(candidate_ids),),
    )

    seal_rows: list[dict[str, Any]] = []
    for rule_id, cand in sorted(by_rule.items()):
        if rule_id not in selected:
            continue
        row = _rows(
            cur,
            "select id, animal_scope, action, effect, review_status, reviewer_id, "
            "review_note, rule_layer, mandatory_level, source_scope_exact, "
            "subject_scope_normalized, normalization_type, normative_effect, holder_scope, "
            "published_rule_id, evidence_bundle_id, source_id, created_at, updated_at "
            "from rule_candidate where id = %s",
            (cand["candidate_id"],),
        )
        seal_rows.append(
            {
                "rule_id": rule_id,
                "candidate_id": cand["candidate_id"],
                "candidate": row[0] if row else None,
            }
        )

    exceptions_by_rule = {r["rule_id"]: r for r in published_exceptions}
    for seal in seal_rows:
        published = next(
            (
                r
                for r in published_rules
                if r["id"] == (seal["candidate"] or {}).get("published_rule_id")
            ),
            None,
        )
        seal["published_access_rule"] = published
        seal["published_rule_exceptions"] = [
            v for k, v in exceptions_by_rule.items() if published and k == published["id"]
        ]

    duplicate_current = _rows(
        cur,
        "select place_id, zone_id, coalesce(rule_layer, '<NULL>') as rule_layer, animal_scope, "
        "action, count(*) as n, array_agg(id order by id) as rule_ids "
        "from access_rule where status = 'current' "
        "group by place_id, zone_id, coalesce(rule_layer, '<NULL>'), animal_scope, action "
        "having count(*) > 1 order by n desc, place_id",
    )

    return {
        "key_sets": key_sets,
        "published_access_rules": published_rules,
        "published_rule_exceptions": published_exceptions,
        "batch_objects": seal_rows,
        "duplicate_current_groups": duplicate_current,
    }


def build(db_name: str, *, registry_path: Path, manifest_path: Path) -> dict[str, Any]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected = [str(x) for x in manifest.get("candidate_rule_ids", [])]

    url = psycopg_url_for(db_name)
    with psycopg.connect(url) as conn:
        guard: DatabaseSafetyGuard = guard_for_psycopg(conn)
        with conn.cursor() as cur:
            identity = {
                "current_database": _scalar(cur, "select current_database()"),
                "current_user": _scalar(cur, "select current_user"),
                "server_version": _scalar(cur, "show server_version"),
                "alembic_head": _scalar(cur, "select version_num from alembic_version"),
                "role": guard.role.value,
            }
            tables = table_fingerprints(cur)
            governed = governed_section(cur, selected, registry)

    semantic = {
        "identity": {k: v for k, v in identity.items() if k != "role"},
        "tables": tables,
        "governed": governed,
        "human_registry_sha256": hashlib.sha256(registry_path.read_bytes()).hexdigest(),
        "batch_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }
    global_digest = _sha256_text(
        json.dumps(semantic, ensure_ascii=False, sort_keys=True, default=str)
    )
    return {
        "at": _now(),
        "database": db_name,
        "role": guard.role.value,
        "selected": selected,
        "fingerprint": global_digest,
        "semantic": semantic,
        "totals": {name: info["rows"] for name, info in tables.items()},
    }


def compare(a_path: Path, b_path: Path) -> int:
    a = json.loads(a_path.read_text(encoding="utf-8"))
    b = json.loads(b_path.read_text(encoding="utf-8"))
    sa, sb = a["semantic"], b["semantic"]
    diffs: list[str] = []

    if sa["identity"] != sb["identity"]:
        diffs.append(f"identity: {sa['identity']} -> {sb['identity']}")

    for name in sorted(set(sa["tables"]) | set(sb["tables"])):
        ta = sa["tables"].get(name)
        tb = sb["tables"].get(name)
        if ta == tb:
            continue
        if tb is None:
            diffs.append(f"table {name}: gone")
        elif ta is None:
            diffs.append(f"table {name}: appeared ({tb['rows']} rows)")
        else:
            diffs.append(f"table {name}: rows {ta['rows']} -> {tb['rows']}, digest changed")

    for name, ka in sorted(sa["governed"]["key_sets"].items()):
        kb = sb["governed"]["key_sets"].get(name, [])
        ids_a = {str(r.get("id")): r for r in ka}
        ids_b = {str(r.get("id")): r for r in kb}
        added = sorted(set(ids_b) - set(ids_a))
        removed = sorted(set(ids_a) - set(ids_b))
        mutated = sorted(k for k in set(ids_a) & set(ids_b) if ids_a[k] != ids_b[k])
        if added or removed or mutated:
            diffs.append(
                f"{name}: +{len(added)} -{len(removed)} ~{len(mutated)}"
                f" (added={added[:5]}{'...' if len(added) > 5 else ''},"
                f" removed={removed[:5]}{'...' if len(removed) > 5 else ''},"
                f" mutated={mutated[:5]}{'...' if len(mutated) > 5 else ''})"
            )

    if sa["governed"]["batch_objects"] != sb["governed"]["batch_objects"]:
        diffs.append("batch_objects: the first real publish batch changed")
    if sa["governed"]["duplicate_current_groups"] != sb["governed"]["duplicate_current_groups"]:
        diffs.append("duplicate_current_groups: changed")
    if sa["human_registry_sha256"] != sb["human_registry_sha256"]:
        diffs.append("human_registry_sha256: changed (Human Signature must never move)")
    if sa["batch_manifest_sha256"] != sb["batch_manifest_sha256"]:
        diffs.append("batch_manifest_sha256: changed")

    print(f"PRODUCTION_FINGERPRINT_A = {a['fingerprint']}")
    print(f"PRODUCTION_FINGERPRINT_B = {b['fingerprint']}")
    if not diffs:
        print("PRODUCTION_DB_SEMANTIC_DIFF = 0")
        print("PRODUCTION_DB_ROW_DIFF = 0")
        print("FINGERPRINT_COMPARE = IDENTICAL")
        return 0
    print("PRODUCTION_DB_SEMANTIC_DIFF > 0")
    for line in diffs:
        print(f"  - {line}")
    print("FINGERPRINT_COMPARE = DIFFERENT")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--out", default=None)
    ap.add_argument("--label", default=None)
    ap.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--replace", action="store_true")
    ap.add_argument("--compare", nargs=2, default=None, metavar=("A", "B"))
    args = ap.parse_args()

    if args.compare:
        return compare(Path(args.compare[0]), Path(args.compare[1]))

    if not args.out:
        print("需要 --out（或 --compare A B）", file=sys.stderr)
        return 2
    out_path = Path(args.out)
    if out_path.exists() and not args.replace:
        print(
            f"REFUSED — 指纹已存在且默认不可覆盖：{out_path}\n"
            "  指纹是「运行前/运行后」的证据，覆盖它就等于抹掉证据。确需重跑请加 --replace。",
            file=sys.stderr,
        )
        return 2
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        doc = build(
            args.db_name, registry_path=Path(args.registry), manifest_path=Path(args.manifest)
        )
    except DatabaseSafetyError as exc:
        print(f"DATABASE_SAFETY_REFUSED: {exc}", file=sys.stderr)
        return 3

    doc["label"] = args.label or out_path.stem
    payload = json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n"
    out_path.write_text(payload, encoding="utf-8")

    print(f"WROTE {out_path}")
    print(f"  database    = {doc['database']}  role = {doc['role']}")
    print(f"  alembic     = {doc['semantic']['identity']['alembic_head']}")
    print(f"  access_rule = {doc['totals'].get('access_rule')} rows total")
    print(f"  rule_excptn = {doc['totals'].get('rule_exception')} rows total")
    print(f"  candidates  = {doc['totals'].get('rule_candidate')}")
    print(f"  audit_log   = {doc['totals'].get('audit_log')}")
    dup_groups = doc["semantic"]["governed"]["duplicate_current_groups"]
    print(f"  duplicate_current_groups = {len(dup_groups)}")
    print(f"  fingerprint = {doc['fingerprint']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
