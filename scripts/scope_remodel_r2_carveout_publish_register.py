"""Project the Disney dog base + the remediated guide-dog carve-out into one register.

Why a second projector
----------------------
``scope_remodel_r2_publish_register.py`` binds the *frozen* carve-out
``w01-305fa08c1e`` to the new dog base. That carve-out cannot be published, so
that register can never produce an executable Disney-dog batch.

The replacement carve-out is a **new candidate** (created by
``scope_remodel_r2_carveout_candidate.py``) with a **new review** of its own
(``review_decisions_scope_remodel_r2_carveout.json``). To publish the pair as one
dependency-closed batch, both rows must sit in the *same* register — the
canonical refusal 4 is measured inside a register, and a cross-file dependency
is invisible to the batch validator.

So this projector emits a register with exactly two rows:

1. the Disney dog base, its existing huangdi97 signature copied verbatim;
2. the new carve-out, its new huangdi97 signature copied verbatim;

plus the ``exception_plan`` that binds (2) to (1). Nothing else is in it — the
four rows already published in SCOPE-REMODEL-R2-BATCH-02 are done, and the
zoo dog row is HOLD.

It refuses to write while either signature is incomplete.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "services" / "api"))

from publish_batch import is_reachable_carveout  # noqa: E402
from scope_remodel_r2_publish_register import (  # noqa: E402
    APPROVAL_DECISIONS,
    DISNEY_DOG_CANDIDATE,
    REVISION,
    build_row,
    fail,
    fetch_chain,
)

SIGNED_BASE_REGISTER = REPO / "docs" / "expansion" / "review_decisions_scope_remodel_r2.json"
SIGNED_CARVE_REGISTER = (
    REPO / "docs" / "expansion" / "review_decisions_scope_remodel_r2_carveout.json"
)
OUT_REGISTER = (
    REPO / "docs" / "expansion" / "review_decisions_scope_remodel_r2_dog_publishable.json"
)

#: The frozen carve-out this batch replaces. It is deliberately NOT in the
#: output: it is blocked, and importing it would make the batch unexecutable.
FROZEN_CARVE_OUT_RULE_ID = "w01-305fa08c1e"


def signed_row(candidate_id: str, doc: dict, where: str) -> dict:
    for row in doc["rows"]:
        if str(row.get("candidate_id")) == candidate_id:
            return row
    fail(f"{candidate_id} not found in {where}")


def require_signature(rows: list[dict], where: str) -> None:
    unsigned = [
        r.get("candidate_id")
        for r in rows
        if not (
            r.get("final_decision")
            and r.get("reviewer")
            and r.get("decided_at")
            and (r.get("decision_note") or r.get("review_note"))
        )
    ]
    if unsigned:
        fail(f"{where}: {len(unsigned)} row(s) lack a complete signature: {unsigned[:3]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_REGISTER))
    ap.add_argument("--execute", action="store_true", help="write the projected register")
    args = ap.parse_args()

    base_doc = json.loads(SIGNED_BASE_REGISTER.read_text(encoding="utf-8"))
    carve_doc = json.loads(SIGNED_CARVE_REGISTER.read_text(encoding="utf-8"))
    if base_doc.get("revision") != REVISION:
        fail(f"base register revision mismatch: {base_doc.get('revision')!r}")

    base_signed = signed_row(DISNEY_DOG_CANDIDATE, base_doc, str(SIGNED_BASE_REGISTER))
    carve_rows = carve_doc["rows"]
    if len(carve_rows) != 1:
        fail(f"expected exactly one carve-out row, got {len(carve_rows)}")
    carve_signed = carve_rows[0]
    require_signature([base_signed], str(SIGNED_BASE_REGISTER))
    require_signature([carve_signed], str(SIGNED_CARVE_REGISTER))

    ids = [base_signed["candidate_id"], carve_signed["candidate_id"]]
    chain = fetch_chain(ids)
    missing = [i for i in ids if i not in chain]
    if missing:
        fail(f"{len(missing)} candidate(s) absent from the evidence chain: {missing}")

    base_row = build_row(base_signed, chain[base_signed["candidate_id"]])
    carve_row = build_row(carve_signed, chain[carve_signed["candidate_id"]])
    carve_row["_remediates"] = FROZEN_CARVE_OUT_RULE_ID
    rows = [base_row, carve_row]

    verdict = is_reachable_carveout(base_row, carve_row)
    same_layer = carve_row.get("rule_layer") == base_row.get("rule_layer")
    exception_plan = [
        {
            "rule_id": carve_row["rule_id"],
            "candidate_id": carve_row["candidate_id"],
            "place_name": carve_row.get("place_name"),
            "zone_name": carve_row.get("zone_name"),
            "layer": carve_row.get("rule_layer"),
            "effect": carve_row.get("effect"),
            "mandatory_level": carve_row.get("mandatory_level"),
            "subject_scope_normalized": carve_row.get("subject_scope_normalized"),
            "normalization_type": carve_row.get("normalization_type"),
            "normative_effect": carve_row.get("normative_effect"),
            "decision": carve_row.get("final_decision"),
            "mode": "rule_exception",
            "bases": [
                {
                    "rule_id": base_row["rule_id"],
                    "layer": base_row.get("rule_layer"),
                    "decision": base_row.get("final_decision"),
                    "same_layer": bool(same_layer),
                    "executable": base_row.get("final_decision") in APPROVAL_DECISIONS,
                }
            ],
            "cross_layer_dropped": [],
            "reachable": verdict is True,
            "reachability_verdict": {True: "reachable", False: "unreachable", None: "unevaluable"}[
                verdict
            ],
            "replaces": FROZEN_CARVE_OUT_RULE_ID,
        }
    ]
    base_row["carve_out_of"] = [carve_row["rule_id"]]
    base_row["exception_binding_required"] = True
    base_row["reachable"] = verdict is True

    doc = {
        "_readme": (
            "Projected by scripts/scope_remodel_r2_carveout_publish_register.py from the signed "
            "SCOPE-REMODEL-R2 register (Disney dog base) and the signed carve-out register "
            "(remediated guide-dog exception). Both signatures are COPIED, never computed. "
            "The frozen carve-out w01-305fa08c1e is deliberately absent: it is blocked by the "
            "canonical gate and importing it would make this batch unexecutable."
        ),
        "revision": REVISION,
        "generated_at": base_doc.get("generated_at"),
        "human_signoff_required": True,
        "rows": rows,
        "exception_plan": exception_plan,
        "exception_binding": {
            e["rule_id"]: {
                "bases": [b["rule_id"] for b in e["bases"] if b["same_layer"]],
                "cross_layer_dropped": e["cross_layer_dropped"],
            }
            for e in exception_plan
            if any(b["same_layer"] for b in e["bases"])
        },
    }

    out = Path(args.out)
    print(f"rows            : {len(rows)}")
    print(f"base            : {base_row['rule_id']} ({base_row['final_decision']})")
    print(f"carve-out       : {carve_row['rule_id']} ({carve_row['final_decision']})")
    print(f"carve-out reach : {verdict}  same_layer={same_layer}")
    print(f"out             : {out}")

    if not args.execute:
        print("DRY-RUN: no changes written (pass --execute to write)")
        return 0
    out.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"WROTE {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
