"""Drop a database that was created by accident — but only after proving it is one.

Why a script instead of a one-liner
-----------------------------------
`petaccess_dev_only` is not a database name anywhere in this repo. It is the
**value of `POSTGRES_PASSWORD`**. It exists because `scripts/visual_db_reset.py`
was invoked with the password where the database name was expected, and that
script only refuses names on its `FORBIDDEN_DB_NAMES` list — an unknown name is
dropped and recreated without complaint. The result is a silent, fully seeded
clone of the demo database sitting next to the real one.

Deleting a database is irreversible, so the decision must not rest on a human
saying "yes it was an accident". This script re-derives the evidence:

1. **Preconditions** — the name is not in `PROTECTED_DB_NAMES` (the real, the
   dev, the pilot, the visual, the admin and the template databases), it is not
   referenced as a database anywhere in the repo, and nothing is connected to it.
2. **Fingerprint** — a per-table row census, printed and recorded. Two databases
   with the same fingerprint are the same data; a governed database is orders of
   magnitude larger and carries candidates, evidence and audit history.
3. **Refusal, not guessing** — any failed precondition exits non-zero with the
   reason and changes nothing. There is no `--force`: an accident you cannot
   prove was an accident is a `MANUAL_REVIEW_REQUIRED`, not a drop.

The drop itself runs with `WITH (FORCE)` so a lingering connection cannot make
the command fail halfway.

Usage:
    python scripts/db_cleanup_accidental.py --db-name petaccess_dev_only --confirm-drop
    python scripts/db_cleanup_accidental.py --db-name petaccess_dev_only --report-only --json
"""

# NOTE: no ``from __future__ import annotations`` — see the same note in
# ``scripts/publish_reviewed_r1.py``: dataclasses loaded by path via
# ``spec_from_file_location`` cannot resolve string annotations.

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
for _extra in (str(REPO / "scripts"), str(REPO / "services" / "api")):
    if _extra not in sys.path:
        sys.path.insert(0, _extra)

from app.db.safety import DatabaseRole, classify_database_name, describe_roles  # noqa: E402

#: Databases this tool must never touch, whatever it is asked to do.
#:
#: Derived from the one canonical registry (`app.db.safety`) rather than listed
#: here: a name is protected precisely when it classifies as a known role, so a
#: new role added tomorrow is protected the moment it is registered. Only
#: *unregistered* names are droppable, and only after the preconditions below
#: prove the database really was an accident.
PROTECTED_DB_NAMES = frozenset(
    row["canonical_name"] for row in describe_roles() if not row["canonical_name"].startswith("<")
) | frozenset({"petaccess_dev", "petaccess_pilot"})


def is_protected(name: str) -> bool:
    return classify_database_name(name) is not DatabaseRole.UNKNOWN


#: Tables (when present) whose counts fingerprint "is this governed data?".
CENSUS_TABLES = (
    "place",
    "zone",
    "access_rule",
    "rule_exception",
    "rule_candidate",
    "evidence_bundle",
    "source",
    "source_artifact",
    "audit_log",
    "operator",
    "user",
    "observation_claim",
)

#: Tables whose non-zero count means "governed content, not a demo clone".
GOVERNED_TABLES = ("rule_candidate", "evidence_bundle", "source_artifact", "rule_exception")


def admin_url() -> str:
    """Admin connection URL, from `.env` when present, else the documented default."""
    repo_env = REPO / ".env"
    user, password, host, port = "petaccess", "", "127.0.0.1", "5432"
    if repo_env.exists():
        values: dict[str, str] = {}
        for line in repo_env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()
        user = "petaccess"
        password = values.get("POSTGRES_PASSWORD", password)
        url = values.get("DATABASE_URL", "")
        if "@" in url:
            hostport = url.rsplit("@", 1)[1].split("/", 1)[0]
            host, _, port = hostport.partition(":")
            host = host or "127.0.0.1"
            port = port or "5432"
    return f"postgresql://{user}:{password}@{host}:{port}/postgres"


def _connect(url: str):  # pragma: no cover - environment dependent
    import psycopg

    return psycopg.connect(url, autocommit=True)


def database_exists(conn, name: str) -> bool:  # pragma: no cover
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        return cur.fetchone() is not None


def active_connections(conn, name: str) -> list[dict[str, Any]]:  # pragma: no cover
    with conn.cursor() as cur:
        cur.execute(
            "SELECT pid, usename, coalesce(application_name, ''), coalesce(state, ''),"
            " coalesce(host(client_addr), '')"
            " FROM pg_stat_activity WHERE datname = %s",
            (name,),
        )
        return [
            {
                "pid": row[0],
                "usename": row[1],
                "application_name": row[2],
                "state": row[3],
                "client_addr": row[4],
            }
            for row in cur.fetchall()
        ]


