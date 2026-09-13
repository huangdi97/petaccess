"""rule_exception — first-class statutory/operator carve-out (SG-REAL-01)

Revision ID: a7f3c2d91e04
Revises: c81e02ba6d45
Create Date: 2026-09-13

A base rule may govern a broad scope (e.g. LEGAL prohibition on DOG) while the
SAME normative statement carves out a narrower scope (e.g. guide dogs exempt,
《上海市养犬管理条例》第二十三条但书). Modelling that carve-out as a second
standalone rule cannot express "exempt FROM this rule": the resolver saw two
same-layer rules and silently picked the strictest, banning working guide dogs.

RuleException is attached to its base rule and carries its own source (NOT NULL
— an exception without provenance is invalid), lifecycle status and validity
window. The resolver suppresses the base rule for queries matching the exempt
scope and applies the exception effect instead. Observations never take part
(ADR-004). Generic mechanism — no hardcoded service_dog branch.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7f3c2d91e04"
down_revision: str | None = "c81e02ba6d45"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rule_exception",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "rule_id",
            sa.String(length=36),
            sa.ForeignKey("access_rule.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("animal_scope", sa.String(length=20), nullable=False),
        sa.Column("effect", sa.String(length=16), nullable=False),
        sa.Column(
            "source_id",
            sa.String(length=36),
            sa.ForeignKey("source.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="current"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "animal_scope IN ('dog','cat','ordinary_pet','service_dog','other')",
            name="ck_rule_exception_scope",
        ),
        sa.CheckConstraint(
            "effect IN ('allowed','prohibited','conditional')",
            name="ck_rule_exception_effect",
        ),
        sa.CheckConstraint(
            "status IN ('pending_review','current','superseded','withdrawn','disputed','archived')",
            name="ck_rule_exception_status",
        ),
    )
    op.create_index("ix_rule_exception_rule", "rule_exception", ["rule_id"])
    op.create_index("ix_rule_exception_status", "rule_exception", ["status"])


def downgrade() -> None:
    op.drop_index("ix_rule_exception_status", table_name="rule_exception")
    op.drop_index("ix_rule_exception_rule", table_name="rule_exception")
    op.drop_table("rule_exception")
