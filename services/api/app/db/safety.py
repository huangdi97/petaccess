"""Canonical database roles + one fail-closed safety guard for every database.

Why this module exists
----------------------
`petaccess` stopped being a scratch database the moment the first real governed
batch was published into it (R2-FINAL-R3-BATCH-01B). It is production data now.
The test suites did not know that: pytest, the E2E suite and the visual suite all
resolved their connection from the repository `.env`, which points at
`petaccess`, so a full QA run silently wrote fixtures into the governed
database::

    access_rule      current 815 -> 843
    rule_exception   current  83 ->  87

The fixtures had names like `回滚测试场所*`, `E2E-A 告示咖啡`, `质量基线测试咖啡`.

Three things went wrong, and this module fixes all three:

1. **No positive allowlist.** `scripts/visual_db_reset.py` and
   `scripts/rehearsal_db.py` each carried their own `FORBIDDEN_DB_NAMES` set. A
   deny list can only refuse the names somebody thought of; an unknown name
   (once `petaccess_dev_only`) was accepted and a destructive reset was one
   typo away. Here a workload declares *what it is* and the guard requires the
   live database to match an explicit allowlist for that workload.
2. **Duplicated policy.** Every script invented its own list, so they drifted.
   There is exactly one registry below, and every caller goes through it.
3. **Warning instead of refusal.** A warning after the fact is not a control.
   Every assertion in :class:`DatabaseSafetyGuard` raises.

The authoritative input is never the URL. A URL can be wrong, stale, inherited
from a shell profile, or point at a name that no longer means what it did
yesterday. The guard asks the *server* — ``SELECT current_database()`` — and
classifies the answer.
"""

from __future__ import annotations

import argparse
import contextlib
import enum
import json
import re
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

__all__ = [
    "DatabaseRole",
    "DatabaseRoleSpec",
    "DatabaseSafetyError",
    "DatabaseSafetyGuard",
    "ProductionCleanupRefused",
    "ProductionDatabaseRefused",
    "RoleMismatchRefused",
    "UnknownDatabaseRefused",
    "ROLE_REGISTRY",
    "classify_database_name",
    "database_name_from_url",
    "describe_roles",
    "guard_for_psycopg",
    "guard_for_url",
    "probe_database_name",
    "require_role_from_env",
    "role_spec",
]


class DatabaseRole(enum.StrEnum):
    """What a database is *for*. Not where it lives, not what it is called.

    ``StrEnum`` (3.11+) rather than ``(str, Enum)``: the members are compared and
    logged as plain strings everywhere, and the mixin form renders as
    ``DatabaseRole.PRODUCTION`` in an f-string, which is exactly the kind of
    surprise this module exists to remove.
    """

    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"
    TEST = "TEST"
    E2E = "E2E"
    VISUAL = "VISUAL"
    REHEARSAL = "REHEARSAL"
    RESTORE = "RESTORE"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DatabaseRoleSpec:
    """One row of the role registry (§5).

    ``patterns`` are full-match regexes over the *database name*. They exist
    because two roles legitimately need per-run names (``petaccess_test_<run>``,
    ``petaccess_publish_rehearsal_<rev>``); ``canonical_name`` is what the
    runbook and the docs refer to.
    """

    role: DatabaseRole
    canonical_name: str
    purpose: str
    patterns: tuple[str, ...]
    fixture_allowed: bool
    destructive_allowed: bool
    real_publish_allowed: bool
    real_data_allowed: bool
    notes: str = ""

    def matches(self, db_name: str) -> bool:
        return any(re.fullmatch(p, db_name) for p in self.patterns)

    def as_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "canonical_name": self.canonical_name,
            "purpose": self.purpose,
            "patterns": list(self.patterns),
            "fixture_allowed": self.fixture_allowed,
            "destructive_allowed": self.destructive_allowed,
            "real_publish_allowed": self.real_publish_allowed,
            "real_data_allowed": self.real_data_allowed,
            "notes": self.notes,
        }


