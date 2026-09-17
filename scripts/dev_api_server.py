"""Run the API against a chosen database without ever exporting a credential.

Rehearsal needs the *same* application pointed at a *different* database. The
usual way to do that is ``export DATABASE_URL=...`` in a shell — which puts the
password into the shell history, the process listing and every log line that
echoes its environment. This launcher instead reads ``.env`` in-process, swaps the
database name, and never prints or exports the secret.

It is also the one place that decides whether an API process is *allowed* to
serve a given database (§17: production must be an explicit opt-in, never a
default). Two rules:

* the target's role is probed from the server, not parsed from the URL;
* ``petaccess`` cannot be served without ``--production-confirm``, and a
  ``--role`` that disagrees with the live database is refused outright.

Usage::

    python scripts/dev_api_server.py --db-name petaccess_dev --port 8010
    python scripts/dev_api_server.py --db-name petaccess_e2e --role E2E --port 8010
    python scripts/dev_api_server.py --db-name petaccess_publish_rehearsal_r3 --port 8010
    python scripts/dev_api_server.py --port 8011 --production-confirm   # .env DB, explicit
"""

import argparse
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
API_DIR = REPO / "services" / "api"
for extra in (str(REPO / "scripts"), str(API_DIR)):
    if extra not in sys.path:
        sys.path.insert(0, extra)

from app.db.safety import (  # noqa: E402
    DatabaseRole,
    DatabaseSafetyError,
)


def database_url_for(db_name: str | None) -> str | None:
    """The repo's DATABASE_URL, repointed at ``db_name`` when one is given."""
    env_file = REPO / ".env"
    if not env_file.exists():
        return None
    match = re.search(r"^DATABASE_URL=(.*)$", env_file.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        return None
    url = match.group(1).strip()
    if db_name:
        url = re.sub(r"/[^/?]+$", f"/{db_name}", url)
    return url


def psycopg_url_for(db_name: str | None) -> str | None:
    """Same URL, driver-less, for callers that speak libpq rather than SQLAlchemy.

    ``psycopg.connect`` rejects ``postgresql+psycopg://`` outright ("missing '='
    after ..."), because the ``+driver`` suffix is a SQLAlchemy convention.
    """
    url = database_url_for(db_name)
    return url.replace("postgresql+psycopg://", "postgresql://", 1) if url else None


def probe_role(url: str) -> tuple[str, DatabaseRole]:
    """Ask the server which database this URL really points at."""
    import psycopg

    from app.db.safety import guard_for_psycopg

    with psycopg.connect(url, connect_timeout=5) as conn:
        guard = guard_for_psycopg(conn)
    return guard.database_name, guard.role


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8010)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--db-name", default=None, help="覆盖 .env 中的库名（不改文件）")
    ap.add_argument("--log-level", default="warning")
    ap.add_argument(
        "--role",
        default=None,
        help="断言目标库角色（TEST/E2E/VISUAL/REHEARSAL/DEVELOPMENT），不符即拒绝启动",
    )
    ap.add_argument(
        "--production-confirm",
        action="store_true",
        help="显式确认：允许把 API 指向 PRODUCTION（petaccess）。默认拒绝。",
    )
    args = ap.parse_args()

    url = database_url_for(args.db_name)
    if url is None:
        print("未找到 .env 中的 DATABASE_URL，使用应用默认设置。", file=sys.stderr)
    else:
        target = url.rsplit("/", 1)[-1]
        # Print the database name only — the URL carries the password.
        print(f"API -> database {target} on {args.host}:{args.port}")
        os.environ["DATABASE_URL"] = url

    try:
        # psycopg needs the libpq form: handing it the SQLAlchemy DSN raises
        # "missing \"=\" after ..." and the server refuses to start, which is a
        # confusing way to discover a driver-suffix mismatch.
        live_name, role = probe_role(psycopg_url_for(args.db_name) or "")
    except DatabaseSafetyError:
        raise
    except Exception as exc:  # noqa: BLE001
        print(
            f"REFUSED — 无法连接目标库以确认角色（{type(exc).__name__}: {exc}）。\n"
            "  没有服务端事实就无法证明 API 指向哪里，因此拒绝启动。",
            file=sys.stderr,
        )
        return 3

    print(f"TARGET_DB = {live_name}")
    print(f"TARGET_DB_ROLE = {role.value}")

    if args.role:
        wanted = DatabaseRole(args.role.strip().upper())
        if role is not wanted:
            print(
                f"REFUSED — --role {wanted.value} 与实际库角色 {role.value} 不一致"
                f"（{live_name!r}）。",
                file=sys.stderr,
            )
            return 3

    if role is DatabaseRole.PRODUCTION and not args.production_confirm:
        print(
            "REFUSED — 目标库是 PRODUCTION（petaccess）。\n"
            "  正式库只能由人工授权的 publish 改写；一个可写 API 指向它必须是显式选择。\n"
            "  调试请用： --db-name petaccess_dev\n"
            "  E2E 请用： --db-name petaccess_e2e --role E2E\n"
            "  确实需要，请显式加 --production-confirm。",
            file=sys.stderr,
        )
        return 3

    os.environ["DB_ROLE"] = role.value
    sys.path.insert(0, str(API_DIR))
    os.chdir(API_DIR)

    import uvicorn

    uvicorn.run("app.main:app", host=args.host, port=args.port, log_level=args.log_level)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
