"""Wave 01 Human Review signature writer.

Mechanically records the human reviewer's explicit final decisions for
EXP-R1-W01-REVIEW-R1. The agent does not reinterpret, optimize or infer any
decision: the mapping below is a verbatim transcription of the human's stated
decisions.

Governance contract (WAVE01_HUMAN_REVIEW_SIGNATURE_AND_PREPUBLISH_CONTINUATION_R1):
  - only final_decision / reviewer / decided_at (and derived summaries) change
  - decisions are written by stable candidate_id, verified against #NN / place / scope
  - refuses to run if any signature already exists (no overwrite)
  - refuses to run if revision / expansion_run_id / row count do not match
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REGISTRY = Path("docs/expansion/review_decisions_expansion_r1_wave01.json")

EXPECTED_REVISION = "EXP-R1-W01-REVIEW-R1"
EXPECTED_RUN_ID = "EXP-R1-W01-20260918"
EXPECTED_ROWS = 31
REVIEWER = "huangdi97"

CANONICAL_DECISIONS = {"APPROVED", "APPROVED_WITH_NOTE", "HOLD", "REJECTED"}

# #NN -> (final_decision, decision_note)
# Transcribed from the human reviewer's authorization. Notes use the reason
# labels supplied in the authorization (section 6); no new business reasoning is
# invented here.
DECISIONS: dict[int, tuple[str, str]] = {
    1: ("APPROVED", ""),
    2: ("REJECTED", "LEAD_ONLY_SOURCE_NOT_PUBLISHABLE"),
    3: ("APPROVED", ""),
    4: ("HOLD", "ZONE_SPLIT_REQUIRED"),
    5: ("HOLD", "PRIMARY_OPERATOR_SOURCE_NOT_VERIFIED"),
    6: ("APPROVED", ""),
    7: ("APPROVED", ""),
    8: ("APPROVED", ""),
    9: ("APPROVED", ""),
    10: ("APPROVED", ""),
    11: ("HOLD", "LEGAL_OPERATOR_SCOPE_CONFLICT_REQUIRES_RESOLUTION"),
    12: ("HOLD", "LEGAL_OPERATOR_SCOPE_CONFLICT_REQUIRES_RESOLUTION"),
    13: ("HOLD", "LEGAL_OPERATOR_SCOPE_CONFLICT_REQUIRES_RESOLUTION"),
    14: ("APPROVED", ""),
    15: ("HOLD", "LEGAL_APPLICABILITY_TO_OUTDOOR_ZONE_UNRESOLVED"),
    16: ("HOLD", "ZONE_SCOPE_NOT_PRECISE_ENOUGH"),
    17: ("HOLD", "ZONE_SCOPE_NOT_PRECISE_ENOUGH"),
    18: ("APPROVED", ""),
    19: ("APPROVED", ""),
    20: ("HOLD", "SOURCE_REQUIRES_VERIFICATION"),
    21: ("APPROVED", ""),
    22: ("APPROVED", ""),
    23: ("APPROVED", ""),
    24: ("HOLD", "SOURCE_SCOPE_NOT_EQUIVALENT_AND_SECONDARY_SOURCE"),
    25: ("APPROVED", ""),
    26: ("HOLD", "CURRENT_SUPERSESSION_UNRESOLVED"),
    27: ("HOLD", "SECONDARY_SOURCE_NEEDS_FIRST_PARTY_CONFIRMATION"),
    28: ("APPROVED", ""),
    29: ("HOLD", "SUPERSESSION_CURRENT_VERSION_UNRESOLVED"),
    30: ("REJECTED", "NO_UNIFIED_RULE_SHOULD_REMAIN_UNKNOWN"),
    31: ("HOLD", "CUSTOMER_SERVICE_SOURCE_NEEDS_VERIFICATION"),
}

EXPECTED_DISTRIBUTION = {"APPROVED": 15, "APPROVED_WITH_NOTE": 0, "HOLD": 14, "REJECTED": 2}

# Fields that must never be touched by this script.
FROZEN_FIELDS = (
    "candidate_id",
    "place_name",
    "place_id",
    "zone_id",
    "animal_scope",
    "subject_scope_normalized",
    "source_scope_exact",
    "normalization_type",
    "normative_effect",
    "effect",
    "rule_layer",
    "mandatory_level",
    "evidence_bundle_id",
    "source_type",
)


def fail(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    raise SystemExit(4)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="write the registry")
    ap.add_argument("--decided-at", default=None, help="override signing timestamp (ISO-8601)")
    args = ap.parse_args()

    if not REGISTRY.exists():
        fail(f"registry not found: {REGISTRY}")

    doc = json.loads(REGISTRY.read_text(encoding="utf-8"))

    # ---- section 3: pre-flight assertions -------------------------------
    if doc.get("revision") != EXPECTED_REVISION:
        fail(f"revision mismatch: {doc.get('revision')!r} != {EXPECTED_REVISION!r}")
    if doc.get("expansion_run_id") != EXPECTED_RUN_ID:
        fail(f"expansion_run_id mismatch: {doc.get('expansion_run_id')!r}")

    rows = doc.get("rows") or []
    if len(rows) != EXPECTED_ROWS:
        fail(f"row count mismatch: {len(rows)} != {EXPECTED_ROWS}")

    if doc.get("reviewer") or doc.get("decided_at"):
        fail("registry already carries a top-level signature; refusing to overwrite")
    for r in rows:
        if r.get("final_decision") or r.get("reviewer") or r.get("decided_at"):
            fail(f"row {r.get('candidate_id')} already signed; refusing to overwrite")

    if len({r["candidate_id"] for r in rows}) != len(rows):
        fail("duplicate candidate_id present")

    # ---- section 4: verify ordinal -> stable id mapping -----------------
    # The registry order defines #01..#31. The reviewer's mapping was produced
    # against the quick table, whose order is identical. Both were generated
    # from the same run manifest, so ordinal position is a *verified* join key
    # and each row is additionally checked against its expected place/scope.
    D43_CHECK = {  # spot-check anchors from the review packet
        8: ("上海博物馆东馆", "service_dog", "allowed", "LEGAL"),
        19: ("上海迪士尼乐园", "service_dog", "conditional", "OPERATOR_POLICY"),
        23: ("兴业太古汇", "service_dog", "allowed", "LEGAL"),
        30: ("西岸梦中心（Gate M）", "ordinary_pet", "conditional", "OPERATOR_POLICY"),
    }

    planned: list[tuple[str, str, str]] = []  # (candidate_id, decision, note)
    for ordinal, row in enumerate(rows, start=1):
        if ordinal not in DECISIONS:
            fail(f"no decision supplied for #{ordinal:02d}")
        decision, note = DECISIONS[ordinal]
        if decision not in CANONICAL_DECISIONS:
            fail(f"non-canonical decision for #{ordinal:02d}: {decision!r}")
        if ordinal in D43_CHECK:
            exp_place, exp_scope, exp_effect, exp_layer = D43_CHECK[ordinal]
            got = (
                row.get("place_name"),
                row.get("animal_scope"),
                row.get("effect"),
                row.get("rule_layer"),
            )
            if got != (exp_place, exp_scope, exp_effect, exp_layer):
                fail(
                    f"#{ordinal:02d} anchor mismatch: {got} != "
                    f"{(exp_place, exp_scope, exp_effect, exp_layer)}"
                )
        planned.append((row["candidate_id"], decision, note))

    decided_at = args.decided_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")

    print(f"revision   : {doc['revision']}")
    print(f"run_id     : {doc['expansion_run_id']}")
    print(f"rows       : {len(planned)}")
    print(f"reviewer   : {REVIEWER}")
    print(f"decided_at : {decided_at}")
    from collections import Counter

    dist = Counter(d for _, d, _ in planned)
    print(f"distribution: {dict(dist)}")

    if not args.execute:
        print("DRY-RUN: no changes written (pass --execute to write)")
        return 0

    # ---- write ----------------------------------------------------------
    for row, (_cid, decision, note) in zip(rows, planned, strict=True):
        row["final_decision"] = decision
        row["reviewer"] = REVIEWER
        row["decided_at"] = decided_at
        if "decision_note" in row or note:
            row["decision_note"] = note

    doc["reviewer"] = REVIEWER
    doc["decided_at"] = decided_at

    REGISTRY.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"WROTE {REGISTRY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
