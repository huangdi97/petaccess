"""SCOPE-REMODEL-R2 — materialise the new-revision candidates for gate B2.

The two over-broad source terms (「动物」 at 上海动物园, 「动物（导盲犬除外）」 at
上海迪士尼乐园) are recorded in the *signed* Wave-01 revision as
``animal_scope=other`` + ``normalization_type=exact``. That claim is false:
``other`` is ``{other_pet}`` under ADR-025, while 「动物」 is every animal. The
canonical gate rejects them with ``SOURCE_SCOPE_NORMALIZATION_NOT_SEMANTICALLY_
EQUIVALENT``, and they can never be published as written.

A signed candidate is immutable, and a decision is not a technical detail that
may be re-derived. So the repair is **a new revision, not an edit**: this script
clones each frozen base into three exhaustive decomposition rows
(``dog`` / ``cat`` / ``other``, ``normalization_type=compound_term_split``),
keeping ``source_scope_exact`` byte-for-byte, and leaves every new row at
``REVIEW_PENDING`` for a human.

What this script refuses to do
------------------------------

* write ``final_decision`` / ``reviewer`` / ``decided_at``;
* mutate or supersede-in-place the frozen rows (they stay ``REVIEW_PENDING``,
  still APPROVED in the register — the register is never touched here);
* publish anything (no ``/candidates/{id}/publish``).

Usage
-----

    python scripts/scope_remodel_r2_candidates.py --plan
    python scripts/scope_remodel_r2_candidates.py --apply --token-file .tmp/x.jwt
    python scripts/scope_remodel_r2_candidates.py --verify
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
import psycopg

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "services" / "api"))

# The canonical judgements, reused rather than restated.
from publish_batch import is_reachable_carveout  # noqa: E402

from app.rulespec.source_scope_semantics import (  # noqa: E402
    validate_source_scope_semantic_compatibility,
)

PROPOSALS = REPO / "docs" / "expansion" / "scope_remodel_proposals_r2.json"
MANIFEST_OUT = REPO / "docs" / "expansion" / "scope_remodel_r2_candidates.json"
REGISTER_OUT = REPO / "docs" / "expansion" / "review_decisions_scope_remodel_r2.json"

REVISION = "SCOPE-REMODEL-R2"
RUN_ID = "SCOPE-R2-20260918"
EXTRACTION_METHOD = "broad_term_split_2026_09_18"
EXTRACTION_PROVIDER = "workbuddy-agent"
DEFAULT_BASE_URL = "http://127.0.0.1:8010"

#: Columns cloned verbatim from the frozen base. Everything not listed here is
#: either derived (scope, dedup) or must stay empty until a human signs.
CLONED_COLUMNS = (
    "place_id",
    "zone_id",
    "source_id",
    "action",
    "effect",
    "rule_layer",
    "mandatory_level",
    "proposed_conditions",
    "normative_effect",
    "holder_scope",
    "evidence_bundle_id",
    "internal_confidence",
    "source_scope_exact",
)


def db_url(db_name: str) -> str:
    return f"postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/{db_name}"


def dedup_key(base_id: str, subject: str) -> str:
    raw = f"{RUN_ID}|{base_id}|{subject}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_base(conn: psycopg.Connection, candidate_uuid: str) -> dict:
    """Read the frozen candidate row. Read-only; never updated here."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select id, place_id, zone_id, source_id, action, effect, rule_layer,
                   mandatory_level, proposed_conditions, normative_effect,
                   holder_scope, evidence_bundle_id, internal_confidence,
                   source_scope_exact, raw_text, review_status
            from rule_candidate
            where id::text = %s
            """,
            (candidate_uuid,),
        )
        row = cur.fetchone()
    if row is None:
        raise SystemExit(f"base candidate {candidate_uuid} not found")
    keys = (
        "id",
        "place_id",
        "zone_id",
        "source_id",
        "action",
        "effect",
        "rule_layer",
        "mandatory_level",
        "proposed_conditions",
        "normative_effect",
        "holder_scope",
        "evidence_bundle_id",
        "internal_confidence",
        "source_scope_exact",
        "raw_text",
        "review_status",
    )
    return dict(zip(keys, row, strict=True))


def planned_rows(db_name: str) -> list[dict]:
    """Every row this revision would create. No decisions, no writes."""
    payload = json.loads(PROPOSALS.read_text(encoding="utf-8"))
    out: list[dict] = []
    with psycopg.connect(db_url(db_name)) as conn:
        for target in payload["targets"]:
            base = load_base(conn, target["candidate_uuid"])
            for spec in target["proposed_rows"]:
                subject = spec["subject_scope_normalized"]
                body = {k: base[k] for k in CLONED_COLUMNS}
                body.update(
                    {
                        "animal_scope": subject,
                        "subject_scope_normalized": subject,
                        "normalization_type": spec["normalization_type"],
                        "extraction_method": EXTRACTION_METHOD,
                        "extraction_provider": EXTRACTION_PROVIDER,
                        "projection_of_rule_id": base["id"],
                        "expansion_run_id": RUN_ID,
                        "dedup_key": dedup_key(base["id"], subject),
                        "raw_text": (
                            f"{REVISION} 拆分自冻结候选 {base['id']}：来源术语"
                            f"「{base['source_scope_exact']}」归一为 {subject}"
                            f"（{spec['normalization_type']}），逐字保留原术语。"
                            f"原候选仍为 APPROVED 且未发布；本行为新 revision 待审候选。"
                        ),
                    }
                )
                out.append(
                    {
                        "place": target["place"],
                        "revision": REVISION,
                        "supersedes_candidate_id": base["id"],
                        "subject_scope_normalized": subject,
                        "body": body,
                    }
                )
    return out


def print_plan(rows: list[dict]) -> None:
    print(f"{REVISION}: {len(rows)} 待审候选（全部 REVIEW_PENDING，无任何批准）")
    for r in rows:
        b = r["body"]
        print(
            f"  {r['place']:<10} {b['subject_scope_normalized']:<6}"
            f" {b['animal_scope']:<6} {b['normalization_type']:<20}"
            f" src=「{b['source_scope_exact']}」"
            f" layer={b['rule_layer']} effect={b['effect']}"
        )


def apply_rows(rows: list[dict], base_url: str, token: str, db_name: str) -> list[dict]:
    client = httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
        trust_env=False,
    )
    created: list[dict] = []
    for r in rows:
        resp = client.post("/api/v1/admin/candidates", json=r["body"])
        resp.raise_for_status()
        cid = resp.json()["id"]
        tr = client.post(
            f"/api/v1/admin/candidates/{cid}/transition",
            json={
                "target": "REVIEW_PENDING",
                "note": f"{REVISION}/{RUN_ID}: 待人工审核（不得自动批准或发布）",
            },
        )
        tr.raise_for_status()
        created.append({**r, "candidate_id": cid})
        print(f"  created {cid}  {r['place']} / {r['subject_scope_normalized']}")
    return created


def verify(db_name: str, created: list[dict]) -> int:
    """Re-run the canonical gate against the rows as stored. Read-only."""
    failures = 0
    with psycopg.connect(db_url(db_name)) as conn:
        for row in created:
            cid = row["candidate_id"]
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select source_scope_exact, subject_scope_normalized,
                           normalization_type, animal_scope, effect, rule_layer
                    from rule_candidate where id::text = %s
                    """,
                    (cid,),
                )
                got = cur.fetchone()
            if got is None:
                print(f"  MISSING {cid}")
                failures += 1
                continue
            term, subj, ntype = got[0], got[1], got[2]
            sc = validate_source_scope_semantic_compatibility(term, subj, ntype)
            ok = sc.compatible
            failures += 0 if ok else 1
            print(
                f"  {'PASS' if ok else 'FAIL'} {row['place']:<10}"
                f" {str(subj):<6} {ntype:<20} 「{term}」"
            )
            if not ok:
                print(f"        reason: {sc.reason}")

        # The point of the Disney split: its approved carve-out becomes
        # reachable. Measured, not asserted — the frozen base fails this.
        payload = json.loads(PROPOSALS.read_text(encoding="utf-8"))
        for target in payload["targets"]:
            carve = target.get("proposed_carve_out")
            if not carve:
                continue
            new_dog = next(
                (
                    c
                    for c in created
                    if c["supersedes_candidate_id"] == target["candidate_uuid"]
                    and c["subject_scope_normalized"] == "dog"
                ),
                None,
            )
            if new_dog is None:
                continue
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select animal_scope, subject_scope_normalized,
                           normalization_type, effect, rule_layer
                    from rule_candidate where id::text = %s
                    """,
                    (carve["candidate_rule_id"].replace("w01-", "")[:8],),
                )
                cur.fetchone()  # shape probe only; id is a 12-char prefix
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select animal_scope, subject_scope_normalized,
                           normalization_type, effect, rule_layer
                    from rule_candidate
                    where replace(id::text, '-', '') like %s
                    """,
                    (carve["candidate_rule_id"].replace("w01-", "") + "%",),
                )
                exc_row = cur.fetchone()
                cur.execute(
                    """
                    select animal_scope, subject_scope_normalized,
                           normalization_type, effect, rule_layer
                    from rule_candidate where id::text = %s
                    """,
                    (new_dog["candidate_id"],),
                )
                base_row = cur.fetchone()
            cols = (
                "animal_scope",
                "subject_scope_normalized",
                "normalization_type",
                "effect",
                "rule_layer",
            )
            exc = dict(zip(cols, exc_row, strict=True)) if exc_row else None
            base = dict(zip(cols, base_row, strict=True))
            if exc is None:
                print("  carve-out row not found — reachability unevaluable")
                continue
            verdict = is_reachable_carveout(base, exc)
            label = {True: "reachable", False: "unreachable"}.get(verdict, "unevaluable")
            failures += 0 if verdict is True else 1
            flag = "PASS" if verdict is True else "FAIL"
            print(
                f"  {flag} carve-out {label}: {exc['subject_scope_normalized']}"
                f" on {base['subject_scope_normalized']} base"
            )
    print(f"\nverify failures = {failures}")
    return failures


