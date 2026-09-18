"""RuleException invariants (SG-REAL-01, PILOT-REVIEW-AND-SCHEMA-FIX-01 S3/S5).

The mechanism is generic — no hardcoded service_dog branch. Covered invariants:

- ordinary dogs stay restricted by a dog-scoped prohibition;
- guide/service dogs are exempted only while the exception is active and sourced;
- expired / withdrawn / superseded exceptions fall back to the base rule;
- an exception without a source never applies;
- exceptions never widen to ordinary pets (cat / ordinary_pet queries);
- conflicting matching exceptions => REVIEW_REQUIRED, never a guess;
- Observation data has no path into the normative resolver (unchanged);
- the v1 evaluator honors exceptions with the same semantics.
"""

from datetime import UTC, datetime, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from app.models.enums import HolderScope
from app.rulespec.holder_scope import HolderContext
from app.rulespec.v05_resolver import (
    ComplianceState,
    LayeredException,
    LayeredRule,
    resolve,
)

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)

STATUTE_BAN = LayeredRule(
    id="legal-dog-ban",
    animal_scope="dog",
    action="enter",
    effect="prohibited",
    rule_layer="LEGAL",
    origin="legal",
    zone_id="indoor",
    source_id="src-statute",
)
GUIDE_EXEMPTION = LayeredException(
    id="exc-butie",
    rule_id="legal-dog-ban",
    animal_scope="service_dog",
    effect="allowed",
    source_id="src-statute",
    # ADR-025: the proviso names 导盲犬 and nothing wider. Stored as the precise
    # role with an *exact* normalisation — that is what lets it confer legal
    # effect. A bare `service_dog` scope (no normalisation) governs nothing.
    subject_scope_normalized="guide_dog",
    normalization_type="exact",
    normative_effect="exempt_from_prohibition",
)


def _precise_exception(**kwargs) -> LayeredException:
    """An exception with the ADR-025 precise-scope fields filled in.

    Every test below wants to exercise *its own* condition (expiry, status,
    provenance, conflict) — not the scope gate. Without these fields the scope
    gate would refuse the exception first and mask the behaviour under test.
    """
    base = {
        "animal_scope": "service_dog",
        "effect": "allowed",
        "subject_scope_normalized": "guide_dog",
        "normalization_type": "exact",
    }
    base.update(kwargs)
    return LayeredException(**base)


def _resolve(
    rules,
    *,
    animal="dog",
    service_role="none",
    exceptions=(),
    zone_id="indoor",
    now=NOW,
    declared_role=None,
    holder_context=None,
):
    by_layer = {
        "legal": [r for r in rules if r.rule_layer == "LEGAL"],
        "guidance": [r for r in rules if r.rule_layer == "REGULATORY_GUIDANCE"],
        "template": [],
        "operator": [r for r in rules if r.rule_layer == "OPERATOR_POLICY"],
        "event": [r for r in rules if r.rule_layer == "TEMPORARY_POLICY"],
    }
    return resolve(
        legal=by_layer["legal"],
        guidance=by_layer["guidance"],
        template_rules=by_layer["template"],
        operator_rules=by_layer["operator"],
        event_rules=by_layer["event"],
        animal=animal,
        service_role=service_role,
        action="enter",
        zone_id=zone_id,
        now=now,
        exceptions=list(exceptions),
        declared_role=declared_role,
        holder_context=holder_context,
    )


# ------------------------------------------------------------- deterministic


def test_ordinary_dog_still_restricted():
    rs = _resolve([STATUTE_BAN], animal="dog", service_role="none", exceptions=[GUIDE_EXEMPTION])
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


def test_service_dog_exempt_via_exception():
    """The carve-out fires when the query names the role *and* the holder."""
    rs = _resolve(
        [STATUTE_BAN],
        animal="dog",
        service_role="working",
        declared_role="guide_dog",
        holder_context=HolderContext.of(HolderScope.PERSON_WITH_DISABILITY.value),
        exceptions=[GUIDE_EXEMPTION],
    )
    assert rs.effect == "allowed"
    assert rs.applied_exceptions == ["exc-butie"]
    assert any("exempted by exception" in reason for _, reason in rs.suppressed_rules)


def test_underspecified_service_dog_query_is_not_allowed_by_a_guide_dog_carve_out():
    """ADR-031 §12: a group query never inherits one member's allowance.

    The previous behaviour — "a child of the parent scope hits an exception, so
    the parent query is allowed" — answered a question the source never
    answered. The honest answer is conditional, with the missing role named, so
    a consumer can ask 「具体属于哪类工作/服务动物？」 instead.
    """
    rs = _resolve([STATUTE_BAN], animal="dog", service_role="working", exceptions=[GUIDE_EXEMPTION])
    assert rs.effect == "conditional"
    assert rs.applied_exceptions == []
    assert rs.pending_exceptions == ["exc-butie"]
    assert rs.missing_inputs == ["service_role"]


