"""place alias names — search affordance, not identity

Revision ID: a7c4e1b90d33
Revises: e5b1c9d4a726
Create Date: 2026-09-16

Why
---

Users search with the name they know, and the name they know is frequently not
the canonical one: 「星巴克臻选」 for 「星巴克臻选上海烘焙工坊」, a former name
after a rebrand, a mall's colloquial short form. Today `GET /places?q=` only
matches ``canonical_name``, so those searches return nothing and the user reads
the empty result as "no rules here" — the one failure mode this product exists
to prevent, since 「查不到」 and 「没有限制」 look identical on screen.

Scope, deliberately narrow
--------------------------

An alias is a **lookup key**, never a claim about the place. It carries no
source, no evidence, no verification state, and it can never be shown as the
place's name. ``canonical_name`` stays the single identity, and every result
raised by an alias reports *which* alias matched so the user can see why a
place they did not name came back.

That is also why this is a column on ``place`` and not a child table: a child
table would imply aliases participate in the source/audit/dispute machinery,
and they must not. The column is JSONB because the list is small (<10), is read
whole, and is only ever queried by element containment.

A GIN index makes the containment lookup cheap; the per-element fuzzy match
still relies on ``pg_trgm``, which is already enabled for the trigram search on
``canonical_name``.

Idempotent: the column and index are created only when absent, so this is safe
to re-run and safe on a fresh database.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a7c4e1b90d33"
down_revision: str | None = "e5b1c9d4a726"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_INDEX = "ix_place_alias_names_gin"


def _has_column(table: str, column: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column in {c["name"] for c in inspector.get_columns(table)}


def _has_index(table: str, name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return name in {i["name"] for i in inspector.get_indexes(table)}


def upgrade() -> None:
    if not _has_column("place", "alias_names"):
        op.add_column(
            "place",
            sa.Column(
                "alias_names",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
        )
    if not _has_index("place", _INDEX):
        op.create_index(_INDEX, "place", ["alias_names"], postgresql_using="gin")


def downgrade() -> None:
    if _has_index("place", _INDEX):
        op.drop_index(_INDEX, table_name="place")
    if _has_column("place", "alias_names"):
        op.drop_column("place", "alias_names")
