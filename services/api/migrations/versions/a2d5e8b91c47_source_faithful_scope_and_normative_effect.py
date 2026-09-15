"""source-faithful scope + normative effect layer (ADR-025)

Revision ID: a2d5e8b91c47
Revises: f4c9d2e7a831
Create Date: 2026-09-15

Two modelling defects found while reviewing the R1 packet:

1. **Ontology was treated as law.** ADR-020 §4 said "guide dog = service_dog +
   service_role=working", so every 导盲犬 proviso in 《上海市养犬管理条例》第23条
   was ingested as ``animal_scope='service_dog'``. The statute says 导盲犬 and
   nothing wider; the stored row nevertheless claimed *all* service dogs are
   allowed. Ontology (GUIDE_DOG is-a SERVICE_DOG) is a query convenience and must
   never widen a source-specific legal effect.

2. **Effect vocabulary was too coarse.** ``allowed/prohibited/conditional`` cannot
   express "this carve-out removes the base prohibition for a narrow subject"
   (但书/豁免) nor "the venue must actively accommodate" (《无障碍环境建设法》
   第46条「提供便利」). Folding a duty into ``allowed`` inflates it into an
   unconditional permission.

This migration adds the storage for both, additively:

  * ``source_scope_exact``          — what the source literally names
  * ``subject_scope_normalized``    — the precise role the rule governs
  * ``normalization_type``          — exact | parent_group_for_query_only |
                                      legal_interpretation_required
  * ``normative_effect``            — permission | prohibition |
                                      conditional_permission |
                                      exempt_from_prohibition | facilitation_required
  * ``holder_scope``                — any_handler | person_with_disability
  * ``operator_obligations``        — positive duties the venue owes (JSON list)
  * ``jurisdiction_code`` / ``applies_to_place_types`` / ``projection_of_rule_id``
    — a jurisdiction-level rule is stored **once**; per-place rows are projections

``needs_owner`` is relaxed so a jurisdiction rule (no place, no zone) is legal.

Backfill is conservative and **never widens a scope**:

  * ``dog``          → ``dog`` (exact: the source said 犬只)
  * ``ordinary_pet`` → ``ordinary_pet`` (exact: the semantic scope is preserved)
  * ``service_dog``  → **NULL** + ``legal_interpretation_required``, because the
    stored scope is precisely the unproven widening. Those rows are held for
    scope re-modelling rather than silently reinterpreted here.
  * ``normative_effect`` is only derived from ``effect`` where the normalisation
    is exact — otherwise the value would encode the very inference under review.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a2d5e8b91c47"
down_revision: str | None = "f4c9d2e7a831"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: columns every rule-shaped row carries (rule, candidate, exception)
_SCOPE_COLUMNS = [
    ("source_scope_exact", sa.String(length=64)),
    ("subject_scope_normalized", sa.String(length=32)),
    ("normalization_type", sa.String(length=32)),
    ("normative_effect", sa.String(length=32)),
    ("holder_scope", sa.String(length=32)),
]

#: rule + candidate only
_OBLIGATION_COLUMN = ("operator_obligations", sa.JSON())

#: rule + candidate only — provenance link to the jurisdiction rule
_PROJECTION_COLUMN = ("projection_of_rule_id", sa.String(length=36))

#: jurisdiction-level rules only
_JURISDICTION_COLUMNS = [
    ("jurisdiction_code", sa.String(length=16)),
    ("applies_to_place_types", sa.JSON()),
]

_TABLE_COLUMNS = {
    "access_rule": [
        *_SCOPE_COLUMNS,
        _OBLIGATION_COLUMN,
        _PROJECTION_COLUMN,
        *_JURISDICTION_COLUMNS,
    ],
    "rule_candidate": [*_SCOPE_COLUMNS, _OBLIGATION_COLUMN, _PROJECTION_COLUMN],
    "rule_exception": _SCOPE_COLUMNS,
}

#: never widens: only scopes the source actually named
_BACKFILL_SCOPE = sa.text(
    """
    UPDATE {table}
       SET source_scope_exact = COALESCE(source_scope_exact, animal_scope),
           subject_scope_normalized = CASE animal_scope
             WHEN 'dog' THEN 'dog'
             WHEN 'ordinary_pet' THEN 'ordinary_pet'
             ELSE NULL
           END,
           normalization_type = CASE animal_scope
             WHEN 'dog' THEN 'exact'
             WHEN 'ordinary_pet' THEN 'exact'
             WHEN 'service_dog' THEN 'legal_interpretation_required'
             ELSE normalization_type
           END
     WHERE subject_scope_normalized IS NULL
    """
)

#: only where the normalisation is exact — otherwise it would encode the
#: inference under review
_BACKFILL_NORMATIVE = sa.text(
    """
    UPDATE {table}
       SET normative_effect = CASE effect
             WHEN 'prohibited' THEN 'prohibition'
             WHEN 'allowed' THEN 'permission'
             WHEN 'conditional' THEN 'conditional_permission'
             ELSE NULL
           END
     WHERE normative_effect IS NULL
       AND normalization_type = 'exact'
    """
)

_NORMALIZATION_CHECK = (
    "normalization_type IS NULL OR normalization_type IN "
    "('exact','parent_group_for_query_only','legal_interpretation_required')"
)
_NORMATIVE_CHECK = (
    "normative_effect IS NULL OR normative_effect IN "
    "('permission','prohibition','conditional_permission',"
    "'exempt_from_prohibition','facilitation_required')"
)


def upgrade() -> None:
    for table, columns in _TABLE_COLUMNS.items():
        for name, coltype in columns:
            op.add_column(table, sa.Column(name, coltype, nullable=True))
        op.execute(_BACKFILL_SCOPE.text.format(table=table))
        op.execute(_BACKFILL_NORMATIVE.text.format(table=table))

    # a jurisdiction rule has neither place nor zone; relax the ownership check
    op.drop_constraint(op.f("ck_access_rule_needs_owner"), "access_rule", type_="check")
    op.create_check_constraint(
        op.f("ck_access_rule_needs_owner"),
        "access_rule",
        "(place_id IS NOT NULL) OR (zone_id IS NOT NULL) OR (jurisdiction_code IS NOT NULL)",
    )

    for table in ("access_rule", "rule_exception"):
        op.create_check_constraint(
            op.f(f"ck_{table}_normalization_type"), table, _NORMALIZATION_CHECK
        )
        op.create_check_constraint(op.f(f"ck_{table}_normative_effect"), table, _NORMATIVE_CHECK)
    op.create_check_constraint(
        op.f("ck_access_rule_holder_scope"),
        "access_rule",
        "holder_scope IS NULL OR holder_scope IN ('any_handler','person_with_disability')",
    )
    op.create_index("ix_access_rule_jurisdiction", "access_rule", ["jurisdiction_code", "status"])


def downgrade() -> None:
    op.drop_index("ix_access_rule_jurisdiction", table_name="access_rule")
    op.drop_constraint(op.f("ck_access_rule_holder_scope"), "access_rule", type_="check")
    for table in ("rule_exception", "access_rule"):
        op.drop_constraint(op.f(f"ck_{table}_normative_effect"), table, type_="check")
        op.drop_constraint(op.f(f"ck_{table}_normalization_type"), table, type_="check")
    op.drop_constraint(op.f("ck_access_rule_needs_owner"), "access_rule", type_="check")
    op.create_check_constraint(
        op.f("ck_access_rule_needs_owner"),
        "access_rule",
        "(place_id IS NOT NULL) OR (zone_id IS NOT NULL)",
    )
    for table, columns in _TABLE_COLUMNS.items():
        for name, _ in columns:
            op.drop_column(table, name)
