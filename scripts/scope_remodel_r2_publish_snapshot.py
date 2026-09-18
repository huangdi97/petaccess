"""Capture a before/after snapshot of the production state around a publish.

Why this file exists
--------------------
A publish must be provable *without re-running it*: the reviewer asks for the
fingerprint before and after, the new ids, the new audit rows, and — the part
that is easy to forget — proof that nothing **old** moved. This script writes
one JSON per invocation and can diff two of them.

It is deliberately read-only and does its own hashing: the fingerprint script
summarises tables, this one pins the individual historical objects that must
survive a publish untouched (frozen candidates, earlier published rules,
signed registers, monitor history).

Usage::

    python scripts/scope_remodel_r2_publish_snapshot.py --label before
    python scripts/scope_remodel_r2_publish_snapshot.py --label after
    python scripts/scope_remodel_r2_publish_snapshot.py --diff before after
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from dev_api_server import psycopg_url_for  # noqa: E402

DEFAULT_OUT_DIR = REPO / "artifacts" / "scope_remodel_r2_round5"

#: Candidates that are frozen: signed and never to be edited in place (ADR-029 §9).
FROZEN_CANDIDATES = ("305fa08c-1edd-4cc9-9b7e-554647e44b0a",)

#: Registers whose bytes must not change as a side effect of publishing.
FROZEN_FILES = (
    "docs/expansion/review_decisions_expansion_r1_wave01.json",
    "docs/expansion/review_decisions_scope_remodel_r2.json",
    "docs/expansion/review_decisions_scope_remodel_r2_carveout.json",
)

TABLES = (
    "access_rule",
    "rule_exception",
    "rule_candidate",
    "jurisdiction_exception",
    "source",
    "source_monitor",
    "audit_log",
    "place",
)


def _sha(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def capture(db_name: str) -> dict:
    import psycopg

    url = psycopg_url_for(db_name)
    if url is None:
        raise SystemExit(f"REFUSED — 无法解析 {db_name} 的 DATABASE_URL")

    out: dict = {
        "database": db_name,
        "captured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "counts": {},
        "frozen_candidates": {},
        "published_rules": {},
        "published_exceptions": {},
        "monitor_rows": {},
    }

    with psycopg.connect(url, connect_timeout=10) as conn, conn.cursor() as cur:
        for table in TABLES:
            cur.execute(f"SELECT count(*) FROM {table}")  # noqa: S608 - fixed list
            out["counts"][table] = cur.fetchone()[0]

        for cid in FROZEN_CANDIDATES:
            cur.execute("SELECT * FROM rule_candidate WHERE id::text = %s", (cid,))
            cols = [c.name for c in cur.description]
            rows = [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]
            out["frozen_candidates"][cid] = _sha(rows)

        # Every published object, keyed by id: a publish may only ADD keys here.
        cur.execute(
            """
            SELECT id, animal_scope, effect, rule_layer, mandatory_level, status,
                   source_id, zone_id, place_id, source_scope_exact,
                   subject_scope_normalized, normalization_type, normative_effect
              FROM access_rule
            """
        )
        cols = [c.name for c in cur.description]
        for row in cur.fetchall():
            d = dict(zip(cols, row, strict=True))
            out["published_rules"][str(d["id"])] = _sha(d)

        cur.execute(
            """
            SELECT id, rule_id, animal_scope, effect, status, source_id,
                   source_scope_exact, subject_scope_normalized,
                   normalization_type, normative_effect, holder_scope
              FROM rule_exception
            """
        )
        cols = [c.name for c in cur.description]
        for row in cur.fetchall():
            d = dict(zip(cols, row, strict=True))
            out["published_exceptions"][str(d["id"])] = _sha(d)

        # Freshness / monitor history must survive a publish untouched.
        cur.execute(
            """
            SELECT id, source_id, status, last_checked_at, last_changed_at,
                   content_hash, failure_count, next_check_at, updated_at
              FROM source_monitor
            """
        )
        cols = [c.name for c in cur.description]
        for row in cur.fetchall():
            d = dict(zip(cols, row, strict=True))
            out["monitor_rows"][str(d["id"])] = _sha(d)

    out["register_files"] = {
        p: _sha((REPO / p).read_bytes().hex()) for p in FROZEN_FILES if (REPO / p).exists()
    }
    return out


def diff(before: dict, after: dict) -> dict:
    result: dict = {"problems": []}

    for table, count in before["counts"].items():
        delta = after["counts"][table] - count
        result[f"delta_{table}"] = delta

    for cid, sha in before["frozen_candidates"].items():
        if after["frozen_candidates"].get(cid) != sha:
            result["problems"].append(f"冻结候选 {cid} 发生变化（FROZEN_CANDIDATE_MUTATED）")

    changed_rules = [
        rid
        for rid, sha in before["published_rules"].items()
        if after["published_rules"].get(rid) != sha
    ]
    result["published_rules_changed"] = changed_rules
    result["published_rules_new"] = sorted(
        set(after["published_rules"]) - set(before["published_rules"])
    )
    if changed_rules:
        result["problems"].append(f"已发布规则被重写：{changed_rules}")

    changed_exc = [
        eid
        for eid, sha in before["published_exceptions"].items()
        if after["published_exceptions"].get(eid) != sha
    ]
    result["published_exceptions_changed"] = changed_exc
    result["published_exceptions_new"] = sorted(
        set(after["published_exceptions"]) - set(before["published_exceptions"])
    )
    if changed_exc:
        result["problems"].append(f"已发布例外被重写：{changed_exc}")

    changed_mon = [
        mid
        for mid, sha in before["monitor_rows"].items()
        if after["monitor_rows"].get(mid) != sha
    ]
    result["monitor_rows_changed"] = changed_mon
    if changed_mon:
        result["problems"].append(f"source_monitor 历史被改动：{changed_mon}")

    changed_reg = [
        p for p, sha in before["register_files"].items() if after["register_files"].get(p) != sha
    ]
    result["register_files_changed"] = changed_reg
    if changed_reg:
        result["problems"].append(f"已签署登记表被改动：{changed_reg}")

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--label", default="snapshot")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--diff", nargs=2, metavar=("BEFORE", "AFTER"), default=None)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.diff:
        a = json.loads((out_dir / f"{args.diff[0]}.json").read_text(encoding="utf-8"))
        b = json.loads((out_dir / f"{args.diff[1]}.json").read_text(encoding="utf-8"))
        result = diff(a, b)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result["problems"] else 0

    snap = capture(args.db_name)
    path = out_dir / f"{args.label}.json"
    path.write_text(
        json.dumps(snap, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"WROTE {path}")
    print(f"  counts = {snap['counts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
