"""Reality awareness + facility purpose states.

Revision ID: a91f3c7d2e40
Revises: e9f2c1d4a5b6
Create Date: 2026-10-05

Add the two v0.10 Reality semantics that were already frozen in the domain
vocabulary but were not persisted on published claims:

- staff_response_observation.staff_awareness_state
- animal_facility.purpose_state

Both columns are explicit, non-null state axes with conservative UNKNOWN
server defaults. The migration does not infer historical intent: existing rows
become UNKNOWN, so no old claim is upgraded into "staff knew" or "facility
purpose confirmed" without evidence.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a91f3c7d2e40"
down_revision: str | None = "e9f2c1d4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "staff_response_observation",
        sa.Column(
            "staff_awareness_state",
            sa.String(length=24),
            nullable=False,
            server_default="awareness_unknown",
        ),
    )
    op.add_column(
        "animal_facility",
        sa.Column(
            "purpose_state",
            sa.String(length=32),
            nullable=False,
            server_default="purpose_unknown",
        ),
    )


def downgrade() -> None:
    op.drop_column("animal_facility", "purpose_state")
    op.drop_column("staff_response_observation", "staff_awareness_state")
