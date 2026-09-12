"""rule_candidate.evidence_bundle_id — cite the evidence chain (E2E-D)

Revision ID: c81e02ba6d45
Revises: 4565819baf78
Create Date: 2026-09-13

Additive only: a rule candidate produced through the evidence chain
(SourceArtifact → EvidenceBundle → candidate) now cites the bundle it came
from, so the lead-only publish gate and rule-evidence traceability can be
enforced at the publish boundary (brief §5, §10). Nullable: legacy candidates
(media/OCR, monitor sweeps) keep their existing media_id / raw_text anchors.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c81e02ba6d45"
down_revision: str | None = "4565819baf78"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "rule_candidate",
        sa.Column("evidence_bundle_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_rule_candidate_evidence_bundle_id_evidence_bundle",
        "rule_candidate",
        "evidence_bundle",
        ["evidence_bundle_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_rule_candidate_evidence_bundle_id_evidence_bundle",
        "rule_candidate",
        type_="foreignkey",
    )
    op.drop_column("rule_candidate", "evidence_bundle_id")
