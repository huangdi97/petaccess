"""REAL DATA PILOT ingest (PART B, B1-B7 + B13).

Walks the full evidence chain through the LIVE API for the 10 pilot places:
    Source -> SourceArtifact -> EvidenceBundle -> RuleCandidate / ObservationCandidate

Hard rules enforced by this script:
  - every candidate rests at REVIEW_PENDING (transition MATCH_PENDING -> REVIEW_PENDING);
    NOTHING is approved or published (B13: first real-data round is 100% human review).
  - licences: artifact display/redistribution/storage flags come from the evidence register.
  - idempotent: IDs already recorded in docs/reality_audit/real_pilot_ingest_manifest.json
    are reused; missing entries are looked up by unique fields before creation.

Usage: uv run python scripts/real_pilot_ingest.py [--evidence PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8010"
MANIFEST_PATH = REPO / "docs" / "reality_audit" / "real_pilot_ingest_manifest.json"

EXTRACTION_METHOD = "agent_assisted_extraction_2026_09_13"
EXTRACTION_PROVIDER = "zcode-agent"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Api:
    def __init__(self, token: str) -> None:
        self.c = httpx.Client(
            base_url=BASE,
            timeout=20.0,
            trust_env=False,
            headers={"Authorization": f"Bearer {token}"},
        )

    def post(self, path: str, body: dict) -> dict:
        r = self.c.post(path, json=body)
        if r.status_code >= 400:
            raise RuntimeError(f"POST {path} -> {r.status_code}: {r.text[:300]}")
        return r.json()

    def get(self, path: str) -> dict:
        r = self.c.get(path)
        if r.status_code >= 400:
            raise RuntimeError(f"GET {path} -> {r.status_code}: {r.text[:300]}")
        return r.json()


def bootstrap_admin(evidence: dict) -> str:
    """Register (or reuse) the pilot admin user, promote it in DB, return token."""
    email = evidence["admin_email"]
    password = "PilotAdmin0913!"
    with httpx.Client(base_url=BASE, timeout=15.0, trust_env=False) as c:
        r = c.post(
            "/api/v1/auth/register",
            json={"display_name": "real-pilot-admin", "email": email, "password": password},
        )
        already = "已被注册" in r.text or "exists" in r.text
        # 409/400 with "already" is fine on rerun; anything else is fatal
        if r.status_code not in (200, 201) and not already and r.status_code not in (400, 409):
            raise RuntimeError(f"register failed: {r.status_code} {r.text[:300]}")
        r = c.post("/api/v1/auth/login", json={"email": email, "password": password})
        if r.status_code >= 400:
            raise RuntimeError(f"login failed: {r.status_code} {r.text[:300]}")
        token = r.json()["access_token"]

    from app.db.session import get_session_factory
    from app.models import User

    s = get_session_factory()()
    row = s.query(User).filter(User.email == email).one()
    if str(row.role) != "admin":
        row.role = "admin"
        s.commit()
    s.close()
    return token


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


_MANIFEST_KEYS = (
    "places",
    "zones",
    "sources",
    "artifacts",
    "bundles",
    "rule_candidates",
    "observation_candidates",
)


def run(evidence_path: Path) -> int:
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    manifest: dict = (
        json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if MANIFEST_PATH.exists()
        else {k: {} for k in _MANIFEST_KEYS}
    )
    for k in _MANIFEST_KEYS:
        manifest.setdefault(k, {})

    token = bootstrap_admin(evidence)
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
    }

    for pdata in evidence["places"]:
        pkey = pdata["key"]

        # ---- Place -----------------------------------------------------
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
                    "location_wkt": pdata["location_wkt"],
                },
            )
            place_id = created["id"]
            counts["places"] += 1
        manifest["places"][pkey] = place_id

        # ---- Zones -----------------------------------------------------
        zone_ids: dict[str, str | None] = {}
        existing_zones = api.get(f"/api/v1/places/{place_id}/zones")
        zone_rows = (
            existing_zones.get("items", []) if isinstance(existing_zones, dict) else existing_zones
        )
        by_name = {z["name"]: z["id"] for z in zone_rows if isinstance(z, dict)}
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

        # ---- Sources + Artifacts + Bundules -----------------------------
        bundle_for_rule: dict[str, str] = {}
        for sdata in pdata["sources"]:
            skey = f"{pkey}:{sdata['key']}"
            source_id = manifest["sources"].get(skey)
            if not source_id:
                found = find_source(api, sdata.get("source_url"), sdata["issuer"])
                source_id = found["id"] if found else None
            if not source_id:
                created = api.post(
                    "/api/v1/sources",
                    {
                        "source_type": sdata["source_type"],
                        "issuer": sdata["issuer"],
                        "issuer_verification": sdata["issuer_verification"],
                        "source_url": sdata.get("source_url"),
                        "observed_at": evidence["captured_at"],
                        "published_at": sdata.get("published_at"),
                        "directness": sdata["directness"],
                        "spatial_precision": sdata["spatial_precision"],
                        "notes": (
                            f"capture_method={sdata['capture_method']}; "
                            f"needs_verification={sdata.get('needs_verification', False)}"
                        ),
                    },
                )
                source_id = created["id"]
                counts["sources"] += 1
            manifest["sources"][skey] = source_id

            # artifact: one per source; content_hash over excerpt (verbatim capture)
            akey = f"{skey}:artifact"
            artifact_id = manifest["artifacts"].get(akey)
            excerpt = sdata["excerpt"]
            if not artifact_id:
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
                    },
                )
                artifact_id = created["id"]
                counts["artifacts"] += 1
            manifest["artifacts"][akey] = artifact_id

            # one bundle per (source x fragment used by rules)
            used_fragments = sorted(
                {r["fragment"] for r in pdata["rules"] if r["source_key"] == sdata["key"]}
            )
            for frag_key in used_fragments:
                bkey = f"{skey}:bundle:{frag_key}"
                bundle_id = manifest["bundles"].get(bkey)
                if not bundle_id:
                    quoted = (
                        sdata["fragments"][frag_key]
                        if frag_key in sdata.get("fragments", {})
                        else excerpt
                    )
                    place_match = {
                        "matched_by": "canonical_name_and_address",
                        "canonical_name": pdata["canonical_name"],
                        "canonical_address": pdata["canonical_address"],
                        "spatial_precision": sdata["spatial_precision"],
                    }
                    temporal = {
                        "published_at": sdata.get("published_at"),
                        "captured_at": evidence["captured_at"],
                        "effective_from": next(
                            (
                                r.get("effective_from")
                                for r in pdata["rules"]
                                if r["source_key"] == sdata["key"] and r.get("effective_from")
                            ),
                            None,
                        ),
                    }
                    created = api.post(
                        "/api/v1/admin/evidence-bundles",
                        {
                            "artifact_id": artifact_id,
                            "quoted_fragment": quoted,
                            "extracted_fragment": json.dumps(
                                [
                                    r["rule_id"]
                                    for r in pdata["rules"]
                                    if r["source_key"] == sdata["key"] and r["fragment"] == frag_key
                                ],
                                ensure_ascii=False,
                            ),
                            "evidence_class": "original",
                            "extraction_method": EXTRACTION_METHOD,
                            "extraction_model": EXTRACTION_PROVIDER,
                            "place_match_evidence": place_match,
                            "temporal_evidence": temporal,
                            "privacy_notes": (
                                None
                                if sdata["storage_allowed"]
                                else "lead-only social content: not stored beyond excerpt"
                            ),
                        },
                    )
                    bundle_id = created["id"]
                    counts["bundles"] += 1
                manifest["bundles"][bkey] = bundle_id
                bundle_for_rule[(sdata["key"], frag_key)] = bundle_id

        # ---- RuleCandidates (rest at REVIEW_PENDING) --------------------
        for r in pdata["rules"]:
            ckey = f"{pkey}:{r['rule_id']}"
            cand_id = manifest["rule_candidates"].get(ckey)
            if not cand_id:
                created = api.post(
                    "/api/v1/admin/candidates",
                    {
                        "source_id": manifest["sources"][f"{pkey}:{r['source_key']}"],
                        "place_id": place_id,
                        "zone_id": zone_ids.get(r.get("zone_key") or ""),
                        "animal_scope": r["animal_scope"],
                        "action": r["action"],
                        "effect": r["effect"],
                        # normative layer from the evidence register; without this
                        # a statutory rule would be published as an operator policy
                        "rule_layer": r.get("rule_layer") or "OPERATOR_POLICY",
                        "proposed_conditions": r.get("conditions") or [],
                        "extraction_method": EXTRACTION_METHOD,
                        "extraction_provider": EXTRACTION_PROVIDER,
                        "internal_confidence": r.get("confidence"),
                        "raw_text": (
                            pdata["sources"][0]["excerpt"][:200] if not r.get("fragment") else None
                        ),
                        "evidence_bundle_id": bundle_for_rule.get((r["source_key"], r["fragment"])),
                    },
                )
                cand_id = created["id"]
                counts["rule_candidates"] += 1
                # advance MATCH_PENDING -> REVIEW_PENDING (human review queue; NEVER approve here)
                api.post(
                    f"/api/v1/admin/candidates/{cand_id}/transition",
                    {
                        "target": "REVIEW_PENDING",
                        "note": "REAL PILOT: 待人工审核（第一轮全部人工）",
                    },
                )
                counts["transitions"] += 1
            manifest["rule_candidates"][ckey] = cand_id

        # ---- ObservationCandidates --------------------------------------
        for o in pdata.get("observations", []):
            okey = f"{pkey}:{o['key']}"
            oc_id = manifest["observation_candidates"].get(okey)
            if not oc_id:
                # observation candidates must cite a bundle; use the first bundle of the place
                first_bundle = next(
                    iter(
                        manifest["bundles"].get(k)
                        for k in manifest["bundles"]
                        if k.startswith(f"{pkey}:")
                    ),
                    None,
                )
                first_bundle = first_bundle or bundle_for_rule[next(iter(bundle_for_rule))]
                created = api.post(
                    "/api/v1/admin/observation-candidates",
                    {
                        "evidence_bundle_id": first_bundle,
                        "place_id": place_id,
                        "zone_id": zone_ids.get(o["spatial_context"]),
                        "animal_scope": o["animal_scope"],
                        "observed_action": o["observed_action"],
                        "spatial_context": o["spatial_context"],
                        "occurred_at": o.get("occurred_at"),
                        "extraction_method": EXTRACTION_METHOD,
                        "raw_text": o["raw_text"],
                        "derivation_confidence": o.get("derivation_confidence"),
                    },
                )
                oc_id = created["id"]
                counts["observation_candidates"] += 1
            manifest["observation_candidates"][okey] = oc_id

    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"created": counts, "manifest": str(MANIFEST_PATH)}, ensure_ascii=False, indent=2
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="REAL DATA PILOT ingest (no publishing)")
    parser.add_argument(
        "--evidence", default=str(REPO / "docs" / "reality_audit" / "real_pilot_evidence.json")
    )
    args = parser.parse_args()
    try:
        return run(Path(args.evidence))
    except Exception as exc:  # noqa: BLE001 - operator-facing CLI error
        print(f"INGEST FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
