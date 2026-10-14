"""Preview database URL rendering stays credential-safe and URL-correct."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "render_preview_database_url.py"
SPEC = importlib.util.spec_from_file_location("render_preview_database_url", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_preview_database_url_encodes_credentials() -> None:
    rendered = MODULE.render_database_url(
        "pet access",
        "p@ss:/?#[]",
        "preview db",
    )
    assert rendered == (
        "postgresql+psycopg://pet%20access:p%40ss%3A%2F%3F%23%5B%5D@db:5432/preview%20db"
    )


def test_preview_database_url_rejects_missing_password() -> None:
    try:
        MODULE.render_database_url("petaccess", "", "preview")
    except ValueError as exc:
        assert "POSTGRES_PASSWORD" in str(exc)
    else:
        raise AssertionError("missing Preview DB password must be rejected")
