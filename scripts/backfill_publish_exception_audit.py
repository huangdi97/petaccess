"""Append the missing canonical RuleException publish audit for BATCH-01B (§16–§18).

What happened
-------------
The first real batch published five AccessRules and three RuleExceptions. The
five AccessRules carry ``candidate.publish``; the three RuleExceptions carry
**nothing** — neither ``candidate.publish_exception`` nor even
``rule_exception.create``. The governance chain is not missing, it is
*unnamed*: each of the three candidates does have its ``candidate.transition``
row written at the same instant, so the human decision and the publish moment
are both on record.

Why this is a backfill and not a re-publish
-------------------------------------------
§16 forbids re-running the publisher to manufacture audit rows: re-publishing
would mint new objects and move ``published_rule_id``, which is exactly what
§1 freezes. So this script *appends* rows and says so:

* ``detail.backfilled`` = ``true``
* ``detail.reason``     = ``CLI_AUDIT_EVENT_CONTRACT_RECONCILIATION``
* ``detail.original_publish_at`` = the true publish instant, read from
  ``rule_exception.created_at`` — never invented
* ``audit_log.created_at`` = *now*, because that is when this row was written

Scope (§17)
-----------
Only the three RuleExceptions of ``R2-FINAL-R3-BATCH-01B``. Nothing is guessed
about the rest of history: ``candidate.transition`` rows from earlier rounds are
reported, never reconciled, because there is no deterministic source that says
which publication each of them belongs to.

Usage::

    python scripts/backfill_publish_exception_audit.py --db-name petaccess \\
        --out artifacts/integrity_final_closure/BACKFILL_PLAN.json
    python scripts/backfill_publish_exception_audit.py --db-name petaccess \\
        --execute --confirm-database petaccess \\
        --backup artifacts/.../petaccess_before_backfill.dump \\
        --i-reviewed-the-dry-run artifacts/.../BACKFILL_PLAN.json
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

from app.core.audit_events import (  # noqa: E402
    AUDIT_BACKFILL_REASON,
    BACKFILL_FLAG,
    ORIGINAL_PUBLISH_AT,
    AuditEvent,
)
from app.db.safety import DatabaseSafetyError, guard_for_psycopg  # noqa: E402

DEFAULT_REGISTRY = ROOT / "docs" / "reality_audit" / "review_decisions_r2_final.json"
DEFAULT_MANIFEST = ROOT / "docs" / "governance" / "publish_batches" / "R2_FINAL_R3_BATCH_01B.json"

#: Written into ``detail`` so a reader can tell who decided and who executed,
#: which §15 requires to stay separate.
REVIEWER = "huangdi97"
REVISION = "R2-FINAL-R3"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _iso(value: Any) -> Any:
    return value.isoformat() if isinstance(value, datetime) else value


def load_batch_carve_outs(registry_path: Path, manifest_path: Path) -> list[dict[str, Any]]:
    """The batch's carve-out candidates, each with its base rule label.

    ``carve_out_of`` in the signed register is the deterministic source for
    "this candidate is an exception, not a rule of its own" (§17: no guessing).
    A candidate row in the database cannot answer that question: publishing an
    exception also stamps ``published_rule_id`` with the *base* rule, so the
    base's own candidate and its carve-outs are indistinguishable by id alone.
    """
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = registry.get("rows", [])
    by_rule_id = {str(r["rule_id"]): r for r in rows if r.get("rule_id")}
    labels = [str(c) for c in manifest.get("candidate_rule_ids", [])]
    missing = [c for c in labels if c not in by_rule_id]
    if missing:
        raise SystemExit(f"清单里的 rule_id 在登记表中找不到：{missing}")
    return [
        {
            "rule_id": label,
            "candidate_id": str(by_rule_id[label]["candidate_id"]),
            "carve_out_of": [str(x) for x in (by_rule_id[label].get("carve_out_of") or [])],
        }
        for label in labels
        if by_rule_id[label].get("carve_out_of")
    ]


def discover(cur: Any, candidate_ids: list[str]) -> list[dict[str, Any]]:
    """The batch's RuleExceptions that have no canonical publish audit.

    A carve-out candidate is one whose ``published_rule_id`` points at a base
    rule that carries a RuleException. The exception is matched through the base
    rule, which is the only link the schema offers (a candidate row has no
    exception pointer of its own).
    """
    cur.execute(
        """
        select c.id as candidate_id,
               c.published_rule_id as base_rule_id,
               e.id as rule_exception_id,
               e.animal_scope, e.effect, e.source_id, e.status,
               e.source_scope_exact, e.subject_scope_normalized,
               e.normalization_type, e.normative_effect, e.holder_scope,
               e.created_at as published_at
        from rule_candidate c
        join rule_exception e on e.rule_id = c.published_rule_id
        where c.id = any(%s)
        order by e.created_at
        """,
        (candidate_ids,),
    )
    cols = [d.name for d in cur.description]
    rows = [dict(zip(cols, r, strict=False)) for r in cur.fetchall()]

    out: list[dict[str, Any]] = []
    for row in rows:
        cur.execute(
            "select count(*) from audit_log where action = %s"
            " and after_state->>'candidate_id' = %s",
            (AuditEvent.CANDIDATE_PUBLISH_EXCEPTION.value, row["candidate_id"]),
        )
        row["existing_publish_exception_audit"] = int(cur.fetchone()[0])
        cur.execute(
            "select count(*) from audit_log where action = %s and target_id = %s",
            (AuditEvent.CANDIDATE_TRANSITION.value, row["candidate_id"]),
        )
        row["existing_transition_audit"] = int(cur.fetchone()[0])
        cur.execute(
            "select id, created_at from audit_log where action = %s and target_id = %s"
            " order by created_at desc limit 1",
            (AuditEvent.CANDIDATE_TRANSITION.value, row["candidate_id"]),
        )
        latest = cur.fetchone()
        row["original_transition_audit_id"] = latest[0] if latest else None
        row["needs_backfill"] = row["existing_publish_exception_audit"] == 0
        out.append(row)
    return out


def render(rows: list[dict[str, Any]]) -> str:
    lines = ["AUDIT_BACKFILL_PLAN"]
    for r in rows:
        lines.append(
            f"  candidate {r['candidate_id'][:8]}  base {str(r['base_rule_id'])[:8]}"
            f"  exception {r['rule_exception_id'][:8]}  {r['animal_scope']}/{r['effect']}"
            f"  transition_audit={r['existing_transition_audit']}"
            f"  publish_exception_audit={r['existing_publish_exception_audit']}"
            f"  -> {'BACKFILL' if r['needs_backfill'] else 'ALREADY_PRESENT'}"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--out", default=None)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--confirm-database", default=None)
    ap.add_argument("--backup", default=None)
    ap.add_argument("--i-reviewed-the-dry-run", default=None)
    ap.add_argument("--replace", action="store_true")
    args = ap.parse_args()

    out_path = Path(args.out) if args.out else None
    if out_path and out_path.exists() and not args.replace:
        print(
            f"REFUSED — 计划已存在且默认不可覆盖：{out_path}",
            file=sys.stderr,
        )
        return 2

    carve_outs = load_batch_carve_outs(Path(args.registry), Path(args.manifest))
    candidate_ids = [c["candidate_id"] for c in carve_outs]
    url = psycopg_url_for(args.db_name)
    if not url:
        print("无法解析数据库 URL", file=sys.stderr)
        return 3

    doc: dict[str, Any] = {
        "at": _now(),
        "database": args.db_name,
        "revision": REVISION,
        "reviewer": REVIEWER,
        "batch_id": json.loads(Path(args.manifest).read_text(encoding="utf-8")).get("batch_id"),
        "mode": "execute" if args.execute else "dry-run",
        "carve_outs": carve_outs,
        "candidate_ids": candidate_ids,
    }

    try:
        with psycopg.connect(url) as conn:
            guard = guard_for_psycopg(conn)
            doc["role"] = guard.role.value
            if args.execute:
                # Same bar as a governed cleanup: a real backup and a reviewed
                # plan must already exist on disk before a production write.
                guard.assert_production_cleanup_allowed(
                    "audit reconciliation backfill",
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
                rows = discover(cur, candidate_ids)
            doc["rows"] = [{k: _iso(v) for k, v in r.items()} for r in rows]
            doc["backfill_count"] = sum(1 for r in rows if r["needs_backfill"])

            print(render(rows))
            print(f"AUDIT_BACKFILL_COUNT = {doc['backfill_count']}")
            print("AUDIT_HISTORY_DELETED = 0")

            if not args.execute:
                if out_path:
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(
                        json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n",
                        encoding="utf-8",
                    )
                    print(f"WROTE {out_path}")
                return 0

            inserted = 0
            with conn.cursor() as cur:
                for r in rows:
                    if not r["needs_backfill"]:
                        continue
                    after_state = {
                        "candidate_id": r["candidate_id"],
                        "base_rule_id": r["base_rule_id"],
                        "rule_exception_id": r["rule_exception_id"],
                        "animal_scope": r["animal_scope"],
                        "effect": r["effect"],
                        "source_scope_exact": r["source_scope_exact"],
                        "subject_scope_normalized": r["subject_scope_normalized"],
                        "normalization_type": r["normalization_type"],
                        "normative_effect": r["normative_effect"],
                        "holder_scope": r["holder_scope"],
                    }
                    detail = {
                        BACKFILL_FLAG: True,
                        "reason": AUDIT_BACKFILL_REASON,
                        ORIGINAL_PUBLISH_AT: _iso(r["published_at"]),
                        "original_candidate_transition_audit_id": r["original_transition_audit_id"],
                        "rule_exception_id": r["rule_exception_id"],
                        "base_rule_id": r["base_rule_id"],
                        "batch_id": doc["batch_id"],
                        "revision": REVISION,
                        "reviewer": REVIEWER,
                    }
                    cur.execute(
                        """
                        insert into audit_log
                          (id, actor_user_id, actor_role, action, target_type, target_id,
                           before_state, after_state, detail, created_at)
                        values
                          (gen_random_uuid()::text, %s, %s, %s, %s, %s,
                           %s::jsonb, %s::jsonb, %s::jsonb, now())
                        """,
                        (
                            None,
                            "governance-reconciliation",
                            AuditEvent.CANDIDATE_PUBLISH_EXCEPTION.value,
                            "rule_exception",
                            r["rule_exception_id"],
                            json.dumps({"published": False}),
                            json.dumps(after_state),
                            json.dumps(detail),
                        ),
                    )
                    inserted += 1
            conn.commit()
    except DatabaseSafetyError as exc:
        print(f"DATABASE_SAFETY_REFUSED: {exc}", file=sys.stderr)
        return 3

    doc["inserted"] = inserted
    print(f"AUDIT_BACKFILL_INSERTED = {inserted}")
    print("AUDIT_BACKFILL_MODE = execute")
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        print(f"WROTE {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
