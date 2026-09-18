"""30-50 PLACE EXPANSION WAVE 01 — additive production-run / freshness columns.

Revision ID: c9d4e2a17b30
Revises: b8d2f4a1c556
Create Date: 2026-09-18

Purely additive: every column is NULLABLE, no table is rewritten, no existing
row is backfilled with invented values and no constraint is tightened. The
governance freeze on R2-FINAL-R3 (its evidence, sources, audit trail and the
already-published BATCH-01B rows) is therefore untouched by this migration.

What it adds and why:

1. ``source.last_verified_at`` / ``review_due_at`` / ``freshness_policy_id``
   A source could previously be cited by a published rule with no machine
   readable notion of *when* it was last checked or *when* it must be checked
   again. Expansion turns 15 sources into hundreds, so "we will remember to
   re-read this page" stops being a strategy. review_due means "needs
   re-verification", never "invalid" — no code path may read it as a signal to
   drop evidence or flip a conclusion.

2. ``source_monitor.last_http_status`` / ``last_latency_ms``
   Conditional GET (ETag / If-None-Match, Last-Modified / If-Modified-Since)
   only saves work if the sweep records *why* it got a 304 rather than a body.
   Without these two columns a monitor that silently starts returning 403 is
   indistinguishable from a genuinely unchanged page.

3. ``expansion_run_id`` on the six production-chain tables
   A wave touches place selection, collection, candidates, monitors and the
   report. Without a run id there is no way to answer "which of these 40
   candidates came from this wave" without re-deriving it from timestamps.

4. ``rule_candidate.dedup_key`` / ``observation_candidate.dedup_key``
   A monitor that re-detects the same content must not produce a second
   candidate for the same statement. Dedup needs a deterministic key over
   (source, content hash, scope, action, effect) — it is an ingestion guard,
   not an identity claim about the rule.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9d4e2a17b30"
down_revision: str | None = "b8d2f4a1c556"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RUN_ID_TABLES = (
    "data_source_job",
    "source_artifact",
    "evidence_bundle",
    "rule_candidate",
    "observation_candidate",
    "source_monitor",
)


def upgrade() -> None:
    # --- 1. source freshness -------------------------------------------------
    op.add_column(
        "source", sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("source", sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("source", sa.Column("freshness_policy_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        op.f("fk_source_freshness_policy"),
        "source",
        "freshness_policy",
        ["freshness_policy_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_source_review_due_at"), "source", ["review_due_at"])

    # --- 2. monitor conditional-GET bookkeeping ------------------------------
    op.add_column("source_monitor", sa.Column("last_http_status", sa.Integer(), nullable=True))
    op.add_column("source_monitor", sa.Column("last_latency_ms", sa.Integer(), nullable=True))

    # --- 3. expansion run traceability --------------------------------------
    for table in _RUN_ID_TABLES:
        op.add_column(table, sa.Column("expansion_run_id", sa.String(length=64), nullable=True))
        op.create_index(op.f(f"ix_{table}_expansion_run_id"), table, ["expansion_run_id"])

    # --- 4. candidate ingestion dedup ---------------------------------------
    op.add_column("rule_candidate", sa.Column("dedup_key", sa.String(length=128), nullable=True))
    op.create_index(op.f("ix_rule_candidate_dedup_key"), "rule_candidate", ["dedup_key"])
    op.add_column(
        "observation_candidate", sa.Column("dedup_key", sa.String(length=128), nullable=True)
    )
    op.create_index(
        op.f("ix_observation_candidate_dedup_key"), "observation_candidate", ["dedup_key"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_observation_candidate_dedup_key"), table_name="observation_candidate")
    op.drop_column("observation_candidate", "dedup_key")
    op.drop_index(op.f("ix_rule_candidate_dedup_key"), table_name="rule_candidate")
    op.drop_column("rule_candidate", "dedup_key")

    for table in _RUN_ID_TABLES:
        op.drop_index(op.f(f"ix_{table}_expansion_run_id"), table_name=table)
        op.drop_column(table, "expansion_run_id")

    op.drop_column("source_monitor", "last_latency_ms")
    op.drop_column("source_monitor", "last_http_status")

    op.drop_index(op.f("ix_source_review_due_at"), table_name="source")
    op.drop_constraint(op.f("fk_source_freshness_policy"), "source", type_="foreignkey")
    op.drop_column("source", "freshness_policy_id")
    op.drop_column("source", "review_due_at")
    op.drop_column("source", "last_verified_at")
