"""allow the compound_term_split normalisation (ADR-028)

Revision ID: e5b1c9d4a726
Revises: d4a8b2f6c903
Create Date: 2026-09-15

Why
---

上海图书馆《读者须知》 grants an exception for 「导盲犬、军警犬」. 「军警犬」 is a
*compound* term covering exactly two roles — police dogs and military working
dogs — and the source does not distinguish further. Modelling it as one
`service_dog` row would be the ADR-025 widening again; modelling it as a single
`police_dog` row would silently drop military working dogs.

So the term is split into one row per member, each keeping the compound wording
verbatim in ``source_scope_exact``, and the rows are labelled with a normalisation
that means "this row is one member of a documented, exhaustive split of the
source's compound term" — ``compound_term_split``.

The two existing CHECK constraints enumerate the vocabulary, so they must be
extended. This migration drops and recreates them (additive vocabulary only: no
existing row can become invalid).

Idempotent: the constraint is dropped only when present, and recreated with the
extended list, so re-running or running on a fresh database is safe.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5b1c9d4a726"
down_revision: str | None = "d4a8b2f6c903"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ("access_rule", "rule_exception")

_WITH_SPLIT = (
    "normalization_type IS NULL OR normalization_type IN "
    "('exact','parent_group_for_query_only','legal_interpretation_required',"
    "'compound_term_split')"
)
_WITHOUT_SPLIT = (
    "normalization_type IS NULL OR normalization_type IN "
    "('exact','parent_group_for_query_only','legal_interpretation_required')"
)


def _check_names(table: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {c["name"] for c in inspector.get_check_constraints(table)}


def upgrade() -> None:
    for table in _TABLES:
        name = f"ck_{table}_normalization_type"
        if name in _check_names(table):
            op.drop_constraint(op.f(name), table, type_="check")
        op.create_check_constraint(op.f(name), table, _WITH_SPLIT)


def downgrade() -> None:
    for table in _TABLES:
        name = f"ck_{table}_normalization_type"
        if name in _check_names(table):
            op.drop_constraint(op.f(name), table, type_="check")
        op.create_check_constraint(op.f(name), table, _WITHOUT_SPLIT)
