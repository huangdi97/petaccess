"""Persist explicit rule supersession intent on RuleCandidate.

Revision ID: f9c2d4a7b801
Revises: f6b2c4d8e901
Create Date: 2026-10-05

A consumer can report that one specific current rule changed. Previously the
target rule id lived only in the create audit event, while RuleCandidate itself
lost that relation. Publishing then only superseded same-source rules, which is
insufficient for a consumer lead because each lead has a new Source row.

The nullable pointer preserves review intent without changing any existing
candidate. Publication still requires the ordinary human review and publish
gates; this column never authorizes supersession by itself.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f9c2d4a7b801"
down_revision: str | None = "f6b2c4d8e901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "rule_candidate",
        sa.Column("supersedes_rule_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_rule_candidate_supersedes_rule",
        "rule_candidate",
        "access_rule",
        ["supersedes_rule_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_rule_candidate_supersedes_rule",
        "rule_candidate",
        ["supersedes_rule_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_rule_candidate_supersedes_rule", table_name="rule_candidate")
    op.drop_constraint(
        "fk_rule_candidate_supersedes_rule",
        "rule_candidate",
        type_="foreignkey",
    )
    op.drop_column("rule_candidate", "supersedes_rule_id")
