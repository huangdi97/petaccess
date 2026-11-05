#!/usr/bin/env python3
"""Render the Preview PostgreSQL SQLAlchemy URL from environment variables.

The password is URL-encoded at runtime so deployment workflows never need to
embed a credential-bearing database URL template.
"""

from __future__ import annotations

import os
from urllib.parse import quote, urlunsplit


def render_database_url(
    user: str,
    password: str,
    database: str,
    *,
    host: str = "db",
    port: int = 5432,
) -> str:
    values = {
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": database,
        "host": host,
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise ValueError(f"missing Preview database URL fields: {', '.join(missing)}")

    netloc = f"{quote(user, safe='')}:{quote(password, safe='')}@{host}:{int(port)}"
    return urlunsplit(
        (
            "postgresql+psycopg",
            netloc,
            f"/{quote(database, safe='')}",
            "",
            "",
        )
    )


def main() -> int:
    print(
        render_database_url(
            os.environ.get("POSTGRES_USER", ""),
            os.environ.get("POSTGRES_PASSWORD", ""),
            os.environ.get("POSTGRES_DB", ""),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
