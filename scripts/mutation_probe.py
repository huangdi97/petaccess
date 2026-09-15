"""Mutation-style assertion probe (§29).

A test suite that passes can still be a suite that asserts nothing. This script
deliberately breaks each governance invariant in the source, checks that the
protection actually fires, and then puts the source back byte-for-byte.

A protection is either:

* a **test** — mutate, run the tests, require them to go red; or
* a **generation-time guard** — mutate, run the generator, require it to refuse
  to write (the guard exists because some invariants must be impossible to emit,
  not merely easy to notice).

If a mutation survives (everything stays green), the invariant is *not actually
protected* and this script exits non-zero. That is the point of running it.

Usage::

    python scripts/mutation_probe.py            # run every mutation
    python scripts/mutation_probe.py --list     # show the mutations
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESOLVER = ROOT / "services" / "api" / "app" / "rulespec" / "v05_resolver.py"
PUBLISHER = ROOT / "scripts" / "publish_reviewed_r1.py"
GENERATOR = ROOT / "scripts" / "gen_human_review_packet_r2_final.py"


@dataclass(frozen=True)
class Mutation:
    """One deliberate break, and the protection that must catch it."""

    name: str
    invariant: str
    path: Path
    old: str
    new: str
    tests: tuple[str, ...] = ()
    command: tuple[str, ...] = field(default=())

    def apply(self) -> None:
        text = self.path.read_text(encoding="utf-8")
        if self.old not in text:
            raise SystemExit(f"[{self.name}] anchor not found in {self.path}:\n{self.old!r}")
        if text.count(self.old) != 1:
            raise SystemExit(f"[{self.name}] anchor is ambiguous in {self.path}")
        self.path.write_text(text.replace(self.old, self.new, 1), encoding="utf-8", newline="\n")


MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        name="legal_floor_removed",
        invariant="LEGAL > OPERATOR_POLICY: a mandatory statutory prohibition is the floor",
        path=RESOLVER,
        old="""            relaxes_prohibition = bool(mandatory_prohibited) and r.effect in (
                "allowed",
                "conditional",
            )""",
        new="""            relaxes_prohibition = False and bool(
                mandatory_prohibited
            ) and r.effect in (
                "allowed",
                "conditional",
            )""",
        tests=("tests/unit/test_domain_invariants.py", "tests/unit/test_v05_resolver.py"),
    ),
    Mutation(
        name="unknown_becomes_allowed",
        invariant="UNKNOWN != ALLOWED: absence of evidence is not permission",
        path=RESOLVER,
        old=(
            '            explanation_steps=["no in-scope rules in any layer"],\n'
            "            compliance_state=ComplianceState.UNKNOWN,\n"
            '            effect="unknown",'
        ),
        new=(
            '            explanation_steps=["no in-scope rules in any layer"],\n'
            "            compliance_state=ComplianceState.UNKNOWN,\n"
            '            effect="allowed",'
        ),
        tests=("tests/unit/test_domain_invariants.py", "tests/unit/test_v05_resolver.py"),
    ),
    Mutation(
        name="hold_becomes_publishable",
        invariant="HOLD cannot publish",
        path=PUBLISHER,
        old=(
            "        if fd == HOLD:\n"
            '            result["held"].append({"candidate_id": cid, "rule_id": rule_id})'
        ),
        new=(
            "        if False:\n"
            '            result["held"].append({"candidate_id": cid, "rule_id": rule_id})'
        ),
        tests=("tests/unit/test_governance_baseline.py",),
    ),
    Mutation(
        name="cross_layer_binding_allowed",
        invariant="an operator carve-out must never bind a LEGAL base rule",
        path=GENERATOR,
        old='        if same_layer_only and other["rule_layer"] != me["rule_layer"]:',
        new="        if False:",
        command=(sys.executable, str(GENERATOR)),
    ),
)


def _run(argv: list[str]) -> int:
    proc = subprocess.run(
        argv,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode


def probe(mutation: Mutation) -> bool:
    """Return True when the mutation was caught (protection fired)."""
    original = mutation.path.read_bytes()
    try:
        mutation.apply()
        if mutation.tests:
            return (
                _run(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        *mutation.tests,
                        "-q",
                        "--no-header",
                        "-p",
                        "no:cacheprovider",
                    ]
                )
                != 0
            )
        assert mutation.command, f"{mutation.name} has neither tests nor a command"
        return _run(list(mutation.command)) != 0
    finally:
        mutation.path.write_bytes(original)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list the mutations and exit")
    args = parser.parse_args()

    if args.list:
        for m in MUTATIONS:
            print(f"{m.name}: {m.invariant}")
        return 0

    survivors: list[str] = []
    for mutation in MUTATIONS:
        caught = probe(mutation)
        status = "CAUGHT" if caught else "SURVIVED"
        print(f"{status:9} {mutation.name:32} {mutation.invariant}")
        if not caught:
            survivors.append(mutation.name)

    if survivors:
        print("\nThese invariants are NOT actually protected:")
        for name in survivors:
            print(f"  - {name}")
        return 1
    print(f"\nAll {len(MUTATIONS)} mutations were caught; the suite asserts something real.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
