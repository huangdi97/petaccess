"""Record huangdi97's decision on the SCOPE-REMODEL-R2 carve-out remedial row.

Why this file exists
--------------------
The frozen carve-out ``w01-305fa08c1e`` is signed APPROVED but cannot be
published: its ``proposed_conditions`` use the legacy key ``type``, which the
canonical gate cannot read, and ADR-029 §9 forbids editing a signed candidate in
place. The remedy is a new candidate plus a new review. This script is the
tool that records that new review — the same discipline as
``sign_scope_remodel_r2_decisions.py``, narrowed to one row.

The decision itself is **data**, not code: it comes from ``AUTHORISED`` below,
which is a transcription of what the reviewer said. Nothing here computes,
derives or upgrades a decision.

Hard gates (all must hold before a single byte is written)
----------------------------------------------------------
 1. ``revision`` == ``SCOPE-REMODEL-R2`` and the register holds exactly the one
    remedial candidate.
 2. Every sign-off field is still blank (never signs twice).
 3. The decision is in the canonical vocabulary (``scripts/human_decisions``).
 4. The remediation target is the frozen ``w01-305fa08c1e``, and the file has
    not been re-pointed at some other candidate.
 5. **Dependency closure**: the base this carve-out hangs off
    (``sr2-7b595de9e0`` / Disney dog) is APPROVED in the already-signed
    SCOPE-REMODEL-R2 register. An exception approved against a base that was
    never approved — or held — is refused.
 6. No cross-layer binding.
 7. After writing, everything except the sign-off fields hashes equal.

Usage::

    python scripts/sign_scope_remodel_r2_carveout_decision.py --check
    python scripts/sign_scope_remodel_r2_carveout_decision.py --write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from human_decisions import (  # noqa: E402
    APPROVED,
    HUMAN_DECISIONS,
    is_valid,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "expansion" / "review_decisions_scope_remodel_r2_carveout.json"
BASE_REGISTRY = ROOT / "docs" / "expansion" / "review_decisions_scope_remodel_r2.json"

REVISION = "SCOPE-REMODEL-R2"
REVIEWER = "huangdi97"

FORBIDDEN_REVIEWERS = {"", "agent", "ai", "workbuddy", "opencode", "codex", "admin", "human"}

#: The remedial candidate created by scripts/scope_remodel_r2_carveout_candidate.py.
CARVEOUT = "69e0916a-2f13-4b1e-b601-f8731e6869d1"

#: The frozen row this one remediates. Must still be what the file says.
REMEDIATES = "305fa08c-1edd-4cc9-9b7e-554647e44b0a"

#: The Disney dog base the carve-out hangs off, in both identifier spaces.
BASE_RULE_ID = "sr2-7b595de9e0"
BASE_CANDIDATE_ID = "7b595de9-e0c3-4092-aab4-348c4878c296"

#: The reviewer's decision, transcribed. Not computed, not inferred.
DECISION = APPROVED

DECISION_NOTE = (
    "维持本人对 w01-305fa08c1e（上海迪士尼乐园／导盲犬例外）的原有批准："
    "该冻结候选因 proposed_conditions 使用遗留键 'type' 而无法通过 canonical 发布闸门，"
    "ADR-029 §9 禁止原地改写已签署候选，故就同一实质内容另立新候选重签。"
    "新候选与冻结候选在来源、证据包、作用域三列、层级、效果、holder_scope 与条件语义上逐字一致，"
    "唯一改动为条件键规范化（type -> condition_type，走 canonical normalize_conditions）。"
    "发布约束：必须与基底 sr2-7b595de9e0（迪士尼 dog 禁令）同批发布，"
    "不得先发布基底而把已批准的例外留在批外。"
)

SIGNED_FIELDS = ("final_decision", "reviewer", "decided_at", "decision_note")
SIGNED_TOP_FIELDS = ("reviewer", "decided_at", "decision_summary")


class Refused(Exception):
    """A hard gate failed. Nothing was written."""


def _digest(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def frozen_digest(registry: dict) -> str:
    rows = [{k: v for k, v in row.items() if k not in SIGNED_FIELDS} for row in registry["rows"]]
    top = {k: v for k, v in registry.items() if k not in (*SIGNED_TOP_FIELDS, "rows")}
    return _digest({"rows": rows, "top": top})


def preflight(registry: dict) -> list[str]:
    problems: list[str] = []
    rows = registry["rows"]

    if registry.get("revision") != REVISION:
        problems.append(f"revision={registry.get('revision')!r}，授权版本为 {REVISION!r}")
    if len(rows) != 1:
        problems.append(f"行数={len(rows)}，本登记表只授权 1 行")

    ids = [r.get("candidate_id") for r in rows]
    if ids != [CARVEOUT]:
        problems.append(f"candidate_id={ids}，授权集为 ['{CARVEOUT}']")

    if registry.get("remediates_candidate_id") != REMEDIATES:
        problems.append(
            f"remediates_candidate_id={registry.get('remediates_candidate_id')!r}，"
            f"应为 {REMEDIATES!r}"
        )

    for row in rows:
        for field in SIGNED_FIELDS:
            if row.get(field) not in (None, ""):
                problems.append(f"{row.get('candidate_id')} 的 {field} 已非空，拒绝二次签署")

    if not is_valid(DECISION):
        problems.append(f"决定 {DECISION!r} 不在规范词表 {HUMAN_DECISIONS} 内")

    # Gate 5 — dependency closure against the already-signed base register.
    base_reg = json.loads(BASE_REGISTRY.read_text(encoding="utf-8"))
    base_rows = {r.get("candidate_id"): r for r in base_reg["rows"]}
    base_row = base_rows.get(BASE_CANDIDATE_ID)
    if base_row is None:
        problems.append(f"基底候选 {BASE_CANDIDATE_ID} 不在已签署登记表中")
    else:
        base_decision = base_row.get("final_decision")
        if base_decision != APPROVED:
            problems.append(
                f"基底 {BASE_CANDIDATE_ID} 的 final_decision={base_decision!r}，"
                f"例外不能挂在非 APPROVED 基底上"
            )
        if not base_row.get("decided_at"):
            problems.append(f"基底 {BASE_CANDIDATE_ID} 未签署（decided_at 为空）")

    # Gate 6 — no cross-layer binding, base must be named.
    for entry in registry.get("exception_plan") or []:
        for base in entry.get("bases") or []:
            if base.get("rule_id") != BASE_RULE_ID:
                problems.append(f"例外挂到未授权基底 {base.get('rule_id')}")
            if not base.get("same_layer"):
                problems.append(f"例外跨层绑定到 {base.get('rule_id')}")
        if entry.get("cross_layer_dropped") is None:
            problems.append("例外缺少 cross_layer_dropped")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只跑硬闸门，不写")
    parser.add_argument("--write", action="store_true", help="通过闸门后机械写入决定")
    parser.add_argument("--reviewer", default=REVIEWER)
    parser.add_argument(
        "--decided-at",
        default=None,
        help="timezone-aware ISO-8601；缺省取执行时刻本机时区",
    )
    args = parser.parse_args()

    if not (args.check ^ args.write):
        print("必须且只能指定 --check 或 --write")
        return 2

    reviewer = (args.reviewer or "").strip()
    if reviewer.lower() in FORBIDDEN_REVIEWERS:
        print(f"REFUSED: reviewer={reviewer!r} 不是具名人类评审员")
        return 2

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    before = frozen_digest(registry)

    problems = preflight(registry)
    if problems:
        print("HARD GATE REFUSED — 未写入任何字节")
        for item in problems:
            print(f"  - {item}")
        return 3

    base_reg = json.loads(BASE_REGISTRY.read_text(encoding="utf-8"))
    base_row = next(r for r in base_reg["rows"] if r.get("candidate_id") == BASE_CANDIDATE_ID)

    print("== 硬闸门 ==")
    print(f"  revision          = {registry['revision']}")
    print(f"  rows              = {len(registry['rows'])}")
    print(f"  candidate_id      = {CARVEOUT}")
    print(f"  remediates        = {REMEDIATES}")
    print("  sign-off fields   = 全部空白")
    print(f"  decision          = {DECISION}")
    print(f"  base              = {BASE_RULE_ID} / {base_row['final_decision']}")
    print(f"  base decided_at   = {base_row.get('decided_at')}")
    print(f"  reviewer          = {reviewer}")

    if args.check:
        print("\nCHECK ONLY — 未写入。")
        return 0

    decided_at = args.decided_at or datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        parsed = datetime.fromisoformat(decided_at.replace("Z", "+00:00"))
    except ValueError as exc:
        print(f"REFUSED: decided_at 不是合法 ISO-8601：{decided_at!r}（{exc}）")
        return 3
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        print(f"REFUSED: decided_at 缺少时区：{decided_at!r}")
        return 3

    for row in registry["rows"]:
        row["final_decision"] = DECISION
        row["reviewer"] = reviewer
        row["decided_at"] = decided_at
        row["decision_note"] = DECISION_NOTE

    registry["reviewer"] = reviewer
    registry["decided_at"] = decided_at
    registry["decision_summary"] = {
        "signed_rows": 1,
        "counts": {DECISION: 1},
        "note": "计数直接来自授权决定本身，不是二次推断。",
    }

    if frozen_digest(registry) != before:
        print("REFUSED: 签署过程中改动了非签署字段，回滚（未写盘）")
        return 3

    REGISTRY.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"\nWRITTEN — decided_at = {decided_at}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
