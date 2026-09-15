"""Publish preflight must cross-check the signed register against the database.

Why this exists (found by running the toolchain against a real PostGIS instance,
which ENV-01 had made impossible until now):

The 33 real-pilot candidates were ingested *before* ``rule_candidate.rule_layer``
existed. The column therefore carried its server default (OPERATOR_POLICY) for
all of them, while the evidence register declared 16 of them LEGAL. The publish
endpoint writes whatever the *row* holds, so signing the register and publishing
would have flattened 16 statutory rules into operator policy — the exact silent
downgrade ADR-023 was written to prevent, reached through stale data instead of a
missing column.

``preflight()`` now refuses when the register and the row disagree, so the
mismatch is a hard stop *before* any write. These tests pin that guard.

The script lives outside the importable package, so it is loaded by path.
"""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "publish_reviewed_r1.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("publish_reviewed_r1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(**over):
    row = {
        "candidate_id": "c-1",
        "rule_id": "r-1",
        "final_decision": "APPROVED",
        "reviewer": "审阅人甲",
        "reviewed_at": "2026-09-14T00:00:00Z",
        "evidence_strength": "primary_direct",
        "rule_layer": "LEGAL",
        "mandatory_level": "mandatory",
    }
    row.update(over)
    return row


def _state(**over):
    state = {
        "rule_layer": "LEGAL",
        "mandatory_level": "mandatory",
        "review_status": "REVIEW_PENDING",
    }
    state.update(over)
    return {"c-1": state}


def test_matching_register_and_row_passes(mod):
    problems = mod.preflight([_row()], "审阅人甲", 20, _state())
    assert problems == []


def test_stale_layer_in_db_blocks_the_publish(mod):
    """The real defect: the row still says OPERATOR_POLICY for a statutory rule."""
    problems = mod.preflight([_row()], "审阅人甲", 20, _state(rule_layer="OPERATOR_POLICY"))
    assert any("rule_layer 不一致" in p for p in problems)
    assert any("backfill_candidate_rule_layer" in p for p in problems)


def test_stale_mandatory_level_in_db_blocks_the_publish(mod):
    problems = mod.preflight(
        [_row()], "审阅人甲", 20, _state(mandatory_level="operator_discretion")
    )
    assert any("mandatory_level 不一致" in p for p in problems)


def test_missing_candidate_blocks_the_publish(mod):
    problems = mod.preflight([_row()], "审阅人甲", 20, {})
    assert any("库中不存在该候选" in p for p in problems)


def test_cross_check_is_skipped_when_no_db_state_is_supplied(mod):
    """A dry run without a token must still work; it just cannot cross-check."""
    assert mod.preflight([_row()], "审阅人甲", 20, None) == []


def test_hold_rows_are_not_cross_checked(mod):
    row = _row(final_decision="HOLD")
    problems = mod.preflight([row], "审阅人甲", 20, _state(rule_layer="OPERATOR_POLICY"))
    assert problems == []


def test_legal_without_level_is_still_refused_from_the_register_alone(mod):
    """The register-side guard (ADR-023) is independent of the DB cross-check."""
    problems = mod.preflight([_row(mandatory_level=None)], "审阅人甲", 20, None)
    assert any("LEGAL 规则缺少 mandatory_level" in p for p in problems)


def test_unsigned_register_is_refused(mod):
    """An unfilled decision is refused, and the message names the accepted set so
    the reviewer is told what to write instead of only what is wrong."""
    problems = mod.preflight([_row(final_decision=None)], "审阅人甲", 20, _state())
    assert any("不在词表内" in p for p in problems)
    assert any("APPROVED" in p and "REJECTED" in p for p in problems)


def test_approved_with_note_is_an_approval_not_a_rejection(mod):
    """Regression: this value used to be called '未填', and had it reached run()
    the ``else REJECTED`` branch would have inverted the reviewer's decision."""
    problems = mod.preflight([_row(final_decision="APPROVED_WITH_NOTE")], "审阅人甲", 20, None)
    assert not any("不在词表内" in p for p in problems)


def test_approved_with_note_must_carry_the_note_that_makes_it_meaningful(mod):
    problems = mod.preflight(
        [_row(final_decision="APPROVED_WITH_NOTE", review_note="")], "审阅人甲", 20, None
    )
    assert any("必须填写 review_note" in p for p in problems)


def test_approved_with_note_publishes_as_an_approval(mod):
    """Dry-run planning must route it to the approval bucket."""
    result = mod.run(
        [
            _row(
                final_decision="APPROVED_WITH_NOTE",
                review_note="证据充分，但来源页面无归档快照",
                proposed_decision="RECOMMEND_APPROVE",
            )
        ],
        None,
        execute=False,
    )
    assert [r["rule_id"] for r in result["approved"]] == ["r-1"]
    assert result["rejected"] == []
