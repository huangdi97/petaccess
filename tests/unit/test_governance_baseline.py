"""Governance protection for the human-review register, now that it is signed.

The register is what a human signs. Formatters, generators, builds and test runs
must not move it: same revision, same 37 rows, same recommendation distribution,
same RuleException bindings — and, since 2026-09-16 (commit 8ac1925), a complete
signature by one named human that no tool may erase.

These four assertions used to read "every sign-off field is still blank". That
was the correct pre-signature checkpoint and it did its job; asserting it after
the signature would be asserting something false. They are now the *post*
signature form of the same intent: the signature is present, whole, single-
reviewer, timezone-aware, and the only thing that differs from the pre-signature
baseline. Deleting them would have removed the protection with the assertion.

The assertions here read the *generated artifact on disk*, so they fail if a
tool rewrote the register rather than merely if the generator's logic changed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs" / "reality_audit" / "review_decisions_r2_final.json"
SNAPSHOT = ROOT / "scripts" / "governance_snapshot.py"

EXPECTED_REVISION = "R2-FINAL-R3"
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


def test_every_human_signature_field_is_filled_in(register):
    """The post-signature form of "an agent must never sign".

    The old assertion refused any non-empty field, because the only way one could
    be non-empty was an unauthorised write. Now that the named human has signed,
    the dangerous states are (a) a half-signed register and (b) a signature on a
    row that the sign-off sheet does not corroborate. Both fail here.
    """
    incomplete = [
        (r["rule_id"], field)
        for r in register["rows"]
        for field in ("final_decision", "reviewer", "reviewed_at")
        if not str(r.get(field) or "").strip()
    ]
    assert incomplete == [], f"签署不完整：{incomplete[:6]}"
    reviewers = {r["reviewer"] for r in register["rows"]}
    assert reviewers == {"huangdi97"}, f"reviewer 必须唯一且为具名人类：{reviewers}"
    stamps = {r["reviewed_at"] for r in register["rows"]}
    assert len(stamps) == 1
    assert datetime.fromisoformat(next(iter(stamps))).utcoffset() is not None


def test_the_decision_sheet_carries_the_same_signature():
    """The two files a reviewer owns must agree, field for field."""
    sheet = ROOT / "HUMAN_REVIEW_DECISIONS_R2_FINAL.json"
    doc = json.loads(sheet.read_text(encoding="utf-8"))
    register = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert doc["reviewer"] == "huangdi97"
    assert doc["reviewed_at"] == register["rows"][0]["reviewed_at"]
    signed = {r["candidate_id"]: r["final_decision"] for r in register["rows"]}
    for row in doc["decisions"]:
        assert row["final_decision"] == signed[row["candidate_id"]], row["candidate_id"]
    assert all(row["final_decision"] for row in doc["decisions"]), "逐条决策文件不得留有未填项"


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

    This is the assertion the mutation probe flips: if the planner stops
    short-circuiting HOLD, the held rows fall through into the publish branch.

    Selection is by the **human** ``final_decision``, not by the machine's
    ``proposed_decision``. The two happen to agree on this register, so the test
    would have passed either way — which is exactly why it is written against the
    decision that authorises publication.
    """
    import importlib.util

    script = ROOT / "scripts" / "publish_reviewed_r1.py"
    spec = importlib.util.spec_from_file_location("publish_reviewed_r1", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.run(register["rows"], None, execute=False)
    human_hold = {r["rule_id"] for r in register["rows"] if r["final_decision"] == "HOLD"}
    human_reject = {r["rule_id"] for r in register["rows"] if r["final_decision"] == "REJECTED"}
    assert len(human_hold) == EXPECTED_DISTRIBUTION["RECOMMEND_HOLD"]
    assert {h["rule_id"] for h in result["held"]} == human_hold
    assert {r["rule_id"] for r in result["rejected"]} == human_reject
    assert result["published"] == []
    assert result["failed"] == []


def test_the_snapshot_tool_reports_no_drift_against_the_post_signature_snapshot():
    """Runs the snapshot tool against the **post-signature** snapshot.

    It used to compare against the pre-signature baseline, which cannot match
    once anyone signs — the digest covers the signature-field counts on purpose.
    Requiring that match after a signature would have meant either never signing
    or deleting the check. Comparing against the signed snapshot keeps the real
    guarantee ("nothing has moved since the signature") and a separate test below
    proves the *only* thing that moved at signing time was the signature.
    """
    snapshot = ROOT / "docs" / "reality_audit" / "snapshots" / "post_human_signature_r3.json"
    if not snapshot.exists():
        pytest.skip("no post-signature snapshot recorded yet")
    proc = subprocess.run(
        [sys.executable, str(SNAPSHOT), "--compare", "post_human_signature_r3"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert '"GOVERNANCE_BASELINE_UNCHANGED": "YES"' in proc.stdout


def test_signing_moved_nothing_but_the_signature():
    """Pre-signature baseline vs post-signature snapshot: same governance, signed.

    The non-signature projection must be identical; only the sign-off counts may
    differ. This is what makes "the human signed, and nothing else happened" a
    checked fact instead of a claim in a report.
    """
    before_path = ROOT / "docs" / "reality_audit" / "snapshots" / "baseline.json"
    after_path = ROOT / "docs" / "reality_audit" / "snapshots" / "post_human_signature_r3.json"
    if not (before_path.exists() and after_path.exists()):
        pytest.skip("both snapshots are required for this comparison")
    before = json.loads(before_path.read_text(encoding="utf-8"))
    after = json.loads(after_path.read_text(encoding="utf-8"))
    moved = [
        key
        for key in (
            "revision",
            "row_count",
            "candidate_ids",
            "rule_ids",
            "distribution",
            "per_row_decision",
            "exception_bindings",
        )
        if before[key] != after[key]
    ]
    assert moved == [], f"签署之外还动了：{moved}"
    assert before["human_signature_nonempty"]["final_decision"] == 0
    assert after["human_signature_nonempty"] == {
        "final_decision": 37,
        "reviewer": 37,
        "reviewed_at": 37,
    }


def test_the_snapshot_digest_is_stable_across_runs():
    sys.path.insert(0, str(ROOT / "scripts"))
    import governance_snapshot

    first = governance_snapshot.snapshot()
    second = governance_snapshot.snapshot()
    assert first["sha256"] == second["sha256"]
    # generated_at is excluded on purpose: it changes on every run
    assert "generated_at" not in first
