"""WAVE_01 duplicate audit (read-only).

The first ingest run aborted at the DataSourceJob finish step, before the
manifest was written; the second run therefore re-created artifacts / bundles /
candidates that already existed. This script lists every Wave-01 object and
flags duplicates so they can be cleaned deliberately (never by guesswork).
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "api"))

os.environ.setdefault("DB_ROLE", "PRODUCTION")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess",
)

from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import get_engine  # noqa: E402

RUN_ID = "EXP-R1-W01-20260918"

QUERIES = {
    "artifacts": """
        SELECT id, source_id, content_hash, created_at, expansion_run_id
        FROM source_artifact WHERE expansion_run_id = :run ORDER BY created_at, id
    """,
    "bundles": """
        SELECT id, artifact_id, quoted_fragment, created_at, expansion_run_id
        FROM evidence_bundle WHERE expansion_run_id = :run ORDER BY created_at, id
    """,
    "candidates": """
        SELECT id, dedup_key, place_id, animal_scope, rule_layer, created_at
        FROM rule_candidate WHERE expansion_run_id = :run ORDER BY created_at, id
    """,
    "places": """
        SELECT p.id, p.canonical_name, p.place_type, p.created_at
        FROM place p ORDER BY p.created_at, p.id
    """,
    "monitors": """
        SELECT id, source_id, url, created_at FROM source_monitor
        WHERE expansion_run_id = :run ORDER BY created_at, id
    """,
}


def main() -> int:
    engine = get_engine()
    out: dict = {"run_id": RUN_ID, "counts": {}, "duplicates": {}}
    with Session(engine) as s:
        total = s.execute(text("SELECT count(*) FROM place")).scalar()
        out["counts"]["place_total"] = total
        for name, q in QUERIES.items():
            rows = [dict(r._mapping) for r in s.execute(text(q), {"run": RUN_ID})]
            out["counts"][name] = len(rows)
            if name == "artifacts":
                groups = defaultdict(list)
                for r in rows:
                    groups[(r["source_id"], r["content_hash"])].append(r["id"])
                out["duplicates"]["artifacts"] = {
                    "groups": sum(1 for v in groups.values() if len(v) > 1),
                    "extra": sum(len(v) - 1 for v in groups.values()),
                    "keep_one_of": [v for v in groups.values() if len(v) > 1],
                }
            elif name == "bundles":
                groups = defaultdict(list)
                for r in rows:
                    groups[(r["artifact_id"], r["quoted_fragment"])].append(r["id"])
                out["duplicates"]["bundles"] = {
                    "groups": sum(1 for v in groups.values() if len(v) > 1),
                    "extra": sum(len(v) - 1 for v in groups.values()),
                    "keep_one_of": [v for v in groups.values() if len(v) > 1],
                }
            elif name == "candidates":
                groups = defaultdict(list)
                for r in rows:
                    groups[r["dedup_key"]].append(r["id"])
                out["duplicates"]["candidates"] = {
                    "groups": sum(1 for v in groups.values() if len(v) > 1),
                    "extra": sum(len(v) - 1 for v in groups.values()),
                    "keep_one_of": [v for v in groups.values() if len(v) > 1],
                }
                out["candidate_status"] = dict(Counter(r.get("status") for r in rows))
            elif name == "places":
                out["places"] = [
                    {"id": r["id"], "name": r["canonical_name"], "type": r["place_type"]}
                    for r in rows
                ]
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
