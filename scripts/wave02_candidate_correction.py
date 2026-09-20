"""WAVE02 candidate correction — remove erroneous REVIEW_PENDING rows I created.

Why this exists
---------------
The first Wave-02 ingest (this session) wrote 15 candidates whose scope
encoding did not match the platform's declared vocabulary:

  * `动物` was split with `ordinary_pet` as a member — the declared split
    (broad_term_split) has members dog/cat/other only;
  * `犬类` / `猫类` were used before these readings were declared;
  * parenthetical source terms (`宠物（符合规定的导盲犬除外）`,
    `动物（后滩滨江区域除外）`) are not source terms — the base must carry the
    bare declared term and the carve-out is a separate exception candidate.

The canonical §29 gate refused those rows (SOURCE_SCOPE_SEMANTICS=FAIL), which
is the gate doing its job. These rows are REVIEW_PENDING, carry no human
decision, were created in this same session and never published, so the correct
fix is to remove them and re-run the now-corrected ingest — the evidence file
has already been rewritten to declared vocabulary.

Scope of deletion: ONLY ``rule_candidate`` rows with
``expansion_run_id = EXP-R1-W02-20260919`` and ``review_status = REVIEW_PENDING``
and ``published_rule_id IS NULL``. Nothing else is touched: places, zones,
sources, artifacts, bundles and monitors stay; the re-ingest is idempotent
through the manifest and will not duplicate them.

Audit posture: the audit-event vocabulary has no ``candidate.delete`` action,
so no row is fabricated here. The deletion is recorded the same way the
Wave-01 dedup cleanup recorded its own: as a reviewable plan artifact plus
before/after fingerprints in ``artifacts/expansion_w02/``, and the audit events
for the original ``candidate.create`` / ``candidate.transition`` remain intact
as historical facts.

A plan artifact + fingerprint are always written; ``--execute`` performs the
deletion and clears the manifest's candidate section.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))
sys.path.insert(0, str(REPO / "scripts"))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import get_session_factory  # noqa: E402

RUN_ID = "EXP-R1-W02-20260919"
MANIFEST = REPO / "docs" / "expansion" / "expansion_r1_wave02_manifest.json"
ART_DIR = REPO / "artifacts" / "expansion_w02"
PLAN = ART_DIR / "wave02_candidate_correction_plan.json"
EXEC = ART_DIR / "wave02_candidate_correction_execute.json"


def collect(session: Session) -> list[dict]:
    rows = session.execute(
        text(
            "select id, animal_scope, subject_scope_normalized, source_scope_exact, "
            "normalization_type, review_status, published_rule_id "
            "from rule_candidate "
            "where expansion_run_id = :run and review_status = 'REVIEW_PENDING' "
            "and published_rule_id is null "
            "order by id"
        ),
        {"run": RUN_ID},
    ).fetchall()
    return [
        {
            "id": str(r[0]),
            "animal_scope": r[1],
            "subject_scope_normalized": r[2],
            "source_scope_exact": r[3],
            "normalization_type": r[4],
            "review_status": r[5],
            "published_rule_id": str(r[6]) if r[6] else None,
        }
        for r in rows
    ]


def fingerprint(session: Session) -> str:
    vals = (
        session.execute(
            text("select id from rule_candidate where expansion_run_id = :run  order by id"),
            {"run": RUN_ID},
        )
        .scalars()
        .all()
    )
    return hashlib.sha256("\n".join(str(v) for v in vals).encode()).hexdigest()


def clear_manifest_candidates() -> None:
    if not MANIFEST.exists():
        return
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    doc["rule_candidates"] = {}
    doc["observation_candidates"] = {}
    MANIFEST.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print("manifest rule_candidates cleared")


def main() -> int:
    ap = argparse.ArgumentParser(description="WAVE02 erroneous-candidate correction")
    ap.add_argument("--plan", action="store_true", help="dry-run: list, no deletion")
    ap.add_argument("--execute", action="store_true", help="delete + clear manifest")
    args = ap.parse_args()

    session_factory = get_session_factory()
    session = session_factory()

    rows = collect(session)
    fp_pre = fingerprint(session)
    print(f"CANDIDATES_TO_REMOVE = {len(rows)}")
    print(f"FINGERPRINT_PRE       = {fp_pre}")
    for r in rows:
        print(
            f"  {r['id'][:8]} | {r['animal_scope']} | subj={r['subject_scope_normalized']} "
            f"| sage={r['source_scope_exact']!r} | norm={r['normalization_type']}"
        )

    plan_doc = {
        "operation": "wave02_candidate_correction",
        "run_id": RUN_ID,
        "at": datetime.now(UTC).isoformat(),
        "reason": (
            "scope encoding used undeclared vocabulary (animals split members, "
            "犬类/猫类, parenthetical terms); §29 SOURCE_SCOPE_SEMANTICS refused; "
            "un-reviewed rows removed so the corrected ingest can rebuild them"
        ),
        "fingerprint_pre": fp_pre,
        "candidates": rows,
    }
    ART_DIR.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps(plan_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", PLAN)

    if args.execute:
        session.execute(
            text(
                "delete from rule_candidate where expansion_run_id = :run "
                " and review_status = 'REVIEW_PENDING' and published_rule_id is null"
            ),
            {"run": RUN_ID},
        )
        session.commit()
        fp_post = fingerprint(session)
        print(f"DELETED {len(rows)} rows")
        print(f"FINGERPRINT_POST      = {fp_post}")
        exec_doc = {
            "operation": "wave02_candidate_correction",
            "at": datetime.now(UTC).isoformat(),
            "deleted": len(rows),
            "fingerprint_pre": fp_pre,
            "fingerprint_post": fp_post,
            "manifest_candidates_cleared": True,
        }
        EXEC.write_text(json.dumps(exec_doc, ensure_ascii=False, indent=2), encoding="utf-8")
        print("WROTE", EXEC)
        clear_manifest_candidates()
    session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
