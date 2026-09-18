"""WAVE_01 duplicate cleanup (governed production cleanup, DB safety §27).

The Wave-01 ingest ran three times. The first two aborted *before* the manifest
was written, so the third run re-created artifacts / bundles / candidates that
already existed. This script removes the duplicates only — it never touches a
row that a surviving row depends on, and it never touches pre-Wave-01 data.

Selection rule (deterministic, reviewable):
  1. rule_candidate    : per ``dedup_key`` keep the oldest row, delete the rest
  2. evidence_bundle   : delete Wave-01 bundles no surviving candidate cites
  3. source_artifact   : delete Wave-01 artifacts no surviving bundle cites
  4. source_monitor    : per ``source_id`` keep the oldest, delete the rest

Only rows carrying ``expansion_run_id = EXP-R1-W01-20260918`` are eligible.
A physical backup and a reviewed dry-run plan must exist on disk before
``--execute`` will run (``assert_production_cleanup_allowed``).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
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

RUN_ID = "EXP-R1-W01-20260918"
BACKUP = REPO / "artifacts" / "expansion_w01" / "backup" / "petaccess_pre_wave01.dump"
PLAN = REPO / "artifacts" / "expansion_w01" / "wave01_dedup_cleanup_plan.json"

SEL_CAND = """
SELECT id, dedup_key, created_at FROM rule_candidate
WHERE expansion_run_id = :run ORDER BY created_at, id
"""
SEL_BUNDLE = """
SELECT id, artifact_id, quoted_fragment, created_at FROM evidence_bundle
WHERE expansion_run_id = :run ORDER BY created_at, id
"""
SEL_ART = """
SELECT id, source_id, created_at FROM source_artifact
WHERE expansion_run_id = :run ORDER BY created_at, id
"""
SEL_MON = """
SELECT id, source_id, url, created_at FROM source_monitor
WHERE expansion_run_id = :run ORDER BY created_at, id
"""


def build_plan(session: Session) -> dict:
    cands = [dict(r._mapping) for r in session.execute(text(SEL_CAND), {"run": RUN_ID})]
    bundles = [dict(r._mapping) for r in session.execute(text(SEL_BUNDLE), {"run": RUN_ID})]
    arts = [dict(r._mapping) for r in session.execute(text(SEL_ART), {"run": RUN_ID})]
    mons = [dict(r._mapping) for r in session.execute(text(SEL_MON), {"run": RUN_ID})]

    # 1. candidates: keep oldest per dedup_key
    by_key: dict[str, list[str]] = defaultdict(list)
    for c in cands:
        by_key[c["dedup_key"]].append(c["id"])
    keep_cand = {v[0] for v in by_key.values()}
    del_cand = sorted({c["id"] for c in cands} - keep_cand)

    # 2. bundles: keep only the ones the *surviving* candidates cite
    keep_ids = list(keep_cand)
    cited: set = set()
    if keep_ids:
        cited |= {
            row[0]
            for row in session.execute(
                text(
                    "SELECT DISTINCT evidence_bundle_id FROM rule_candidate "
                    "WHERE id = ANY(:ids) AND evidence_bundle_id IS NOT NULL"
                ),
                {"ids": keep_ids},
            )
        }
    cited |= {
        row[0]
        for row in session.execute(
            text(
                "SELECT DISTINCT evidence_bundle_id FROM observation_candidate "
                "WHERE expansion_run_id = :run AND evidence_bundle_id IS NOT NULL"
            ),
            {"run": RUN_ID},
        )
    }
    keep_bundle = {b["id"] for b in bundles if b["id"] in cited}
    del_bundle = sorted({b["id"] for b in bundles} - keep_bundle)

    # 3. artifacts: keep the ones surviving bundles cite
    cited_art = {b["artifact_id"] for b in bundles if b["id"] in keep_bundle}
    keep_art = {a["id"] for a in arts if a["id"] in cited_art}
    del_art = sorted({a["id"] for a in arts} - keep_art)

    # 4. monitors: keep oldest per source_id
    by_src: dict[str, list[str]] = defaultdict(list)
    for m in mons:
        by_src[str(m["source_id"])].append(m["id"])
    keep_mon = {v[0] for v in by_src.values()}
    del_mon = sorted({m["id"] for m in mons} - keep_mon)

    return {
        "operation": "wave01_dedup_cleanup",
        "expansion_run_id": RUN_ID,
        "reason": "注入脚本前两次在写 manifest 前中断，第三次重跑产生重复",
        "before": {
            "rule_candidate": len(cands),
            "evidence_bundle": len(bundles),
            "source_artifact": len(arts),
            "source_monitor": len(mons),
        },
        "delete": {
            "rule_candidate": del_cand,
            "evidence_bundle": del_bundle,
            "source_artifact": del_art,
            "source_monitor": del_mon,
        },
        "keep": {
            "rule_candidate": len(keep_cand),
            "evidence_bundle": len(keep_bundle),
            "source_artifact": len(keep_art),
            "source_monitor": len(keep_mon),
        },
        "delete_counts": {
            k: len(v)
            for k, v in {
                "rule_candidate": del_cand,
                "evidence_bundle": del_bundle,
                "source_artifact": del_art,
                "source_monitor": del_mon,
            }.items()
        },
        "scope_guard": "仅删除 expansion_run_id = EXP-R1-W01-20260918 且无存活行引用的记录",
    }


def delete_ids(session: Session, table: str, ids: list[str]) -> int:
    if not ids:
        return 0
    res = session.execute(
        text(f"DELETE FROM {table} WHERE id = ANY(:ids) AND expansion_run_id = :run"),
        {"ids": ids, "run": RUN_ID},
    )
    return res.rowcount or 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--plan", default=str(PLAN))
    args = ap.parse_args()

    from app.db.safety import guard_with_probe
    from app.db.session import get_engine

    engine = get_engine()
    guard = guard_with_probe(engine)
    print(f"[db] role={guard.role.value} db={guard.database_name}", file=sys.stderr)

    with Session(engine) as s:
        plan = build_plan(s)
        if not args.execute:
            Path(args.plan).parent.mkdir(parents=True, exist_ok=True)
            Path(args.plan).write_text(
                json.dumps(plan, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
            )
            plan["plan_written_to"] = str(args.plan)
            print(json.dumps(plan, ensure_ascii=False, indent=2, default=str))
            return 0

        # governed gate: backup + reviewed plan must already exist on disk
        guard.assert_production_cleanup_allowed(
            "wave01_dedup_cleanup", backup_path=BACKUP, reviewed_plan_path=args.plan
        )
        removed = {}
        for table in ("rule_candidate", "evidence_bundle", "source_artifact"):
            removed[table] = delete_ids(s, table, plan["delete"][table])
        # source_monitor has no per-row delete guard issue; same scope guard applies
        removed["source_monitor"] = delete_ids(
            s, "source_monitor", plan["delete"]["source_monitor"]
        )
        s.commit()

        after = build_plan(s)
        out = {
            "removed": removed,
            "after": after["before"],
            "residual_duplicates": after["delete_counts"],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return 0


if __name__ == "__main__":
    sys.exit(main())
