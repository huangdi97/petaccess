"""source-faithful scope on policy_template_rule (ADR-025)

Revision ID: d4a8b2f6c903
Revises: c1f7a3e8d502
Create Date: 2026-09-15

``policy_template_rule`` is a rule source like any other: an organization's
template can declare service-dog entry, and the resolver treats inherited
entries exactly like place rules. Without the ADR-025 scope columns a template
entry could only say ``animal_scope='service_dog'`` — the unproven widening — so
after ADR-025 took effect every template-carried service-dog entry silently
stopped governing (caught by ``test_e2e_b_operator_template_inheritance_and_override``).

This adds the five scope columns so a template can record what its source
literally names, additively and idempotently.

Backfill is conservative and identical in spirit to ``a2d5e8b91c47``: rows are
left with ``subject_scope_normalized`` NULL unless the scope is one the source
genuinely named; ``service_dog`` becomes ``legal_interpretation_required`` so it
confers nothing until a human re-models it.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4a8b2f6c903"
down_revision: str | None = "c1f7a3e8d502"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "policy_template_rule"

_COLUMNS: list[tuple[str, sa.types.TypeEngine]] = [
    ("source_scope_exact", sa.String(length=64)),
    ("subject_scope_normalized", sa.String(length=32)),
    ("normalization_type", sa.String(length=32)),
    ("normative_effect", sa.String(length=32)),
    ("holder_scope", sa.String(length=32)),
]

_BACKFILL = sa.text(
    """
    UPDATE policy_template_rule
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


def _existing_columns() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {c["name"] for c in inspector.get_columns(_TABLE)}


def upgrade() -> None:
    present = _existing_columns()
    for name, coltype in _COLUMNS:
        if name in present:
            continue
        op.add_column(_TABLE, sa.Column(name, coltype, nullable=True))
    op.execute(_BACKFILL.text)


def downgrade() -> None:
    present = _existing_columns()
    for name, _ in reversed(_COLUMNS):
        if name in present:
            op.drop_column(_TABLE, name)
