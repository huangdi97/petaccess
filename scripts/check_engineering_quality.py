#!/usr/bin/env python3
"""Engineering quality gate for petaccess v0.1.0 (M1) — entry point.

Aggregates the check functions from `engineering_quality_checks.py` and
applies the explicit exemption registry (`scripts/gate_exemptions.json`).
Every exemption must reference a documented reason in
docs/audit/V010_TECH_DEBT_REGISTER.md — no path-based blanket ignores.

Usage:
    uv run python scripts/check_engineering_quality.py            # full gate
    uv run python scripts/check_engineering_quality.py --json     # machine report
    uv run python scripts/check_engineering_quality.py --dump     # all violations

Exit code: 0 = PASS (no unregistered FAIL), 1 = FAIL.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engineering_quality_checks import check_functions, check_size, dependency_cycles
from engineering_quality_scan import check_todos, check_ts_colors, check_type_escapes

ROOT = Path(__file__).resolve().parent.parent
EXEMPTIONS_FILE = ROOT / "scripts" / "gate_exemptions.json"
PY_ROOTS = [ROOT / "services/api/app", ROOT / "services/worker"]
TS_ROOTS = [ROOT / "apps/client-h5/src", ROOT / "apps/admin/src", ROOT / "packages/client-core/src"]


def load_exemptions() -> list[dict]:
    if not EXEMPTIONS_FILE.exists():
        return []
    data = json.loads(EXEMPTIONS_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "exemptions" not in data:
        raise SystemExit(f"invalid exemptions file: {EXEMPTIONS_FILE}")
    return data["exemptions"]


def collect() -> list[dict]:
    exemptions = load_exemptions()
    out: list[dict] = []
    out += check_size(exemptions, PY_ROOTS, TS_ROOTS)
    out += check_functions(exemptions, PY_ROOTS)
    cycles = dependency_cycles(PY_ROOTS)
    out += [{"rule": "cycle", "path": "**", "severity": "FAIL", "detail": c} for c in cycles]
    out += check_type_escapes(exemptions, PY_ROOTS, TS_ROOTS)
    out += check_todos(exemptions, PY_ROOTS, TS_ROOTS)
    out += check_ts_colors(exemptions, TS_ROOTS)
    return out


def render_human(violations: list[dict]) -> str:
    lines = ["engineering quality gate summary"]
    for sev, label in (("FAIL", "FAIL"), ("REVIEW", "review"), ("WARN", "warn")):
        hits = [v for v in violations if v["severity"] == sev]
        lines.append(f"  {label:<7s}{len(hits)}")
        for v in hits[:12]:
            lines.append(f"    {v['rule']:15s} {v['path']} :: {v['detail']}")
        if len(hits) > 12:
            lines.append(f"    ... {len(hits) - 12} more")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="petaccess engineering quality gate (M1)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable report")
    ap.add_argument("--dump", action="store_true", help="print every violation")
    args = ap.parse_args()

    violations = collect()
    fails = [v for v in violations if v["severity"] == "FAIL"]
    review = [v for v in violations if v["severity"] == "REVIEW"]
    warns = [v for v in violations if v["severity"] == "WARN"]

    if args.json:
        json.dump(
            {
                "violations": violations,
                "fail": len(fails),
                "review": len(review),
                "warn": len(warns),
            },
            sys.stdout,
            indent=2,
        )
        return 1 if fails else 0
    if args.dump:
        for v in violations:
            print(f"[{v['severity']:<6}] {v['rule']:15s} {v['path']} :: {v['detail']}")
        return 1 if fails else 0
    print(render_human(violations))
    status = "FAIL" if fails else "PASS"
    print(f"RESULT: {status} ({len(fails)} FAIL / {len(review)} REVIEW / {len(warns)} WARN)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
