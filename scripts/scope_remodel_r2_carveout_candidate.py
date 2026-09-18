"""SCOPE-REMODEL-R2 — a *new* candidate for the Disney guide-dog carve-out.

Why a new candidate and not a repair
------------------------------------
The frozen carve-out ``w01-305fa08c1e`` is human-signed and cannot be published:
its ``proposed_conditions`` use the legacy key ``type``, which the canonical
publisher schema does not read (ADR-029 §1). The obvious fix — rewrite the key
in place — is exactly what §9 forbids: a candidate that a human already signed
keeps its bytes. The remedy is a new candidate plus a new review.

What this script does
---------------------
It clones the frozen carve-out substance-for-substance and changes one thing:
the condition key, translated by ``normalize_conditions`` — the same ingest
boundary every importer uses. Everything else (source, evidence bundle, scope
columns, layer, effect, holder scope) is copied verbatim. The new row is left at
``REVIEW_PENDING``.

The clone's lineage is recorded in ``raw_text``: ``projection_of_rule_id`` is not
on the admin create schema, so passing it is silently dropped (it is ``None``
for every candidate created through that endpoint, including the six
SCOPE-REMODEL-R2 base rows).

What this script refuses to do
------------------------------
* write ``final_decision`` / ``reviewer`` / ``decided_at``;
* mutate the frozen row (it stays ``REVIEW_PENDING``, still APPROVED in the
  Wave-01 register, which is never touched here);
* publish anything.

Usage
-----

    python scripts/scope_remodel_r2_carveout_candidate.py --plan
    python scripts/scope_remodel_r2_carveout_candidate.py --apply \
        --token-file .tmp/x.jwt --production-confirm
    python scripts/scope_remodel_r2_carveout_candidate.py --verify
    python scripts/scope_remodel_r2_carveout_candidate.py --register
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

from publish_batch import is_reachable_carveout  # noqa: E402

from app.services.condition_ingest import (  # noqa: E402
    CANONICAL_CONDITION_KEY,
    LEGACY_CONDITION_KEY,
    normalize_conditions,
)

FROZEN_CARVE_OUT = "305fa08c-1edd-4cc9-9b7e-554647e44b0a"
#: The new Disney dog base the carve-out must hang from (SCOPE-REMODEL-R2).
DISNEY_DOG_CANDIDATE = "7b595de9-e0c3-4092-aab4-348c4878c296"

MANIFEST_OUT = REPO / "docs" / "expansion" / "scope_remodel_r2_carveout_candidate.json"
REGISTER_OUT = REPO / "docs" / "expansion" / "review_decisions_scope_remodel_r2_carveout.json"

REVISION = "SCOPE-REMODEL-R2"
RUN_ID = "SCOPE-R2-CARVEOUT-20260918"
EXTRACTION_METHOD = "signed_row_remediation_2026_09_18"
EXTRACTION_PROVIDER = "workbuddy-agent"
DEFAULT_BASE_URL = "http://127.0.0.1:8010"

#: Cloned verbatim. ``proposed_conditions`` is cloned *and normalised* — that is
#: the single change this revision makes.
CLONED_COLUMNS = (
    "place_id",
    "zone_id",
    "source_id",
    "animal_scope",
    "action",
    "effect",
    "rule_layer",
    "mandatory_level",
    "normative_effect",
    "holder_scope",
    "evidence_bundle_id",
    "internal_confidence",
    "source_scope_exact",
    "subject_scope_normalized",
    "normalization_type",
)


def db_url(db_name: str) -> str:
    return f"postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/{db_name}"


def load_frozen(conn: psycopg.Connection, candidate_uuid: str) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            select {", ".join(CLONED_COLUMNS)}, proposed_conditions, raw_text
            from rule_candidate
            where id::text = %s
            """,
            (candidate_uuid,),
        )
        row = cur.fetchone()
    if row is None:
        raise SystemExit(f"frozen carve-out {candidate_uuid} not found")
    keys = (*CLONED_COLUMNS, "proposed_conditions", "raw_text")
    return dict(zip(keys, row, strict=True))


