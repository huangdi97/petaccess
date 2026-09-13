"""Backfill rule_candidate.rule_layer from the evidence register (BLK-LAYER-01).

Migration d1a4f7c93b28 added the column with a server default of
OPERATOR_POLICY, which is the value the old publish path wrote anyway. The 33
real-pilot candidates were ingested before the column existed, so their true
layer (16 LEGAL + 2 TEMPORARY_POLICY + 15 OPERATOR_POLICY) lives only in
``docs/reality_audit/real_pilot_evidence.json``.

This script reconciles the two through the LIVE API and writes an audit entry
per changed row. It is idempotent: rows already carrying the right layer are
skipped.

Usage:
    python scripts/backfill_candidate_rule_layer.py --dry-run
    python scripts/backfill_candidate_rule_layer.py --execute
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "docs" / "reality_audit"
EVIDENCE = AUDIT / "real_pilot_evidence.json"
MANIFEST = AUDIT / "real_pilot_ingest_manifest.json"
BASE = "http://127.0.0.1:8010"


def expected_layers() -> dict[str, str]:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    index: dict[str, str] = manifest["rule_candidates"]
    out: dict[str, str] = {}
    for place in evidence["places"]:
        for rule in place["rules"]:
            cid = index[f"{place['key']}:{rule['rule_id']}"]
            out[cid] = rule.get("rule_layer") or "OPERATOR_POLICY"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--token", default=None)
    args = ap.parse_args()

    if not (args.dry_run ^ args.execute):
        print("必须且只能指定 --dry-run 或 --execute")
        return 2

    expected = expected_layers()
    by_layer: dict[str, int] = {}
    for layer in expected.values():
        by_layer[layer] = by_layer.get(layer, 0) + 1
    print(
        json.dumps(
            {"candidates": len(expected), "expected_layer_histogram": by_layer},
            ensure_ascii=False,
            indent=2,
        )
    )

    if args.dry_run:
        print(
            "dry-run：未写库。执行时逐条 POST /api/v1/admin/candidates/{id}/rule-layer 并留 audit。"
        )
        return 0

    token = args.token
    if not token:
        env = REPO / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("PILOT_ADMIN_TOKEN="):
                    token = line.split("=", 1)[1].strip()
    if not token:
        print("缺少 admin token（--token 或 .env PILOT_ADMIN_TOKEN）")
        return 4

    c = httpx.Client(
        base_url=BASE,
        timeout=30.0,
        trust_env=False,
        headers={"Authorization": f"Bearer {token}"},
    )
    changed, skipped, failed = 0, 0, 0
    for cid, layer in expected.items():
        r = c.post(f"/api/v1/admin/candidates/{cid}/rule-layer", json={"rule_layer": layer})
        if r.status_code == 404:
            failed += 1
            print(f"  ! {cid}: 端点不存在（需先部署 rule-layer 端点）")
            continue
        if r.status_code >= 400:
            failed += 1
            print(f"  ! {cid} -> {r.status_code}: {r.text[:160]}")
            continue
        if r.json().get("changed"):
            changed += 1
        else:
            skipped += 1
    print(
        json.dumps({"changed": changed, "skipped": skipped, "failed": failed}, ensure_ascii=False)
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