def test_expired_exception_falls_back_to_base():
    expired = _precise_exception(
        id="exc-old",
        rule_id="legal-dog-ban",
        source_id="src-statute",
        effective_to=NOW - timedelta(days=1),
    )
    rs = _resolve([STATUTE_BAN], animal="dog", service_role="working", exceptions=[expired])
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


def test_future_exception_not_yet_effective():
    future = _precise_exception(
        id="exc-future",
        rule_id="legal-dog-ban",
        source_id="src-statute",
        effective_from=NOW + timedelta(days=1),
    )
    rs = _resolve([STATUTE_BAN], animal="dog", service_role="working", exceptions=[future])
    assert rs.effect == "prohibited"


def test_withdrawn_and_superseded_exceptions_never_apply():
    for status in ("withdrawn", "superseded", "archived"):
        exc = _precise_exception(
            id="exc-dead", rule_id="legal-dog-ban", source_id="src-statute", status=status
        )
        rs = _resolve([STATUTE_BAN], animal="dog", service_role="working", exceptions=[exc])
        assert rs.effect == "prohibited", status


def test_exception_without_source_never_applies():
    exc = _precise_exception(id="exc-nosrc", rule_id="legal-dog-ban", source_id=None)
    rs = _resolve([STATUTE_BAN], animal="dog", service_role="working", exceptions=[exc])
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


def test_exception_never_widens_to_ordinary_pets():
    """A service_dog exception must not touch cat / ordinary pet queries."""
    for animal, role in (("cat", "none"), ("dog", "none")):
        rs = _resolve([STATUTE_BAN], animal=animal, service_role=role, exceptions=[GUIDE_EXEMPTION])
        if animal == "cat":
            assert rs.effect == "unknown"  # dog-scope ban doesn't govern cats
        else:
            assert rs.effect == "prohibited"
        assert rs.applied_exceptions == []


def test_conflicting_exceptions_force_review():
    contradict = _precise_exception(
        id="exc-no", rule_id="legal-dog-ban", effect="prohibited", source_id="src-other"
    )
    rs = _resolve(
        [STATUTE_BAN],
        animal="dog",
        service_role="working",
        exceptions=[GUIDE_EXEMPTION, contradict],
    )
    assert rs.compliance_state == ComplianceState.REVIEW_REQUIRED


def test_exception_carries_explanation_and_source_ref():
    rs = _resolve([STATUTE_BAN], animal="dog", service_role="working", exceptions=[GUIDE_EXEMPTION])
    joined = "\n".join(rs.explanation_steps)
    assert "exc-butie" in joined
    assert any(r.source_id == "src-statute" for r in rs.applicable_rules)


def test_conditional_exception_works_too():
    conditional = _precise_exception(
        id="exc-cond",
        rule_id="legal-dog-ban",
        source_id="src-statute",
        effect="conditional",
        conditions=({"condition_type": "leash_required", "value_flag": True},),
    )
    rs = _resolve(
        [STATUTE_BAN],
        animal="dog",
        service_role="working",
        declared_role="guide_dog",
        holder_context=HolderContext.of(HolderScope.PERSON_WITH_DISABILITY.value),
        exceptions=[conditional],
    )
    assert rs.effect == "conditional"
    assert "leash_required" in rs.obligations


def test_evaluator_honors_exceptions():
    """v1 evaluator (POST /rules/evaluate path) with the same exception dict."""
    from app.rulespec.evaluator import evaluate
    from app.rulespec.model import AnimalInput, QueryContext, Rule

    ban = Rule(
        id="legal-dog-ban",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        zone_id="indoor",
        source_id="src-statute",
    )
    ctx = QueryContext(
        animal=AnimalInput(species="dog", service_role="working"),
        place_id="p1",
        zone_id="indoor",
        date_time=NOW,
        intended_action="enter",
    )
    exc = [
        {
            "id": "exc-butie",
            "rule_id": "legal-dog-ban",
            "animal_scope": "service_dog",
            "effect": "allowed",
            "source_id": "src-statute",
            "status": "current",
        }
    ]
    result = evaluate(ctx, [ban], exc)
    assert result.status.value == "MATCH"
    # ordinary dog unaffected
    ctx2 = QueryContext(
        animal=AnimalInput(species="dog", service_role="none"),
        place_id="p1",
        zone_id="indoor",
        date_time=NOW,
        intended_action="enter",
    )
    result2 = evaluate(ctx2, [ban], exc)
    assert result2.status.value == "RESTRICTED"


# ----------------------------------------------------------- property-based

scopes = st.sampled_from(["ordinary_pet", "dog", "service_dog", "cat", "other"])
roles = st.sampled_from(["none", "working", "in_training", "unknown"])
species = st.sampled_from(["dog", "cat", "other"])
statuses = st.sampled_from(["current", "withdrawn", "superseded", "archived", "pending_review"])
window_offsets = st.integers(min_value=-30, max_value=30)
# ADR-025 fields — drawn independently so the property exercises the scope gate.
subject_scopes = st.sampled_from(
    [None, "dog", "ordinary_pet", "service_dog", "cat", "other", "guide_dog", "police_dog"]
)
normalisations = st.sampled_from(
    [None, "exact", "parent_group_for_query_only", "legal_interpretation_required"]
)

