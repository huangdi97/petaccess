"""rule_candidate.rule_layer — normative layer carried to publish (P0 fix)

Revision ID: d1a4f7c93b28
Revises: b5e8d2c4a710
Create Date: 2026-09-13

P0-REVIEW-PUBLISH-01 defect: `candidate_service.publish()` hard-coded
`AccessRule.rule_layer = "OPERATOR_POLICY"`, and `RuleCandidate` had no
`rule_layer` field, so the layer recorded in the evidence register (LEGAL /
TEMPORARY_POLICY / …) was silently dropped at ingest and flattened at publish.

`rule_layer` is load-bearing: `v05_resolver._load_layered_rules()` routes rules
into the legal / guidance / event / operator pools purely on this value, and
suppression logic ("a mandatory legal prohibition cannot be relaxed by an
operator policy", "an active temporary policy shadows operator-side entries")
keys on it. Flattening a statutory prohibition to an operator policy therefore
changes the published answer — unacceptable for the first real publish.

This migration is additive: existing rows default to OPERATOR_POLICY (the value
the old code wrote anyway), so no published rule changes meaning. Candidates
whose true layer differs are corrected by
`scripts/backfill_candidate_rule_layer.py`, which reads the evidence register and
writes an audit entry per row.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d1a4f7c93b28"
down_revision: str | None = "b5e8d2c4a710"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_LAYERS = "'LEGAL','REGULATORY_GUIDANCE','OPERATOR_POLICY','TEMPORARY_POLICY'"


def upgrade() -> None:
    op.add_column(
        "rule_candidate",
        sa.Column(
            "rule_layer",
            sa.String(length=30),
            nullable=False,
            server_default="OPERATOR_POLICY",
        ),
    )
    op.create_check_constraint(
        "ck_rule_candidate_layer",
        "rule_candidate",
        f"rule_layer IN ({_LAYERS})",
    )


def downgrade() -> None:
    op.drop_constraint("ck_rule_candidate_layer", "rule_candidate", type_="check")
    op.drop_column("rule_candidate", "rule_layer")
