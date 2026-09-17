"""Create, clone and drop the publish rehearsal database — under a name guard.

The rule this enforces (Master Goal §10 / ROLLBACK_RUNBOOK.md): *the first real
``--execute`` is never rehearsed against a database anyone depends on.* Not the
real one, not the pilot one, not the visual-regression one, not a development
database that happens to be lying around. The rehearsal target is a purpose-named
clone that can be dropped and rebuilt at will.

Two independent guards, because one is not enough:

* **FORBIDDEN** — an explicit deny list. Those names are refused even with
  ``--confirm``; there is no override.
* **ALLOWLIST PATTERN** — the name must match ``petaccess_publish_rehearsal_*``.
  Anything else is refused. This is the guard that matters: the incident this
  round is cleaning up happened because an unknown name was *accepted*, not
  because a known one was.

Cloning uses ``CREATE DATABASE ... TEMPLATE``, a physical copy — schema, data,
PostGIS geometry columns, the alembic stamp and every row of governed history,
byte for byte. ``pg_dump``/``pg_restore`` is the alternative and is not
equivalent: extension-owned tables such as ``spatial_ref_sys`` are not dumped,
so a restore silently produces a database that is *nearly* the same. A rehearsal
that runs against "nearly the same" proves nothing about the real one.

Usage:
    python scripts/rehearsal_db.py --db-name petaccess_publish_rehearsal_r3
    python scripts/rehearsal_db.py --db-name petaccess_publish_rehearsal_r3 --clone --confirm
    python scripts/rehearsal_db.py --db-name petaccess_publish_rehearsal_r3 --fingerprint
    python scripts/rehearsal_db.py --db-name petaccess_publish_rehearsal_r3 --drop --confirm
"""

# NOTE: no ``from __future__ import annotations`` — see scripts/publish_reviewed_r1.py.

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
for _extra in (str(REPO / "scripts"), str(REPO / "services" / "api")):
    if _extra not in sys.path:
        sys.path.insert(0, _extra)

from app.db.safety import DatabaseRole, classify_database_name  # noqa: E402

#: Databases that may serve as the clone *source*. Read-only from here.
ALLOWED_SOURCE_DB_NAMES = frozenset({"petaccess"})

CONTAINER = "petaccess-db-1"

#: Tables whose counts identify the rehearsal database's state.
FINGERPRINT_TABLES = (
    "place",
    "zone",
    "access_rule",
    "rule_exception",
    "rule_candidate",
    "evidence_bundle",
    "source",
    "source_artifact",
    "audit_log",
)


class GuardRefused(Exception):
    """The requested name is not one this tool may touch."""


def check_name(db_name: str) -> None:
    """The rehearsal target must classify as REHEARSAL — nothing else may be touched.

    This used to be a `FORBIDDEN_DB_NAMES` deny list next to a local allowlist
    regex. The list is gone: `app.db.safety` is now the only place that decides
    what a database name means, so a new script cannot invent a second opinion.
    """
    role = classify_database_name(db_name)
    if role is not DatabaseRole.REHEARSAL:
        raise GuardRefused(
            f"{db_name!r} 的角色是 {role.value}，不是 REHEARSAL；"
            "本工具只操作 petaccess_publish_rehearsal_* 形状的重建库"
        )


def check_source_name(source: str) -> None:
    """Only the real production database may be cloned from — and only read."""
    if source not in ALLOWED_SOURCE_DB_NAMES:
        raise GuardRefused(f"克隆源 {source!r} 不在允许名单 {sorted(ALLOWED_SOURCE_DB_NAMES)} 中")
    if classify_database_name(source) is not DatabaseRole.PRODUCTION:
        raise GuardRefused(f"克隆源 {source!r} 的角色不是 PRODUCTION，拒绝克隆")


def admin_url() -> str:
    """Admin connection URL derived from the repo `.env` (password never printed)."""
    url = (REPO / ".env").read_text(encoding="utf-8") if (REPO / ".env").exists() else ""
    password, user, host, port = "", "petaccess", "127.0.0.1", "5432"
    for line in url.splitlines():
        if line.startswith("POSTGRES_PASSWORD="):
            password = line.split("=", 1)[1].strip()
        elif line.startswith("DATABASE_URL="):
            value = line.split("=", 1)[1].strip()
            if "@" in value:
                hostport = value.rsplit("@", 1)[1].split("/", 1)[0]
                host, _, port = hostport.partition(":")
                host = host or "127.0.0.1"
                port = port or "5432"
    return f"postgresql://{user}:{password}@{host}:{port}/postgres"


def db_url_for(db_name: str) -> str:
    base = admin_url().rsplit("/", 1)[0]
    return f"{base}/{db_name}"


def _connect(url: str):  # pragma: no cover - environment dependent
    import psycopg

    return psycopg.connect(url, autocommit=True)


def exists(db_name: str) -> bool:  # pragma: no cover
    with _connect(admin_url()) as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        return cur.fetchone() is not None


