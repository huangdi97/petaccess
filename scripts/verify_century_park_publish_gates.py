"""Per-gate pre-publish probe for the Century Park single-row batch.

Why this exists
---------------
`publish_reviewed_r1.py --dry-run` prints one aggregate verdict per row
(`gate_result = PASS`). That is the right thing for the publisher to print, but
it is not enough to answer a reviewer who asks "was *this* named gate actually
evaluated, and what value did it read?".

This script answers that question **without adding a second gate**. It calls the
canonical `app.services.publish_gate.evaluate_for_publish`, the canonical
`evidence_acceptance` module and the canonical `publish_batch` loader, and then
maps their *existing* violation codes onto the twelve named gates. It is
read-only: no session.commit(), no DML, no audit event.

A gate that was not evaluated reports NOT_RUN. Silence is never PASS.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "services" / "api"))

GATES = (
    "HUMAN_DECISION",
    "EVIDENCE",
    "HUMAN_EVIDENCE_ACCEPTANCE",
    "SOURCE_IDENTITY",
    "SOURCE_DRIFT",
    "FRESHNESS",
    "LICENSE",
    "PLACE_MATCH",
    "SCHEMA",
    "CONFLICT",
    "SUPERSESSION",
    "EXECUTION_CONTRACT",
)

#: canonical violation code -> the named gate it is evidence for.
_CODE_TO_GATE = {
    "evidence_bundle_missing": "EVIDENCE",
    "evidence_missing": "EVIDENCE",
    "evidence_not_traceable": "EVIDENCE",
    "lead_only_source_not_publishable": "LICENSE",
    "place_match_missing": "PLACE_MATCH",
    "schema_unsupported": "SCHEMA",
    "legal_requires_mandatory_level": "SCHEMA",
    "scope_normalization_incomplete": "SCHEMA",
    "service_dog_scope_unproven": "SCHEMA",
    "unresolved_conflict": "CONFLICT",
    "evidence_stale": "FRESHNESS",
}


def _session(database_url: str):
    from sqlalchemy.orm import sessionmaker

    from app.db.session import make_engine

    return sessionmaker(bind=make_engine(database_url), autoflush=False, expire_on_commit=False)()


def _register_row(registry: Path, rule_id: str) -> dict[str, Any]:
    doc = json.loads(registry.read_text(encoding="utf-8"))
    for row in doc.get("rows") or []:
        if str(row.get("rule_id")) == rule_id:
            return row
    raise SystemExit(f"登记表中找不到 {rule_id}")


def probe(
    *,
    database_url: str,
    batch_file: Path,
    registry: Path,
    acceptance_file: Path | None,
    dry_run_json: Path | None = None,
) -> dict[str, Any]:
    import evidence_acceptance as ea
    from publish_batch import load_manifest
    from publish_reviewed_r1 import _source_rows

    from app.models import EvidenceBundle, RuleCandidate, Source, SourceArtifact, Zone
    from app.services.publish_gate import STALE_DAYS, evaluate_for_publish

    manifest = load_manifest(batch_file)
    rule_ids = [str(x) for x in manifest.rule_ids]
    session = _session(database_url)

    # ---- EXECUTION_CONTRACT ------------------------------------------------
    # Taken from the *publisher's own* dry-run verdict rather than re-wired here:
    # `validate_manifest` needs DB-derived inputs (published ids, approved
    # exception map, bindings) whose assembly lives in the publisher. Re-deriving
    # them would be a second gate wearing this file's name.
    contract: dict[str, Any] = {"source": "manifest load only"}
    if dry_run_json is not None and Path(dry_run_json).exists():
        raw = Path(dry_run_json).read_text(encoding="utf-8")
        doc = json.loads(raw[raw.find("{") :])
        contract = {
            "source": str(dry_run_json),
            "batch": doc.get("summary", {}).get("batch"),
            "preflight_problems": doc.get("summary", {}).get("preflight_problems"),
            "integrity": doc.get("integrity"),
            "DRY_RUN_ZERO_DB_MUTATION": doc.get("summary", {}).get("DRY_RUN_ZERO_DB_MUTATION"),
            "selection": doc.get("summary", {}).get("selection"),
        }

    acceptances = ea.load_acceptances(acceptance_file) if acceptance_file is not None else {}

    rows: list[dict[str, Any]] = []
    for rule_id in rule_ids:
        row = _register_row(registry, rule_id)
        candidate_id = str(row["candidate_id"])
        candidate = session.get(RuleCandidate, candidate_id)

        result: dict[str, Any] = {
            "rule_id": rule_id,
            "candidate_id": candidate_id,
            "gates": {},
            "measures": {},
        }
        g = result["gates"]
        m = result["measures"]

        # ---- 1. HUMAN_DECISION ---------------------------------------------
        m["human_final_decision"] = row.get("final_decision")
        m["human_reviewer"] = row.get("reviewer")
        m["human_reviewed_at"] = row.get("reviewed_at")
        m["human_decision_note"] = row.get("decision_note")
        g["HUMAN_DECISION"] = (
            "PASS"
            if str(row.get("final_decision")) in {"APPROVED", "APPROVED_WITH_NOTE"}
            else "FAIL"
        )

        # ---- 2..5. canonical gate ------------------------------------------
        if candidate is None:
            for name in ("EVIDENCE", "LICENSE", "PLACE_MATCH", "SCHEMA", "CONFLICT", "FRESHNESS"):
                g[name] = "NOT_RUN"
            m["gate_note"] = "库中不存在该候选"
            rows.append(result)
            continue

        violations = evaluate_for_publish(session, candidate, now=datetime.now(UTC))
        touched: dict[str, list[str]] = {}
        for v in violations:
            touched.setdefault(_CODE_TO_GATE.get(v.code, "UNMAPPED"), []).append(
                f"{v.code}: {v.message}"
            )
        m["gate_violations"] = [f"{v.code}: {v.message}" for v in violations]
        for name in ("EVIDENCE", "LICENSE", "PLACE_MATCH", "SCHEMA", "CONFLICT", "FRESHNESS"):
            g[name] = "FAIL" if touched.get(name) else "PASS"

        # ---- measured values behind those verdicts -------------------------
        bundle = (
            session.get(EvidenceBundle, candidate.evidence_bundle_id)
            if candidate.evidence_bundle_id
            else None
        )
        artifact = session.get(SourceArtifact, bundle.artifact_id) if bundle is not None else None
        m["evidence_bundle_id"] = str(candidate.evidence_bundle_id or "")
        m["evidence_bundle_quoted_fragment"] = bool(bundle.quoted_fragment) if bundle else None
        m["evidence_bundle_content_hash"] = bundle.content_hash if bundle else None
        m["evidence_artifact_content_hash"] = artifact.content_hash if artifact else None
        m["evidence_artifact_collected_at"] = (
            artifact.collected_at.isoformat()
            if artifact is not None and artifact.collected_at
            else None
        )
        m["evidence_artifact_storage_allowed"] = (
            artifact.storage_allowed if artifact is not None else None
        )
        m["STALE_DAYS"] = STALE_DAYS
        if artifact is not None and artifact.collected_at:
            captured = artifact.collected_at
            if captured.tzinfo is None:
                captured = captured.replace(tzinfo=UTC)
            m["evidence_age_days"] = (datetime.now(UTC) - captured).days
        else:
            m["evidence_age_days"] = None

        source = session.get(Source, candidate.source_id) if candidate.source_id else None
        m["source_id"] = str(candidate.source_id or "")
        m["source_type"] = source.source_type if source else None
        m["source_issuer"] = source.issuer if source else None
        m["source_directness"] = source.directness if source else None
        m["source_availability"] = source.source_availability if source else None
        m["source_issuer_verification"] = source.issuer_verification if source else None
        m["source_notes"] = source.notes if source else None
        m["source_url"] = source.source_url if source else None
        m["artifact_evidence_strength"] = artifact.evidence_strength if artifact else None

        # ---- SOURCE_IDENTITY ------------------------------------------------
        g["SOURCE_IDENTITY"] = (
            "PASS"
            if source is not None and source.source_type == "government_service" and source.issuer
            else "FAIL"
        )

        # ---- PLACE_MATCH measures -------------------------------------------
        zone = session.get(Zone, candidate.zone_id) if candidate.zone_id else None
        m["candidate_place_id"] = str(candidate.place_id or "")
        m["candidate_zone_id"] = str(candidate.zone_id or "")
        m["zone_name"] = zone.name if zone else None
        m["zone_place_matches_candidate_place"] = bool(
            zone is not None and str(zone.place_id) == str(candidate.place_id)
        )
        m["evidence_place_match_evidence"] = (
            bundle.place_match_evidence if bundle is not None else None
        )

        # ---- SCHEMA measures -------------------------------------------------
        m["animal_scope"] = candidate.animal_scope
        m["action"] = candidate.action
        m["effect"] = candidate.effect
        m["rule_layer"] = candidate.rule_layer
        m["mandatory_level"] = candidate.mandatory_level
        m["proposed_conditions"] = candidate.proposed_conditions
        m["subject_scope_normalized"] = candidate.subject_scope_normalized
        m["normalization_type"] = candidate.normalization_type
        m["review_status"] = candidate.review_status
        m["published_rule_id"] = str(candidate.published_rule_id or "")

        # ---- 3. HUMAN_EVIDENCE_ACCEPTANCE + 5. SOURCE_DRIFT ------------------
        entry = acceptances.get(rule_id)
        if entry is None:
            g["HUMAN_EVIDENCE_ACCEPTANCE"] = "NOT_APPLICABLE"
            g["SOURCE_DRIFT"] = "NOT_APPLICABLE"
            m["acceptance"] = None
        else:
            source_rows = _source_rows(session, [entry])
            problems = ea.acceptance_problems(entry, source_rows.get(str(entry["source_id"])))
            m["acceptance"] = {
                "acceptance_id": entry.get("acceptance_id"),
                "reviewer": entry.get("reviewer"),
                "decided_at": entry.get("decided_at"),
                "declared_source_type": entry.get("declared_source_type"),
                "declared_source_type_semantics": entry.get("declared_source_type_semantics"),
                "accepted_despite_evidence_strength": entry.get(
                    "accepted_despite_evidence_strength"
                ),
                "operator_first_party_verified": entry.get("operator_first_party_verified"),
                "first_party_operator_source_pending": entry.get(
                    "first_party_operator_source_pending"
                ),
                "forbidden_claims": entry.get("forbidden_claims"),
                "file": entry.get("_file"),
                "structural_problems": ea.validate_acceptance_record(entry),
                "drift_problems": problems,
                "released": not ea.validate_acceptance_record(entry) and not problems,
            }
            g["HUMAN_EVIDENCE_ACCEPTANCE"] = "PASS" if m["acceptance"]["released"] else "FAIL"
            g["SOURCE_DRIFT"] = "PASS" if not problems else "FAIL"

        # ---- 11. SUPERSESSION ------------------------------------------------
        from publish_reviewed_r1 import _load_superseded_semantics, _supersede_targets

        superseded = _load_superseded_semantics()
        targets = _supersede_targets(row)
        m["plan_supersedes"] = list(targets)
        m["in_superseded_semantics"] = rule_id in superseded
        m["publication_type_expected"] = (
            "CREATE_ACCESS_RULE" if not targets and rule_id not in superseded else "UNEXPECTED"
        )
        g["SUPERSESSION"] = "PASS" if not targets and rule_id not in superseded else "FAIL"
        rows.append(result)

    # ---- EXECUTION_CONTRACT = publisher verdict + per-row publication type --
    publication_types = {}
    for r in rows:
        publication_types[r["rule_id"]] = r["measures"].get("publication_type_expected")
    batch = contract.get("batch") or {}
    integrity = contract.get("integrity") or {}
    contract_ok = (
        not contract.get("preflight_problems")
        and not (integrity.get("SELECTED_BUT_BLOCKED") or 0)
        and bool(batch.get("dependency_closed"))
        and publication_types
        and all(v == "CREATE_ACCESS_RULE" for v in publication_types.values())
    )
    g_contract = "PASS" if contract_ok else "FAIL"

    session.close()
    return {
        "probe": "CENTURY_PARK_PRE_PUBLISH_PER_GATE_PROBE",
        "at": datetime.now(UTC).isoformat(),
        "database_url": database_url,
        "batch_file": str(batch_file),
        "batch_id": manifest.batch_id,
        "batch_revision": manifest.revision,
        "batch_reviewer": manifest.reviewer,
        "batch_size": manifest.size,
        "registry": str(registry),
        "acceptance_file": str(acceptance_file) if acceptance_file else None,
        "execution_contract_evidence": contract,
        "publication_types": publication_types,
        "EXECUTION_CONTRACT": g_contract,
        "rows": rows,
        "gate_names": list(GATES),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--database-url", required=True)
    ap.add_argument("--batch-file", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--evidence-acceptance")
    ap.add_argument(
        "--dry-run-json", help="发布器 --dry-run --json 的输出；EXECUTION_CONTRACT 取自它"
    )
    ap.add_argument("--out")
    args = ap.parse_args()

    report = probe(
        database_url=args.database_url,
        batch_file=Path(args.batch_file),
        registry=Path(args.registry),
        acceptance_file=Path(args.evidence_acceptance) if args.evidence_acceptance else None,
        dry_run_json=Path(args.dry_run_json) if args.dry_run_json else None,
    )

    if args.out:
        Path(args.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    for row in report["rows"]:
        print(f"=== {row['rule_id']}  ({row['candidate_id']}) ===")
        for name in GATES:
            print(f"  {name:<28} = {row['gates'].get(name, '(n/a)')}")
        print(f"  SUPERSESSION_TARGETS         = {row['measures'].get('plan_supersedes')}")
        print(
            f"  PUBLICATION_TYPE             = {row['measures'].get('publication_type_expected')}"
        )
    print(f"  EXECUTION_CONTRACT           = {report['EXECUTION_CONTRACT']}")
    contract_evidence = json.dumps(report["execution_contract_evidence"], ensure_ascii=False)
    print(f"  EXECUTION_CONTRACT_EVIDENCE  = {contract_evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
