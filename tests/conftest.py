"""Repository-root pytest guard: the suite may never touch the production database.

Why this file exists
--------------------
`petaccess` is production data — it holds the objects published by
R2-FINAL-R3-BATCH-01B and a human signature. It is also where this repository's
`.env` points, and pytest resolves its connection from there. A full QA run once
left 28 stray access rules, 4 stray exceptions and a pile of `回滚测试场所*`
places behind, because nothing in the suite asked *which* database it had been
handed.

This conftest runs before anything else and refuses to start unless the server
itself confirms the connection is a disposable test database. It is a
`pytest_sessionstart` hook rather than a fixture on purpose: a fixture runs when
a test requests it, which is already too late — the first integration test would
have written its fixture before the check fired.

The rules (§9/§10/§50):

* role `TEST` — the only role a pytest run may use.
* anything else, including `PRODUCTION` and any unregistered name, aborts the
  whole suite *before the first test executes*.
* the role is read from `SELECT current_database()`, never inferred from the URL,
  because the URL can be stale, inherited, or simply wrong about where it points.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
API_DIR = ROOT / "services" / "api"
for extra in (str(API_DIR), str(ROOT / "scripts")):
    if extra not in sys.path:
        sys.path.insert(0, extra)

from app.db.safety import (  # noqa: E402
    DatabaseRole,
    DatabaseSafetyError,
    database_name_from_url,
    describe_roles,
)

#: Exit code for "refused to start because of the database". Distinct from 1
#: (test failures) and 3 (pytest internal error) so tooling can tell them apart.
REFUSED_EXIT_CODE = 4

#: The only role pytest is allowed to run against.
REQUIRED_ROLE = DatabaseRole.TEST

_MESSAGE = """\
================================================================================
 {headline}
================================================================================
DATABASE_URL resolves to : {resolved_name}  ({role})
current_database()       : {live_name}
pytest requires          : {required}

{detail}

Production is read-only for this suite. Provision a disposable database first:

    python scripts/isolated_db.py --role TEST --reset
    DATABASE_URL=postgresql+psycopg://petaccess:petaccess_dev_only@localhost:5432/petaccess_test \\
      .venv/Scripts/python.exe -m pytest -q

See docs/engineering/DATABASE_ENVIRONMENT_MODEL.md and
docs/engineering/TEST_DATABASE_ISOLATION.md.
================================================================================
"""


def _database_url() -> str:
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    from app.core.config import get_settings

    return get_settings().database_url


def _probe(url: str) -> tuple[str, DatabaseRole]:
    """Ask the server. Falls back to the URL only when the server is unreachable."""
    import psycopg

    from app.db.safety import classify_database_name, guard_for_psycopg

    libpq = url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(libpq, connect_timeout=5) as conn:
        guard = guard_for_psycopg(conn)
        return guard.database_name, classify_database_name(guard.database_name)


def pytest_sessionstart(session: pytest.Session) -> None:  # noqa: ARG001 - hook signature
    url = _database_url()
    resolved = database_name_from_url(url)
    from app.db.safety import classify_database_name

    resolved_role = classify_database_name(resolved)

    try:
        live_name, live_role = _probe(url)
    except DatabaseSafetyError:
        raise
    except Exception as exc:  # noqa: BLE001 - any connect failure has the same remedy
        pytest.exit(
            _MESSAGE.format(
                headline="PYTEST DATABASE UNREACHABLE",
                resolved_name=resolved,
                role=resolved_role.value,
                live_name=f"<unreachable: {type(exc).__name__}>",
                required=REQUIRED_ROLE.value,
                detail=(
                    "The database could not be reached, so the suite cannot prove where\n"
                    "it would be writing. Start the stack (docker compose up -d) and\n"
                    "provision the test database, then re-run."
                ),
            ),
            returncode=REFUSED_EXIT_CODE,
        )
        return

    if live_role is REQUIRED_ROLE:
        print(f"\n[pytest-guard] TARGET_DB = {live_name}  TARGET_DB_ROLE = {live_role.value}\n")
        return

    if live_role is DatabaseRole.PRODUCTION:
        headline = "PRODUCTION_DATABASE_REFUSED — pytest will not run against petaccess"
        detail = (
            "This is the database that carries the real published rules and the human\n"
            "signature. Fixtures, rollbacks and supersession drills write rows; on\n"
            "production those rows are indistinguishable from governed data."
        )
    elif live_role is DatabaseRole.UNKNOWN:
        headline = "UNKNOWN_DATABASE_REFUSED — pytest requires a positively allowlisted database"
        detail = (
            "A deny list can only refuse names somebody thought of. Only names that\n"
            f"match the {REQUIRED_ROLE.value} role's patterns are accepted; unregistered\n"
            "names are refused rather than tolerated.\n\nRegistered roles:\n"
            + "\n".join(
                f"  {row['role']:<14} {row['canonical_name']:<32} {row['purpose']}"
                for row in describe_roles()
            )
        )
    else:
        headline = f"WRONG_DATABASE_ROLE_REFUSED — pytest requires {REQUIRED_ROLE.value}"
        detail = (
            f"The connection is a real {live_role.value} database, which is fine for other\n"
            "workloads but not for pytest: this suite creates and deletes business rows.\n"
            "Use the TEST database instead."
        )

    pytest.exit(
        _MESSAGE.format(
            headline=headline,
            resolved_name=resolved,
            role=resolved_role.value,
            live_name=live_name,
            required=REQUIRED_ROLE.value,
            detail=detail,
        ),
        returncode=REFUSED_EXIT_CODE,
    )
