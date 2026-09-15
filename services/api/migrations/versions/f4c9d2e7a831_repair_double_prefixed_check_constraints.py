"""repair double-prefixed check-constraint names

Revision ID: f4c9d2e7a831
Revises: e3b7a1c4f920
Create Date: 2026-09-14

Four hand-written migrations passed an already-prefixed name to
``op.create_check_constraint`` / ``sa.CheckConstraint`` without wrapping it in
``op.f()``. The metadata naming convention (``ck_%(table_name)s_%(constraint_name)s``)
was therefore applied a second time, producing names such as

    ck_access_rule_ck_access_rule_mandatory_level

instead of the intended

    ck_access_rule_mandatory_level

The migration sources are fixed, so a **fresh** database now gets the intended
names. This migration repairs databases that already ran the buggy revisions by
renaming the legacy constraints in place.

It is deliberately idempotent and safe on both kinds of database:

  * a repaired / freshly-built database has no ``ck_<t>_ck_<t>_*`` constraint
    left, so the loop body never executes;
  * a database that ran the buggy revisions has exactly those names renamed.

Only constraint *names* change — no column, type, or data is touched, and the
check expressions are preserved verbatim by ``RENAME CONSTRAINT``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f4c9d2e7a831"
down_revision: str | None = "e3b7a1c4f920"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: (table, legacy double-prefixed name, intended name)
_RENAMES: list[tuple[str, str, str]] = [
    (
        "access_rule",
        "ck_access_rule_ck_access_rule_mandatory_level",
        "ck_access_rule_mandatory_level",
    ),
    (
        "rule_candidate",
        "ck_rule_candidate_ck_rule_candidate_layer",
        "ck_rule_candidate_layer",
    ),
    (
        "rule_candidate",
        "ck_rule_candidate_ck_rule_candidate_mandatory_level",
        "ck_rule_candidate_mandatory_level",
    ),
    (
        "rule_exception",
        "ck_rule_exception_ck_rule_exception_scope",
        "ck_rule_exception_scope",
    ),
    (
        "rule_exception",
        "ck_rule_exception_ck_rule_exception_effect",
        "ck_rule_exception_effect",
    ),
    (
        "rule_exception",
        "ck_rule_exception_ck_rule_exception_status",
        "ck_rule_exception_status",
    ),
    (
        "source_artifact",
        "ck_source_artifact_ck_source_artifact_strength",
        "ck_source_artifact_strength",
    ),
]

#: rename only when the legacy name exists and the intended one does not, so a
#: fresh database (already correct) is a no-op.
_LIST_CHECK_CONSTRAINTS = sa.text(
    "SELECT conname FROM pg_constraint WHERE conrelid = to_regclass(:tbl) AND contype = 'c'"
)


def _check_constraint_names(table: str) -> set[str]:
    bind = op.get_bind()
    rows = bind.execute(_LIST_CHECK_CONSTRAINTS, {"tbl": table}).fetchall()
    return {row[0] for row in rows}


def upgrade() -> None:
    for table, old, new in _RENAMES:
        existing = _check_constraint_names(table)
        if old in existing and new not in existing:
            # identifiers come from the hard-coded _RENAMES table, never from
            # user input, so quoting them into the DDL is safe.
            op.execute(f'ALTER TABLE "{table}" RENAME CONSTRAINT "{old}" TO "{new}"')


def downgrade() -> None:
    """Intentionally a no-op.

    Renaming the constraints back to a name that no migration ever intended
    would re-introduce the defect. After this revision is downgraded the names
    stay correct, and re-upgrading re-runs the (idempotent) rename, so the
    up/down/up cycle is stable.
    """
