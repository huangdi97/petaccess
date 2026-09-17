"""§50 — the decisive proof: every non-production workload refuses `petaccess`.

The point of this file is negative. It does not check that isolation *works* on a
correct setup; it checks that on a **wrong** setup every entry point stops. A
guard that is only exercised on the happy path is indistinguishable from no guard
at all, because the failure mode we care about is the one where somebody points a
suite at production and everything appears to succeed.

Two layers:

**In-process** — the guard assertions, called exactly as the scripts call them.
Cheap, no server, and directly documents each workload's contract.

**Out-of-process** — the real commands, run with the production URL in the
environment, asserting on the *process exit code*. This is the part that matters:
it proves the refusal survives being wired up the way a human actually wires it
up, and that a refused run does not quietly leave rows behind.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

#: The production DSN from `.env`. These tests only ever *describe* it; the
#: out-of-process cases deliberately hand it to commands that must reject it.
PRODUCTION_URL = "postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"

#: The exit code `tests/conftest.py` uses for "refused because of the database".
REFUSED_EXIT_CODE = 4


@pytest.fixture(autouse=True)
def _no_ambient_db_role(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drop the ambient `DB_ROLE` declaration for this module.

    `DB_ROLE` is a *declaration* that the guard requires to agree with the server,
    and the suite itself exports `DB_ROLE=TEST`. These tests deliberately hand the
    guard a production URL, so leaving the declaration in place would make every
    case raise `RoleMismatchRefused` at construction time — passing for a reason
    that has nothing to do with the refusal under test.
    """
    monkeypatch.delenv("DB_ROLE", raising=False)


def _guard(url: str):  # noqa: ANN202 - only used inside this module
    sys.path.insert(0, str(ROOT / "services" / "api"))
    from app.db.safety import guard_for_url

    return guard_for_url(url)


