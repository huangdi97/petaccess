"""Rebuild the WAVE_01 manifest from the database (read-only w.r.t. evidence).

The duplicate cleanup deleted rows that the ingest manifest still pointed at.
Re-deriving the manifest from the surviving rows keeps it truthful without
re-running the ingest (which would re-create what was just deduplicated).
"""

from __future__ import annotations

import hashlib
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

from app.db.session import get_engine  # noqa: E402

RUN_ID = "EXP-R1-W01-20260918"
EVIDENCE = REPO / "docs" / "expansion" / "expansion_r1_wave01_evidence.json"
MANIFEST = REPO / "docs" / "expansion" / "expansion_r1_wave01_manifest.json"


def _dedup_key(run_id: str, place_key: str, rule_id: str) -> str:
    return hashlib.sha256(f"{run_id}|{place_key}|{rule_id}".encode()).hexdigest()


def main() -> int:
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}

    engine = get_engine()
    with Session(engine) as s:
        cand_rows = {
            r["dedup_key"]: r["id"]
            for r in (
                dict(x._mapping)
                for x in s.execute(
                    text(
                        "SELECT id, dedup_key, evidence_bundle_id FROM rule_candidate "
                        "WHERE expansion_run_id = :run"
                    ),
                    {"run": RUN_ID},
                )
            )
        }
        bundle_art = {
            r["id"]: r["artifact_id"]
            for r in (
                dict(x._mapping)
                for x in s.execute(
                    text(
                        "SELECT id, artifact_id FROM evidence_bundle WHERE expansion_run_id = :run"
                    ),
                    {"run": RUN_ID},
                )
            )
        }
        cand_bundle = {
            r["id"]: r["evidence_bundle_id"]
            for r in (
                dict(x._mapping)
                for x in s.execute(
                    text(
                        "SELECT id, evidence_bundle_id FROM rule_candidate "
                        "WHERE expansion_run_id = :run"
                    ),
                    {"run": RUN_ID},
                )
            )
        }
        jobs = [
            dict(x._mapping)
            for x in s.execute(
                text(
                    "SELECT id, state, created_at FROM data_source_job "
                    "WHERE expansion_run_id = :run ORDER BY created_at"
                ),
                {"run": RUN_ID},
            )
        ]
        monitors = [
            dict(x._mapping)
            for x in s.execute(
                text("SELECT id, source_id, url FROM source_monitor WHERE expansion_run_id = :run"),
                {"run": RUN_ID},
            )
        ]
        policies = [
            dict(x._mapping) for x in s.execute(text("SELECT id, name FROM freshness_policy"))
        ]

    manifest = {k: dict(v) for k, v in old.items()}

    rule_candidates: dict[str, str] = {}
    bundles: dict[str, str] = {}
    artifacts: dict[str, str] = {}
    missing: list[str] = []

    for pdata in ev["places"]:
        pkey = pdata["key"]
        for r in pdata["rules"]:
            dk = _dedup_key(RUN_ID, pkey, r["rule_id"])
            cid = cand_rows.get(dk)
            if not cid:
                missing.append(f"{pkey}:{r['rule_id']}")
                continue
            ckey = f"{pkey}:{r['rule_id']}"
            rule_candidates[ckey] = cid
            bid = cand_bundle.get(cid)
            if bid:
                src_key = r["source_key"]
                bundles[f"{src_key}:bundle:{r['fragment']}"] = bid
                aid = bundle_art.get(bid)
                if aid:
                    artifacts[f"{src_key}:artifact"] = aid

    manifest["rule_candidates"] = rule_candidates
    manifest["bundles"] = bundles
    manifest["artifacts"] = artifacts
    manifest["monitors"] = {f"monitor:{m['source_id']}:{m['url']}": m["id"] for m in monitors}
    manifest["freshness_policies"] = {f"policy:{p['name']}": p["id"] for p in policies}
    manifest["run"] = {
        "expansion_run_id": RUN_ID,
        "review_revision": ev["review_revision"],
        "data_source_job_ids": [j["id"] for j in jobs],
        "completed_job_id": next((j["id"] for j in jobs if j.get("state") == "COMPLETED"), None),
        "aborted_job_ids": [j["id"] for j in jobs if j.get("state") != "COMPLETED"],
    }
    manifest["_rebuild"] = {
        "method": "derived from surviving DB rows by expansion_run_id + dedup_key",
        "missing_candidates": missing,
    }

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "manifest": str(MANIFEST),
                "rule_candidates": len(rule_candidates),
                "bundles": len(bundles),
                "artifacts": len(artifacts),
                "monitors": len(monitors),
                "jobs": [{"id": j["id"], "state": j.get("state")} for j in jobs],
                "missing_candidates": missing,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