#: The single source of truth. Order matters only for readability — a name that
#: matches two rows would be a bug, and `_assert_registry_is_disjoint()` below
#: turns that bug into an import error instead of a coin flip.
ROLE_REGISTRY: tuple[DatabaseRoleSpec, ...] = (
    DatabaseRoleSpec(
        role=DatabaseRole.PRODUCTION,
        canonical_name="petaccess",
        purpose="正式业务库：唯一承载真实发布对象、Human Signature 与只读消费答案",
        patterns=(r"petaccess", r"petaccess_production", r"petaccess_prod"),
        fixture_allowed=False,
        destructive_allowed=False,
        real_publish_allowed=True,
        real_data_allowed=True,
        notes="写入只能来自人工授权的 publish；任何 fixture / destructive 操作一律 FAIL CLOSED",
    ),
    DatabaseRoleSpec(
        role=DatabaseRole.RESTORE,
        canonical_name="petaccess_restore_<stamp>",
        purpose="备份恢复演练库：从 production 备份还原后做只读核对",
        patterns=(r"petaccess_restore_[a-z0-9_]*",),
        fixture_allowed=False,
        destructive_allowed=True,
        real_publish_allowed=False,
        real_data_allowed=True,
        notes="含真实数据副本：只用于恢复验证，绝不作为测试夹具落地处",
    ),
    DatabaseRoleSpec(
        role=DatabaseRole.REHEARSAL,
        canonical_name="petaccess_publish_rehearsal_r3",
        purpose="发布演练库：clone 自 production，验证 batch 计划与幂等",
        patterns=(r"petaccess_publish_rehearsal_[a-z0-9_]{1,40}",),
        fixture_allowed=True,
        destructive_allowed=True,
        real_publish_allowed=False,
        real_data_allowed=True,
        notes="允许 rollback / supersession / watch 破坏性演练；不得与 TEST/E2E/VISUAL 复用",
    ),
    DatabaseRoleSpec(
        role=DatabaseRole.VISUAL,
        canonical_name="petaccess_visual",
        purpose="视觉回归库：每次运行从固定 demo 种子重建，保证截图可比",
        patterns=(r"petaccess_visual",),
        fixture_allowed=True,
        destructive_allowed=True,
        real_publish_allowed=False,
        real_data_allowed=False,
        notes="destroy+reseed 是设计的一部分；不得读取 production 实时计数",
    ),
    DatabaseRoleSpec(
        role=DatabaseRole.E2E,
        canonical_name="petaccess_e2e",
        purpose="Playwright E2E 库：由 E2E 测试自己创建与消耗业务对象",
        patterns=(r"petaccess_e2e", r"petaccess_e2e_[a-z0-9_]*"),
        fixture_allowed=True,
        destructive_allowed=True,
        real_publish_allowed=False,
        real_data_allowed=False,
    ),
    DatabaseRoleSpec(
        role=DatabaseRole.TEST,
        canonical_name="petaccess_test",
        purpose="pytest / integration 库：夹具、回滚、supersession、分页均可自由写入",
        patterns=(r"petaccess_test", r"petaccess_test_[a-z0-9_]*"),
        fixture_allowed=True,
        destructive_allowed=True,
        real_publish_allowed=False,
        real_data_allowed=False,
    ),
    DatabaseRoleSpec(
        role=DatabaseRole.DEVELOPMENT,
        canonical_name="petaccess_dev",
        purpose="本地手工调试库：可以随意折腾，与正式库无关",
        patterns=(r"petaccess_dev", r"petaccess_dev_[a-z0-9_]*", r"petaccess_pilot"),
        fixture_allowed=True,
        destructive_allowed=True,
        real_publish_allowed=False,
        real_data_allowed=False,
        notes="日常调试应当指向这里，而不是 petaccess",
    ),
    DatabaseRoleSpec(
        role=DatabaseRole.INFRASTRUCTURE,
        canonical_name="postgres",
        purpose="集群管理库（postgres / template*）：只用于 CREATE DATABASE 之类的管理动作",
        patterns=(r"postgres", r"template0", r"template1"),
        fixture_allowed=False,
        destructive_allowed=False,
        real_publish_allowed=False,
        real_data_allowed=False,
    ),
)