def other_connections(db_name: str) -> int:  # pragma: no cover
    """Backends connected to `db_name` other than this one."""
    with _connect(admin_url()) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
            (db_name,),
        )
        return int(cur.fetchone()[0])


def terminate_connections(db_name: str) -> int:  # pragma: no cover
    with _connect(admin_url()) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity"
            " WHERE datname = %s AND pid <> pg_backend_pid()",
            (db_name,),
        )
        return len(cur.fetchall())


def fingerprint(db_name: str) -> dict[str, Any]:  # pragma: no cover
    """Row counts plus the alembic stamp — what "this database" means concretely."""
    counts: dict[str, int] = {}
    with _connect(db_url_for(db_name)) as conn, conn.cursor() as cur:
        for table in FINGERPRINT_TABLES:
            quoted = '"user"' if table == "user" else table
            try:
                cur.execute(f"SELECT count(*) FROM {quoted}")
                counts[table] = int(cur.fetchone()[0])
            except Exception:
                continue
        try:
            cur.execute("SELECT version_num FROM alembic_version")
            revision = cur.fetchone()[0]
        except Exception:
            revision = None
    return {"db_name": db_name, "alembic_version": revision, "counts": counts}


def clone(source: str, target: str, *, force_terminate: bool = False) -> None:  # pragma: no cover
    """Physically copy `source` onto a freshly created `target`.

    ``CREATE DATABASE ... TEMPLATE`` refuses while any other session is attached
    to the source, which is why the guard reports *how many* connections it is
    up against rather than failing with Postgres's terse message.
    """
    if source not in ALLOWED_SOURCE_DB_NAMES:
        raise GuardRefused(f"{source!r} 不在允许的克隆源名单 {sorted(ALLOWED_SOURCE_DB_NAMES)}")

    if exists(target):
        with _connect(admin_url()) as conn, conn.cursor() as cur:
            cur.execute(f'DROP DATABASE "{target}" WITH (FORCE)')

    attached = other_connections(source)
    if attached and force_terminate:
        terminate_connections(source)
        attached = other_connections(source)
    if attached:
        raise RuntimeError(
            f"源库 {source} 仍有 {attached} 个活动连接，无法作为 TEMPLATE 克隆；"
            "先停止 API/worker，或加 --force-terminate"
        )

    with _connect(admin_url()) as conn, conn.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{target}" TEMPLATE "{source}"')


def drop(db_name: str) -> bool:  # pragma: no cover
    with _connect(admin_url()) as conn, conn.cursor() as cur:
        cur.execute(f'DROP DATABASE "{db_name}" WITH (FORCE)')
    return not exists(db_name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-name", default="petaccess_publish_rehearsal_r3")
    ap.add_argument("--source", default="petaccess", help="克隆源（只读）")
    ap.add_argument("--clone", action="store_true", help="删除已有 rehearsal 库并以源库为模板重建")
    ap.add_argument("--drop", action="store_true", help="删除 rehearsal 库")
    ap.add_argument("--fingerprint", action="store_true", help="打印行数指纹")
    ap.add_argument("--force-terminate", action="store_true", help="克隆前断开源库连接")
    ap.add_argument("--confirm", action="store_true", help="破坏性操作必须显式确认")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        check_name(args.db_name)
    except GuardRefused as exc:
        print(f"REFUSED — {exc}", file=sys.stderr)
        return 4

    if (args.clone or args.drop) and not args.confirm:
        print("需要 --confirm 才会执行破坏性操作（--clone / --drop）", file=sys.stderr)
        return 2

    out: dict[str, Any] = {"db_name": args.db_name, "guard": "PASS"}

    if args.clone:
        check_source_name(args.source)
        clone(args.source, args.db_name, force_terminate=args.force_terminate)
        out["clone"] = "PASS"
        out["source"] = args.source
    if args.drop:
        out["drop"] = "PASS" if drop(args.db_name) else "FAIL"
    if args.fingerprint or args.clone:
        if exists(args.db_name):
            out["fingerprint"] = fingerprint(args.db_name)
        out["exists"] = exists(args.db_name)

    print(json.dumps(out, ensure_ascii=False, indent=2) if args.json else _render(out))
    return 0


def _render(out: dict[str, Any]) -> str:
    lines = [f"DB_NAME   = {out['db_name']}", f"GUARD     = {out['guard']}"]
    if "clone" in out:
        lines.insert(1, f"CLONED_FROM = {out['source']}")
        lines.insert(2, f"CLONE     = {out['clone']}")
    if "drop" in out:
        lines.append(f"DROP      = {out['drop']}")
    if "exists" in out:
        lines.append(f"EXISTS    = {out['exists']}")
    fp = out.get("fingerprint")
    if fp:
        lines.append(f"ALEMBIC   = {fp['alembic_version']}")
        lines.extend(f"  {k:<20} = {v}" for k, v in fp["counts"].items())
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
