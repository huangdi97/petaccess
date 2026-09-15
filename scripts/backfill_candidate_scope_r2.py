"""Backfill candidate animal scope from the review register into the database (ADR-025).

Why this is required before sign-off
------------------------------------

The register records what each candidate's scope *should* be, read faithfully from
its source. The database still holds the pre-ADR-025 value for the service-dog
rows (``animal_scope='service_dog'`` with no legal normalisation), which the
resolver now treats as the unproven widening — it governs nothing.

Two consequences if the two are left out of sync:

  * the publish gate refuses such a candidate (``service_dog_scope_unproven``), so
    a signed batch would fail at the boundary; and
  * were the gate passed, the published rule would be inert — 导盲犬 would lose the
    exemption the source actually grants.

Every write goes through the **audited admin API** (``candidate.set_scope``), never
raw SQL, so each correction leaves a before/after audit record.

Idempotent: rows already at the target scope are reported as ``unchanged``.

Usage: python scripts/backfill_candidate_scope_r2.py [--apply]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx

REPO = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8010"
REGISTRY_R2 = REPO / "docs" / "reality_audit" / "review_decisions_r2.json"

LEGAL_NORMS = {"exact", "compound_term_split"}
ADMIN_EMAIL = "scope-split-ops@example.com"


def _token() -> str:
    with httpx.Client(base_url=BASE, timeout=30) as c:
        r = c.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": "passw0rd123"},
        )
        r.raise_for_status()
        return r.json()["access_token"]


def _candidate(client: httpx.Client, headers: dict, candidate_id: str) -> dict | None:
    """Look the candidate up through the place-scoped listing (paginated-safe)."""
    r = client.get("/api/v1/admin/candidates", params={"limit": 200}, headers=headers)
    r.raise_for_status()
    for row in r.json()["items"]:
        if row["id"] == candidate_id:
            return row
    # fall back to paging
    offset = 200
    while offset < 2000:
        r = client.get(
            "/api/v1/admin/candidates",
            params={"limit": 200, "offset": offset},
            headers=headers,
        )
        r.raise_for_status()
        items = r.json()["items"]
        if not items:
            return None
        for row in items:
            if row["id"] == candidate_id:
                return row
        offset += 200
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = json.loads(REGISTRY_R2.read_text(encoding="utf-8"))["rows"]
    targets = [
        r
        for r in rows
        if r.get("subject_scope_normalized") and r.get("normalization_type") in LEGAL_NORMS
    ]

    token = _token()
    headers = {"Authorization": f"Bearer {token}"}

    # Mixed value types (lists of ids + scalar run metadata), so `Any` it is.
    report: dict[str, Any] = {
        "changed": [],
        "unchanged": [],
        "skipped": [],
        "missing": [],
    }
    with httpx.Client(base_url=BASE, timeout=60) as client:
        for row in targets:
            current = _candidate(client, headers, row["candidate_id"])
            if current is None:
                report["missing"].append(row["rule_id"])
                continue
            already = (
                current.get("subject_scope_normalized") == row["subject_scope_normalized"]
                and current.get("normalization_type") == row["normalization_type"]
                and current.get("source_scope_exact") == row["source_scope_exact"]
            )
            if already:
                report["unchanged"].append(row["rule_id"])
                continue
            payload = {
                "source_scope_exact": row["source_scope_exact"],
                "subject_scope_normalized": row["subject_scope_normalized"],
                "normalization_type": row["normalization_type"],
                "normative_effect": row.get("normative_effect"),
                "holder_scope": row.get("holder_scope"),
                "reason": "ADR-025：按来源原话回填精确 scope（导盲犬 ≠ 全部服务犬）",
            }
            if not args.apply:
                report["changed"].append({"rule_id": row["rule_id"], "to": payload})
                continue
            r = client.post(
                f"/api/v1/admin/candidates/{row['candidate_id']}/scope",
                json=payload,
                headers=headers,
            )
            r.raise_for_status()
            report["changed"].append({"rule_id": row["rule_id"], "result": r.json()})

    report["skipped"] = [
        r["rule_id"]
        for r in rows
        if not (r.get("subject_scope_normalized") and r.get("normalization_type") in LEGAL_NORMS)
    ]
    report["apply"] = bool(args.apply)
    report["target_count"] = len(targets)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