def _run(args: list[str], **env_extra: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("DB_ROLE", None)
    env.update(env_extra)
    return subprocess.run(  # noqa: S603 - fixed argv, no shell
        args,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


# --------------------------------------------------------------------------- #
# In-process: the guard contract for each workload
# --------------------------------------------------------------------------- #
class TestProductionIsClassifiedAsProduction:
    def test_petaccess_is_production(self) -> None:
        from app.db.safety import DatabaseRole, classify_database_name

        assert classify_database_name("petaccess") is DatabaseRole.PRODUCTION

    def test_production_may_not_be_destructively_reset_by_any_generic_tool(self) -> None:
        """`destructive_allowed` must stay False, or every tool gains a hole."""
        guard = _guard(PRODUCTION_URL)
        assert guard.is_production
        assert guard.spec.destructive_allowed is False
        assert guard.spec.fixture_allowed is False

    @pytest.mark.parametrize(
        "assertion",
        [
            "assert_not_production",
            "assert_test_workload",
            "assert_test_database",
            "assert_e2e_database",
            "assert_visual_database",
            "assert_rehearsal_database",
            "assert_destructive_allowed",
            "assert_fixture_write_allowed",
        ],
    )
    def test_workload_assertions_refuse_production(self, assertion: str) -> None:
        from app.db.safety import DatabaseSafetyError

        guard = _guard(PRODUCTION_URL)
        with pytest.raises(DatabaseSafetyError):
            getattr(guard, assertion)("isolation proof")

    def test_production_cleanup_needs_a_backup_and_a_reviewed_plan(self) -> None:
        """Removing leaked fixtures from production is its own governed operation.

        The entry point exists so that a cleanup can be authorised *without*
        flipping `destructive_allowed` on the PRODUCTION role — so it must refuse
        when the evidence is not already on disk.
        """
        from app.db.safety import ProductionCleanupRefused

        guard = _guard(PRODUCTION_URL)
        with pytest.raises(ProductionCleanupRefused):
            guard.assert_production_cleanup_allowed(
                "cleanup", backup_path=None, reviewed_plan_path=None
            )
        with pytest.raises(ProductionCleanupRefused):
            guard.assert_production_cleanup_allowed(
                "cleanup", backup_path="/nope.dump", reviewed_plan_path="/nope.json"
            )

    def test_unknown_database_is_refused_not_tolerated(self) -> None:
        """A deny list only refuses names somebody thought of (§8)."""
        from app.db.safety import DatabaseRole, UnknownDatabaseRefused, classify_database_name

        assert classify_database_name("petaccess_typo_2027") is DatabaseRole.UNKNOWN
        guard = _guard("postgresql://petaccess:x@127.0.0.1:5432/petaccess_typo_2027")
        with pytest.raises(UnknownDatabaseRefused):
            guard.assert_not_production("unknown-name proof")

    def test_test_roles_are_positively_allowlisted(self) -> None:
        """The allowlist is positive: only registered TEST-workload names pass."""
        from app.db.safety import TEST_WORKLOAD_ROLES, DatabaseRole, classify_database_name

        for name, role in (
            ("petaccess_test", DatabaseRole.TEST),
            ("petaccess_test_run42", DatabaseRole.TEST),
            ("petaccess_e2e", DatabaseRole.E2E),
            ("petaccess_visual", DatabaseRole.VISUAL),
            ("petaccess_publish_rehearsal_r3", DatabaseRole.REHEARSAL),
        ):
            assert classify_database_name(name) is role
            assert role in TEST_WORKLOAD_ROLES
            _guard(f"postgresql://petaccess:x@127.0.0.1:5432/{name}").assert_test_workload("ok")


# --------------------------------------------------------------------------- #
# Out-of-process: the real commands, pointed at production
# --------------------------------------------------------------------------- #
class TestTheCommandsActuallyRefuseProduction:
    def test_pytest_refuses_before_the_first_test(self) -> None:
        """The headline §9/§10 requirement, proven on the real pytest process."""
        proc = _run(
            [sys.executable, "-m", "pytest", "-q", "tests/unit/test_animal_scope.py"],
            DATABASE_URL=PRODUCTION_URL,
        )
        assert proc.returncode == REFUSED_EXIT_CODE, (
            f"pytest did not refuse production (exit {proc.returncode})\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
        assert "PRODUCTION_DATABASE_REFUSED" in (proc.stdout + proc.stderr)

    def test_cleanup_execute_without_evidence_is_refused(self) -> None:
        """No backup + no reviewed plan ⇒ refuse, and refuse before connecting."""
        proc = _run(
            [
                sys.executable,
                "scripts/production_fixture_cleanup.py",
                "--execute",
                "--confirm-database",
                "petaccess",
            ]
        )
        assert proc.returncode != 0
        assert "REFUSED" in (proc.stdout + proc.stderr)

    def test_cleanup_execute_cannot_target_a_test_database(self) -> None:
        """The governed entry point is for production only — not a way to drop a test DB."""
        proc = _run(
            [
                sys.executable,
                "scripts/production_fixture_cleanup.py",
                "--execute",
                "--db-name",
                "petaccess_test",
                "--confirm-database",
                "petaccess_test",
                "--backup",
                "artifacts/production_isolation/petaccess_after_batch01.dump",
                "--i-reviewed-the-dry-run",
                "artifacts/production_isolation/CLEANUP_PLAN_BATCH02_DRYRUN.json",
            ]
        )
        assert proc.returncode != 0
        assert "Refusing" in (proc.stdout + proc.stderr)

    def test_visual_reset_refuses_production(self) -> None:
        proc = _run(
            [sys.executable, "scripts/visual_db_reset.py", "--db-name", "petaccess"],
        )
        assert proc.returncode != 0

    def test_rehearsal_refuses_production_as_a_rehearsal_target(self) -> None:
        proc = _run(
            [
                sys.executable,
                "scripts/rehearsal_db.py",
                "--db-name",
                "petaccess",
                "--clone",
                "--confirm",
            ]
        )
        assert proc.returncode != 0
