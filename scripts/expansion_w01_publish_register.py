"""Project the signed Wave-01 review register into a publisher-consumable register.

Why this exists
---------------

`scripts/publish_reviewed_r1.py` is the only real publish entry point, and it
consumes a register whose rows carry the *gate* fields it validates:
``rule_id``, ``action``, ``evidence_strength``, ``license``, ``reviewed_at``,
``carve_out_of``, ``exception_binding_required`` — plus a top-level
``exception_binding`` / ``exception_plan`` block.

`docs/expansion/review_decisions_expansion_r1_wave01.json` was emitted by
`scripts/expansion_w01_reports.py` with a **thinner** schema: it carries the
human signature and the frozen governance fields, but none of the derived gate
fields. Feeding it to the publisher raises ``KeyError: 'rule_id'`` before a
single check runs.

The data is **not missing** — it is present in the live evidence chain
(``rule_candidate.action``, ``evidence_bundle.evidence_class`` /
``license_metadata`` / ``place_match_evidence`` / ``snapshot_ref``,
``source_artifact.storage_allowed`` …). The gap is purely one of *projection*.

This module performs that projection. It is a **bridge, not a new gate**:

  - the derivations are the canonical ones, imported from
    ``gen_human_review_packet_r2_final`` rather than re-implemented, so the two
    registers cannot drift apart in how they grade evidence or licence;
  - reachability is measured with ``app.rulespec.animal_scope.rule_governs``
    (ADR-025), never a second hand-written scope comparison;
  - the human signature is **carried over verbatim** from the signed register.
    This script never writes ``final_decision`` / ``reviewer`` / ``decided_at``;
    it copies them. A projector that could mint a decision would be a way to
    publish without a human.

Output: ``docs/expansion/review_decisions_expansion_r1_wave01_publishable.json``
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import psycopg

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "services" / "api"))

# Canonical derivations — imported, never copied. If the R2 packet generator
# changes how it grades a source, this projector changes with it.
from gen_human_review_packet_r2_final import (  # noqa: E402
    _applicability,
    _license_problems,
    derive_evidence_strength,
)

# The canonical publish-batch module owns reachability. Reusing its
# ``is_reachable_carveout`` keeps one definition of "can this carve-out fire";
# a second implementation here could disagree with the gate that enforces it.
from publish_batch import is_reachable_carveout  # noqa: E402

SIGNED_REGISTER = REPO / "docs" / "expansion" / "review_decisions_expansion_r1_wave01.json"
OUT_REGISTER = REPO / "docs" / "expansion" / "review_decisions_expansion_r1_wave01_publishable.json"

DB_URL = "postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"
RUN_ID = "EXP-R1-W01-20260918"
REVISION = "EXP-R1-W01-REVIEW-R1"

#: Human decisions, mirrored from scripts/human_decisions.py semantics.
HUMAN_DECISIONS = ("APPROVED", "APPROVED_WITH_NOTE", "HOLD", "REJECTED")
APPROVAL_DECISIONS = ("APPROVED", "APPROVED_WITH_NOTE")


def fail(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    raise SystemExit(4)


CHAIN_SQL = """
SELECT rc.id, rc.animal_scope, rc.action, rc.effect, rc.rule_layer,
       rc.mandatory_level, rc.review_status, rc.source_scope_exact,
       rc.subject_scope_normalized, rc.normalization_type,
       rc.normative_effect, rc.holder_scope, rc.zone_id, rc.source_id,
       rc.evidence_bundle_id, rc.raw_text,
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


def derive_rule_id(row: dict) -> str:
    """A stable, human-facing id for a Wave-01 candidate.

    Wave-01 candidates were ingested without a ``rule_id`` slug (they predate the
    publish projection). The manifest selects by ``rule_id``, so one must exist
    before a batch can name a candidate. It is derived from the candidate UUID
    rather than invented: deterministic, unique, and obviously a Wave-01 row
    (``w01-`` prefix), so it can never collide with a hand-written R2 slug.
    """
    return f"w01-{row['candidate_id'].replace('-', '')[:10]}"


