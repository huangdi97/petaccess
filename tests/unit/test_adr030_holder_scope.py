"""ADR-031 · holder-scope and service-role semantics (the last ADR-030 gap).

Two measured defects, both of which made a carve-out wider than its source:

P0-01
    ``holder_scope`` existed on the row and was never read by the resolver, so
    「盲人携带导盲犬的，不受本条规定的限制」 answered an unconditional
    ``allowed`` for *any* handler.

P0-02
    An underspecified ``service_dog`` query expanded to four assistance roles
    and inherited the guide-dog proviso through **existence semantics**: "one
    child of the parent scope hits an exception, so the parent is allowed".

The law this must not misrepresent
----------------------------------

《上海市养犬管理条例》第二十三条: dogs are prohibited from malls, museums,
restaurants… with the proviso 「盲人携带导盲犬的，不受本条规定的限制。」 Three
conditions sit inside one sentence: the subject (导盲犬), the holder (盲人) and
the instrument (本条). A platform that drops the holder tells a mall it must
admit any handler's guide dog; a platform that keeps the holder but answers
``prohibited`` when the holder is simply unknown hides a statutory right behind
a missing input. Both are wrong, so the third state — conditional with a named
missing input — is part of the contract, not a nicety.

Privacy boundary
----------------

Whether a person has a disability is a sensitive attribute. The tests below
therefore also lock the boundary: ``HolderContext`` is ephemeral, is never a
column, and "not supplied" is never silently read as "no".
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.models.enums import AnimalRole, HolderScope
from app.rulespec.holder_scope import (
    MISSING_CONTEXT_HOLDER_SCOPE,
    MISSING_CONTEXT_SERVICE_ROLE,
    HolderContext,
    HolderMatch,
    evaluate_holder,
)
from app.rulespec.v05_resolver import (
    ComplianceState,
    LayeredException,
    LayeredRule,
    resolve,
)

NOW = datetime(2026, 9, 18, 12, 0, tzinfo=UTC)

#: two ``source`` rows of the *same* statute (a police-site reprint and the
#: municipal portal full text) — the reason ADR-030 binds by instrument list.
STATUTE_A = "src-sh-regulation-police-reprint"
STATUTE_B = "src-sh-regulation-portal"
#: a different jurisdiction's regulation, and a venue's own 参观须知
OTHER_JURISDICTION = "src-bj-regulation"
VENUE_NOTICE = "src-museum-visitor-notice"

MATCHING_HOLDER = HolderContext.of(HolderScope.PERSON_WITH_DISABILITY.value)
NON_MATCHING_HOLDER = HolderContext.of()


def legal_dog_ban(
    rule_id: str = "legal-dog-ban",
    *,
    source_id: str = STATUTE_A,
    layer: str = "LEGAL",
    effect: str = "prohibited",
    subject_scope: str = "dog",
    animal_scope: str = "dog",
) -> LayeredRule:
    """第二十三条: 禁止携带犬只进入… (mandatory, LEGAL, dog-scoped)."""
    return LayeredRule(
        id=rule_id,
        animal_scope=animal_scope,
        action="enter",
        effect=effect,
        rule_layer=layer,
        origin="legal",
        mandatory_level="mandatory",
        source_id=source_id,
        subject_scope_normalized=subject_scope,
        normalization_type="exact",
    )


def jprov_001(**kwargs) -> LayeredException:
    """The jurisdiction-level 但书, as activated in production."""
    base = {
        "id": "JPROV-001",
        "rule_id": "",  # instrument-bound: no single base rule is named
        "animal_scope": "service_dog",
        "effect": "allowed",
        "source_id": STATUTE_B,
        "status": "current",
        "source_scope_exact": "导盲犬",
        "subject_scope_normalized": AnimalRole.GUIDE_DOG.value,
        "normalization_type": "exact",
        "normative_effect": "exempt_from_prohibition",
        # 「盲人携带导盲犬」 — the holder half of the norm, at last enforced.
        "holder_scope": HolderScope.PERSON_WITH_DISABILITY.value,
        "binding": "instrument",
        "instrument_source_ids": (STATUTE_A, STATUTE_B),
        "applies_to_layer": "LEGAL",
        "applies_to_effects": ("prohibited",),
    }
    base.update(kwargs)
    return LayeredException(**base)


def legacy_place_exception(**kwargs) -> LayeredException:
    """A pre-ADR-030 copy of the same proviso, bound to one venue rule."""
    base = {
        "id": "exc-legacy-place",
        "rule_id": "legal-dog-ban",
        "animal_scope": "service_dog",
        "effect": "allowed",
        "source_id": STATUTE_A,
        "status": "current",
        "subject_scope_normalized": AnimalRole.GUIDE_DOG.value,
        "normalization_type": "exact",
        "normative_effect": "exempt_from_prohibition",
        "holder_scope": HolderScope.PERSON_WITH_DISABILITY.value,
    }
    base.update(kwargs)
    return LayeredException(**base)


def _resolve(
    bases,
    exceptions,
    *,
    service_role="working",
    declared_role=None,
    holder_context=None,
    now=NOW,
):
    return resolve(
        legal=list(bases),
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role=service_role,
        action="enter",
        zone_id=None,
        now=now,
        exceptions=list(exceptions),
        declared_role=declared_role,
        holder_context=holder_context,
    )


# --------------------------------------------------------------------------- #
# §22 · the required matrix
# --------------------------------------------------------------------------- #


def test_01_ordinary_dog_and_legal_base_is_prohibited():
    rs = _resolve(
        [legal_dog_ban()],
        [jprov_001()],
        service_role="none",
        declared_role=AnimalRole.ORDINARY_DOG.value,
        holder_context=MATCHING_HOLDER,
    )
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


def test_02_guide_dog_with_matching_holder_applies_jprov_001():
    rs = _resolve(
        [legal_dog_ban()],
        [jprov_001()],
        declared_role=AnimalRole.GUIDE_DOG.value,
        holder_context=MATCHING_HOLDER,
    )
    assert rs.effect == "allowed"
    assert rs.applied_exceptions == ["JPROV-001"]
    # the trace must name the holder condition and its outcome, not just the
    # subject (§20): "guide dog allowed" alone would hide a legal condition.
    assert any("holder condition" in step for step in rs.explanation_steps)


def test_03_guide_dog_with_non_matching_holder_does_not_apply_jprov_001():
    rs = _resolve(
        [legal_dog_ban()],
        [jprov_001()],
        declared_role=AnimalRole.GUIDE_DOG.value,
        holder_context=NON_MATCHING_HOLDER,
    )
    assert rs.applied_exceptions == []
    assert rs.effect == "prohibited"  # the base decides, as the source does
    assert any("holder condition is not satisfied" in s for s in rs.explanation_steps)


def test_04_guide_dog_with_unknown_holder_is_conditional_not_allowed_not_prohibited():
    rs = _resolve([legal_dog_ban()], [jprov_001()], declared_role=AnimalRole.GUIDE_DOG.value)
    assert rs.effect == "conditional"
    assert rs.applied_exceptions == []
    assert rs.missing_inputs == [MISSING_CONTEXT_HOLDER_SCOPE]
    assert rs.pending_exceptions == ["JPROV-001"]
    # the two forbidden answers, named so they cannot creep back in
    assert rs.effect != "allowed"
    assert rs.effect != "prohibited"


def test_05_generic_service_dog_is_not_allowed_via_the_guide_dog_proviso():
    rs = _resolve([legal_dog_ban()], [jprov_001()], holder_context=MATCHING_HOLDER)
    assert rs.applied_exceptions == []
    assert rs.effect != "allowed"
    assert rs.effect == "conditional"
    assert rs.missing_inputs == [MISSING_CONTEXT_SERVICE_ROLE]


@pytest.mark.parametrize(
    "role", [AnimalRole.POLICE_DOG.value, AnimalRole.MILITARY_WORKING_DOG.value]
)
def test_06_07_working_dogs_never_inherit_the_guide_dog_proviso(role):
    rs = _resolve(
        [legal_dog_ban()],
        [jprov_001()],
        declared_role=role,
        holder_context=MATCHING_HOLDER,
    )
    assert rs.applied_exceptions == []
    assert rs.effect == "prohibited"


@pytest.mark.parametrize(
    "role",
    [
        AnimalRole.HEARING_DOG.value,
        AnimalRole.ASSISTANCE_DOG.value,
        AnimalRole.OTHER_SERVICE_DOG.value,
    ],
)
def test_08_other_assistance_roles_need_their_own_source(role):
    """ADR-025 keeps holding: the proviso names 导盲犬 and nothing wider."""
    rs = _resolve(
        [legal_dog_ban()],
        [jprov_001()],
        declared_role=role,
        holder_context=MATCHING_HOLDER,
    )
    assert rs.applied_exceptions == []
    assert rs.effect == "prohibited"


def test_09_operator_policy_guide_dog_exception_is_not_polluted_by_the_legal_holder_rule():
    """§14: the holder condition belongs to the carve-out that declares it.

    An operator who writes 「导盲犬可以进入」 with no holder restriction is
    unrestricted by *its own* source. Requiring 盲人 there would be inventing a
    condition the operator never stated.
    """
    operator_ban = legal_dog_ban("op-dog-ban", layer="OPERATOR_POLICY", source_id=VENUE_NOTICE)
    unrestricted = legacy_place_exception(
        id="exc-operator-guide", rule_id="op-dog-ban", source_id=VENUE_NOTICE, holder_scope=None
    )
    rs = _resolve(
        [operator_ban],
        [unrestricted, jprov_001()],
        declared_role=AnimalRole.GUIDE_DOG.value,
        # no holder context at all, and none is owed for the operator's row
        holder_context=None,
    )
    assert rs.applied_exceptions == ["exc-operator-guide"]
    assert rs.effect == "allowed"


def test_10_legacy_place_exception_and_jprov_001_are_not_applied_twice():
    """§17: same normative content twice ⇒ one effect, two provenance ids."""
    rs = _resolve(
        [legal_dog_ban()],
        [legacy_place_exception(), jprov_001()],
        declared_role=AnimalRole.GUIDE_DOG.value,
        holder_context=MATCHING_HOLDER,
    )
    assert rs.effect == "allowed"
    # the *effect* is computed once: exactly one exception-derived rule governs
    assert sum(1 for r in rs.applicable_rules if r.origin == "exception") == 1
    assert len(rs.applied_exceptions) == 1
    # …and the second claim is still traceable, not silently dropped
    assert rs.duplicate_exceptions
    assert set(rs.applied_exceptions) | set(rs.duplicate_exceptions) == {
        "JPROV-001",
        "exc-legacy-place",
    }


def test_11_wrong_jurisdiction_never_inherits_the_proviso():
    """§18: the binding is the *legal file*, not "this venue is in Shanghai"."""
    base = legal_dog_ban("bj-dog-ban", source_id=OTHER_JURISDICTION)
    rs = _resolve(
        [base],
        [jprov_001()],
        declared_role=AnimalRole.GUIDE_DOG.value,
        holder_context=MATCHING_HOLDER,
    )
    assert rs.applied_exceptions == []
    assert rs.effect == "prohibited"


def test_12_wrong_provision_of_the_same_instrument_does_not_get_the_proviso():
    """§22.12: a different provision of the same statute is not carved out.

    Clause identity is currently expressed as (instrument, layer, effect,
    scope) because ``access_rule`` carries no clause reference — the reported
    limitation, not a licence to widen. Each distinguishing condition is
    asserted separately below.
    """
    provisions = {
        "different_effect": legal_dog_ban("r-cond", effect="conditional"),
        "different_layer": legal_dog_ban("r-op", layer="OPERATOR_POLICY", source_id=STATUTE_A),
        "different_scope": legal_dog_ban("r-other", animal_scope="other", subject_scope="other"),
        "different_instrument": legal_dog_ban("r-notice", source_id=VENUE_NOTICE),
    }
    for label, base in provisions.items():
        rs = _resolve(
            [base],
            [jprov_001()],
            declared_role=AnimalRole.GUIDE_DOG.value,
            holder_context=MATCHING_HOLDER,
        )
        assert rs.applied_exceptions == [], label


def test_13_expired_provision_never_applies():
    expired = jprov_001(effective_to=NOW - timedelta(days=1))
    rs = _resolve(
        [legal_dog_ban()],
        [expired],
        declared_role=AnimalRole.GUIDE_DOG.value,
        holder_context=MATCHING_HOLDER,
    )
    assert rs.applied_exceptions == []
    assert rs.effect == "prohibited"


# --------------------------------------------------------------------------- #
# §7 · the three states of a holder condition, and the privacy boundary
# --------------------------------------------------------------------------- #


def test_holder_match_has_four_states_and_unknown_is_its_own_state():
    assert evaluate_holder(None, None) is HolderMatch.NOT_REQUIRED
    assert evaluate_holder(HolderScope.ANY_HANDLER.value, None) is HolderMatch.NOT_REQUIRED
    assert (
        evaluate_holder(HolderScope.PERSON_WITH_DISABILITY.value, MATCHING_HOLDER)
        is HolderMatch.MATCHES
    )
    assert (
        evaluate_holder(HolderScope.PERSON_WITH_DISABILITY.value, NON_MATCHING_HOLDER)
        is HolderMatch.DOES_NOT_MATCH
    )
    assert evaluate_holder(HolderScope.PERSON_WITH_DISABILITY.value, None) is HolderMatch.UNKNOWN
    # "supplied and empty" ≠ "not supplied": the first is a known non-match
    assert HolderContext.of().supplied
    assert not HolderContext.unknown().supplied


def test_holder_context_is_ephemeral_and_never_defaulted():
    """§4: no holder context is the default, and it is never a stored field."""
    assert HolderContext.unknown().scopes is None
    # the resolver's default (no argument) must be the unknown context, never
    # "no disability" — which would silently prohibit a statutory right.
    rs = _resolve([legal_dog_ban()], [jprov_001()], declared_role=AnimalRole.GUIDE_DOG.value)
    assert rs.effect == "conditional"


def test_a_carve_out_without_a_holder_condition_is_unaffected():
    """§14 again, from the other side: no declared condition ⇒ no gate."""
    rs = _resolve(
        [legal_dog_ban()],
        [jprov_001(holder_scope=None)],
        declared_role=AnimalRole.GUIDE_DOG.value,
        holder_context=None,
    )
    assert rs.applied_exceptions == ["JPROV-001"]
    assert rs.effect == "allowed"
    assert rs.missing_inputs == []


# --------------------------------------------------------------------------- #
# §13 · the role matrix, as one counted assertion (the safety counts)
# --------------------------------------------------------------------------- #


def test_role_matrix_safety_counts_are_all_zero():
    """The §24 counters, computed over the real ontology rather than asserted.

    Every counter here is a *wrong answer* the platform must never produce, so
    each is expected to be 0 — and each is computed, not hand-written.
    """
    base = legal_dog_ban()
    proviso = jprov_001()
    guide = (AnimalRole.GUIDE_DOG.value, "guide_dog")
    counts = {
        "GUIDE_DOG_MATCHING_HOLDER_WRONG_PROHIBITION": 0,
        "GUIDE_DOG_UNKNOWN_HOLDER_UNCONDITIONAL_ALLOW": 0,
        "SERVICE_DOG_OVERGENERALIZATION": 0,
        "POLICE_DOG_OVERGENERALIZATION": 0,
        "MILITARY_DOG_OVERGENERALIZATION": 0,
        "DOUBLE_APPLIED_EXCEPTION": 0,
        "CROSS_LAYER": 0,
    }

    rs = _resolve([base], [proviso], declared_role=guide[0], holder_context=MATCHING_HOLDER)
    counts["GUIDE_DOG_MATCHING_HOLDER_WRONG_PROHIBITION"] += rs.effect == "prohibited"

    unknown = _resolve([base], [proviso], declared_role=guide[0])
    counts["GUIDE_DOG_UNKNOWN_HOLDER_UNCONDITIONAL_ALLOW"] += unknown.effect == "allowed"

    generic = _resolve([base], [proviso], holder_context=MATCHING_HOLDER)
    counts["SERVICE_DOG_OVERGENERALIZATION"] += generic.effect == "allowed"

    for key, role in (
        ("POLICE_DOG_OVERGENERALIZATION", AnimalRole.POLICE_DOG.value),
        ("MILITARY_DOG_OVERGENERALIZATION", AnimalRole.MILITARY_WORKING_DOG.value),
    ):
        rs_role = _resolve([base], [proviso], declared_role=role, holder_context=MATCHING_HOLDER)
        counts[key] += rs_role.effect == "allowed"

    doubled = _resolve(
        [base],
        [legacy_place_exception(), proviso],
        declared_role=guide[0],
        holder_context=MATCHING_HOLDER,
    )
    counts["DOUBLE_APPLIED_EXCEPTION"] += (
        sum(1 for r in doubled.applicable_rules if r.origin == "exception") != 1
    )

    cross = _resolve(
        [legal_dog_ban("op-ban", layer="OPERATOR_POLICY", source_id=VENUE_NOTICE)],
        [proviso],
        declared_role=guide[0],
        holder_context=MATCHING_HOLDER,
    )
    counts["CROSS_LAYER"] += bool(cross.applied_exceptions)

    assert counts == dict.fromkeys(counts, 0), counts


def test_unknown_holder_never_degrades_compliance_to_a_guess():
    """A withheld carve-out is a missing input, not a conflict."""
    rs = _resolve([legal_dog_ban()], [jprov_001()], declared_role=AnimalRole.GUIDE_DOG.value)
    assert rs.compliance_state == ComplianceState.CONSISTENT
    assert rs.unresolved_conflicts == []
