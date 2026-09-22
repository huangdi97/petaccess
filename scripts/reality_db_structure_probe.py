"""AC2/AC3 real-DB verification: Reality migration structure + FK + indexes.

Read-only. Confirms the applied migration 2c7ea6ca8e30 really created the
Reality tables with the expected columns, FKs and indexes on the live DB.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg  # noqa: E402

from app.core.config import psycopg_url  # noqa: E402

TABLES = ["reality_candidate", "observed_presence", "staff_response_observation", "animal_facility"]

with psycopg.connect(psycopg_url(os.environ["DATABASE_URL"])) as conn:
    cur = conn.cursor()
    cur.execute(
        """SELECT table_name FROM information_schema.tables
           WHERE table_schema='public' AND table_name = ANY(%s) ORDER BY table_name""",
        (TABLES,),
    )
    found = [r[0] for r in cur.fetchall()]
    print(f"REALITY_TABLES = {found}")
    missing = set(TABLES) - set(found)
    if missing:
        print(f"MISSING_TABLES = {sorted(missing)}")

    for t in TABLES:
        cur.execute(
            """SELECT column_name, data_type, is_nullable FROM information_schema.columns
               WHERE table_name=%s ORDER BY ordinal_position""",
            (t,),
        )
        cols = cur.fetchall()
        print(f"\n[{t}] {len(cols)} columns:")
        print("  " + ", ".join(f"{c}:{d}({'N' if n == 'NO' else 'Y'})" for c, d, n in cols))

        cur.execute(
            """SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
               WHERE conrelid = %s::regclass AND contype='f' ORDER BY conname""",
            (t,),
        )
        fks = cur.fetchall()
        print(f"  FKs ({len(fks)}):")
        for name, defn in fks:
            print(f"    {name}: {defn}")

        cur.execute(
            """SELECT indexname, indexdef FROM pg_indexes WHERE tablename=%s ORDER BY indexname""",
            (t,),
        )
        idx = cur.fetchall()
        print(f"  Indexes ({len(idx)}):")
        for name, defn in idx:
            print(f"    {name}")

    # enum/constraint posture: reality_decision constraint on candidate
    cur.execute(
        """SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
           WHERE conrelid='reality_candidate'::regclass AND contype='c' ORDER BY conname"""
    )
    chk = cur.fetchall()
    print(f"\nreality_candidate CHECK constraints ({len(chk)}):")
    for name, defn in chk:
        print(f"  {name}: {defn}")

print("\nVERIFICATION_STRUCTURE_COMPLETE")