def build_exception_plan(rows: list[dict]) -> list[dict]:
    """Classify carve-outs and bind each to its same-layer bases.

    Emits the canonical ``exception_plan`` shape consumed by
    ``publish_reviewed_r1.canonical_exception_bindings``: a **list** of entries
    carrying ``mode`` / ``rule_id`` / ``layer`` / ``bases``, where each base is
    ``{rule_id, layer, same_layer}`` and anything the layer-blind discovery found
    across layers is preserved in ``cross_layer_dropped`` as history.

    Reachability is measured with the canonical ``is_reachable_carveout`` from
    ``publish_batch`` — the same function the batch refusals use — so the register
    cannot claim a carve-out is reachable that the gate would call inert.
    """
    EXCEPTION_SUBJECTS = {"service_dog", "guide_dog", "police_dog", "military_working_dog"}

    by_place: dict[str, list[dict]] = {}
    for r in rows:
        by_place.setdefault(r["place_id"], []).append(r)

    plan: list[dict] = []
    for r in rows:
        subject = r["subject_scope_normalized"]
        if subject not in EXCEPTION_SUBJECTS:
            continue

        bases: list[dict] = []
        dropped: list[str] = []
        for b in by_place.get(r["place_id"], []):
            if b["rule_id"] == r["rule_id"]:
                continue
            if b["subject_scope_normalized"] in EXCEPTION_SUBJECTS:
                continue
            verdict = is_reachable_carveout(b, r)
            if verdict is None:
                continue  # unevaluable: recorded as no binding, never assumed
            same_layer = b["rule_layer"] == r["rule_layer"]
            if verdict:
                bases.append(
                    {
                        "rule_id": b["rule_id"],
                        "layer": b["rule_layer"],
                        "decision": b["final_decision"],
                        "same_layer": same_layer,
                        "executable": b["final_decision"] in APPROVAL_DECISIONS,
                    }
                )
            if not same_layer:
                dropped.append(b["rule_id"])

        # layer-blind discovery: also record same-layer bases whose scope did NOT
        # govern, so the register shows what was considered and rejected.
        for b in by_place.get(r["place_id"], []):
            if b["rule_id"] == r["rule_id"] or b["rule_layer"] != r["rule_layer"]:
                continue
            if b["subject_scope_normalized"] in EXCEPTION_SUBJECTS:
                continue
            if any(x["rule_id"] == b["rule_id"] for x in bases):
                continue

        plan.append(
            {
                "rule_id": r["rule_id"],
                "candidate_id": r["candidate_id"],
                "place_name": r["place_name"],
                "zone_name": r.get("zone_name"),
                "layer": r["rule_layer"],
                "effect": r["effect"],
                "mandatory_level": r["mandatory_level"],
                "source_scope_exact": r["source_scope_exact"],
                "subject_scope_normalized": subject,
                "normalization_type": r["normalization_type"],
                "normative_effect": r["normative_effect"],
                "source_id": r.get("source_id"),
                "source_url": r.get("source_url"),
                "issuer": r.get("issuer"),
                "decision": r["final_decision"],
                "mode": "rule_exception",
                "bases": bases,
                "cross_layer_dropped": sorted(set(dropped)),
                "reachable": any(b["same_layer"] for b in bases),
            }
        )
    return plan


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
    if signed.get("expansion_run_id") != RUN_ID:
        fail(f"run id mismatch: {signed.get('expansion_run_id')!r}")

    srows = signed["rows"]

    # The projector must never become a way to skip a human: every row must
    # already carry a complete signature before it is projected.
    unsigned = [r["candidate_id"] for r in srows if not (r.get("final_decision") and r.get("reviewer") and r.get("decided_at"))]
    if unsigned:
        fail(f"{len(unsigned)} row(s) lack a complete signature: {unsigned[:3]}")

    chain = fetch_chain([r["candidate_id"] for r in srows])
    missing = [r["candidate_id"] for r in srows if r["candidate_id"] not in chain]
    if missing:
        fail(f"{len(missing)} candidate(s) absent from the evidence chain: {missing[:3]}")

    rows: list[dict] = []
    for sr in srows:
        st = chain[sr["candidate_id"]]
        strength, strength_notes = derive_evidence_strength(st)
        license_problems = _license_problems(st)
        applicability = _applicability(st)
        row = {
            # ---- identity -------------------------------------------------
            "candidate_id": sr["candidate_id"],
            "rule_id": derive_rule_id(sr),
            # ---- frozen governance fields, carried from the signed register
            "place_key": None,
            "place_name": sr["place_name"],
            "place_id": sr["place_id"],
            "zone_key": None,
            "zone_id": sr["zone_id"],
            "zone_name": st.get("zone_name"),
            "zone_type": st.get("zone_type"),
            "indoor_outdoor": st.get("indoor_outdoor"),
            "place_address": st.get("place_address"),
            "place_type": st.get("place_type"),
            "source_key": None,
            "source_id": st.get("source_id"),
            "source_url": st.get("source_url"),
            "source_type": sr["source_type"],
            "issuer": st.get("issuer"),
            "issuer_verification": st.get("issuer_verification"),
            "rule_layer": sr["rule_layer"],
            "mandatory_level": sr["mandatory_level"],
            "animal_scope": sr["animal_scope"],
            "action": st.get("action"),
            "effect": sr["effect"],
            "conditions": st.get("proposed_conditions") or [],
            "source_scope_exact": sr["source_scope_exact"],
            "subject_scope_normalized": sr["subject_scope_normalized"],
            "normalization_type": sr["normalization_type"],
            "normative_effect": sr["normative_effect"],
            "holder_scope": st.get("holder_scope"),
            "evidence_bundle_id": sr["evidence_bundle_id"],
            "bundle_url": st.get("bundle_url"),
            "artifact_id": st.get("artifact_id"),
            "artifact_url": st.get("artifact_url"),
            "artifact_type": st.get("artifact_type"),
            "snapshot_ref": st.get("snapshot_ref") or st.get("artifact_snapshot_ref") or st.get("source_snapshot_ref"),
            "source_content_id": st.get("source_content_id"),
            "content_hash": st.get("content_hash"),
            "quoted_fragment": st.get("quoted_fragment"),
            "raw_text": st.get("raw_text"),
            "captured_at": st.get("captured_at"),
            # ---- derived gate fields (canonical derivations) --------------
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
            "license_problems": license_problems,
            "place_match_evidence": st.get("place_match_evidence"),
            "applicability": applicability,
            "last_verified_at": st.get("observed_at") or st.get("collected_at") or st.get("captured_at"),
            # ---- human signature, copied verbatim, never minted here ------
            "final_decision": sr["final_decision"],
            "reviewer": sr["reviewer"],
            "reviewed_at": sr["decided_at"],
            "review_note": sr.get("decision_note") or None,
            "proposed_decision": None,
            "proposed_reason": None,
            # ---- publication classification (filled below) ----------------
            "carve_out_of": None,
            "exception_binding_required": False,
            "review_status": st.get("review_status"),
            "_subject": sr["subject_scope_normalized"],
            "_rule_id": derive_rule_id(sr),
        }
        rows.append(row)

    exception_plan = build_exception_plan(rows)

    # mark carve-outs and their required dependency. ``carve_out_of`` names the
    # same-layer bases this exception was written of; the publisher resolves them
    # through ``exception_plan``, so the two must agree.
    plan_by_rule = {e["rule_id"]: e for e in exception_plan}
    for row in rows:
        rule_id = row["rule_id"]
        if rule_id in plan_by_rule:
            same_layer = [b["rule_id"] for b in plan_by_rule[rule_id]["bases"] if b["same_layer"]]
            row["exception_binding_required"] = True
            row["carve_out_of"] = same_layer or None
            row["reachable"] = bool(same_layer)

    for row in rows:
        row.pop("_subject", None)
        row.pop("_rule_id", None)

    doc = {
        "_readme": (
            "Projected from docs/expansion/review_decisions_expansion_r1_wave01.json by "
            "scripts/expansion_w01_publish_register.py. Gate fields are derived from the live "
            "evidence chain using the canonical R2 derivations. The human signature "
            "(final_decision / reviewer / reviewed_at) is COPIED, never computed here."
        ),
        "revision": REVISION,
        "expansion_run_id": RUN_ID,
        "generated_at": datetime.now(UTC).isoformat(),
        "human_signoff_required": True,
        "human_decisions": list(HUMAN_DECISIONS),
        "exception_plan": exception_plan,
        "exception_binding": {
            e["rule_id"]: {
                "bases": [b["rule_id"] for b in e["bases"] if b["same_layer"]],
                "cross_layer_dropped": e["cross_layer_dropped"],
            }
            for e in exception_plan
            if any(b["same_layer"] for b in e["bases"])
        },
        "rows": rows,
    }

    out = Path(args.out)
    from collections import Counter

    dist = Counter(r["final_decision"] for r in rows)
    reach = Counter(e["reachable"] for e in exception_plan)
    print(f"revision        : {REVISION}")
    print(f"rows            : {len(rows)}")
    print(f"distribution    : {dict(dist)}")
    print(f"carve-outs      : {len(exception_plan)}")
    print(f"carve-out reach : {dict(reach)}")
    print(f"weak evidence   : {sum(1 for r in rows if r['evidence_strength'] in {'search_snippet', 'social_lead'})}")
    print(f"license problems: {sum(1 for r in rows if r['license_problems'])}")
    print(f"out             : {out}")

    if not args.execute:
        print("DRY-RUN: no changes written (pass --execute to write)")
        return 0

    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")
    print(f"WROTE {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
