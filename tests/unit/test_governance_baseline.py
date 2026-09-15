"""Governance protection for the human-review register (§13 / §78).

The register is what a human signs. Formatters, generators, builds and test runs
must not move it: same revision, same 37 rows, same recommendation distribution,
same RuleException bindings, and every human signature field still blank.

The assertions here read the *generated artifact on disk*, so they fail if a
tool rewrote the register rather than merely if the generator's logic changed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs" / "reality_audit" / "review_decisions_r2_final.json"
SNAPSHOT = ROOT / "scripts" / "governance_snapshot.py"

EXPECTED_REVISION = "R2-FINAL-R2"
EXPECTED_ROWS = 37
EXPECTED_DISTRIBUTION = {
    "RECOMMEND_APPROVE": 23,
    "RECOMMEND_HOLD": 9,
    "RECOMMEND_REJECT": 5,
}


@pytest.fixture(scope="module")
def register():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_revision_is_the_final_one(register):
    assert register["revision"] == EXPECTED_REVISION


def test_row_count_is_unchanged(register):
    assert len(register["rows"]) == EXPECTED_ROWS


def test_recommendation_distribution_is_unchanged(register):
    from collections import Counter

    counts = Counter(r["proposed_decision"] for r in register["rows"])
    for key, expected in EXPECTED_DISTRIBUTION.items():
        assert counts.get(key, 0) == expected, f"{key} drifted"


def test_no_human_signature_field_is_filled_in(register):
    filled = [
        r["rule_id"]
        for r in register["rows"]
        if r.get("final_decision") or r.get("reviewer") or r.get("reviewed_at")
    ]
    assert filled == [], f"an agent must never sign: {filled}"


def test_the_decision_sheet_is_also_blank():
    sheet = ROOT / "HUMAN_REVIEW_DECISIONS_R2_FINAL.json"
    doc = json.loads(sheet.read_text(encoding="utf-8"))
    assert doc["reviewer"] == ""
    assert doc["reviewed_at"] == ""
    assert all(row["final_decision"] == "" for row in doc["decisions"])


def test_no_exception_binding_crosses_a_layer(register):
    crossings = [
        (entry["rule_id"], base["rule_id"])
        for entry in register.get("exception_plan", [])
        for base in entry.get("bases", [])
        if not base.get("same_layer")
    ]
    assert crossings == [], f"cross-layer bindings: {crossings}"


def test_no_executable_exception_hangs_off_a_non_approved_base(register):
    offenders = [
        entry["rule_id"]
        for entry in register.get("exception_plan", [])
        if entry.get("executable")
        and any(b.get("decision") != "RECOMMEND_APPROVE" for b in entry.get("bases", []))
    ]
    assert offenders == [], f"executable exceptions on HOLD/REJECT bases: {offenders}"


def test_dry_run_holds_every_hold_row_and_publishes_nothing(register):
    """HOLD is not a decision to execute — it is a decision to wait (§13).

    This is the assertion the mutation probe flips: if ``run()`` stops short-
    circuiting HOLD, the held rows fall through into the publish branch.
    """
    import importlib.util

    script = ROOT / "scripts" / "publish_reviewed_r1.py"
    spec = importlib.util.spec_from_file_location("publish_reviewed_r1", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.run(register["rows"], None, execute=False)
    assert len(result["held"]) == EXPECTED_DISTRIBUTION["RECOMMEND_HOLD"]
    assert {h["rule_id"] for h in result["held"]} == {
        r["rule_id"] for r in register["rows"] if r["proposed_decision"] == "RECOMMEND_HOLD"
    }
    assert result["published"] == []
    assert result["failed"] == []


def test_the_snapshot_tool_reports_no_drift_against_the_baseline():
    """Runs scripts/governance_snapshot.py --compare baseline (exit 0 == unchanged)."""
    baseline = ROOT / "docs" / "reality_audit" / "snapshots" / "baseline.json"
    if not baseline.exists():
        pytest.skip("no baseline snapshot recorded yet")
    proc = subprocess.run(
        [sys.executable, str(SNAPSHOT), "--compare", "baseline"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert '"GOVERNANCE_BASELINE_UNCHANGED": "YES"' in proc.stdout


def test_the_snapshot_digest_is_stable_across_runs():
    sys.path.insert(0, str(ROOT / "scripts"))
    import governance_snapshot

    first = governance_snapshot.snapshot()
    second = governance_snapshot.snapshot()
    assert first["sha256"] == second["sha256"]
    # generated_at is excluded on purpose: it changes on every run
    assert "generated_at" not in first
