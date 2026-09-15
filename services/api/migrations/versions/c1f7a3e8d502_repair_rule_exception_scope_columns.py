"""repair rule_exception source-faithful scope columns (ADR-025 / ADR-026)

Revision ID: c1f7a3e8d502
Revises: a2d5e8b91c47
Create Date: 2026-09-15

Defect found during the 2026-09-15 takeover
-------------------------------------------

``a2d5e8b91c47`` was **stamped as applied while only partially executed**.
``access_rule`` and ``rule_candidate`` received the five ADR-025 scope columns,
but ``rule_exception`` did not:

    alembic_version           = a2d5e8b91c47
    access_rule               → source_scope_exact  (present)
    rule_candidate            → source_scope_exact  (present)
    rule_exception            → source_scope_exact  (ABSENT)   ← this migration

Root cause: the columns for ``rule_exception`` were added to the migration file
*after* the revision had already been applied to this database, and Alembic will
not re-run an applied revision. Every ORM read of ``RuleException`` then failed
with ``UndefinedColumn`` — 20+ integration tests went red while the version table
looked healthy. It is the exact failure mode ADR-024 already required a repair
migration for, so this follows that precedent.

Behaviour
---------

Additive and **idempotent** in both directions:

* fresh database  → ``a2d5e8b91c47`` already adds everything; this is a no-op;
* existing database → the five columns + two check constraints are added here.

The backfill never widens a scope (it mirrors ``a2d5e8b91c47`` exactly):
``service_dog`` stays NULL + ``legal_interpretation_required`` — it is the very
generalisation under review, so it must not be silently reinterpreted.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c1f7a3e8d502"
down_revision: str | None = "a2d5e8b91c47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "rule_exception"

_COLUMNS: list[tuple[str, sa.types.TypeEngine]] = [
    ("source_scope_exact", sa.String(length=64)),
    ("subject_scope_normalized", sa.String(length=32)),
    ("normalization_type", sa.String(length=32)),
    ("normative_effect", sa.String(length=32)),
    ("holder_scope", sa.String(length=32)),
]

_BACKFILL_SCOPE = sa.text(
    """
    UPDATE rule_exception
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

_BACKFILL_NORMATIVE = sa.text(
    """
    UPDATE rule_exception
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


def _existing_columns() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {c["name"] for c in inspector.get_columns(_TABLE)}


def _existing_check_names() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {c["name"] for c in inspector.get_check_constraints(_TABLE)}


def upgrade() -> None:
    present = _existing_columns()
    added_any = False
    for name, coltype in _COLUMNS:
        if name in present:
            continue
        op.add_column(_TABLE, sa.Column(name, coltype, nullable=True))
        added_any = True

    # Backfill is safe to run unconditionally: every clause is guarded by
    # `... IS NULL`, so a fully-populated table is unchanged (no-op).
    op.execute(_BACKFILL_SCOPE.text)
    op.execute(_BACKFILL_NORMATIVE.text)

    existing = _existing_check_names()
    for name, condition in (
        ("ck_rule_exception_normalization_type", _NORMALIZATION_CHECK),
        ("ck_rule_exception_normative_effect", _NORMATIVE_CHECK),
    ):
        if name in existing:
            continue
        op.create_check_constraint(op.f(name), _TABLE, condition)

    if not added_any:
        # Nothing to do — keep the migration visible in the log.
        op.get_bind().exec_driver_sql("SELECT 1")


def downgrade() -> None:
    existing = _existing_check_names()
    for name in ("ck_rule_exception_normative_effect", "ck_rule_exception_normalization_type"):
        if name in existing:
            op.drop_constraint(op.f(name), _TABLE, type_="check")

    present = _existing_columns()
    for name, _ in reversed(_COLUMNS):
        if name in present:
            op.drop_column(_TABLE, name)