#: Roles a *test* workload is allowed to run against. This is the positive
#: allowlist of §8: matching a pattern in this set — and only that — unlocks
#: fixture writes and destructive drills.
TEST_WORKLOAD_ROLES: frozenset[DatabaseRole] = frozenset(
    {DatabaseRole.TEST, DatabaseRole.E2E, DatabaseRole.VISUAL, DatabaseRole.REHEARSAL}
)

#: Roles where a governed publish may ever be executed.
PUBLISH_ROLES: frozenset[DatabaseRole] = frozenset({DatabaseRole.PRODUCTION})

_UNKNOWN_SPEC = DatabaseRoleSpec(
    role=DatabaseRole.UNKNOWN,
    canonical_name="<unknown>",
    purpose="未登记库名：不承担任何角色，任何写操作都被拒绝",
    patterns=(),
    fixture_allowed=False,
    destructive_allowed=False,
    real_publish_allowed=False,
    real_data_allowed=False,
    notes="§8：denylist 不足以保护未知名字，未知名字必须被拒绝而不是被允许",
)

_ROLE_TO_SPEC: dict[DatabaseRole, DatabaseRoleSpec] = {s.role: s for s in ROLE_REGISTRY}


def _assert_registry_is_disjoint() -> None:
    """A name matching two roles would make classification order-dependent."""
    names = [
        "petaccess",
        "petaccess_production",
        "petaccess_dev",
        "petaccess_pilot",
        "petaccess_test",
        "petaccess_test_run42",
        "petaccess_e2e",
        "petaccess_e2e_1",
        "petaccess_visual",
        "petaccess_publish_rehearsal_r3",
        "petaccess_restore_20260917",
        "postgres",
        "template1",
        "petaccess_dev_only",
        "who_knows",
    ]
    for name in names:
        hits = [s.role.value for s in ROLE_REGISTRY if s.matches(name)]
        if len(hits) > 1:
            raise AssertionError(f"registry overlap for {name!r}: {hits}")


_assert_registry_is_disjoint()


class DatabaseSafetyError(RuntimeError):
    """Base class: the guard refused an operation. Never a warning, always a raise."""


class ProductionDatabaseRefused(DatabaseSafetyError):
    """A fixture/test/destructive operation was aimed at production."""


class UnknownDatabaseRefused(DatabaseSafetyError):
    """The live database name is not in the registry, so nothing may write to it."""


class RoleMismatchRefused(DatabaseSafetyError):
    """The database is real, but it is not the role the caller asked for."""


class ProductionCleanupRefused(DatabaseSafetyError):
    """A governed production cleanup was started without its evidence (§27)."""


def classify_database_name(name: str) -> DatabaseRole:
    """Map a live database name to its role (``UNKNOWN`` when unregistered)."""
    for spec in ROLE_REGISTRY:
        if spec.matches(name):
            return spec.role
    return DatabaseRole.UNKNOWN


def role_spec(role: DatabaseRole) -> DatabaseRoleSpec:
    return _ROLE_TO_SPEC.get(role, _UNKNOWN_SPEC)


def database_name_from_url(url: str) -> str:
    """Extract the database name from a SQLAlchemy or libpq URL.

    ``postgresql+psycopg://user:pw@host:5432/petaccess?sslmode=disable`` ->
    ``petaccess``. Query strings and credentials are ignored on purpose: the
    name is what is classified, never the host.
    """
    if not url:
        return ""
    # Strip the SQLAlchemy driver suffix so urlsplit handles it like libpq.
    cleaned = re.sub(
        r"^(postgresql|postgres|psycopg|psycopg2)\+[a-z0-9_]+://", "postgresql://", url
    )
    if "://" not in cleaned:
        raise DatabaseSafetyError(f"不是可解析的数据库 URL：{url!r}")
    path = urlsplit(cleaned).path or ""
    return path.lstrip("/").split("/")[0]


