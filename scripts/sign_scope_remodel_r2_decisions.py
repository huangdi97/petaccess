"""Record huangdi97's decisions in the SCOPE-REMODEL-R2 review register — and nothing else.

Why this file exists
--------------------
`scripts/sign_human_review_decisions.py` is hard-bound to one revision
(``R2-FINAL-R3``, 37 rows, ``FINAL-nn`` numbering). SCOPE-REMODEL-R2 is a
different register with its own identifier scheme, so signing it needs its own
tool rather than a relaxed copy of the old one: the whole point of these scripts
is that a decision is applied **by identifier, never by array position**, and
that the authorisation is written down as data that can be re-read.

This script is deliberately narrow:

* it writes exactly four fields per row (``final_decision`` / ``reviewer`` /
  ``decided_at`` / ``decision_note``) plus the two top-level sign-off fields;
* it refuses to run unless every sign-off field is still blank (never signs
  twice, never overwrites a signature);
* it proves afterwards that **no other byte of the register changed** — the
  evidence / scope / layer / exception objects are hashed before and after.

Hard gates (all must hold before a single byte is written)
----------------------------------------------------------
 1. ``revision`` == ``SCOPE-REMODEL-R2`` and there are exactly 6 rows whose
    candidate-id set equals the authorised set.
 2. Every sign-off field is still blank.
 3. Every authorised decision is in the canonical vocabulary
    (``scripts/human_decisions.HUMAN_DECISIONS``).
 4. The distribution is exactly APPROVED=5 / HOLD=1 / REJECTED=0 /
    APPROVED_WITH_NOTE=0 as authorised.
 5. The single HOLD is the Shanghai Zoo / dog row — the only row whose
    ``legal_applicability_caveat`` is set. A HOLD anywhere else is refused.
 6. The carve-out in ``exception_plan`` depends on a base that is APPROVED and
    sits in the same layer; no cross-layer binding and no executable exception
    on a HOLD/REJECTED base.

Usage::

    python scripts/sign_scope_remodel_r2_decisions.py --check
    python scripts/sign_scope_remodel_r2_decisions.py --write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from human_decisions import (  # noqa: E402
    APPROVED,
    APPROVED_WITH_NOTE,
    HOLD,
    HUMAN_DECISIONS,
    REJECTED,
    is_valid,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "expansion" / "review_decisions_scope_remodel_r2.json"

REVISION = "SCOPE-REMODEL-R2"
REVIEWER = "huangdi97"

FORBIDDEN_REVIEWERS = {"", "agent", "ai", "workbuddy", "opencode", "codex", "admin", "human"}

DISNEY_DOG = "7b595de9-e0c3-4092-aab4-348c4878c296"
DISNEY_CAT = "4580ab21-60c2-4bfb-9a2c-47cde25c5678"
DISNEY_OTHER = "4ca5e55a-6aaf-4ef5-9e0d-cdefbfac98cd"
ZOO_DOG = "a4e2ba26-f542-4ee6-a088-c073096db733"
ZOO_CAT = "27893d75-aa05-422f-9797-2120e81db2ec"
ZOO_OTHER = "2a3de3ab-de8d-4074-a4d0-3039c715893d"

#: The **only** row carrying an unresolved higher-level legal question.
HOLD_ROW = ZOO_DOG

#: The fixed, verbatim reason the reviewer gave for that HOLD. Not paraphrased,
#: not recomputed: this string is the human's justification.
HOLD_REASON = (
    "HIGHER_LEVEL_GUIDE_DOG_LEGAL_APPLICABILITY_UNRESOLVED："
    "这不是否认运营方「动物禁止」的来源事实，而是因为当前 OPERATOR_POLICY dog prohibition "
    "若直接发布，可能对 guide_dog 给出错误禁止答案；"
    "现有 JPROV-001 属 LEGAL layer，不得跨层替代这一未解决的法律适用性问题。"
)

#: The three flags the reviewer required on every APPROVED row.
APPROVE_NOTE = (
    "CURRENT_ONTOLOGY_EXPRESSIBLE_SPLIT = YES；"
    "SOURCE_SCOPE_FULL_REAL_WORLD_EXHAUSTIVE = NO；"
    "UNMODELED_SOURCE_SCOPE_REMAINDER = YES。"
    "未建模的鸟类、爬行类等必须继续保持 UNKNOWN / unsupported，不得解释为 ALLOWED。"
)

#: candidate_id -> (decision, decision_note). This dict *is* the human's
#: authorisation; everything else in this script only enforces it.
AUTHORISED: dict[str, tuple[str, str]] = {
    DISNEY_DOG: (APPROVED, APPROVE_NOTE),
    DISNEY_CAT: (APPROVED, APPROVE_NOTE),
    DISNEY_OTHER: (APPROVED, APPROVE_NOTE),
    ZOO_DOG: (HOLD, HOLD_REASON),
    ZOO_CAT: (APPROVED, APPROVE_NOTE),
    ZOO_OTHER: (APPROVED, APPROVE_NOTE),
}

EXPECTED_DISTRIBUTION = {APPROVED: 5, APPROVED_WITH_NOTE: 0, HOLD: 1, REJECTED: 0}

#: Row fields this tool is allowed to touch. Everything else must hash equal.
SIGNED_FIELDS = ("final_decision", "reviewer", "decided_at", "decision_note")

#: Top-level fields this tool is allowed to touch.
SIGNED_TOP_FIELDS = ("reviewer", "decided_at", "decision_summary")


class Refused(Exception):
    """A hard gate failed. Nothing was written."""


def _digest(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def frozen_digest(registry: dict) -> str:
    """Digest of everything the signature must NOT touch."""
    rows = [
        {k: v for k, v in row.items() if k not in SIGNED_FIELDS}
        for row in registry["rows"]
    ]
    top = {k: v for k, v in registry.items() if k not in (*SIGNED_TOP_FIELDS, "rows")}
    return _digest({"rows": rows, "top": top})


def preflight(registry: dict) -> list[str]:
    problems: list[str] = []
    rows = registry["rows"]

    if registry.get("revision") != REVISION:
        problems.append(f"revision={registry.get('revision')!r}，授权版本为 {REVISION!r}")
    if len(rows) != len(AUTHORISED):
        problems.append(f"行数={len(rows)}，期望 {len(AUTHORISED)}")

    ids = [r.get("candidate_id") for r in rows]
    if len(set(ids)) != len(ids):
        problems.append("candidate_id 重复")
    if set(ids) != set(AUTHORISED):
        problems.append(
            f"candidate_id 集合与授权集不一致：多={sorted(set(ids) - set(AUTHORISED))} "
            f"缺={sorted(set(AUTHORISED) - set(ids))}"
        )

    for row in rows:
        for field in SIGNED_FIELDS:
            if row.get(field) not in (None, ""):
                problems.append(f"{row.get('candidate_id')} 的 {field} 已非空，拒绝二次签署")

    for cid, (decision, _note) in AUTHORISED.items():
        if not is_valid(decision):
            problems.append(f"{cid} 的决定 {decision!r} 不在规范词表 {HUMAN_DECISIONS} 内")

    dist = Counter(decision for decision, _ in AUTHORISED.values())
    for key, expected in EXPECTED_DISTRIBUTION.items():
        if dist.get(key, 0) != expected:
            problems.append(f"决定分布与授权不符：{key}={dist.get(key, 0)}，期望 {expected}")

    # Gate 5: the single HOLD must be the row that actually carries the
    # unresolved legal question, and that row must be the one held.
    by_id = {r["candidate_id"]: r for r in rows}
    held = sorted(cid for cid, (d, _) in AUTHORISED.items() if d == HOLD)
    if held != [HOLD_ROW]:
        problems.append(f"HOLD 行集合={held}，授权只允许 {[HOLD_ROW]}")
    flagged = sorted(
        cid for cid, r in by_id.items() if r.get("legal_applicability_caveat")
    )
    if flagged != [HOLD_ROW]:
        problems.append(f"带 legal_applicability_caveat 的行={flagged}，与 HOLD 不一致")
    if HOLD_ROW in by_id and AUTHORISED[HOLD_ROW][0] == APPROVED:
        problems.append("HOLD_ROW 被标记为 APPROVED")

    # Gate 6: exception dependencies must be closed on approved, same-layer bases.
    approved = {
        cid
        for cid, (d, _) in AUTHORISED.items()
        if d in (APPROVED, APPROVED_WITH_NOTE)
    }
    for entry in registry.get("exception_plan") or []:
        for base in entry.get("bases") or []:
            base_id = base.get("rule_id")
            if base_id not in approved:
                problems.append(f"例外 {entry.get('rule_id')} 挂在非批准基底 {base_id}")
            if not base.get("same_layer"):
                problems.append(f"例外 {entry.get('rule_id')} 跨层绑定到 {base_id}")
        if entry.get("cross_layer_dropped") is None:
            problems.append(f"例外 {entry.get('rule_id')} 缺少 cross_layer_dropped")
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

    print("== 硬闸门 ==")
    print(f"  revision            = {registry['revision']}")
    print(f"  rows                = {len(registry['rows'])}")
    print("  sign-off fields     = 全部空白")
    print(f"  reviewer            = {reviewer}")
    print(f"  decision counts     = {dict(Counter(d for d, _ in AUTHORISED.values()))}")
    print(f"  HOLD                = {HOLD_ROW}")

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
        decision, note = AUTHORISED[row["candidate_id"]]
        row["final_decision"] = decision
        row["reviewer"] = reviewer
        row["decided_at"] = decided_at
        row["decision_note"] = note

    registry["reviewer"] = reviewer
    registry["decided_at"] = decided_at
    registry["decision_summary"] = {
        "signed_rows": len(AUTHORISED),
        "counts": dict(Counter(d for d, _ in AUTHORISED.values())),
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
