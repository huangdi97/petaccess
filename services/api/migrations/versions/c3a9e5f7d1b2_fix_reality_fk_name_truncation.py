"""fix_reality_fk_name_truncation

Revision ID: c3a9e5f7d1b2
Revises: 2c7ea6ca8e30
Create Date: 2026-09-22

R-01 (TECH_DEBT_REGISTER): the naming convention
``fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s`` produces

    fk_staff_response_observation_evidence_bundle_id_evidence_bundle

for ``staff_response_observation.evidence_bundle_id``, which is longer than
PostgreSQL's 63-char identifier limit (NAMEDATALEN - 1). PostgreSQL truncates
the name at creation time and appends a suffix, e.g.:

    fk_staff_response_observation_evidence_bundle_id_eviden_d504

The constraint semantics are unaffected (still
``evidence_bundle_id -> evidence_bundle.id ON DELETE SET NULL``), but the
non-deterministic name shows up as drift in ``alembic autogenerate``.

This migration is additive / idempotent:

- it renames the constraint to a deterministic, ≤63-char name;
- it does NOT modify the old migration (2c7ea6ca8e30);
- it does NOT drop data and does NOT change FK semantics;
- on a second run (or on a DB that already has the target name) it is a no-op.

The ORM model names the same FK explicitly so ``alembic autogenerate`` stops
reporting drift (see services/api/app/models/reality.py).

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3a9e5f7d1b2"
down_revision: str | None = "2c7ea6ca8e30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Deterministic, ≤63-char constraint name for the FK. Chosen under the same
#: convention shape (table_column_referred) but short enough to fit.
TARGET_FK_NAME = "fk_staff_response_observation_evidence_bundle"
TABLE = "staff_response_observation"


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    fk_names = [
        fk.get("name") for fk in inspector.get_foreign_keys(TABLE) if fk.get("name")
    ]
    if TARGET_FK_NAME in fk_names:
        # Already named deterministically — nothing to do.
        return
    # Match only the evidence_bundle FK. The convention-generated name is
    # ``fk_staff_response_observation_evidence_bundle_id_evidence_bundle``
    # (truncated by PostgreSQL to ``..._id_eviden_d504``); every other FK on
    # this table legitimately shares the ``fk_staff_response_observation``
    # prefix, so a broad ``startswith`` match would try to rename all of them
    # to the same target and fail. Scope to the evidence_bundle column.
    offenders = [
        n
        for n in fk_names
        if n
        and n.startswith("fk_staff_response_observation_evidence_bundle")
        and n != TARGET_FK_NAME
    ]
    if not offenders:
        # No FK on the table at all (fresh/odd DB) — nothing to rename. The
        # convention-generated name would be created on later migrations; this
        # migration stays a no-op for such databases.
        return
    for name in offenders:
        op.execute(
            f"ALTER TABLE {_quote(TABLE)} RENAME CONSTRAINT {_quote(name)} "
            f"TO {_quote(TARGET_FK_NAME)}"
        )


def downgrade() -> None:
    # Renaming back would re-introduce a >63-char name that PostgreSQL truncates
    # non-deterministically. R-01's fix is intentionally one-way; the previous
    # revision's constraint still exists (same semantics), so a downgrade of the
    # schema is available via the ordinary ``downgrade -1`` path of the parent
    # revisions. This step stays a no-op.
    pass