def planned_row(db_name: str) -> dict:
    with psycopg.connect(db_url(db_name)) as conn:
        frozen = load_frozen(conn, FROZEN_CARVE_OUT)

    old_conditions = frozen["proposed_conditions"] or []
    new_conditions = normalize_conditions(old_conditions)

    body = {k: frozen[k] for k in CLONED_COLUMNS}
    body.update(
        {
            "proposed_conditions": new_conditions,
            "extraction_method": EXTRACTION_METHOD,
            "extraction_provider": EXTRACTION_PROVIDER,
            "projection_of_rule_id": FROZEN_CARVE_OUT,
            "expansion_run_id": RUN_ID,
            "dedup_key": hashlib.sha256(
                f"{RUN_ID}|{FROZEN_CARVE_OUT}|carve_out".encode()
            ).hexdigest(),
            "raw_text": (
                f"{REVISION} 导盲犬 carve-out 救济候选：克隆自已签署候选 {FROZEN_CARVE_OUT}"
                f"（该候选因 proposed_conditions 使用遗留键 {LEGACY_CONDITION_KEY!r} 被 canonical"
                f" 闸门拒绝；ADR-029 §9 禁止原地改写已签署候选）。本行唯一的改动是在 ingest 边界把"
                f"条件键归一为 {CANONICAL_CONDITION_KEY!r}，其余字段逐字搬运。原候选保持原样、仍为"
                f" APPROVED；本行为新 revision 待审候选，base 为新迪士尼 dog 基底"
                f" {DISNEY_DOG_CANDIDATE}。"
            ),
        }
    )
    return {
        "frozen_candidate_id": FROZEN_CARVE_OUT,
        "base_candidate_id": DISNEY_DOG_CANDIDATE,
        "conditions_before": old_conditions,
        "conditions_after": new_conditions,
        "body": body,
    }


def print_plan(plan: dict) -> None:
    b = plan["body"]
    print(f"{REVISION} 导盲犬 carve-out 救济候选（1 条，REVIEW_PENDING，无任何批准）")
    print(f"  克隆自        : {plan['frozen_candidate_id']}")
    print(f"  挂到 base     : {plan['base_candidate_id']}")
    print(
        f"  {b['place_id'] and '迪士尼'} {b['animal_scope']:<12} "
        f"{b['subject_scope_normalized']:<10} {b['normalization_type']:<10}"
        f" effect={b['effect']} layer={b['rule_layer']}"
    )
    print(f"  source_scope_exact = 「{b['source_scope_exact']}」")
    print("  条件键归一（唯一改动）：")
    for old, new in zip(plan["conditions_before"], plan["conditions_after"], strict=True):
        print(f"    {LEGACY_CONDITION_KEY}={old.get(LEGACY_CONDITION_KEY)!r}")
        print(f"      -> {CANONICAL_CONDITION_KEY}={new.get(CANONICAL_CONDITION_KEY)!r}")


def apply_row(plan: dict, base_url: str, token: str) -> dict:
    client = httpx.Client(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
        trust_env=False,
    )
    resp = client.post("/api/v1/admin/candidates", json=plan["body"])
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
    print(f"  created {cid}")
    return {**plan, "candidate_id": cid}