def repo_references(name: str) -> list[str]:
    """Files that mention `name` as a *database*, not as a password or secret.

    A line only counts when the name appears in the path segment of a connection
    URL, i.e. right after `/<port>/`. `petaccess_dev_only` legitimately appears
    all over the repo as `POSTGRES_PASSWORD`; those hits are not references to
    this database and must not block the cleanup.
    """
    hits: list[str] = []
    suffixes = {
        ".py",
        ".ts",
        ".js",
        ".mjs",
        ".toml",
        ".ini",
        ".yml",
        ".yaml",
        ".env",
        ".sh",
        ".ps1",
    }
    skip_dirs = {".venv", "node_modules", ".git", "dist", "__pycache__", ".mypy_cache"}
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes and path.name != ".env":
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if name not in line:
                continue
            after_port = line.split("5432/", 1)
            if len(after_port) > 1 and after_port[1].split("/")[0].split('"')[0].strip() == name:
                hits.append(f"{path.relative_to(REPO).as_posix()}:{number}")
    return hits


def census(conn, name: str) -> dict[str, int]:  # pragma: no cover
    """Row counts for every census table that exists, via a separate connection."""
    url = admin_url()
    db_url = url.rsplit("/", 1)[0] + "/" + name
    counts: dict[str, int] = {}
    with _connect(db_url) as target:
        for table in CENSUS_TABLES:
            quoted = '"user"' if table == "user" else table
            try:
                with target.cursor() as cur:
                    cur.execute(f"SELECT count(*) FROM {quoted}")
                    counts[table] = int(cur.fetchone()[0])
            except Exception:  # table absent in this schema
                continue
    return counts


def build_report(name: str) -> dict[str, Any]:
    report: dict[str, Any] = {
        "db_name": name,
        "protected": is_protected(name),
        "exists": False,
        "active_connections": [],
        "repo_references": [],
        "census": {},
        "governed_data": False,
        "verdict": "UNKNOWN",
    }
    if is_protected(name):
        report["verdict"] = "PROTECTED_REFUSED"
        return report

    with _connect(admin_url()) as conn:
        if not database_exists(conn, name):
            report["verdict"] = "ALREADY_ABSENT"
            return report
        report["exists"] = True
        report["active_connections"] = active_connections(conn, name)

    report["repo_references"] = repo_references(name)
    report["census"] = census(None, name)
    report["governed_data"] = any(report["census"].get(t, 0) > 0 for t in GOVERNED_TABLES)

    blockers = []
    if report["active_connections"]:
        blockers.append(f"仍有 {len(report['active_connections'])} 个活动连接")
    if report["repo_references"]:
        blockers.append(f"仓库中存在把 {name} 当作库名的引用：{report['repo_references']}")
    if report["governed_data"]:
        blockers.append(
            "该库含受治理数据（candidate/evidence/source_artifact/rule_exception 非空）"
        )
    blockers.extend(report.setdefault("extra_blockers", []))
    report["blockers"] = blockers
    report["verdict"] = "MANUAL_REVIEW_REQUIRED" if blockers else "SAFE_TO_DROP"
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-name", required=True)
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--confirm-drop", action="store_true")
    ap.add_argument(
        "--evidence-out",
        default=None,
        help="把校验证据写入该 JSON 路径（默认只打印）",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    report = build_report(args.db_name)
    if args.evidence_out:
        out = Path(args.evidence_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json or not args.report_only:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if report["verdict"] == "ALREADY_ABSENT":
        print(f"ACCIDENTAL_DB_CLEANUP: {args.db_name} 不存在（无需删除）")
        return 0
    if report["verdict"] == "PROTECTED_REFUSED":
        print(f"REFUSED — {args.db_name} 属于受保护库，绝不触碰。", file=sys.stderr)
        return 4
    if report["verdict"] == "MANUAL_REVIEW_REQUIRED":
        print(f"MANUAL_REVIEW_REQUIRED — {args.db_name} 未通过删除前校验：", file=sys.stderr)
        for blocker in report["blockers"]:
            print(f"  - {blocker}", file=sys.stderr)
        return 3
    if args.report_only or not args.confirm_drop:
        print(f"DRY RUN — {args.db_name} 通过校验，可安全删除；加 --confirm-drop 才真正执行。")
        return 0

    with _connect(admin_url()) as conn, conn.cursor() as cur:
        cur.execute(f'DROP DATABASE "{args.db_name}" WITH (FORCE)')

    with _connect(admin_url()) as conn:
        still_there = database_exists(conn, args.db_name)
    if still_there:
        print(f"FAIL — {args.db_name} 仍然存在", file=sys.stderr)
        return 1
    print(f"ACCIDENTAL_DB_CLEANUP = PASS — {args.db_name} no longer exists")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
