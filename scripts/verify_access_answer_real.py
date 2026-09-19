"""AccessAnswer against the real published Century Park row (design §10 / §7).

The point is not that the endpoint returns 200. It is that the answer a consumer
would see states **where the rule came from** — a government platform relaying
the operator's wording, with no first-party operator source obtained — and that
the two over-generalisations are absent:

* the uncovered zone (世纪宠物乐园) must not read as `allowed`;
* a query without a zone must not inherit the zone rule's prohibition.

Run against a live API pointed at production, read-only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

PLACE_ID = "c63f2199-b1e4-4435-b418-f2e86f8fdf45"
ZONE_OTHER = "aee59c64-a9b2-4a69-acd6-1a922f55d127"  # 世纪公园其他区域
ZONE_PET_AREA = "ae0003a8-e7ad-4d32-b29d-f8f21892e35b"  # 世纪宠物乐园（芳花园区域）

FORBIDDEN = ("官方已确认", "官方确认", "运营方已确认", "一手来源已核验", "first-party verified")

CASES = {
    "ordinary_pet_in_rule_zone": (
        {"animal": "dog", "service_role": "none", "action": "enter", "zone_id": ZONE_OTHER},
        "prohibited",
    ),
    "ordinary_pet_in_uncovered_zone": (
        {"animal": "dog", "service_role": "none", "action": "enter", "zone_id": ZONE_PET_AREA},
        "unknown",
    ),
    "ordinary_pet_place_level": (
        {"animal": "dog", "service_role": "none", "action": "enter", "zone_id": None},
        "unknown",
    ),
    "guide_dog_in_rule_zone": (
        {
            "animal": "dog",
            "service_role": "guide_dog",
            "declared_role": "guide_dog",
            "action": "enter",
            "zone_id": ZONE_OTHER,
        },
        "not_allowed",
    ),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default="http://127.0.0.1:8010")
    ap.add_argument("--json-out")
    args = ap.parse_args()

    results: dict[str, dict] = {}
    failures: list[str] = []
    with httpx.Client(base_url=args.base_url, timeout=30.0, trust_env=False) as c:
        for label, (body, expected) in CASES.items():
            r = c.post(f"/api/v1/places/{PLACE_ID}/access-answer", json=body)
            if r.status_code != 200:
                failures.append(f"{label}: HTTP {r.status_code} {r.text[:200]}")
                continue
            results[label] = r.json()
            data = results[label]
            got = data["normative_result"]["effect"]
            if expected == "not_allowed":
                if got == "allowed":
                    failures.append(f"{label}: effect='allowed' —— 未举证的允许")
            elif got != expected:
                failures.append(f"{label}: effect={got!r}，期望 {expected!r}")
            blob = json.dumps(data, ensure_ascii=False)
            for claim in FORBIDDEN:
                if claim in blob:
                    failures.append(f"{label}: 出现越权表述 {claim!r}")

        # the zone rule must not leak into the place-level answer
        if "ordinary_pet_place_level" in results:
            scope = results["ordinary_pet_place_level"]["scope_summary"]
            if scope["scope_level"] == "zone":
                failures.append("place 级查询的 scope_level 被报成 zone")
            if results["ordinary_pet_place_level"]["normative_result"]["effect"] == "prohibited":
                failures.append("zone 规则被压平成 place 级 prohibited")

        # provenance must be visible on the governing answer
        if "ordinary_pet_in_rule_zone" in results:
            ev = results["ordinary_pet_in_rule_zone"]["evidence_state"]
            if not ev["rules"]:
                failures.append("规则 zone 的答案没有 evidence_state.rules")
            else:
                entry = ev["rules"][0]
                if entry["source_type"] != "government_service":
                    failures.append(f"source_type={entry['source_type']!r}")
                if entry["source_type_semantics"] != "政府平台转述园方口径":
                    failures.append(f"语义={entry['source_type_semantics']!r}")
                if entry["first_party_operator_source_pending"] is not True:
                    failures.append("first_party_operator_source_pending 应为 true")

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print("=== ACCESS ANSWER (live API, production data) ===")
    for label, data in results.items():
        nr = data["normative_result"]
        sc = data["scope_summary"]
        ev = data["evidence_state"]
        print(
            f"  {label:<32} effect={nr['effect']:<11} scope={sc['scope_level']:<11} "
            f"rules={len(nr['governing_rule_ids'])} "
            f"fp_pending={ev['first_party_operator_source_pending']}"
        )
    if "ordinary_pet_in_rule_zone" in results:
        entry = results["ordinary_pet_in_rule_zone"]["evidence_state"]["rules"][0]
        print()
        print("  provenance:", entry["provenance_statement"])
        print("  summary   :", results["ordinary_pet_in_rule_zone"]["normative_result"]["summary"])
        print("  next      :", results["ordinary_pet_in_rule_zone"]["next_actions"])
    print()
    print(f"failures = {failures}")
    print(f"ACCESS_ANSWER_REAL = {'PASS' if not failures else 'FAIL'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
