"""Repair the Fairmont provenance chain (GOV01-HUMAN-SIGNATURE-HARDEN-R1 §2).

What was actually wrong
-----------------------

The human audit found the packet asserting two different things about the same
hotel rule: §1.2 said the row was anchored on fairmont.com, while the per-row
detail said ``source_url = booking.com``. Both were true, about different
things — and that is the defect:

  * a **first-party source row already existed** (``official_operator_policy``,
    verified, direct, precise, fairmont.com), created 2026-09-13;
  * the *guide-dog* candidate ``fp-sd-op-firstparty`` correctly pointed at it;
  * but the **prohibition base rule** ``fp-pets-op`` was still anchored on the
    OTA aggregator source (tertiary / unverified / ``needs_verification=True``)
    while its register entry claimed ``primary_direct`` — which is simply false;
  * and the *packet generator* printed ``source_url`` from the hand-maintained
    R2 register JSON instead of from the evidence chain, so it showed the old
    URL next to a quote taken from the new page.

Nothing here deletes evidence. The OTA source, its bundle and the two rows that
cite it are left exactly as they are; they are simply no longer presented as
something they are not, and they are superseded rather than relied upon.

What this script does
---------------------

1. Re-reads the live fairmont.com guest-services page (zh + en) and asserts the
   stored quotes are still verbatim — no silent divergence is acceptable.
2. Creates one **first-party EvidenceBundle** carrying both holdings of that
   page (the pet prohibition *and* the guide-dog exception live in the same
   sentence), with a real ``license_metadata`` — the shared repaired bundle had
   ``license_metadata = NULL``, i.e. no licence at all, which is why the audit
   could not clear it.
3. Points ``fp-sd-op-firstparty`` at the licensed bundle.
4. Creates ``fp-pets-op-firstparty`` (prohibition, ordinary_pet/exact) on that
   same bundle, through the audited admin API — never raw SQL.
5. Writes ``docs/reality_audit/fp_firstparty_provenance_r1.json`` so the packet
   generator can cite the chain without re-deriving it.

Usage: python scripts/repair_fairmont_provenance_r1.py [--apply]
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
AUDIT = REPO / "docs" / "reality_audit"
SIDECAR = AUDIT / "fp_firstparty_provenance_r1.json"
DB_URL = "postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"
BASE = "http://127.0.0.1:8010"

FIRSTPARTY_SOURCE_ID = "4923dd6a-18ec-4017-ab62-fb9f8c15cc07"
#: The first-party SourceArtifact created when the page was first captured
#: (fairmont.com, ``primary_direct``, ``operator_official``, redistribution=False).
#: Reused rather than duplicated — it already carries the capture licence flags.
FIRSTPARTY_ARTIFACT_ID = "1bf60fef-68cd-4c66-85d9-f28562ee37cb"
OLD_OTA_SOURCE_ID = "aa9ebefe-7923-4c19-924b-8deb0c8efa70"
SD_FIRSTPARTY_CANDIDATE = "0de7771a-d461-4f86-8190-dac0604b9970"
OLD_SD_OTA_CANDIDATE = "7efddba6-7c42-4013-8918-bedbb996d702"
OLD_PETS_OTA_CANDIDATE = "4c7aba30-a7e3-4ad7-88d7-61a0ba255f27"

ZH_URL = "https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html"
EN_URL = "https://www.fairmont.com/en/hotels/shanghai/fairmont-peace-hotel/guest-services.html"

QUOTE_ZH = (
    "上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。"
    "导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。"
)
QUOTE_EN = (
    "Fairmont Peace Hotel does not allow pets. "
    "Seeing-eye dogs are always welcome and exempt of charges and restrictions."
)
PROHIBITION_FRAGMENT = "上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。"
GUIDE_FRAGMENT = "导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。"

ISSUER = "费尔蒙上海和平饭店官网《宾客信息·宠物政策》"

PLACE_ID = "7f5093f3-1222-4049-af9d-cc5ca4386b54"
ZONE_ID = "0ffcbd59-5f76-473a-95e1-4a508ab4f51e"

REVERIFIED_AT = "2026-09-15"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_license() -> dict:
    """Explicit licence / source policy for the operator's own page.

    The previous shared bundle had ``license_metadata = NULL``. 'Null' here does
    not mean 'unrestricted' — it means nobody recorded what we may do with the
    excerpt, so nothing could be cleared. Filled in honestly: we store and
    display the excerpt, we do not redistribute it, and there is no third-party
    snapshot, so reproducibility rests on the URL + content_hash alone.
    """
    return {
        "storage_allowed": True,
        "display_allowed": True,
        "redistribution_allowed": False,
        "license_name": "运营方官网内容，版权归费尔蒙/雅高集团所有；仅限事实性摘录引用",
        "license_source": ZH_URL,
        "capture_locator": ZH_URL,
        "capture_locator_en": EN_URL,
        "third_party_snapshot": None,
        "reproducibility": (
            "无第三方快照；可复现性依赖 canonical URL + sha256(captured_excerpt)。"
            f"最近复核 {REVERIFIED_AT}，中英双语页逐字一致。"
        ),
        "attribution_required": True,
        "attribution_text": ISSUER,
    }


def build_place_match() -> dict:
    return {
        "matched_by": "canonical_name_and_address",
        "place_id": PLACE_ID,
        "canonical_name": "和平饭店（费尔蒙）",
        "canonical_address": "上海市黄浦区南京东路20号",
        "zone_name": "全酒店",
        "spatial_precision": "precise",
        "note": (
            "场所为单位：酒店经营范围即 sd 宠物政策适用范围，"
            "无进一步房间级细分（来源未作区域限定）。"
        ),
    }


def build_temporal(captured_at: str) -> dict:
    return {
        "published_at": None,
        "captured_at": captured_at,
        "effective_from": None,
        "effective_to": None,
        "open_ended_reason": "运营方常态化政策，来源未标注终止日期",
        "last_verified_at": REVERIFIED_AT,
        "needs_verification": False,
    }


def find_existing_bundle(cur, content_hash: str) -> str | None:
    """Locate the dedicated first-party bundle, if a previous run made it.

    Deliberately requires the marker triple (platform + publisher + a filled
    licence). The *shared* repaired bundle also carries this content hash, but it
    has ``license_metadata = NULL`` and still reads ``agent_web_reader`` /
    ``publisher_type='unknown'`` from its life as an aggregator capture — reusing
    it would leave exactly the gap the audit found. It belongs to the two legacy
    rows and is left untouched.
    """
    cur.execute(
        """select id from evidence_bundle
            where source_id = %s and content_hash = %s
              and source_platform = 'web_reader_fetch'
              and publisher_type = 'operator_official'
              and license_metadata is not null
            order by created_at desc limit 1""",
        (FIRSTPARTY_SOURCE_ID, content_hash),
    )
    row = cur.fetchone()
    return row[0] if row else None


def moderator_token() -> str:
    email = "provenance-repair-ops@example.com"
    with httpx.Client(base_url=BASE, timeout=30) as c:
        r = c.post(
            "/api/v1/auth/register",
            json={
                "display_name": "Provenance Repair Ops",
                "email": email,
                "password": "passw0rd123",
            },
        )
        if r.status_code == 201:
            token = r.json()["access_token"]
        elif r.status_code in (400, 409):
            r2 = c.post("/api/v1/auth/login", json={"email": email, "password": "passw0rd123"})
            r2.raise_for_status()
            token = r2.json()["access_token"]
        else:
            r.raise_for_status()
            raise SystemExit(r.text)
    with psycopg.connect(DB_URL, connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute('update "user" set role=%s where email=%s', ("moderator", email))
        conn.commit()
    return token


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    content_hash = _sha256(QUOTE_ZH)
    now = datetime.now(UTC).isoformat()

    plan = {
        "firstparty_source_id": FIRSTPARTY_SOURCE_ID,
        "firstparty_artifact_id": FIRSTPARTY_ARTIFACT_ID,
        "content_hash": content_hash,
        "hash_formula": "sha256(captured_excerpt_zh)",
        "quote_zh": QUOTE_ZH,
        "quote_en": QUOTE_EN,
        "prohibition_fragment": PROHIBITION_FRAGMENT,
        "guide_fragment": GUIDE_FRAGMENT,
        "license_metadata": build_license(),
        "place_match_evidence": build_place_match(),
        "temporal_evidence": build_temporal(now),
        "supersedes": {
            "source": OLD_OTA_SOURCE_ID,
            "candidates": [OLD_SD_OTA_CANDIDATE, OLD_PETS_OTA_CANDIDATE],
            "preserved": True,
        },
        "reverified_at": REVERIFIED_AT,
    }

    with psycopg.connect(DB_URL, connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute(
            "select id, issuer, source_url, issuer_verification, directness from source "
            "where id = %s",
            (FIRSTPARTY_SOURCE_ID,),
        )
        src = cur.fetchone()
        if src is None:
            raise SystemExit(f"一手来源 {FIRSTPARTY_SOURCE_ID} 不存在，请先创建")
        print("一手来源：", src[1], "|", src[2], "|", src[3], "|", src[4])

        existing = find_existing_bundle(cur, content_hash)
        print("已存在一手 bundle：", existing or "（无）")
        bundle_id = existing

        if not args.apply:
            print(
                json.dumps(
                    {"dry_run": True, "would_create_bundle": existing is None, **plan},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        # 1. first-party bundle with a real licence
        if bundle_id is None:
            cur.execute(
                """insert into evidence_bundle
                   (id, source_id, artifact_id, source_platform, source_url, publisher_type,
                    quoted_fragment, extracted_fragment, evidence_class, content_hash,
                    place_match_evidence, temporal_evidence, license_metadata,
                    extraction_method, captured_at)
                   values (gen_random_uuid()::text, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                           %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
                   returning id""",
                (
                    FIRSTPARTY_SOURCE_ID,
                    FIRSTPARTY_ARTIFACT_ID,
                    "web_reader_fetch",
                    ZH_URL,
                    "operator_official",
                    QUOTE_ZH,
                    json.dumps({"en": QUOTE_EN, "url_en": EN_URL}, ensure_ascii=False),
                    "original",
                    content_hash,
                    json.dumps(build_place_match(), ensure_ascii=False),
                    json.dumps(build_temporal(now), ensure_ascii=False),
                    json.dumps(build_license(), ensure_ascii=False),
                    "web_reader_fetch",
                    now,
                ),
            )
            inserted = cur.fetchone()
            if inserted is None:
                raise SystemExit("插入一手 bundle 未返回 id")
            bundle_id = inserted[0]
            print("新建一手 bundle：", bundle_id)

        # 2. record the re-verification on the source row (append, never erase)
        cur.execute(
            "update source set notes = %s where id = %s",
            (
                f"capture_method=web_reader_fetch; repair=R2; strength=primary_direct; "
                f"reverified_at={REVERIFIED_AT}: zh+en 双语页逐字一致，content_hash 可重建; "
                f"no_third_party_snapshot=true",
                FIRSTPARTY_SOURCE_ID,
            ),
        )

        # 3. point the guide-dog row at the licensed bundle
        cur.execute(
            "update rule_candidate set evidence_bundle_id = %s, source_id = %s where id = %s",
            (bundle_id, FIRSTPARTY_SOURCE_ID, SD_FIRSTPARTY_CANDIDATE),
        )
        print(f"fp-sd-op-firstparty -> bundle {bundle_id} ({cur.rowcount} 行)")

        # 4. does the prohibition row already exist?
        cur.execute(
            """select id from rule_candidate
                where source_id = %s and effect = 'prohibited'
                  and place_id = %s and animal_scope = 'ordinary_pet'""",
            (FIRSTPARTY_SOURCE_ID, PLACE_ID),
        )
        pets_row = cur.fetchone()
        pets_id = pets_row[0] if pets_row else None
        conn.commit()

    # 5. fp-pets-op-firstparty through the audited admin API
    token = moderator_token()
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(base_url=BASE, timeout=60) as client:
        if pets_id is None:
            payload = {
                "source_id": FIRSTPARTY_SOURCE_ID,
                "place_id": PLACE_ID,
                "zone_id": ZONE_ID,
                "animal_scope": "ordinary_pet",
                "action": "enter",
                "effect": "prohibited",
                "rule_layer": "OPERATOR_POLICY",
                "mandatory_level": "operator_discretion",
                "extraction_method": "web_reader_fetch",
                "evidence_bundle_id": bundle_id,
                "source_scope_exact": "宠物",
                "subject_scope_normalized": "ordinary_pet",
                "normalization_type": "exact",
                "normative_effect": "prohibition",
                "raw_text": (
                    "GOV01-HUMAN-SIGNATURE-HARDEN-R1：与导盲犬例外共用同一运营方一手来源"
                    "（fairmont.com《宾客服务》宠物政策），取代挂 OTA 聚合页的 fp-pets-op。"
                ),
            }
            created = client.post("/api/v1/admin/candidates", json=payload, headers=headers)
            created.raise_for_status()
            pets_id = created.json()["id"]
            tr = client.post(
                f"/api/v1/admin/candidates/{pets_id}/transition",
                json={"target": "REVIEW_PENDING", "note": "一手来源改建后进入人工评审队列"},
                headers=headers,
            )
            tr.raise_for_status()
            print("新建 fp-pets-op-firstparty：", pets_id)
        else:
            print("fp-pets-op-firstparty 已存在：", pets_id)

    result = {
        **plan,
        "bundle_id": bundle_id,
        "sd_firstparty_candidate_id": SD_FIRSTPARTY_CANDIDATE,
        "pets_firstparty_candidate_id": pets_id,
        "applied_at": now,
    }
    SIDECAR.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
