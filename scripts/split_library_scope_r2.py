"""Split 上海图书馆's compound animal-scope exception into source-exact rows (ADR-028).

The source (上海图书馆官网《读者须知》, https://www.library.sh.cn/guide/xuzhi) says:

    请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。

`军警犬` is a **compound** term: it names police dogs *and* military working dogs,
and the source does not distinguish them further. R1 stored the whole exception as
one row with the vague subject `service_dog`, which is the ADR-025 widening in a
different costume: it would have granted 导盲犬's right to every assistance dog,
and it said nothing auditable about which working dogs were covered.

This script re-models it as three source-exact rows:

    lib-sd-op-guide     source_scope_exact='导盲犬'  → guide_dog            (exact)
    lib-sd-op-police    source_scope_exact='军警犬'  → police_dog           (compound_term_split)
    lib-sd-op-military  source_scope_exact='军警犬'  → military_working_dog (compound_term_split)

Rules honoured:
  * the compound wording stays **verbatim** in ``source_scope_exact`` — the split
    is auditable, not a reinterpretation;
  * ``compound_term_split`` is only legal for a documented, exhaustive member set
    (see ``animal_scope.COMPOUND_TERM_SPLIT_MEANINGS``), so these rows can never
    be widened to another working dog;
  * all three rows share the **same EvidenceBundle** as the original — provenance
    is neither duplicated nor weakened ("更新 Evidence linkage");
  * every mutation goes through the **live, audited admin API** (never raw SQL),
    so ``audit_log`` shows ``candidate.set_scope`` / ``candidate.create`` per row.

Prerequisites: API on :8010 (``uv run uvicorn app.main:app --port 8010``) and the
PostgreSQL stack from docker-compose.

Usage: python scripts/split_library_scope_r2.py [--apply]
Without ``--apply`` it prints the planned changes and exits (dry run).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
import psycopg

REPO = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8010"
DB_URL = "postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"

#: the row R1 stored for the whole compound exception
GUIDE_ROW_ID = "76d0dfc3-64ae-4d2b-a152-18ff8ebed588"  # lib-sd-op
PLACE_ID = "b3504140-9828-4814-8d57-26af87c4e43e"
ZONE_ID = "536b0e11-2805-4d55-8147-f6c349e443ae"
SOURCE_ID = "199f3251-ee2f-44c4-94a8-36e3119cd097"
EVIDENCE_BUNDLE_ID = "e82a32fe-a6fe-4bae-9b30-ae92c4390d98"

GUIDE_SCOPE = {
    "source_scope_exact": "导盲犬",
    "subject_scope_normalized": "guide_dog",
    "normalization_type": "exact",
    "normative_effect": "exempt_from_prohibition",
    "holder_scope": "person_with_disability",
}
POLICE_SCOPE = {
    "source_scope_exact": "军警犬",
    "subject_scope_normalized": "police_dog",
    "normalization_type": "compound_term_split",
    "normative_effect": "exempt_from_prohibition",
    "holder_scope": "any_handler",
}
MILITARY_SCOPE = {
    "source_scope_exact": "军警犬",
    "subject_scope_normalized": "military_working_dog",
    "normalization_type": "compound_term_split",
    "normative_effect": "exempt_from_prohibition",
    "holder_scope": "any_handler",
}

COMPOUND_NOTE = (
    "军警犬 = 军用犬 + 警用犬（来源未再细分）。拆为 police_dog / military_working_dog 两行，"
    "source_scope_exact 保留「军警犬」原文；不得扩张到任何其他 working dog。"
)


def _moderator_token() -> str:
    """Create (or reuse) an ops moderator and return a bearer token.

    Account provisioning is the only step that touches the database directly —
    the equivalent of the test fixtures. Every *rule* mutation below goes through
    the audited API.
    """
    email = "scope-split-ops@example.com"
    with httpx.Client(base_url=BASE, timeout=30) as c:
        r = c.post(
            "/api/v1/auth/register",
            json={"display_name": "Scope Split Ops", "email": email, "password": "passw0rd123"},
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
        if cur.rowcount != 1:
            raise SystemExit("未能将运维账号提升为 moderator")
    return token


def _get_candidate(client: httpx.Client, headers: dict, candidate_id: str) -> dict:
    # place-scoped listing: the global list is paginated and this row is an early
    # pilot candidate, so it is not guaranteed to be on the first page.
    r = client.get(
        f"/api/v1/places/{PLACE_ID}/candidates",
        params={"limit": 200},
        headers=headers,
    )
    r.raise_for_status()
    for row in r.json()["items"]:
        if row["id"] == candidate_id:
            return row
    raise SystemExit(f"候选 {candidate_id} 不在场所 {PLACE_ID} 的候选列表中")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真正写入（缺省为 dry-run）")
    args = ap.parse_args()

    token = _moderator_token()
    headers = {"Authorization": f"Bearer {token}"}

    with httpx.Client(base_url=BASE, timeout=60) as client:
        base = _get_candidate(client, headers, GUIDE_ROW_ID)
        method = base["extraction_method"]
        confidence = base.get("internal_confidence")

        plan = {
            "update": {
                "candidate_id": GUIDE_ROW_ID,
                "rule_id": "lib-sd-op-guide",
                "scope": GUIDE_SCOPE,
            },
            "create": [
                {"rule_id": "lib-sd-op-police", "scope": POLICE_SCOPE},
                {"rule_id": "lib-sd-op-military", "scope": MILITARY_SCOPE},
            ],
            "shared": {
                "place_id": PLACE_ID,
                "zone_id": ZONE_ID,
                "source_id": SOURCE_ID,
                "evidence_bundle_id": EVIDENCE_BUNDLE_ID,
                "extraction_method": method,
                "note": COMPOUND_NOTE,
            },
        }
        if not args.apply:
            print(json.dumps({"dry_run": True, **plan}, ensure_ascii=False, indent=2))
            return 0

        results: dict[str, list] = {"updated": [], "created": []}

        # 1. the guide-dog member: re-model the existing row in place
        r = client.post(
            f"/api/v1/admin/candidates/{GUIDE_ROW_ID}/scope",
            json={**GUIDE_SCOPE, "reason": "ADR-028 拆分：导盲犬为独立 source-exact 行"},
            headers=headers,
        )
        r.raise_for_status()
        results["updated"].append(r.json())

        # 2. the two 军警犬 members: new candidates sharing the same evidence
        for spec in (POLICE_SCOPE, MILITARY_SCOPE):
            payload = {
                "source_id": SOURCE_ID,
                "place_id": PLACE_ID,
                "zone_id": ZONE_ID,
                "animal_scope": "dog",
                "action": "enter",
                "effect": "allowed",
                "rule_layer": "OPERATOR_POLICY",
                "mandatory_level": "operator_discretion",
                "extraction_method": method,
                "internal_confidence": confidence,
                "evidence_bundle_id": EVIDENCE_BUNDLE_ID,
                "raw_text": COMPOUND_NOTE,
                **spec,
            }
            created = client.post("/api/v1/admin/candidates", json=payload, headers=headers)
            created.raise_for_status()
            cand_id = created.json()["id"]
            # ingest starts at MATCH_PENDING; the review queue is REVIEW_PENDING
            tr = client.post(
                f"/api/v1/admin/candidates/{cand_id}/transition",
                json={"target": "REVIEW_PENDING", "note": "ADR-028 拆分后进入人工评审队列"},
                headers=headers,
            )
            tr.raise_for_status()
            results["created"].append(
                {
                    "rule_id": spec["subject_scope_normalized"],
                    "candidate_id": cand_id,
                    "scope": spec,
                    "review_status": tr.json()["review_status"],
                }
            )

        print(json.dumps({"applied": True, **results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
