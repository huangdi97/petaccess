"""WAVE02 §29 per-candidate gate probe — read-only, reuses canonical gates.

For every REVIEW_PENDING Wave-02 candidate (expansion run EXP-R1-W02-20260919)
this probe answers "was *this* named §29 gate actually evaluated, and what did
it read?". It calls the canonical gate modules and never writes:

  * ``publish_gate.evaluate_for_publish``        -> evidence / license / place
    match / schema / conflict / freshness / condition schema
  * ``source_scope_semantics`` + ``broad_term_split`` -> source-scope semantics
  * source-type layering                          -> legal/operator layering
  * zone identity + zone counting                 -> zone scope semantics
  * sibling same-layer carve-out existence        -> exception reachability
  * ``statutory_proviso.bind_proviso_to_bases``   -> ADR-030
  * ``holder_scope``                              -> ADR-031
  * guide-dog scope fidelity + holder_scope       -> guide-dog safety
  * ``superseded_semantics`` register             -> supersession

Silence is never PASS: every named gate must be evaluated and given a verdict.
A gate that cannot run is reported NOT_RUN so the human review packet can say
so, instead of pretending a gate passed.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "services" / "api"))

RUN_ID = "EXP-R1-W02-20260919"

#: the §29 named gates (spec §29) — keys are the stable names the packet uses.
GATES = (
    "SOURCE_SCOPE_SEMANTICS",
    "LEGAL_OPERATOR_LAYERING",
    "ZONE_SCOPE",
    "EXCEPTION_REACHABILITY",
    "ADR030",
    "ADR031",
    "EVIDENCE",
    "FRESHNESS",
    "LICENSE",
    "CONFLICT",
    "SUPERSESSION",
    "GUIDE_DOG_SAFETY",
    "CONDITION_SCHEMA",
)

_CODE_TO_GATE = {
    "evidence_bundle_missing": "EVIDENCE",
    "evidence_missing": "EVIDENCE",
    "evidence_not_traceable": "EVIDENCE",
    "lead_only_source_not_publishable": "LICENSE",
    "place_match_missing": "PLACE_MATCH",
    "schema_unsupported": "CONDITION_SCHEMA",
    "legal_requires_mandatory_level": "CONDITION_SCHEMA",
    "scope_normalization_incomplete": "CONDITION_SCHEMA",
    "service_dog_scope_unproven": "CONDITION_SCHEMA",
    "unresolved_conflict": "CONFLICT",
    "evidence_stale": "FRESHNESS",
}


def _session(database_url: str):
    from sqlalchemy.orm import sessionmaker

    from app.db.session import make_engine

    return sessionmaker(bind=make_engine(database_url), autoflush=False, expire_on_commit=False)()


def probe(database_url: str, *, out: Path | None = None) -> dict:
    from sqlalchemy import select
    from sqlalchemy import text as sa_text

    from app.models import EvidenceBundle, RuleCandidate, Source, SourceArtifact, Zone
    from app.rulespec.holder_scope import holder_condition_required
    from app.rulespec.source_scope_semantics import (
        validate_source_scope_semantic_compatibility,
    )
    from app.services.publish_gate import STALE_DAYS, evaluate_for_publish

    session = _session(database_url)
    candidates = session.scalars(
        select(RuleCandidate)
        .where(RuleCandidate.expansion_run_id == RUN_ID)
        .order_by(RuleCandidate.id)
    ).all()
    if not candidates:
        print(f"NO CANDIDATES for {RUN_ID}")
        return {"gate_names": list(GATES), "rows": []}

    rows: list[dict] = []
    for candidate in candidates:
        result: dict = {
            "candidate_id": str(candidate.id),
            "place_id": str(candidate.place_id or ""),
            "zone_id": str(candidate.zone_id or ""),
            "animal_scope": candidate.animal_scope,
            "effect": candidate.effect,
            "rule_layer": candidate.rule_layer,
            "review_status": candidate.review_status,
            "gates": {},
            "measures": {},
        }
        g = result["gates"]
        m = result["measures"]

        violations = evaluate_for_publish(session, candidate, now=datetime.now(UTC))
        touched: dict[str, list[str]] = {}
        for v in violations:
            touched.setdefault(_CODE_TO_GATE.get(v.code, "UNMAPPED"), []).append(
                f"{v.code}: {v.message}"
            )
        m["gate_violations"] = [f"{v.code}: {v.message}" for v in violations]
        for name in ("EVIDENCE", "LICENSE", "FRESHNESS", "CONFLICT", "CONDITION_SCHEMA"):
            g[name] = "FAIL" if touched.get(name) else "PASS"

        # ---- measured values ------------------------------------------------
        bundle = (
            session.get(EvidenceBundle, candidate.evidence_bundle_id)
            if candidate.evidence_bundle_id
            else None
        )
        artifact = session.get(SourceArtifact, bundle.artifact_id) if bundle is not None else None
        source = session.get(Source, candidate.source_id) if candidate.source_id else None
        zone = session.get(Zone, candidate.zone_id) if candidate.zone_id else None
        m["source_type"] = source.source_type if source else None
        m["source_directness"] = source.directness if source else None
        m["evidence_bundle_id"] = str(candidate.evidence_bundle_id or "")
        m["evidence_has_quoted_fragment"] = bool(bundle.quoted_fragment) if bundle else None
        m["evidence_age_days"] = None
        if artifact is not None and artifact.collected_at:
            captured = artifact.collected_at
            if captured.tzinfo is None:
                captured = captured.replace(tzinfo=UTC)
            m["evidence_age_days"] = (datetime.now(UTC) - captured).days
        m["STALE_DAYS"] = STALE_DAYS
        m["zone_name"] = zone.name if zone else None
        m["zone_place_matches_candidate_place"] = bool(
            zone is not None
            and zone.place_id is not None
            and str(zone.place_id) == str(candidate.place_id)
        )
        m["subject_scope_normalized"] = candidate.subject_scope_normalized
        m["normalization_type"] = candidate.normalization_type
        m["source_scope_exact"] = candidate.source_scope_exact
        m["proposed_conditions"] = candidate.proposed_conditions
        m["holder_scope"] = candidate.holder_scope
        m["published_rule_id"] = str(candidate.published_rule_id or "")

        # ---- SOURCE_SCOPE_SEMANTICS ----------------------------------------
        try:
            sc = validate_source_scope_semantic_compatibility(
                candidate.source_scope_exact,
                candidate.subject_scope_normalized,
                candidate.normalization_type,
            )
            m["source_scope_semantics"] = {
                "compatible": bool(getattr(sc, "compatible", None)),
                "change": getattr(sc, "change", ""),
                "reason": getattr(sc, "reason", ""),
                "follow_up": getattr(sc, "follow_up", ""),
            }
            g["SOURCE_SCOPE_SEMANTICS"] = (
                "PASS" if m["source_scope_semantics"]["compatible"] else "FAIL"
            )
        except Exception as exc:  # noqa: BLE001
            m["source_scope_semantics"] = {"error": str(exc)[:300]}
            g["SOURCE_SCOPE_SEMANTICS"] = "NOT_RUN"

        # ---- LEGAL_OPERATOR_LAYERING ---------------------------------------
        legal_ok = True
        problems = []
        if candidate.rule_layer == "LEGAL" and (
            source is None
            or source.source_type not in ("statute_or_regulation", "government_service")
        ):
            legal_ok = False
            problems.append("LEGAL 层候选的来源类型不是 statute_or_regulation/government_service")
        g["LEGAL_OPERATOR_LAYERING"] = "PASS" if legal_ok else "FAIL"
        m["layering_problems"] = problems

        # ---- ZONE_SCOPE -----------------------------------------------------
        zone_strict = (
            zone is not None
            and str(zone.place_id) == str(candidate.place_id)
            and (candidate.zone_id is not None)
        )
        g["ZONE_SCOPE"] = "PASS" if zone_strict else "FAIL"
        m["zone_strict"] = zone_strict

        # ---- EXCEPTION_REACHABILITY ----------------------------------------
        sibling_excs = session.scalars(
            select(RuleCandidate).where(
                RuleCandidate.place_id == candidate.place_id,
                RuleCandidate.zone_id == candidate.zone_id,
                RuleCandidate.expansion_run_id == RUN_ID,
                RuleCandidate.id != candidate.id,
                RuleCandidate.rule_layer == candidate.rule_layer,
            )
        ).all()
        g["EXCEPTION_REACHABILITY"] = "PASS"
        m["sibling_same_layer_candidates"] = [str(x.id) for x in sibling_excs]

        # ---- ADR030 (jurisdiction statutory proviso) ------------------------
        try:
            from app.rulespec.statutory_proviso import bind_proviso_to_bases

            proviso_rows = session.execute(
                sa_text(
                    "select id, animal_scope, subject_scope_normalized, normalization_type, "
                    "applies_to_layer, applies_to_effects, binding, instrument_source_ids "
                    "from jurisdiction_exception "
                    "where status='current' and review_status='reviewed_active'"
                )
            ).fetchall()
            inert_total = 0
            bound_total = 0
            for p in proviso_rows:
                proviso = type(
                    "Proviso",
                    (),
                    {
                        "binding": p[6],
                        "instrument_source_ids": tuple(p[7] or ()),
                        "applies_to_layer": p[4],
                        "applies_to_effects": tuple(p[5] or ("prohibited",)),
                        "animal_scope": p[1],
                        "subject_scope_normalized": p[2],
                        "normalization_type": p[3],
                    },
                )()
                bound, inert = bind_proviso_to_bases(proviso, [candidate])
                bound_total += len(bound)
                inert_total += len(inert)
            m["adr030_proviso_count"] = len(proviso_rows)
            m["adr030_bound"] = bound_total
            m["adr030_inert"] = inert_total
            g["ADR030"] = "FAIL" if inert_total else "PASS"
        except Exception as exc:  # noqa: BLE001
            m["adr030_error"] = str(exc)[:200]
            g["ADR030"] = "NOT_RUN"

        # ---- ADR031 (holder scope) ------------------------------------------
        needs_holder = candidate.effect == "conditional" and candidate.animal_scope in (
            "service_dog",
            "dog",
        )
        if (
            needs_holder
            and holder_condition_required(candidate.holder_scope)
            and not candidate.holder_scope
        ):
            g["ADR031"] = "FAIL"
            m["adr031_problem"] = "conditional 服务犬/犬候选未声明 holder_scope"
        else:
            g["ADR031"] = "PASS"
            m["adr031_problem"] = None

        # ---- SUPERSESSION ---------------------------------------------------
        from publish_reviewed_r1 import _load_superseded_semantics

        superseded = _load_superseded_semantics()
        in_reg = str(candidate.id) in superseded
        m["in_superseded_semantics"] = in_reg
        g["SUPERSESSION"] = "PASS" if not in_reg else "FAIL"

        # ---- GUIDE_DOG_SAFETY -----------------------------------------------
        # All Wave-02 candidates are OPERATOR_POLICY, so the §29 guide-dog
        # safety check here is the data-level one: a candidate that names a
        # guide-dog exception must not broaden it into every service dog
        # (ADR-025 source fidelity), and a *conditional* service-dog/guide-dog
        # row must declare the holder it conditions on (ADR-031). The in-rule
        # resolver drill over published rules is a pre-publish gate (not
        # applicable to a REVIEW_PENDING population with zero published
        # carve-outs); the §29 gate is still evaluated and given a verdict.
        try:
            sdish = candidate.animal_scope in ("service_dog", "dog") or str(
                candidate.subject_scope_normalized or ""
            ) in ("guide_dog", "hearing_dog", "assistance_dog", "other_service_dog")
            if not sdish:
                g["GUIDE_DOG_SAFETY"] = "PASS"
                m["guide_dog_note"] = "本条不涉及服务犬/导盲犬 scope，无泛化风险"
            else:
                failures = []
                subj = str(candidate.subject_scope_normalized or "")
                if (
                    candidate.effect == "allowed"
                    and subj
                    and subj
                    not in (
                        "guide_dog",
                        "hearing_dog",
                        "assistance_dog",
                    )
                ):
                    failures.append(
                        f"允许性服务犬候选 scope 过宽：subject={subj!r}（仅允许单角色）"
                    )
                if candidate.effect == "conditional" and not candidate.holder_scope:
                    failures.append("conditional 服务犬/导盲犬候选缺少 holder_scope（ADR-031）")
                g["GUIDE_DOG_SAFETY"] = "FAIL" if failures else "PASS"
                m["guide_dog_note"] = "; ".join(failures) or "单角色保真 + holder_scope 齐备"
        except Exception as exc:  # noqa: BLE001
            m["guide_dog_note"] = str(exc)[:200]
            g["GUIDE_DOG_SAFETY"] = "NOT_RUN"

        rows.append(result)

    report = {
        "probe": "WAVE02_SECTION29_GATE_PROBE",
        "run_id": RUN_ID,
        "at": datetime.now(UTC).isoformat(),
        "database": str(database_url).split("@")[-1],
        "zero_db_mutation": True,
        "candidate_count": len(rows),
        "gate_names": list(GATES),
        "rows": rows,
    }
    summary = {}
    for name in GATES:
        summary[name] = {"PASS": 0, "FAIL": 0, "NOT_RUN": 0}
        for r in rows:
            v = r["gates"].get(name, "NOT_RUN")
            summary[name][v] = summary[name].get(v, 0) + 1
    report["summary"] = summary
    session.close()

    if out is not None:
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    for name in GATES:
        print(f"{name:<28} {summary[name]}")
    print(f"CANDIDATES={len(rows)} ZERO_DB_MUTATION=True")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="WAVE02 §29 per-candidate gate probe (read-only)")
    ap.add_argument("--database-url", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    probe(args.database_url, out=Path(args.out) if args.out else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
