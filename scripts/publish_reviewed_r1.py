"""Execute the P0 first real publish batch (PILOT-REVIEW-PUBLISH-01 / S6-S7).

Reads the newest sign-off register under ``docs/reality_audit/`` and drives the
LIVE API. Resolution order is R2-FINAL → R2 → R1, so a sign-off can never be
ignored because the publisher still pointed at a superseded register
(``--registry`` overrides):

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

# The sign-off vocabulary lives next to this script, not inside the app package.
# Kept resolvable when this file is loaded by path (tests do exactly that), where
# the script directory would otherwise not be on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from human_decisions import (  # noqa: E402
    APPROVAL_DECISIONS,
    APPROVED,
    APPROVED_WITH_NOTE,
    EXECUTABLE_DECISIONS,
    HOLD,
    HUMAN_DECISIONS,
    REJECTED,
)

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "docs" / "reality_audit"
#: Decision registers are versioned; the publisher must always read the NEWEST
#: one, otherwise a sign-off written on R2-FINAL would be silently ignored and
#: publishing would consume the superseded R2 register instead.
#: `--registry` overrides; keeping one tool means the gate discipline cannot drift
#: between revisions.
_REGISTER_ORDER = (
    "review_decisions_r2_final.json",  # ADR-025 / ADR-028, supersedes R2
    "review_decisions_r2.json",  # ADR-025 source-faithful scope
    "review_decisions_r1.json",  # legacy
)
DECISIONS = AUDIT / next(name for name in _REGISTER_ORDER if (AUDIT / name).exists())
SNAPSHOT = REPO / "PUBLISHED_RULES_SNAPSHOT_R1.json"

BASE = "http://127.0.0.1:8010"
WEAK = {"search_snippet", "social_lead"}
EXECUTABLE = EXECUTABLE_DECISIONS
TERMINAL = {"PUBLISHED", REJECTED}
VALID_MANDATORY = {"mandatory", "advisory", "operator_discretion", "discretionary"}


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


def _registry_display() -> str:
    """Repo-relative path to the active register, shown in operator messages.

    ``--registry`` may point outside the repo, where ``relative_to`` raises —
    fall back to the path as given rather than crashing mid-error-report.
    """
    try:
        return DECISIONS.relative_to(REPO).as_posix()
    except ValueError:
        return str(DECISIONS)


def load_rows() -> list[dict]:
    doc = json.loads(DECISIONS.read_text(encoding="utf-8"))
    return doc["rows"]


def fetch_candidate_state(api: Api) -> dict[str, dict]:
    """candidate_id -> {rule_layer, mandatory_level} straight from the database.

    The publish endpoint carries whatever the *candidate row* holds, so the
    signed register is not enough on its own: if the row drifted (e.g. it was
    ingested before rule_layer existed and still reads OPERATOR_POLICY), a
    statutory rule would publish without its binding force. Cross-checking the
    two before any write turns that silent downgrade into a hard refusal.

    Paginates: the endpoint caps ``limit`` at 200, so a single call would silently
    miss candidates once the queue grows past that.
    """
    state: dict[str, dict] = {}
    offset = 0
    page_size = 200
    while True:
        page = api.get(f"/api/v1/admin/candidates?limit={page_size}&offset={offset}")
        items = page.get("items", [])
        for item in items:
            state[item["id"]] = {
                "rule_layer": item.get("rule_layer"),
                "mandatory_level": item.get("mandatory_level"),
                "review_status": item.get("review_status"),
            }
        total = page.get("total")
        offset += len(items)
        if not items or (isinstance(total, int) and offset >= total):
            break
    return state


def preflight(
    rows: list[dict],
    reviewer: str | None,
    max_approve: int,
    db_state: dict[str, dict] | None = None,
) -> list[str]:
    problems: list[str] = []
    # Both approval spellings count toward the batch cap: publishing either one
    # creates a rule, so counting only "APPROVED" would understate the batch.
    approved = [r for r in rows if r["final_decision"] in APPROVAL_DECISIONS]

    for r in rows:
        fd = r.get("final_decision")
        if fd not in HUMAN_DECISIONS:
            problems.append(
                f"{r['candidate_id']} {r['rule_id']}: final_decision={fd!r} 不在词表内"
                f"（可用：{' | '.join(HUMAN_DECISIONS)}）"
            )
            continue
        if fd == HOLD:
            continue
        if not r.get("reviewer"):
            problems.append(f"{r['candidate_id']} {r['rule_id']}: 缺少 reviewer 署名")
        if not r.get("reviewed_at"):
            problems.append(f"{r['candidate_id']} {r['rule_id']}: 缺少 reviewed_at")
        if fd == APPROVED_WITH_NOTE and not (r.get("review_note") or "").strip():
            problems.append(
                f"{r['candidate_id']} {r['rule_id']}: APPROVED_WITH_NOTE 必须填写 "
                "review_note（附带意见要随决定一起留痕）"
            )
        if fd in APPROVAL_DECISIONS and r["evidence_strength"] in WEAK:
            problems.append(
                f"{r['candidate_id']} {r['rule_id']}: 弱证据({r['evidence_strength']})"
                f"不得 {fd}（ADR-021）"
            )
        if fd in APPROVAL_DECISIONS:
            # BLK-LAYER-02 / ADR-023: a LEGAL rule without an explicit mandatory
            # level cannot become the resolver floor — refuse, never default it.
            ml = r.get("mandatory_level")
            if r.get("rule_layer") == "LEGAL" and ml is None:
                problems.append(
                    f"{r['candidate_id']} {r['rule_id']}: LEGAL 规则缺少 mandatory_level"
                    "（须为 mandatory/advisory/operator_discretion）"
                )
            if ml is not None and ml not in VALID_MANDATORY:
                problems.append(f"{r['candidate_id']} {r['rule_id']}: 非法 mandatory_level {ml!r}")

        # BLK-LAYER-02 / ADR-023: the register is the reviewed truth, the row is
        # what publish() will actually write. They must agree before we write.
        if db_state is not None:
            row_state = db_state.get(r["candidate_id"])
            if row_state is None:
                problems.append(f"{r['candidate_id']} {r['rule_id']}: 库中不存在该候选")
            else:
                if row_state.get("rule_layer") != r.get("rule_layer"):
                    problems.append(
                        f"{r['candidate_id']} {r['rule_id']}: rule_layer 不一致 "
                        f"（登记表={r.get('rule_layer')!r} 库中={row_state.get('rule_layer')!r}）"
                        "——先运行 scripts/backfill_candidate_rule_layer.py"
                    )
                if row_state.get("mandatory_level") != r.get("mandatory_level"):
                    problems.append(
                        f"{r['candidate_id']} {r['rule_id']}: mandatory_level 不一致 "
                        f"（登记表={r.get('mandatory_level')!r} "
                        f"库中={row_state.get('mandatory_level')!r}）"
                        "——先运行 scripts/backfill_candidate_rule_layer.py"
                    )

    signed_reviewers = {r["reviewer"] for r in rows if r.get("reviewer")}
    if reviewer and signed_reviewers and signed_reviewers != {reviewer}:
        problems.append("--reviewer 与登记表中的署名不一致")
    if len(approved) > max_approve:
        problems.append(
            f"批次过大：批准数={len(approved)} > --max-approve={max_approve}（禁止盲批；"
            f"批准含 {' + '.join(sorted(APPROVAL_DECISIONS))}）"
        )
    return problems


def run(rows: list[dict], api: Api | None, execute: bool) -> dict:
    result: dict[str, list[dict]] = {
        "approved": [],
        "rejected": [],
        "held": [],
        "published": [],
        "failed": [],
    }

    for r in rows:
        fd = r["final_decision"]
        if not execute:
            # dry-run: show what the *proposed* decision would do, clearly labelled
            planned = {
                "RECOMMEND_APPROVE": APPROVED,
                "RECOMMEND_APPROVE_WITH_NOTE": APPROVED_WITH_NOTE,
                "RECOMMEND_REJECT": REJECTED,
                "RECOMMEND_HOLD": HOLD,
            }.get(r["proposed_decision"], HOLD)
            fd = planned
        cid, rule_id = r["candidate_id"], r["rule_id"]
        if fd == HOLD:
            result["held"].append({"candidate_id": cid, "rule_id": rule_id})
            continue

        # APPROVED_WITH_NOTE is an approval, not a rejection. The old one-line
        # ternary here mapped anything that was not exactly "APPROVED" to
        # "REJECTED", which would have inverted a reviewer's decision.
        target = APPROVED if fd in APPROVAL_DECISIONS else REJECTED
        if not execute:
            result["approved" if target == APPROVED else "rejected"].append(
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

        if target == REJECTED:
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
        # BLK-LAYER-02 / ADR-023: the published rule must carry the declared
        # normative layer *and* force — a flattened statutory rule is a silent
        # correctness regression, so either mismatch fails the run.
        expected_layer = r.get("rule_layer")
        published_layer = out.get("rule_layer")
        layer_ok = expected_layer is None or published_layer == expected_layer
        expected_ml = r.get("mandatory_level")
        published_ml = out.get("mandatory_level")
        force_ok = expected_ml is None or published_ml == expected_ml
        result["published"].append(
            {
                "candidate_id": cid,
                "rule_id": rule_id,
                "published_rule_id": rule_id_out,
                "expected_layer": expected_layer,
                "published_layer": published_layer,
                "layer_preserved": layer_ok,
                "expected_mandatory_level": expected_ml,
                "published_mandatory_level": published_ml,
                "candidate_linked": linked,
                "mandatory_preserved": force_ok,
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
        if not layer_ok:
            result["failed"].append(
                {
                    "candidate_id": cid,
                    "rule_id": rule_id,
                    "stage": "verify_rule_layer",
                    "error": (
                        f"rule_layer 未被保留：expected={expected_layer!r} "
                        f"published={published_layer!r}"
                    ),
                }
            )
        if not force_ok:
            result["failed"].append(
                {
                    "candidate_id": cid,
                    "rule_id": rule_id,
                    "stage": "verify_mandatory_level",
                    "error": (
                        f"mandatory_level 未被保留：expected={expected_ml!r} "
                        f"published={published_ml!r}"
                    ),
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
    ap.add_argument(
        "--registry",
        default=None,
        help="评审登记表路径（缺省：按 R2-FINAL → R2 → R1 取最新登记表）",
    )
    args = ap.parse_args()

    global DECISIONS
    if args.registry:
        DECISIONS = Path(args.registry)
    print(f"登记表：{DECISIONS}")

    if not (args.dry_run ^ args.execute):
        print("必须且只能指定 --dry-run 或 --execute")
        return 2

    rows = load_rows()

    # Build the client first: the DB cross-check is part of the preflight, so a
    # drifted candidate row blocks the run *before* anything is written.
    api: Api | None = None
    token = args.token
    if not token:
        env = REPO / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("PILOT_ADMIN_TOKEN="):
                    token = line.split("=", 1)[1].strip()
    db_state: dict[str, dict] | None = None
    if token:
        api = Api(token)
        try:
            db_state = fetch_candidate_state(api)
        except RuntimeError as exc:
            if args.execute:
                print(f"无法读取库中候选状态（发布前必须校验）：{exc}")
                return 4
            print(f"提示：未能读取库中候选状态（{exc}），本次未做登记表↔库一致性校验。")
    elif args.execute:
        print("缺少 admin token（--token 或 .env PILOT_ADMIN_TOKEN）")
        return 4

    problems = preflight(rows, args.reviewer, args.max_approve, db_state)

    if args.dry_run:
        print("=== DRY RUN（不写库）===")
        if problems:
            print(f"发布前置条件未满足（{len(problems)} 项）——以下为需要人类评审员处理的事项：")
            for p in problems:
                print(f"  - {p}")
            print(
                "\n这是设计使然：脚本不会在没有具名人类签署的情况下写库。"
                f"\n人类评审员须在 {_registry_display()} 中填写"
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
                        "db_cross_checked": db_state is not None,
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
            f"\n请由人类评审员在 {_registry_display()} 中填写"
            "\nfinal_decision / reviewer / reviewed_at 后重试。"
        )
        return 3

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
