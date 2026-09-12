"""backfill rule_layer from source_type (idempotent, conservative)

Revision ID: b2a1c7d9e001
Revises: 4930732f4783
Create Date: 2026-09-12

Backfill policy (MIGRATION_SPEC_v0.5):
- statute_or_regulation / government_service sources → LEGAL
- official_operator_policy sources → OPERATOR_POLICY
- everything else (onsite signage, ordinary user, external refs…) is NOT
  guessable → stays NULL, resolver reports REVIEW_REQUIRED. Never guessed.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "b2a1c7d9e001"
down_revision: str | None = "4930732f4783"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE access_rule r
        SET rule_layer = 'LEGAL'
        FROM source s
        WHERE r.source_id = s.id
          AND s.source_type IN ('statute_or_regulation', 'government_service')
          AND r.rule_layer IS NULL
        """
    )
    op.execute(
        """
        UPDATE access_rule r
        SET rule_layer = 'OPERATOR_POLICY'
        FROM source s
        WHERE r.source_id = s.id
          AND s.source_type = 'official_operator_policy'
          AND r.rule_layer IS NULL
        """
    )


def downgrade() -> None:
    # data is recoverable by re-running upgrade; clearing layers is lossless
    # only in the sense that NULL was the pre-backfill state — we only clear
    # the two deterministic mappings, leaving no invented data behind.
    op.execute(
        """
        UPDATE access_rule r
        SET rule_layer = NULL
        FROM source s
        WHERE r.source_id = s.id
          AND s.source_type IN ('statute_or_regulation', 'government_service',
                                'official_operator_policy')
          AND r.rule_layer IN ('LEGAL', 'OPERATOR_POLICY')
        """
    )
