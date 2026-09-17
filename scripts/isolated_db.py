"""Provision a throwaway database for a non-production workload.

One script for the roles that need "drop it and build it again": `TEST`
(pytest / integration) and `E2E` (Playwright). `VISUAL` keeps its own reset
script because it has an extra job (deterministic demo seed before screenshots);
`REHEARSAL` keeps `rehearsal_db.py` because it clones production on purpose.

Every name goes through `app.db.safety`, so the refusal logic lives in exactly
one place. In particular the production database cannot be reached from here
even with `--db-name petaccess`: the guard refuses it, and the positive allowlist
refuses anything that is not a `petaccess_test*` / `petaccess_e2e*` name.

Usage::

    python scripts/isolated_db.py --role TEST --reset          # drop, create, migrate, seed
    python scripts/isolated_db.py --role TEST --ensure         # create only if missing
    python scripts/isolated_db.py --role E2E --reset --json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for extra in (str(ROOT / "scripts"), str(ROOT / "services" / "api")):
    if extra not in sys.path:
        sys.path.insert(0, extra)

from app.db.safety import (  # noqa: E402
    DatabaseRole,
    DatabaseSafetyError,
    RoleMismatchRefused,
    classify_database_name,
)

API_DIR = ROOT / "services" / "api"
SQLALCHEMY_DRIVER = "+psycopg"
DEFAULT_ADMIN_URL = "postgresql://petaccess:petaccess_dev_only@localhost:5432/postgres"

#: role -> (default database name, seed strategy)
ROLE_DEFAULTS: dict[DatabaseRole, tuple[str, str]] = {
    DatabaseRole.TEST: ("petaccess_test", "demo"),
    DatabaseRole.E2E: ("petaccess_e2e", "demo"),
}


def _fail(msg: str) -> None:
    print(f"isolated_db: {msg}", file=sys.stderr)
    raise SystemExit(1)


def admin_url() -> str:
    return os.environ.get("TEST_DB_ADMIN_URL", DEFAULT_ADMIN_URL)


def user_url(db_name: str) -> str:
    url = admin_url().rsplit("/", 1)[0] + f"/{db_name}"
    if SQLALCHEMY_DRIVER not in url.split("://", 1)[0]:
        url = url.replace("postgresql://", f"postgresql{SQLALCHEMY_DRIVER}://", 1)
    return url


def guard_name(db_name: str, role: DatabaseRole) -> None:
    """Refuse anything that is not the requested non-production role."""
    classified = classify_database_name(db_name)
    if classified is not role:
        raise RoleMismatchRefused(
            f"{db_name!r} 的角色是 {classified.value}，不是请求的 {role.value}。"
            f"本脚本只服务 {'/'.join(r.value for r in ROLE_DEFAULTS)}，且必须是正向白名单命中。"
        )


def database_exists(conn: Any, db_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("select 1 from pg_database where datname = %s", (db_name,))
        return cur.fetchone() is not None


def recreate(conn: Any, db_name: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = %s AND pid <> pg_backend_pid()",
            (db_name,),
        )
        cur.execute(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')
        cur.execute(f'CREATE DATABASE "{db_name}"')


def run(cmd: list[str], *, database_url: str, env_extra: dict[str, str]) -> None:
    env = {**os.environ, "DATABASE_URL": database_url, **env_extra}
    proc = subprocess.run(cmd, cwd=API_DIR, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        _fail(f"command failed ({proc.returncode}): {' '.join(cmd)}")
    if proc.stdout.strip():
        print("  " + proc.stdout.strip().replace("\n", "\n  "))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--role",
        required=True,
        type=str.lower,
        choices=[r.value.lower() for r in ROLE_DEFAULTS],
        help="目标角色（不区分大小写）",
    )
    ap.add_argument("--db-name", default=None)
    ap.add_argument("--reset", action="store_true", help="drop + create + migrate + seed")
    ap.add_argument("--ensure", action="store_true", help="create only when missing")
    ap.add_argument("--skip-seed", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    role = DatabaseRole(args.role.upper())
    default_name, default_seed = ROLE_DEFAULTS[role]
    db_name = args.db_name or default_name
    try:
        guard_name(db_name, role)
    except DatabaseSafetyError as exc:
        _fail(str(exc))

    if not (args.reset or args.ensure):
        args.ensure = True

    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        _fail(f"psycopg is not installed ({exc}); run this with the project venv")

    created = False
    with psycopg.connect(admin_url(), autocommit=True) as conn:
        exists = database_exists(conn, db_name)
        if args.reset and exists or not exists:
            recreate(conn, db_name)
            created = True
        recreated = args.reset or created

    url = user_url(db_name)
    queue = f"{db_name}"
    env_extra = {
        # §41/§42: a test worker must not consume production tasks, and the test
        # cache must not sit in the same Redis database as the resolver/monitor
        # state.
        "CELERY_TASK_QUEUE": queue,
        "REDIS_URL": os.environ.get("TEST_REDIS_URL", "redis://127.0.0.1:6379/1"),
        "APP_ENV": "test",
        "DB_ROLE": role.value,
    }
    if recreated:
        run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            database_url=url,
            env_extra=env_extra,
        )
        if not args.skip_seed and default_seed:
            run(
                [sys.executable, "-m", "app.db.seed", "--demo"],
                database_url=url,
                env_extra=env_extra,
            )

    info = {
        "role": role.value,
        "database": db_name,
        "recreated": recreated,
        "url": url,
        "alembic": "head",
        "seed": None if args.skip_seed else default_seed,
        "celery_task_queue": queue,
        "redis_url": env_extra["REDIS_URL"],
    }
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print(f"TARGET_DB = {db_name}")
        print(f"TARGET_DB_ROLE = {role.value}")
        print(f"recreated = {recreated}  seed = {info['seed']}")
        print(f"DATABASE_URL = {url}")
        print(f"CELERY_TASK_QUEUE = {queue}")
        print(f"REDIS_URL = {env_extra['REDIS_URL']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
