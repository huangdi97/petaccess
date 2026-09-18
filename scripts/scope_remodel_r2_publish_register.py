"""Project the signed SCOPE-REMODEL-R2 register into a publisher-consumable register.

Why this exists
---------------
`scripts/publish_reviewed_r1.py` is the only real publish entry point, and it
consumes a register whose rows carry the *gate* fields it validates:
``rule_id``, ``action``, ``evidence_strength``, ``license``, ``reviewed_at``,
``carve_out_of`` … plus a top-level ``exception_plan`` / ``exception_binding``
block. `docs/expansion/review_decisions_scope_remodel_r2.json` carries the human
signature and the frozen governance fields but none of the derived gate fields,
so feeding it to the publisher raises ``KeyError: 'rule_id'``.

One thing makes this projector different from the Wave-01 one
-------------------------------------------------------------
The Disney dog base is a *prohibition* whose only approved carve-out — the
guide-dog exception ``w01-305fa08c1e`` — is **a row of another revision**
(``EXP-R1-W01-REVIEW-R1``). The canonical batch refusal 4 ("no prohibition
without its REACHABLE approved carve-out") is measured *within one register*:
if the carve-out is not a row of this register, the publisher cannot see the
obligation at all, and the batch would silently ship a prohibition whose
approved exception stays unpublished.

So this projector imports that one row, carrying its **existing** signature
verbatim (``final_decision`` / ``reviewer`` / ``reviewed_at`` are copied, never
minted). It does not re-review it, does not change it, and does not touch the
Wave-01 register file itself. The imported row is marked
``_imported_dependency = true`` so the report can say exactly why it is here.

Everything else follows the Wave-01 projector:

  - derivations are imported from ``gen_human_review_packet_r2_final``;
  - reachability is measured with ``publish_batch.is_reachable_carveout``
    (which itself uses ``app.rulespec.animal_scope.rule_governs``, ADR-025);
  - the human signature is copied, never computed.

Output: ``docs/expansion/review_decisions_scope_remodel_r2_publishable.json``
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import psycopg

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "services" / "api"))

from gen_human_review_packet_r2_final import (  # noqa: E402
    _applicability,
    _license_problems,
    derive_evidence_strength,
)
from publish_batch import is_reachable_carveout  # noqa: E402

SIGNED_REGISTER = REPO / "docs" / "expansion" / "review_decisions_scope_remodel_r2.json"
WAVE01_PUBLISHABLE = (
    REPO / "docs" / "expansion" / "review_decisions_expansion_r1_wave01_publishable.json"
)
OUT_REGISTER = REPO / "docs" / "expansion" / "review_decisions_scope_remodel_r2_publishable.json"

DB_URL = "postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"
REVISION = "SCOPE-REMODEL-R2"
RUN_ID = "SCOPE-R2-20260918"

#: The revision the imported carve-out was signed under. Recorded, not merged:
#: this register's revision stays SCOPE-REMODEL-R2.
IMPORTED_REVISION = "EXP-R1-W01-REVIEW-R1"

#: The Disney guide-dog carve-out. Its base changes this round (from the frozen
#: ``other``-scope candidate to the new ``dog``-scope one), which is the whole
#: point of the SCOPE-REMODEL-R2 remodel.
CARVE_OUT_RULE_ID = "w01-305fa08c1e"
CARVE_OUT_PLACE = "上海迪士尼乐园"

#: The new Disney dog base, by candidate id — the carve-out's new anchor.
DISNEY_DOG_CANDIDATE = "7b595de9-e0c3-4092-aab4-348c4878c296"

HUMAN_DECISIONS = ("APPROVED", "APPROVED_WITH_NOTE", "HOLD", "REJECTED")
APPROVAL_DECISIONS = ("APPROVED", "APPROVED_WITH_NOTE")


def fail(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    raise SystemExit(4)


CHAIN_SQL = """
SELECT rc.id, rc.animal_scope, rc.action, rc.effect, rc.rule_layer,
       rc.mandatory_level, rc.review_status, rc.source_scope_exact,
       rc.subject_scope_normalized, rc.normalization_type,
       rc.normative_effect, rc.holder_scope, rc.zone_id, rc.place_id,
       rc.source_id, rc.evidence_bundle_id, rc.raw_text, rc.proposed_conditions,
       z.name AS zone_name, z.zone_type, z.indoor_outdoor,
       p.canonical_name AS place_name, p.place_type,
       p.canonical_address AS place_address,
       s.source_type, s.issuer, s.issuer_verification, s.source_url,
       s.source_snapshot_ref, s.source_availability, s.directness,
       s.spatial_precision, s.published_at AS src_published_at,
       s.observed_at, s.collected_at, s.notes AS src_notes,
       eb.id AS bundle_id, eb.source_url AS bundle_url, eb.source_platform,
       eb.publisher_type, eb.evidence_class, eb.quoted_fragment,
       eb.extracted_fragment, eb.content_hash, eb.place_match_evidence,
       eb.temporal_evidence, eb.license_metadata, eb.captured_at,
       eb.published_at AS bundle_published_at, eb.screenshot_ref,
       eb.snapshot_ref, eb.artifact_id,
       art.artifact_type, art.source_url AS artifact_url,
       art.source_content_id, art.snapshot_ref AS artifact_snapshot_ref,
       art.collector_type, art.evidence_strength AS artifact_strength,
       art.storage_allowed, art.display_allowed, art.redistribution_allowed,
       art.publisher_type AS artifact_publisher
  FROM rule_candidate rc
  LEFT JOIN zone  z  ON z.id  = rc.zone_id
  LEFT JOIN place p  ON p.id  = rc.place_id
  LEFT JOIN source s ON s.id  = rc.source_id
  LEFT JOIN evidence_bundle eb ON eb.id = rc.evidence_bundle_id
  LEFT JOIN source_artifact art ON art.id = eb.artifact_id
 WHERE rc.id = ANY(%s)
