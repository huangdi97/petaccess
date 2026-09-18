"""Stage the ADR-030 statutory-proviso candidates, and (only on request) activate one.

Two very different acts live in this one script on purpose, so the difference
between them stays visible:

* **stage** (default) writes the reviewed-packet rows as ``status='proposed'`` /
  ``review_status='not_reviewed'``. The resolver never reads those — staging is
  what an AI is allowed to do, because it changes no answer.
* **activate** additionally requires ``--reviewer`` and flips a row to
  ``current`` + ``reviewed_active``. That is a jurisdiction-level change in legal
  effect for every venue in the jurisdiction; it is a Human Decision and this
  script refuses to invent a reviewer name.

Nothing here infers the instrument: ``instrument_source_ids`` is read verbatim
from the packet, because "these two source rows are the same statute" is an
editorial determination, not a guess.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))

DEFAULT_PACKET = REPO / "docs" / "expansion" / "jurisdiction_proviso_candidates_adr030.json"

PLACEHOLDER_REVIEWERS = {"", "ai", "system", "auto", "drill", "rehearsal-drill", "drill_only"}


def _conn(db_name: str):
    import psycopg

    from app.core.config import psycopg_url

    return psycopg.connect(
        psycopg_url(f"postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/{db_name}")
    )


def _assert_target(db_name: str, *, production_confirm: bool) -> None:
    """Refuse an unregistered database, and refuse production without a flag.

    The production flag is not a formality. Activating a proviso changes the
    legal effect of every venue in the jurisdiction, so "I typed the wrong
    database name" must not be survivable as an accident — which is exactly what
    happened the first time this script was run.
    """
    from app.db.safety import DatabaseRole, classify_database_name

    role = classify_database_name(db_name)
    if role is DatabaseRole.UNKNOWN:
        raise SystemExit(f"REFUSED: {db_name} is not a registered database role.")
    if role is DatabaseRole.PRODUCTION and not production_confirm:
        raise SystemExit(
            f"REFUSED: {db_name} is PRODUCTION. Pass --production-confirm only after a "
            "human reviewer has actually signed off on this activation."
        )


def stage(cur, candidates: list[dict], *, activate: bool, reviewer: str) -> dict:
    out = {"staged": 0, "activated": 0, "skipped": 0}
    for c in candidates:
        cid = c["candidate_id"]
        status = "current" if activate else c.get("status", "proposed")
        review_status = "reviewed_active" if activate else c.get("review_status", "not_reviewed")
        reviewed_at = datetime.now(UTC) if activate else None
        reviewed_by = reviewer if activate else None

        cur.execute("select id from jurisdiction_exception where id = %s", (cid,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                """
                insert into jurisdiction_exception (
                  id, created_at, updated_at,
                  jurisdiction_level, jurisdiction_id, authority, instrument_type,
                  document_name, clause_ref, proviso_text_ref, source_id,
                  binding, instrument_source_ids, applies_to_layer, applies_to_effects,
                  animal_scope, subject_scope_normalized, normalization_type,
                  normative_effect, holder_scope, action, effect,
                  status, review_status, reviewed_at, reviewed_by
                ) values (
                  %s, now(), now(),
                  %s, %s, %s, %s,
                  %s, %s, %s, %s,
                  %s, %s::jsonb, %s, %s::jsonb,
                  %s, %s, %s,
                  %s, %s, %s, %s,
                  %s, %s, %s, %s
                )
                """,
                (
                    cid,
                    c["jurisdiction_level"],
                    c["jurisdiction_id"],
                    c["authority"],
                    c["instrument_type"],
                    c["document_name"],
                    c.get("clause_ref"),
                    c.get("proviso_text_ref"),
                    c["source_id"],
                    c.get("binding", "instrument"),
                    json.dumps(c.get("instrument_source_ids", [])),
                    c.get("applies_to_layer"),
                    json.dumps(c.get("applies_to_effects", ["prohibited"])),
                    c["animal_scope"],
                    c.get("subject_scope_normalized"),
                    c.get("normalization_type"),
                    c.get("normative_effect"),
                    c.get("holder_scope"),
                    c.get("action"),
                    c.get("effect"),
                    status,
                    review_status,
                    reviewed_at,
                    reviewed_by,
                ),
            )
            out["staged"] += 1
        else:
            cur.execute(
                """
                update jurisdiction_exception set
                  status = %s, review_status = %s, reviewed_at = %s, reviewed_by = %s,
                  updated_at = now()
                where id = %s
                """,
                (status, review_status, reviewed_at, reviewed_by, cid),
            )
            out["skipped"] += 1
        if activate:
            out["activated"] += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db-name", required=True)
    ap.add_argument("--packet", default=str(DEFAULT_PACKET))
    ap.add_argument(
        "--activate",
        action="store_true",
        help="flip staged rows to current + reviewed_active (HUMAN DECISION)",
    )
    ap.add_argument("--reviewer", default="", help="required with --activate; a human signature")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--production-confirm",
        action="store_true",
        help="required when --db-name is the production database",
    )
    args = ap.parse_args()

    if args.activate:
        if not args.reviewer or args.reviewer.strip().lower() in PLACEHOLDER_REVIEWERS:
            raise SystemExit(
                "REFUSED: --activate requires a real --reviewer. "
                "Activating a jurisdiction-level proviso is a Human Decision; "
                "this script will not sign it."
            )
    elif args.reviewer:
        raise SystemExit("REFUSED: --reviewer without --activate would silently do nothing.")

    _assert_target(args.db_name, production_confirm=args.production_confirm)
    packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    candidates = packet["candidates"]

    with _conn(args.db_name) as c, c.cursor() as cur:
        result = stage(cur, candidates, activate=args.activate, reviewer=args.reviewer.strip())
        c.commit()

    result["db"] = args.db_name
    result["activated"] = bool(args.activate)
    result["reviewer"] = args.reviewer.strip() if args.activate else ""
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for k, v in result.items():
            print(f"{k} = {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