def probe_database_name(bind: Any) -> str:
    """Ask the server which database this connection is actually attached to.

    Accepts a SQLAlchemy ``Engine``/``Connection``/``Session``. Prefer
    :func:`probe_database_name_psycopg` for raw psycopg connections (the
    rehearsal and snapshot tooling speaks libpq directly).
    """
    if hasattr(bind, "cursor"):
        return probe_database_name_psycopg(bind)
    from sqlalchemy import text

    with bind.connect() if hasattr(bind, "connect") else contextlib.nullcontext(bind) as conn:
        return str(conn.execute(text("SELECT current_database()")).scalar_one())


def probe_database_name_psycopg(conn: Any) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        row = cur.fetchone()
    if not row:
        raise DatabaseSafetyError("无法读取 current_database()")
    return str(row[0])


@dataclass
class DatabaseSafetyGuard:
    """Fail-closed assertions about the database underneath an operation.

    Construct it from a live connection (``guard_for_psycopg``) or from a URL
    (``guard_for_url``). A URL-built guard re-probes the server when a bind is
    supplied, so the URL can never be the last word.

    Every method raises on refusal. There is deliberately no ``warn``-and-continue
    path: the whole point is that the bad operation does not happen.
    """

    database_name: str
    role: DatabaseRole
    declared_role: DatabaseRole | None = None
    probe_source: str = "url"

    def __post_init__(self) -> None:
        if self.declared_role is not None and self.declared_role is not self.role:
            raise RoleMismatchRefused(
                f"声明的 DB_ROLE={self.declared_role.value} 与实际库 {self.database_name!r} "
                f"({self.role.value}) 不一致；声明的角色不能覆盖服务端事实。"
            )

    # ---------------------------------------------------------------- facts --
    @property
    def spec(self) -> DatabaseRoleSpec:
        return role_spec(self.role)

    @property
    def is_production(self) -> bool:
        return self.role is DatabaseRole.PRODUCTION

    def describe(self) -> dict[str, Any]:
        return {
            "database": self.database_name,
            "role": self.role.value,
            "probe_source": self.probe_source,
            "declared_role": self.declared_role.value if self.declared_role else None,
            "fixture_allowed": self.spec.fixture_allowed,
            "destructive_allowed": self.spec.destructive_allowed,
            "real_publish_allowed": self.spec.real_publish_allowed,
            "real_data_allowed": self.spec.real_data_allowed,
        }

    def banner(self, label: str = "TARGET_DB") -> str:
        """One-line, greppable proof of what an operation is aimed at."""
        return f"{label} = {self.database_name}\n{label}_ROLE = {self.role.value}"

    # ------------------------------------------------------------ assertions --
    def assert_not_production(self, operation: str) -> None:
        if self.is_production:
            raise ProductionDatabaseRefused(
                f"Refusing {operation} on PRODUCTION database {self.database_name!r}. "
                "正式库只承载真实业务数据：夹具、清理、回滚、重建都必须指向 "
                "TEST / E2E / VISUAL / REHEARSAL 角色的库。"
            )
        if self.role is DatabaseRole.UNKNOWN:
            raise UnknownDatabaseRefused(
                f"Refusing {operation} on unregistered database {self.database_name!r}. "
                "§8：仅拒绝黑名单不够——未知库名必须被拒绝。请先把它登记到 "
                "app.db.safety.ROLE_REGISTRY，或换用带角色前缀的库名。"
            )

    def assert_role(self, expected: DatabaseRole | Iterable[DatabaseRole], operation: str) -> None:
        wanted = {expected} if isinstance(expected, DatabaseRole) else set(expected)
        if self.role not in wanted:
            names = ", ".join(sorted(r.value for r in wanted))
            raise RoleMismatchRefused(
                f"Refusing {operation}: 需要 {names} 角色的库，实际是 "
                f"{self.role.value}（{self.database_name!r}）。"
            )

    def assert_test_workload(self, operation: str) -> None:
        """The positive-allowlist gate for anything that writes fixtures."""
        if self.role not in TEST_WORKLOAD_ROLES:
            raise ProductionDatabaseRefused(
                f"Refusing {operation} on {self.role.value} database "
                f"{self.database_name!r}. 测试负载只能运行在 "
                f"{', '.join(sorted(r.value for r in TEST_WORKLOAD_ROLES))} 角色的库上。"
            )

    # Named entry points, one per §6. Each is `assert_*` + a useful message.
    def assert_test_database(self, operation: str) -> None:
        self.assert_role(DatabaseRole.TEST, operation)

    def assert_e2e_database(self, operation: str) -> None:
        self.assert_role(DatabaseRole.E2E, operation)

    def assert_visual_database(self, operation: str) -> None:
        self.assert_role(DatabaseRole.VISUAL, operation)

    def assert_rehearsal_database(self, operation: str) -> None:
        self.assert_role(DatabaseRole.REHEARSAL, operation)

    def assert_production_database(self, operation: str) -> None:
        self.assert_role(DatabaseRole.PRODUCTION, operation)

    def assert_destructive_allowed(self, operation: str) -> None:
        self.assert_test_workload(operation)
        if not self.spec.destructive_allowed:
            raise DatabaseSafetyError(
                f"Refusing {operation}: {self.role.value} 角色不允许破坏性操作。"
            )

    def assert_fixture_write_allowed(self, operation: str) -> None:
        self.assert_test_workload(operation)
        if not self.spec.fixture_allowed:
            raise DatabaseSafetyError(
                f"Refusing {operation}: {self.role.value} 角色不允许写入测试夹具。"
            )

    def assert_real_publish_allowed(self, operation: str) -> None:
        if self.role not in PUBLISH_ROLES:
            raise RoleMismatchRefused(
                f"Refusing {operation}: 真实发布只允许在 PRODUCTION 库执行，实际是 "
                f"{self.role.value}（{self.database_name!r}）。演练请走 REHEARSAL 角色。"
            )

    def assert_production_cleanup_allowed(
        self,
        operation: str,
        *,
        backup_path: str | Path | None,
        reviewed_plan_path: str | Path | None,
    ) -> None:
        """The **only** governed way to delete rows from the production database (§27).

        ``PRODUCTION`` deliberately keeps ``destructive_allowed = False``: no
        generic tool may drop, reset or rebuild it, and that must not change.
        Removing fixtures that leaked into production is a different operation,
        so it gets its own entry point with its own evidence requirements rather
        than a widened role spec:

        * the target must be ``PRODUCTION`` — so a cleanup can never silently
          land on a test database and be mistaken for real work;
        * a physical backup must already exist on disk, i.e. the caller cannot
          ask for permission and take the backup afterwards;
        * a reviewed dry-run plan must already exist on disk.

        This relaxes nothing else. ``assert_destructive_allowed`` still refuses
        ``PRODUCTION`` for every other caller, and this method grants no
        fixture-write or publish capability.
        """
        self.assert_role(DatabaseRole.PRODUCTION, operation)
        missing: list[str] = []
        if not backup_path or not Path(backup_path).is_file():
            missing.append(f"备份文件不存在：{backup_path!r}")
        if not reviewed_plan_path or not Path(reviewed_plan_path).is_file():
            missing.append(f"已审阅的 dry-run 计划不存在：{reviewed_plan_path!r}")
        if missing:
            raise ProductionCleanupRefused(
                f"Refusing {operation} on PRODUCTION database {self.database_name!r}："
                "受治理的生产清理必须先具备物理备份与已审阅的 dry-run 计划。" + "；".join(missing)
            )


