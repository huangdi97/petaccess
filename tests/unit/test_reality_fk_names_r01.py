"""R-01 — Reality FK names must be deterministic and fit PostgreSQL's 63-char limit.

PostgreSQL identifiers are limited to NAMEDATALEN - 1 = 63 characters; a longer
name is silently truncated with a non-deterministic suffix, which shows up as
drift in ``alembic autogenerate`` (and in any tool that names constraints by
convention). The original Reality migration (2c7ea6ca8e30) generated

    fk_staff_response_observation_evidence_bundle_id_evidence_bundle   (64 chars)

for ``staff_response_observation.evidence_bundle_id``. R-01 fixes it with an
additive/idempotent migration (c3a9e5f7d1b2) plus an explicit ORM name.

These tests lock the invariant so the defect cannot return:

* every Reality-table FK name is ≤ 63 chars;
* the evidence_bundle FK on staff_response_observation has the deterministic
  name the migration renames it to;
* the ORM name and the migration's TARGET_FK_NAME agree (no drift between
  model metadata and migration intent).
"""

from __future__ import annotations

from pathlib import Path

from app.models.reality import (
    AnimalFacility,
    ObservedPresence,
    RealityCandidate,
    StaffResponseObservation,
)

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "services" / "api" / "migrations" / "versions"

#: PostgreSQL identifier limit (NAMEDATALEN - 1).
POSTGRES_MAX_IDENTIFIER = 63

REALITY_MODELS = (
    RealityCandidate,
    ObservedPresence,
    StaffResponseObservation,
    AnimalFacility,
)


def _all_fk_names(model) -> list[str]:
    """Collect every explicit/convention FK name on the model's table."""
    names: list[str] = []
    table = model.__table__
    for fk in table.foreign_key_constraints:
        name = fk.name
        if name:
            names.append(name)
        else:
            # Columns without an explicit constraint name use the convention.
            for col in fk.columns:
                if col.name == "evidence_bundle_id":
                    names.append(f"fk_{table.name}_evidence_bundle_id_evidence_bundle")
    return names


def test_every_reality_fk_name_fits_postgres_identifier_limit() -> None:
    offenders: list[str] = []
    for model in REALITY_MODELS:
        for name in _all_fk_names(model):
            if len(name) > POSTGRES_MAX_IDENTIFIER:
                offenders.append(f"{model.__tablename__}.{name} ({len(name)} chars)")
    assert not offenders, (
        "Reality FK names must stay within PostgreSQL's 63-char limit; "
        "longer names get truncated non-deterministically (R-01). Offenders: "
        + "; ".join(offenders)
    )


def test_staff_response_evidence_bundle_fk_has_deterministic_name() -> None:
    """R-01: the exact FK that exceeded the limit now carries the fixed name."""
    table = StaffResponseObservation.__table__
    fk = next(
        fk
        for fk in table.foreign_key_constraints
        if any(col.name == "evidence_bundle_id" for col in fk.columns)
    )
    assert fk.name == "fk_staff_response_observation_evidence_bundle"
    assert len(fk.name) <= POSTGRES_MAX_IDENTIFIER


def test_orm_name_matches_migration_target_name() -> None:
    """The ORM metadata and the fix migration must agree on the final name."""
    migration = (MIGRATIONS / "c3a9e5f7d1b2_fix_reality_fk_name_truncation.py").read_text(
        encoding="utf-8"
    )
    assert 'TARGET_FK_NAME = "fk_staff_response_observation_evidence_bundle"' in migration
    table = StaffResponseObservation.__table__
    fk = next(
        fk
        for fk in table.foreign_key_constraints
        if any(col.name == "evidence_bundle_id" for col in fk.columns)
    )
    assert fk.name == "fk_staff_response_observation_evidence_bundle"


def test_all_reality_foreign_keys_use_ondelete_semantics() -> None:
    """Every Reality FK keeps its designed ondelete action (R-01 must not change it)."""
    expected: dict[str, str] = {
        "reality_candidate": {
            "report_id": "SET NULL",
            "place_id": "CASCADE",
            "zone_id": "SET NULL",
            "source_id": "SET NULL",
            "evidence_bundle_id": "SET NULL",
        },
        "observed_presence": {
            "candidate_id": "RESTRICT",
            "place_id": "CASCADE",
            "zone_id": "SET NULL",
            "source_id": "SET NULL",
            "evidence_bundle_id": "SET NULL",
        },
        "staff_response_observation": {
            "candidate_id": "RESTRICT",
            "place_id": "CASCADE",
            "zone_id": "SET NULL",
            "source_id": "SET NULL",
            "evidence_bundle_id": "SET NULL",
        },
        "animal_facility": {
            "candidate_id": "RESTRICT",
            "place_id": "CASCADE",
            "zone_id": "SET NULL",
            "source_id": "SET NULL",
            "evidence_bundle_id": "SET NULL",
        },
    }
    for model in REALITY_MODELS:
        table = model.__table__
        for fk in table.foreign_key_constraints:
            col = next(iter(fk.columns)).name
            want = expected[table.name][col]
            assert fk.ondelete == want, (
                f"{table.name}.{col} ondelete={fk.ondelete}, expected {want} "
                "(R-01 fix must not change FK semantics)"
            )
