"""Probe the live consumer path for the Disney dog rule + guide-dog carve-out.

Why this file exists
--------------------
The publish is only meaningful if the *consumer* answers correctly, and the
interesting failures are all over-generalisations: a guide-dog proviso that
leaks to a generic service dog, a police dog or a military working dog. Those
are the answers that would put a real visitor in the wrong place, so they are
asserted separately rather than eyeballed in a table.

It talks to a running API (never to the database directly) because the point is
to exercise the shipped path, not the resolver in isolation.

Usage::

    python scripts/verify_scope_r2_disney_matrix.py --place-name 上海迪士尼乐园
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

DISNEY_ZONE = "2c868f71-96d3-40d9-894b-aec9315d7948"


#: label -> (body, check). A check returns None when satisfied, else a reason.
def _expect_effect(wanted: str):
    return lambda r: None if r["effect"] == wanted else f"effect={r['effect']!r}，期望 {wanted!r}"


def _expect_conditional_with_holder_missing(r):
    if r["effect"] != "conditional":
        return f"effect={r['effect']!r}，期望 'conditional'"
    if "holder_scope" not in r.get("missing_inputs", []):
        return f"missing_inputs={r.get('missing_inputs')}，应含 'holder_scope'"
    return None


def _expect_applied(r):
    applied = r.get("applied_exceptions") or []
    if not applied:
        return f"applied_exceptions={applied}，例外未被应用"
    return None


def _expect_not_allowed(r):
    if r["effect"] == "allowed":
        return "effect='allowed' —— 但书被过度泛化"
    return None


CASES: dict[str, tuple[dict, object]] = {
    "ordinary_dog": (
        {"animal": "dog", "service_role": "none", "action": "enter", "zone_id": DISNEY_ZONE},
        _expect_effect("prohibited"),
    ),
    "guide_dog_no_holder": (
        {
            "animal": "dog",
            "service_role": "guide_dog",
            "declared_role": "guide_dog",
            "action": "enter",
            "zone_id": DISNEY_ZONE,
        },
        _expect_conditional_with_holder_missing,
    ),
    "guide_dog_statutory_holder": (
        {
            "animal": "dog",
            "service_role": "guide_dog",
            "declared_role": "guide_dog",
            "holder_scopes": ["person_with_disability"],
            "action": "enter",
            "zone_id": DISNEY_ZONE,
        },
        _expect_applied,
    ),
    "generic_service_dog": (
        {
            "animal": "dog",
            "service_role": "service_dog",
            "action": "enter",
            "zone_id": DISNEY_ZONE,
        },
        _expect_not_allowed,
    ),
    "police_dog": (
        {
            "animal": "dog",
            "service_role": "service_dog",
            "declared_role": "police_dog",
            "action": "enter",
            "zone_id": DISNEY_ZONE,
        },
        _expect_not_allowed,
    ),
    "military_working_dog": (
        {
            "animal": "dog",
            "service_role": "service_dog",
            "declared_role": "military_working_dog",
            "action": "enter",
            "zone_id": DISNEY_ZONE,
        },
        _expect_not_allowed,
    ),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default="http://127.0.0.1:8010")
    ap.add_argument("--place-id", default=None)
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--token-file", default=None)
    args = ap.parse_args()

    headers = {}
    if args.token_file:
        headers["Authorization"] = f"Bearer {Path(args.token_file).read_text().strip()}"

    place_id = args.place_id
    with httpx.Client(base_url=args.base_url, timeout=20.0, trust_env=False, headers=headers) as c:
        if place_id is None:
            raise SystemExit("--place-id 必填（或用调用方查到的场所 id）")
        results: dict[str, dict] = {}
        failures: list[str] = []
        for label, (body, check) in CASES.items():
            resp = c.post(f"/api/v1/places/{place_id}/effective-rules", json=body)
            resp.raise_for_status()
            data = resp.json()
            results[label] = data
            reason = check(data)
            if reason is not None:
                failures.append(f"{label}: {reason}")
            applied = data.get("applied_exceptions") or []
            print(
                f"  {label:<28} effect={data['effect']:<12} "
                f"state={data.get('compliance_state')!s:<14} "
                f"applied={len(applied)} missing={data.get('missing_inputs')}"
            )

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(results, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"\nWROTE {args.json_out}")

    if failures:
        print("\nMATRIX = FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nMATRIX = PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
