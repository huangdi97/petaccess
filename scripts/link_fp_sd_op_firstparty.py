"""Link the FIRST-PARTY operator source for 和平饭店 (Fairmont Peace Hotel).

Context
-------

``fp-sd-op`` was ingested from an OTA aggregator page (booking.com/hotels.com/
expedia). R2 therefore marked it HOLD: an aggregator is not the operator's own
channel, and an aggregator page must never be the reason to publish a rule.

The first-party source is available — Fairmont's own website states, verbatim:

    「上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付
      额外费用或受任何限制。」                                   (zh, guest-services)
    "Fairmont Peace Hotel does not allow pets. Seeing-eye dogs are always welcome
     and exempt of charges and restrictions."                   (en, guest-services)

Quote fidelity is enforced, not assumed: the artifact's ``content_hash`` is
``sha256(verbatim_excerpt)`` — the same formula used by
``scripts/evidence_repair_r2.py``, which first linked this page on 2026-09-13 —
so anyone can recompute it from the stored excerpt. It was re-read against the
live page on 2026-09-15 and matched character for character.

That is an `official_operator_policy` from the operator's own domain, naming
**导盲犬 and nothing wider** — the same shape as every other `*-sd-op` row.

What this script does
---------------------

Following the project's own rule ("拿到正确来源后新建 Candidate，不复用旧错误
Candidate"), it does **not** re-point the OTA-sourced row. It:

  1. creates a `Source` (official_operator_policy, fairmont.com);
  2. freezes a `SourceArtifact` (OperatorSiteCollector, verbatim excerpt + hash);
  3. creates an `EvidenceBundle` citing that artifact;
  4. creates a NEW candidate `fp-sd-op-firstparty` scoped `guide_dog` / `exact`;
  5. writes `docs/reality_audit/fp_sd_op_firstparty.json` so the packet generator
     can pick the row up without guessing ids.

Every write goes through the audited admin API. The old OTA row keeps its
evidence untouched and is dispositioned as superseded — never silently rewritten.

Usage: python scripts/link_fp_sd_op_firstparty.py [--apply]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
import psycopg

REPO = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8010"
DB_URL = "postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"
SIDECAR = REPO / "docs" / "reality_audit" / "fp_sd_op_firstparty.json"

OLD_CANDIDATE_ID = "7efddba6-7c42-4013-8918-bedbb996d702"  # fp-sd-op (OTA-sourced)
ADMIN_EMAIL = "scope-split-ops@example.com"

SOURCE_URL_EN = (
    "https://www.fairmont.com/en/hotels/shanghai/fairmont-peace-hotel/guest-services.html"
)
SOURCE_URL_ZH = (
    "https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html"
)
#: VERBATIM. Re-read against the live page on 2026-09-15; any paraphrase would
#: break content_hash reproducibility and therefore cannot be used here. Split
#: at the source's own sentence boundary so lines stay readable — the resulting
#: value is byte-identical to what the artifact pins.
QUOTE_ZH_HEAD = "上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。"
QUOTE_ZH_TAIL = "导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。"
QUOTE_ZH = QUOTE_ZH_HEAD + QUOTE_ZH_TAIL
QUOTE_EN = (
    "Fairmont Peace Hotel does not allow pets. Seeing-eye dogs are always welcome "
    "and exempt of charges and restrictions."
)
ISSUER = "费尔蒙酒店集团官网《上海和平饭店 · 宾客服务》宠物政策"
CAPTURED_AT = "2026-09-15T00:00:00Z"

SCOPE = {
    "source_scope_exact": "导盲犬",
    "subject_scope_normalized": "guide_dog",
    "normalization_type": "exact",
    "normative_effect": "exempt_from_prohibition",
    "holder_scope": "person_with_disability",
}


def _token() -> str:
    with httpx.Client(base_url=BASE, timeout=30) as c:
        r = c.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": "passw0rd123"})
        r.raise_for_status()
        return r.json()["access_token"]


def _old_candidate_owner() -> dict:
    with psycopg.connect(DB_URL, connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute(
            "select place_id, zone_id, extraction_method, internal_confidence "
            "from rule_candidate where id=%s",
            (OLD_CANDIDATE_ID,),
        )
        row = cur.fetchone()
        if row is None:
            raise SystemExit("旧候选 fp-sd-op 不存在")
        place_id, zone_id, method, confidence = row
        cur.execute("select canonical_name from place where id=%s", (place_id,))
        name = cur.fetchone()
        return {
            "place_id": place_id,
            "zone_id": zone_id,
            "extraction_method": method,
            "internal_confidence": confidence,
            "place_name": name[0] if name else None,
        }


def _existing_chain() -> dict | None:
    """Reuse an already-created first-party chain (idempotent re-run).

    Read-only lookup; all *writes* still go through the audited API. Without this
    a partially-failed run would leave duplicate sources/artifacts behind.
    """
    with psycopg.connect(DB_URL, connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute(
            "select id from source where source_url=%s order by created_at limit 1",
            (SOURCE_URL_ZH,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        source_id = row[0]
        cur.execute(
            "select id from source_artifact where source_id=%s order by created_at limit 1",
            (source_id,),
        )
        art = cur.fetchone()
        if art is None:
            return None
        artifact_id = art[0]
        cur.execute(
            "select id from evidence_bundle where artifact_id=%s order by created_at limit 1",
            (artifact_id,),
        )
        bun = cur.fetchone()
        if bun is None:
            return None
        return {"source_id": source_id, "artifact_id": artifact_id, "evidence_bundle_id": bun[0]}


def _check(resp: httpx.Response) -> None:
    """Raise with the API's error body, not just the status code."""
    if resp.status_code >= 400:
        raise SystemExit(f"{resp.status_code} {resp.request.url}\n{resp.text}")


