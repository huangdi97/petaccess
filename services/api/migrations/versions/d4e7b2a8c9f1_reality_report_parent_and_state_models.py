"""reality_report_parent_and_state_models

Revision ID: d4e7b2a8c9f1
Revises: c3a9e5f7d1b2
Create Date: 2026-09-22

Additive migration for the 2026-09-22 contribution-deepening addendum:

- ``reality_report``            — parent context of a contribution (one report
  may produce several RealityCandidates). Carries origin / place match / time
  evidence / fact evidence / media / source / privacy / moderation / anti-abuse
  fields.
- ``observation_effort``        — "was on site and did not see an animal"
  structured record. animal_observed=false forms ONLY an effort row, never a
  NO_ANIMAL_PRESENCE claim.
- ``reality_confirmation``      — lightweight on-site confirmation; evidence,
  never a deletion (NOT_SEEN_NOW must not remove older Observations).
- ``external_content_reference``— external post/video reference with dedup
  hashes (content_hash / media_hash) and OCR/keyframe metadata.
- ``reality_candidate.report_id`` — nullable FK onto reality_report (parent link).

All FK names are explicit and ≤63 characters (R-01 lesson). No old migration is
touched; no data is dropped; FK semantics unchanged.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e7b2a8c9f1"
down_revision: str | None = "c3a9e5f7d1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- reality_report (parent) ---------------------------------------------
    op.create_table(
        "reality_report",
        sa.Column("reporter_id", sa.String(length=36), nullable=True),
        sa.Column("anonymous_token", sa.String(length=128), nullable=True),
        sa.Column("origin", sa.String(length=32), nullable=False),
        sa.Column("place_id", sa.String(length=36), nullable=True),
        sa.Column("container_place_id", sa.String(length=36), nullable=True),
        sa.Column("subject_place_id", sa.String(length=36), nullable=True),
        sa.Column("place_match_state", sa.String(length=24), nullable=False),
        sa.Column("place_match_evidence_types", sa.JSON(), nullable=True),
        sa.Column("time_evidence_state", sa.String(length=32), nullable=False),
        sa.Column("content_published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_certainty", sa.String(length=16), nullable=False),
        sa.Column("fact_evidence_state", sa.String(length=32), nullable=False),
        sa.Column("privacy_state", sa.String(length=16), nullable=False),
        sa.Column("media_refs", sa.JSON(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_platform", sa.String(length=24), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("media_hash", sa.String(length=128), nullable=True),
        sa.Column("external_keyframe_ref", sa.String(length=255), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("moderation_state", sa.String(length=16), nullable=False),
        sa.Column("abuse_flags", sa.JSON(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
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
            ["place_id"],
            ["place.id"],
            name=op.f("fk_reality_report_place_id_place"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_id"],
            ["user.id"],
            name=op.f("fk_reality_report_reporter_id_user"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reality_report")),
    )
    op.create_index(
        "ix_reality_report_origin_moderation",
        "reality_report",
        ["origin", "moderation_state"],
        unique=False,
    )
    op.create_index(
        "ix_reality_report_reporter",
        "reality_report",
        ["reporter_id"],
        unique=False,
    )

    # --- observation_effort ---------------------------------------------------
    op.create_table(
        "observation_effort",
        sa.Column("place_id", sa.String(length=36), nullable=False),
        sa.Column("duration_bucket", sa.String(length=16), nullable=False),
        sa.Column("covered_zone_ids", sa.JSON(), nullable=True),
        sa.Column("animal_observed", sa.Boolean(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reporter_id", sa.String(length=36), nullable=True),
        sa.Column("source_id", sa.String(length=36), nullable=True),
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
            ["place_id"],
            ["place.id"],
            name=op.f("fk_observation_effort_place_id_place"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_id"],
            ["user.id"],
            name=op.f("fk_observation_effort_reporter_id_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["source.id"],
            name=op.f("fk_observation_effort_source_id_source"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_observation_effort")),
    )
    op.create_index(
        "ix_observation_effort_animal",
        "observation_effort",
        ["animal_observed"],
        unique=False,
    )
    op.create_index(
        "ix_observation_effort_place_time",
        "observation_effort",
        ["place_id", "observed_at"],
        unique=False,
    )

    # --- reality_confirmation -------------------------------------------------
    op.create_table(
        "reality_confirmation",
        sa.Column("confirmation_type", sa.String(length=24), nullable=False),
        sa.Column("place_id", sa.String(length=36), nullable=False),
        sa.Column("target_claim_id", sa.String(length=36), nullable=True),
        sa.Column("target_candidate_id", sa.String(length=36), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reporter_id", sa.String(length=36), nullable=True),
        sa.Column("source_id", sa.String(length=36), nullable=True),
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
            ["place_id"],
            ["place.id"],
            name=op.f("fk_reality_confirmation_place_id_place"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_id"],
            ["user.id"],
            name=op.f("fk_reality_confirmation_reporter_id_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["source.id"],
            name=op.f("fk_reality_confirmation_source_id_source"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_candidate_id"],
            ["reality_candidate.id"],
            name=op.f("fk_reality_confirmation_target_candidate_reality_cand"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reality_confirmation")),
    )
    op.create_index(
        "ix_reality_confirmation_place_type",
        "reality_confirmation",
        ["place_id", "confirmation_type"],
        unique=False,
    )
    op.create_index(
        "ix_reality_confirmation_target",
        "reality_confirmation",
        ["target_claim_id"],
        unique=False,
    )

    # --- external_content_reference -------------------------------------------
    op.create_table(
        "external_content_reference",
        sa.Column("report_id", sa.String(length=36), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("platform", sa.String(length=24), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("place_metadata", sa.JSON(), nullable=True),
        sa.Column("keyframe_ref", sa.String(length=255), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("media_hash", sa.String(length=128), nullable=True),
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
            ["report_id"],
            ["reality_report.id"],
            name=op.f("fk_external_content_ref_report_id_reality_report"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_external_content_reference")),
    )
    op.create_index(
        "ix_external_content_ref_hash",
        "external_content_reference",
        ["content_hash"],
        unique=False,
    )
    op.create_index(
        "ix_external_content_ref_report",
        "external_content_reference",
        ["report_id"],
        unique=False,
    )

    # --- reality_candidate.report_id (parent link) ----------------------------
    op.add_column(
        "reality_candidate",
        sa.Column("report_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_reality_candidate_report_id_reality_report",
        "reality_candidate",
        "reality_report",
        ["report_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_reality_candidate_report_id_reality_report",
        "reality_candidate",
        type_="foreignkey",
    )
    op.drop_column("reality_candidate", "report_id")
    op.drop_index("ix_external_content_ref_report", table_name="external_content_reference")
    op.drop_index("ix_external_content_ref_hash", table_name="external_content_reference")
    op.drop_table("external_content_reference")
    op.drop_index("ix_reality_confirmation_target", table_name="reality_confirmation")
    op.drop_index("ix_reality_confirmation_place_type", table_name="reality_confirmation")
    op.drop_table("reality_confirmation")
    op.drop_index("ix_observation_effort_place_time", table_name="observation_effort")
    op.drop_index("ix_observation_effort_animal", table_name="observation_effort")
    op.drop_table("observation_effort")
    op.drop_index("ix_reality_report_reporter", table_name="reality_report")
    op.drop_index("ix_reality_report_origin_moderation", table_name="reality_report")
    op.drop_table("reality_report")
