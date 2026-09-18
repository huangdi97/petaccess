"""Verify a SCOPE-REMODEL-R2 publish: rule provenance, evidence chain, audit.

Why this exists
---------------
"Four rows were written" is not a publish; it is a write. What makes it a
publish is that every published rule can be walked back to a **source** and an
**evidence bundle** that the human actually reviewed, that the frozen scope
triple survived the trip from candidate to rule, and that the whole thing is in
the audit log under the canonical action vocabulary.

This is a read-only drill. It reports, never repairs.

Usage::

    python scripts/verify_scope_r2_publish.py --db-name petaccess_publish_rehearsal_scope_r2 \
        --batch-file docs/governance/publish_batches/SCOPE_REMODEL_R2_BATCH_02.json \
        --registry docs/expansion/review_decisions_scope_remodel_r2_publishable.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import psycopg

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(str(REPO / "services" / "api")))

from dev_api_server import psycopg_url_for  # noqa: E402

#: Canonical audit vocabulary — a literal action string is a governance defect
#: (core/audit_events.py is the only place they are declared).
AUDIT_ACTIONS_SQL = """
SELECT DISTINCT action FROM audit_log ORDER BY 1
"""

#: The candidate → rule edge is ``rule_candidate.published_rule_id``. It is not
#: ``access_rule.projection_of_rule_id``: that column is only set for *cloned*
#: rows (candidates materialised from an existing rule), and is NULL for a rule
#: created by publishing a candidate — the only trace there is the note text.
RULES_SQL = """
SELECT ar.id, ar.animal_scope, ar.effect, ar.rule_layer, ar.mandatory_level,
       ar.zone_id, ar.place_id, ar.source_id, ar.status,
       ar.source_scope_exact, ar.subject_scope_normalized, ar.normalization_type,
       ar.normative_effect, ar.projection_of_rule_id,
       s.source_type, s.issuer, s.source_url, s.source_availability,
       eb.id AS bundle_id, eb.evidence_class, eb.publisher_type, eb.snapshot_ref,
       art.storage_allowed, art.display_allowed, art.redistribution_allowed,
       rc.id AS candidate_id, rc.review_status
  FROM access_rule ar
  LEFT JOIN source s ON s.id = ar.source_id
  LEFT JOIN rule_candidate rc ON rc.published_rule_id = ar.id
  LEFT JOIN evidence_bundle eb ON eb.id = rc.evidence_bundle_id
  LEFT JOIN source_artifact art ON art.id = eb.artifact_id
 WHERE ar.id = ANY(%s)
"""

#: A carve-out candidate does not become an ``access_rule``: it becomes a
#: ``rule_exception`` hanging off the base rule. Its ``published_rule_id``
#: therefore points at the *base*, and comparing the base's scope triple against
#: the carve-out candidate's reports drift that does not exist. Resolve those
#: rows from ``rule_exception`` instead — the publisher leaves the candidate id
#: in the note, which is the only back-reference there is.
EXCEPTION_SQL = """
SELECT re.id, re.animal_scope, re.effect, NULL::text AS rule_layer,
       NULL::text AS mandatory_level, NULL::uuid AS zone_id, NULL::uuid AS place_id,
       re.source_id, re.status,
       re.source_scope_exact, re.subject_scope_normalized, re.normalization_type,
       re.normative_effect, NULL::uuid AS projection_of_rule_id,
       s.source_type, s.issuer, s.source_url, s.source_availability,
       eb.id AS bundle_id, eb.evidence_class, eb.publisher_type, eb.snapshot_ref,
       art.storage_allowed, art.display_allowed, art.redistribution_allowed,
       rc.id AS candidate_id, rc.review_status
  FROM rule_exception re
  LEFT JOIN source s ON s.id = re.source_id
  LEFT JOIN rule_candidate rc ON rc.id = %s
  LEFT JOIN evidence_bundle eb ON eb.id = rc.evidence_bundle_id
  LEFT JOIN source_artifact art ON art.id = eb.artifact_id
 WHERE re.note LIKE %s
"""

AUDIT_SQL = """
SELECT action, target_type, target_id, actor_role, created_at
  FROM audit_log
 WHERE target_id = ANY(%s)
 ORDER BY created_at
