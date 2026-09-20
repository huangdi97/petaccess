"""30_50_PLACE_EXPANSION_R1 — WAVE_02 ingest (authorized metadata write).

Walks the SAME canonical evidence chain as Wave-01 through the LIVE API
(DataSourceJob -> Source -> SourceArtifact -> EvidenceBundle ->
RuleCandidate / ObservationCandidate, all REVIEW_PENDING). The chain-wiring
helpers are imported from ``expansion_w01_ingest`` so there is exactly one
implementation of the wire contract.

Wave-02 differs from Wave-01 in three deliberate ways:

1. **Real coordinates.** Every Wave-02 place carries ``geo.location_wkt`` from
   OpenStreetMap Nominatim (ODbL) with full provenance (osm_type/osm_id/
   display_name/licence/query/fetch time) in the evidence file. Wave-01
   deliberately wrote no coordinates; Wave-02's whole point is real geo.
2. **A fresh run id / revision** (``EXP-R1-W02-20260919`` /
   ``EXP-R1-W02-REVIEW-R1``) so the audit trail is never mixed with Wave-01.
3. **Wave-02 monitor keys** come from the evidence file, not a hard-coded set.

Hard rules (spec §2, §3, §39, §41):
  * every write is attributable to one DataSourceJob carrying
    ``expansion_run_id``;
  * candidates get a deterministic ``dedup_key`` so re-runs are idempotent;
  * NOTHING is approved, published, or given a human ``final_decision``;
  * no raw SQL, no INSERT-then-backfill: everything goes through the API;
  * no Rule / Exception / supersede / publish rows are written here — this is
    metadata + REVIEW_PENDING candidates only.

Usage::

    python scripts/expansion_w02_ingest.py --dry-run
    python scripts/expansion_w02_ingest.py
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

from expansion_w01_ingest import (  # noqa: E402  # noqa: E402
    FRESHNESS_BY_SOURCE_TYPE,
    Api,
    _dedup_key,
    ensure_artifact,
    ensure_bundle,
    ensure_source,
    find_place,
    login,
)

EVIDENCE_PATH = REPO / "docs" / "expansion" / "expansion_r1_wave02_evidence.json"
MANIFEST_PATH = REPO / "docs" / "expansion" / "expansion_r1_wave02_manifest.json"

RUN_ID = "EXP-R1-W02-20260919"
REVISION = "EXP-R1-W02-REVIEW-R1"
WAVE = "WAVE_02"
JURISDICTION = "上海市"

_MANIFEST_KEYS = (
    "run",
    "places",
    "zones",
    "sources",
    "artifacts",
    "bundles",
    "rule_candidates",
    "observation_candidates",
    "monitors",
    "freshness_policies",
)


def run(evidence_path: Path, dry_run: bool) -> int:
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    captured_at = evidence["captured_at"]

    manifest: dict = (
        json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if MANIFEST_PATH.exists()
        else {k: {} for k in _MANIFEST_KEYS}
    )
    for k in _MANIFEST_KEYS:
        manifest.setdefault(k, {})

    #: monitorable source keys are part of the evidence artifact (spec §28)
    MONITORABLE_SOURCE_KEYS = set(evidence.get("monitorable_source_keys", []))

    if dry_run:
        plan = {
            "expansion_run_id": RUN_ID,
            "review_revision": REVISION,
            "places": [p["key"] for p in evidence["places"]],
            "rules": sum(len(p["rules"]) for p in evidence["places"]),
            "monitorable_sources": len(MONITORABLE_SOURCE_KEYS),
            "geo_provided": sum(
                1 for p in evidence["places"] if p.get("geo", {}).get("location_wkt")
            ),
        }
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    token = login()
    api = Api(token)
    counts = {
        "places": 0,
        "zones": 0,
        "sources": 0,
        "artifacts": 0,
        "bundles": 0,
        "rule_candidates": 0,
        "observation_candidates": 0,
        "transitions": 0,
        "monitors": 0,
        "freshness_policies": 0,
        "freshness_assignments": 0,
    }

    # ---- DataSourceJob: one bounded, auditable production run (spec §39) ----
    job = api.post(
        "/api/v1/admin/data-source-jobs",
        {
            "job_type": "expansion_wave02",
            "target": "SHANGHAI_30_50_EXPANSION_WAVE02",
            "expansion_run_id": RUN_ID,
            "params": {
                "revision": REVISION,
                "wave": WAVE,
                "jurisdiction": JURISDICTION,
                "captured_at": captured_at,
            },
        },
    )
    manifest["run"] = {
        "expansion_run_id": RUN_ID,
        "review_revision": REVISION,
        "data_source_job_id": job.get("id"),
    }

    # ---- shared sources (e.g. the municipal park rules) ---------------------
    shared_sources: dict[str, str] = {}
    for sdata in evidence.get("shared_sources", []):
        skey = f"shared:{sdata['key']}"
        sid = manifest["sources"].get(skey)
        if not sid:
            sid = ensure_source(api, sdata, captured_at=captured_at, counts=counts)
            manifest["sources"][skey] = sid
        shared_sources[skey] = sid
        aid = ensure_artifact(
            api,
            source_id=sid,
            sdata=sdata,
            excerpt=sdata["excerpt"],
            run_id=RUN_ID,
            manifest=manifest,
            mkey=f"{skey}:artifact",
            counts=counts,
        )
        used = sorted(
            {
                r["fragment"]
                for p in evidence["places"]
                for r in p["rules"]
                if r["source_key"] == skey and r["fragment"] in sdata.get("fragments", {})
            }
        )
        for frag in used:
            bkey = f"{skey}:bundle:{frag}"
            if bkey in manifest["bundles"]:
                continue
            ensure_bundle(
                api,
                artifact_id=aid,
                quoted=sdata["fragments"][frag],
                extracted=json.dumps({"fragment_key": frag}, ensure_ascii=False),
                run_id=RUN_ID,
                place_match={
                    "matched_by": "statutory_applicability_by_place_type",
                    "note": "行政区级/市级规范性文件适用于本市公园类型场所；逐场所适用性由人工复核",
                },
                temporal={"published_at": sdata.get("published_at"), "captured_at": captured_at},
                privacy=None,
                manifest=manifest,
                mkey=bkey,
                counts=counts,
            )

    # ---- freshness policies (spec §34) -------------------------------------
    for stype, days in FRESHNESS_BY_SOURCE_TYPE.items():
        fkey = f"policy:{stype}"
        if fkey not in manifest["freshness_policies"]:
            created = api.post(
                "/api/v1/admin/freshness-policies",
                {
                    "name": f"wave02-{stype}-{days}d",
                    "review_interval_days": days,
                    "description": f"Wave02 默认复核周期：{stype} 每 {days} 天",
                },
            )
            manifest["freshness_policies"][fkey] = created["id"]
            counts["freshness_policies"] += 1

    # ---- places -------------------------------------------------------------
    for pdata in evidence["places"]:
        pkey = pdata["key"]

        place_id = manifest["places"].get(pkey)
        if not place_id:
            found = find_place(api, pdata["canonical_name"])
            place_id = found["id"] if found else None
        if not place_id:
            location_wkt = pdata.get("geo", {}).get("location_wkt")
            created = api.post(
                "/api/v1/places",
                {
                    "canonical_name": pdata["canonical_name"],
                    "place_type": pdata["place_type"],
                    "canonical_address": pdata["canonical_address"],
                    # Real coordinate backed by OSM provenance in the evidence
                    # file (spec §20: never mock geo, never a guessed point).
                    "location_wkt": location_wkt,
                },
            )
            place_id = created["id"]
            counts["places"] += 1
        manifest["places"][pkey] = place_id

        if pdata.get("aliases"):
            try:
                api.patch(f"/api/v1/places/{place_id}", {"alias_names": pdata["aliases"]})
            except RuntimeError as exc:
                print(f"[warn] alias patch failed for {pkey}: {exc}", file=sys.stderr)

        # ---- zones ----------------------------------------------------------
        zone_ids: dict[str, str | None] = {}
        existing = api.get(f"/api/v1/places/{place_id}/zones")
        rows = existing.get("items", []) if isinstance(existing, dict) else existing
        by_name = {z["name"]: z["id"] for z in rows if isinstance(z, dict)}
        for z in pdata["zones"]:
            zkey = f"{pkey}:{z['key']}"
            zid = manifest["zones"].get(zkey) or by_name.get(z["name"])
            if not zid:
                created = api.post(
                    "/api/v1/zones",
                    {
                        "place_id": place_id,
                        "name": z["name"],
                        "zone_type": z["zone_type"],
                        "indoor_outdoor": z["indoor_outdoor"],
                    },
                )
                zid = created["id"]
                counts["zones"] += 1
            manifest["zones"][zkey] = zid
            zone_ids[z["key"]] = zid

        # ---- place-level sources --------------------------------------------
        bundle_for_rule: dict[tuple[str, str], str] = {}
        for sdata in pdata["sources"]:
            skey = f"{pkey}:{sdata['key']}"
            sid = manifest["sources"].get(skey)
            if not sid:
                sid = ensure_source(api, sdata, captured_at=captured_at, counts=counts)
                manifest["sources"][skey] = sid

            aid = ensure_artifact(
                api,
                source_id=sid,
                sdata=sdata,
                excerpt=sdata["excerpt"],
                run_id=RUN_ID,
                manifest=manifest,
                mkey=f"{skey}:artifact",
                counts=counts,
            )

            used = sorted(
                {r["fragment"] for r in pdata["rules"] if r["source_key"] == sdata["key"]}
            )
            for frag in used:
                bkey = f"{skey}:bundle:{frag}"
                frags = sdata.get("fragments", {})
                quoted = frags.get(frag, sdata["excerpt"])
                rule_ids = sorted(
                    r["rule_id"]
                    for r in pdata["rules"]
                    if r["source_key"] == sdata["key"] and r["fragment"] == frag
                )
                bid = ensure_bundle(
                    api,
                    artifact_id=aid,
                    quoted=quoted,
                    extracted=json.dumps(
                        {"fragment_key": frag, "rule_ids": rule_ids}, ensure_ascii=False
                    ),
                    run_id=RUN_ID,
                    place_match=pdata["place_match_evidence"],
                    temporal={
                        "published_at": sdata.get("published_at"),
                        "captured_at": captured_at,
                    },
                    privacy=(
                        None
                        if sdata["storage_allowed"]
                        else "lead-only: 第三方/社媒内容，除摘录外不留存"
                    ),
                    manifest=manifest,
                    mkey=bkey,
                    counts=counts,
                )
                bundle_for_rule[(sdata["key"], frag)] = bid

            # ---- freshness assignment (100% coverage target, spec §35) ------
            policy_key = f"policy:{sdata['source_type']}"
            policy_id = manifest["freshness_policies"].get(policy_key)
            if policy_id:
                api.post(
                    f"/api/v1/admin/sources/{sid}/freshness",
                    {
                        "freshness_policy_id": policy_id,
                        "last_verified_at": captured_at,
                        "review_due_at": None,
                    },
                )
                counts["freshness_assignments"] += 1

            # ---- SourceMonitor for dynamic primary sources (spec §28-33) ----
            if skey in MONITORABLE_SOURCE_KEYS and sdata.get("source_url"):
                mkey = f"{skey}:monitor"
                if mkey not in manifest["monitors"]:
                    created = api.post(
                        "/api/v1/admin/monitors",
                        {
                            "source_id": sid,
                            "url": sdata["source_url"],
                            "schedule_minutes": 1440,
                            "place_id": place_id,
                            "expansion_run_id": RUN_ID,
                        },
                    )
                    manifest["monitors"][mkey] = created["id"]
                    counts["monitors"] += 1
        # statute / municipal shared-source monitor (spec §28)
        skey = "shared:shanghai_park_civil_rules_2018"
        if skey in MONITORABLE_SOURCE_KEYS and f"{skey}:monitor" not in manifest["monitors"]:
            sdata = next(s for s in evidence["shared_sources"] if f"shared:{s['key']}" == skey)
            created = api.post(
                "/api/v1/admin/monitors",
                {
                    "source_id": shared_sources[skey],
                    "url": sdata["source_url"],
                    "schedule_minutes": 10080,  # municipal rules change rarely
                    "expansion_run_id": RUN_ID,
                },
            )
            manifest["monitors"][f"{skey}:monitor"] = created["id"]
            counts["monitors"] += 1
        for r in pdata["rules"]:
            ckey = f"{pkey}:{r['rule_id']}"
            if ckey in manifest["rule_candidates"]:
                continue
            src_key = r["source_key"]
            source_id = (
                shared_sources[src_key]
                if src_key.startswith("shared:")
                else manifest["sources"][f"{pkey}:{src_key}"]
            )
            layer = r.get("rule_layer") or "OPERATOR_POLICY"
            conditions = r.get("conditions") or []
            body = {
                "source_id": source_id,
                "place_id": place_id,
                "zone_id": zone_ids.get(r.get("zone_key") or ""),
                "animal_scope": r["animal_scope"],
                "action": r["action"],
                "effect": r["effect"],
                "rule_layer": layer,
                "mandatory_level": r.get("mandatory_level")
                or ("mandatory" if layer == "LEGAL" else "operator_discretion"),
                "proposed_conditions": conditions,
                "extraction_method": "agent_assisted_extraction_2026_09_19",
                "extraction_provider": "workbuddy-agent",
                "internal_confidence": r.get("confidence"),
                # --- ADR-025 / ADR-028: source-faithful scope ---
                "source_scope_exact": r.get("source_scope_exact"),
                "subject_scope_normalized": r.get("subject_scope_normalized"),
                "normalization_type": r.get("normalization_type"),
                "normative_effect": r.get("normative_effect"),
                "holder_scope": r.get("holder_scope"),
                "raw_text": r.get("review_note"),
                "evidence_bundle_id": bundle_for_rule.get((src_key, r["fragment"]))
                or manifest["bundles"].get(f"{src_key}:bundle:{r['fragment']}"),
                "expansion_run_id": RUN_ID,
                "dedup_key": _dedup_key(RUN_ID, pkey, r["rule_id"]),
            }
            created = api.post("/api/v1/admin/candidates", body)
            manifest["rule_candidates"][ckey] = created["id"]
            counts["rule_candidates"] += 1
            api.post(
                f"/api/v1/admin/candidates/{created['id']}/transition",
                {
                    "target": "REVIEW_PENDING",
                    "note": f"WAVE02/{RUN_ID}: 待人工审核（不得自动批准或发布）",
                },
            )
            counts["transitions"] += 1

        # ---- ObservationCandidates ------------------------------------------
        for o in pdata.get("observations", []):
            okey = f"{pkey}:{o['key']}"
            if okey in manifest["observation_candidates"]:
                continue
            created = api.post(
                "/api/v1/admin/observation-candidates",
                {
                    "place_id": place_id,
                    "zone_id": zone_ids.get(o["spatial_context"]),
                    "animal_scope": o["animal_scope"],
                    "observed_action": o["observed_action"],
                    "spatial_context": o["spatial_context"],
                    "occurred_at": o.get("occurred_at"),
                    "extraction_method": "agent_assisted_extraction_2026_09_19",
                    "raw_text": o["raw_text"],
                    "derivation_confidence": o.get("derivation_confidence"),
                    "expansion_run_id": RUN_ID,
                },
            )
            manifest["observation_candidates"][okey] = created["id"]
            counts["observation_candidates"] += 1

    # ---- close the DataSourceJob -------------------------------------------
    api.post(
        f"/api/v1/admin/data-source-jobs/{job['id']}/finish",
        {"state": "COMPLETED", "result_counts": counts, "errors": []},
    )

    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"created": counts, "run": manifest["run"], "manifest": str(MANIFEST_PATH)},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="WAVE_02 expansion ingest (no publishing)")
    ap.add_argument("--evidence", default=str(EVIDENCE_PATH))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    try:
        return run(Path(args.evidence), args.dry_run)
    except Exception as exc:  # noqa: BLE001 - operator-facing CLI error
        print(f"INGEST FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
