"""access_rule.mandatory_level — normative force becomes first-class (BLK-LAYER-02)

Revision ID: e3b7a1c4f920
Revises: d1a4f7c93b28
Create Date: 2026-09-14

BLK-LAYER-02: ``AccessRule`` had no ``mandatory_level`` column, so every
DB-sourced LEGAL rule fell into the resolver's ``legal_other`` bucket
(``v05_resolver.py``) and was excluded from the governing set whenever any
non-legal rule applied. A venue operator's "allowed" rule could therefore
outvote 《上海市养犬管理条例》第二十三条's statutory prohibition.

The fix (ADR-023) makes normative force a first-class, reviewer-controlled
field on the candidate → publish path:

  * ``rule_candidate.mandatory_level`` — declared during review
  * ``access_rule.mandatory_level``    — carried through publish() verbatim

Vocabulary: ``mandatory`` | ``advisory`` | ``operator_discretion``.
NULL is preserved as "not declared"; the resolver NEVER reads NULL as
mandatory, and the publish gate refuses a LEGAL candidate that leaves it blank.

Additive + idempotent:
  * both columns are nullable (no existing row changes meaning);
  * the backfill only touches rows where ``mandatory_level IS NULL`` and maps
    LEGAL → mandatory, any other known layer → operator_discretion, legacy
    NULL layer → NULL (the resolver already flags those REVIEW_REQUIRED);
  * the legacy spelling ``discretionary`` is normalised to
    ``operator_discretion``;
  * re-running the migration is a no-op.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e3b7a1c4f920"
down_revision: str | None = "d1a4f7c93b28"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_LEVELS = "'mandatory','advisory','operator_discretion','discretionary'"

#: idempotent: only fills NULLs; deterministic from rule_layer (never guesses
#: for a legacy NULL layer — that stays NULL so the resolver keeps flagging it)
_BACKFILL = sa.text(
    """
    UPDATE {table}
       SET mandatory_level = CASE
             WHEN rule_layer = 'LEGAL' THEN 'mandatory'
             WHEN rule_layer IS NULL THEN NULL
             ELSE 'operator_discretion'
           END
     WHERE mandatory_level IS NULL
    """
)

_NORMALIZE = sa.text(
    """
    UPDATE {table}
       SET mandatory_level = 'operator_discretion'
     WHERE mandatory_level = 'discretionary'
    """
)


def upgrade() -> None:
    for table in ("access_rule", "rule_candidate"):
        op.add_column(table, sa.Column("mandatory_level", sa.String(length=20), nullable=True))
        op.execute(_NORMALIZE.text.format(table=table))
        op.execute(_BACKFILL.text.format(table=table))
        # op.f() marks the name as already-final: without it the metadata naming
        # convention (ck_%(table_name)s_%(constraint_name)s) would prefix it a
        # second time, producing ck_access_rule_ck_access_rule_mandatory_level —
        # a name that diverges from the one the model declares.
        op.create_check_constraint(
            op.f(f"ck_{table}_mandatory_level"),
            table,
            f"mandatory_level IS NULL OR mandatory_level IN ({_LEVELS})",
        )


def downgrade() -> None:
    for table in ("rule_candidate", "access_rule"):
        op.drop_constraint(op.f(f"ck_{table}_mandatory_level"), table, type_="check")
        op.drop_column(table, "mandatory_level")
