"""Revision semantic-equivalence gate for the human-review register.

The register (`docs/reality_audit/review_decisions_r2_final.json`) is the
single source of truth for what a human is being asked to sign. Any change to
its *business* meaning invalidates the review packet that was handed out, so
this script exists to make that check mechanical instead of remembered.

It compares the live register against a frozen governance snapshot
(`docs/reality_audit/snapshots/baseline.json`) and prints one line per
invariant, so a reviewer can read the verdict without reading the code.

Exit codes:
    0 = SEMANTIC_EQUIVALENCE = PASS
    3 = a business-meaning change was detected (stop downstream work)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance_snapshot import REGISTRY, SNAPSHOT_DIR, canonical, load  # noqa: E402

EXPECTED_ROW_COUNT = 37
EXPECTED_DISTRIBUTION = {
    "RECOMMEND_APPROVE": 23,
    "RECOMMEND_HOLD": 9,
    "RECOMMEND_REJECT": 5,
}


def cross_layer_count(doc: dict) -> int:
    """Bindings whose exception and base rule live on different layers.

    A non-zero value means a carve-out is being applied across the layer
    boundary — the failure mode ADR-025 exists to prevent.
    """
    n = 0
    for entry in doc.get("exception_plan") or []:
        for base in entry.get("bases") or []:
            if base.get("same_layer") is False:
                n += 1
    return n


def main() -> int:
    doc = load()
    live = canonical(doc)
    snapshot_path = SNAPSHOT_DIR / "baseline.json"
    frozen = json.loads(snapshot_path.read_text(encoding="utf-8"))

    checks: list[tuple[str, bool, str]] = []

    checks.append(
        ("row count = 37", live["row_count"] == EXPECTED_ROW_COUNT, str(live["row_count"]))
    )

    ids_unchanged = live["candidate_ids"] == frozen.get("candidate_ids")
    checks.append(
        (
            "candidate ids unchanged",
            ids_unchanged,
            f"{len(live['candidate_ids'])} ids"
            if ids_unchanged
            else f"+{set(live['candidate_ids']) - set(frozen.get('candidate_ids', []))}",
        )
    )

    dist_ok = live["distribution"] == EXPECTED_DISTRIBUTION == frozen.get("distribution")
    checks.append(("distribution 23/9/5", dist_ok, str(live["distribution"])))

    bindings_unchanged = live["exception_bindings"] == frozen.get("exception_bindings")
    checks.append(
        (
            "RuleException binding semantics unchanged",
            bindings_unchanged,
            f"{len(live['exception_bindings'])} bindings",
        )
    )

    cross = cross_layer_count(doc)
    checks.append(("cross-layer override = 0", cross == 0, str(cross)))

    sig = live["human_signature_nonempty"]
    for field in ("final_decision", "reviewer", "reviewed_at"):
        checks.append((f"{field} all empty", sig[field] == 0, f"{sig[field]} filled"))

    print("== revision semantic equivalence ==")
    print(f"register        : {REGISTRY.relative_to(Path(__file__).resolve().parents[1])}")
    print(f"live revision   : {live['revision']}")
    print(f"frozen snapshot : {snapshot_path.name} (revision {frozen.get('revision')})")
    print()
    for label, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:<44} {detail}")

    failed = [label for label, ok, _ in checks if not ok]
    print()
    if failed:
        print("SEMANTIC_EQUIVALENCE = FAIL")
        for f in failed:
            print(f"  - {f}")
        return 3
    print("SEMANTIC_EQUIVALENCE = PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
