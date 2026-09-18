"""Animal-role taxonomy and source-faithful scope matching (ADR-025).

The defect this module exists to prevent
----------------------------------------

``《上海市养犬管理条例》第二十三条`` prohibits dogs from entering malls, with a
proviso: 「盲人携带导盲犬的，不受本条规定的限制。」 The proviso names **导盲犬**
(guide dog) and nothing wider.

The previous model stored that proviso as ``animal_scope='service_dog'``, on the
reasoning that GUIDE_DOG *is-a* SERVICE_DOG. The stored row then claimed that
*every* service dog — hearing, assistance, other — is exempt from the statutory
prohibition. That is an ontology relationship being used as a legal argument.
It is wrong: ontology is a **query** convenience, never a source of legal scope.

Two ideas keep this honest:

* ``source_scope_exact`` / ``subject_scope_normalized`` / ``normalization_type``
  record what the source said, what we stored, and whether those two are legal
  equivalents. Only ``exact`` may confer legal effect.
* Query expansion (``service_dog`` → the four assistance roles) happens on the
  **query** side only. It decides which rules we *look at*; it never widens what
  a rule *means*.

Everything is modelled as a set of concrete *subjects* so that semantic scopes
(``dog``, ``ordinary_pet``) and precise roles (``guide_dog``) are comparable
without special cases.

The invariant, stated for tests:

    ONTOLOGY_PARENT_RELATIONSHIP MUST_NOT IMPLY_LEGAL_SCOPE_EXPANSION
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import (
    LEGAL_NORMALIZATION_TYPES,
    AnimalRole,
    HolderScope,
    NormalizationType,
)

#: subjects outside the dog taxonomy (a cat is not a dog, and vice versa)
ORDINARY_CAT = "ordinary_cat"
OTHER_PET = "other_pet"

#: every concrete dog role — what the bare scope ``dog`` legally covers
DOG_ROLES: frozenset[str] = frozenset(r.value for r in AnimalRole)

#: what the semantic scope ``ordinary_pet`` covers: pets generally, service
#: dogs excluded (their access rights are governed separately)
ORDINARY_PET_SUBJECTS: frozenset[str] = frozenset(
    {AnimalRole.ORDINARY_DOG.value, ORDINARY_CAT, OTHER_PET}
)

#: roles a "service dog" *query* expands to. POLICE_DOG and
#: MILITARY_WORKING_DOG are deliberately absent — they are working dogs, not
#: assistance dogs, and must never be folded into this group.
SERVICE_DOG_QUERY_ROLES: frozenset[str] = frozenset(
    {
        AnimalRole.GUIDE_DOG.value,
        AnimalRole.HEARING_DOG.value,
        AnimalRole.ASSISTANCE_DOG.value,
        AnimalRole.OTHER_SERVICE_DOG.value,
    }
)

#: precise roles that are NOT service dogs
NON_SERVICE_ROLES: frozenset[str] = frozenset(
    {
        AnimalRole.ORDINARY_DOG.value,
        AnimalRole.POLICE_DOG.value,
        AnimalRole.MILITARY_WORKING_DOG.value,
    }
)

DOG_PARENT_SCOPE = "dog"
ORDINARY_PET_SCOPE = "ordinary_pet"
#: The assistance-dog category **as a scope the source itself may name**.
#: It is legal only when the source literally speaks of service dogs as a group
#: (e.g. 《无障碍环境建设法》第46条 mentions 导盲犬、助听犬 and assistance dogs
#: together) and a reviewer records ``normalization_type='exact'``. It is *never*
#: the legal meaning of a 导盲犬 proviso — that case is ``GUIDE_DOG``.
SERVICE_DOG_SCOPE = "service_dog"

#: scope name → the concrete subjects it legally covers
SCOPE_SUBJECTS: dict[str, frozenset[str]] = {
    DOG_PARENT_SCOPE: DOG_ROLES,
    ORDINARY_PET_SCOPE: ORDINARY_PET_SUBJECTS,
    SERVICE_DOG_SCOPE: SERVICE_DOG_QUERY_ROLES,
    "cat": frozenset({ORDINARY_CAT}),
    "other": frozenset({OTHER_PET}),
    **{role: frozenset({role}) for role in DOG_ROLES},
}

#: scopes that may only ever confer legal effect when a reviewer declared the
#: normalisation ``exact``. ``service_dog`` is here because storing it *without*
#: that declaration is precisely the ADR-025 defect: a guide-dog proviso widened
#: to the whole assistance category.
_EXACT_ONLY_SCOPES: frozenset[str] = frozenset({SERVICE_DOG_SCOPE})

#: normalisations that do NOT authorise a rule to confer legal effect
_NON_LEGAL_NORMALISATIONS = frozenset(
    {
        NormalizationType.LEGAL_INTERPRETATION_REQUIRED.value,
        NormalizationType.PARENT_GROUP_FOR_QUERY_ONLY.value,
    }
)


def normalization_confers_legal_effect(normalization_type: str | None) -> bool:
    """Whether a recorded normalisation is a faithful reading of the source.

    Membership is checked against the closed ``LEGAL_NORMALIZATION_TYPES`` set
    rather than by excluding the non-legal ones, so a newly added type can never
    become legal by accident.
    """
    return normalization_type in LEGAL_NORMALIZATION_TYPES


def compound_split_is_exhaustive(
    source_scope_exact: str, split_roles: frozenset[str] | set[str]
) -> bool:
    """Guard for ``COMPOUND_TERM_SPLIT`` rows (ADR-028).

    A compound source term may only be split when the members cover the term
    exactly: no member outside the term's documented meaning, and none missing.
    The platform has no machine-readable dictionary of Chinese compound animal
    terms, so the *meaning* is declared here explicitly and the guard checks the
    declared members are precisely that set — never a superset.
    """
    declared = COMPOUND_TERM_SPLIT_MEANINGS.get(source_scope_exact)
    if declared is None:
        return False
    return frozenset(split_roles) == declared


#: Documented meanings of compound source terms the pilot actually encountered.
#: This is a *reading of the source wording*, kept in code so the split is
#: auditable and testable rather than living only in a review spreadsheet.
COMPOUND_TERM_SPLIT_MEANINGS: dict[str, frozenset[str]] = {
    # 军警犬 = 军用犬 + 警用犬 (military working dogs + police dogs). It does NOT
    # include guide/hearing/assistance/other service dogs.
    "军警犬": frozenset({AnimalRole.POLICE_DOG.value, AnimalRole.MILITARY_WORKING_DOG.value}),
    "军警用犬": frozenset({AnimalRole.POLICE_DOG.value, AnimalRole.MILITARY_WORKING_DOG.value}),
}


@dataclass(frozen=True)
class QuerySubject:
    """What the user is asking about.

    ``declared_role`` is optional: a user who knows their dog is a guide dog can
    say so; otherwise the coarser ``service_role`` expands to the service-dog
    group. Either way the expansion is query-side only.
    """

    species: str
    service_role: str = "none"
    declared_role: str | None = None


def query_subjects(subject: QuerySubject) -> frozenset[str]:
    """The concrete subjects this query is about (query-side expansion only).

    ``declared_role`` wins when present: a user who says "my dog is a hearing
    dog" is asking a task-specific question and must not inherit a guide-dog
    proviso. Without it, a service-dog query expands to the whole assistance
    group so correctly-modelled rules can still be found.
    """
    if subject.declared_role:
        return frozenset({subject.declared_role})
    if subject.species == "cat":
        return frozenset({ORDINARY_CAT})
    if subject.species == "other":
        return frozenset({OTHER_PET})
    if subject.species != "dog":
        return frozenset()
    if subject.service_role in ("working", "in_training"):
        return SERVICE_DOG_QUERY_ROLES
    return frozenset({AnimalRole.ORDINARY_DOG.value})


def legal_subjects(
    animal_scope: str | None,
    subject_scope_normalized: str | None,
    normalization_type: str | None,
) -> frozenset[str] | None:
    """The concrete subjects a rule may **legally** speak about.

    Returns ``None`` when the rule cannot confer legal effect at all — because
    its scope was never established as a legal equivalent, or because the stored
    scope is explicitly a query-only parent group. Callers must read ``None`` as
    "this rule does not govern", never as "governs everything".
    """
    if normalization_type in _NON_LEGAL_NORMALISATIONS:
        return None

    scope = subject_scope_normalized
    if scope is None:
        # Legacy row with no recorded normalisation. Be conservative: a
        # `service_dog` scope is exactly the unproven widening, so it confers
        # nothing until reviewed.
        scope = animal_scope if animal_scope in ("dog", "ordinary_pet") else None
        if scope is None:
            return None
    elif scope in _EXACT_ONLY_SCOPES and not normalization_confers_legal_effect(normalization_type):
        # `service_dog` only carries legal effect when a reviewer declared a
        # *legal* normalisation (exact, or a documented compound-term split).
        # Anything else is the ADR-025 widening.
        return None
    return SCOPE_SUBJECTS.get(scope)


def rule_governs(
    query: frozenset[str],
    animal_scope: str | None,
    subject_scope_normalized: str | None,
    normalization_type: str | None,
) -> bool:
    """Does a rule with this recorded scope govern a query about ``query`` subjects?

    Existential on purpose: a statute written of 「犬」 governs a question about
    *any* dog, including one the asker has not narrowed down yet.
    """
    if not query:
        return False
    scope = legal_subjects(animal_scope, subject_scope_normalized, normalization_type)
    if scope is None:
        return False
    return bool(query & scope)


def carve_out_covers(
    query: frozenset[str],
    animal_scope: str | None,
    subject_scope_normalized: str | None,
    normalization_type: str | None,
) -> bool:
    """Does a carve-out answer this query *completely*? (ADR-031)

    The dual of :func:`rule_governs`, and deliberately stricter. A prohibition
    written of 「犬」 may govern an underspecified service-dog question, but an
    exemption written of 「导盲犬」 may not: it covers one of the four roles the
    question could be about, so applying it would answer a question the source
    never answered.

    That is the *existence semantics* defect: "some child of the parent scope
    hits an exception, therefore the parent query is allowed". Under this
    predicate a carve-out fires only when every subject the query might denote
    is inside it — ``query ⊆ carve-out`` — so a group query never inherits the
    allowance of one of its members.
    """
    if not query:
        return False
    scope = legal_subjects(animal_scope, subject_scope_normalized, normalization_type)
    if scope is None:
        return False
    return query <= scope


def parent_expansion_is_legal(source_scope: str, stored_scope: str) -> bool:
    """Guard used by tests and the ingest pipeline.

    Widening a narrow source scope into a broader stored scope is only legal
    when the two are the *same* scope. Anything else is an ontology inference,
    which is not a legal argument.
    """
    return source_scope == stored_scope


def holder_scope_allows(rule_holder_scope: str | None, is_person_with_disability: bool) -> bool:
    """《无障碍环境建设法》第46条 applies to persons with disabilities.

    A rule that names ``person_with_disability`` does not silently extend to any
    handler; a rule that names ``any_handler`` (or names nothing) is unaffected.

    This is the *boolean* form, kept for the duty-side tests: the caller always
    supplies a truth value, so "unknown" cannot arise. The resolver uses the
    four-state :func:`app.rulespec.holder_scope.evaluate_holder` instead — one
    implementation, two shapes.
    """
    from app.rulespec.holder_scope import HolderContext, HolderMatch, evaluate_holder

    context = (
        HolderContext.of(HolderScope.PERSON_WITH_DISABILITY.value)
        if is_person_with_disability
        else HolderContext.of()
    )
    return evaluate_holder(rule_holder_scope, context) != HolderMatch.DOES_NOT_MATCH