_ROLE_SET = {
    "ordinary_dog",
    "guide_dog",
    "hearing_dog",
    "assistance_dog",
    "other_service_dog",
    "police_dog",
    "military_working_dog",
}
_ASSISTANCE_ROLES = {"guide_dog", "hearing_dog", "assistance_dog", "other_service_dog"}


def _expected_legal_scope(exc_animal_scope, subject_scope, normalization_type) -> set[str] | None:
    """Independent re-derivation of the ADR-025 legal scope (hand-written mirror).

    Deliberately NOT importing `app.rulespec.animal_scope` — the point is to
    catch a drift in the production rule, not to restate it.
    """
    if normalization_type in ("legal_interpretation_required", "parent_group_for_query_only"):
        return None
    scope = subject_scope
    if scope is None:
        scope = exc_animal_scope if exc_animal_scope in ("dog", "ordinary_pet") else None
        if scope is None:
            return None
    elif scope == "service_dog" and normalization_type != "exact":
        return None
    if scope == "dog":
        return set(_ROLE_SET)
    if scope == "ordinary_pet":
        return {"ordinary_dog", "ordinary_cat", "other_pet"}
    if scope == "service_dog":
        return set(_ASSISTANCE_ROLES)
    if scope == "cat":
        return {"ordinary_cat"}
    if scope == "other":
        return {"other_pet"}
    if scope in _ROLE_SET:
        return {scope}
    return None


def _expected_query_subjects(sp, rl) -> set[str]:
    if sp == "cat":
        return {"ordinary_cat"}
    if sp == "other":
        return {"other_pet"}
    if sp != "dog":
        return set()
    if rl in ("working", "in_training"):
        return set(_ASSISTANCE_ROLES)
    return {"ordinary_dog"}


@st.composite
def exception_batches(draw):
    n = draw(st.integers(min_value=0, max_value=3))
    out = []
    for i in range(n):
        from_off = draw(window_offsets)
        to_off = draw(window_offsets)
        out.append(
            LayeredException(
                id=f"exc{i}",
                rule_id="legal-dog-ban",
                animal_scope=draw(scopes),
                effect=draw(st.sampled_from(["allowed", "prohibited", "conditional"])),
                source_id=draw(st.sampled_from(["src-statute", None])),
                status=draw(statuses),
                subject_scope_normalized=draw(subject_scopes),
                normalization_type=draw(normalisations),
                effective_from=NOW + timedelta(days=from_off) if from_off != 0 else None,
                effective_to=NOW + timedelta(days=to_off) if to_off != 0 else None,
            )
        )
    return out


@given(exc_batch=exception_batches(), role=roles, species=species)
@settings(max_examples=250, deadline=None)
def test_exception_never_governs_outside_its_scope(exc_batch, role, species):
    """Exceptions apply only to queries their scope matches; the base rule
    otherwise keeps governing. No input combination may invent an effect."""
    rules = [STATUTE_BAN]
    by_layer = {
        "legal": rules,
        "guidance": [],
        "template": [],
        "operator": [],
        "event": [],
    }
    rs = resolve(
        legal=by_layer["legal"],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal=species,
        service_role=role,
        action="enter",
        zone_id="indoor",
        now=NOW,
        exceptions=list(exc_batch),
    )
    # Core invariant (ADR-025): every APPLIED exception must be sourced, active,
    # AND its legal scope must overlap the query's subjects. Anything else
    # applying is a leak — exactly the 导盲犬→service_dog widening.
    query = _expected_query_subjects(species, role)
    for exc_id in rs.applied_exceptions:
        matching = []
        for e in exc_batch:
            if e.id != exc_id or not e.source_id or e.status != "current":
                continue
            if e.effective_from is not None and e.effective_from > NOW:
                continue
            if e.effective_to is not None and e.effective_to < NOW:
                continue
            legal = _expected_legal_scope(
                e.animal_scope, e.subject_scope_normalized, e.normalization_type
            )
            if legal and query & legal:
                matching.append(e)
        assert matching, f"exception {exc_id} applied without source/activity/scope match"

    # `service_dog` declared as an exact scope is legal by construction (the
    # source itself names the category); anything less must never be reachable.
    for exc_id in rs.applied_exceptions:
        src = next(e for e in exc_batch if e.id == exc_id)
        if src.subject_scope_normalized == "service_dog":
            assert src.normalization_type == "exact"


@given(exc_batch=exception_batches(), role=roles)
@settings(max_examples=200, deadline=None)
def test_unknown_inputs_never_become_decided_rules(exc_batch, role):
    """A resolved prohibition always traces to an explicit prohibited rule or
    exception (SG-REAL-01 must not launder bans into exceptions)."""
    rs = resolve(
        legal=[STATUTE_BAN],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role=role,
        action="enter",
        zone_id="indoor",
        now=NOW,
        exceptions=list(exc_batch),
    )
    if rs.effect == "prohibited":
        assert any(r.effect == "prohibited" for r in rs.applicable_rules), (
            "prohibition without a prohibited source rule/exception"
        )
