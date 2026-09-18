"""Post-publish verification for EXP-R1-W01-REVIEW-R1-BATCH-01A.

Read-only against ``petaccess`` (PRODUCTION). Emits a machine-readable report;
never writes. Sections are separated so a failure is attributable:

  1. the 3 published AccessRule rows (place / layer / mandatory / scope / source)
  2. the 2 published RuleException rows and their base binding
  3. base reachability: base scope must govern the exception scope (non-inert)
  4. excluded APPROVED / HOLD / REJECTED must not have been published
  5. audit linkage for all 5 published rows
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))

import psycopg  # noqa: E402

from app.core.config import psycopg_url  # noqa: E402

DB_URL = psycopg_url("postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess")

ACCESS_RULE_PUBLISHED = {
    "w01-1fb3d7f1c7": (
        "47a1d679-1c19-4422-b3b9-02451a19adb8",
        "兴业太古汇",
        "LEGAL",
        "mandatory",
    ),
    "w01-4710a68f56": (
        "f07ffa88-bc3c-4d77-ab38-40f137f225bb",
        "上海博物馆东馆",
        "OPERATOR_POLICY",
        "operator_discretion",
    ),
    "w01-fa5f33f122": (
        "ca0b01c2-10b2-47ea-87bd-f76ac813d1f2",
        "上海博物馆东馆",
        "LEGAL",
        "mandatory",
    ),
}
EXCEPTION_PUBLISHED = {
    "w01-6482477d8d": (
        "64262b3b-d97f-4501-a059-c502deb75e9d",
        "47a1d679-1c19-4422-b3b9-02451a19adb8",
    ),
    "w01-73de8e3357": (
        "39cbdef1-179d-441a-8001-6122ca18bce8",
        "ca0b01c2-10b2-47ea-87bd-f76ac813d1f2",
    ),
}
EXCLUDED_APPROVED = [
    "w01-052d19ccba",
    "w01-7de2f5d75b",
    "w01-6f2bfd39d7",
    "w01-df1645fe68",
    "w01-8ba2b49b01",
    "w01-3a04d4d1aa",
    "w01-305fa08c1e",
    "w01-4e217d5810",
    "w01-d1aee78159",
    "w01-e951785d1b",
]

report: dict = {}
problems: list[str] = []


def main() -> int:
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        # ---------- 1. AccessRule rows --------------------------------------
        cur.execute(
            """
            select ar.id, p.canonical_name, ar.rule_layer, ar.mandatory_level,
                   ar.animal_scope, ar.action, ar.effect, ar.status,
                   ar.source_scope_exact, ar.subject_scope_normalized, ar.normalization_type,
                   ar.source_id, ar.zone_id
            from access_rule ar
            join place p on p.id = ar.place_id
            where ar.id = any(%s)
            order by p.canonical_name
            """,
            ([v[0] for v in ACCESS_RULE_PUBLISHED.values()],),
        )
        ar_rows = cur.fetchall()
        report["access_rule_rows_found"] = len(ar_rows)
        report["access_rules"] = [
            {
                "published_rule_id": r[0],
                "place": r[1],
                "rule_layer": r[2],
                "mandatory_level": r[3],
                "animal_scope": r[4],
                "action": r[5],
                "effect": r[6],
                "status": r[7],
                "source_scope_exact": r[8],
                "subject_scope_normalized": r[9],
                "normalization_type": r[10],
                "has_source_id": r[11] is not None,
                "zone_id": r[12],
            }
            for r in ar_rows
        ]
        by_id = {r[0]: r for r in ar_rows}
        for rule_id, (uuid, place, layer, mand) in ACCESS_RULE_PUBLISHED.items():
            got = by_id.get(uuid)
            if got is None:
                problems.append(f"ACCESS_RULE_MISSING {rule_id} {uuid}")
                continue
            if got[1] != place:
                problems.append(f"PLACE_MISMATCH {rule_id}: {got[1]!r} != {place!r}")
            if got[2] != layer:
                problems.append(f"LAYER_NOT_PRESERVED {rule_id}: {got[2]} != {layer}")
            if got[3] != mand:
                problems.append(f"MANDATORY_NOT_PRESERVED {rule_id}: {got[3]} != {mand}")
            if got[11] is None:
                problems.append(f"ACCESS_RULE_WITHOUT_SOURCE {rule_id}")
            if got[12] is None:
                problems.append(f"ACCESS_RULE_WITHOUT_ZONE {rule_id}")

        # ---------- 2. RuleException rows + binding -------------------------
        cur.execute(
            """
            select re.id, re.rule_id, re.animal_scope, re.effect,
                   re.status, re.source_scope_exact, re.subject_scope_normalized,
                   re.normalization_type, re.source_id
            from rule_exception re
            where re.id = any(%s)
            """,
            ([v[0] for v in EXCEPTION_PUBLISHED.values()],),
        )
        ex_rows = cur.fetchall()
        report["rule_exception_rows_found"] = len(ex_rows)
        report["rule_exceptions"] = [
            {
                "rule_exception_id": r[0],
                "base_published_rule_id": r[1],
                "animal_scope": r[2],
                "effect": r[3],
                "status": r[4],
                "source_scope_exact": r[5],
                "subject_scope_normalized": r[6],
                "normalization_type": r[7],
                "has_source_id": r[8] is not None,
            }
            for r in ex_rows
        ]
        ex_by_id = {r[0]: r for r in ex_rows}
        for rule_id, (uuid, expected_base) in EXCEPTION_PUBLISHED.items():
            got = ex_by_id.get(uuid)
            if got is None:
                problems.append(f"RULE_EXCEPTION_MISSING {rule_id} {uuid}")
                continue
            if got[1] != expected_base:
                problems.append(f"BASE_BINDING_WRONG {rule_id}: {got[1]} != {expected_base}")
            if got[8] is None:
                problems.append(f"RULE_EXCEPTION_WITHOUT_SOURCE {rule_id}")

        # ---------- 3. base reachability (non-inert) ------------------------
        cur.execute(
            """
            select re.id, ar.animal_scope as base_scope, re.animal_scope as exc_scope,
                   ar.rule_layer as base_layer, ar.id as base_id,
                   ar.subject_scope_normalized as base_subject_scope,
                   ar.normalization_type as base_normalization_type,
                   re.subject_scope_normalized as exc_subject_scope
            from rule_exception re join access_rule ar on ar.id = re.rule_id
            where re.id = any(%s)
            """,
            ([v[0] for v in EXCEPTION_PUBLISHED.values()],),
        )
        bind = cur.fetchall()
        report["exception_base_scopes"] = [
            {
                "exception": r[0],
                "base_rule_id": r[4],
                "base_scope": r[1],
                "exception_scope": r[2],
                "base_layer": r[3],
            }
            for r in bind
        ]
        # Reachability via the canonical scope algorithm (single source of truth).
        from app.rulespec.animal_scope import legal_subjects, rule_governs

        def subject_query(scope: str) -> frozenset[str]:
            """The subject set a scope string denotes, via the canonical table."""
            return legal_subjects(scope, scope, "exact") or frozenset({scope})

        for r in bind:
            base_scope, exc_scope = r[1], r[2]
            # Query = the exception's declared subject scope; the base must govern it.
            query = subject_query(str(r[7] or exc_scope))
            ok = rule_governs(query, base_scope, r[5], r[6])
            if not ok:
                problems.append(
                    f"INERT_EXCEPTION {r[0]}: base scope={base_scope} "
                    f"(subject={r[5]}, norm={r[6]}) does not govern {sorted(query)}"
                )
        report["inert_exceptions"] = [p for p in problems if p.startswith("INERT_EXCEPTION")]

        # ---------- 4. forbidden rows must be absent ------------------------
        cur.execute(
            """
            select rc.id, rc.review_status, rc.published_rule_id
            from rule_candidate rc
            where rc.id = any(%s)
            """,
            (EXCLUDED_APPROVED,),
        )
        excl = cur.fetchall()
        report["excluded_approved_state"] = [
            {"candidate_id": r[0], "review_status": r[1], "published_rule_id": r[2]} for r in excl
        ]
        leaked = [r[0] for r in excl if r[2] is not None]
        report["excluded_approved_published"] = leaked
        if leaked:
            problems.append(f"EXCLUDED_APPROVED_PUBLISHED {leaked}")

        cur.execute(
            """
            select rc.id, rc.review_status, rc.published_rule_id
            from rule_candidate rc
            where rc.review_status in ('HOLD','REJECTED') and rc.published_rule_id is not null
            """
        )
        bad = cur.fetchall()
        report["hold_rejected_published"] = [
            {"candidate_id": r[0], "review_status": r[1], "published_rule_id": r[2]} for r in bad
        ]
        if bad:
            problems.append(f"HOLD_OR_REJECTED_PUBLISHED {[r[0] for r in bad]}")

        # ---------- 5. audit linkage ----------------------------------------
        targets = [u for u, *_ in ACCESS_RULE_PUBLISHED.values()] + [
            u for u, *_ in EXCEPTION_PUBLISHED.values()
        ]
        cur.execute(
            """
            select target_id, target_type, action, count(*)
            from audit_log
            where target_id = any(%s)
            group by target_id, target_type, action
            order by target_id, action
            """,
            (targets,),
        )
        audits = cur.fetchall()
        report["audit_by_target"] = [
            {"target_id": r[0], "target_type": r[1], "action": r[2], "count": r[3]} for r in audits
        ]
        covered = {r[0] for r in audits}
        missing = [t for t in targets if t not in covered]
        report["audit_missing_for"] = missing
        if missing:
            problems.append(f"AUDIT_MISSING {missing}")

    report["problems"] = problems
    report["verdict"] = "PASS" if not problems else "FAIL"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
