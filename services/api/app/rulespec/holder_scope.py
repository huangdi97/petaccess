"""Holder (携犬人) conditions on a carve-out — the missing half of a proviso.

Why this module exists
----------------------

《上海市养犬管理条例》第二十三条的但书 is not "guide dogs may enter". It is
「盲人携带导盲犬的，不受本条规定的限制」 — *a blind person leading a guide dog*.
The holder is part of the norm, not a footnote. Before this module the row
carried ``holder_scope='person_with_disability'`` and the resolver never read
it, so the answer to "may I bring a guide dog?" was an unconditional ``allowed``
for **any** handler. That is a carve-out wider than its source, which ADR-025
forbids for subjects; ADR-031 extends the same rule to holders.

The privacy boundary is the other half of the design
----------------------------------------------------

Whether someone is a person with a disability is a sensitive attribute. The
platform therefore never persists it: ``HolderContext`` is **ephemeral and
query-time only** — it is supplied by the caller, evaluated, and dropped. There
is no column for it, no ``PetProfile`` field, and no default. A missing context
is a first-class state (``HolderMatch.UNKNOWN``), never silently coerced to
"no", because coercing it would answer ``prohibited`` to a handler the statute
exempts.

Failure semantics, stated for tests
-----------------------------------

    subject matches AND holder matches AND jurisdiction matches
        AND provision matches AND time valid  →  carve-out applies

    holder unknown  →  the carve-out is WITHHELD, not applied, and the answer
                       becomes CONDITIONAL with missing context — never an
                       unconditional ALLOWED and never a bare PROHIBITED.

An unconditional ALLOWED with an unevaluated holder condition would be the very
widening this module exists to prevent; a bare PROHIBITED would hide a
statutory right behind a missing input.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.models.enums import HolderScope

__all__ = [
    "MISSING_CONTEXT_HOLDER_SCOPE",
    "MISSING_CONTEXT_SERVICE_ROLE",
    "HolderContext",
    "HolderMatch",
    "evaluate_holder",
    "holder_condition_required",
]

#: ``missing_inputs`` token for "the holder condition could not be evaluated".
MISSING_CONTEXT_HOLDER_SCOPE = "holder_scope"

#: ``missing_inputs`` token for "the query named a group, not a role".
MISSING_CONTEXT_SERVICE_ROLE = "service_role"


class HolderMatch(StrEnum):
    """The four outcomes of evaluating an exception's holder condition."""

    #: the norm names no holder restriction — it applies to any handler
    NOT_REQUIRED = "not_required"
    #: a holder restriction was named and the supplied context satisfies it
    MATCHES = "matches"
    #: a holder restriction was named and the supplied context does not
    DOES_NOT_MATCH = "does_not_match"
    #: a holder restriction was named and no context was supplied at all
    UNKNOWN = "unknown"


#: Holder scopes that impose **no** restriction on who the handler is.
#: ``None`` is a legacy row that never recorded a holder condition — it is not
#: evidence that the source imposes none, but it is also not something we may
#: *tighten* retroactively, so it is treated as unrestricted until re-reviewed.
UNRESTRICTED_HOLDER_SCOPES: frozenset[str | None] = frozenset(
    {None, "", HolderScope.ANY_HANDLER.value}
)


@dataclass(frozen=True)
class HolderContext:
    """Ephemeral, query-time statement about who is handling the animal.

    ``scopes`` enumerates the statutory holder statuses the caller states the
    handler holds. ``None`` means *nothing was supplied*, which is deliberately
    distinct from "supplied and empty": the first is ``UNKNOWN`` and yields a
    conditional answer, the second is a known non-match.

    Nothing here is persisted. There is no table, no column and no profile
    field for disability status — adding one would be a separate privacy
    decision with its own authorisation (ADR-031 §4).
    """

    scopes: frozenset[str] | None = None

    @classmethod
    def unknown(cls) -> HolderContext:
        """No holder context supplied (the default for every public query)."""
        return cls(scopes=None)

    @classmethod
    def of(cls, *scopes: str) -> HolderContext:
        """A supplied context — possibly empty, i.e. a known non-match."""
        return cls(scopes=frozenset(scopes))

    @property
    def supplied(self) -> bool:
        return self.scopes is not None


def holder_condition_required(rule_holder_scope: str | None) -> bool:
    """Whether this norm actually restricts who may invoke it."""
    return rule_holder_scope not in UNRESTRICTED_HOLDER_SCOPES


def evaluate_holder(
    rule_holder_scope: str | None,
    context: HolderContext | None,
) -> HolderMatch:
    """Evaluate one carve-out's holder condition against a query-time context.

    The rule's own ``holder_scope`` is the only source of the restriction: a
    norm that names none applies to any handler, so an OPERATOR_POLICY that
    genuinely says 「导盲犬可以进入」 without a holder clause is *not* polluted
    by the statute's stricter wording (ADR-031 §14). Layers stay independent.
    """
    if not holder_condition_required(rule_holder_scope):
        return HolderMatch.NOT_REQUIRED
    if context is None or not context.supplied:
        # A restriction exists and we were told nothing about the handler.
        # Refusing to guess is the whole point: neither allow nor prohibit.
        return HolderMatch.UNKNOWN
    assert context.scopes is not None
    return (
        HolderMatch.MATCHES if rule_holder_scope in context.scopes else HolderMatch.DOES_NOT_MATCH
    )
