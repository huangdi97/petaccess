"""WAVE_01 §55–§57 / §78 regression: the three published places must answer
exactly what they answered before Wave-01.

Wave-01 adds 10 new places, 12 new sources and 31 review-pending candidates.
None of that is allowed to move the answers of the places that were already
published under ``R2-FINAL-R3-BATCH-01B``.

The baseline is not a guess: it is the resolver matrix captured by
``scripts/verify_publish_r3.py`` immediately after the first real publish
(``artifacts/integrity_final_closure/VERIFY_PUBLISH_BATCH01B_FINAL.json``,
2026-09-17). This script replays the *same* 15 queries against the live API and
diffs every answer field — effect, compliance_state, applied_exceptions,
applicable_rule_count and the explanation steps — not just the top-level effect.

Usage:
    python scripts/expansion_w01_resolver_regression.py \\
        --out artifacts/expansion_w01/RESOLVER_REGRESSION_AFTER_WAVE01.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
BASELINE = REPO / "artifacts" / "integrity_final_closure" / "VERIFY_PUBLISH_BATCH01B_FINAL.json"
DEFAULT_OUT = REPO / "artifacts" / "expansion_w01" / "RESOLVER_REGRESSION_AFTER_WAVE01.json"

#: Same matrix as verify_publish_r3.check_resolver. Do NOT "improve" it here —
#: a changed matrix would silently stop being a regression test.
QUERIES: dict[str, dict[str, str]] = {
    "ordinary_pet": {"animal": "dog", "service_role": "none"},
    "guide_dog": {"animal": "dog", "service_role": "working", "declared_role": "guide_dog"},
    "police_dog": {"animal": "dog", "service_role": "working", "declared_role": "police_dog"},
    "military_working_dog": {
        "animal": "dog",
        "service_role": "working",
        "declared_role": "military_working_dog",
    },
}
NO_ZONE_QUERY = {"animal": "dog", "service_role": "working", "declared_role": "guide_dog"}
COMPARE_FIELDS = (
    "effect",
    "compliance_state",
    "applied_exceptions",
    "applicable_rule_count",
    "explanation_steps",
)


def replay(client: httpx.Client, base: str, obs: dict) -> dict:
    if obs["query"] == "guide_dog_place_level_no_zone":
        # zone 级规则不得压平成 place 总状态：不带 zone_id 地问一次
        body = {"action": "enter", **NO_ZONE_QUERY}
        eff = client.post(f"{base}/api/v1/places/{obs['place_id']}/effective-rules", json=body)
    else:
        body = {"action": "enter", "zone_id": obs["zone_id"], **QUERIES[obs["query"]]}
        eff = client.post(f"{base}/api/v1/places/{obs['place_id']}/effective-rules", json=body)
    eff.raise_for_status()
    payload = eff.json()
    return {
        "place": obs["place"],
        "query": obs["query"],
        "zone_id": obs["zone_id"],
        "effect": payload.get("effect"),
        "compliance_state": payload.get("compliance_state"),
        "applied_exceptions": payload.get("applied_exceptions") or [],
        "applicable_rule_count": len(payload.get("applicable_rules") or []),
        "explanation_steps": payload.get("explanation_steps") or [],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8010")
    ap.add_argument("--baseline", default=str(BASELINE))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    doc = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    baseline_obs = doc["resolver"]["observations"]
    places = doc["places"]

    # place key -> place_id (the baseline observations only carry the key)
    by_id = {str(v["place_id"]): k for k, v in places.items()}
    enriched = []
    for o in baseline_obs:
        pid = next(
            (str(v["place_id"]) for k, v in places.items() if k == o["place"]),
            None,
        )
        enriched.append({**o, "place_id": pid, "place_key_confirmed": by_id.get(pid or "")})

    diffs: list[str] = []
    current_rows: list[dict] = []
    with httpx.Client(timeout=20.0) as client:
        for o in enriched:
            got = replay(client, args.base_url.rstrip("/"), o)
            current_rows.append(got)
            for f in COMPARE_FIELDS:
                # The no-zone baseline rows only record effect / compliance_state;
                # the other fields were never captured there, so a missing key is
                # "not observed", not "changed to null".
                if f not in o:
                    continue
                if o[f] != got.get(f):
                    diffs.append(
                        f"{o['place']}/{o['query']}.{f}: "
                        f"{json.dumps(o.get(f), ensure_ascii=False)} -> "
                        f"{json.dumps(got.get(f), ensure_ascii=False)}"
                    )

    out = {
        "baseline": str(args.baseline),
        "baseline_at": doc.get("at"),
        "base_url": args.base_url,
        "queries_replayed": len(enriched),
        "places": sorted(places.keys()),
        "RESOLVER_REGRESSION_WAVE01": "PASS" if not diffs else "FAIL",
        "diffs": diffs,
        "current": current_rows,
    }
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps({k: v for k, v in out.items() if k != "current"}, ensure_ascii=False, indent=2)
    )
    print(f"WROTE {args.out}")
    return 0 if not diffs else 1


if __name__ == "__main__":
    sys.exit(main())
