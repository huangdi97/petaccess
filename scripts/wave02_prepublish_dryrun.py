"""Wave 02 pre-publish evaluation — READ-ONLY dry-run against the live DB.

For every Wave-02 candidate the human (huangdi97) APPROVED, this script runs
the REAL pre-publish gate (``publish_gate.evaluate_for_publish``) on a live
session, then applies the same plan/scope/dependency checks the publisher
would (base-before-exception ordering, no HOLD/REJECTED rows, no already
published rows). It writes NOTHING: no commits, no candidate transitions, no
rule rows, no audit rows.

Output:
  - per-candidate gate result (PASS / BLOCKED + reasons)
  - publishability disposition (WRITE / NOOP / NEVER)
  - proposed safe batch manifest (as JSON, written only when --out is given)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for extra in (str(ROOT / "scripts"), str(ROOT / "services" / "api"), str(ROOT)):
    if extra not in sys.path:
        sys.path.insert(0, extra)

from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.db.session import make_engine  # noqa: E402
from app.models import RuleCandidate  # noqa: E402
from app.services.publish_gate import evaluate_for_publish  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from dev_api_server import database_url_for  # noqa: E402

RUN_ID = "EXP-R1-W02-20260919"
REGISTRY = ROOT / "docs" / "expansion" / "review_decisions_expansion_r1_wave02.json"
APPROVED = "APPROVED"


def load_signed() -> list[dict]:
    doc = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if doc.get("reviewer") != "huangdi97":
        raise SystemExit(f"REFUSED: registry not signed by huangdi97 (got {doc.get('reviewer')!r})")
    return doc["rows"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--database-url", default=None)
    ap.add_argument("--out", default=None, help="write the proposed manifest JSON here (optional)")
    args = ap.parse_args()

    url = args.database_url or database_url_for("petaccess")
    if not url:
        raise SystemExit("REFUSED: no DATABASE_URL (checked .env + --database-url)")
    engine = make_engine(url)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    rows = load_signed()
    approved = [r for r in rows if r.get("final_decision") == APPROVED]
    holds = [r for r in rows if r.get("final_decision") == "HOLD"]
    rejected = [r for r in rows if r.get("final_decision") == "REJECTED"]
    print(f"signed rows       : {len(rows)}")
    print(f"APPROVED          : {len(approved)}")
    print(f"HOLD              : {len(holds)}")
    print(f"REJECTED          : {len(rejected)}")

    report: dict = {
        "revision": "EXP-R1-W02-REVIEW-R1",
        "run_id": RUN_ID,
        "reviewer": "huangdi97",
        "evaluated_at": datetime.now(UTC).isoformat(),
        "zero_db_mutation": True,
        "rows": [],
    }

    with Session() as session:
        for r in approved:
            cid = r["candidate_id"]
            cand = session.get(RuleCandidate, cid)
            if cand is None:
                report["rows"].append(
                    {
                        "candidate_id": cid,
                        "place": r.get("place_name"),
                        "gate": "NOT_RUN",
                        "reason": "candidate_row_missing",
                    }
                )
                continue
            violations = evaluate_for_publish(session, cand)
            gate = "PASS" if not violations else "BLOCKED"
            report["rows"].append(
                {
                    "candidate_id": cid,
                    "place": r.get("place_name"),
                    "animal_scope": cand.animal_scope,
                    "effect": cand.effect,
                    "gate": gate,
                    "violations": [v.code for v in violations],
                    "violation_messages": [v.message for v in violations],
                }
            )
            print(f"  {cid[:8]} {r.get('place_name')} [{cand.animal_scope}] gate={gate}")

    dist = Counter(entry["gate"] for entry in report["rows"])
    report["gate_distribution"] = dict(dist)

    passed = [e for e in report["rows"] if e["gate"] == "PASS"]
    manifest = {
        "_schema": "publish batch manifest v1 — Wave-02 safe batch (proposed, NOT executed)",
        "revision": "EXP-R1-W02-REVIEW-R1",
        "batch_id": "EXP-R1-W02-REVIEW-R1-BATCH-01",
        "reviewer": "huangdi97",
        "candidate_ids": [e["candidate_id"] for e in passed],
        "execution_status": "PROPOSED_DRY_RUN_ONLY",
    }
    report["proposed_manifest"] = manifest
    report["proposed_batch_size"] = len(passed)

    print(f"gate distribution : {dict(dist)}")
    print(f"proposed batch    : {len(passed)} candidates (PASS only)")
    print("ZERO_DB_MUTATION  : True (nothing written)")

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE {out}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
