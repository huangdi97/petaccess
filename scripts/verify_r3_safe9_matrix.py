"""Resolver matrix for the places touched by the SAFE-9 batch.

Used twice with the same code: once against the rehearsal clone (which already
carries the batch, so it defines the expected state) and once against production
after the real publish. Identical output is the evidence that the rehearsal
predicted the production result; a difference is a finding, not a rounding error.

The matrix deliberately includes the roles that a careless publish would
over-generalise: a generic `service_dog` and a `police_dog` must never come back
`allowed` just because a guide-dog carve-out exists nearby.

Usage::

    python scripts/verify_r3_safe9_matrix.py --base-url http://127.0.0.1:8010 --out <path>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

PLACES = {
    "上海迪士尼乐园": "d85a4c00-3be9-48a5-ac31-d0486451ba69",
    "港汇恒隆广场": "ae797630-12dd-4f3b-8233-a3f3d0253a46",
    "Manner咖啡（凯德虹口商业中心店）": "a44f56b5-fab0-4ebe-8cdf-b8900c0efe77",
    "前滩太古里": "3fef5239-1588-45d1-b03e-e1e3e8ec28c1",
    "星巴克咖啡（徐汇西岸梦中心店）": "91bdaeba-2841-4aa8-88fe-5aa55a2df8b9",
}

QUERIES = {
    "ordinary_dog": {"animal": "dog", "service_role": "none"},
    "ordinary_cat": {"animal": "cat", "service_role": "none"},
    "guide_dog_no_holder": {
        "animal": "dog",
        "service_role": "guide_dog",
        "declared_role": "guide_dog",
    },
    "guide_dog_statutory_holder": {
        "animal": "dog",
        "service_role": "guide_dog",
        "declared_role": "guide_dog",
        "holder_scopes": ["person_with_disability"],
    },
    "generic_service_dog": {"animal": "dog", "service_role": "service_dog"},
    "police_dog": {
        "animal": "dog",
        "service_role": "service_dog",
        "declared_role": "police_dog",
    },
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default="http://127.0.0.1:8010")
    ap.add_argument("--out")
    args = ap.parse_args()

    matrix: dict[str, dict] = {}
    with httpx.Client(base_url=args.base_url, timeout=30.0, trust_env=False) as c:
        for label, pid in PLACES.items():
            place_out: dict[str, dict] = {}
            zones = c.get(f"/api/v1/places/{pid}/zones")
            zone_list = zones.json() if zones.status_code == 200 else []
            for qlabel, body in QUERIES.items():
                # Place level first: it must NOT inherit any zone rule (that is
                # the flattening this platform refuses to do).
                targets = [("place", None)]
                targets += [(z["name"], z["id"]) for z in zone_list]
                for zlabel, zid in targets:
                    payload = {**body, "action": "enter", "zone_id": zid}
                    r = c.post(f"/api/v1/places/{pid}/effective-rules", json=payload)
                    key = f"{qlabel}@{zlabel}"
                    if r.status_code != 200:
                        place_out[key] = {"error": f"HTTP {r.status_code}"}
                        continue
                    d = r.json()
                    place_out[key] = {
                        "effect": d.get("effect"),
                        "compliance_state": d.get("compliance_state"),
                        "applicable_rules": sorted(d.get("applicable_rules") or []),
                        "applied_exceptions": sorted(d.get("applied_exceptions") or []),
                        "missing_inputs": sorted(d.get("missing_inputs") or []),
                        "normative_effects": sorted(d.get("normative_effects") or []),
                    }
            matrix[label] = place_out

    # Invariants that do not depend on my guessing a value in advance.
    problems: list[str] = []
    for label, row in matrix.items():
        for key, data in row.items():
            if "error" in data:
                continue
            qlabel = key.split("@", 1)[0]
            if qlabel in ("generic_service_dog", "police_dog") and data["effect"] == "allowed":
                problems.append(f"{label}/{key}: effect=allowed —— 但书外溢")
            if qlabel == "guide_dog_no_holder" and data["effect"] == "allowed":
                problems.append(f"{label}/{key}: 未声明 holder 却无条件允许")
        # A zone rule must never become a place verdict.
        for key, data in row.items():
            if key.endswith("@place") and data.get("effect") == "prohibited":
                problems.append(f"{label}/place: 场所级被判 prohibited —— zone 规则被压平")

    if args.out:
        Path(args.out).write_text(
            json.dumps({"base_url": args.base_url, "matrix": matrix, "problems": problems},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"base_url = {args.base_url}")
    for label, row in matrix.items():
        print(f"\n=== {label}")
        for qlabel, data in row.items():
            if "error" in data:
                print(f"  {qlabel:<48} {data['error']}")
                continue
            print(
                f"  {qlabel:<48} effect={data['effect']:<12} state={data['compliance_state']:<16}"
                f" rules={len(data['applicable_rules'])}"
                f" applied={len(data['applied_exceptions'])} missing={data['missing_inputs']}"
            )
    print(f"\nproblems = {problems}")
    print(f"MATRIX = {'PASS' if not problems else 'FAIL'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
