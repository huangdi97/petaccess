"""ADR-025 / ADR-028 publish-path fidelity: the precise scope must survive.

Why this file exists
--------------------

Getting the scope right in the picker is not enough. Two later steps can still
drop it, and both were real defects found while preparing GOV-01:

D1 — ``candidate_service.publish()`` created the ``AccessRule`` **without**
copying ``source_scope_exact`` / ``subject_scope_normalized`` /
``normalization_type`` / ``normative_effect`` / ``holder_scope`` /
``operator_obligations``. The published rule then kept only the coarse
``animal_scope='service_dog'``, which the resolver reads as the unproven
widening — i.e. **governs nothing**. Signing the register would have silently
disabled every 导盲犬 carve-out at the exact moment it went live.

D2 — nothing stopped a candidate declaring a precise subject scope *without* a
normalisation type, in which case the platform would have to guess whether the
stored scope is a legal equivalent. Guessing is precisely what ADR-025 forbids.

The gate refuses both shapes; these tests pin that refusal.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.core.errors import ApiError
from app.models.enums import AnimalRole, NormalizationType
from app.models.v05 import RuleCandidate
from app.services.candidate_service import create_from_extraction, transition
from app.services.candidate_service import publish as publish_candidate
from app.services.publish_gate import (
    NORMALIZATION_VALUES,
    SUBJECT_SCOPE_VALUES,
    scope_violations,
)


def _cand(**over) -> SimpleNamespace:
    """Minimal stand-in exposing only what the gate reads (pure-function test)."""
    base = {
        "animal_scope": "dog",
        "subject_scope_normalized": None,
        "normalization_type": None,
    }
    base.update(over)
    return SimpleNamespace(**base)


def _failing(candidate: SimpleNamespace) -> list[str]:
    return [code for code, failed, _ in scope_violations(candidate) if failed]


# --- D2: the gate refuses to guess ------------------------------------------


def test_gate_accepts_ordinary_rows_without_normalisation():
    """A plain dog row never had to prove anything — no precise claim is made."""
    assert _failing(_cand(animal_scope="dog")) == []
    assert _failing(_cand(animal_scope="ordinary_pet")) == []


def test_gate_refuses_a_precise_scope_with_no_normalisation():
    codes = _failing(_cand(subject_scope_normalized=AnimalRole.GUIDE_DOG.value))
    assert "scope_normalization_incomplete" in codes


def test_gate_refuses_a_scope_or_normalisation_outside_the_vocabulary():
    assert _failing(_cand(subject_scope_normalized="killer_robot_dog")) != []
    assert _failing(_cand(normalization_type="vibes")) != []
    # the vocabularies themselves are closed
    assert "compound_term_split" in NORMALIZATION_VALUES
    assert AnimalRole.GUIDE_DOG.value in SUBJECT_SCOPE_VALUES


def test_gate_refuses_the_unproven_service_dog_widening():
    """This is the 导盲犬→service_dog defect in the shape it took in production."""
    for norm in (None, "legal_interpretation_required", "parent_group_for_query_only"):
        codes = _failing(
            _cand(
                animal_scope="service_dog",
                subject_scope_normalized="service_dog",
                normalization_type=norm,
            )
        )
        assert "service_dog_scope_unproven" in codes, norm


def test_gate_accepts_the_coarse_scope_when_the_source_itself_names_it():
    """《无障碍环境建设法》第46条 names the assistance category — so the coarse
    scope IS source-faithful there, provided a reviewer declared it exact."""
    for norm in (NormalizationType.EXACT.value, NormalizationType.COMPOUND_TERM_SPLIT.value):
        codes = _failing(
            _cand(
                animal_scope="service_dog",
                subject_scope_normalized="service_dog",
                normalization_type=norm,
            )
        )
        assert "service_dog_scope_unproven" not in codes, norm


def test_gate_accepts_the_library_compound_split():
    for role in (AnimalRole.POLICE_DOG, AnimalRole.MILITARY_WORKING_DOG):
        codes = _failing(
            _cand(
                animal_scope="dog",
                subject_scope_normalized=role.value,
                normalization_type=NormalizationType.COMPOUND_TERM_SPLIT.value,
            )
        )
        assert codes == [], role


# --- D1: publish() must carry the scope onto the AccessRule ------------------


def _source(db, issuer="scope-fidelity"):
    from app.models import Source

    src = Source(
        source_type="onsite_signage",
        issuer=issuer,
        directness="direct",
        collected_at="2026-09-15T00:00:00Z",
    )
    db.add(src)
    db.flush()
    return src


def _approved(db, *, source_id, **over):
    """An APPROVED candidate whose bundle satisfies checks 1/2/6 of the gate."""
    from app.models import Place
    from app.models.evidence import EvidenceBundle, SourceArtifact

    place = Place(canonical_name="scope-fidelity-place", place_type="mall")
    db.add(place)
    db.flush()

    artifact = SourceArtifact(
        source_id=source_id,
        source_platform="OnsiteEvidenceCollector",
        artifact_type="signage_photo",
        collector_type="OnsiteEvidenceCollector",
        content_hash="c" * 64,
        captured_excerpt="导盲犬除外",
        collected_at=datetime.now(UTC),
        storage_allowed=True,
        display_allowed=True,
        redistribution_allowed=True,
    )
    db.add(artifact)
    db.flush()
    bundle = EvidenceBundle(
        artifact_id=artifact.id,
        source_id=source_id,
        source_platform="OnsiteEvidenceCollector",
        quoted_fragment="导盲犬除外",
        content_hash="c" * 64,
        captured_at=datetime.now(UTC),
        place_match_evidence={"matched_by": "manual_review_fixture"},
    )
    db.add(bundle)
    db.flush()

    cand = create_from_extraction(
        db,
        source_id=source_id,
        place_id=place.id,
        extraction_method="ocr",
        action="enter",
        effect="allowed",
        evidence_bundle_id=bundle.id,
        **over,
    )
    transition(cand, "REVIEW_PENDING")
    transition(cand, "APPROVED")
    return cand


SCOPE_FIELDS = {
    "animal_scope": "service_dog",
    "source_scope_exact": "导盲犬",
    "subject_scope_normalized": AnimalRole.GUIDE_DOG.value,
    "normalization_type": NormalizationType.EXACT.value,
    "normative_effect": "exempt_from_prohibition",
    "holder_scope": "person_with_disability",
}


def test_publish_carries_the_source_faithful_scope_onto_the_rule(db_session):
    src = _source(db_session)
    cand = _approved(db_session, source_id=src.id, **SCOPE_FIELDS)
    rule = publish_candidate(db_session, cand, reviewer_id="r1")

    db_session.flush()
    assert rule.source_scope_exact == "导盲犬"
    assert rule.subject_scope_normalized == AnimalRole.GUIDE_DOG.value
    assert rule.normalization_type == NormalizationType.EXACT.value
    assert rule.normative_effect == "exempt_from_prohibition"
    assert rule.holder_scope == "person_with_disability"
    # the coarse public-API scope is preserved too — it is not replaced, but
    # paired with the precise one so the resolver can stop guessing
    assert rule.animal_scope == "service_dog"


def test_published_carve_out_would_otherwise_be_inert():
    """Regression guard for D1: a published rule carrying ONLY the coarse scope
    confers nothing, so a publish() that drops the precise fields is exactly the
    failure this test exists to catch — expressed through the resolver itself."""
    from app.rulespec.v05_resolver import LayeredRule, resolve

    coarse_only = LayeredRule(
        id="r-coarse",
        animal_scope="service_dog",
        action="enter",
        effect="allowed",
        rule_layer="OPERATOR_POLICY",
        origin="operator_direct",
        subject_scope_normalized=None,
        normalization_type=None,
    )
    precise = LayeredRule(
        id="r-precise",
        animal_scope="service_dog",
        action="enter",
        effect="allowed",
        rule_layer="OPERATOR_POLICY",
        origin="operator_direct",
        subject_scope_normalized=AnimalRole.GUIDE_DOG.value,
        normalization_type=NormalizationType.EXACT.value,
    )
    query = frozenset({AnimalRole.GUIDE_DOG.value})
    kw = dict(
        legal=[],
        guidance=[],
        template_rules=[],
        event_rules=[],
        animal="dog",
        service_role="working",
        action="enter",
        zone_id=None,
        now=datetime.now(UTC),
    )
    assert resolve(operator_rules=[coarse_only], **kw).effect == "unknown"
    assert resolve(operator_rules=[precise], **kw).effect == "allowed"
    assert query


def test_gate_blocks_publishing_the_unproven_widening(db_session):
    """End-to-end: the same defective shape must not clear validate_for_publish."""
    from app.services.publish_gate import validate_for_publish

    src = _source(db_session)
    cand = _approved(
        db_session,
        source_id=src.id,
        animal_scope="service_dog",
        source_scope_exact="service_dog",
        subject_scope_normalized=None,
        normalization_type=None,
    )
    with pytest.raises(ApiError) as exc:
        validate_for_publish(db_session, cand)
    assert exc.value.code == "service_dog_scope_unproven"


def test_candidate_model_exposes_every_adr025_field():
    """The ingest surface must be able to carry the full source-faithful tuple."""
    for field in (
        "source_scope_exact",
        "subject_scope_normalized",
        "normalization_type",
        "normative_effect",
        "holder_scope",
        "operator_obligations",
    ):
        assert hasattr(RuleCandidate, field), field
