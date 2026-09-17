"""§21 — one URL conversion, used everywhere.

``psycopg.connect`` rejects the SQLAlchemy DSN outright ("missing '=' after
..."), so every caller that speaks libpq has to strip the ``+psycopg`` suffix.
Doing that in two places is how a driver mismatch gets reintroduced: the fix
lands in one helper, the other copy keeps the bug, and the failure only shows up
as "the server refused to start" with a message that points nowhere.

These tests lock the conversion itself and then lock the fact that all the
entry points route through it, rather than re-implementing it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from dev_api_server import database_url_for, psycopg_url_for

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services" / "api"


def test_sqlalchemy_dsn_is_converted_to_libpq_form() -> None:
    url = psycopg_url_for("petaccess_test")
    assert url is not None
    assert url.startswith("postgresql://")
    assert "+psycopg" not in url


def test_conversion_preserves_credentials_and_host() -> None:
    """Stripping the driver must not touch anything else in the DSN."""
    raw = database_url_for("petaccess_test")
    converted = psycopg_url_for("petaccess_test")
    assert raw is not None and converted is not None
    if raw.startswith("postgresql+psycopg://"):
        assert raw.replace("postgresql+psycopg://", "postgresql://", 1) == converted
    else:
        assert raw == converted


def test_psycopg_accepts_the_converted_url() -> None:
    """The end-to-end point of the conversion: the driver must not choke.

    Connecting is the only honest check — a regex that looks right but produces a
    URL psycopg still refuses is exactly the failure this regression exists for.
    """
    psycopg = pytest.importorskip("psycopg")
    url = psycopg_url_for("petaccess_test")
    assert url is not None
    try:
        with psycopg.connect(url, connect_timeout=5) as conn, conn.cursor() as cur:
            cur.execute("select current_database()")
            assert cur.fetchone()[0] == "petaccess_test"
    except Exception as exc:  # noqa: BLE001 - the point is "no driver error"
        pytest.fail(f"转换后的 URL 仍被 psycopg 拒绝：{type(exc).__name__}: {exc}")


def test_no_second_url_conversion_implementation() -> None:
    """One helper, not one per script.

    A second ``replace("postgresql+psycopg://", ...)`` anywhere is a copy that
    will drift: the fix lands in one file and the other keeps the bug.
    """
    offenders: list[str] = []
    pattern = re.compile(r'["\']postgresql\+psycopg://["\']')
    for base in (ROOT / "scripts", ROOT / "services" / "api", ROOT / "services" / "worker"):
        for path in sorted(base.rglob("*.py")):
            # The canonical implementation, and the scheme constants it is built
            # from, are the only allowed occurrences.
            if path.name in {"dev_api_server.py", "config.py"}:
                continue
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    offenders.append(f"{path.relative_to(ROOT)}:{lineno}")
    assert not offenders, f"请复用 app.core.config.psycopg_url：{offenders}"


def test_conversion_has_a_single_implementation() -> None:
    """The app owns the conversion; scripts delegate to it."""
    config = (SERVICES / "app" / "core" / "config.py").read_text(encoding="utf-8")
    assert "def psycopg_url(" in config

    dev_api = (ROOT / "scripts" / "dev_api_server.py").read_text(encoding="utf-8")
    assert "psycopg_url(database_url_for(db_name))" in dev_api, (
        "dev_api_server 必须委派给 app.core.config.psycopg_url，而不是自己再实现一遍"
    )