"""

CARVE_OUT_EFFECT = "exempt_from_prohibition"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-name", required=True)
    ap.add_argument("--batch-file", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    url = psycopg_url_for(args.db_name)
    if url is None:
        print(f"REFUSED — 无法解析 {args.db_name} 的 DATABASE_URL")
        return 4

    manifest = json.loads(Path(args.batch_file).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    by_rule = {str(r["rule_id"]): r for r in registry["rows"]}
    selected = [str(x) for x in manifest["candidate_rule_ids"]]

    findings: list[str] = []

    with psycopg.connect(url, connect_timeout=10) as conn, conn.cursor() as cur:
        # Which candidate UUIDs should have become rules?
        expected_candidates = [by_rule[r]["candidate_id"] for r in selected if r in by_rule]

        cur.execute(
            """
            SELECT id, published_rule_id, review_status
              FROM rule_candidate
             WHERE id = ANY(%s)
            """,
            (expected_candidates,),
        )
        cols = [c.name for c in cur.description]
        rules = [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]

        rule_ids = [str(r["published_rule_id"]) for r in rules if r.get("published_rule_id")]
        missing_rule = [
            str(r["id"]) for r in rules if not r.get("published_rule_id")
        ]
        if missing_rule:
            findings.append(f"候选未记录 published_rule_id：{missing_rule}")
        cur.execute(RULES_SQL, (rule_ids,))
        cols2 = [c.name for c in cur.description]
        detailed = [dict(zip(cols2, row, strict=True)) for row in cur.fetchall()]

        by_candidate = {str(r.get("candidate_id")): r for r in registry["rows"]}
        resolved: list[dict] = []
        for row in detailed:
            cid = str(row.get("candidate_id"))
            if by_candidate.get(cid, {}).get("normative_effect") != CARVE_OUT_EFFECT:
                resolved.append(row)
                continue
            cur.execute(EXCEPTION_SQL, (cid, f"%from candidate {cid}%"))
            cols3 = [c.name for c in cur.description]
            exceptions = [dict(zip(cols3, r, strict=True)) for r in cur.fetchall()]
            if not exceptions:
                findings.append(f"{cid}: 例外候选未找到对应 rule_exception 行")
                resolved.append(row)
                continue
            resolved.extend(exceptions)
        detailed = resolved

        cur.execute(AUDIT_SQL, ([str(r["id"]) for r in rules] + expected_candidates,))
        audits = cur.fetchall()

        cur.execute(AUDIT_ACTIONS_SQL)
        vocab = [r[0] for r in cur.fetchall()]

    print(f"batch                  = {manifest['batch_id']}")
    print(f"selected               = {len(selected)}")
    print(f"rules found            = {len(rules)} / expected {len(expected_candidates)}")

    if len(rules) != len(expected_candidates):
        findings.append(
            f"发布规则数 {len(rules)} != 清单条数 {len(expected_candidates)}"
        )

    print("")
    print("== 规则 → 来源 / 证据 / scope 三列 ==")
    for row in detailed:
        rule = by_rule.get(
            next(
                (
                    r
                    for r in selected
                    if by_rule[r]["candidate_id"] == str(row["candidate_id"])
                ),
                "",
            ),
            {},
        )
        print(
            f"  {str(row['id'])[:8]} {str(row['animal_scope']):<6} "
            f"{str(row['effect']):<10} {str(row['rule_layer']):<16} "
            f"status={row['status']}"
        )
        print(f"      source      = {row['issuer']}")
        print(f"      source_url  = {row['source_url']}")
        print(f"      bundle      = {str(row['bundle_id'])[:8]} class={row['evidence_class']}")
        print(
            f"      license     = storage={row['storage_allowed']} "
            f"display={row['display_allowed']} redistribute={row['redistribution_allowed']}"
        )
        print(
            f"      scope       = exact={row['source_scope_exact']!r} "
            f"subject={row['subject_scope_normalized']!r} norm={row['normalization_type']!r}"
        )
        print(f"      candidate   = {str(row['candidate_id'])[:8]} ({row['review_status']})")

        if row["source_id"] is None:
            findings.append(f"{row['id']}: 发布规则缺少 source_id（高影响规则必须有来源）")
        if row["bundle_id"] is None:
            findings.append(f"{row['id']}: 证据链断开（无 evidence_bundle）")
        if row["evidence_class"] != "original":
            findings.append(
                f"{row['id']}: evidence_class={row['evidence_class']!r}，非一手证据"
            )
        if row["storage_allowed"] is not True:
            findings.append(f"{row['id']}: artifact.storage_allowed != True")
        # The frozen scope triple must survive candidate -> rule, or the rule
        # silently stops governing the subject it was written for.
        expected_subject = str(rule.get("subject_scope_normalized"))
        if str(row["subject_scope_normalized"]) != expected_subject:
            findings.append(
                f"{row['id']}: subject_scope_normalized 在发布后漂移 "
                f"（{expected_subject!r} -> {row['subject_scope_normalized']!r}）"
            )
        if str(row["normalization_type"]) != str(rule.get("normalization_type")):
            findings.append(f"{row['id']}: normalization_type 在发布后漂移")
        if str(row["source_scope_exact"]) != str(rule.get("source_scope_exact")):
            findings.append(
                f"{row['id']}: source_scope_exact 未逐字保留 "
                f"（{rule.get('source_scope_exact')!r} -> {row['source_scope_exact']!r}）"
            )
        if str(row["review_status"]) != "PUBLISHED":
            findings.append(
                f"{row['id']}: 候选 review_status={row['review_status']!r}，期望 PUBLISHED"
            )

    print("")
    print("== 审计 ==")
    by_action: dict[str, int] = {}
    for action, *_rest in audits:
        by_action[str(action)] = by_action.get(str(action), 0) + 1
    for action, count in sorted(by_action.items()):
        print(f"  {action}: {count}")
    print(f"  audit rows total = {len(audits)}")
    if not audits:
        findings.append("发布未产生任何 audit_log 记录")
    unknown = sorted(a for a in by_action if a not in vocab)
    if unknown:
        findings.append(f"审计动作不在词表内：{unknown}")
    print(f"  vocabulary size  = {len(vocab)}")

    print("")
    if findings:
        print(f"VERIFY = FAIL（{len(findings)} 项）")
        for f in findings:
            print(f"  - {f}")
    else:
        print("VERIFY = PASS")

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(
                {
                    "batch_id": manifest["batch_id"],
                    "rules": detailed,
                    "audit_by_action": by_action,
                    "findings": findings,
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"WROTE {args.json_out}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
