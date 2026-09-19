"""Superseded semantics and human-authorised evidence acceptance.

Two new refusals, each pinned by the regression that would undo it.

**Superseded semantics.** Wave-01's ``other`` bases were replaced by Scope
Remodel R2's ``dog``/``cat``/``other`` split. Measured against the real
production database, re-publishing them did this::

    w01-3a04d4d1aa -> SUPERSEDE_ACCESS_RULE, supersedes 0d2f70f8 (Disney other)
    w01-6f2bfd39d7 -> SUPERSEDE_ACCESS_RULE, supersedes 352f6e0f (Zoo other)

— i.e. the old row planned to overwrite the rule that replaced it. Marking the
planning manifests obsolete is the human-facing half; these tests pin the
machine half, so a *new* manifest listing the same ids gets the same answer.

**Evidence acceptance.** ADR-021 refuses weak evidence. That refusal stays; what
is added is a narrow, signed release for one specific source. The three things
it must never become are asserted directly: a strength upgrade, a claim of
operator first-party verification, and a licence that survives the source
changing underneath it.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BATCH_MODULE = REPO / "scripts" / "publish_batch.py"
PUBLISHER = REPO / "scripts" / "publish_reviewed_r1.py"
ACCEPTANCE_MODULE = REPO / "scripts" / "evidence_acceptance.py"

SUPERSEDED_REGISTER = REPO / "docs" / "governance" / "superseded_semantics.json"
OBSOLETE_MANIFEST = REPO / "docs" / "governance" / "publish_batches" / "EXP_R1_W01_REVIEW_R1_BATCH_01.json"
CENTURY_PARK_ACCEPTANCE = (
    REPO / "docs" / "governance" / "evidence_acceptance" / "CENTURY_PARK_EVIDENCE_ACCEPTANCE_R1.json"
)

SOURCE_ID = "ca5b81a7-ca5b-495c-9026-6d8b69dbaea7"
CANDIDATE_ID = "4e217d58-1060-4945-9fa1-b9b7e17d7e64"
RULE_ID = "w01-4e217d5810"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def batch():
    return _load("publish_batch_superseded", BATCH_MODULE)


@pytest.fixture(scope="module")
def pub():
    return _load("publish_reviewed_r1_superseded", PUBLISHER)


@pytest.fixture(scope="module")
def acceptance():
    return _load("evidence_acceptance", ACCEPTANCE_MODULE)


def _write_manifest(tmp_path: Path, ids: list[str], **extra) -> Path:
    doc = {
        "revision": "EXP-R1-W01-REVIEW-R1",
        "batch_id": "TEST-BATCH",
        "reviewer": "huangdi97",
        **extra,
        "candidate_rule_ids": ids,
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return path


# =============================================== superseded semantics (batch side)


def test_the_retired_planning_manifest_cannot_even_be_loaded(batch):
    """executing the dead manifest would overwrite the rules that replaced it."""
    OBSOLETE_MANIFEST.read_text(encoding="utf-8")  # exists
    with pytest.raises(batch.BatchManifestError) as exc:
        batch.load_manifest(OBSOLETE_MANIFEST)
    assert "不可执行" in str(exc.value) or "不可执行" in str(exc.value)


def test_a_status_of_obsolete_is_refused_in_every_spelling(batch, tmp_path):
    for status in ("OBSOLETE", "NON_EXECUTABLE", "obsolete_non_executable"):
        path = _write_manifest(tmp_path, ["whatever"], execution_status=status)
        with pytest.raises(batch.BatchManifestError):
            batch.load_manifest(path)


def test_a_live_manifest_is_not_refused(batch, tmp_path):
    path = _write_manifest(tmp_path, ["w01-4e217d5810"])
    manifest = batch.load_manifest(path)
    assert manifest.rule_ids == ("w01-4e217d5810",)


def test_the_register_names_the_three_rows_it_retired(batch):
    table = batch.load_superseded_semantics(SUPERSEDED_REGISTER)
    assert set(table) == {"w01-3a04d4d1aa", "w01-6f2bfd39d7", "w01-305fa08c1e"}
    for record in table.values():
        assert record["reason"] == "SUPERSEDED_BY_SCOPE_REMODEL_R2"
        assert record["superseded_by"], "a replaced row must name its replacement"


def test_a_new_manifest_that_relists_retired_rows_is_refused(batch, tmp_path):
    """The whole point: marking files is not enough.

    Retiring the planning manifests answers "which files may not run". If that
    were the only guard, a new manifest listing the same ids would undo the
    remodel — and this is exactly what it measuredly does without the guard.
    """
    path = _write_manifest(tmp_path, ["w01-3a04d4d1aa", "w01-6f2bfd39d7"])
    manifest = batch.load_manifest(path)
    superseded = batch.load_superseded_semantics(SUPERSEDED_REGISTER)

    found = batch.superseded_semantics_selected(manifest.rule_ids, superseded)
    assert {rule_id for rule_id, _ in found} == {"w01-3a04d4d1aa", "w01-6f2bfd39d7"}


def test_an_absent_register_blocks_nothing(batch, tmp_path):
    missing = tmp_path / "does-not-exist.json"
    assert batch.load_superseded_semantics(missing) == {}
    assert batch.superseded_semantics_selected(["anything"], {}, path=None) == ()


# ============================================ superseded semantics (planner side)


class _FakeGate:
    status = "PASS"
    reasons: tuple = ()

    def evaluate(self, *, candidate_id: str, rule_id: str):
        from types import SimpleNamespace

        return SimpleNamespace(status="PASS", reasons=())


def test_the_planner_classifies_a_retired_row_as_non_writable(pub, tmp_path):
    """A second line of defence, not the first.

    The batch layer refuses the manifest; this refuses the row. They read the
    same register so they cannot disagree, and either alone would leave a path
    open.
    """
    row = {
        "rule_id": "w01-3a04d4d1aa",
        "candidate_id": "3a04d4d1-aaac-4c3d-8364-9d1acf18ef35",
        "final_decision": "APPROVED",
        "reviewer": "huangdi97",
        "reviewed_at": "2026-09-18T07:31:10.598135Z",
        "rule_layer": "OPERATOR_POLICY",
        "animal_scope": "other",
        "action": "enter",
        "evidence_strength": "primary_direct",
        "_supersedes_existing": ["0d2f70f8-b712-4d43-858f-f32a5f535df6"],
        "_db_review_status": "REVIEW_PENDING",
    }
    plan = pub.build_plan(
        [row],
        bindings={},
        gate=_FakeGate(),
        revision="EXP-R1-W01-REVIEW-R1",
        reviewer="huangdi97",
        superseded_semantics={"w01-3a04d4d1aa": {"reason": "SUPERSEDED_BY_SCOPE_REMODEL_R2"}},
    )
    step = plan.steps[0]
    assert step.publication_type == pub.SUPERSEDED_NON_EXECUTABLE
    assert plan.writable == [], "a retired row must plan nothing writable"
    #: The human ruling is a fact about the past. It does not move.
    assert step.human_decision == "APPROVED"


def test_a_retired_row_plans_a_write_when_the_register_is_absent(pub):
    """Reverse control: without the register the old damage would ship.

    This is what the register prevents, stated as the thing that happens when it
    is not there — so the guard is proven load-bearing rather than decorative.
    """
    row = {
        "rule_id": "w01-3a04d4d1aa",
        "candidate_id": "3a04d4d1-aaac-4c3d-8364-9d1acf18ef35",
        "final_decision": "APPROVED",
        "reviewer": "huangdi97",
        "reviewed_at": "2026-09-18T07:31:10.598135Z",
        "rule_layer": "OPERATOR_POLICY",
        "animal_scope": "other",
        "action": "enter",
        "evidence_strength": "primary_direct",
        "_supersedes_existing": ["0d2f70f8-b712-4d43-858f-f32a5f535df6"],
        "_db_review_status": "REVIEW_PENDING",
    }
    plan = pub.build_plan(
        [row],
        bindings={},
        gate=_FakeGate(),
        revision="EXP-R1-W01-REVIEW-R1",
        reviewer="huangdi97",
        superseded_semantics={},
    )
    assert plan.steps[0].publication_type == pub.SUPERSEDE_ACCESS_RULE
    assert plan.writable, "without the register it plans the overwrite"


# ====================================================== evidence acceptance


def _acceptance_dict(tmp_path: Path, **over) -> Path:
    entry = {
        "acceptance_id": "TEST",
        "reviewer": "huangdi97",
        "decided_at": "2026-09-19T00:00:00+08:00",
        "candidate_id": CANDIDATE_ID,
        "rule_id": RULE_ID,
        "source_id": SOURCE_ID,
        "declared_source_type": "government_service",
        "first_party_operator_source_pending": True,
        "operator_first_party_verified": False,
        "accepted_despite_evidence_strength": "search_snippet",
        **over,
    }
    path = tmp_path / "acceptance.json"
    path.write_text(json.dumps({"entries": [entry]}, ensure_ascii=False), encoding="utf-8")
    return path


GOOD_SOURCE = {"source_type": "government_service", "issuer": "上海市文化和旅游事业发展中心"}


def test_the_shipped_century_park_acceptance_loads(acceptance):
    table = acceptance.load_acceptances(CENTURY_PARK_ACCEPTANCE)
    assert RULE_ID in table
    entry = table[RULE_ID]
    assert entry["declared_source_type"] == "government_service"
    assert entry["operator_first_party_verified"] is False
    assert entry["first_party_operator_source_pending"] is True


def test_a_missing_reviewer_is_refused(acceptance, tmp_path):
    path = _acceptance_dict(tmp_path, reviewer="")
    with pytest.raises(acceptance.EvidenceAcceptanceError):
        acceptance.load_acceptances(path)


def test_claiming_operator_first_party_source_is_refused(acceptance, tmp_path):
    """The one claim this mechanism exists *not* to manufacture."""
    path = _acceptance_dict(tmp_path, declared_source_type="official_operator_policy")
    with pytest.raises(acceptance.EvidenceAcceptanceError) as exc:
        acceptance.load_acceptances(path)
    assert "official_operator_policy" in str(exc.value)


def test_claiming_first_party_verification_is_refused(acceptance, tmp_path):
    path = _acceptance_dict(tmp_path, operator_first_party_verified=True)
    with pytest.raises(acceptance.EvidenceAcceptanceError) as exc:
        acceptance.load_acceptances(path)
    assert "operator_first_party_verified" in str(exc.value)


def test_a_null_first_party_flag_is_refused_not_treated_as_false(acceptance, tmp_path):
    """'Nobody said yes' is not the same statement as 'somebody said no'."""
    path = _acceptance_dict(tmp_path, operator_first_party_verified=None)
    with pytest.raises(acceptance.EvidenceAcceptanceError):
        acceptance.load_acceptances(path)


def test_dropping_the_pending_gap_is_refused(acceptance, tmp_path):
    path = _acceptance_dict(tmp_path, first_party_operator_source_pending=False)
    with pytest.raises(acceptance.EvidenceAcceptanceError) as exc:
        acceptance.load_acceptances(path)
    assert "first_party_operator_source_pending" in str(exc.value)


def test_the_mechanism_cannot_be_used_to_stamp_strong_evidence(acceptance, tmp_path):
    path = _acceptance_dict(tmp_path, accepted_despite_evidence_strength="primary_direct")
    with pytest.raises(acceptance.EvidenceAcceptanceError):
        acceptance.load_acceptances(path)


def test_a_source_that_drifted_invalidates_the_acceptance(acceptance, tmp_path):
    """The record asserts a fact about a source; the source must still agree."""
    path = _acceptance_dict(tmp_path)
    table = acceptance.load_acceptances(path)
    released, problems = acceptance.released_weak_evidence_rows(
        [{"rule_id": RULE_ID, "candidate_id": CANDIDATE_ID}],
        table,
        {SOURCE_ID: {"source_type": "official_operator_policy", "issuer": "whatever"}},
    )
    assert released == set()
    assert any("漂移" in p for p in problems)


def test_a_matching_source_releases_the_row(acceptance, tmp_path):
    path = _acceptance_dict(tmp_path)
    table = acceptance.load_acceptances(path)
    released, problems = acceptance.released_weak_evidence_rows(
        [{"rule_id": RULE_ID, "candidate_id": CANDIDATE_ID}],
        table,
        {SOURCE_ID: GOOD_SOURCE},
    )
    assert problems == []
    assert released == {RULE_ID}


def test_an_acceptance_does_not_transfer_to_another_candidate(acceptance, tmp_path):
    path = _acceptance_dict(tmp_path)
    table = acceptance.load_acceptances(path)
    released, problems = acceptance.released_weak_evidence_rows(
        [{"rule_id": RULE_ID, "candidate_id": "00000000-0000-0000-0000-000000000000"}],
        table,
        {SOURCE_ID: GOOD_SOURCE},
    )
    assert released == set()
    assert problems, "a mismatched candidate must be refused, never released"


def test_a_missing_source_row_is_refused_rather_than_assumed(acceptance, tmp_path):
    path = _acceptance_dict(tmp_path)
    table = acceptance.load_acceptances(path)
    released, problems = acceptance.released_weak_evidence_rows(
        [{"rule_id": RULE_ID, "candidate_id": CANDIDATE_ID}],
        table,
        {},
    )
    assert released == set()
    assert problems


# =============================================== preflight integration


def _weak_row(rule_id: str) -> dict:
    return {
        "candidate_id": CANDIDATE_ID,
        "rule_id": rule_id,
        "final_decision": "APPROVED",
        "reviewer": "huangdi97",
        "reviewed_at": "2026-09-18T07:31:10.598135Z",
        "evidence_strength": "search_snippet",
        "rule_layer": "OPERATOR_POLICY",
        "mandatory_level": "operator_discretion",
    }


def test_adr021_still_refuses_every_unaccepted_weak_row(pub):
    problems = pub.preflight([_weak_row("other-row")], None, 20, None)
    assert any("ADR-021" in p for p in problems)


def test_an_accepted_row_is_no_longer_refused(pub):
    problems = pub.preflight(
        [_weak_row(RULE_ID)], None, 20, None, released_weak_evidence={RULE_ID}
    )
    assert problems == []


def test_acceptance_is_reported_not_silent(pub):
    """A release nobody can see is indistinguishable from a bug."""
    notes: list[str] = []
    pub.preflight([_weak_row(RULE_ID)], None, 20, None, released_weak_evidence={RULE_ID}, notes=notes)
    assert any("EVIDENCE_ACCEPTANCE" in n for n in notes)
    assert any(RULE_ID in n for n in notes)


def test_two_weak_rows_only_one_released(pub):
    rows = [_weak_row(RULE_ID), _weak_row("other-row")]
    problems = pub.preflight(rows, None, 20, None, released_weak_evidence={RULE_ID})
    assert len(problems) == 1
    assert "other-row" in problems[0]
