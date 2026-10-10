"""Separate Rule Watch from Reality Watch.

Revision ID: c6d1a8e4f205
Revises: f9c2d4a7b801
Create Date: 2026-10-06

Existing subscriptions are preserved as Rule Watch. The additive watch_domain
axis lets the same user follow reviewed Rule changes and newly published,
human-verified Reality facts independently for the same place/zone/rule target.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c6d1a8e4f205"
down_revision: str | None = "f9c2d4a7b801"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "watch_subscription",
        sa.Column(
            "watch_domain",
            sa.String(length=16),
            nullable=False,
            server_default="rule",
        ),
    )
    op.drop_constraint("uq_watch_user_target", "watch_subscription", type_="unique")
    op.drop_index("ix_watch_target", table_name="watch_subscription")
    op.create_unique_constraint(
        "uq_watch_user_domain_target",
        "watch_subscription",
        ["user_id", "watch_domain", "target_type", "target_id"],
    )
    op.create_index(
        "ix_watch_target",
        "watch_subscription",
        ["watch_domain", "target_type", "target_id"],
        unique=False,
    )


def downgrade() -> None:
    # A user may have both Rule and Reality watches on one target. Keep the
    # Rule row when both exist so the legacy unique constraint can be restored.
    op.execute(
        """
        DELETE FROM watch_subscription AS reality
        USING watch_subscription AS rule
        WHERE reality.user_id = rule.user_id
          AND reality.target_type = rule.target_type
          AND reality.target_id = rule.target_id
          AND reality.watch_domain = 'reality'
          AND rule.watch_domain = 'rule'
        """
    )
    op.drop_index("ix_watch_target", table_name="watch_subscription")
    op.drop_constraint("uq_watch_user_domain_target", "watch_subscription", type_="unique")
    op.create_unique_constraint(
        "uq_watch_user_target",
        "watch_subscription",
        ["user_id", "target_type", "target_id"],
    )
    op.create_index(
        "ix_watch_target",
        "watch_subscription",
        ["target_type", "target_id"],
        unique=False,
    )
    op.drop_column("watch_subscription", "watch_domain")
