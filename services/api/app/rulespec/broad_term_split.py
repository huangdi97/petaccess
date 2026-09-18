"""Exhaustive decomposition of source terms too broad for one stored scope.

The defect this closes
----------------------

Two Wave01 rows record a source term that is *broader than any single scope the
platform can store*:

    source_scope_exact  "动物"                 (上海动物园)
    source_scope_exact  "动物（导盲犬除外）"   (上海迪士尼乐园)

Both were stored as ``other`` with ``normalization_type='exact'``.
``SCOPE_SUBJECTS['other'] == {other_pet}`` — one subject — so the row asserted
that "every animal" and "other pets" name the same set. They do not.

The consequence is not cosmetic and it is not symmetric with the ADR-025 defect.
ADR-025 *widened* a proviso; this *narrows* a prohibition, and a narrowed
prohibition does not merely answer wrongly, it **goes silent**: a dog query
against an ``other``-scoped base matches nothing and resolves ``unknown``. The
platform tells a dog owner "we found no rule" about a venue whose own notice
says no animals may enter. Silence is read as permission.

Why decomposition and not a new scope
-------------------------------------

The obvious alternative is to add an ``all_animals`` scope. It is rejected for
two reasons. First, "动物" covers animals the taxonomy does not model (a visitor
with a bird), so the new scope would only ever be an approximation wearing the
name of the thing it approximates — and under ADR-025 an approximation may not
be recorded as ``exact``. Second, a single all-animals base cannot express the
Disney wording at all, because that wording *already contains its own proviso*.

Decomposition fits the mechanism ADR-028 built for 军警犬: the source term is
split into disjoint platform atoms, each row keeps the verbatim
``source_scope_exact`` and records ``normalization_type='compound_term_split'``,
and the declared member set is auditable in code rather than in a spreadsheet.
``compound_term_split`` is already one of the two normalisations that confer
legal effect, so no new channel is invented.

「动物（导盲犬除外）」 is the interesting case
---------------------------------------------

Its base is the whole animal domain, which is exactly *why* the source needed to
write 「导盲犬除外」 in the first place: a proviso is only necessary when the base
it qualifies would otherwise cover the exempted subject. That gives textual
proof, internal to the source, that the base governs guide dogs.

So the faithful shape is three base atoms — ``dog``, ``cat``, ``other`` — plus a
``guide_dog`` carve-out hanging off the ``dog`` atom. Splitting without that
carve-out would publish the *opposite* of what the source says, so the proviso is
not optional here: ``requires_proviso`` makes the split refuse to validate
without it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.rulespec.animal_scope import SCOPE_SUBJECTS

__all__ = [
    "BroadTermSplit",
    "BROAD_TERM_SPLITS",
    "SplitRowVerdict",
    "SplitGroupVerdict",
    "declared_split",
    "split_subjects",
    "validate_split_row",
    "validate_split_group",
    "propose_split_rows",
]

#: Follow-up token, kept identical to the carve-out reachability gate and to
#: ``source_scope_semantics``: all three mean "the animal-scope model cannot
#: express this source, and choosing the shape is a human decision".
SEMANTIC_REMODEL_REQUIRED = "SEMANTIC_REMODEL_REQUIRED"


@dataclass(frozen=True)
class BroadTermSplit:
    """A source term whose meaning must be expressed as several scope atoms.

    ``members`` are stored-scope names, pairwise disjoint, whose union is the
    declared meaning. ``requires_proviso`` names subjects the source *itself*
    carves out from that union — the split is incomplete without them.
    """

    source_scope_exact: str
    members: tuple[str, ...]
    reading: str
    note: str = ""
    requires_proviso: tuple[str, ...] = field(default=())


BROAD_TERM_SPLITS: dict[str, BroadTermSplit] = {
    "动物": BroadTermSplit(
        source_scope_exact="动物",
        # dog covers every dog role (ordinary + all six working/assistance
        # roles); cat and other_pet are the remaining modelled pets. Together
        # they are the whole modelled animal domain, disjointly.
        members=("dog", "cat", "other"),
        reading="「动物」指全部动物；在平台主体词表内穷尽且互斥的拆分为 dog ∪ cat ∪ other。",
        note=(
            "拆分不是等价：动物含词表未建模的主体（如观赏鸟），"
            "故不得标 exact，只能按 compound_term_split 落在词表原子上。"
        ),
    ),
    "动物（导盲犬除外）": BroadTermSplit(
        source_scope_exact="动物（导盲犬除外）",
        members=("dog", "cat", "other"),
        reading=(
            "「动物（导盲犬除外）」= 全部动物减去导盲犬；基底同为全域，"
            "但来源已内嵌但书——正因基底覆盖导盲犬，才需要写「除外」。"
        ),
        note="拆分后必须由 guide_dog carve-out 挂在 dog 原子上，否则与来源原文相反。",
        requires_proviso=("guide_dog",),
    ),
    "动物（导盲犬等工作犬除外）": BroadTermSplit(
        source_scope_exact="动物（导盲犬等工作犬除外）",
        members=("dog", "cat", "other"),
        reading=(
            "「动物（导盲犬等工作犬除外）」= 全部动物减去工作犬；"
            "「等」字未穷举，须人工确认成员后再落地。"
        ),
        note="「等」为开放列举，未人工确认前不得发布（fail closed）。",
        requires_proviso=("guide_dog",),
    ),
}


def declared_split(source_scope_exact: str | None) -> BroadTermSplit | None:
    """The declared decomposition of a term, or ``None`` when undeclared.

    ``None`` must be read as "not proven", never as "no split needed" — the same
    fail-closed posture ``SOURCE_TERM_READINGS`` takes for undeclared terms.
    """
    if not source_scope_exact:
        return None
    return BROAD_TERM_SPLITS.get(source_scope_exact.strip())


def split_subjects(split: BroadTermSplit) -> frozenset[str]:
    """The concrete subjects a decomposition covers (union of its atoms)."""
    out: set[str] = set()
    for member in split.members:
        out |= SCOPE_SUBJECTS.get(member, frozenset())
    return frozenset(out)


@dataclass(frozen=True)
class SplitRowVerdict:
    """Whether *one* row is a legal member of a declared decomposition."""

    ok: bool
    reason: str = ""
    declared_members: tuple[str, ...] = ()
    follow_up: str = ""


@dataclass(frozen=True)
class SplitGroupVerdict:
    """Whether a *set* of rows expresses a declared decomposition completely."""

    ok: bool
    reason: str = ""
    missing_members: tuple[str, ...] = ()
    extra_members: tuple[str, ...] = ()
    missing_proviso: tuple[str, ...] = ()
    follow_up: str = ""


def validate_split_row(
    source_scope_exact: str | None,
    subject_scope_normalized: str | None,
    normalization_type: str | None,
) -> SplitRowVerdict:
    """May this single row stand as one member of a declared split?

    A row may only claim ``compound_term_split`` when the term has a declared
    decomposition and the stored scope is one of its members. This is the check
    ``source_scope_semantics`` delegates to: an equivalence test is the wrong
    question for a split row, and applying it would refuse every split.
    """
    from app.models.enums import NormalizationType

    term = (source_scope_exact or "").strip()
    split = declared_split(term)
    if split is None:
        return SplitRowVerdict(
            ok=False,
            reason=(
                f"来源术语「{source_scope_exact}」没有声明的拆分读法——"
                "不得以 compound_term_split 发布（未声明即拒）。"
            ),
            follow_up=SEMANTIC_REMODEL_REQUIRED,
        )

    if normalization_type != NormalizationType.COMPOUND_TERM_SPLIT.value:
        return SplitRowVerdict(
            ok=False,
            reason=(
                f"来源术语「{term}」只能按 compound_term_split 建模，"
                f"本行为 {normalization_type!r}。"
            ),
            declared_members=split.members,
            follow_up=SEMANTIC_REMODEL_REQUIRED,
        )

    if subject_scope_normalized not in split.members:
        return SplitRowVerdict(
            ok=False,
            reason=(
                f"来源术语「{term}」的声明拆分成员为 {list(split.members)}，"
                f"本行存储为 {subject_scope_normalized!r}——不是其成员。"
            ),
            declared_members=split.members,
            follow_up=SEMANTIC_REMODEL_REQUIRED,
        )

    return SplitRowVerdict(
        ok=True,
        reason=f"来源术语「{term}」的声明拆分成员之一：{subject_scope_normalized}。",
        declared_members=split.members,
    )


def validate_split_group(
    source_scope_exact: str | None,
    member_scopes: tuple[str, ...] | list[str] | set[str],
    carve_out_subjects: tuple[str, ...] | list[str] | set[str] = (),
) -> SplitGroupVerdict:
    """Is a decomposition *complete* — exhaustive, and with its proviso?

    Per-row membership is not enough. A split that omits an atom silently drops
    part of the source's meaning, and a split whose source carries an inline
    proviso but ships without the carve-out states the opposite of the source.
    """
    term = (source_scope_exact or "").strip()
    split = declared_split(term)
    if split is None:
        return SplitGroupVerdict(
            ok=False,
            reason=f"来源术语「{source_scope_exact}」没有声明的拆分读法。",
            follow_up=SEMANTIC_REMODEL_REQUIRED,
        )

    have = set(member_scopes)
    want = set(split.members)
    missing = tuple(sorted(want - have))
    extra = tuple(sorted(have - want))
    proviso = set(split.requires_proviso) - set(carve_out_subjects)
    missing_proviso = tuple(sorted(proviso))

    if missing or extra:
        return SplitGroupVerdict(
            ok=False,
            reason=(
                f"来源术语「{term}」的拆分不完整：缺 {list(missing)}，多 {list(extra)}。"
                "缺成员会静默丢掉一部分来源语义。"
            ),
            missing_members=missing,
            extra_members=extra,
            missing_proviso=missing_proviso,
            follow_up=SEMANTIC_REMODEL_REQUIRED,
        )

    if missing_proviso:
        return SplitGroupVerdict(
            ok=False,
            reason=(
                f"来源术语「{term}」内嵌但书，声明要求 carve-out 覆盖 "
                f"{list(split.requires_proviso)}；"
                f"当前缺 {list(missing_proviso)}。"
                "没有该 carve-out，拆分后的基底会禁止来源明确豁免的主体，与原文相反。"
            ),
            missing_members=missing,
            extra_members=extra,
            missing_proviso=missing_proviso,
            follow_up=SEMANTIC_REMODEL_REQUIRED,
        )

    return SplitGroupVerdict(
        ok=True,
        reason=(
            f"来源术语「{term}」的拆分完整：{list(split.members)}"
            + (
                f"，且内嵌但书已由 carve-out {list(split.requires_proviso)} 覆盖。"
                if split.requires_proviso
                else "。"
            )
        ),
    )


def propose_split_rows(source_scope_exact: str) -> list[dict[str, str]]:
    """The row specs a declared decomposition asks for.

    Returns an empty list for an undeclared term: proposing nothing is the only
    safe proposal. Callers must not fall back to "keep the current single row".
    """
    split = declared_split(source_scope_exact)
    if split is None:
        return []
    return [
        {
            "source_scope_exact": split.source_scope_exact,
            "subject_scope_normalized": member,
            "normalization_type": "compound_term_split",
        }
        for member in split.members
    ]
