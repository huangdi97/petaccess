"""Animal-scope legal-fidelity invariants (ADR-020 → ADR-025, Workstream A).

The defect this file exists to pin
----------------------------------

``《上海市养犬管理条例》第二十三条`` prohibits dogs in malls, with a proviso:
「盲人携带导盲犬的，不受本条规定的限制。」 The proviso names **导盲犬** and
nothing wider. The platform used to store it as ``animal_scope='service_dog'``,
reasoning that GUIDE_DOG *is-a* SERVICE_DOG — so the stored row silently claimed
that hearing dogs, assistance dogs and every other service dog were exempt from
the statutory prohibition. Ontology had been used as a legal argument.

The invariant, stated once and tested from every angle:

    ONTOLOGY_PARENT_RELATIONSHIP
    MUST_NOT
    IMPLY_LEGAL_SCOPE_EXPANSION

Map to the Master Goal §5.8 required cases (11):

    1  ordinary dog + mall → prohibited
    2  guide dog + applicable mall → local exception
    3  hearing dog does NOT inherit the Shanghai guide-dog exception
    4  assistance dog does NOT inherit the Shanghai guide-dog exception
    5  national accessibility rule matches guide/hearing/assistance correctly
    6  ontology parent never widens legal effect
    7  POLICE_DOG is not a service dog
    8  MILITARY_WORKING_DOG is not a service dog
    9  Disney: guide dog + leash condition preserved
    10 Shanghai Library: precise scopes for 导盲犬 / 军警犬
    11 gh-outdoor-keep cannot enter the publish queue
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.enums import AnimalRole, HolderScope, NormalizationType
from app.rulespec.animal_scope import (
    COMPOUND_TERM_SPLIT_MEANINGS,
    DOG_ROLES,
    NON_SERVICE_ROLES,
    SERVICE_DOG_QUERY_ROLES,
    QuerySubject,
    compound_split_is_exhaustive,
    holder_scope_allows,
    legal_subjects,
    normalization_confers_legal_effect,
    parent_expansion_is_legal,
    query_subjects,
    rule_governs,
)
from app.rulespec.v05_resolver import LayeredException, LayeredRule, resolve

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
REPO = Path(__file__).resolve().parents[2]
REGISTRY_R2 = REPO / "docs" / "reality_audit" / "review_decisions_r2.json"


# --------------------------------------------------------------------------- #
# Fixtures — the real statutory shape, modelled source-faithfully
# --------------------------------------------------------------------------- #

#: 《上海市养犬管理条例》第23条: dogs are prohibited from malls (base rule).
MALL_DOG_BAN = LayeredRule(
    id="sh-dog-ban",
    animal_scope="dog",
    action="enter",
    effect="prohibited",
    rule_layer="LEGAL",
    origin="legal",
    mandatory_level="mandatory",
    source_id="src-sh-dog-regulation",
)

#: its 但书: 盲人携带导盲犬 — stored as the precise role, declared exact.
GUIDE_DOG_CARVE_OUT = LayeredException(
    id="exc-guide",
    rule_id="sh-dog-ban",
    animal_scope="service_dog",  # coarse public-API scope, unchanged
    effect="allowed",
    source_id="src-sh-dog-regulation",
    source_scope_exact="导盲犬",
    subject_scope_normalized=AnimalRole.GUIDE_DOG.value,
    normalization_type=NormalizationType.EXACT.value,
    normative_effect="exempt_from_prohibition",
    holder_scope="person_with_disability",
)


def _resolve(legal, operator=(), exceptions=(), *, service_role, declared_role=None):
    return resolve(
        legal=list(legal),
        guidance=[],
        template_rules=[],
        operator_rules=list(operator),
        event_rules=[],
        animal="dog",
        service_role=service_role,
        action="enter",
        zone_id=None,
        now=NOW,
        exceptions=list(exceptions),
        declared_role=declared_role,
    )


# --------------------------------------------------------------------------- #
# 1–4 · the statutory case
# --------------------------------------------------------------------------- #


def test_01_ordinary_dog_in_mall_is_prohibited():
    rs = _resolve([MALL_DOG_BAN], exceptions=[GUIDE_DOG_CARVE_OUT], service_role="none")
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


def test_02_guide_dog_in_mall_gets_the_local_exception():
    rs = _resolve(
        [MALL_DOG_BAN],
        exceptions=[GUIDE_DOG_CARVE_OUT],
        service_role="working",
        declared_role=AnimalRole.GUIDE_DOG.value,
    )
    assert rs.effect == "allowed"
    assert rs.applied_exceptions == ["exc-guide"]
    assert any("exempted by exception" in reason for _, reason in rs.suppressed_rules)


def test_03_hearing_dog_does_not_inherit_the_guide_dog_exception():
    rs = _resolve(
        [MALL_DOG_BAN],
        exceptions=[GUIDE_DOG_CARVE_OUT],
        service_role="working",
        declared_role=AnimalRole.HEARING_DOG.value,
    )
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


def test_04_assistance_dog_does_not_inherit_the_guide_dog_exception():
    for role in (AnimalRole.ASSISTANCE_DOG, AnimalRole.OTHER_SERVICE_DOG):
        rs = _resolve(
            [MALL_DOG_BAN],
            exceptions=[GUIDE_DOG_CARVE_OUT],
            service_role="working",
            declared_role=role.value,
        )
        assert rs.effect == "prohibited", role
        assert rs.applied_exceptions == [], role


# --------------------------------------------------------------------------- #
# 5 · the national accessibility rule (a duty, not a blanket permission)
# --------------------------------------------------------------------------- #


def _national_accessibility_rule() -> LayeredRule:
    """《无障碍环境建设法》第46条: guide / hearing / assistance dogs are to be
    facilitated for persons with disabilities.

    Modelled as ``service_dog`` **declared exact** (the source itself names the
    assistance category) with ``facilitation_required`` — a duty the venue owes.
    The 3-value API reduces that to ``conditional``, never ``allowed``: a duty is
    not a permission.
    """
    return LayeredRule(
        id="national-accessibility",
        animal_scope="service_dog",
        action="enter",
        effect="conditional",
        rule_layer="LEGAL",
        origin="legal",
        mandatory_level="mandatory",
        source_id="src-accessibility-law",
        source_scope_exact="导盲犬、助听犬、辅助犬",
        subject_scope_normalized="service_dog",
        normalization_type=NormalizationType.EXACT.value,
        normative_effect="facilitation_required",
        holder_scope=HolderScope.PERSON_WITH_DISABILITY.value,
    )


def test_05_national_rule_matches_all_assistance_roles_but_not_working_dogs():
    rule = _national_accessibility_rule()
    for role in (
        AnimalRole.GUIDE_DOG,
        AnimalRole.HEARING_DOG,
        AnimalRole.ASSISTANCE_DOG,
        AnimalRole.OTHER_SERVICE_DOG,
    ):
        rs = _resolve([rule], service_role="working", declared_role=role.value)
        assert rs.effect == "conditional", role
        assert "facilitation_required" in {r.normative_effect for r in rs.applicable_rules}

    for role in (AnimalRole.POLICE_DOG, AnimalRole.MILITARY_WORKING_DOG):
        rs = _resolve([rule], service_role="working", declared_role=role.value)
        assert rs.effect == "unknown", role

    # and never for an ordinary pet
    assert _resolve([rule], service_role="none").effect == "unknown"


def test_05b_facilitation_duty_is_never_rendered_as_unconditional_allowed():
    from app.models.enums import NORMATIVE_TO_EFFECT

    assert NORMATIVE_TO_EFFECT["facilitation_required"] == "conditional"
    assert NORMATIVE_TO_EFFECT["facilitation_required"] != "allowed"


def test_05c_holder_scope_confines_the_duty_to_persons_with_disabilities():
    scope = HolderScope.PERSON_WITH_DISABILITY.value
    assert holder_scope_allows(scope, is_person_with_disability=True) is True
    assert holder_scope_allows(scope, is_person_with_disability=False) is False
    # a rule that names no holder (or any handler) is unaffected
    assert holder_scope_allows(None, is_person_with_disability=False) is True
    assert (
        holder_scope_allows(HolderScope.ANY_HANDLER.value, is_person_with_disability=False) is True
    )


# --------------------------------------------------------------------------- #
# 6 · the invariant itself — ontology is a query convenience, never law
# --------------------------------------------------------------------------- #


def test_06_ontology_parent_never_widens_legal_effect():
    """A rule the source scoped to 导盲犬 must not govern hearing dogs, even
    though GUIDE_DOG is-a SERVICE_DOG in the taxonomy."""
    assert AnimalRole.GUIDE_DOG.value in SERVICE_DOG_QUERY_ROLES  # ontology holds
    # …and yet the legal scope is exactly one role:
    legal = legal_subjects("service_dog", AnimalRole.GUIDE_DOG.value, "exact")
    assert legal == frozenset({AnimalRole.GUIDE_DOG.value})

    guide_query = query_subjects(QuerySubject("dog", "working", AnimalRole.GUIDE_DOG.value))
    hearing_query = query_subjects(QuerySubject("dog", "working", AnimalRole.HEARING_DOG.value))
    assert rule_governs(guide_query, "service_dog", "guide_dog", "exact")
    assert not rule_governs(hearing_query, "service_dog", "guide_dog", "exact")


def test_06b_parent_expansion_is_only_legal_when_the_source_said_the_same_thing():
    assert parent_expansion_is_legal("guide_dog", "guide_dog") is True
    assert parent_expansion_is_legal("guide_dog", "service_dog") is False
    assert parent_expansion_is_legal("导盲犬", "service_dog") is False


def test_06c_non_exact_normalisation_confers_no_legal_effect():
    for norm in (
        NormalizationType.LEGAL_INTERPRETATION_REQUIRED.value,
        NormalizationType.PARENT_GROUP_FOR_QUERY_ONLY.value,
    ):
        assert legal_subjects("service_dog", "service_dog", norm) is None
    # legacy row: bare `service_dog`, no normalisation recorded → governs nothing
    assert legal_subjects("service_dog", None, None) is None
    # …but the scopes the source literally named still do
    assert legal_subjects("dog", "dog", "exact") == DOG_ROLES
    assert legal_subjects("ordinary_pet", "ordinary_pet", "exact") is not None


def test_06d_query_side_expansion_is_what_makes_the_rule_discoverable():
    """A generic "service dog" question must still find a guide-dog rule — that
    is the *only* thing the parent relation is for."""
    generic = query_subjects(QuerySubject("dog", "working", None))
    assert generic == SERVICE_DOG_QUERY_ROLES
    assert rule_governs(generic, "service_dog", "guide_dog", "exact")
    # while a declared role does not expand
    declared = query_subjects(QuerySubject("dog", "working", AnimalRole.HEARING_DOG.value))
    assert declared == frozenset({AnimalRole.HEARING_DOG.value})


# --------------------------------------------------------------------------- #
# 7–8 · working dogs are not service dogs
# --------------------------------------------------------------------------- #


def test_07_police_dog_is_not_a_service_dog():
    assert AnimalRole.POLICE_DOG.value not in SERVICE_DOG_QUERY_ROLES
    assert AnimalRole.POLICE_DOG.value in NON_SERVICE_ROLES
    # a service-dog-scoped rule does not govern a police dog
    assert not rule_governs(
        query_subjects(QuerySubject("dog", "working", AnimalRole.POLICE_DOG.value)),
        "service_dog",
        "service_dog",
        "exact",
    )
    # and a police dog is still a dog
    assert rule_governs(
        query_subjects(QuerySubject("dog", "none", AnimalRole.POLICE_DOG.value)),
        "dog",
        "dog",
        "exact",
    )


def test_08_military_working_dog_is_not_a_service_dog():
    assert AnimalRole.MILITARY_WORKING_DOG.value not in SERVICE_DOG_QUERY_ROLES
    assert AnimalRole.MILITARY_WORKING_DOG.value in NON_SERVICE_ROLES
    assert not rule_governs(
        query_subjects(QuerySubject("dog", "working", AnimalRole.MILITARY_WORKING_DOG.value)),
        "service_dog",
        "service_dog",
        "exact",
    )


def test_08b_taxonomy_is_complete_and_partitioned():
    """Every role is either a service (assistance) dog or it is not."""
    assert SERVICE_DOG_QUERY_ROLES | NON_SERVICE_ROLES == DOG_ROLES
    assert frozenset() == SERVICE_DOG_QUERY_ROLES & NON_SERVICE_ROLES
    assert len(DOG_ROLES) == len(AnimalRole)


# --------------------------------------------------------------------------- #
# 9 · Disney — precise scope + the leash condition is preserved
# --------------------------------------------------------------------------- #


def test_09_disney_guide_dog_keeps_the_leash_condition():
    disney_guide = LayeredRule(
        id="dl-guide-op",
        animal_scope="service_dog",
        action="enter",
        effect="conditional",
        rule_layer="OPERATOR_POLICY",
        origin="operator_direct",
        conditions=({"condition_type": "leash_required", "value_flag": True},),
        source_id="src-disney-official",
        source_scope_exact="导盲犬",
        subject_scope_normalized=AnimalRole.GUIDE_DOG.value,
        normalization_type="exact",
    )
    rs = _resolve(
        [],
        operator=[disney_guide],
        service_role="working",
        declared_role=AnimalRole.GUIDE_DOG.value,
    )
    assert rs.effect == "conditional"
    # the condition survives on the governing rule (`obligations` is reserved for
    # LEGAL obligations + exception conditions, so read the rule's own conditions)
    cond_types = {c["condition_type"] for r in rs.applicable_rules for c in r.conditions}
    assert "leash_required" in cond_types

    # a hearing dog gets no Disney policy at all (the source named 导盲犬 only)
    rs_hearing = _resolve(
        [],
        operator=[disney_guide],
        service_role="working",
        declared_role=AnimalRole.HEARING_DOG.value,
    )
    assert rs_hearing.effect == "unknown"


# --------------------------------------------------------------------------- #
# 10 · Shanghai Library — 导盲犬、军警犬 must be three precise scopes
# --------------------------------------------------------------------------- #


def _library_rules() -> tuple[list[LayeredRule], list[LayeredException]]:
    """《读者须知》: 「请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。」

    The exception is **compound**: 导盲犬 is one named role; 军警犬 is a compound
    term that the source does not further split. Per ADR-028 it therefore becomes
    two rows that share the verbatim ``source_scope_exact='军警犬'`` and declare
    ``normalization_type='compound_term_split'`` — each carrying exactly one
    member of the term's documented meaning.
    """
    base = LayeredRule(
        id="lib-dog-ban",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer="LEGAL",
        origin="legal",
        mandatory_level="mandatory",
        source_id="src-sh-dog-regulation",
    )
    guide = LayeredException(
        id="exc-guide_dog",
        rule_id="lib-dog-ban",
        animal_scope="service_dog",
        effect="allowed",
        source_id="src-library-notice",
        source_scope_exact="导盲犬",
        subject_scope_normalized=AnimalRole.GUIDE_DOG.value,
        normalization_type=NormalizationType.EXACT.value,
        normative_effect="exempt_from_prohibition",
    )
    compound_members = [
        LayeredException(
            id=f"exc-{role.value}",
            rule_id="lib-dog-ban",
            animal_scope="dog",
            effect="allowed",
            source_id="src-library-notice",
            # the compound wording is kept VERBATIM — never reworded to 警犬
            source_scope_exact="军警犬",
            subject_scope_normalized=role.value,
            normalization_type=NormalizationType.COMPOUND_TERM_SPLIT.value,
            normative_effect="exempt_from_prohibition",
        )
        for role in (AnimalRole.POLICE_DOG, AnimalRole.MILITARY_WORKING_DOG)
    ]
    return [base], [guide, *compound_members]


def test_10_shanghai_library_precise_scopes():
    legal, excs = _library_rules()
    allowed_roles = (
        AnimalRole.GUIDE_DOG,
        AnimalRole.POLICE_DOG,
        AnimalRole.MILITARY_WORKING_DOG,
    )
    for role in allowed_roles:
        rs = _resolve(legal, exceptions=excs, service_role="working", declared_role=role.value)
        assert rs.effect == "allowed", role

    # roles the notice does NOT name keep the statutory prohibition
    for role in (
        AnimalRole.HEARING_DOG,
        AnimalRole.ASSISTANCE_DOG,
        AnimalRole.OTHER_SERVICE_DOG,
        AnimalRole.ORDINARY_DOG,
    ):
        rs = _resolve(legal, exceptions=excs, service_role="working", declared_role=role.value)
        assert rs.effect == "prohibited", role


def test_10b_compound_rows_keep_the_source_wording_verbatim():
    """ADR-028: 军警犬 stays 军警犬. Rewriting it to 「警犬」 would be the
    platform inventing a narrower source than the one actually published."""
    _, excs = _library_rules()
    compound = [e for e in excs if e.normalization_type == "compound_term_split"]
    assert len(compound) == 2
    assert {e.source_scope_exact for e in compound} == {"军警犬"}
    assert {e.subject_scope_normalized for e in compound} == {
        AnimalRole.POLICE_DOG.value,
        AnimalRole.MILITARY_WORKING_DOG.value,
    }


def test_10c_compound_split_is_exhaustive_and_closed():
    declared = COMPOUND_TERM_SPLIT_MEANINGS["军警犬"]
    assert declared == frozenset(
        {AnimalRole.POLICE_DOG.value, AnimalRole.MILITARY_WORKING_DOG.value}
    )
    members = frozenset({AnimalRole.POLICE_DOG.value, AnimalRole.MILITARY_WORKING_DOG.value})
    assert compound_split_is_exhaustive("军警犬", members) is True
    # dropping a member leaves part of the term's meaning unmodelled
    assert compound_split_is_exhaustive("军警犬", {AnimalRole.POLICE_DOG.value}) is False
    # adding one silently widens to a role the term does not include
    assert compound_split_is_exhaustive("军警犬", members | {AnimalRole.GUIDE_DOG.value}) is False
    # an undocumented term may never be split
    assert compound_split_is_exhaustive("导盲犬", {AnimalRole.GUIDE_DOG.value}) is False


def test_10d_compound_term_split_conveys_legal_effect_for_its_own_member_only():
    police = legal_subjects("dog", AnimalRole.POLICE_DOG.value, "compound_term_split")
    military = legal_subjects("dog", AnimalRole.MILITARY_WORKING_DOG.value, "compound_term_split")
    assert police == frozenset({AnimalRole.POLICE_DOG.value})
    assert military == frozenset({AnimalRole.MILITARY_WORKING_DOG.value})
    # the split does NOT leak into the coarse service-dog category
    assert legal_subjects("service_dog", "service_dog", "compound_term_split") == (
        SERVICE_DOG_QUERY_ROLES
    )
    # and it does not rescue a bare service_dog row (which needs `exact`)
    assert legal_subjects("service_dog", "guide_dog", "compound_term_split") == frozenset(
        {AnimalRole.GUIDE_DOG.value}
    )


def test_10e_compound_split_members_are_not_service_dogs():
    """The least obvious leak: 军警犬 working dogs must never be reachable
    through the service-dog query group."""
    for role in (AnimalRole.POLICE_DOG, AnimalRole.MILITARY_WORKING_DOG):
        assert role.value not in SERVICE_DOG_QUERY_ROLES
        for norm in (NormalizationType.EXACT.value, "compound_term_split"):
            assert not rule_governs(
                SERVICE_DOG_QUERY_ROLES,
                "dog",
                role.value,
                norm,
            )


# --------------------------------------------------------------------------- #
# 11 · gh-outdoor-keep must not reach the publish queue
# --------------------------------------------------------------------------- #


def _registry_rows() -> list[dict]:
    assert REGISTRY_R2.exists(), (
        "docs/reality_audit/review_decisions_r2.json is required (regenerate with "
        "scripts/gen_human_review_packet_r2.py)"
    )
    return json.loads(REGISTRY_R2.read_text(encoding="utf-8"))["rows"]


def test_11_gh_outdoor_keep_is_rejected_and_never_publishable():
    rows = [r for r in _registry_rows() if r["rule_id"] == "gh-outdoor-keep"]
    assert rows, "gh-outdoor-keep is missing from the R2 register"
    row = rows[0]
    assert row["proposed_decision"] == "RECOMMEND_REJECT"
    # an AI recommendation is not a ruling — the human field must stay blank
    assert not row.get("final_decision")
    reasons = " ".join(row.get("reject_reason_codes") or [])
    assert "INSUFFICIENT_PLACE_ZONE_EVIDENCE" in reasons
    assert "LEGAL_SCOPE_CONFLICT" in reasons
    # the claim is source-untraceable
    assert row["evidence_strength"] in {"search_snippet", "social_lead"}


def test_11b_no_registry_row_is_pre_signed_by_the_agent():
    """GOV-01: nothing may be signed without a named human (Master Goal §0.9)."""
    for row in _registry_rows():
        assert not row.get("final_decision"), row["candidate_id"]
        assert not row.get("reviewer"), row["candidate_id"]
        assert not row.get("reviewed_at"), row["candidate_id"]


# --------------------------------------------------------------------------- #
# 12 · an ordinary_pet base is semantically independent of guide dogs
#
# This is the proof behind the publish gate's reachability rule. An operator
# writes 「宠物禁止，导盲犬除外」 and we store the ban as `ordinary_pet` and the
# proviso as `guide_dog`. Under ADR-025 `ordinary_pet` covers
# {ordinary_dog, ordinary_cat, other_pet} — it does NOT govern a guide dog. The
# resolver only applies a carve-out to a base that is in scope for the query, so
# the carve-out can never fire: it is published, linked, audited and inert.
#
# The consequence the publisher depends on: shipping the `ordinary_pet` base on
# its own does **not** create a "guide dog prohibited" user state, so an
# unreachable approved carve-out must not be allowed to hold the base hostage.
# --------------------------------------------------------------------------- #


def _operator_pet_ban() -> LayeredRule:
    return LayeredRule(
        id="op-pet-ban",
        animal_scope="ordinary_pet",
        action="enter",
        effect="prohibited",
        rule_layer="OPERATOR_POLICY",
        origin="operator_direct",
        source_id="src-operator-notice",
        subject_scope_normalized="ordinary_pet",
        normalization_type="exact",
    )


def _guide_dog_proviso(base_id: str) -> LayeredException:
    return LayeredException(
        id="exc-guide-op",
        rule_id=base_id,
        animal_scope="service_dog",
        effect="allowed",
        source_id="src-operator-notice",
        source_scope_exact="导盲犬",
        subject_scope_normalized=AnimalRole.GUIDE_DOG.value,
        normalization_type=NormalizationType.EXACT.value,
        normative_effect="exempt_from_prohibition",
    )


def test_12_ordinary_pet_base_never_governs_a_guide_dog():
    """The base alone must not answer 'prohibited' to a guide-dog query."""
    rs = _resolve(
        [],
        operator=[_operator_pet_ban()],
        service_role="working",
        declared_role=AnimalRole.GUIDE_DOG.value,
    )
    assert rs.effect != "prohibited"
    assert rs.effect == "unknown"
    assert rs.applied_exceptions == []


def test_12b_a_guide_dog_carve_out_of_an_ordinary_pet_base_is_inert():
    base = _operator_pet_ban()
    rs = _resolve(
        [],
        operator=[base],
        exceptions=[_guide_dog_proviso(base.id)],
        service_role="working",
        declared_role=AnimalRole.GUIDE_DOG.value,
    )
    # not allowed → the carve-out did not fire; not prohibited → the base does
    # not govern. Both halves are what "inert" means, and neither is a guess.
    assert rs.effect == "unknown"
    assert rs.applied_exceptions == []
    assert rs.suppressed_rules == []


def test_12c_the_same_carve_out_fires_when_its_base_actually_governs():
    """The contrast case: the predicate is not 'nothing is ever reachable'.

    A `dog` base legally covers every dog role including guide_dog, so the very
    same proviso fires. A reachability check that returns 'unreachable' here too
    would be a broken check, not a careful one.
    """
    base = LayeredRule(
        id="op-dog-ban",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer="OPERATOR_POLICY",
        origin="operator_direct",
        source_id="src-operator-notice",
        subject_scope_normalized="dog",
        normalization_type="exact",
    )
    rs = _resolve(
        [],
        operator=[base],
        exceptions=[_guide_dog_proviso(base.id)],
        service_role="working",
        declared_role=AnimalRole.GUIDE_DOG.value,
    )
    assert rs.effect == "allowed"
    assert rs.applied_exceptions == ["exc-guide-op"]


def test_12d_the_ordinary_pet_base_still_governs_ordinary_pets():
    """Independence is not impotence — the rule must still do its real job."""
    base = _operator_pet_ban()
    rs = _resolve(
        [],
        operator=[base],
        exceptions=[_guide_dog_proviso(base.id)],
        service_role="none",
        declared_role=AnimalRole.ORDINARY_DOG.value,
    )
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


# --------------------------------------------------------------------------- #
# Property: no input combination may widen a source-specific scope
# --------------------------------------------------------------------------- #

_roles = st.sampled_from([r.value for r in AnimalRole])
_scope_names = st.sampled_from(["dog", "ordinary_pet", "service_dog", "cat", "other", None])
_norms = st.sampled_from(
    [
        "exact",
        "compound_term_split",
        "parent_group_for_query_only",
        "legal_interpretation_required",
        None,
    ]
)
_PRECISE = {r.value for r in AnimalRole}


@given(stored_scope=st.one_of(st.none(), _scope_names, _roles), norm=_norms)
@settings(max_examples=300, deadline=None)
def test_property_legal_scope_never_exceeds_an_exact_source_scope(stored_scope, norm):
    """If the stored scope is a single precise role, the legal subjects are
    exactly that role — regardless of which parent it belongs to."""
    subjects = legal_subjects(stored_scope, stored_scope, norm)
    if subjects is None:
        return
    if stored_scope in _PRECISE:
        assert subjects == frozenset({stored_scope})


@given(norm=st.one_of(st.none(), _norms))
@settings(max_examples=100, deadline=None)
def test_property_only_declared_normalisations_confer_legal_effect(norm):
    """Membership is decided against the CLOSED legal set, so a newly added
    normalisation type can never silently become legal by default."""
    legal = set(NormalizationType) & {
        NormalizationType.EXACT,
        NormalizationType.COMPOUND_TERM_SPLIT,
    }
    expected = norm in {e.value for e in legal}
    assert normalization_confers_legal_effect(norm) is expected
    # and the coarse assistance category is only ever law via a legal norm
    if not expected:
        assert legal_subjects("service_dog", "service_dog", norm) is None


@given(
    species=st.sampled_from(["dog", "cat", "other"]),
    service_role=st.sampled_from(["none", "working", "in_training", "unknown"]),
    declared=st.one_of(st.none(), st.sampled_from([r.value for r in AnimalRole])),
)
@settings(max_examples=300, deadline=None)
def test_property_declared_role_never_expands_the_query(species, service_role, declared):
    """A declared role pins the query to that role; only an underspecified
    working-dog query expands."""
    subjects = query_subjects(QuerySubject(species, service_role, declared))
    if declared is not None:
        assert subjects == frozenset({declared})
    elif species == "dog" and service_role in ("working", "in_training"):
        assert subjects == SERVICE_DOG_QUERY_ROLES
    elif species == "dog":
        assert subjects == frozenset({AnimalRole.ORDINARY_DOG.value})
    elif species == "cat":
        assert subjects == frozenset({"ordinary_cat"})
    elif species == "other":
        assert subjects == frozenset({"other_pet"})
    else:
        pytest.fail(f"unexpected species {species}")
