"""Wave 02 Human Review signature writer.

Mechanically records the human reviewer's explicit final decisions for
EXP-R1-W02-REVIEW-R1. The agent does not reinterpret, optimize or infer any
decision: the mapping below is a verbatim transcription of the human's stated
decisions (huangdi97: "接受建议" = accept the AI recommendations of
docs/expansion/WAVE02_REVIEW_RECOMMENDATIONS.md).

Governance contract (mirrors scripts/expansion_w01_sign_review.py):
  - only final_decision / reviewer / decided_at / decision_note change
  - decisions are written by stable candidate_id, verified via ordinal anchor
  - refuses to run if any signature already exists (no overwrite)
  - refuses to run if revision / expansion_run_id / row count do not match
  - decided_at is a single top-level timestamp shared by every row
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

REGISTRY = Path("docs/expansion/review_decisions_expansion_r1_wave02.json")

EXPECTED_REVISION = "EXP-R1-W02-REVIEW-R1"
EXPECTED_RUN_ID = "EXP-R1-W02-20260919"
EXPECTED_ROWS = 20
REVIEWER = "huangdi97"

CANONICAL_DECISIONS = {"APPROVED", "APPROVED_WITH_NOTE", "HOLD", "REJECTED"}

# #NN -> (final_decision, decision_note)
# Transcribed from the human reviewer's authorization ("接受建议").
# Notes reuse the reason labels from the recommendation document; no new
# business reasoning is invented here.
DECISIONS: dict[int, tuple[str, str]] = {
    1: ("APPROVED", ""),   # 7774a487 世博 dog
    2: ("APPROVED", ""),   # afe409b1 世博 other
    3: ("APPROVED", ""),   # f80c6071 世博 cat
    4: ("APPROVED", ""),   # 4b4b4e07 植物园 cat
    5: ("APPROVED", ""),   # 630e1c0d 植物园 other
    6: ("APPROVED", ""),   # 97d564fa 植物园 dog
    7: ("APPROVED", ""),   # 700dcd4d 自然博物馆
    8: ("HOLD", "OFFICIAL_PAGE_VERBATIM_VERIFICATION_REQUIRED"),   # 81eca767 辰山
    9: ("APPROVED", ""),   # 237512f7 野生动物园
    10: ("APPROVED", ""),  # c111a1a1 共青 dog
    11: ("APPROVED", ""),  # eba1843a 共青 other
    12: ("APPROVED", ""),  # ec883c91 共青 cat
    13: ("APPROVED", ""),  # 98d2b355 和平 dog
    14: ("APPROVED", ""),  # da0c270c 和平 cat
    15: ("APPROVED", ""),  # d5551907 昆山 dog
    16: ("APPROVED", ""),  # 5f22e9a1 豫园 base
    17: ("APPROVED", ""),  # 91970069 豫园 guide_dog
    18: ("HOLD", "SECONDARY_SOURCE_NEEDS_FIRST_PARTY_CONFIRMATION"),  # 36f6382f 顾村 dog
    19: ("HOLD", "SECONDARY_SOURCE_NEEDS_FIRST_PARTY_CONFIRMATION"),  # b6abed36 顾村 other
    20: ("HOLD", "SECONDARY_SOURCE_NEEDS_FIRST_PARTY_CONFIRMATION"),  # c6c5b74d 顾村 cat
}

EXPECTED_DISTRIBUTION = {"APPROVED": 16, "APPROVED_WITH_NOTE": 0, "HOLD": 4, "REJECTED": 0}

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

# Spotlight anchors: (candidate_id prefix, place, scope, effect, layer)
ANCHORS: dict[int, tuple[str, str, str, str, str]] = {
    8: ("81eca767", "上海辰山植物园", "ordinary_pet", "prohibited", "OPERATOR_POLICY"),
    16: ("5f22e9a1", "豫园", "ordinary_pet", "prohibited", "OPERATOR_POLICY"),
    17: ("91970069", "豫园", "service_dog", "conditional", "OPERATOR_POLICY"),
}


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

    # ---- pre-flight assertions -----------------------------------------
    if doc.get("revision") != EXPECTED_REVISION:
        fail(f"revision mismatch: {doc.get('revision')!r} != {EXPECTED_REVISION!r}")
    if doc.get("expansion_run_id") != EXPECTED_RUN_ID:
        fail(f"expansion_run_id mismatch: {doc.get('expansion_run_id')!r}")
    rows = doc.get("rows") or []
    if len(rows) != EXPECTED_ROWS:
        fail(f"row count mismatch: {len(rows)} != {EXPECTED_ROWS}")
        fail("registry already carries a top-level signature; refusing to overwrite")
    for r in rows:
        if r.get("final_decision") or r.get("reviewer") or r.get("decided_at"):
            fail(f"row {r.get('candidate_id')} already signed; refusing to overwrite")

    if len({r["candidate_id"] for r in rows}) != len(rows):
        fail("duplicate candidate_id present")

    # ---- ordinal -> stable id mapping + anchors ------------------------
    planned: list[tuple[str, str, str]] = []  # (candidate_id, decision, note)
    for ordinal, row in enumerate(rows, start=1):
        if ordinal not in DECISIONS:
            fail(f"no decision supplied for #{ordinal:02d}")
        decision, note = DECISIONS[ordinal]
        if decision not in CANONICAL_DECISIONS:
            fail(f"non-canonical decision for #{ordinal:02d}: {decision!r}")
        if ordinal in ANCHORS:
            exp_id, exp_place, exp_scope, exp_effect, exp_layer = ANCHORS[ordinal]
            got = (
                (row.get("candidate_id") or "")[:8],
                row.get("place_name"),
                row.get("animal_scope"),
                row.get("effect"),
                row.get("rule_layer"),
            )
            if got != (exp_id, exp_place, exp_scope, exp_effect, exp_layer):
                fail(
                    f"#{ordinal:02d} anchor mismatch: {got} != "
                    f"{(exp_id, exp_place, exp_scope, exp_effect, exp_layer)}"
                )
        planned.append((row["candidate_id"], decision, note))

    decided_at = args.decided_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")

    dist = Counter(d for _, d, _ in planned)
    print(f"revision   : {doc['revision']}")
    print(f"run_id     : {doc['expansion_run_id']}")
    print(f"rows       : {len(planned)}")
    print(f"reviewer   : {REVIEWER}")
    print(f"decided_at : {decided_at}")
    print(f"distribution: {dict(dist)}")
    effective_expected = {k: v for k, v in EXPECTED_DISTRIBUTION.items() if v}
    if dict(dist) != effective_expected:
        fail(f"distribution mismatch: {dict(dist)} != {EXPECTED_DISTRIBUTION}")

    if not args.execute:
        print("DRY-RUN: no changes written (pass --execute to write)")
        return 0

    # ---- write ---------------------------------------------------------
    for row, (_cid, decision, note) in zip(rows, planned, strict=True):
        row["final_decision"] = decision
        row["reviewer"] = REVIEWER
        row["decided_at"] = decided_at
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