def _declared_role_from_env() -> DatabaseRole | None:
    import os

    raw = os.environ.get("DB_ROLE", "").strip()
    if not raw:
        return None
    try:
        return DatabaseRole(raw.upper())
    except ValueError as exc:
        raise DatabaseSafetyError(
            f"DB_ROLE={raw!r} 不是合法角色；可选：{', '.join(r.value for r in DatabaseRole)}"
        ) from exc


def guard_for_url(url: str, *, declared_role: DatabaseRole | None = None) -> DatabaseSafetyGuard:
    """Classify by name only. Use ``guard_for_psycopg``/``guard_with_probe`` when possible."""
    name = database_name_from_url(url)
    return DatabaseSafetyGuard(
        database_name=name,
        role=classify_database_name(name),
        declared_role=declared_role if declared_role is not None else _declared_role_from_env(),
        probe_source="url",
    )


def guard_for_psycopg(conn: Any) -> DatabaseSafetyGuard:
    """Authoritative guard: the name comes from the server, not from a string."""
    name = probe_database_name_psycopg(conn)
    return DatabaseSafetyGuard(
        database_name=name,
        role=classify_database_name(name),
        declared_role=_declared_role_from_env(),
        probe_source="current_database()",
    )


def guard_with_probe(bind: Any, *, url: str | None = None) -> DatabaseSafetyGuard:
    """Authoritative guard for SQLAlchemy binds (Engine/Connection/Session)."""
    try:
        name = probe_database_name(bind)
    except Exception:
        if url is None:
            raise
        return guard_for_url(url)
    return DatabaseSafetyGuard(
        database_name=name,
        role=classify_database_name(name),
        declared_role=_declared_role_from_env(),
        probe_source="current_database()",
    )


