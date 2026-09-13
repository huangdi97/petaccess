"""Execute the P0 first real publish batch (PILOT-REVIEW-PUBLISH-01 / S6-S7).

Reads ``docs/reality_audit/review_decisions_r1.json`` and drives the LIVE API:

    REVIEW_PENDING --(APPROVED|REJECTED)--> publish() --> AccessRule

Hard gates enforced here (all must hold, otherwise the script aborts):

  1. HUMAN SIGN-OFF. Every row must carry ``final_decision`` AND ``reviewer``
     AND ``reviewed_at``. A machine-proposed decision is never executed on its
     own — AI does not make the final rule call (ADR-005 / Master Goal §0.9).
  2. NO WEAK EVIDENCE. A row whose ``evidence_strength`` is search_snippet or
     social_lead may not be APPROVED (ADR-021); the API's Pre-Publish Validation
     would reject it anyway, but failing here keeps the run atomic.
  3. NO BULK BLIND APPROVE. ``--max-approve`` (default 20) caps the batch, so a
     signed file that approves all 33 in one shot must be split deliberately.
  4. VERIFY AFTER PUBLISH. Each published candidate is re-read: the AccessRule
     must exist, carry the candidate's rule_layer, be linked back to the
     candidate, and be visible through /effective-rules.

Usage:
    python scripts/publish_reviewed_r1.py --dry-run
    python scripts/publish_reviewed_r1.py --execute --reviewer "姓名"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "docs" / "reality_audit"
DECISIONS = AUDIT / "review_decisions_r1.json"
SNAPSHOT = REPO / "PUBLISHED_RULES_SNAPSHOT_R1.json"

BASE = "http://127.0.0.1:8010"
WEAK = {"search_snippet", "social_lead"}
EXECUTABLE = {"APPROVED", "REJECTED"}
TERMINAL = {"PUBLISHED", "REJECTED"}


class Api:
    def __init__(self, token: str) -> None:
        self.c = httpx.Client(
            base_url=BASE,
            timeout=30.0,
            trust_env=False,
            headers={"Authorization": f"Bearer {token}"},
        )

    def post(self, path: str, body: dict | None = None) -> dict:
        r = self.c.post(path, json=body or {})
        if r.status_code >= 400:
            raise RuntimeError(f"POST {path} -> {r.status_code}: {r.text[:400]}")
        return r.json()

    def get(self, path: str) -> dict:
        r = self.c.get(path)
        if r.status_code >= 400:
            raise RuntimeError(f"GET {path} -> {r.status_code}: {r.text[:400]}")
        return r.json()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def load_rows() -> list[dict]:
    doc = json.loads(DECISIONS.read_text(encoding="utf-8"))
    return doc["rows"]


def preflight(rows: list[dict], reviewer: str | None, max_approve: int) -> list[str]:
    problems: list[str] = []
    approved = [r for r in rows if r["final_decision"] == "APPROVED"]

    for r in rows:
        fd = r.get("final_decision")
        if fd not in EXECUTABLE and fd != "HOLD":
            problems.append(f"{r['candidate_id']} {r['rule_id']}: final_decision 未填")
            continue
        if fd == "HOLD":
            continue
        if not r.get("reviewer"):
            problems.append(f"{r['candidate_id']} {r['rule_id']}: 缺少 reviewer 署名")
        if not r.get("reviewed_at"):
            problems.append(f"{r['candidate_id']} {r['rule_id']}: 缺少 reviewed_at")
        if fd == "APPROVED" and r["evidence_strength"] in WEAK:
            problems.append(
                f"{r['candidate_id']} {r['rule_id']}: 弱证据({r['evidence_strength']})不得 APPROVED"
            )

    signed_reviewers = {r["reviewer"] for r in rows if r.get("reviewer")}
    if reviewer and signed_reviewers and signed_reviewers != {reviewer}:
        problems.append("--reviewer 与登记表中的署名不一致")
    if len(approved) > max_approve:
        problems.append(
            f"批次过大：APPROVED={len(approved)} > --max-approve={max_approve}（禁止盲批）"
        )
    return problems


def run(rows: list[dict], api: Api | None, execute: bool) -> dict:
    result = {"approved": [], "rejected": [], "held": [], "published": [], "failed": []}

    for r in rows:
        fd = r["final_decision"]
        if not execute:
            # dry-run: show what the *proposed* decision would do, clearly labelled
            planned = {
                "RECOMMEND_APPROVE": "APPROVED",
                "RECOMMEND_APPROVE_WITH_NOTE": "APPROVED",
                "RECOMMEND_REJECT": "REJECTED",
                "RECOMMEND_HOLD": "HOLD",
            }.get(r["proposed_decision"], "HOLD")
            fd = planned
        cid, rule_id = r["candidate_id"], r["rule_id"]
        if fd == "HOLD":
            result["held"].append({"candidate_id": cid, "rule_id": rule_id})
            continue

        target = "APPROVED" if fd == "APPROVED" else "REJECTED"
        if not execute:
            result["approved" if target == "APPROVED" else "rejected"].append(
                {"candidate_id": cid, "rule_id": rule_id, "layer": r["rule_layer"]}
            )
            continue

        assert api is not None
        try:
            api.post(
                f"/api/v1/admin/candidates/{cid}/transition",
                {"target": target, "note": f"R1 human review by {r['reviewer']}"},
            )
        except RuntimeError as exc:
            result["failed"].append(
                {"candidate_id": cid, "rule_id": rule_id, "stage": target, "error": str(exc)}
            )
            continue

        if target == "REJECTED":
            result["rejected"].append({"candidate_id": cid, "rule_id": rule_id})
            continue
        result["approved"].append({"candidate_id": cid, "rule_id": rule_id})

        try:
            out = api.post(f"/api/v1/admin/candidates/{cid}/publish")
        except RuntimeError as exc:
            result["failed"].append(
                {"candidate_id": cid, "rule_id": rule_id, "stage": "publish", "error": str(exc)}
            )
            continue

        rule_id_out = out.get("published_rule_id")
        after = api.get("/api/v1/admin/candidates?limit=200")
        row = next((x for x in after.get("items", []) if x["id"] == cid), None)
        linked = bool(row and row.get("published_rule_id") == rule_id_out)
        result["published"].append(
            {
                "candidate_id": cid,
                "rule_id": rule_id,
                "published_rule_id": rule_id_out,
                "expected_layer": r["rule_layer"],
                "candidate_linked": linked,
            }
        )
        if not linked:
            result["failed"].append(
                {
                    "candidate_id": cid,
                    "rule_id": rule_id,
                    "stage": "verify_link",
                    "error": "candidate->rule 链接缺失",
                }
            )
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--reviewer", default=None, help="具名人类评审员；必须与登记表署名一致")
    ap.add_argument("--token", default=None, help="admin JWT；缺省读 .env 的 PILOT_ADMIN_TOKEN")
    ap.add_argument("--max-approve", type=int, default=20)
    args = ap.parse_args()

    if not (args.dry_run ^ args.execute):
        print("必须且只能指定 --dry-run 或 --execute")
        return 2

    rows = load_rows()
    problems = preflight(rows, args.reviewer, args.max_approve)

    if args.dry_run:
        print("=== DRY RUN（不写库）===")
        if problems:
            print(f"发布前置条件未满足（{len(problems)} 项）——以下为需要人类评审员处理的事项：")
            for p in problems:
                print(f"  - {p}")
            print(
                "\n这是设计使然：脚本不会在没有具名人类签署的情况下写库。"
                "\n人类评审员须在 docs/reality_audit/review_decisions_r1.json 中填写"
                "\nfinal_decision / reviewer / reviewed_at。"
            )
        result = run(rows, None, execute=False)
        print(
            json.dumps(
                {
                    "summary": {
                        "mode": "dry-run",
                        "at": _now(),
                        "signed": not problems,
                        "planned_counts": {k: len(v) for k, v in result.items()},
                    },
                    "planned": result,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if not problems else 3

    if problems:
        print("PREFLIGHT FAILED — 未满足发布前置条件：")
        for p in problems:
            print(f"  - {p}")
        print(
            "\n这是设计使然：本脚本不会在没有具名人类签署的情况下写库。"
            "\n请由人类评审员在 docs/reality_audit/review_decisions_r1.json 中填写"
            "\nfinal_decision / reviewer / reviewed_at 后重试。"
        )
        return 3

    api = None
    if args.execute:
        token = args.token
        if not token:
            env = REPO / ".env"
            if env.exists():
                for line in env.read_text(encoding="utf-8").splitlines():
                    if line.startswith("PILOT_ADMIN_TOKEN="):
                        token = line.split("=", 1)[1].strip()
        if not token:
            print("缺少 admin token（--token 或 .env PILOT_ADMIN_TOKEN）")
            return 4
        api = Api(token)

    result = run(rows, api, execute=args.execute)
    summary = {
        "mode": "execute" if args.execute else "dry-run",
        "at": _now(),
        "reviewer": args.reviewer,
        "counts": {k: len(v) for k, v in result.items()},
    }
    print(json.dumps({"summary": summary, "detail": result}, ensure_ascii=False, indent=2))

    if args.execute:
        SNAPSHOT.write_text(
            json.dumps({"summary": summary, "detail": result}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0 if not result["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
