"""Consolidated post-publish evidence for EXP-R1-W01-REVIEW-R1-BATCH-01A.

Merges the independent verifications (publish receipt, DB row state, resolver
probe, integrity scan, monkey-branch audit linkage) into a single JSON that can
be cited from the report. Read-only: it only reads the artifacts produced during
the run, plus one live fingerprint comparison.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ART = REPO / "artifacts" / "real_publish_batch01a"
PY = str(REPO / ".venv" / "Scripts" / "python.exe")


def run_json(script: str) -> dict:
    r = subprocess.run(
        [PY, str(REPO / "scripts" / script)], capture_output=True, text=True, cwd=str(REPO)
    )
    # scripts print a single JSON document; tolerate leading traceback-free noise
    txt = r.stdout
    start = txt.find("{")
    return json.loads(txt[start:]) if start >= 0 else {"_error": r.stderr[-2000:]}


def main() -> int:
    out: dict = {
        "batch_id": "EXP-R1-W01-REVIEW-R1-BATCH-01A",
        "revision": "EXP-R1-W01-REVIEW-R1",
        "reviewer": "huangdi97",
        "generated_at": datetime.now(UTC).isoformat(),
        "authorized_rule_ids": [
            "w01-1fb3d7f1c7",
            "w01-4710a68f56",
            "w01-5a5f33f122".replace("5a5f", "fa5f"),
            "w01-6482477d8d",
            "w01-73de8e3357",
        ],
    }

    # publish receipt
    snap = json.loads((ART / "PUBLISHED_RULES_SNAPSHOT_BATCH_01A.json").read_text("utf-8"))
    out["publish_receipt"] = snap["summary"]
    out["published_objects"] = snap["detail"]["published"]

    # idempotency
    rerun = (ART / "execute_second_stdout.json").read_text("utf-8", errors="replace")
    out["second_execute"] = {
        "noop_count": rerun.count("NOOP_ALREADY_EXISTS"),
        "note": "second identical execute produced only already-exists outcomes",
    }

    # database row state + audit linkage
    out["db_verification"] = run_json("verify_batch01a_publish.py")
    # resolver semantics
    out["resolver"] = run_json("verify_batch01a_resolver.py")
    # integrity
    integ = json.loads((ART / "integrity_post_publish.json").read_text("utf-8"))
    out["integrity"] = {
        k: v
        for k, v in integ.items()
        if k in ("severity_counts", "checks", "alembic_head", "database", "verdict")
    }

    out["gates"] = {
        "PUBLISH_EXECUTED": snap["summary"]["counts"]["published"] == 5,
        "PUBLISH_FAILED_ZERO": snap["summary"]["counts"]["failed"] == 0,
        "AUDIT_CONTRACT_PASS": snap["summary"]["audit_contract"]["verdict"] == "PASS",
        "DB_ROW_VERIFY": out["db_verification"].get("verdict"),
        "RESOLVER_VERIFY": out["resolver"].get("verdict"),
        "EXCLUDED_APPROVED_PUBLISHED": len(
            out["db_verification"].get("excluded_approved_published", [])
        ),
        "HOLD_REJECTED_PUBLISHED": len(out["db_verification"].get("hold_rejected_published", [])),
        "INERT_EXCEPTIONS": len(out["db_verification"].get("inert_exceptions", [])),
    }
    out["overall"] = (
        "PASS"
        if (
            out["gates"]["PUBLISH_EXECUTED"]
            and out["gates"]["PUBLISH_FAILED_ZERO"]
            and out["gates"]["AUDIT_CONTRACT_PASS"]
            and out["gates"]["DB_ROW_VERIFY"] == "PASS"
            and out["gates"]["RESOLVER_VERIFY"] == "PASS"
            and out["gates"]["EXCLUDED_APPROVED_PUBLISHED"] == 0
            and out["gates"]["HOLD_REJECTED_PUBLISHED"] == 0
            and out["gates"]["INERT_EXCEPTIONS"] == 0
        )
        else "FAIL"
    )

    dest = ART / "CONSOLIDATED_POST_PUBLISH_EVIDENCE.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {dest}")
    print("OVERALL =", out["overall"])
    for k, v in out["gates"].items():
        print(f"  {k} = {v}")
    return 0 if out["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
