"""Regression locks for the Wave 01 pre-real-publish semantic bridge (§20).

Nine locks, one per defect class the bridge round introduced or closed. Each one
fails if a future change re-opens its hole, which is the point: these are not
descriptions of behaviour, they are refusals.

The tests are deliberately written against the *modules*, not the scripts' CLI, so
they keep working when the bridge script is reorganised.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "services" / "api"))
sys.path.insert(0, str(REPO / "scripts"))

from app.rulespec.animal_scope import SCOPE_SUBJECTS, rule_governs  # noqa: E402
from app.rulespec.guide_dog_safety import (  # noqa: E402
    REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE,
    probe_guide_dog_safety_path,
)
from app.rulespec.source_scope_semantics import (  # noqa: E402
    validate_source_scope_semantic_compatibility,
)
from app.rulespec.v05_resolver import (  # noqa: E402
    LayeredException,
    LayeredRule,
    resolve,
)

REVISION = "EXP-R1-W01-REVIEW-R1"
SIGNED_REGISTER = REPO / "docs" / "expansion" / "review_decisions_expansion_r1_wave01.json"
PROJECTED_REGISTER = (
    REPO / "docs" / "expansion" / "review_decisions_expansion_r1_wave01_publishable.json"
)
BATCH_01 = REPO / "docs" / "governance" / "publish_batches" / "EXP_R1_W01_REVIEW_R1_BATCH_01.json"
BATCH_01A = REPO / "docs" / "governance" / "publish_batches" / "EXP_R1_W01_REVIEW_R1_BATCH_01A.json"


# ---------------------------------------------------------------------------
# 1. `other` does not govern guide_dog under ADR-025
# ---------------------------------------------------------------------------


def test_other_scope_does_not_govern_guide_dog():
    """The premise §2 corrects: `other` is {other_pet}, not "all animals".

    If this ever starts returning True, the Disney carve-out would become
    reachable and every downstream verdict in this round would need re-measuring.
    """
    assert SCOPE_SUBJECTS["other"] == frozenset({"other_pet"})
    assert rule_governs(frozenset({"guide_dog"}), "other", "other", "exact") is False
    # and the contrast that makes it a real distinction rather than a bug
    assert rule_governs(frozenset({"guide_dog"}), "dog", "dog", "exact") is True


# ---------------------------------------------------------------------------
# 2. a broad source "动物" cannot be silently normalised to the narrow `other`
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("term", ["动物", "动物（导盲犬除外）"])
def test_broad_source_term_cannot_be_exact_normalized_to_other(term):
    """Both Disney and the Zoo stored 「动物」 as `other`/`exact`. That is a
    narrowing dressed as an equivalence, and it must not pass."""
    verdict = validate_source_scope_semantic_compatibility(term, "other", "exact")
    assert verdict.compatible is False
    assert verdict.change == "narrowing"


def test_genuine_equivalences_still_pass():
    """The check must not be so strict it blocks legitimate rows.

    A gate that refuses everything is not conservative, it is broken — and it
    would have blocked 100% of the batch rather than the three rows at issue.
    """
    for term, scope in (
        ("犬只", "dog"),
        ("导盲犬", "guide_dog"),
        ("宠物", "ordinary_pet"),
    ):
        assert validate_source_scope_semantic_compatibility(term, scope, "exact").compatible


def test_exact_on_a_mismatched_pair_is_refused():
    verdict = validate_source_scope_semantic_compatibility("宠物", "dog", "exact")
    assert verdict.compatible is False


def test_non_legal_normalization_is_refused_regardless_of_term():
    """`legal_interpretation_required` confers no legal effect however well the
    term reads — the two checks are independent and both must hold."""
    verdict = validate_source_scope_semantic_compatibility(
        "犬只", "dog", "legal_interpretation_required"
    )
    assert verdict.compatible is False
    assert verdict.change == "non_legal_type"


# ---------------------------------------------------------------------------
# 3. an unreachable approved carve-out is not executable
# ---------------------------------------------------------------------------


def test_unreachable_approved_carveout_is_inert_and_not_executable():
    """Disney #19: a guide_dog carve-out whose base scope is `other`.

    The resolver applies an exception only when the base is in scope for the
    query, so a base that does not govern guide_dog can never reach it.
    """
    base = LayeredRule(
        id="disney-base",
        animal_scope="other",
        action="enter",
        effect="prohibited",
        rule_layer="OPERATOR_POLICY",
        origin="place_override",
        subject_scope_normalized="other",
        normalization_type="exact",
    )
    exc = LayeredException(
        id="disney-guide",
        rule_id="disney-base",
        animal_scope="service_dog",
        effect="allowed",
        source_id="0bc744e2",
        status="current",
        subject_scope_normalized="guide_dog",
        normalization_type="exact",
        normative_effect="exempt_from_prohibition",
    )
    result = resolve(
        legal=[],
        guidance=[],
        template_rules=[],
        operator_rules=[base],
        event_rules=[],
        animal="dog",
        service_role="working",
        declared_role="guide_dog",
        action="enter",
        zone_id=None,
        now=datetime.now(UTC),
        exceptions=[exc],
    )
    # the exception never fires: guide dog still resolves as prohibited
    assert list(result.applied_exceptions) == []
    # NOTE: the resolved effect is `unknown`, not `prohibited`. An `other`-scoped
    # rule is *silent* about guide dogs: it neither prohibits them nor exempts
    # them. That is precisely why the carve-out is inert — there is no base
    # prohibition for it to carve out of, so it can never fire. The test pins the
    # actual semantics rather than the intuitive-but-wrong "prohibited".
    assert result.effect == "unknown"


def test_reachable_carveout_does_fire():
    """The mirror case, so the test above proves a distinction and not a bug:
    a `dog` base does reach a guide_dog carve-out."""
    base = LayeredRule(
        id="mall-base",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer="LEGAL",
        origin="place_override",
        mandatory_level="mandatory",
        subject_scope_normalized="dog",
        normalization_type="exact",
    )
    exc = LayeredException(
        id="statutory-proviso",
        rule_id="mall-base",
        animal_scope="service_dog",
        effect="allowed",
        source_id="f20bdb2c",
        status="current",
        subject_scope_normalized="guide_dog",
        normalization_type="exact",
        normative_effect="exempt_from_prohibition",
    )
    result = resolve(
        legal=[base],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role="working",
        declared_role="guide_dog",
        action="enter",
        zone_id=None,
        now=datetime.now(UTC),
        exceptions=[exc],
    )
    assert list(result.applied_exceptions) == ["statutory-proviso"]
    assert result.effect == "allowed"


# ---------------------------------------------------------------------------
# 4. signed candidate fields remain immutable
# ---------------------------------------------------------------------------


def test_signed_register_human_fields_are_frozen():
    """The bridge may add findings; it may not touch a signature.

    The distribution and the reviewer pin the human act itself. If a future round
    wanted to change any of these it would have to re-sign, which is a different
    decision and a different file.
    """
    doc = json.loads(SIGNED_REGISTER.read_text(encoding="utf-8"))
    assert doc["revision"] == REVISION
    assert doc["reviewer"] == "huangdi97"

    rows = doc["rows"]
    assert len(rows) == 31
    decisions = [r["final_decision"] for r in rows]
    assert decisions.count("APPROVED") == 15
    assert decisions.count("HOLD") == 14
    assert decisions.count("REJECTED") == 2
    assert all(r["reviewer"] == "huangdi97" for r in rows)
    assert all(r["decided_at"] for r in rows)


def test_bridge_never_writes_a_human_field():
    """Structural: the bridge must not write a signature into the *register*.

    It legitimately writes ``reviewer`` into the batch *manifest*, where the
    schema requires it as an identity claim ("this batch is selected against the
    revision huangdi97 signed"). That is not a signature. What must never appear
    is a write of ``final_decision`` — the field that constitutes the human act —
    or any write into the signed register file.
    """
    source = (REPO / "scripts" / "w01_semantic_bridge.py").read_text(encoding="utf-8")
    assert '"final_decision":' not in source
    assert '"decided_at":' not in source
    # the signed register is opened read-only, never assigned to
    assert "SIGNED_REGISTER.write_text" not in source
    assert 'SIGNED_REGISTER.open("w"' not in source
    # and the reviewer it writes is the manifest's identity claim, verbatim
    assert '"reviewer": REVIEWER,' in source


# ---------------------------------------------------------------------------
# 5. old `type` conditions normalise to `condition_type` only at ingest
# ---------------------------------------------------------------------------


def test_legacy_type_key_normalizes_at_the_ingest_boundary():
    from app.services.condition_ingest import normalize_conditions

    out = normalize_conditions([{"type": "leash_required", "value": True}])
    assert out == [{"condition_type": "leash_required", "value": True}]


def test_canonical_key_passes_through_untouched():
    from app.services.condition_ingest import normalize_conditions

    src = [{"condition_type": "max_weight_kg", "value": 15}]
    assert normalize_conditions(src) == src


def test_ambiguous_dual_key_is_refused_not_guessed():
    from app.services.condition_ingest import ConditionIngestError, normalize_conditions

    with pytest.raises(ConditionIngestError):
        normalize_conditions([{"condition_type": "leash_required", "type": "carrier_required"}])


def test_unknown_condition_type_is_refused():
    from app.services.condition_ingest import ConditionIngestError, normalize_conditions

    with pytest.raises(ConditionIngestError):
        normalize_conditions([{"type": "definitely_not_a_condition"}])


# ---------------------------------------------------------------------------
# 6. the publisher's canonical schema only uses `condition_type`
# ---------------------------------------------------------------------------


def test_domain_layer_does_not_accept_the_legacy_key():
    """§8: no second canonical key. A reader that tolerates `type` keeps the
    legacy spelling alive forever and lets a real condition be silently dropped."""
    for rel in (
        "services/api/app/services/answerability.py",
        "services/api/app/services/candidate_service.py",
    ):
        source = (REPO / rel).read_text(encoding="utf-8")
        assert 'c.get("condition_type") or c.get("type")' not in source
        assert 'cond.get("condition_type") or cond.get("type")' not in source


def test_publish_gate_requires_the_canonical_key():
    source = (REPO / "services" / "api" / "app" / "services" / "publish_gate.py").read_text(
        encoding="utf-8"
    )
    assert 'c.get("condition_type") in CONDITION_TYPES' in source


# ---------------------------------------------------------------------------
# 7. a LEGAL dog prohibition requires an executable statutory safety path
# ---------------------------------------------------------------------------


def test_legal_dog_prohibition_without_exception_is_blocked():
    base = {
        "rule_id": "new-legal-dog",
        "place_name": "某商场",
        "animal_scope": "dog",
        "subject_scope_normalized": "dog",
        "normalization_type": "exact",
        "effect": "prohibited",
        "rule_layer": "LEGAL",
        "action": "enter",
        "mandatory_level": "mandatory",
        "source_id": "a11aff10",
    }
    probe = probe_guide_dog_safety_path(base=base, candidate_exceptions=[])
    assert probe.ordinary_dog_prohibited is True
    assert probe.guide_dog_prohibited is True
    assert probe.has_executable_exception is False
    assert probe.safe_to_publish is False
    assert probe.block_reason == REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE


def test_legal_dog_prohibition_with_same_batch_exception_passes():
    base = {
        "rule_id": "new-legal-dog",
        "place_name": "某博物馆",
        "animal_scope": "dog",
        "subject_scope_normalized": "dog",
        "normalization_type": "exact",
        "effect": "prohibited",
        "rule_layer": "LEGAL",
        "action": "enter",
        "mandatory_level": "mandatory",
        "source_id": "a11aff10",
    }
    exc = {
        "rule_id": "guide-exc",
        "base_rule_id": "new-legal-dog",
        "animal_scope": "service_dog",
        "subject_scope_normalized": "guide_dog",
        "normalization_type": "exact",
        "effect": "allowed",
        "rule_layer": "LEGAL",
        "source_id": "a11aff10",
        "status": "current",
    }
    probe = probe_guide_dog_safety_path(base=base, candidate_exceptions=[exc])
    assert probe.safe_to_publish is True
    assert probe.exception_source == "batch"


def test_an_exception_of_another_rule_is_not_a_path():
    """A carve-out written of rule A does not protect rule B. Attaching by
    proximity rather than by binding is how a venue gets an exemption it was
    never granted."""
    base = {
        "rule_id": "rule-b",
        "place_name": "某商场",
        "animal_scope": "dog",
        "subject_scope_normalized": "dog",
        "normalization_type": "exact",
        "effect": "prohibited",
        "rule_layer": "LEGAL",
        "action": "enter",
        "mandatory_level": "mandatory",
        "source_id": "a11aff10",
    }
    exc = {
        "rule_id": "guide-exc",
        "base_rule_id": "rule-a",
        "animal_scope": "service_dog",
        "subject_scope_normalized": "guide_dog",
        "normalization_type": "exact",
        "effect": "allowed",
        "rule_layer": "LEGAL",
        "source_id": "a11aff10",
        "status": "current",
    }
    probe = probe_guide_dog_safety_path(base=base, candidate_exceptions=[exc])
    assert probe.safe_to_publish is False


def test_exception_without_source_is_not_a_path():
    """An exception with no provenance never applies, so it cannot be a safety
    path either."""
    base = {
        "rule_id": "rule-b",
        "place_name": "某商场",
        "animal_scope": "dog",
        "subject_scope_normalized": "dog",
        "normalization_type": "exact",
        "effect": "prohibited",
        "rule_layer": "LEGAL",
        "action": "enter",
        "mandatory_level": "mandatory",
        "source_id": "a11aff10",
    }
    exc = {
        "rule_id": "guide-exc",
        "base_rule_id": "rule-b",
        "animal_scope": "service_dog",
        "subject_scope_normalized": "guide_dog",
        "normalization_type": "exact",
        "effect": "allowed",
        "rule_layer": "LEGAL",
        "source_id": None,
        "status": "current",
    }
    probe = probe_guide_dog_safety_path(base=base, candidate_exceptions=[exc])
    assert probe.safe_to_publish is False


# ---------------------------------------------------------------------------
# 8. search_snippet + needs_verification cannot become executable
# ---------------------------------------------------------------------------


def test_weak_evidence_cannot_be_executable():
    from publish_reviewed_r1 import WEAK

    assert "search_snippet" in WEAK
    assert "social_lead" in WEAK

    projected = json.loads(PROJECTED_REGISTER.read_text(encoding="utf-8"))
    row = next(r for r in projected["rows"] if r["rule_id"] == "w01-4e217d5810")  # 世纪公园
    assert row["evidence_strength"] in WEAK
    assert row["final_decision"] == "APPROVED"  # the human decision stands


def test_bridge_weak_set_matches_the_publisher():
    """The bridge reports the execution-layer verdict without running the
    publisher; if the two sets drift, the report lies about what would execute."""
    from publish_reviewed_r1 import WEAK

    source = (REPO / "scripts" / "w01_semantic_bridge.py").read_text(encoding="utf-8")
    assert 'WEAK_EVIDENCE = frozenset({"search_snippet", "social_lead"})' in source
    assert set(WEAK) == {"search_snippet", "social_lead"}


# ---------------------------------------------------------------------------
# 9. planning PASS and execution PASS cannot be conflated
# ---------------------------------------------------------------------------


def test_the_safe_batch_manifest_is_a_new_artefact():
    """§16: the audited dry-run manifest is never overwritten in place."""
    assert BATCH_01.exists(), "the original planning manifest must remain"
    assert BATCH_01A.exists(), "the safe batch must be a separate file"

    old = json.loads(BATCH_01.read_text(encoding="utf-8"))
    new = json.loads(BATCH_01A.read_text(encoding="utf-8"))
    assert new["supersedes_planning_manifest"] == BATCH_01.name
    assert new["supersede_reason"] == "PRE_REAL_PUBLISH_SEMANTIC_BRIDGE"
    assert new["batch_id"] != old["batch_id"]
    # the safe batch may only ever be smaller, never larger
    assert len(new["candidate_rule_ids"]) < len(old["candidate_rule_ids"])


def test_the_safe_batch_excludes_every_blocked_row_it_documents():
    """The manifest's own exclusion list and its selection must not overlap, and
    every excluded row must carry a measured reason."""
    manifest = json.loads(BATCH_01A.read_text(encoding="utf-8"))
    selected = set(manifest["candidate_rule_ids"])
    excluded = {e["rule_id"] for e in manifest["excluded_approved"]}
    assert not (selected & excluded)
    assert all(e["reason"] for e in manifest["excluded_approved"])
    assert all(e["human_decision"] == "APPROVED" for e in manifest["excluded_approved"])


def test_the_safe_batch_carries_base_before_exception():
    """Position is execution order: a carve-out must follow its base."""
    manifest = json.loads(BATCH_01A.read_text(encoding="utf-8"))
    projected = json.loads(PROJECTED_REGISTER.read_text(encoding="utf-8"))
    bindings = {
        e["rule_id"]: e["bases"][0]["rule_id"]
        for e in projected["exception_plan"]
        if e.get("mode") == "rule_exception" and e.get("bases")
    }
    order = manifest["candidate_rule_ids"]
    for exc_id, base_id in bindings.items():
        if exc_id in order:
            assert base_id in order, f"{exc_id} 的 base {base_id} 不在批次内"
            assert order.index(base_id) < order.index(exc_id), f"{exc_id} 排在其 base 之前"


def test_no_inert_carveout_is_selected():
    """§17: zero inert rules. The Disney carve-out is the measured case."""
    manifest = json.loads(BATCH_01A.read_text(encoding="utf-8"))
    assert "w01-305fa08c1e" not in manifest["candidate_rule_ids"]
    assert "w01-305fa08c1e" in {e["rule_id"] for e in manifest["excluded_approved"]}


# --- ADR-030 path C: the bridge must hand the gate the activated proviso ----
#
# The gate in guide_dog_safety has always accepted a third provenance for the
# guide-dog path, but the bridge never passed one in. With the proviso activated
# in the database and the wiring missing, every LEGAL dog base without a
# same-batch carve-out still reported blocked — which is indistinguishable, from
# the outside, from "the proviso does not work". These two locks pin the wiring.

def test_load_jurisdiction_exceptions_maps_instrument_binding(monkeypatch):
    """Rows come back shaped the way `_attaches_to` and `_exception_layered` read them."""
    import psycopg

    import w01_semantic_bridge as bridge

    row = (
        "JPROV-001", "service_dog", "allowed", "f20bdb2c-0000-0000-0000-000000000000",
        "current", "guide_dog", "exact", "exempt_from_prohibition",
        "person_with_disability", "instrument",
        ["f20bdb2c-0000-0000-0000-000000000000", "a11aff10-0000-0000-0000-000000000000"],
        "LEGAL", ["prohibited"],
    )

    class _Cur:
        def execute(self, q, params=None):
            self.sql = q

        def fetchall(self):
            return [row]

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class _Conn:
        def cursor(self):
            return _Cur()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(psycopg, "connect", lambda url: _Conn())
    out = bridge.load_jurisdiction_exceptions()

    assert len(out) == 1
    proviso = out[0]
    assert proviso["binding"] == "instrument"
    assert proviso["instrument_source_ids"] == [
        "f20bdb2c-0000-0000-0000-000000000000",
        "a11aff10-0000-0000-0000-000000000000",
    ]
    assert proviso["applies_to_layer"] == "LEGAL"
    assert proviso["applies_to_effects"] == ["prohibited"]
    # `rule_id` is what `_attaches_to` compares against; leaving it empty would
    # make an instrument-bound proviso indistinguishable from an unbound one.
    assert proviso["rule_id"] == "JPROV-001"


def test_load_jurisdiction_exceptions_fails_closed(monkeypatch):
    """Unreachable database ⇒ no proviso ⇒ bases stay blocked. Never invent one."""
    import psycopg

    import w01_semantic_bridge as bridge

    def boom(url):
        raise RuntimeError("db down")

    monkeypatch.setattr(psycopg, "connect", boom)
    assert bridge.load_jurisdiction_exceptions() == []


def test_proviso_is_a_guide_dog_path_for_a_grounded_base():
    """Path C actually fires: same source ⇒ the base is exempted, not blocked."""
    base = {
        "rule_id": "w01-testbase00",
        "animal_scope": "dog",
        "effect": "prohibited",
        "rule_layer": "LEGAL",
        "action": "enter",
        "mandatory_level": "mandatory",
        "source_id": "f20bdb2c-0000-0000-0000-000000000000",
        "subject_scope_normalized": "dog",
        "normalization_type": "exact",
    }
    proviso = {
        "rule_id": "JPROV-001",
        "animal_scope": "service_dog",
        "effect": "allowed",
        "source_id": "f20bdb2c-0000-0000-0000-000000000000",
        "status": "current",
        "subject_scope_normalized": "guide_dog",
        "normalization_type": "exact",
        "normative_effect": "exempt_from_prohibition",
        "holder_scope": "person_with_disability",
        "binding": "instrument",
        "instrument_source_ids": ["f20bdb2c-0000-0000-0000-000000000000"],
        "applies_to_layer": "LEGAL",
        "applies_to_effects": ["prohibited"],
    }
    probe = probe_guide_dog_safety_path(
        base=base, candidate_exceptions=[], jurisdiction_exceptions=[proviso]
    )
    assert probe.exception_source == "jurisdiction"
    assert probe.safe_to_publish
    assert probe.applied_exceptions == ("JPROV-001",)