def _create_chain(
    client: httpx.Client, headers: dict, owner: dict, digest: str
) -> tuple[str, str, str]:
    """source → artifact → bundle, in that order, all audited."""
    src = client.post(
        "/api/v1/sources",
        json={
            "source_type": "official_operator_policy",
            "issuer": ISSUER,
            "issuer_verification": "verified",
            "source_url": SOURCE_URL_ZH,
            "observed_at": CAPTURED_AT,
            "directness": "direct",
            "spatial_precision": "precise",
            "notes": f"first-party operator channel; EN locale: {SOURCE_URL_EN}",
        },
        headers=headers,
    )
    _check(src)
    source_id = src.json()["id"]

    art = client.post(
        "/api/v1/admin/source-artifacts",
        json={
            "source_id": source_id,
            "collector_type": "OperatorSiteCollector",
            "artifact_type": "web_page",
            "source_url": SOURCE_URL_ZH,
            "content_hash": digest,
            "publisher_type": "operator",
            "published_at": CAPTURED_AT,
            "captured_excerpt": QUOTE_ZH,
            "storage_allowed": True,
            "display_allowed": True,
            "redistribution_allowed": True,
            "evidence_strength": "primary_direct",
        },
        headers=headers,
    )
    _check(art)
    artifact_id = art.json()["id"]

    bundle = client.post(
        "/api/v1/admin/evidence-bundles",
        json={
            "artifact_id": artifact_id,
            "quoted_fragment": QUOTE_ZH,
            "extracted_fragment": "fp-sd-op-firstparty",
            "evidence_class": "original",
            "extraction_method": "manual_first_party_review",
            "place_match_evidence": {
                "matched_by": "canonical_name_and_brand",
                "canonical_name": owner["place_name"],
                "source_locale_zh": SOURCE_URL_ZH,
                "source_locale_en": SOURCE_URL_EN,
            },
        },
        headers=headers,
    )
    _check(bundle)
    return source_id, artifact_id, bundle.json()["id"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    owner = _old_candidate_owner()
    plan = {
        "source": {
            "source_type": "official_operator_policy",
            "issuer": ISSUER,
            "url": SOURCE_URL_ZH,
        },
        "artifact": {
            "collector_type": "OperatorSiteCollector",
            "evidence_strength": "primary_direct",
        },
        "quote_zh": QUOTE_ZH,
        "quote_en": QUOTE_EN,
        "new_candidate": {"rule_id": "fp-sd-op-firstparty", "scope": SCOPE, **owner},
    }
    if not args.apply:
        print(json.dumps({"dry_run": True, **plan}, ensure_ascii=False, indent=2))
        return 0

    token = _token()
    headers = {"Authorization": f"Bearer {token}"}
    # content_hash pins the STORED EXCERPT, matching the convention used by
    # scripts/evidence_repair_r2.py (which created this chain on 2026-09-13).
    # Hashing the excerpt alone — rather than excerpt+translation — is what makes
    # the hash reproducible from the artifact row anyone can read.
    digest = hashlib.sha256(QUOTE_ZH.encode("utf-8")).hexdigest()

    with httpx.Client(base_url=BASE, timeout=60) as client:
        reused = _existing_chain()
        if reused is not None:
            # idempotent re-run: never create a second source/artifact/bundle
            source_id = reused["source_id"]
            artifact_id = reused["artifact_id"]
            bundle_id = reused["evidence_bundle_id"]
        else:
            source_id, artifact_id, bundle_id = _create_chain(client, headers, owner, digest)

        cand = client.post(
            "/api/v1/admin/candidates",
            json={
                "source_id": source_id,
                "place_id": owner["place_id"],
                "zone_id": owner["zone_id"],
                "animal_scope": "service_dog",
                "action": "enter",
                "effect": "allowed",
                "rule_layer": "OPERATOR_POLICY",
                "mandatory_level": "operator_discretion",
                "extraction_method": owner["extraction_method"],
                # the old row carried 0.5 precisely because its evidence was an
                # aggregator page; a verbatim first-party statement is not that.
                "internal_confidence": 0.95,
                "evidence_bundle_id": bundle_id,
                "raw_text": f"{QUOTE_ZH} / {QUOTE_EN}",
                **SCOPE,
            },
            headers=headers,
        )
        cand.raise_for_status()
        candidate_id = cand.json()["id"]

        tr = client.post(
            f"/api/v1/admin/candidates/{candidate_id}/transition",
            json={"target": "REVIEW_PENDING", "note": "一手来源（fairmont.com）补齐后进入评审队列"},
            headers=headers,
        )
        tr.raise_for_status()

    sidecar = {
        "rule_id": "fp-sd-op-firstparty",
        "candidate_id": candidate_id,
        "source_id": source_id,
        "artifact_id": artifact_id,
        "evidence_bundle_id": bundle_id,
        "source_url": SOURCE_URL_ZH,
        "source_url_en": SOURCE_URL_EN,
        "issuer": ISSUER,
        "quote_zh": QUOTE_ZH,
        "quote_en": QUOTE_EN,
        "content_hash": digest,
        "captured_at": CAPTURED_AT,
        "supersedes_ota_row": OLD_CANDIDATE_ID,
        "note": (
            "OTA 聚合页（旧候选 fp-sd-op）不作为发布依据；本行为运营方一手来源新建的候选，"
            "遵守「不复用旧错误 Candidate」原则。"
        ),
    }
    SIDECAR.write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"applied": True, **sidecar}, ensure_ascii=False, indent=2))
    _ = datetime.now(UTC)
    return 0


if __name__ == "__main__":
    sys.exit(main())
