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
)


def _resolve(rules, *, animal="dog", service_role="none", exceptions=(), zone_id="indoor", now=NOW):
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
    )


# ------------------------------------------------------------- deterministic


def test_ordinary_dog_still_restricted():
    rs = _resolve([STATUTE_BAN], animal="dog", service_role="none", exceptions=[GUIDE_EXEMPTION])
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


def test_service_dog_exempt_via_exception():
    rs = _resolve([STATUTE_BAN], animal="dog", service_role="working", exceptions=[GUIDE_EXEMPTION])
    assert rs.effect == "allowed"
    assert rs.applied_exceptions == ["exc-butie"]
    assert any("exempted by exception" in reason for _, reason in rs.suppressed_rules)


def test_expired_exception_falls_back_to_base():
    expired = LayeredException(
        id="exc-old",
        rule_id="legal-dog-ban",
        animal_scope="service_dog",
        effect="allowed",
        source_id="src-statute",
        effective_to=NOW - timedelta(days=1),
    )
    rs = _resolve([STATUTE_BAN], animal="dog", service_role="working", exceptions=[expired])
    assert rs.effect == "prohibited"
    assert rs.applied_exceptions == []


def test_future_exception_not_yet_effective():
    future = LayeredException(
        id="exc-future",
        rule_id="legal-dog-ban",
        animal_scope="service_dog",
        effect="allowed",
        source_id="src-statute",
        effective_from=NOW + timedelta(days=1),
    )
    rs = _resolve([STATUTE_BAN], animal="dog", service_role="working", exceptions=[future])
    assert rs.effect == "prohibited"


def test_withdrawn_and_superseded_exceptions_never_apply():
    for status in ("withdrawn", "superseded", "archived"):
        exc = LayeredException(
            id="exc-dead",
            rule_id="legal-dog-ban",
            animal_scope="service_dog",
            effect="allowed",
            source_id="src-statute",
            status=status,
        )
        rs = _resolve([STATUTE_BAN], animal="dog", service_role="working", exceptions=[exc])
        assert rs.effect == "prohibited", status


def test_exception_without_source_never_applies():
    exc = LayeredException(
        id="exc-nosrc",
        rule_id="legal-dog-ban",
        animal_scope="service_dog",
        effect="allowed",
        source_id=None,
    )
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
    contradict = LayeredException(
        id="exc-no",
        rule_id="legal-dog-ban",
        animal_scope="service_dog",
        effect="prohibited",
        source_id="src-other",
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
    conditional = LayeredException(
        id="exc-cond",
        rule_id="legal-dog-ban",
        animal_scope="service_dog",
        effect="conditional",
        source_id="src-statute",
        conditions=({"condition_type": "leash_required", "value_flag": True},),
    )
    rs = _resolve([STATUTE_BAN], animal="dog", service_role="working", exceptions=[conditional])
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
    # Core invariant: every APPLIED exception must be sourced, active, and its
    # scope must match the query — anything else applying is a leak.
    # Additionally a service_dog-scoped exception must never apply to a
    # non-working-like query (must not widen to ordinary pets).

    def scope_matches(e, sp, rl):
        # mirror evaluator scope semantics for the probe
        if e.animal_scope == "service_dog":
            return rl in ("working", "in_training", "unknown") and sp == "dog"
        if e.animal_scope == "ordinary_pet":
            if rl in ("working", "in_training"):
                return False
            return sp in ("dog", "cat", "other")
        if e.animal_scope == "dog":
            return sp == "dog"
        if e.animal_scope == "cat":
            return sp == "cat"
        return True  # other

    for exc_id in rs.applied_exceptions:
        matching = [
            e
            for e in exc_batch
            if e.id == exc_id
            and e.source_id
            and e.status == "current"
            and scope_matches(e, species, role)
        ]
        assert matching, f"exception {exc_id} applied without source/activity/scope match"

    # a service_dog-scoped exception must never apply to a query that is
    # explicitly NOT working (role=none). role=unknown applies by design
    # (conservative: the evaluator treats unknown as potentially working).
    if not (species == "dog" and role in ("working", "in_training", "unknown")):
        service_scoped = {e.id for e in exc_batch if e.animal_scope == "service_dog"}
        assert service_scoped.isdisjoint(set(rs.applied_exceptions))


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
