"""Jurisdiction-level statutory proviso (ADR-030).

Revision ID: f2a1c7d9e034
Revises: c9d4e2a17b30
Create Date: 2026-09-18

Purely additive: one new table, no existing row or column is touched.

Why it exists
-------------
《上海市养犬管理条例》第二十三条 prohibits dogs from entering malls, museums,
restaurants and similar venues and then adds 「盲人携带导盲犬的，不受本条规定的
限制。」 That proviso is part of the *instrument*, not of any one venue. The only
carve-out model the platform had, ``rule_exception``, binds to a single
``rule_id`` — so every new LEGAL dog prohibition had to be given its own copy of
the proviso, and until it was, a guide-dog query resolved ``prohibited`` while
citing the very statute that exempts it.

``jurisdiction_exception`` stores the proviso once and binds it to every LEGAL
prohibition **grounded in the same instrument**, via the explicitly declared
``instrument_source_ids`` list (the same statute has two ``source`` rows in this
database, and different venues cite different ones — instrument identity is an
editorial determination, declared and reviewed, never inferred).

Fail-closed by construction: rows default to ``status='proposed'`` and
``review_status='not_reviewed'``, and only ``current`` + ``reviewed_active`` is
ever applied. Nothing in this migration activates a proviso.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2a1c7d9e034"
down_revision: str | None = "c9d4e2a17b30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jurisdiction_exception",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("jurisdiction_level", sa.String(16), nullable=False),
        sa.Column("jurisdiction_id", sa.String(64), nullable=False),
        sa.Column("authority", sa.String(200), nullable=False),
        sa.Column("instrument_type", sa.String(64), nullable=False),
        sa.Column("document_name", sa.String(300), nullable=False),
        sa.Column("clause_ref", sa.String(64), nullable=True),
        sa.Column("proviso_text_ref", sa.String(512), nullable=True),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column("binding", sa.String(16), nullable=False, server_default="instrument"),
        sa.Column("instrument_source_ids", sa.JSON(), nullable=False),
        sa.Column("applies_to_layer", sa.String(24), nullable=True),
        sa.Column("applies_to_effects", sa.JSON(), nullable=False),
        sa.Column("animal_scope", sa.String(20), nullable=False),
        sa.Column("subject_scope_normalized", sa.String(40), nullable=True),
        sa.Column("normalization_type", sa.String(40), nullable=True),
        sa.Column("normative_effect", sa.String(40), nullable=True),
        sa.Column("holder_scope", sa.String(32), nullable=True),
        sa.Column("action", sa.String(24), nullable=True),
        sa.Column("effect", sa.String(16), nullable=True),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="proposed"),
        sa.Column("review_status", sa.String(40), nullable=False, server_default="not_reviewed"),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_jur_exc_geo",
        "jurisdiction_exception",
        ["jurisdiction_level", "jurisdiction_id"],
    )
    op.create_index("ix_jur_exc_review", "jurisdiction_exception", ["review_status"])


def downgrade() -> None:
    op.drop_index("ix_jur_exc_review", table_name="jurisdiction_exception")
    op.drop_index("ix_jur_exc_geo", table_name="jurisdiction_exception")
    op.drop_table("jurisdiction_exception")
