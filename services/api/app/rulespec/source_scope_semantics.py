"""Source-scope semantic compatibility (WAVE01 pre-real-publish bridge, §4-§6).

The question this module answers
--------------------------------

A candidate records three things:

    source_scope_exact        what the source literally said  ("动物（导盲犬除外）")
    subject_scope_normalized  the scope we stored              ("other")
    normalization_type        whether those are equivalents    ("exact")

``exact`` is a *claim of equivalence*. Under ADR-025 only ``exact`` (and a
documented ``compound_term_split``) lets the stored scope stand in for the
source's legal effect. So when the source says "动物" and we store ``other``, the
row asserts that **"动物" and "other" name the same set of subjects**.

They do not. ``SCOPE_SUBJECTS['other'] == {other_pet}`` — one subject. "动物" is
every animal. Recording that pair as ``exact`` is a *narrowing* mislabelled as an
equivalence, and the consequence is not cosmetic: it silently releases every
non-pet animal from the rule, under a normalisation that claims to be faithful.

The defect family this closes
-----------------------------

The same class of error produced the ADR-025 defect itself (a 导盲犬 proviso
stored as the wider ``service_dog``). The direction differs — that one widened,
this one narrows — but the failure is identical: **a scope relationship the
source does not support, recorded as if the source supported it.**

How the reading is decided
--------------------------

``animal_scope.py`` can say what ``other`` covers. It cannot say whether "动物"
*means* that, because the platform has no machine-readable dictionary of Chinese
source terms, and inventing one would be precisely the "ontology as legal
argument" mistake ADR-025 forbids. So the meanings are **declared explicitly**,
the same construction ``COMPOUND_TERM_SPLIT_MEANINGS`` already uses, and the
check reads that declaration:

* ``SOURCE_TERM_READINGS`` — verbatim source terms whose documented meaning is
  an *equivalence*, a *narrowing*, a *broadening*, or *not legally readable*.
* A term not in the table is **undeclared**: it is reported as such and refused
  under ``exact`` (fail closed). That is the conservative direction — a new term
  must be read by a human before it can carry legal effect, and adding it to the
  table is a one-line, reviewable change.

Why fail-closed is the default for *undeclared* terms
-----------------------------------------------------

The alternative — treating an unknown term as equivalent because the reviewer
ticked ``exact`` — is exactly what let "动物（导盲犬除外）" ship as ``other``. The
claim is not evidence. So the table is the evidence, and the check must refuse
what it cannot read. The cost is that a genuinely new source term blocks until
declared; that cost is bounded, visible, and paid once, which is the right trade
against silently mis-scoping a published rule.

Note the asymmetry with ``rule_governs``: that function decides *which rules a
query sees*. This one decides *whether a normalisation is honest*. A rule can
pass this check and still be inert (its base may not govern its carve-out) — the
two questions are independent and both must be asked.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.enums import NormalizationType
from app.rulespec.animal_scope import SCOPE_SUBJECTS

__all__ = [
    "SemanticCompatibility",
    "SOURCE_TERM_READINGS",
    "classify_source_term_reading",
    "validate_source_scope_semantic_compatibility",
]

#: The follow-up state for a pair that claims equivalence without support.
#: Deliberately the *same* token the carve-out reachability gate uses: both mean
#: "the animal-scope model cannot express this source, and that is a human
#: decision" (see ``docs/governance/OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL.md``).
SEMANTIC_REMODEL_REQUIRED = "SEMANTIC_REMODEL_REQUIRED"

#: Declared readings of source terms the pilot actually met. Each entry states
#: what the term names, whether that is the stored scope, and what the stored
#: scope covers — so a reviewer audits the reading rather than re-deriving it.
#:
#: ``meaning`` is a frozenset of concrete subjects, or ``None`` when the term is
#: not legally readable (a colloquialism). ``equivalent_to`` names the scope the
#: term genuinely maps onto, or ``None`` when no single stored scope expresses it.
SOURCE_TERM_READINGS: dict[str, dict] = {
    # --- equivalences: the term names exactly the stored scope -----------------
    "犬只": {"equivalent_to": "dog", "note": "「犬只」即犬类，含全部犬类角色。"},
    "犬": {"equivalent_to": "dog", "note": "「犬」即犬类。"},
    "狗狗": {"equivalent_to": "dog", "note": "「狗狗」为犬只的口语表述，语义同 dog。"},
    "宠物": {"equivalent_to": "ordinary_pet", "note": "「宠物」即普通宠物（不含服务犬）。"},
    "携带宠物者": {"equivalent_to": "ordinary_pet", "note": "「携带宠物者」指携带普通宠物的人。"},
    "导盲犬": {"equivalent_to": "guide_dog", "note": "「导盲犬」精确指 guide_dog。"},
    # --- narrowings: the term is broader than the stored scope -----------------
    "动物": {
        "equivalent_to": None,
        "verdict": "narrowing",
        "reading": "「动物」指全部动物（全域），而 other 仅覆盖 {other_pet}（宠物一类）。",
        "note": "把全域归一为 other_pet 是收窄，不是等价。",
        # A declared decomposition exists (see broad_term_split): the fix is a
        # compound_term_split, not a re-reading of `other`.
        "remodel": "compound_term_split",
    },
    "动物（导盲犬除外）": {
        "equivalent_to": None,
        "verdict": "narrowing",
        "reading": "「动物（导盲犬除外）」= 全部动物减去导盲犬；基底仍是全域。",
        "note": "收窄，且内嵌但书未建模为 RuleException——双重缺陷。",
        "remodel": "compound_term_split",
    },
    # --- not legally readable --------------------------------------------------
    "毛孩子": {
        "equivalent_to": None,
        "verdict": "unreadable",
        "reading": "「毛孩子」是口语化宠物称谓，不构成法定主体表述。",
        "note": "无法律语义，不得标 exact。",
    },
    "毛孩子们": {
        "equivalent_to": None,
        "verdict": "unreadable",
        "reading": "「毛孩子们」是口语化宠物称谓，不构成法定主体表述。",
        "note": "无法律语义，不得标 exact。",
    },
    "除导盲犬等工作犬以外的其他宠物": {
        "equivalent_to": None,
        "verdict": "unreadable",
        "reading": "「除导盲犬等工作犬以外的其他宠物」含排除条款（但书），是复合否定表述。",
        "note": "复合否定表述无法直接归一到单一 scope；须拆为基底规则 + RuleException。",
    },
}

#: Normalisations that may confer legal effect (ADR-025).
_LEGAL_NORMALIZATIONS = frozenset(
    {
        NormalizationType.EXACT.value,
        NormalizationType.COMPOUND_TERM_SPLIT.value,
    }
)


@dataclass(frozen=True)
class SemanticCompatibility:
    """The verdict for one (source term, stored scope, normalisation) triple.

    ``compatible`` is the only field a gate may read, and it is ``True`` only
    for a *proven* equivalence. Everything else reports ``False`` with a
    ``reason`` so the caller can explain itself without re-deriving the
    judgement.
    """

    compatible: bool
    #: exact | narrowing | broadening | unreadable | undeclared | non_legal_type
    change: str
    reason: str
    #: what the source term is read to mean
    reading: str = ""
    #: the scope the term genuinely maps onto, when one is declared
    declared_equivalent: str | None = None
    #: the state a blocked row is recorded under
    follow_up: str = ""


def _declared_split_reading(source_scope_exact: str | None) -> str:
    from app.rulespec.broad_term_split import declared_split

    split = declared_split(source_scope_exact)
    return split.reading if split is not None else ""


def classify_source_term_reading(source_scope_exact: str | None) -> str:
    """The declared shape of a source term, without judging publishability.

    Kept separate so a report can say "this is a narrowing" before the legal
    question is answered — the shape of the error is useful on its own.
    """
    if not source_scope_exact:
        return "undeclared"
    entry = SOURCE_TERM_READINGS.get(source_scope_exact.strip())
    if entry is None:
        return "undeclared"
    if entry.get("equivalent_to"):
        return "exact"
    return str(entry.get("verdict") or "undeclared")


def validate_source_scope_semantic_compatibility(
    source_scope_exact: str | None,
    subject_scope_normalized: str | None,
    normalization_type: str | None,
) -> SemanticCompatibility:
    """May this row's normalisation confer legal effect? (§6)

    ``compatible=True`` requires **all** of:

    1. the declared normalisation is one that confers legal effect; and
    2. the source term has a declared reading; and
    3. that reading is the stored scope (an equivalence).

    Anything else is refused with a specific reason. The order matters: the
    normalisation is checked first so a row cannot pass by having a correct term
    reading while still carrying a non-legal ``legal_interpretation_required``.
    """
    if normalization_type not in _LEGAL_NORMALIZATIONS:
        non_legal_entry = SOURCE_TERM_READINGS.get((source_scope_exact or "").strip()) or {}
        return SemanticCompatibility(
            compatible=False,
            change="non_legal_type",
            reason=(
                f"normalization_type={normalization_type!r} 不具备法律效力，不得据此发布（ADR-025）"
            ),
            reading=non_legal_entry.get("reading", ""),
            declared_equivalent=non_legal_entry.get("equivalent_to"),
            follow_up=SEMANTIC_REMODEL_REQUIRED,
        )

    # A `compound_term_split` row is not claiming an equivalence at all — it is
    # claiming membership of a declared decomposition. Testing it against
    # SOURCE_TERM_READINGS would refuse every split (a split term has no
    # `equivalent_to` by construction), so it is answered by the split module.
    if normalization_type == NormalizationType.COMPOUND_TERM_SPLIT.value:
        from app.rulespec.broad_term_split import validate_split_row

        row = validate_split_row(source_scope_exact, subject_scope_normalized, normalization_type)
        return SemanticCompatibility(
            compatible=row.ok,
            change="compound_term_split" if row.ok else "split_not_declared",
            reason=row.reason,
            reading=(_declared_split_reading(source_scope_exact)),
            follow_up="" if row.ok else SEMANTIC_REMODEL_REQUIRED,
        )

    term = (source_scope_exact or "").strip()
    entry: dict[str, Any] = SOURCE_TERM_READINGS.get(term) or {}
    if not entry:
        return SemanticCompatibility(
            compatible=False,
            change="undeclared",
            reason=(
                f"来源术语「{source_scope_exact}」未在 SOURCE_TERM_READINGS 中声明语义——"
                "无法证明其与存储 scope 等价，fail closed，不得以 exact 发布。"
                "若确为等价，请以可复核的方式补充声明。"
            ),
            follow_up=SEMANTIC_REMODEL_REQUIRED,
        )

    equivalent_to = entry.get("equivalent_to")
    if equivalent_to:
        if equivalent_to == subject_scope_normalized:
            return SemanticCompatibility(
                compatible=True,
                change="exact",
                reason=f"来源术语「{term}」的声明语义即 {equivalent_to}，与存储 scope 一致。",
                reading=entry.get("note", ""),
                declared_equivalent=equivalent_to,
            )
        return SemanticCompatibility(
            compatible=False,
            change="interpretation",
            reason=(
                f"来源术语「{term}」的声明语义是 {equivalent_to}，"
                f"但本行存储为 {subject_scope_normalized!r}——两者不等价。"
            ),
            reading=entry.get("note", ""),
            declared_equivalent=equivalent_to,
            follow_up=SEMANTIC_REMODEL_REQUIRED,
        )

    verdict = str(entry.get("verdict") or "undeclared")
    return SemanticCompatibility(
        compatible=False,
        change=verdict,
        reason=(
            f"来源术语「{term}」{entry.get('reading', '')}"
            f"归一为 {subject_scope_normalized!r} 属于 {verdict}，"
            f"但被标为 {normalization_type!r}（声称等价）——{entry.get('note', '')}"
        ),
        reading=entry.get("reading", ""),
        follow_up=SEMANTIC_REMODEL_REQUIRED,
    )


def declared_scope_subjects(scope: str | None) -> frozenset[str] | None:
    """The subjects a stored scope covers — re-exported for the report layer.

    Thin passthrough so a caller building a human-readable explanation does not
    have to reach into two modules to say "other covers {other_pet}".
    """
    if scope is None:
        return None
    return SCOPE_SUBJECTS.get(scope)