def verify(db_name: str, created: dict) -> int:
    """Run the publisher's own gate on the new row — measured, not asserted."""
    from dev_api_server import database_url_for
    from publish_reviewed_r1 import GATE_BLOCKED, GATE_PASS, DatabaseGate, build_session

    url = database_url_for(db_name)
    if url is None:
        print("REFUSED — 无法解析 DATABASE_URL")
        return 4
    session = build_session(url)
    gate = DatabaseGate(session)
    failures = 0

    new_verdict = gate.evaluate(
        candidate_id=created["candidate_id"], rule_id=f"sr2-{created['candidate_id'][:8]}"
    )
    old_verdict = gate.evaluate(candidate_id=FROZEN_CARVE_OUT, rule_id="w01-305fa08c1e")
    for label, verdict, expected in (
        ("冻结原候选", old_verdict, GATE_BLOCKED),
        ("新救济候选", new_verdict, GATE_PASS),
    ):
        ok = verdict.status == expected
        failures += 0 if ok else 1
        print(f"  {'PASS' if ok else 'FAIL'} {label}: gate={verdict.status}")
        for reason in verdict.reasons:
            print(f"        {reason}")

    with psycopg.connect(db_url(db_name)) as conn, conn.cursor() as cur:
        cur.execute(
            "select proposed_conditions, review_status, projection_of_rule_id "
            "from rule_candidate where id::text = %s",
            (created["candidate_id"],),
        )
        conds, status, projection = cur.fetchone()
        keys = sorted({k for c in (conds or []) for k in c})
        legacy = LEGACY_CONDITION_KEY in keys
        canonical = CANONICAL_CONDITION_KEY in keys
        ok = canonical and not legacy and status == "REVIEW_PENDING"
        failures += 0 if ok else 1
        # The admin create endpoint does not persist projection_of_rule_id (it is
        # not on the request schema), so the clone's lineage lives in raw_text.
        print(
            f"  {'PASS' if ok else 'FAIL'} 条件键: canonical={canonical} legacy={legacy} "
            f"review_status={status}"
        )
        print(
            f"  NOTE projection_of_rule_id={projection!r}：admin create 不持久化该列，"
            "克隆血缘记录在 raw_text"
        )

        # Reachability against the *new* dog base, with the canonical function.
        cols = (
            "animal_scope",
            "subject_scope_normalized",
            "normalization_type",
            "effect",
            "rule_layer",
        )
        sel = ", ".join(cols)
        cur.execute(
            f"select {sel} from rule_candidate where id::text = %s", (DISNEY_DOG_CANDIDATE,)
        )
        base = dict(zip(cols, cur.fetchone(), strict=True))
        cur.execute(
            f"select {sel} from rule_candidate where id::text = %s", (created["candidate_id"],)
        )
        exc = dict(zip(cols, cur.fetchone(), strict=True))
    verdict = is_reachable_carveout(base, exc)
    ok = verdict is True
    failures += 0 if ok else 1
    print(
        f"  {'PASS' if ok else 'FAIL'} 可达性: {exc['subject_scope_normalized']} on "
        f"{base['subject_scope_normalized']} base = {verdict}"
    )
    print(f"\nverify failures = {failures}")
    return failures