def build_register(db_name: str, created: list[dict]) -> dict:
    """An **empty** review register: every decision cell is null.

    The template is mechanical — it copies the stored row and leaves the human
    columns blank. Filling them is the reviewer's act, not this script's.
    """
    payload = json.loads(PROPOSALS.read_text(encoding="utf-8"))
    by_base = {t["candidate_uuid"]: t for t in payload["targets"]}
    rows: list[dict] = []
    with psycopg.connect(db_url(db_name)) as conn:
        for c in created:
            cid = c["candidate_id"]
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select rc.animal_scope, rc.subject_scope_normalized,
                           rc.normalization_type, rc.effect, rc.rule_layer,
                           rc.mandatory_level, rc.source_scope_exact,
                           rc.normative_effect, rc.evidence_bundle_id,
                           rc.zone_id, p.canonical_name, z.name, s.source_type
                    from rule_candidate rc
                    join place p on p.id = rc.place_id
                    left join zone z on z.id = rc.zone_id
                    left join source s on s.id = rc.source_id
                    where rc.id::text = %s
                    """,
                    (cid,),
                )
                got = cur.fetchone()
            if got is None:
                continue
            target = by_base.get(c["supersedes_candidate_id"], {})
            before = {(b["query"]): b["effect"] for b in target.get("before", [])}
            after = {(a["query"]): a["effect"] for a in target.get("after", [])}
            rows.append(
                {
                    "candidate_id": cid,
                    "supersedes_candidate_id": c["supersedes_candidate_id"],
                    "place_name": got[10],
                    "zone_name": got[11],
                    "zone_id": str(got[9]) if got[9] else None,
                    "animal_scope": got[0],
                    "subject_scope_normalized": got[1],
                    "normalization_type": got[2],
                    "effect": got[3],
                    "rule_layer": got[4],
                    "mandatory_level": got[5],
                    "source_scope_exact": got[6],
                    "normative_effect": got[7],
                    "evidence_bundle_id": str(got[8]) if got[8] else None,
                    "source_type": got[12],
                    "answer_before": before,
                    "answer_after": after,
                    # --- the human's cells; left blank on purpose ---
                    "final_decision": None,
                    "reviewer": None,
                    "decided_at": None,
                    "decision_note": None,
                }
            )

    exception_plan = []
    for c in created:
        target = by_base.get(c["supersedes_candidate_id"], {})
        carve = target.get("proposed_carve_out")
        if carve and c["subject_scope_normalized"] == carve["attaches_to"]:
            exception_plan.append(
                {
                    "mode": "carve_out",
                    "rule_id": carve["candidate_rule_id"],
                    "layer": None,
                    "bases": [
                        {
                            "rule_id": c["candidate_id"],
                            "same_layer": True,
                            "layer": None,
                        }
                    ],
                    "cross_layer_dropped": [],
                    "note": (
                        f"该 carve-out 改挂到新 revision 的 {carve['attaches_to']} 基底；"
                        f"原基底（{c['supersedes_candidate_id']}）scope 为 other，"
                        f"该例外在其上不可达。"
                    ),
                }
            )

    return {
        "revision": REVISION,
        "expansion_run_id": RUN_ID,
        "generated_at": datetime.now(UTC).isoformat(),
        "reviewer": None,
        "decided_at": None,
        "note": (
            f"{REVISION} 人工审查登记表（**模板**：所有 final_decision 为 null）。"
            f"对 {len(rows)} 条过宽来源术语拆分候选逐条裁决；签署后方可发布。"
            f"被取代的冻结候选仍为 APPROVED，不在本表内，不受本表影响。"
        ),
        "rows": rows,
        "exception_plan": exception_plan,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--token-file")
    ap.add_argument("--plan", action="store_true", help="print the rows, write nothing")
    ap.add_argument("--apply", action="store_true", help="create the candidates")
    ap.add_argument("--verify", action="store_true", help="re-run the gate on stored rows")
    ap.add_argument("--register", action="store_true", help="write the empty review register")
    ap.add_argument(
        "--production-confirm",
        action="store_true",
        help="required when --db-name is the production database",
    )
    args = ap.parse_args()

    if args.db_name == "petaccess" and (args.apply and not args.production_confirm):
        raise SystemExit("refusing to write production without --production-confirm")

    if args.apply:
        rows = planned_rows(args.db_name)
        token = Path(args.token_file).read_text(encoding="utf-8").strip()
        created = apply_rows(rows, args.base_url, token, args.db_name)
        MANIFEST_OUT.write_text(
            json.dumps(
                {
                    "revision": REVISION,
                    "run_id": RUN_ID,
                    "db": args.db_name,
                    "created": created,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"wrote {MANIFEST_OUT.relative_to(REPO)} rows={len(created)}")
        return 0

    if args.verify:
        manifest = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
        return 1 if verify(args.db_name, manifest["created"]) else 0

    if args.register:
        manifest = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
        reg = build_register(args.db_name, manifest["created"])
        REGISTER_OUT.write_text(
            json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {REGISTER_OUT.relative_to(REPO)} rows={len(reg['rows'])} decisions_filled=0")
        return 0

    print_plan(planned_rows(args.db_name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
