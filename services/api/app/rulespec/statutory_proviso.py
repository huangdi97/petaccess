"""Jurisdiction-level statutory provisos — the pure binding rule (ADR-030).

A statutory proviso (但书) such as 「盲人携带导盲犬的，不受本条规定的限制」 is a
property of the *instrument*, not of one venue. This module holds the one place
where "this proviso carves out of that base rule" is decided, so the resolver,
the publish gate and the tests cannot drift apart.

The binding is deliberately **declared, not inferred**: a proviso names the
``source`` rows that count as "the same instrument". The same statute can have
several source rows (a police-site reprint and the municipal portal full text)
and different venues cite different ones, so identity is an editorial
determination that must be reviewed — never a guess from URL similarity.

Every condition below is necessary. Failing one means the proviso does not
apply, and a rule that fails only the last one is reported as **inert** rather
than applied, because applying it would manufacture legal effect (ADR-025).
"""

from __future__ import annotations

from app.rulespec.animal_scope import legal_subjects, rule_governs

__all__ = [
    "BindingMode",
    "JURISDICTION_EXCEPTION_INERT",
    "proviso_subjects",
    "bind_proviso_to_bases",
]


class BindingMode:
    """How a carve-out finds the rule it carves out of."""

    #: the ordinary case: ``rule_id`` names the base rule (SG-REAL-01)
    RULE = "rule"
    #: ADR-030: any in-scope prohibition grounded in the same instrument
    INSTRUMENT = "instrument"


#: Recorded when a proviso names the right instrument and layer but the base
#: does not govern the proviso's subject — applying it would turn a base that is
#: *silent* about guide dogs into an explicit allowance.
JURISDICTION_EXCEPTION_INERT = "JURISDICTION_EXCEPTION_INERT"


def proviso_subjects(
    animal_scope: str | None,
    subject_scope_normalized: str | None,
    normalization_type: str | None,
) -> frozenset[str]:
    """The concrete subjects a proviso legally speaks about.

    Empty when the proviso's own scope was never established as a legal
    equivalent — a proviso that governs nothing binds nothing.
    """
    return legal_subjects(animal_scope, subject_scope_normalized, normalization_type) or frozenset()


def bind_proviso_to_bases(
    proviso,
    bases,
) -> tuple[list[str], list[str]]:
    """Split ``bases`` into (bound, inert) for one instrument-bound proviso.

    ``bound``  — base ids the proviso genuinely carves out of.
    ``inert``  — base ids that matched instrument + layer + effect but whose
                 scope does **not** govern the proviso's subject. Those are never
                 carved out; they are reported so the gap is visible.

    Nothing here is inferred from the instrument's text: ``instrument_source_ids``
    is the reviewed declaration of what counts as the same instrument.
    """
    bound: list[str] = []
    inert: list[str] = []

    if getattr(proviso, "binding", BindingMode.RULE) != BindingMode.INSTRUMENT:
        return bound, inert
    instrument_sources = frozenset(getattr(proviso, "instrument_source_ids", ()) or ())
    if not instrument_sources:
        return bound, inert
    target_layer = getattr(proviso, "applies_to_layer", None)
    if not target_layer:
        return bound, inert
    target_effects = frozenset(getattr(proviso, "applies_to_effects", ()) or ("prohibited",))
    subjects = proviso_subjects(
        getattr(proviso, "animal_scope", None),
        getattr(proviso, "subject_scope_normalized", None),
        getattr(proviso, "normalization_type", None),
    )
    if not subjects:
        return bound, inert

    for base in bases:
        if base.source_id not in instrument_sources:
            continue
        if base.rule_layer != target_layer:
            continue
        if base.effect not in target_effects:
            continue
        if rule_governs(
            subjects,
            base.animal_scope,
            base.subject_scope_normalized,
            base.normalization_type,
        ):
            bound.append(base.id)
        else:
            inert.append(base.id)
    return bound, inert
