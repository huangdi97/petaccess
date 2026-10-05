"""Link RealityReport child evidence rows back to their parent provenance.

Revision ID: f6b2c4d8e901
Revises: b37e5a1c9d20
Create Date: 2026-10-05

ObservationEffort and RealityConfirmation are children of one RealityReport,
but the original additive schema did not persist that parent link. Add nullable
report/evidence references so historical rows remain valid while new writes
retain the full Report -> EvidenceBundle -> child provenance chain.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6b2c4d8e901"
down_revision: str | None = "b37e5a1c9d20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table, prefix in (
        ("observation_effort", "effort"),
        ("reality_confirmation", "confirmation"),
    ):
        op.add_column(table, sa.Column("report_id", sa.String(length=36), nullable=True))
        op.add_column(
            table,
            sa.Column("evidence_bundle_id", sa.String(length=36), nullable=True),
        )
        op.create_foreign_key(
            f"fk_{prefix}_report",
            table,
            "reality_report",
            ["report_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_foreign_key(
            f"fk_{prefix}_evidence",
            table,
            "evidence_bundle",
            ["evidence_bundle_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(f"ix_{table}_report", table, ["report_id"])


def downgrade() -> None:
    for table, prefix in reversed(
        (
            ("observation_effort", "effort"),
            ("reality_confirmation", "confirmation"),
        )
    ):
        op.drop_index(f"ix_{table}_report", table_name=table)
        op.drop_constraint(f"fk_{prefix}_evidence", table, type_="foreignkey")
        op.drop_constraint(f"fk_{prefix}_report", table, type_="foreignkey")
        op.drop_column(table, "evidence_bundle_id")
        op.drop_column(table, "report_id")
