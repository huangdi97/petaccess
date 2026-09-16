"""Record a named human's GOV-01 decision in the review register — and nothing else.

Why this file exists
--------------------
The register and the decision sheet must be signed by a **named human**
(ADR-005 / Master Goal §0.9: AI does not make the final rule call). Before this
script the mechanical part of that had no tool, so it would have been done by
hand — the one place where a typo silently signs the wrong row, or where an
array index gets trusted and every decision lands one row off.

This tool is deliberately narrow. It writes exactly three fields
(``final_decision`` / ``reviewer`` / ``reviewed_at``), it refuses to run unless
the frozen object it was authorised against is provably still frozen, and it
never invents a judgement of its own.

Hard gates (all must hold before a single byte is written)
----------------------------------------------------------
 1. ``revision`` is the authorised one.
 2. 37 rows, recommendation distribution 23 / 9 / 5.
 3. The candidate-id set equals the frozen baseline snapshot's.
 4. Every sign-off field is still **blank** — this tool never signs twice, and
    it will not overwrite a signature that is already there with a different
    one.
 5. ``FINAL-nn`` → ``rule_id`` → ``candidate_id`` agree three ways: the reviewer's
    own numbering (quick table), the register's row order, and the register's own
    ``rule_id``/``candidate_id`` pairing. Decisions are keyed by **identifier**,
    never by array position.
 6. No ``RuleException`` binding crosses a layer, and no executable exception
    hangs off a base that is not recommended for approval.

Anything the human did not authorise is out of scope: this script has no code
path that touches evidence, sources, scope, layer, freshness, licence, the
``proposed_*`` machine proposal, or any ``RuleException`` binding.

Usage::

    python scripts/sign_human_review_decisions.py --check
    python scripts/sign_human_review_decisions.py --write --reviewed-at "<ISO-8601 with offset>"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from human_decisions import APPROVED, HOLD, HUMAN_DECISIONS, REJECTED  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "reality_audit"
REGISTRY = AUDIT / "review_decisions_r2_final.json"
BASELINE = AUDIT / "snapshots" / "baseline.json"
QUICK_TABLE = ROOT / "HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md"
DECISION_SHEET = ROOT / "HUMAN_REVIEW_DECISIONS_R2_FINAL.json"

#: The revision this signature is authorised against. A mismatch is a stop, not
#: something to adapt to: signing a revision the authorising document did not
#: name is exactly the failure this constant exists to prevent.
REVISION = "R2-FINAL-R3"

#: Stable internal id of the human reviewer. Never an agent, a role, or a tool.
REVIEWER = "huangdi97"

#: §2: words that must never end up in the ``reviewer`` field.
FORBIDDEN_REVIEWERS = {"", "agent", "ai", "workbuddy", "opencode", "codex", "admin", "human"}

#: The FINAL numbering the reviewer actually read, and the decision they made.
#: FINAL-01..05 rejected, FINAL-06..14 held, FINAL-15..37 approved.
AUTHORISED: dict[str, str] = {
    **{f"FINAL-{i:02d}": REJECTED for i in range(1, 6)},
    **{f"FINAL-{i:02d}": HOLD for i in range(6, 15)},
    **{f"FINAL-{i:02d}": APPROVED for i in range(15, 38)},
}

EXPECTED_ROWS = 37
EXPECTED_DISTRIBUTION = {"RECOMMEND_APPROVE": 23, "RECOMMEND_HOLD": 9, "RECOMMEND_REJECT": 5}


class Refused(Exception):
    """A hard gate failed. Nothing was written."""


def load() -> tuple[dict, dict, dict]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    sheet = json.loads(DECISION_SHEET.read_text(encoding="utf-8"))
    return registry, baseline, sheet


def final_numbering() -> dict[str, str]:
    """FINAL-nn -> rule_id, read from the sheet the reviewer signed against."""
    text = QUICK_TABLE.read_text(encoding="utf-8")
    found: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"\|\s*\*\*(FINAL-\d+)\*\*.*?\|\s*`([a-z0-9\-.]+)`", line)
        if match:
            found[match.group(1)] = match.group(2)
    return found


def resolve(registry: dict) -> list[tuple[str, str, dict]]:
    """Return (final number, rule_id, row) in the reviewer's own numbering.

    Three independent facts must agree before a decision is applied: the quick
    table says FINAL-nn is ``rule_id``; the register's row order puts that
    ``rule_id`` at position nn; and the register itself maps that ``rule_id`` to
    a ``candidate_id``. Any disagreement is a refusal — a decision is never
    applied by array index.
    """
    rows = registry["rows"]
    numbering = final_numbering()
    missing = [k for k in AUTHORISED if k not in numbering]
    if missing:
        raise Refused(f"速填表缺少编号：{missing}")
    if len(numbering) != len(AUTHORISED):
        raise Refused(f"速填表编号数 {len(numbering)} != 授权数 {len(AUTHORISED)}")

    by_rule: dict[str, dict] = {}
    for row in rows:
        if row["rule_id"] in by_rule:
            raise Refused(f"rule_id 重复：{row['rule_id']}")
        by_rule[row["rule_id"]] = row

    out: list[tuple[str, str, dict]] = []
    for index, number in enumerate(sorted(AUTHORISED), start=1):
        rule_id = numbering[number]
        if rule_id not in by_rule:
            raise Refused(f"{number} 指向的 rule_id 不在登记表中：{rule_id}")
        if rows[index - 1]["rule_id"] != rule_id:
            sheet_rule = rows[index - 1]["rule_id"]
            raise Refused(
                f"{number} 与登记表行序不一致：速填表={rule_id} 登记表第{index}行={sheet_rule}"
            )
        row = by_rule[rule_id]
        if not row.get("candidate_id"):
            raise Refused(f"{rule_id} 缺少 candidate_id")
        out.append((number, rule_id, row))
    if len({row["candidate_id"] for _, _, row in out}) != EXPECTED_ROWS:
        raise Refused("candidate_id 不唯一")
    return out


def preflight(registry: dict, baseline: dict, sheet: dict) -> list[str]:
    problems: list[str] = []
    rows = registry["rows"]

    if registry.get("revision") != REVISION:
        problems.append(f"revision={registry.get('revision')!r}，授权版本为 {REVISION!r}")
    if len(rows) != EXPECTED_ROWS:
        problems.append(f"行数={len(rows)}，期望 {EXPECTED_ROWS}")

    counts = Counter(r.get("proposed_decision") for r in rows)
    for key, expected in EXPECTED_DISTRIBUTION.items():
        if counts.get(key, 0) != expected:
            problems.append(f"建议分布漂移：{key}={counts.get(key, 0)}，期望 {expected}")

    if sorted(r["candidate_id"] for r in rows) != sorted(baseline["candidate_ids"]):
        problems.append("candidate_id 集合与冻结基线快照不一致")

    signed = [
        r["rule_id"]
        for r in rows
        if r.get("final_decision") or r.get("reviewer") or r.get("reviewed_at")
    ]
    if signed:
        problems.append(f"登记表已有非空签署字段：{signed[:5]}（共 {len(signed)} 行）")
    if sheet.get("reviewer") or sheet.get("reviewed_at"):
        problems.append("逐条决策文件已有非空 reviewer/reviewed_at")
    if any(d.get("final_decision") for d in sheet.get("decisions", [])):
        problems.append("逐条决策文件已有非空 final_decision")

    crossings = [
        (e["rule_id"], b.get("rule_id"))
        for e in registry.get("exception_plan") or []
        for b in e.get("bases") or []
        if not b.get("same_layer")
    ]
    if crossings:
        problems.append(f"RuleException 跨层绑定：{crossings}")
    offenders = [
        e["rule_id"]
        for e in registry.get("exception_plan") or []
        if e.get("executable")
        and any(b.get("decision") != "RECOMMEND_APPROVE" for b in e.get("bases") or [])
    ]
    if offenders:
        problems.append(f"HOLD/REJECT base 上存在可执行例外：{offenders}")

    if sheet.get("human_decisions") != list(HUMAN_DECISIONS):
        problems.append("逐条决策文件的决策词表与 canonical 词表不一致")
    return problems


def check_reviewed_at(value: str) -> str:
    """The signature timestamp must be real, timezone-aware ISO-8601."""
    text = (value or "").strip()
    if not text:
        raise Refused("reviewed_at 为空")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refused(f"reviewed_at 不是合法 ISO-8601：{text!r}（{exc}）") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise Refused(f"reviewed_at 缺少时区（naive datetime 不被接受）：{text!r}")
    return text


def write(registry: dict, sheet: dict) -> None:
    # The register is written exactly the way its generator writes it
    # (scripts/gen_human_review_packet_r2_final.py::_jdump, compact with
    # ", " / ": " separators) so the diff is the three signed fields and nothing
    # else — no reflow, no reformat.
    REGISTRY.write_text(
        json.dumps(registry, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    DECISION_SHEET.write_text(
        json.dumps(sheet, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只跑硬闸门，不写")
    parser.add_argument("--write", action="store_true", help="通过闸门后写入三个签署字段")
    parser.add_argument("--reviewer", default=REVIEWER)
    parser.add_argument("--reviewed-at", default=None, help="timezone-aware ISO-8601")
    args = parser.parse_args()

    if not (args.check ^ args.write):
        print("必须且只能指定 --check 或 --write")
        return 2

    reviewer = (args.reviewer or "").strip()
    if reviewer.lower() in FORBIDDEN_REVIEWERS:
        print(f"REFUSED: reviewer={reviewer!r} 不是具名人类评审员")
        return 2

    registry, baseline, sheet = load()
    try:
        problems = preflight(registry, baseline, sheet)
        if problems:
            raise Refused("；".join(problems))
        resolved = resolve(registry)
        if args.write:
            reviewed_at = check_reviewed_at(args.reviewed_at or "")
    except Refused as exc:
        print("HARD GATE REFUSED — 未写入任何字节")
        print(f"  reason = {exc}")
        return 3

    print("== 硬闸门 ==")
    print(f"  revision            = {registry['revision']}")
    print(f"  rows                = {len(registry['rows'])}")
    print(
        f"  distribution        = {dict(Counter(r['proposed_decision'] for r in registry['rows']))}"
    )
    print("  sign-off fields     = 全部空白")
    print(f"  FINAL->candidate    = {len(resolved)} 条三重一致")
    print(f"  reviewer            = {reviewer}")
    print(f"  decision counts     = {dict(Counter(AUTHORISED.values()))}")

    if args.check:
        print("\nCHECK ONLY — 未写入。")
        return 0

    for number, _rule_id, row in resolved:
        row["final_decision"] = AUTHORISED[number]
        row["reviewer"] = reviewer
        row["reviewed_at"] = reviewed_at
    sheet["reviewer"] = reviewer
    sheet["reviewed_at"] = reviewed_at
    sheet_by_cid = {d["candidate_id"]: d for d in sheet["decisions"]}
    for number, _rule_id, row in resolved:
        sheet_by_cid[row["candidate_id"]]["final_decision"] = AUTHORISED[number]

    write(registry, sheet)
    print(f"\nWRITTEN — reviewed_at = {reviewed_at}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
