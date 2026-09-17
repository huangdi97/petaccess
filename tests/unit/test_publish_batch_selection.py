"""Explicit batch selection: a manifest, not a slice (§4/§6/§7/§8/§22).

The failure this file guards against is not a crash — it is a *silent* widening.
``--max-approve`` bounds a run; it cannot name one. If selection fell back to
"whatever the register lists first", a real publish would be defined by array
order, and the eleven approved candidates left out of Batch 01 would ship
whenever the file happened to be sorted differently.

So every refusal below is a property of the selection itself, and each one is
pinned by the assertion that would catch the regression:

    manifest is not authority        a HOLD in the list is refused, not filtered
    closure                          a carve-out needs its base earlier, or published
    no prohibition without its carve-out
    identity                         HOLD/REJECTED/cross-revision/unknown/duplicate
    --execute demands --batch-file   bare --execute is refused outright
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PUBLISHER = REPO / "scripts" / "publish_reviewed_r1.py"
BATCH_MODULE = REPO / "scripts" / "publish_batch.py"
REGISTER = REPO / "docs" / "reality_audit" / "review_decisions_r2_final.json"
BATCH_DIR = REPO / "docs" / "governance" / "publish_batches"
#: The batch that is actually allowed to publish. 01 and 01A are kept as
#: rehearsal history — and are now REFUSED by the upgraded gate, which is itself
#: asserted below so the guard cannot quietly stop biting.
MANIFEST = BATCH_DIR / "R2_FINAL_R3_BATCH_01B.json"
MANIFEST_01 = BATCH_DIR / "R2_FINAL_R3_BATCH_01.json"
MANIFEST_01A = BATCH_DIR / "R2_FINAL_R3_BATCH_01A.json"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def pub():
    return _load("publish_reviewed_r1_batch", PUBLISHER)


@pytest.fixture(scope="module")
def batch():
    return _load("publish_batch", BATCH_MODULE)


@pytest.fixture(scope="module")
def register() -> dict:
    return json.loads(REGISTER.read_text(encoding="utf-8"))


def _manifest(tmp_path, batch_module, **over):
    doc = {
        "revision": "R2-FINAL-R3",
        "batch_id": "TEST-BATCH",
        "reviewer": "huangdi97",
        #: the reachable LEGAL pair — the default because it is the *valid* case.
        #: ``dl-pet-ban -> dl-sd-op`` is deliberately not the default: that pair
        #: is inert, so it exercises the unreachable branch instead.
        "candidate_rule_ids": ["fp-legal-dog", "fp-sd-legal"],
    }
    doc.update(over)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return batch_module.load_manifest(path)


def _validate(batch_module, pub, register, manifest):
    rows = register["rows"]
    return batch_module.validate_manifest(
        manifest,
        rows,
        bindings=pub.canonical_exception_bindings(register),
        register_revision=register["revision"],
        published_rule_ids=[],
        approved_exception_map=batch_module.approved_exception_map(register, rows),
    )


# ------------------------------------------------------------------ the real batch


def test_the_shipped_batch_is_eight_with_a_closed_dependency(batch, pub, register):
    """R2-FINAL-R3-BATCH-01B: 5 AccessRule + 3 RuleException, zero inert."""
    manifest = batch.load_manifest(MANIFEST)
    result = _validate(batch, pub, register, manifest)

    assert result.ok, result.problems
    assert len(result.selected) == 8
    assert len(result.access_rule_ids) == 5
    assert len(result.exception_ids) == 3
    assert result.dependency_closed
    assert not result.hold_selected
    assert not result.rejected_selected
    assert not result.cross_layer
    assert not result.bases_missing_approved_exception
    assert result.zero_inert_rules
    assert not result.inert_selected_exceptions


def test_the_shipped_batch_excludes_the_fifteen_other_approvals(batch, register):
    """15 of the 23 approved candidates are deliberately not in this batch.

    Four of them (dl-pet-ban, dl-sd-op, fp-sd-op-firstparty, lib-sd-op-guide)
    are deferred for a semantic remodel, not rejected — asserted separately.
    """
    manifest = batch.load_manifest(MANIFEST)
    approved = {
        r["rule_id"]
        for r in register["rows"]
        if r["final_decision"] in ("APPROVED", "APPROVED_WITH_NOTE")
    }
    assert len(approved) == 23
    assert len(approved - set(manifest.rule_ids)) == 15


def test_the_deferred_rules_are_named_and_still_approved(batch, register):
    """DEFERRED_APPROVED_SEMANTIC_REMODEL is not HOLD and not REJECTED.

    The whole point of deferring instead of re-deciding: the human approval
    stands. If this test starts failing because someone rewrote the register,
    the signed record was tampered with.
    """
    manifest = batch.load_manifest(MANIFEST)
    assert manifest.raw.get("deferred") == [
        "dl-pet-ban",
        "dl-sd-op",
        "fp-sd-op-firstparty",
        "lib-sd-op-guide",
    ]
    decisions = {r["rule_id"]: r["final_decision"] for r in register["rows"]}
    for rule_id in manifest.raw["deferred"]:
        assert decisions[rule_id] in ("APPROVED", "APPROVED_WITH_NOTE"), rule_id
        assert rule_id not in manifest.rule_ids


def test_the_shipped_batch_records_its_two_unreachable_carve_outs(batch, pub, register):
    """`fp-pets-op-firstparty` and `lib-pets-op` may ship without their inert
    operator guide-dog carve-outs — but the fact must be on the record."""
    result = _validate(batch, pub, register, batch.load_manifest(MANIFEST))
    assert result.unreachable_approved_carve_outs == (
        "fp-pets-op-firstparty->fp-sd-op-firstparty",
        "lib-pets-op->lib-sd-op-guide",
    )
    assert result.ok, result.problems


def test_batch_01_and_01a_are_refused_by_the_zero_inert_gate(batch, pub, register):
    """The two historical batches are exactly what the upgrade rejects.

    This test is the guard against the guard going soft: if reachability ever
    stops being measured, both of these become OK again and this fails.
    """
    for path, expected in ((MANIFEST_01, 3), (MANIFEST_01A, 2)):
        result = _validate(batch, pub, register, batch.load_manifest(path))
        assert not result.ok, path
        assert len(result.inert_selected_exceptions) == expected, (path, result.problems)
        assert not result.zero_inert_rules
        assert any("惰性规则" in p for p in result.problems)
        # deferral is not a re-decision: nothing was turned into HOLD/REJECTED
        assert not result.hold_selected
        assert not result.rejected_selected


def test_batch_01b_supersedes_01a_and_both_ancestors_stay_on_disk(batch, pub, register):
    """Narrowing must not erase history — all three manifests are readable."""
    ids = []
    for path in (MANIFEST_01, MANIFEST_01A, MANIFEST):
        manifest = batch.load_manifest(path)
        ids.append(manifest.batch_id)
        assert manifest.revision == "R2-FINAL-R3"
        assert manifest.reviewer == "huangdi97"
    assert ids == [
        "R2-FINAL-R3-BATCH-01",
        "R2-FINAL-R3-BATCH-01A",
        "R2-FINAL-R3-BATCH-01B",
    ]
    assert batch.load_manifest(MANIFEST).raw["supersedes_batch"] == "R2-FINAL-R3-BATCH-01A"


# ------------------------------------------------------------------ refusals


def test_a_hold_in_the_manifest_is_refused_not_filtered(batch, pub, register, tmp_path):
    manifest = _manifest(tmp_path, batch, candidate_rule_ids=["dl-pet-ban", "dl-legal-dog"])
    result = _validate(batch, pub, register, manifest)
    assert not result.ok
    assert result.hold_selected == ("dl-legal-dog",)
    assert any("HOLD" in p for p in result.problems)


def test_a_rejected_candidate_cannot_be_selected(batch, pub, register, tmp_path):
    manifest = _manifest(tmp_path, batch, candidate_rule_ids=["fp-pets-op"])
    result = _validate(batch, pub, register, manifest)
    assert not result.ok
    assert result.rejected_selected == ("fp-pets-op",)


def test_an_unknown_rule_id_is_refused(batch, pub, register, tmp_path):
    manifest = _manifest(tmp_path, batch, candidate_rule_ids=["dl-pet-ban", "no-such-rule"])
    result = _validate(batch, pub, register, manifest)
    assert not result.ok
    assert any("不存在" in p for p in result.problems)


def test_a_duplicate_id_is_refused(batch, pub, register, tmp_path):
    manifest = _manifest(tmp_path, batch, candidate_rule_ids=["dl-pet-ban", "dl-pet-ban"])
    result = _validate(batch, pub, register, manifest)
    assert not result.ok
    assert any("重复" in p for p in result.problems)


def test_an_exception_without_its_base_is_refused(batch, pub, register, tmp_path):
    """dl-sd-op carves out of dl-pet-ban; selecting it alone must not plan."""
    manifest = _manifest(tmp_path, batch, candidate_rule_ids=["dl-sd-op"])
    result = _validate(batch, pub, register, manifest)
    assert not result.ok
    assert not result.dependency_closed
    assert any("依赖闭包不成立" in p for p in result.problems)


def test_an_exception_listed_before_its_base_is_refused(batch, pub, register, tmp_path):
    """Manifest order is execution order, so it is also the dependency order."""
    manifest = _manifest(tmp_path, batch, candidate_rule_ids=["dl-sd-op", "dl-pet-ban"])
    result = _validate(batch, pub, register, manifest)
    assert not result.ok
    assert any("不得先于 base 执行" in p for p in result.problems)


def test_a_cross_revision_manifest_is_refused(batch, pub, register, tmp_path):
    manifest = _manifest(tmp_path, batch, revision="R2-FINAL-R2")
    result = _validate(batch, pub, register, manifest)
    assert not result.ok
    assert any("跨版本选择" in p for p in result.problems)


def test_a_wrong_reviewer_is_refused(batch, pub, register, tmp_path):
    manifest = _manifest(tmp_path, batch, reviewer="someone-else")
    result = _validate(batch, pub, register, manifest)
    assert not result.ok
    assert any("reviewer" in p for p in result.problems)


def test_a_base_may_not_ship_without_its_reachable_approved_carve_out(
    batch, pub, register, tmp_path
):
    """fp-legal-dog alone leaves "guide dogs prohibited" with no way out.

    The pair is a `dog` base with a `guide_dog` carve-out, so the carve-out can
    actually fire — which is exactly why its absence is a refusal rather than a
    note. lib-pets-op's HOLD'd carve-outs (police / military) are deliberately
    *not* part of this rule: a HOLD is not a carve-out anyone signed, so it
    cannot force a base to wait.
    """
    manifest = _manifest(tmp_path, batch, candidate_rule_ids=["fp-legal-dog", "fp-sd-legal"])
    result = _validate(batch, pub, register, manifest)
    assert result.ok, result.problems

    manifest = _manifest(tmp_path, batch, candidate_rule_ids=["fp-legal-dog"])
    result = _validate(batch, pub, register, manifest)
    assert not result.ok
    assert result.bases_missing_approved_exception == ("fp-legal-dog->fp-sd-legal",)


def test_an_unreachable_approved_carve_out_does_not_block_its_base(batch, pub, register, tmp_path):
    """The rule the whole upgrade exists for.

    ``fp-pets-op-firstparty`` is an ``ordinary_pet`` ban; ``fp-sd-op-firstparty``
    is a ``guide_dog`` proviso. Under ADR-025 ``ordinary_pet`` does not govern
    guide dogs, so the proviso can never fire and publishing the ban alone
    changes no user's answer. Holding the base hostage to an inert carve-out
    would let a modelling defect veto real rules.
    """
    manifest = _manifest(tmp_path, batch, candidate_rule_ids=["fp-pets-op-firstparty"])
    result = _validate(batch, pub, register, manifest)

    assert result.ok, result.problems
    assert not result.bases_missing_approved_exception
    assert result.unreachable_approved_carve_outs == ("fp-pets-op-firstparty->fp-sd-op-firstparty",)
    assert result.ok  # re-stated: the finding is recorded, never enforced


def test_an_unreachable_carve_out_may_not_be_selected(batch, pub, register, tmp_path):
    """Refusal 5: an inert carve-out must not be *shipped* either.

    Releasing its base is one thing; publishing a rule that can never apply is
    worse than not publishing it — it is audited, linked and counted while
    silently promising access it does not deliver.
    """
    manifest = _manifest(
        tmp_path,
        batch,
        candidate_rule_ids=["fp-pets-op-firstparty", "fp-sd-op-firstparty"],
    )
    result = _validate(batch, pub, register, manifest)

    assert not result.ok
    assert result.inert_selected_exceptions == ("fp-sd-op-firstparty:unreachable",)
    assert not result.zero_inert_rules
    assert any("惰性规则" in p for p in result.problems)


def test_a_base_is_satisfied_by_an_already_published_carve_out(batch, pub, register, tmp_path):
    manifest = _manifest(tmp_path, batch, candidate_rule_ids=["fp-legal-dog"])
    rows = register["rows"]
    result = batch.validate_manifest(
        manifest,
        rows,
        bindings=pub.canonical_exception_bindings(register),
        register_revision=register["revision"],
        published_rule_ids=["fp-sd-legal"],
        approved_exception_map=batch.approved_exception_map(register, rows),
    )
    assert result.ok, result.problems


# ------------------------------------------------------- reachability predicate


def test_reachability_reuses_the_canonical_adr025_matcher(batch, pub, register):
    """The predicate must not carry a second copy of the scope algorithm.

    A hand-rolled comparison would drift from ``animal_scope.py`` the first time
    the ontology moved, and then "reachable" would be a claim made by a copy
    nobody maintains. So this asserts the documented ADR-025 outcomes directly,
    from the register's own rows.
    """
    rows = {str(r["rule_id"]): r for r in register["rows"]}
    bindings = pub.canonical_exception_bindings(register)
    reach = batch.carve_out_reachability(register["rows"], bindings)

    # a `dog` base legally covers every dog role, so the proviso fires
    assert reach["fp-sd-legal"]["state"] == "reachable"
    assert batch.is_reachable_carveout(rows["fp-legal-dog"], rows["fp-sd-legal"]) is True
    # an `ordinary_pet` base does not — this is the inert family
    assert reach["fp-sd-op-firstparty"]["state"] == "unreachable"
    assert (
        batch.is_reachable_carveout(rows["fp-pets-op-firstparty"], rows["fp-sd-op-firstparty"])
        is False
    )
    assert reach["lib-sd-op-guide"]["state"] == "unreachable"
    assert reach["dl-sd-op"]["state"] == "unreachable"
    # and the reachable ones in the shipped batch
    assert reach["lib-sd-legal"]["state"] == "reachable"
    assert reach["sb-sd-legal"]["state"] == "reachable"


def test_a_carve_out_without_scope_data_is_unevaluable_and_blocks(batch, pub, register, tmp_path):
    """'We cannot tell' must never be reported as 'it is fine'.

    An unevaluable pair still obliges its base: only a *measured* inert carve-out
    may release it.
    """
    rows = [
        {
            "rule_id": "x-pet-ban",
            "candidate_id": "c1",
            "final_decision": "APPROVED",
            "rule_layer": "OPERATOR_POLICY",
            "reviewer": "huangdi97",
            "animal_scope": None,
            "subject_scope_normalized": None,
            "normalization_type": None,
        },
        {
            "rule_id": "x-sd-op",
            "candidate_id": "c2",
            "final_decision": "APPROVED",
            "rule_layer": "OPERATOR_POLICY",
            "reviewer": "huangdi97",
            "animal_scope": None,
            "subject_scope_normalized": None,
            "normalization_type": None,
        },
    ]
    bindings = {"x-sd-op": pub.ExceptionBinding("x-sd-op", ("x-pet-ban",), "OPERATOR_POLICY")}
    manifest = _manifest(tmp_path, batch, candidate_rule_ids=["x-pet-ban"])
    result = batch.validate_manifest(
        manifest,
        rows,
        bindings=bindings,
        register_revision="R2-FINAL-R3",
        published_rule_ids=[],
        approved_exception_map={"x-pet-ban": ["x-sd-op"]},
    )
    assert not result.ok
    assert result.unevaluable_approved_carve_outs == ("x-pet-ban->x-sd-op",)
    assert not result.unreachable_approved_carve_outs


def test_a_manifest_with_a_misspelled_key_is_refused(batch, register, tmp_path):
    """A typo'd key would otherwise select nothing — and silence looks like success."""
    path = tmp_path / "typo.json"
    path.write_text(
        json.dumps(
            {
                "revision": "R2-FINAL-R3",
                "batch_id": "X",
                "reviewer": "huangdi97",
                "candidate_rule_ids": ["dl-pet-ban"],
                "candidate_rule_id": ["dl-sd-op"],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(batch.BatchManifestError):
        batch.load_manifest(path)


# ------------------------------------------------------------------ CLI contract


def test_execute_without_a_batch_file_is_refused_entirely(pub, monkeypatch, capsys):
    """Bare --execute must never publish all 23 approvals."""
    monkeypatch.setattr("sys.argv", ["publish_reviewed_r1.py", "--execute"])
    assert pub.main() == 4
    assert "必须同时提供 --batch-file" in capsys.readouterr().out


def test_select_rows_follows_manifest_order_and_drops_everything_else(
    pub, batch, register, tmp_path
):
    manifest = _manifest(
        tmp_path, batch, candidate_rule_ids=["fp-legal-dog", "dl-pet-ban", "fp-sd-legal"]
    )
    selected = pub.select_rows(register["rows"], manifest)
    assert [r["rule_id"] for r in selected] == ["fp-legal-dog", "dl-pet-ban", "fp-sd-legal"]
    assert len(selected) == 3  # the other 34 register rows are not planned at all
