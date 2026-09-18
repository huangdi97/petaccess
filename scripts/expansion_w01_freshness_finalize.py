"""WAVE_01 freshness finalization (spec §34-§35, §80).

Goal: 100% of sources carry ``freshness_policy_id`` + ``last_verified_at`` +
``review_due_at``. The three aborted ingest runs also created four duplicate
copies of every freshness policy; this script consolidates onto one canonical
policy per ``source_type`` and removes the unused duplicates (governed cleanup).

``review_due_at`` means "needs re-verification", never "invalid" (§35).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import timedelta
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
BACKUP = REPO / "artifacts" / "expansion_w01" / "backup" / "petaccess_pre_wave01.dump"
PLAN = REPO / "artifacts" / "expansion_w01" / "wave01_freshness_plan.json"

INTERVAL_BY_TYPE = {
    "statute_or_regulation": 365,
    "government_service": 180,
    "official_operator_policy": 90,
    "onsite_signage": 90,
    "certified_verifier": 90,
    "external_web_reference": 180,
    "ordinary_user": 180,
    "imported_dataset": 365,
}


def snapshot(session: Session) -> dict:
    total = session.execute(text("SELECT count(*) FROM source")).scalar()
    assigned = session.execute(
        text("SELECT count(*) FROM source WHERE freshness_policy_id IS NOT NULL")
    ).scalar()
    verified = session.execute(
        text("SELECT count(*) FROM source WHERE last_verified_at IS NOT NULL")
    ).scalar()
    due = session.execute(
        text("SELECT count(*) FROM source WHERE review_due_at IS NOT NULL")
    ).scalar()
    types = [r[0] for r in session.execute(text("SELECT DISTINCT source_type FROM source"))]
    policies = [
        dict(r._mapping)
        for r in session.execute(
            text(
                "SELECT id, name, review_interval_days, created_at FROM freshness_policy "
                "ORDER BY created_at, id"
            )
        )
    ]
    return {
        "sources": total,
        "with_policy": assigned,
        "with_last_verified": verified,
        "with_review_due": due,
        "source_types": types,
        "policies": len(policies),
    }


def build_plan(session: Session) -> dict:
    types = [r[0] for r in session.execute(text("SELECT DISTINCT source_type FROM source"))]
    policies = [
        dict(r._mapping)
        for r in session.execute(
            text(
                "SELECT id, name, review_interval_days, created_at FROM freshness_policy "
                "ORDER BY created_at, id"
            )
        )
    ]

    canonical: dict[str, str] = {}
    for t in types:
        want = INTERVAL_BY_TYPE.get(t, 180)
        cands = [p for p in policies if p["review_interval_days"] == want]
        if cands:
            canonical[t] = cands[0]["id"]
        else:
            canonical[t] = None  # to be created

    dup_ids = [
        p["id"]
        for p in policies
        if p["id"] not in set(canonical.values()) and (p["name"].startswith("wave01-"))
    ]
    used = {
        r[0]
        for r in session.execute(
            text(
                "SELECT DISTINCT freshness_policy_id FROM source "
                "WHERE freshness_policy_id IS NOT NULL"
            )
        )
    }

    rows = [
        dict(r._mapping)
        for r in session.execute(
            text(
                "SELECT id, source_type, collected_at, observed_at, published_at, "
                "last_verified_at, freshness_policy_id FROM source"
            )
        )
    ]
    updates = []
    for r in rows:
        new_pid = canonical.get(r["source_type"])
        base = r["last_verified_at"] or r["observed_at"] or r["published_at"] or r["collected_at"]
        due = base + timedelta(days=INTERVAL_BY_TYPE.get(r["source_type"], 180))
        updates.append(
            {
                "source_id": r["id"],
                "source_type": r["source_type"],
                "from_policy": r["freshness_policy_id"],
                "to_policy": new_pid,
                "last_verified_at": str(base),
                "review_due_at": str(due),
            }
        )
    return {
        "operation": "wave01_freshness_finalize",
        "expansion_run_id": RUN_ID,
        "canonical_policy_by_source_type": dict(canonical),
        "create_policies_for": [t for t, v in canonical.items() if v is None],
        "sources_total": len(rows),
        "sources_to_update": len(updates),
        "delete_unused_duplicate_policies": [p for p in dup_ids if p not in used],
        "delete_policies_still_in_use": [p for p in dup_ids if p in used],
        "sample_updates": updates[:5],
        "note": "review_due_at = 需重新核验的时间点，不等于规则失效（§35）",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--plan", default=str(PLAN))
    args = ap.parse_args()

    from app.db.safety import guard_with_probe

    engine = get_engine()
    guard = guard_with_probe(engine)
    print(f"[db] role={guard.role.value} db={guard.database_name}", file=sys.stderr)

    with Session(engine) as s:
        before = snapshot(s)
        plan = build_plan(s)
        plan["before"] = before
        if not args.execute:
            Path(args.plan).parent.mkdir(parents=True, exist_ok=True)
            Path(args.plan).write_text(
                json.dumps(plan, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
            )
            print(json.dumps(plan, ensure_ascii=False, indent=2, default=str))
            return 0

        guard.assert_production_cleanup_allowed(
            "wave01_freshness_finalize", backup_path=BACKUP, reviewed_plan_path=args.plan
        )

        # 1. create any missing canonical policy
        for t, pid in list(plan["canonical_policy_by_source_type"].items()):
            if pid is None:
                days = INTERVAL_BY_TYPE.get(t, 180)
                row = s.execute(
                    text(
                        "INSERT INTO freshness_policy (id, name, review_interval_days, "
                        "description, created_at, updated_at) VALUES "
                        "(gen_random_uuid()::text, :name, :days, :desc, now(), now()) "
                        "RETURNING id"
                    ),
                    {
                        "name": f"wave01-{t}-{days}d",
                        "days": days,
                        "desc": f"Wave01 默认复核周期：{t} 每 {days} 天",
                    },
                ).fetchone()
                plan["canonical_policy_by_source_type"][t] = row[0]

        # 2. assign every source
        updated = 0
        for t, pid in plan["canonical_policy_by_source_type"].items():
            days = INTERVAL_BY_TYPE.get(t, 180)
            base = "COALESCE(last_verified_at, observed_at, published_at, collected_at)"
            res = s.execute(
                text(
                    "UPDATE source SET freshness_policy_id = :pid, "
                    f"last_verified_at = {base}, "
                    f"review_due_at = {base} + (:days || ' days')::interval "
                    "WHERE source_type = :t"
                ),
                {"pid": pid, "days": str(days), "t": t},
            )
            updated += res.rowcount or 0

        # 3. drop duplicate policies no source references.
        #    Recomputed AFTER step 2: the plan's used-set was captured before the
        #    re-assignment, so policies listed there may now be orphaned.
        canonical_ids = set(plan["canonical_policy_by_source_type"].values())
        still_used = {
            r[0]
            for r in s.execute(
                text(
                    "SELECT DISTINCT freshness_policy_id FROM source "
                    "WHERE freshness_policy_id IS NOT NULL"
                )
            )
        }
        removable = [
            r[0]
            for r in s.execute(text("SELECT id FROM freshness_policy WHERE name LIKE 'wave01-%'"))
        ]
        to_delete = [p for p in removable if p not in canonical_ids and p not in still_used]
        blocked = [p for p in removable if p not in canonical_ids and p in still_used]
        removed = 0
        for pid in to_delete:
            res = s.execute(text("DELETE FROM freshness_policy WHERE id = :id"), {"id": pid})
            removed += res.rowcount or 0
        s.commit()
        after = snapshot(s)
        print(
            json.dumps(
                {
                    "updated_sources": updated,
                    "removed_duplicate_policies": removed,
                    "blocked_still_in_use": blocked,
                    "before": before,
                    "after": after,
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
