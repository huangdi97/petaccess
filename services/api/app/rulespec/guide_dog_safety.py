"""Executable statutory guide-dog safety path (WAVE01 bridge, §10-§12).

Why this is a publish gate, not a nicety
----------------------------------------

``《上海市养犬管理条例》第二十三条`` prohibits dogs from entering malls, museums,
restaurants and similar venues, and then adds: 「盲人携带导盲犬的，不受本条规定的
限制。」 The proviso is part of the same statutory provision. A platform that
publishes the prohibition without the proviso tells a guide-dog handler
"prohibited" where the statute says otherwise — the platform would be *less*
accurate than the law it cites, and it would do so with a citation attached,
which is worse than saying nothing.

So: a LEGAL, dog-scoped, prohibiting rule may only ship when a same-layer
guide-dog exception **can actually fire in the resolver**. Not "the law contains
a proviso" — the *executable* path is what users experience.

What "executable" means here
----------------------------

The check does not read a document and reason about it. It builds real
``LayeredRule``/``LayeredException`` objects and calls the canonical
``v05_resolver.resolve`` for two queries:

* an ordinary dog must resolve ``prohibited`` (the base still works); and
* a guide dog must **not** resolve ``prohibited`` (the proviso applies).

Anything the resolver would refuse — an exception with no ``source_id``, a
non-``current`` status, a normalisation that confers no legal effect, a
same-layer mismatch — therefore fails here too, because it fails there. There is
no second scope algorithm and no second exception mechanism.

Accepted sources of the exception (§10)
---------------------------------------

A. a same-layer APPROVED/executable ``RuleException`` in this batch;
B. an already-``current`` published same-layer exception for the same venue; or
C. a jurisdiction-level legal exception the resolver actually applies.

C became reachable in Phase B (ADR-030): a statutory proviso is stored once as a
``JurisdictionException`` and binds by *instrument* — it claims every LEGAL
prohibition grounded in the same statute rather than one ``rule_id``. Path C is
still only ever *measured*: this module never creates or assumes a proviso, and
an unactivated one (``status != current`` or ``review_status != reviewed_active``)
simply does not fire.

The two rejected justifications are named in the code so they cannot creep back:
"the law ought to have one" and "users probably know" are not paths. Missing
exception ⇒ ``BASE_PUBLISHABLE = false`` with
``REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE``.

§12: this module **never mints** an exception. When one is missing it returns a
*proposal* with every human field empty, for a later human review.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.rulespec.statutory_proviso import BindingMode
from app.rulespec.v05_resolver import (
    LayeredException,
    LayeredRule,
    RuleLayer,
    resolve,
)

__all__ = [
    "GuideDogSafetyProbe",
    "GuideDogExceptionProposal",
    "probe_guide_dog_safety_path",
]

#: The state recorded when a base ships without an executable statutory exception.
REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE = "REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE"


@dataclass(frozen=True)
class GuideDogExceptionProposal:
    """A *proposed* exception for a missing statutory path (§12).

    Every human-owned field is left empty on purpose: ``final_decision``,
    ``reviewer``, ``decided_at``. This round may describe the gap; it may not
    fill it. The proposal is an input to a future human review, never a decision.
    """

    for_base_rule_id: str
    place_name: str
    source_scope_exact: str = "导盲犬"
    proposed_animal_scope: str = "service_dog"
    proposed_subject_scope_normalized: str = "guide_dog"
    proposed_normalization_type: str = "exact"
    proposed_normative_effect: str = "exempt_from_prohibition"
    proposed_rule_layer: str = RuleLayer.LEGAL.value
    proposed_holder_scope: str = "person_with_disability"
    reason: str = REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE
    # --- human-owned, deliberately empty -------------------------------------
    final_decision: str = ""
    reviewer: str = ""
    decided_at: str = ""


@dataclass
class GuideDogSafetyProbe:
    """The measured outcome of the two resolver queries."""

    base_rule_id: str
    place_name: str
    #: ordinary dog resolved to prohibited (the base still governs)
    ordinary_dog_prohibited: bool
    #: guide dog resolved to prohibited (must be False when a proviso exists)
    guide_dog_prohibited: bool
    #: how the guide-dog query resolved, for the report
    guide_dog_effect: str
    #: ids the resolver actually applied
    applied_exceptions: tuple[str, ...] = ()
    #: whether *any* executable same-layer exception was found
    exception_source: str = "none"  # batch | published | jurisdiction | none
    explanation: tuple[str, ...] = ()

    @property
    def has_executable_exception(self) -> bool:
        """The gate's question: is there a live statutory guide-dog path?

        Judged by the resolver's own output rather than by inspecting the
        exception list, so an exception that exists but is unreachable cannot
        count as a path.
        """
        return bool(self.applied_exceptions)

    @property
    def safe_to_publish(self) -> bool:
        """Base ships only if the ordinary dog is prohibited AND the guide dog is not."""
        return self.ordinary_dog_prohibited and not self.guide_dog_prohibited

    @property
    def block_reason(self) -> str:
        if self.safe_to_publish:
            return ""
        if not self.ordinary_dog_prohibited:
            return "BASE_DOES_NOT_GOVERN_ORDINARY_DOG"
        return REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE


def _base_layered(base: dict, *, zone_id: str | None = None) -> LayeredRule:
    return LayeredRule(
        id=str(base.get("rule_id") or base.get("id")),
        animal_scope=str(base.get("animal_scope")),
        action=str(base.get("action") or "enter"),
        effect=str(base.get("effect") or "prohibited"),
        rule_layer=base.get("rule_layer"),
        origin="place_override",
        zone_id=zone_id,
        source_id=base.get("source_id"),
        mandatory_level=base.get("mandatory_level"),
        subject_scope_normalized=base.get("subject_scope_normalized"),
        normalization_type=base.get("normalization_type"),
    )


def _exception_layered(exc: dict) -> LayeredException:
    return LayeredException(
        id=str(exc.get("rule_id") or exc.get("id")),
        rule_id=str(exc.get("base_rule_id") or exc.get("rule_id") or exc.get("id")),
        animal_scope=str(exc.get("animal_scope") or "service_dog"),
        effect=str(exc.get("effect") or "allowed"),
        source_id=exc.get("source_id"),
        status=str(exc.get("status") or "current"),
        conditions=tuple(exc.get("conditions") or ()),
        source_scope_exact=exc.get("source_scope_exact"),
        subject_scope_normalized=exc.get("subject_scope_normalized"),
        normalization_type=exc.get("normalization_type"),
        normative_effect=exc.get("normative_effect"),
        holder_scope=exc.get("holder_scope"),
        # ADR-030: a statutory proviso binds by instrument, not by rule_id.
        binding=str(exc.get("binding") or BindingMode.RULE),
        instrument_source_ids=tuple(exc.get("instrument_source_ids") or ()),
        applies_to_layer=exc.get("applies_to_layer"),
        applies_to_effects=tuple(exc.get("applies_to_effects") or ("prohibited",)),
    )


def _attaches_to(exc: dict, base_rule_id: str, base: dict) -> bool:
    """Does this carve-out claim this base rule?

    Two ways to claim a base, and only these two:
    * it names it (``base_rule_id`` / ``rule_id``) — the ordinary case; or
    * it is an instrument-bound statutory proviso (ADR-030) and the base is
      grounded in one of the sources it declares as that instrument.

    A carve-out written of *another* rule is not a path for this one, and a
    proviso for a different instrument is not either.
    """
    if str(exc.get("base_rule_id") or exc.get("rule_id") or "") == base_rule_id:
        return True
    if str(exc.get("binding") or BindingMode.RULE) != BindingMode.INSTRUMENT:
        return False
    return base.get("source_id") in set(exc.get("instrument_source_ids") or ())


def probe_guide_dog_safety_path(
    *,
    base: dict,
    candidate_exceptions: list[dict],
    published_exceptions: list[dict] | None = None,
    jurisdiction_exceptions: list[dict] | None = None,
    now: datetime | None = None,
) -> GuideDogSafetyProbe:
    """Run the two resolver queries for one LEGAL dog prohibition (§10-§11).

    ``candidate_exceptions`` / ``published_exceptions`` / ``jurisdiction_exceptions``
    are tried in that order of provenance (§10 A/B/C). The first provenance that
    yields a live path is recorded; if none does, the base is blocked. An
    exception is only ever attached to the base it names via ``base_rule_id`` —
    a carve-out written of another rule is not a path for this one.
    """
    now = now or datetime.now(UTC)
    base_rule_id = str(base.get("rule_id") or base.get("id"))
    zone_id = base.get("zone_id")

    base_rule = _base_layered(base, zone_id=zone_id)

    provenances = (
        ("batch", candidate_exceptions or []),
        ("published", published_exceptions or []),
        ("jurisdiction", jurisdiction_exceptions or []),
    )

    for label, rows in provenances:
        matched = [
            _exception_layered(e)
            for e in rows
            if _attaches_to(e, base_rule_id, base)
            and (e.get("rule_layer") or RuleLayer.LEGAL.value) == RuleLayer.LEGAL.value
        ]
        if not matched:
            continue

        # ordinary dog: the base must still prohibit
        ordinary = resolve(
            legal=[base_rule],
            guidance=[],
            template_rules=[],
            operator_rules=[],
            event_rules=[],
            animal="dog",
            service_role="none",
            action=str(base_rule.action),
            zone_id=zone_id,
            now=now,
            exceptions=matched,
        )
        # guide dog: the proviso must apply, so it must not resolve prohibited
        guide = resolve(
            legal=[base_rule],
            guidance=[],
            template_rules=[],
            operator_rules=[],
            event_rules=[],
            animal="dog",
            service_role="working",
            declared_role="guide_dog",
            action=str(base_rule.action),
            zone_id=zone_id,
            now=now,
            exceptions=matched,
        )
        probe = GuideDogSafetyProbe(
            base_rule_id=base_rule_id,
            place_name=str(base.get("place_name") or ""),
            ordinary_dog_prohibited=ordinary.effect == "prohibited",
            guide_dog_prohibited=guide.effect == "prohibited",
            guide_dog_effect=guide.effect,
            applied_exceptions=tuple(guide.applied_exceptions),
            exception_source=label if guide.applied_exceptions else "none",
            explanation=tuple(guide.explanation_steps),
        )
        if probe.has_executable_exception:
            return probe

    # nothing fired anywhere: measure the base alone so the report can still say
    # whether the base itself governs an ordinary dog.
    ordinary = resolve(
        legal=[base_rule],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role="none",
        action=str(base_rule.action),
        zone_id=zone_id,
        now=now,
    )
    guide = resolve(
        legal=[base_rule],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role="working",
        declared_role="guide_dog",
        action=str(base_rule.action),
        zone_id=zone_id,
        now=now,
    )
    return GuideDogSafetyProbe(
        base_rule_id=base_rule_id,
        place_name=str(base.get("place_name") or ""),
        ordinary_dog_prohibited=ordinary.effect == "prohibited",
        guide_dog_prohibited=guide.effect == "prohibited",
        guide_dog_effect=guide.effect,
        applied_exceptions=(),
        exception_source="none",
        explanation=tuple(guide.explanation_steps),
    )
