"""Add reviewed in-app Watch Event ledger.

Revision ID: d8f4b1c2e730
Revises: c6d1a8e4f205
Create Date: 2026-10-13

v0.10-R1 §39 requires a reviewed publication chain ending in Watch Event.
This table records one in-app delivery per subscription + published subject +
event type. It references public Rule/Reality truth without copying private
RealityReport provenance or pretending an external push provider exists.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8f4b1c2e730"
down_revision: str | None = "c6d1a8e4f205"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "watch_event",
        sa.Column("subscription_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("watch_domain", sa.String(length=16), nullable=False),
        sa.Column("target_type", sa.String(length=16), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("subject_type", sa.String(length=32), nullable=False),
        sa.Column("subject_id", sa.String(length=36), nullable=False),
        sa.Column("place_id", sa.String(length=36), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["watch_subscription.id"],
            name=op.f("fk_watch_event_subscription_id_watch_subscription"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_watch_event_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["place_id"],
            ["place.id"],
            name=op.f("fk_watch_event_place_id_place"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_watch_event")),
        sa.UniqueConstraint(
            "subscription_id",
            "event_type",
            "subject_id",
            name="uq_watch_event_delivery",
        ),
    )
    op.create_index(
        "ix_watch_event_user_created",
        "watch_event",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_watch_event_subscription_created",
        "watch_event",
        ["subscription_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_watch_event_subscription_created", table_name="watch_event")
    op.drop_index("ix_watch_event_user_created", table_name="watch_event")
    op.drop_table("watch_event")
