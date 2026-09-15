"""Backfill rule_candidate normative fields from the evidence register.

BLK-LAYER-01 / BLK-LAYER-02 (ADR-023).

Migration d1a4f7c93b28 added ``rule_candidate.rule_layer`` with a server default
of OPERATOR_POLICY, which is the value the old publish path wrote anyway. The 33
real-pilot candidates were ingested before that column existed, so their true
layer (16 LEGAL + 2 TEMPORARY_POLICY + 15 OPERATOR_POLICY) lives only in
``docs/reality_audit/real_pilot_evidence.json``.

``mandatory_level`` (added later by e3b7a1c4f920) is stale for the same reason:
every row reads ``operator_discretion``, so the 16 statutory rules would publish
without their binding force — the exact silent downgrade ADR-023 exists to
prevent. The level is therefore reconciled alongside the layer, using the same
deterministic mapping the ingest applies (LEGAL → mandatory, everything else →
operator_discretion); an explicit ``mandatory_level`` in the evidence wins.

Both fields are written through the **live API**, so every change produces an
audit entry (``candidate.set_rule_layer`` / ``candidate.set_mandatory_level``)
and a published candidate is refused rather than mutated. The script is
idempotent: rows already carrying the right values are reported as skipped.

Usage:
    python scripts/backfill_candidate_rule_layer.py --dry-run
    python scripts/backfill_candidate_rule_layer.py --execute --token <admin JWT>
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

DEFAULT_LAYER = "OPERATOR_POLICY"


def expected_fields() -> dict[str, tuple[str, str]]:
    """candidate_id -> (rule_layer, mandatory_level), from the evidence register."""
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    index: dict[str, str] = manifest["rule_candidates"]
    out: dict[str, tuple[str, str]] = {}
    for place in evidence["places"]:
        for rule in place["rules"]:
            cid = index[f"{place['key']}:{rule['rule_id']}"]
            layer = rule.get("rule_layer") or DEFAULT_LAYER
            level = rule.get("mandatory_level") or (
                "mandatory" if layer == "LEGAL" else "operator_discretion"
            )
            out[cid] = (layer, level)
    return out


def _histogram(pairs: list[tuple[str, str]], idx: int) -> dict[str, int]:
    hist: dict[str, int] = {}
    for pair in pairs:
        hist[pair[idx]] = hist.get(pair[idx], 0) + 1
    return hist


def _resolve_token(cli_token: str | None) -> str | None:
    if cli_token:
        return cli_token
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("PILOT_ADMIN_TOKEN="):
                return line.split("=", 1)[1].strip()
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--token", default=None)
    ap.add_argument("--base", default=BASE)
    args = ap.parse_args()

    if not (args.dry_run ^ args.execute):
        print("必须且只能指定 --dry-run 或 --execute")
        return 2

    expected = expected_fields()
    pairs = list(expected.values())
    print(
        json.dumps(
            {
                "candidates": len(expected),
                "expected_layer_histogram": _histogram(pairs, 0),
                "expected_mandatory_histogram": _histogram(pairs, 1),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    if args.dry_run:
        print(
            "dry-run：未写库。执行时逐条 POST "
            "/api/v1/admin/candidates/{id}/rule-layer 与 /mandatory-level 并留 audit。"
        )
        return 0

    token = _resolve_token(args.token)
    if not token:
        print("缺少 admin token（--token 或 .env PILOT_ADMIN_TOKEN）")
        return 4

    c = httpx.Client(
        base_url=args.base,
        timeout=30.0,
        trust_env=False,
        headers={"Authorization": f"Bearer {token}"},
    )

    layer_changed = layer_same = level_changed = level_same = failed = 0
    for cid, (layer, level) in expected.items():
        for path, payload, kind in (
            (f"/api/v1/admin/candidates/{cid}/rule-layer", {"rule_layer": layer}, "layer"),
            (
                f"/api/v1/admin/candidates/{cid}/mandatory-level",
                {
                    "mandatory_level": level,
                    "reason": "BLK-LAYER-02 backfill from evidence register",
                },
                "level",
            ),
        ):
            r = c.post(path, json=payload)
            if r.status_code >= 400:
                failed += 1
                print(f"  ! {cid} {kind} -> {r.status_code}: {r.text[:160]}")
                continue
            changed = bool(r.json().get("changed"))
            if kind == "layer":
                layer_changed += changed
                layer_same += not changed
            else:
                level_changed += changed
                level_same += not changed

    print(
        json.dumps(
            {
                "layer": {"changed": layer_changed, "already_correct": layer_same},
                "mandatory_level": {"changed": level_changed, "already_correct": level_same},
                "failed": failed,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
