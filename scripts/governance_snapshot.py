"""Governance semantic snapshot — the pre/post comparison for a hardening pass.

A hardening round is allowed to touch code, tests, docs and tooling, but it must
not move the governance state by a single millimetre. This script freezes the
parts of the human-review register that are *semantic* (a human is going to sign
against them) and hashes them, so "nothing changed" is a fact rather than an
assertion.

What is captured
----------------
* ``revision`` — the register revision string (R2-FINAL-R2)
* ``row_count`` and the **ordered** candidate-id list
* the recommendation distribution (APPROVE / HOLD / REJECT)
* every ``RuleException`` binding, as ``(exception -> base, same_layer)`` triples
* the human signature fields — these must stay **empty**; the snapshot records
  how many are non-empty so a stray write is detectable at a glance

What is deliberately **not** captured: ``generated_at``, filesystem layout, and
any other value that legitimately changes every run.

Usage::

    python scripts/governance_snapshot.py --write baseline
    python scripts/governance_snapshot.py --compare baseline
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "docs" / "reality_audit"
REGISTRY = AUDIT / "review_decisions_r2_final.json"
SNAPSHOT_DIR = ROOT / "docs" / "reality_audit" / "snapshots"

#: The only recommendation values the register is allowed to carry. Anything
#: else means a generator bug or an unauthorised edit.
RECOMMENDATIONS = ("RECOMMEND_APPROVE", "RECOMMEND_HOLD", "RECOMMEND_REJECT")


def canonical(doc: dict[str, Any]) -> dict[str, Any]:
    """Reduce the register to the fields that carry governance meaning."""
    rows = doc.get("rows") or []
    bindings: list[dict[str, Any]] = []
    for entry in doc.get("exception_plan") or []:
        for base in entry.get("bases") or []:
            bindings.append(
                {
                    "exception": entry.get("rule_id"),
                    "exception_layer": entry.get("layer"),
                    "base": base.get("rule_id"),
                    "base_layer": base.get("layer"),
                    "same_layer": base.get("same_layer"),
                }
            )
    return {
        "revision": doc.get("revision"),
        "row_count": len(rows),
        "candidate_ids": sorted(str(r.get("candidate_id")) for r in rows),
        "rule_ids": sorted(str(r.get("rule_id")) for r in rows),
        "distribution": {
            key: int(Counter(str(r.get("proposed_decision")) for r in rows).get(key, 0))
            for key in RECOMMENDATIONS
        },
        "per_row_decision": {str(r.get("rule_id")): str(r.get("proposed_decision")) for r in rows},
        "exception_bindings": sorted(
            bindings,
            key=lambda b: (str(b["exception"]), str(b["base"])),
        ),
        "human_signature_nonempty": {
            "final_decision": sum(1 for r in rows if r.get("final_decision")),
            "reviewer": sum(1 for r in rows if r.get("reviewer")),
            "reviewed_at": sum(1 for r in rows if r.get("reviewed_at")),
        },
    }


def digest(doc: dict[str, Any]) -> str:
    """Stable sha256 over the canonical projection (sorted keys, UTF-8)."""
    blob = json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load() -> dict[str, Any]:
    if not REGISTRY.exists():
        print(f"registry not found: {REGISTRY}", file=sys.stderr)
        raise SystemExit(2)
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def snapshot() -> dict[str, Any]:
    doc = load()
    canon = canonical(doc)
    canon["source"] = str(REGISTRY.relative_to(ROOT)).replace("\\", "/")
    canon["sha256"] = digest(canon)
    return canon


def write(name: str) -> int:
    snap = snapshot()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    out = SNAPSHOT_DIR / f"{name}.json"
    out.write_text(
        json.dumps(snap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                "written": str(out.relative_to(ROOT)).replace("\\", "/"),
                "revision": snap["revision"],
                "row_count": snap["row_count"],
                "distribution": snap["distribution"],
                "human_signature_nonempty": snap["human_signature_nonempty"],
                "sha256": snap["sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def compare(name: str) -> int:
    snap = snapshot()
    ref_path = SNAPSHOT_DIR / f"{name}.json"
    if not ref_path.exists():
        print(f"baseline snapshot not found: {ref_path}", file=sys.stderr)
        return 2
    ref = json.loads(ref_path.read_text(encoding="utf-8"))
    diffs: list[str] = []
    for key in (
        "revision",
        "row_count",
        "candidate_ids",
        "rule_ids",
        "distribution",
        "per_row_decision",
        "exception_bindings",
        "human_signature_nonempty",
    ):
        if ref.get(key) != snap.get(key):
            diffs.append(key)
    result = {
        "baseline": str(ref_path.relative_to(ROOT)).replace("\\", "/"),
        "changed_keys": diffs,
        "sha256_before": ref.get("sha256"),
        "sha256_after": snap["sha256"],
        "GOVERNANCE_BASELINE_UNCHANGED": "YES" if not diffs else "NO",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not diffs else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", metavar="NAME", help="write a snapshot under docs/reality_audit/snapshots"
    )
    parser.add_argument(
        "--compare", metavar="NAME", help="diff the current register against a snapshot"
    )
    args = parser.parse_args()
    if args.write:
        return write(args.write)
    if args.compare:
        return compare(args.compare)
    print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