"""


def fetch_chain(candidate_ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    with psycopg.connect(DB_URL, connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute(CHAIN_SQL, (candidate_ids,))
        if cur.description is None:
            raise RuntimeError("证据链查询未返回列描述")
        cols = [c.name for c in cur.description]
        for raw in cur.fetchall():
            d = dict(zip(cols, raw, strict=True))
            out[d["id"]] = d
    return out


def derive_rule_id(candidate_id: str) -> str:
    """``sr2-`` + the first 10 hex chars of the UUID — deterministic, unique,
    and unmistakably a SCOPE-REMODEL-R2 row (it can never collide with a
    hand-written R2 slug or a ``w01-`` Wave-01 id)."""
    return f"sr2-{candidate_id.replace('-', '')[:10]}"


def build_row(signed_row: dict, st: dict) -> dict:
    strength, strength_notes = derive_evidence_strength(st)
    return {
        # ---- identity -----------------------------------------------------
        "candidate_id": signed_row["candidate_id"],
        "rule_id": derive_rule_id(signed_row["candidate_id"]),
        # ---- frozen governance fields, carried from the signed register ----
        "place_key": None,
        "place_name": signed_row["place_name"],
        "place_id": st.get("place_id"),
        "zone_key": None,
        "zone_id": signed_row["zone_id"],
        "zone_name": st.get("zone_name"),
        "zone_type": st.get("zone_type"),
        "indoor_outdoor": st.get("indoor_outdoor"),
        "place_address": st.get("place_address"),
        "place_type": st.get("place_type"),
        "source_key": None,
        "source_id": st.get("source_id"),
        "source_url": st.get("source_url"),
        "source_type": signed_row.get("source_type"),
        "issuer": st.get("issuer"),
        "issuer_verification": st.get("issuer_verification"),
        "rule_layer": signed_row["rule_layer"],
        "mandatory_level": signed_row["mandatory_level"],
        "animal_scope": signed_row["animal_scope"],
        "action": st.get("action"),
        "effect": signed_row["effect"],
        "conditions": st.get("proposed_conditions") or [],
        "source_scope_exact": signed_row["source_scope_exact"],
        "subject_scope_normalized": signed_row["subject_scope_normalized"],
        "normalization_type": signed_row["normalization_type"],
        "normative_effect": signed_row["normative_effect"],
        "holder_scope": st.get("holder_scope"),
        "evidence_bundle_id": signed_row.get("evidence_bundle_id"),
        "bundle_url": st.get("bundle_url"),
        "artifact_id": st.get("artifact_id"),
        "artifact_url": st.get("artifact_url"),
        "artifact_type": st.get("artifact_type"),
        "snapshot_ref": (
            st.get("snapshot_ref")
            or st.get("artifact_snapshot_ref")
            or st.get("source_snapshot_ref")
        ),
        "source_content_id": st.get("source_content_id"),
        "content_hash": st.get("content_hash"),
        "quoted_fragment": st.get("quoted_fragment"),
        "raw_text": st.get("raw_text"),
        "captured_at": st.get("captured_at"),
        # ---- derived gate fields (canonical derivations) ------------------
        "evidence_strength": strength,
        "strength_notes": strength_notes,
        "evidence_strength_claimed": st.get("artifact_strength"),
        "directness": st.get("directness"),
        "spatial_precision": st.get("spatial_precision"),
        "source_availability": st.get("source_availability"),
        "license_metadata": st.get("license_metadata"),
        "artifact_license": {
            "storage_allowed": st.get("storage_allowed"),
            "display_allowed": st.get("display_allowed"),
            "redistribution_allowed": st.get("redistribution_allowed"),
        },
        "license_problems": _license_problems(st),
        "place_match_evidence": st.get("place_match_evidence"),
        "applicability": _applicability(st),
        "last_verified_at": (
            st.get("observed_at") or st.get("collected_at") or st.get("captured_at")
        ),
        # ---- human signature, COPIED VERBATIM -----------------------------
        "final_decision": signed_row["final_decision"],
        "reviewer": signed_row["reviewer"],
        "reviewed_at": signed_row["decided_at"],
        "review_note": signed_row.get("decision_note") or None,
        "proposed_decision": None,
        "proposed_reason": None,
        # ---- publication classification -----------------------------------
        "carve_out_of": None,
        "exception_binding_required": False,
        "reachable": None,
        "review_status": st.get("review_status"),
        # ---- provenance of the row inside this register -------------------
        "supersedes_candidate_id": signed_row.get("supersedes_candidate_id"),
        "_imported_dependency": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_REGISTER))
    ap.add_argument("--execute", action="store_true", help="write the projected register")
    args = ap.parse_args()

    if not SIGNED_REGISTER.exists():
        fail(f"signed register not found: {SIGNED_REGISTER}")

    signed = json.loads(SIGNED_REGISTER.read_text(encoding="utf-8"))
    if signed.get("revision") != REVISION:
        fail(f"revision mismatch: {signed.get('revision')!r}")

    srows = signed["rows"]
    unsigned = [
        r["candidate_id"]
        for r in srows
        if not (
            r.get("final_decision")
            and r.get("reviewer")
            and r.get("decided_at")
            and r.get("decision_note")
        )
    ]
    if unsigned:
        fail(f"{len(unsigned)} row(s) lack a complete signature: {unsigned[:3]}")

    wave01 = json.loads(WAVE01_PUBLISHABLE.read_text(encoding="utf-8"))
    imported = [r for r in wave01["rows"] if r.get("rule_id") == CARVE_OUT_RULE_ID]
    if len(imported) != 1:
        fail(f"expected exactly one {CARVE_OUT_RULE_ID} row in the Wave-01 register")
    carve_out_row = dict(imported[0])
    carve_out_row["_imported_dependency"] = True
    carve_out_row["_imported_from_revision"] = IMPORTED_REVISION

    ids = [r["candidate_id"] for r in srows] + [carve_out_row["candidate_id"]]
    chain = fetch_chain(ids)
    missing = [i for i in ids if i not in chain]
    if missing:
        fail(f"{len(missing)} candidate(s) absent from the evidence chain: {missing[:3]}")

    rows = [build_row(sr, chain[sr["candidate_id"]]) for sr in srows]
    rows.append(carve_out_row)

    by_candidate = {r["candidate_id"]: r for r in rows}
    base_row = by_candidate.get(DISNEY_DOG_CANDIDATE)
    if base_row is None:
        fail(f"Disney dog base {DISNEY_DOG_CANDIDATE} missing from the register")

    # ---- exception plan: the one declared dependency -----------------------
    # Reachability is measured, never asserted: the same function the batch
    # refusals use decides whether the new dog base actually governs guide_dog.
    verdict = is_reachable_carveout(base_row, carve_out_row)
    same_layer = carve_out_row.get("rule_layer") == base_row.get("rule_layer")
    exception_plan = [
        {
            "rule_id": carve_out_row["rule_id"],
            "candidate_id": carve_out_row["candidate_id"],
            "place_name": carve_out_row.get("place_name"),
            "zone_name": carve_out_row.get("zone_name"),
            "layer": carve_out_row.get("rule_layer"),
            "effect": carve_out_row.get("effect"),
            "mandatory_level": carve_out_row.get("mandatory_level"),
            "source_scope_exact": carve_out_row.get("source_scope_exact"),
            "subject_scope_normalized": carve_out_row.get("subject_scope_normalized"),
            "normalization_type": carve_out_row.get("normalization_type"),
            "normative_effect": carve_out_row.get("normative_effect"),
            "source_id": carve_out_row.get("source_id"),
            "source_url": carve_out_row.get("source_url"),
            "issuer": carve_out_row.get("issuer"),
            "decision": carve_out_row.get("final_decision"),
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
            "imported_from_revision": IMPORTED_REVISION,
        }
    ]

    base_row["carve_out_of"] = [carve_out_row["rule_id"]]
    base_row["exception_binding_required"] = True
    base_row["reachable"] = verdict is True

    doc = {
        "_readme": (
            "Projected from docs/expansion/review_decisions_scope_remodel_r2.json by "
            "scripts/scope_remodel_r2_publish_register.py. Gate fields are derived from the "
            "live evidence chain using the canonical R2 derivations. The human signature "
            "(final_decision / reviewer / reviewed_at / review_note) is COPIED, never computed. "
            f"The row {CARVE_OUT_RULE_ID} is imported from revision {IMPORTED_REVISION} because "
            "the Disney dog prohibition has an approved guide-dog carve-out in that revision; "
            "without it the canonical batch validator cannot see the dependency and would "
            "silently ship a prohibition with its approved exception unpublished. Its signature "
            "is copied verbatim; the Wave-01 register is not modified."
        ),
        "revision": REVISION,
        "expansion_run_id": RUN_ID,
        "generated_at": datetime.now(UTC).isoformat(),
        "human_signoff_required": True,
        "human_decisions": list(HUMAN_DECISIONS),
        "imported_dependency_rows": [
            {
                "rule_id": carve_out_row["rule_id"],
                "candidate_id": carve_out_row["candidate_id"],
                "from_revision": IMPORTED_REVISION,
                "why": "Disney dog 禁令的唯一已批准导盲犬 carve-out，位于另一个 revision。",
            }
        ],
        "exception_plan": exception_plan,
        "exception_binding": {
            e["rule_id"]: {
                "bases": [b["rule_id"] for b in e["bases"] if b["same_layer"]],
                "cross_layer_dropped": e["cross_layer_dropped"],
            }
            for e in exception_plan
            if any(b["same_layer"] for b in e["bases"])
        },
        "normalization_semantics": signed.get("normalization_semantics"),
        "rows": rows,
    }

    out = Path(args.out)
    dist = Counter(r["final_decision"] for r in rows)
    print(f"revision        : {REVISION}")
    print(f"rows            : {len(rows)}  (6 signed + 1 imported dependency)")
    print(f"distribution    : {dict(dist)}")
    print(f"carve-out       : {CARVE_OUT_RULE_ID} -> {base_row['rule_id']}")
    print(f"carve-out reach : {verdict}")
    print(f"same layer      : {same_layer}")
    weak = sum(1 for r in rows if r["evidence_strength"] in {"search_snippet", "social_lead"})
    print(f"weak evidence   : {weak}")
    print(f"license problems: {sum(1 for r in rows if r['license_problems'])}")
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
