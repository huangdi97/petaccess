"""source_artifact.evidence_strength — capture-posture classification (S7)

Revision ID: b5e8d2c4a710
Revises: a7f3c2d91e04
Create Date: 2026-09-13

Internal, provenance-descriptive classification of HOW the artifact was
captured (PRIMARY_DIRECT / PRIMARY_CAPTURED / SECONDARY_REPUTABLE /
SEARCH_SNIPPET / USER_SUBMITTED / SOCIAL_LEAD). Deliberately NOT a composite
trust score: strength is descriptive, reviewable and per-artifact; no number is
synthesized. Backfill derives from collector_type + source_type + directness
using the same mapping as app.services.evidence_service.strength_for_artifact.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b5e8d2c4a710"
down_revision: str | None = "a7f3c2d91e04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BACKFILL = """
UPDATE source_artifact a SET evidence_strength = v.strength
FROM (VALUES
    ('agent_web_reader', 'statute_or_regulation', 'primary_direct'),
    ('agent_web_reader', 'government_service', 'primary_direct'),
    ('agent_web_reader', 'official_operator_policy', 'primary_direct'),
    ('agent_web_reader', 'external_web_reference', 'secondary_reputable'),
    ('agent_web_reader', 'ordinary_user', 'user_submitted'),
    ('agent_search_snippet', 'external_web_reference', 'search_snippet'),
    ('agent_search_snippet', 'ordinary_user', 'social_lead')
) AS v(collector, stype, strength)
WHERE a.collector_type = v.collector
  AND a.source_id IN (SELECT id FROM source WHERE source_type = v.stype)
  AND a.evidence_strength IS NULL
"""


def upgrade() -> None:
    op.add_column(
        "source_artifact",
        sa.Column("evidence_strength", sa.String(length=24), nullable=True),
    )
    op.create_check_constraint(
        op.f("ck_source_artifact_strength"),
        "source_artifact",
        "evidence_strength IS NULL OR evidence_strength IN ("
        "'primary_direct','primary_captured','secondary_reputable',"
        "'search_snippet','user_submitted','social_lead')",
    )
    op.execute(_BACKFILL)


def downgrade() -> None:
    op.drop_constraint(op.f("ck_source_artifact_strength"), "source_artifact", type_="check")
    op.drop_column("source_artifact", "evidence_strength")
