"""Track media uploader separately from subject ownership.

Revision ID: b37e5a1c9d20
Revises: a91f3c7d2e40
Create Date: 2026-10-05

Media owner_type/owner_id identify what a file belongs to (for example a Place),
not who uploaded it. Access control therefore needs a separate uploader key.
Existing rows are conservatively backfilled from the append-only media.upload
audit event; unresolved legacy rows remain NULL and are readable only by
reviewers/admins.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b37e5a1c9d20"
down_revision: str | None = "a91f3c7d2e40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "media_object",
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_media_object_created_by_user_id_user",
        "media_object",
        "user",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_media_object_created_by_user_id",
        "media_object",
        ["created_by_user_id"],
        unique=False,
    )
    op.execute(
        """
        UPDATE media_object AS m
           SET created_by_user_id = (
               SELECT a.actor_user_id
                 FROM audit_log AS a
                WHERE a.target_type = 'media_object'
                  AND a.target_id = m.id
                  AND a.action = 'media.upload'
                  AND a.actor_user_id IS NOT NULL
                ORDER BY a.created_at ASC
                LIMIT 1
           )
         WHERE m.created_by_user_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_media_object_created_by_user_id", table_name="media_object")
    op.drop_constraint(
        "fk_media_object_created_by_user_id_user",
        "media_object",
        type_="foreignkey",
    )
    op.drop_column("media_object", "created_by_user_id")
