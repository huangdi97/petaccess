"""WAVE_01 SourceMonitor completion (spec §28-§33, §29 monitorable-source-first).

Two things this fixes, both found by inspection rather than assumption:

1. Six sources that are required to be monitored had no monitor at all.
2. Every existing monitor had ``next_check_at = NULL``. Since the only code that
   ever wrote that column ran *after* a sweep, nothing was ever due — the fleet
   recorded intent, not observation. ``admin_create_monitor`` now seeds
   ``next_check_at`` at creation; this backfills the rows created before that
   change.

Monitor-required rule (applied uniformly, recorded in
``docs/expansion/SOURCE_MONITOR_MATRIX.md``):

    required  = source_type in {official_operator_policy, statute_or_regulation,
                                government_service}  AND  source_url IS NOT NULL

Exempt: ``external_web_reference`` (dated third-party reporting — secondary
evidence that cannot be "re-checked" for a current policy value) and
``ordinary_user`` (no canonical fetchable URL). Exemptions are per-source
reasoned, not silent.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))

API = os.getenv("WAVE01_API", "http://127.0.0.1:8010")
EMAIL = os.getenv("WAVE01_ADMIN_EMAIL", "admin@demo-petaccess.com")
PASSWORD = os.getenv("WAVE01_ADMIN_PASSWORD", "admin12345")
RUN_ID = "EXP-R1-W01-20260918"
OUT = REPO / "artifacts" / "expansion_w01" / "wave01_monitor_init.json"

os.environ.setdefault("DB_ROLE", "PRODUCTION")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess",
)

#: schedule per source_type (minutes). Statutes move slowly; operator policy
#: pages are the ones that actually change without warning.
SCHEDULE_BY_TYPE = {
    "statute_or_regulation": 10080,  # weekly
    "government_service": 10080,
    "official_operator_policy": 1440,  # daily
}

REQUIRED_TYPES = ("official_operator_policy", "statute_or_regulation", "government_service")


def login() -> str:
    r = httpx.post(
        f"{API}/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30
    )
    r.raise_for_status()
    return r.json()["access_token"]


def api(token: str):
    return httpx.Client(base_url=API, headers={"Authorization": f"Bearer {token}"}, timeout=60)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    from sqlalchemy import text
    from sqlalchemy.orm import Session

    from app.db.safety import guard_with_probe
    from app.db.session import get_engine

    engine = get_engine()
    guard = guard_with_probe(engine)
    print(f"[db] role={guard.role.value} db={guard.database_name}", file=sys.stderr)

    token = login()
    client = api(token)

    sel_source = (
        "SELECT id, source_type, issuer, source_url FROM source ORDER BY source_type, issuer"
    )
    with Session(engine) as s:
        sources = [dict(r._mapping) for r in s.execute(text(sel_source))]
        monitors = {
            r[0]: r[1] for r in s.execute(text("SELECT source_id, url FROM source_monitor"))
        }
        null_next = s.execute(
            text("SELECT count(*) FROM source_monitor WHERE next_check_at IS NULL")
        ).scalar()

        required, exempt = [], []
        for src in sources:
            if src["source_type"] in REQUIRED_TYPES and src["source_url"]:
                required.append(src)
            else:
                exempt.append(src)

        missing = [x for x in required if x["id"] not in monitors]
        plan = {
            "expansion_run_id": RUN_ID,
            "captured_at": datetime.now(UTC).isoformat(),
            "required_rule": (
                "source_type in {official_operator_policy, statute_or_regulation, "
                "government_service} AND source_url IS NOT NULL"
            ),
            "sources_total": len(sources),
            "required_sources": len(required),
            "exempt_sources": len(exempt),
            "monitors_before": len(monitors),
            "monitors_to_create": [
                {
                    "source_id": x["id"],
                    "source_type": x["source_type"],
                    "issuer": x["issuer"],
                    "url": x["source_url"],
                    "schedule_minutes": SCHEDULE_BY_TYPE[x["source_type"]],
                }
                for x in missing
            ],
            "next_check_at_null_before": null_next,
        }

        if not args.execute:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
            )
            print(json.dumps(plan, ensure_ascii=False, indent=2, default=str))
            return 0

        created = []
        for x in missing:
            body = {
                "source_id": x["id"],
                "url": x["source_url"],
                "schedule_minutes": SCHEDULE_BY_TYPE[x["source_type"]],
                "expansion_run_id": RUN_ID,
            }
            r = client.post("/api/v1/admin/monitors", json=body)
            r.raise_for_status()
            created.append({"source_id": x["id"], "issuer": x["issuer"], **r.json()})

        # Backfill monitors created before next_check_at was seeded at creation.
        s.execute(
            text("UPDATE source_monitor SET next_check_at = now() WHERE next_check_at IS NULL")
        )
        s.commit()

        after_monitors = s.execute(text("SELECT count(*) FROM source_monitor")).scalar()
        after_null = s.execute(
            text("SELECT count(*) FROM source_monitor WHERE next_check_at IS NULL")
        ).scalar()
        cov_required = s.execute(
            text("SELECT count(DISTINCT source_id) FROM source_monitor")
        ).scalar()

        result = {
            **plan,
            "created": created,
            "monitors_after": after_monitors,
            "next_check_at_null_after": after_null,
            "distinct_monitored_sources": cov_required,
        }
        OUT.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0


if __name__ == "__main__":
    sys.exit(main())
