"""Reset the throwaway database the visual-regression suite runs against.

Why this exists
---------------
Visual baselines are only meaningful if the thing being photographed is the
same every time. The dev database is not: the audit log, the candidate queue
and the observation list all grow monotonically, so a full-page baseline of
`/admin/audit` taken yesterday is already wrong today.

That is not a theoretical concern. Re-running the committed 47 baselines in
compare mode produced 8 failures, *all* of them admin list pages:

    admin-rule-candidates   90644 px different (ratio 0.03)
    admin-sources           height 839 -> 843
    admin-regulations       height 3040 -> 3334
    admin-audit             height 7471 -> 7452, and 130871 -> 130890 at 768px

The audit baseline alone is 130k pixels tall, and it times out at 20s rather
than diffing. A baseline that changes on every run does not detect regressions
— it just produces noise, and noise gets ignored.

So the suite gets its own database, dropped and re-seeded from the fixed demo
dataset before every run. Both the `--update-snapshots` run and the compare run
then start from byte-identical state, which is the property that makes a diff
mean something.

This NEVER touches the dev/pilot database. The database name is fixed
(`petaccess_visual`) and the script refuses to run against anything else,
because `run_demo_seed()` clears the candidate, dispute and audit tables —
running it on the wrong database would destroy governed data.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "services" / "api"

DEFAULT_ADMIN_URL = "postgresql://petaccess:petaccess_dev_only@localhost:5432/postgres"
DB_NAME = "petaccess_visual"

# `postgresql://` is enough for psycopg3 (used to drop/create above), but
# SQLAlchemy still resolves a driver-less URL to psycopg2, which is not
# installed. Alembic and the app both go through SQLAlchemy, so they need the
# driver named explicitly.
SQLALCHEMY_DRIVER = "+psycopg"

# Guard: `run_demo_seed()` truncates governed tables. If this ever points at the
# real database the loss is not recoverable from here.
FORBIDDEN_DB_NAMES = {"petaccess", "petaccess_dev", "petaccess_pilot", "postgres", "template1"}


def _fail(msg: str) -> None:
    print(f"visual_db_reset: {msg}", file=sys.stderr)
    raise SystemExit(1)


def recreate_database(admin_url: str, db_name: str) -> None:
    """Drop and recreate `db_name`, terminating any open connections first."""
    if db_name in FORBIDDEN_DB_NAMES:
        _fail(f"refusing to reset protected database {db_name!r}")

    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - environment problem, not logic
        _fail(f"psycopg is not installed ({exc}); run this with the project venv")

    # `DROP DATABASE ... WITH (FORCE)` needs PG13+; the compose image is 17.
    with psycopg.connect(admin_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (db_name,),
            )
            cur.execute(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')
            cur.execute(f'CREATE DATABASE "{db_name}"')
    print(f"visual_db_reset: recreated database {db_name}")


def run(cmd: list[str], *, database_url: str) -> None:
    """Run `cmd` in the API package with DATABASE_URL pointed at the visual DB."""
    env = {**os.environ, "DATABASE_URL": database_url}
    proc = subprocess.run(cmd, cwd=API_DIR, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        _fail(f"command failed ({proc.returncode}): {' '.join(cmd)}")
    if proc.stdout.strip():
        print(proc.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--admin-url", default=os.environ.get("VISUAL_DB_ADMIN_URL", DEFAULT_ADMIN_URL))
    parser.add_argument("--db-name", default=os.environ.get("VISUAL_DB_NAME", DB_NAME))
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="migrate only, leaving the new database empty",
    )
    args = parser.parse_args()

    db_name = args.db_name
    user_url = args.admin_url.rsplit("/", 1)[0] + f"/{db_name}"
    if SQLALCHEMY_DRIVER not in user_url.split("://", 1)[0]:
        user_url = user_url.replace("postgresql://", f"postgresql{SQLALCHEMY_DRIVER}://", 1)
    py = sys.executable

    recreate_database(args.admin_url, db_name)
    run([py, "-m", "alembic", "upgrade", "head"], database_url=user_url)
    if not args.skip_seed:
        run([py, "-m", "app.db.seed", "--demo"], database_url=user_url)
    print(f"visual_db_reset: {db_name} is ready at {user_url}")


if __name__ == "__main__":
    main()
