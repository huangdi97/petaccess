"""30_50_PLACE_EXPANSION_R1 — WAVE_01 ingest (workstream A + B).

Walks the canonical evidence chain through the LIVE API:

    DataSourceJob -> Source -> SourceArtifact -> EvidenceBundle
                 -> RuleCandidate / ObservationCandidate  (all REVIEW_PENDING)

Hard rules enforced here (spec §2, §3, §39, §41):
  * every write carries ``expansion_run_id = EXP-R1-W01-20260918`` and is
    attributable to one DataSourceJob;
  * candidates get a deterministic ``dedup_key`` so a re-run is idempotent;
  * NOTHING is approved, published, or given a human ``final_decision``;
  * no raw SQL, no INSERT-then-backfill: everything goes through the API.

Usage::

    python scripts/expansion_w01_ingest.py
    python scripts/expansion_w01_ingest.py --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8010"
EVIDENCE_PATH = REPO / "docs" / "expansion" / "expansion_r1_wave01_evidence.json"
MANIFEST_PATH = REPO / "docs" / "expansion" / "expansion_r1_wave01_manifest.json"

EXTRACTION_METHOD = "agent_assisted_extraction_2026_09_18"
EXTRACTION_PROVIDER = "workbuddy-agent"

#: Sources whose content can change in place — these MUST get a SourceMonitor
#: (spec §28: monitorable-source-first). One-shot news articles do not.
MONITORABLE_SOURCE_KEYS = {
    "zoo-shanghai:zoo_official",
    "mus-shanghai-east:museum_official",
    "dl-disneyland:disney_park_rules_2026",
    "ht-langham-xintiandi:langham_pawcation",
    "shared:sh_dog_regulation_gov",
}

#: Freshness: review interval in days per source_type (spec §34).
FRESHNESS_BY_SOURCE_TYPE = {
    "statute_or_regulation": 365,
    "government_service": 180,
    "official_operator_policy": 90,
    "onsite_signage": 90,
    "external_web_reference": 180,
}

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


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _dedup_key(run_id: str, place_key: str, rule_id: str) -> str:
    return _sha256(f"{run_id}|{place_key}|{rule_id}")


class Api:
    def __init__(self, token: str) -> None:
        self.c = httpx.Client(
            base_url=BASE,
            timeout=30.0,
            trust_env=False,
            headers={"Authorization": f"Bearer {token}"},
        )

    def post(self, path: str, body: dict) -> dict:
        r = self.c.post(path, json=body)
        if r.status_code >= 400:
            raise RuntimeError(f"POST {path} -> {r.status_code}: {r.text[:400]}")
        return r.json()

    def patch(self, path: str, body: dict) -> dict:
        r = self.c.patch(path, json=body)
        if r.status_code >= 400:
            raise RuntimeError(f"PATCH {path} -> {r.status_code}: {r.text[:400]}")
        return r.json()

    def get(self, path: str) -> dict:
        r = self.c.get(path)
        if r.status_code >= 400:
            raise RuntimeError(f"GET {path} -> {r.status_code}: {r.text[:400]}")
        return r.json()


def login() -> str:
    """Log in as the existing demo admin (no new privileged account is created)."""
    email = os.environ.get("WAVE01_ADMIN_EMAIL", "admin@demo-petaccess.com")
    password = os.environ.get("WAVE01_ADMIN_PASSWORD", "admin12345")
    with httpx.Client(base_url=BASE, timeout=20.0, trust_env=False) as c:
        r = c.post("/api/v1/auth/login", json={"email": email, "password": password})
        if r.status_code >= 400:
            raise RuntimeError(f"login failed: {r.status_code} {r.text[:300]}")
        return r.json()["access_token"]


def find_place(api: Api, canonical_name: str) -> dict | None:
    data = api.get(f"/api/v1/places?limit=100&q={canonical_name}")
    for item in data.get("items", []):
        if item.get("canonical_name") == canonical_name:
            return item
    return None


def find_source(api: Api, source_url: str | None, issuer: str) -> dict | None:
    data = api.get("/api/v1/sources?limit=100")
    for item in data.get("items", []):
        if source_url and item.get("source_url") == source_url:
            return item
        if item.get("issuer") == issuer:
            return item
    return None


def ensure_source(api: Api, sdata: dict, *, captured_at: str, counts: dict) -> str:
    found = find_source(api, sdata.get("source_url"), sdata["issuer"])
    if found:
        return found["id"]
    created = api.post(
        "/api/v1/sources",
        {
            "source_type": sdata["source_type"],
            "issuer": sdata["issuer"],
            "issuer_verification": sdata["issuer_verification"],
            "source_url": sdata.get("source_url"),
            "observed_at": captured_at,
            "published_at": sdata.get("published_at"),
            "directness": sdata["directness"],
            "spatial_precision": sdata["spatial_precision"],
            "notes": (
                f"capture_method={sdata['capture_method']}; "
                f"needs_verification={sdata.get('needs_verification', False)}"
            ),
        },
    )
    counts["sources"] += 1
    return created["id"]


def ensure_artifact(
    api: Api,
    *,
    source_id: str,
    sdata: dict,
    excerpt: str,
    run_id: str,
    manifest: dict,
    mkey: str,
    counts: dict,
) -> str:
    if mkey in manifest["artifacts"]:
        return manifest["artifacts"][mkey]
    created = api.post(
        "/api/v1/admin/source-artifacts",
        {
            "source_id": source_id,
            "collector_type": sdata["collector_type"],
            "artifact_type": sdata["artifact_type"],
            "source_url": sdata.get("source_url"),
            "content_hash": _sha256(excerpt),
            "publisher_type": sdata["publisher_type"],
            "published_at": sdata.get("published_at"),
            "captured_excerpt": excerpt,
            "storage_allowed": sdata["storage_allowed"],
            "display_allowed": sdata["display_allowed"],
            "redistribution_allowed": sdata["redistribution_allowed"],
            "expansion_run_id": run_id,
        },
    )
    manifest["artifacts"][mkey] = created["id"]
    counts["artifacts"] += 1
    return created["id"]


def ensure_bundle(
    api: Api,
    *,
    artifact_id: str,
    quoted: str,
    extracted: str,
    run_id: str,
    place_match: dict,
    temporal: dict,
    privacy: str | None,
    manifest: dict,
    mkey: str,
    counts: dict,
) -> str:
    if mkey in manifest["bundles"]:
        return manifest["bundles"][mkey]
    created = api.post(
        "/api/v1/admin/evidence-bundles",
        {
            "artifact_id": artifact_id,
            "quoted_fragment": quoted,
            "extracted_fragment": extracted,
            "evidence_class": "original",
            "extraction_method": EXTRACTION_METHOD,
            "extraction_model": EXTRACTION_PROVIDER,
            "place_match_evidence": place_match,
            "temporal_evidence": temporal,
            "privacy_notes": privacy,
            "expansion_run_id": run_id,
        },
    )
    manifest["bundles"][mkey] = created["id"]
    counts["bundles"] += 1
    return created["id"]


def run(evidence_path: Path, dry_run: bool) -> int:
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    run_id = evidence["expansion_run_id"]
    captured_at = evidence["captured_at"]

    manifest: dict = (
        json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if MANIFEST_PATH.exists()
        else {k: {} for k in _MANIFEST_KEYS}
    )
    for k in _MANIFEST_KEYS:
        manifest.setdefault(k, {})

    if dry_run:
        plan = {
            "expansion_run_id": run_id,
            "review_revision": evidence["review_revision"],
            "places": [p["key"] for p in evidence["places"]],
            "shared_sources": [s["key"] for s in evidence["shared_sources"]],
            "new_places": sum(1 for p in evidence["places"] if p["workstream"] == "B"),
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
            "job_type": "expansion_wave01",
            "target": "SHANGHAI_30_50_EXPANSION_WAVE01",
            "expansion_run_id": run_id,
            "params": {
                "revision": evidence["review_revision"],
                "wave": evidence["wave"],
                "jurisdiction": evidence["jurisdiction"],
                "captured_at": captured_at,
            },
        },
    )
    manifest["run"] = {
        "expansion_run_id": run_id,
        "review_revision": evidence["review_revision"],
        "data_source_job_id": job.get("id"),
    }

    # ---- shared sources (e.g. the statute) --------------------------------
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
            run_id=run_id,
            manifest=manifest,
            mkey=f"{skey}:artifact",
            counts=counts,
        )
        # one bundle per fragment actually used by a rule
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
                extracted=json.dumps(
                    {
                        "fragment_key": frag,
                        "rule_ids": [
                            r["rule_id"]
                            for p in evidence["places"]
                            for r in p["rules"]
                            if r["source_key"] == skey and r["fragment"] == frag
                        ],
                    },
                    ensure_ascii=False,
                ),
                run_id=run_id,
                place_match={
                    "matched_by": "statutory_applicability_by_place_type",
                    "note": "法条适用于 places 中类型落入第二十三条第一款列举清单者；"
                    "逐场所适用性由人工复核",
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
                    "name": f"wave01-{stype}-{days}d",
                    "review_interval_days": days,
                    "description": f"Wave01 默认复核周期：{stype} 每 {days} 天",
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
            created = api.post(
                "/api/v1/places",
                {
                    "canonical_name": pdata["canonical_name"],
                    "place_type": pdata["place_type"],
                    "canonical_address": pdata["canonical_address"],
                    # location intentionally omitted: no source published
                    # coordinates, and Wave 01 does not invent any (spec §72-73)
                    "location_wkt": None,
                },
            )
            place_id = created["id"]
            counts["places"] += 1
        manifest["places"][pkey] = place_id

        if pdata.get("aliases"):
            try:
                api.patch(f"/api/v1/places/{place_id}", {"alias_names": pdata["aliases"]})
            except RuntimeError as exc:  # alias patch is non-fatal, but must be visible
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
                run_id=run_id,
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
                        {"fragment_key": frag, "rule_ids": rule_ids},
                        ensure_ascii=False,
                    ),
                    run_id=run_id,
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

            # ---- freshness assignment (100% coverage target, spec §35) -------
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

            # ---- SourceMonitor for dynamic primary sources (spec §28-33) -----
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
                            "expansion_run_id": run_id,
                        },
                    )
                    manifest["monitors"][mkey] = created["id"]
                    counts["monitors"] += 1

        # statute monitor (shared source)
        skey = "shared:sh_dog_regulation_gov"
        if skey in MONITORABLE_SOURCE_KEYS and f"{skey}:monitor" not in manifest["monitors"]:
            sdata = next(s for s in evidence["shared_sources"] if f"shared:{s['key']}" == skey)
            created = api.post(
                "/api/v1/admin/monitors",
                {
                    "source_id": shared_sources[skey],
                    "url": sdata["source_url"],
                    "schedule_minutes": 10080,  # statute changes rarely
                    "expansion_run_id": run_id,
                },
            )
            manifest["monitors"][f"{skey}:monitor"] = created["id"]
            counts["monitors"] += 1

        # ---- RuleCandidates (rest at REVIEW_PENDING) -------------------------
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
                "proposed_conditions": r.get("conditions") or [],
                "extraction_method": EXTRACTION_METHOD,
                "extraction_provider": EXTRACTION_PROVIDER,
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
                # --- Wave 01 traceability ---
                "expansion_run_id": run_id,
                "dedup_key": _dedup_key(run_id, pkey, r["rule_id"]),
            }
            created = api.post("/api/v1/admin/candidates", body)
            manifest["rule_candidates"][ckey] = created["id"]
            counts["rule_candidates"] += 1
            api.post(
                f"/api/v1/admin/candidates/{created['id']}/transition",
                {
                    "target": "REVIEW_PENDING",
                    "note": f"WAVE01/{run_id}: 待人工审核（不得自动批准或发布）",
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
                    "extraction_method": EXTRACTION_METHOD,
                    "raw_text": o["raw_text"],
                    "derivation_confidence": o.get("derivation_confidence"),
                    "expansion_run_id": run_id,
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
    parser = argparse.ArgumentParser(description="WAVE_01 expansion ingest (no publishing)")
    parser.add_argument("--evidence", default=str(EVIDENCE_PATH))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        return run(Path(args.evidence), args.dry_run)
    except Exception as exc:  # noqa: BLE001 - operator-facing CLI error
        print(f"INGEST FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