def require_role_from_env(
    env_var: str, expected: Sequence[DatabaseRole], *, operation: str
) -> None:
    """Shell-facing helper: assert ``$<env_var>`` classifies as one of ``expected``.

    Used by the PowerShell/bash wrappers so a mistyped ``PYTEST_DB`` fails before
    pytest is even imported.
    """
    import os

    url = os.environ.get(env_var, "")
    if not url:
        raise DatabaseSafetyError(
            f"{env_var} 未设置：无法证明目标库角色，拒绝继续（{operation}）。"
        )
    guard = guard_for_url(url)
    guard.assert_role(expected, operation)


def describe_roles() -> list[dict[str, Any]]:
    return [spec.as_dict() for spec in ROLE_REGISTRY] + [_UNKNOWN_SPEC.as_dict()]


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m app.db.safety",
        description="数据库角色注册表与安全守卫（只读）。",
    )
    ap.add_argument("--describe", action="store_true", help="打印角色注册表")
    ap.add_argument("--probe-url", default=None, help="从 URL 名推断角色")
    ap.add_argument(
        "--probe-db", action="store_true", help="连接 .env 的 DATABASE_URL 并读取真实库名"
    )
    ap.add_argument(
        "--assert-role",
        default=None,
        help="断言真实库角色属于其一（逗号分隔），否则非零退出",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.describe:
        rows = describe_roles()
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            for row in rows:
                print(
                    f"{row['role']:<14} {row['canonical_name']:<32} "
                    f"fixture={'Y' if row['fixture_allowed'] else 'n'} "
                    f"destructive={'Y' if row['destructive_allowed'] else 'n'} "
                    f"publish={'Y' if row['real_publish_allowed'] else 'n'}  {row['purpose']}"
                )
        return 0

    guard: DatabaseSafetyGuard | None = None
    if args.probe_db:
        import psycopg

        from app.core.config import get_settings, psycopg_url

        url = psycopg_url(get_settings().database_url)
        if not url:
            raise SystemExit("DATABASE_URL 未配置——无法用真实连接探测数据库角色")
        with psycopg.connect(url) as conn:
            guard = guard_for_psycopg(conn)
    elif args.probe_url:
        guard = guard_for_url(args.probe_url)

    if guard is not None:
        if args.json:
            print(json.dumps(guard.describe(), ensure_ascii=False, indent=2))
        else:
            print(guard.banner())
            print(f"PROBE_SOURCE = {guard.probe_source}")
        if args.assert_role:
            wanted = [
                DatabaseRole(part.strip().upper())
                for part in args.assert_role.split(",")
                if part.strip()
            ]
            guard.assert_role(wanted, "命令行角色断言")
            print(f"ROLE_ASSERT = PASS ({', '.join(r.value for r in wanted)})")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    try:
        raise SystemExit(main())
    except DatabaseSafetyError as exc:
        print(f"DATABASE_SAFETY_REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(3) from exc
