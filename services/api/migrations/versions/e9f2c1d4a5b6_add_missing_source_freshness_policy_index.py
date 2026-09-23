"""add_missing_source_freshness_policy_index

Revision ID: e9f2c1d4a5b6
Revises: d4e7b2a8c9f1
Create Date: 2026-09-23

Closes a pre-existing ORM/DB drift found during the F1 "Alembic no drift"
closure: the ``Source`` model declares ``freshness_policy_id`` with
``index=True`` (convention name ``ix_source_freshness_policy_id``), but no
migration ever created that index. ``alembic check`` therefore proposes an
``add_index`` every run.

This is additive / idempotent:

- it creates only the missing index;
- it does NOT touch the old migration (c9d4e2a17b30) that added the column;
- no data is dropped; FK semantics unchanged.

The three other pre-existing drift items (ix_place_canonical_name_trgm /
ix_place_alias_names_gin / ix_source_review_due_at) were the reverse case
(DB had hand-written indexes the ORM did not declare); those are declared in
the ORM metadata (place.py / rule.py) so autogenerate reports no drift either.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "e9f2c1d4a5b6"
down_revision: str | None = "d4e7b2a8c9f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        op.f("ix_source_freshness_policy_id"),
        "source",
        ["freshness_policy_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_source_freshness_policy_id"), table_name="source")
