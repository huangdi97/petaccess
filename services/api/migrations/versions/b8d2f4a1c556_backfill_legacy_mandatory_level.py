"""backfill the legacy `discretionary` mandatory_level

Revision ID: b8d2f4a1c556
Revises: a7c4e1b90d33
Create Date: 2026-09-16

Why
---

ADR-023 renamed the third mandatory level to `operator_discretion`, and
`normalize_mandatory_level()` keeps accepting the old spelling on read so
existing rows and fixtures keep working. One `jurisdiction_rule` row still
carries `discretionary`, and that single row was returning **500 for the whole
`GET /regulations` list**: response validation runs per item, so one
unconvertible value fails the entire response instead of that one row.

The read path is now fixed separately (`RegulationOut` normalises before
validation), which is the part that matters for robustness. This migration
closes the other half: the stored vocabulary should equal the canonical
vocabulary so the next consumer of this column does not have to know about a
dead spelling. A read-time normaliser is a compatibility shim, not a licence to
leave the data wrong.

No business semantics change: `discretionary` and `operator_discretion` denote
the same normative force, and the normaliser has mapped them 1:1 since ADR-023.

Idempotent: the UPDATE matches nothing once applied.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8d2f4a1c556"
down_revision: str | None = "a7c4e1b90d33"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Every table that carries a mandatory_level, so the next occurrence cannot
# hide in one that was forgotten.
_TABLES = ("jurisdiction_rule", "access_rule", "rule_candidate")

_LEGACY = "discretionary"
_CANONICAL = "operator_discretion"


def _has_column(table: str, column: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    conn = op.get_bind()
    for table in _TABLES:
        if not _has_column(table, "mandatory_level"):
            continue
        result = conn.execute(
            sa.text(
                f"UPDATE {table} SET mandatory_level = :canonical "  # noqa: S608 - literal table name
                "WHERE mandatory_level = :legacy"
            ),
            {"canonical": _CANONICAL, "legacy": _LEGACY},
        )
        if result.rowcount:
            print(f"  {table}: normalised {result.rowcount} legacy row(s)")


def downgrade() -> None:
    # Deliberately a no-op. Reintroducing a spelling that the schema no longer
    # accepts would restore the 500 this migration exists to remove, and the
    # two values are semantically identical, so there is nothing to restore.
    pass
