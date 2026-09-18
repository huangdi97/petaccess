"""WAVE_01 orphan source cleanup (governed production cleanup, DB safety §27).

Wave-01 collection produced one ``source`` row that never received a
``source_artifact`` and therefore never produced an ``evidence_bundle`` or a
claim. It is referenced by nothing:

    source 8cdcbc8d…  上海市青浦区人民政府《青浦蟠龙天地荣获2023中国城市更新优秀案例…》
    notes = "capture_method=search_snippet; needs_verification=True"

A source that supports no claim is not evidence — it is a dangling lead. Keeping
it would (a) trip the ``ORPHAN_SOURCE`` integrity check and (b) invite a later
operator to treat an unverified search snippet as if it were captured evidence.
The place it was collected for (蟠龙天地) is already covered by a properly
captured operator source ``4785e43f…``, so nothing is lost.

Scope guard (stricter than the dedup cleanup, because ``source`` has no
``expansion_run_id`` column):
  1. only ids explicitly listed in the reviewed dry-run plan,
  2. only rows created on/after 2026-09-18 (Wave-01 window),
  3. only rows with **zero** references from evidence_bundle / source_artifact /
     rule_candidate / observation_candidate / access_rule / rule_exception,
  4. re-verified immediately before the DELETE.

A physical backup and a reviewed dry-run plan must exist on disk before
``--execute`` will run (``assert_production_cleanup_allowed``).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
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

BACKUP = REPO / "artifacts" / "expansion_w01" / "backup" / "petaccess_pre_wave01.dump"
PLAN = REPO / "artifacts" / "expansion_w01" / "wave01_orphan_source_plan.json"
WAVE01_SINCE = "2026-09-18T00:00:00+00:00"

# Every table that can point at a source. A row is only removable when all of
# these return zero — this is the same predicate the integrity scanner uses.
REF_CHECKS = (
    ("evidence_bundle", "source_id"),
    ("source_artifact", "source_id"),
    ("rule_candidate", "source_id"),
    ("observation_candidate", "source_id"),
    ("access_rule", "source_id"),
    ("rule_exception", "source_id"),
)


def orphan_ids(session: Session) -> list[str]:
    rows = [
        r[0]
        for r in session.execute(
            text("SELECT id FROM source WHERE created_at >= :since ORDER BY created_at"),
            {"since": WAVE01_SINCE},
        )
    ]
    out = []
    for sid in rows:
        refs = {}
        for table, col in REF_CHECKS:
            n = session.execute(
                text(f"SELECT count(*) FROM {table} WHERE {col} = :sid"),  # noqa: S608
                {"sid": sid},
            ).scalar_one()
            if n:
                refs[table] = n
        if not refs:
            out.append(str(sid))
    return out


def describe(session: Session, ids: list[str]) -> list[dict]:
    if not ids:
        return []
    rows = session.execute(
        text(
            "SELECT id, source_type, issuer, source_url, notes, created_at "
            "FROM source WHERE id = ANY(:ids) ORDER BY created_at"
        ),
        {"ids": ids},
    )
    out = []
    for r in rows:
        d = dict(r._mapping)
        d["monitors"] = session.execute(
            text("SELECT count(*) FROM source_monitor WHERE source_id = :sid"),
            {"sid": str(d["id"])},
        ).scalar_one()
        out.append(d)
    return out


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
        ids = orphan_ids(s)
        detail = describe(s, ids)
        plan = {
            "operation": "wave01_orphan_source_cleanup",
            "expansion_run_id": "EXP-R1-W01-20260918",
            "reason": "Wave-01 采集到但从未产出 artifact/证据束/主张的悬空来源；"
            "保留会让未核验的 search snippet 被误当作已抓取证据",
            "scope_guard": "仅删除清单内、Wave-01 新建、且 6 张引用表全为 0 的 source",
            "reference_tables_checked": [t for t, _ in REF_CHECKS],
            "count": len(ids),
            "sources": [
                {
                    "id": str(d["id"]),
                    "source_type": d["source_type"],
                    "issuer": d["issuer"],
                    "source_url": d["source_url"],
                    "notes": d["notes"],
                    "created_at": str(d["created_at"]),
                    "attached_monitors": d["monitors"],
                }
                for d in detail
            ],
        }
        if not args.execute:
            Path(args.plan).parent.mkdir(parents=True, exist_ok=True)
            Path(args.plan).write_text(
                json.dumps(plan, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
            )
            plan["plan_written_to"] = str(args.plan)
            print(json.dumps(plan, ensure_ascii=False, indent=2, default=str))
            return 0

        guard.assert_production_cleanup_allowed(
            "wave01_orphan_source_cleanup", backup_path=BACKUP, reviewed_plan_path=args.plan
        )
        reviewed = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        allowed = {r["id"] for r in reviewed.get("sources", [])}

        # re-verify: still in the reviewed plan AND still unreferenced
        current = set(orphan_ids(s))
        targets = sorted((set(ids) & allowed) & current)
        refused = sorted(set(ids) - current)
        if refused:
            print(f"REFUSED (now referenced): {refused}", file=sys.stderr)
            return 4

        removed_monitors = 0
        for sid in targets:
            removed_monitors += (
                s.execute(
                    text("DELETE FROM source_monitor WHERE source_id = :sid"), {"sid": sid}
                ).rowcount
                or 0
            )
        removed_sources = 0
        for sid in targets:
            removed_sources += (
                s.execute(text("DELETE FROM source WHERE id = :sid"), {"sid": sid}).rowcount or 0
            )
        s.commit()

        print(
            json.dumps(
                {
                    "removed_sources": removed_sources,
                    "removed_monitors": removed_monitors,
                    "deleted_ids": targets,
                    "remaining_orphan_sources": len(orphan_ids(s)),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