def build_register(db_name: str, created: dict) -> dict:
    """An **empty** review register: every decision cell is null."""
    sql = """
    select rc.animal_scope, rc.subject_scope_normalized, rc.normalization_type,
           rc.effect, rc.rule_layer, rc.mandatory_level, rc.source_scope_exact,
           rc.normative_effect, rc.holder_scope, rc.evidence_bundle_id, rc.zone_id,
           rc.proposed_conditions, p.canonical_name, z.name, s.source_type
      from rule_candidate rc
      join place p on p.id = rc.place_id
      left join zone z on z.id = rc.zone_id
      left join source s on s.id = rc.source_id
     where rc.id::text = %s
    """
    with psycopg.connect(db_url(db_name)) as conn, conn.cursor() as cur:
        cur.execute(sql, (created["candidate_id"],))
        got = cur.fetchone()
    if got is None:
        raise SystemExit("new carve-out candidate not found in the database")
    keys = (
        "animal_scope",
        "subject_scope_normalized",
        "normalization_type",
        "effect",
        "rule_layer",
        "mandatory_level",
        "source_scope_exact",
        "normative_effect",
        "holder_scope",
        "evidence_bundle_id",
        "zone_id",
        "proposed_conditions",
        "place_name",
        "zone_name",
        "source_type",
    )
    st = dict(zip(keys, got, strict=True))
    rule_id = f"sr2-{created['candidate_id'].replace('-', '')[:10]}"
    base_rule_id = f"sr2-{DISNEY_DOG_CANDIDATE.replace('-', '')[:10]}"

    return {
        "_readme": (
            f"{REVISION} 导盲犬 carve-out 救济候选的人工审查登记表（**模板**："
            "final_decision 为 null）。被救济的冻结候选 w01-305fa08c1e 仍是已签署的 APPROVED，"
            "不在本表内、不受本表影响；本表只裁决新候选是否可作为它的替代被发布。"
            "签署后还需把本行与 sr2 迪士尼 dog 基底投影进同一张可发布登记表，"
            "才能构成 dependency-closed 的批次。"
        ),
        "revision": REVISION,
        "expansion_run_id": RUN_ID,
        "generated_at": datetime.now(UTC).isoformat(),
        "remediates_candidate_id": FROZEN_CARVE_OUT,
        "note": (
            "冻结候选 w01-305fa08c1e 的 proposed_conditions 使用遗留键 "
            f"{LEGACY_CONDITION_KEY!r}，canonical 发布闸门无法读取（ADR-029 §1）；"
            "§9 禁止原地改写已签署候选，因此本行为新候选，等待新的人工审查。"
        ),
        "rows": [
            {
                "candidate_id": created["candidate_id"],
                "rule_id": rule_id,
                "place_name": st["place_name"],
                "zone_name": st["zone_name"],
                "zone_id": str(st["zone_id"]) if st["zone_id"] else None,
                "animal_scope": st["animal_scope"],
                "subject_scope_normalized": st["subject_scope_normalized"],
                "normalization_type": st["normalization_type"],
                "effect": st["effect"],
                "rule_layer": st["rule_layer"],
                "mandatory_level": st["mandatory_level"],
                "source_scope_exact": st["source_scope_exact"],
                "normative_effect": st["normative_effect"],
                "holder_scope": st["holder_scope"],
                "evidence_bundle_id": str(st["evidence_bundle_id"]),
                "source_type": st["source_type"],
                "conditions": st["proposed_conditions"] or [],
                "carve_out_of": base_rule_id,
                # --- the human's cells; left blank on purpose ---
                "final_decision": None,
                "reviewer": None,
                "decided_at": None,
                "decision_note": None,
            }
        ],
        "exception_plan": [
            {
                "mode": "rule_exception",
                "rule_id": rule_id,
                "candidate_id": created["candidate_id"],
                "layer": st["rule_layer"],
                "bases": [
                    {"rule_id": base_rule_id, "layer": "OPERATOR_POLICY", "same_layer": True}
                ],
                "cross_layer_dropped": [],
                "note": (
                    f"该 carve-out 挂到 {REVISION} 的迪士尼 dog 基底 {base_rule_id}；"
                    "发布时必须与基底同批，否则禁令会带着未发布的已批准例外上线。"
                ),
            }
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--token-file")
    ap.add_argument("--plan", action="store_true", help="print the row, write nothing")
    ap.add_argument("--apply", action="store_true", help="create the candidate")
    ap.add_argument("--verify", action="store_true", help="run the publisher's gate")
    ap.add_argument("--register", action="store_true", help="write the empty review register")
    ap.add_argument(
        "--production-confirm",
        action="store_true",
        help="required when --db-name is the production database",
    )
    args = ap.parse_args()

    if args.db_name == "petaccess" and args.apply and not args.production_confirm:
        raise SystemExit("refusing to write production without --production-confirm")

    if args.apply:
        plan = planned_row(args.db_name)
        token = Path(args.token_file).read_text(encoding="utf-8").strip()
        created = apply_row(plan, args.base_url, token)
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
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"wrote {MANIFEST_OUT.relative_to(REPO)}")
        return 0

    if args.verify:
        manifest = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
        return 1 if verify(args.db_name, manifest["created"]) else 0

    if args.register:
        manifest = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
        reg = build_register(args.db_name, manifest["created"])
        REGISTER_OUT.write_text(
            json.dumps(reg, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
        )
        print(f"wrote {REGISTER_OUT.relative_to(REPO)} rows=1 decisions_filled=0")
        return 0

    print_plan(planned_row(args.db_name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
