"""WAVE01_APPROVED_DISPOSITION_AUDIT — classify every approved Wave-01 row.

Why this exists
---------------
The Wave-01 planning manifests must never be re-executed as a whole (they are
now ``OBSOLETE_NON_EXECUTABLE``: their ``other`` bases would supersede Scope
Remodel R2's split rules). Retiring the manifests answers "what may not run";
it does not answer "what *is* the state of each approved row". That is this
audit's only job, and it is deliberately a re-measurement, not a recollection:

    Evidence · Freshness · License · Source Scope · ADR-030 · ADR-031
    Jurisdiction proviso · Holder scope · Service role · Supersession
    Execution contract

are all re-read through the **real** gate against the **real** database, and the
verdict per row comes from what the publisher would actually do with it today.

Three dispositions, and nothing else:

* ``SUPERSEDED_BY_SCOPE_REMODEL``    — a later revision replaced the row's
  semantics. Human decision unchanged (APPROVED stands). Execution status
  permanently non-executable.
* ``CURRENTLY_EXECUTABLE``           — measured publishable right now.
* ``APPROVED_BUT_PUBLISH_BLOCKED``   — a real refusal exists. The refusal is
  recorded; the human decision is **not** rewritten, and nothing is
  auto-repaired.

Rows already published are listed separately as ``ALREADY_PUBLISHED``: they are
not "remaining approved", and counting them here would inflate every number.

Nothing here writes a rule. It only writes its own report.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "services" / "api"))

from evidence_acceptance import (  # noqa: E402
    load_acceptances,
    released_weak_evidence_rows,
)
from human_decisions import APPROVAL_DECISIONS  # noqa: E402
from publish_batch import load_superseded_semantics  # noqa: E402
from publish_reviewed_r1 import (  # noqa: E402
    CREATE_ACCESS_RULE,
    CREATE_RULE_EXCEPTION,
    NOOP_ALREADY_EXISTS,
    SUPERSEDE_ACCESS_RULE,
    DatabaseGate,
    _source_rows,  # noqa: E402
    annotate_from_db,
    build_plan,
    build_session,
    canonical_exception_bindings,
    preflight,
    signed_reviewer,
    table_counts,
)

WRITING_TYPES = {CREATE_ACCESS_RULE, SUPERSEDE_ACCESS_RULE, CREATE_RULE_EXCEPTION}

SUPERSEDED_DISPOSITION = "SUPERSEDED_BY_SCOPE_REMODEL"
EXECUTABLE_DISPOSITION = "CURRENTLY_EXECUTABLE"
BLOCKED_DISPOSITION = "APPROVED_BUT_PUBLISH_BLOCKED"
PUBLISHED_DISPOSITION = "ALREADY_PUBLISHED"

DISPOSITION_ORDER = (
    SUPERSEDED_DISPOSITION,
    EXECUTABLE_DISPOSITION,
    BLOCKED_DISPOSITION,
    PUBLISHED_DISPOSITION,
)


def _reason_for(
    step: Any, row: dict, *, superseded: dict[str, dict], preflight_problems: list[str]
) -> tuple[str, list[str]]:
    """Measured reasons a row landed where it did. Never an interpretation."""
    rule_id = step.rule_id
    if rule_id in superseded:
        record = superseded[rule_id]
        replaced = record.get("superseded_by") or []
        return (
            SUPERSEDED_DISPOSITION,
            [
                record.get("reason") or SUPERSEDED_DISPOSITION,
                "取代方：" + ("、".join(str(x) for x in replaced) if replaced else "未知"),
                str(record.get("measured_evidence") or ""),
            ],
        )
    #: Refusals are checked **before** writability. The planner classifies from
    #: the human decision plus the gate; the preflight refusals live in their own
    #: pass, so a row can plan as CREATE and still be unpublishable. Taking the
    #: planner's word first is how a blocked row would be reported as executable.
    refusals: list[str] = ["preflight: " + p.strip() for p in preflight_problems if rule_id in p]
    if step.gate_status == "BLOCKED":
        refusals.extend(str(x) for x in step.gate_reasons if x)
    refusals.extend(str(x) for x in step.blocked_reasons if x)
    if step.publication_type == NOOP_ALREADY_EXISTS:
        return PUBLISHED_DISPOSITION, ["候选已处于 PUBLISHED，无需重复发布"]
    if refusals:
        if step.depends_on:
            refusals.append("depends_on=" + "、".join(str(x) for x in step.depends_on))
        return BLOCKED_DISPOSITION, refusals
    if step.publication_type in WRITING_TYPES:
        return EXECUTABLE_DISPOSITION, [
            f"实跑 publication_type={step.publication_type}",
            f"gate={step.gate_status}",
            " Evidence / Freshness / License / Source Scope / ADR-030 / ADR-031 / "
            "Jurisdiction proviso / Holder scope / Service role / Supersession / "
            "Execution contract 全部实测通过",
        ]
    return BLOCKED_DISPOSITION, ["未知原因（不得假设可执行）"]


def audit(
    database_url: str,
    *,
    registry: Path | None = None,
    superseded_path: Path | None = None,
    evidence_acceptance: Sequence[str | Path] = (),
) -> dict:
    """Re-measure the whole register and return the machine-readable audit.

    The register is pointed through the publisher's own global so this audit
    cannot accidentally review a *different* file than the publisher publishes
    from — one switch, one artefact.
    """
    if registry is not None:
        import publish_reviewed_r1 as publisher

        publisher.DECISIONS = Path(registry)
    from publish_reviewed_r1 import load_registry

    doc = load_registry()
    rows = doc["rows"]
    superseded = load_superseded_semantics(
        superseded_path or REPO / "docs" / "governance" / "superseded_semantics.json"
    )

    session = build_session(database_url)
    before = table_counts(session)
    annotate_from_db(rows, session)
    bindings = canonical_exception_bindings(doc)

    plan = build_plan(
        rows,
        bindings=bindings,
        gate=DatabaseGate(session),
        revision=str(doc.get("revision") or ""),
        reviewer=str(doc.get("reviewer") or ""),
        already_published={
            r["candidate_id"]
            for r in rows
            if (r.get("_db_review_status") or r.get("review_status")) == "PUBLISHED"
        },
        superseded_semantics=superseded,
    )
    #: Evidence acceptance is opt-in here for the same reason it is in the
    #: publisher: the audit measures what would happen *given the artefacts the
    #: operator intends to rely on*, and must not silently pick up records.
    released_weak_evidence: set[str] = set()
    for path in evidence_acceptance:
        acceptances = load_acceptances(path)
        released, issues = released_weak_evidence_rows(
            rows, acceptances, _source_rows(session, list(acceptances.values()))
        )
        if issues:
            raise SystemExit(
                "REFUSED — evidence acceptance 在当前库状态下不成立：\n  - " + "\n  - ".join(issues)
            )
        released_weak_evidence |= released

    problems = preflight(
        list(rows), None, 10_000, None, released_weak_evidence=released_weak_evidence
    )
    zero_mutation = table_counts(session) == before

    by_rule = {str(r["rule_id"]): r for r in rows}
    items: list[dict] = []
    for step in plan.steps:
        if step.human_decision not in APPROVAL_DECISIONS:
            continue
        row = by_rule.get(step.rule_id, {})
        disposition, reasons = _reason_for(
            step, row, superseded=superseded, preflight_problems=problems
        )
        items.append(
            {
                "rule_id": step.rule_id,
                "candidate_id": step.candidate_id,
                "place_name": step.place_name,
                "zone_name": step.zone_name,
                "layer": step.layer,
                "animal_scope": row.get("animal_scope"),
                "source_scope_exact": row.get("source_scope_exact"),
                "source_type": row.get("source_type"),
                "evidence_strength": row.get("evidence_strength"),
                "human_decision": step.human_decision,
                "human_decision_unchanged": True,
                "disposition": disposition,
                "execution_status": (
                    "SUPERSEDED_BY_SCOPE_REMODEL_R2"
                    if disposition == SUPERSEDED_DISPOSITION
                    else ("NON_EXECUTABLE" if disposition == BLOCKED_DISPOSITION else "EXECUTABLE")
                ),
                "publication_type": step.publication_type,
                "gate_status": step.gate_status,
                "reasons": reasons,
            }
        )

    remaining = [i for i in items if i["disposition"] != PUBLISHED_DISPOSITION]
    counts = {
        name: sum(1 for i in remaining if i["disposition"] == name)
        for name in DISPOSITION_ORDER
        if name != PUBLISHED_DISPOSITION
    }
    counts[PUBLISHED_DISPOSITION] = len(items) - len(remaining)
    items.sort(key=lambda i: (DISPOSITION_ORDER.index(i["disposition"]), i["rule_id"]))
    return {
        "audit_id": "WAVE01_APPROVED_DISPOSITION_AUDIT_R1",
        "revision": str(doc.get("revision") or ""),
        "reviewer": signed_reviewer(rows),
        "at": datetime.now(UTC).isoformat(),
        "database": str(database_url).split("@")[-1],
        "gate_ran": True,
        "zero_db_mutation": zero_mutation,
        "approved_total": len(items),
        "SUPERSEDED_APPROVED": counts[SUPERSEDED_DISPOSITION],
        "CURRENTLY_EXECUTABLE_APPROVED": counts[EXECUTABLE_DISPOSITION],
        "PUBLISH_BLOCKED_APPROVED": counts[BLOCKED_DISPOSITION],
        "ALREADY_PUBLISHED_APPROVED": counts[PUBLISHED_DISPOSITION],
        "items": items,
    }


def render(report: dict) -> str:
    lines = [
        "=== WAVE01_APPROVED_DISPOSITION_AUDIT ===",
        f"REVISION                       = {report['revision']}",
        f"REVIEWER                       = {report['reviewer']}",
        f"DATABASE                       = {report['database']}",
        f"GATE_RAN                       = {report['gate_ran']}",
        f"ZERO_DB_MUTATION               = {report['zero_db_mutation']}",
        f"APPROVED_TOTAL                 = {report['approved_total']}",
        f"SUPERSEDED_APPROVED            = {report['SUPERSEDED_APPROVED']}",
        f"CURRENTLY_EXECUTABLE_APPROVED  = {report['CURRENTLY_EXECUTABLE_APPROVED']}",
        f"PUBLISH_BLOCKED_APPROVED       = {report['PUBLISH_BLOCKED_APPROVED']}",
        f"ALREADY_PUBLISHED_APPROVED     = {report['ALREADY_PUBLISHED_APPROVED']}",
        "",
        "  rule               place              disposition                  reasons",
    ]
    for item in report["items"]:
        lines.append(
            f"  {item['rule_id']:<18} {str(item['place_name'])[:14]:<16} "
            f"{item['disposition']:<28} {item['reasons'][0][:60]}"
        )
        for extra in item["reasons"][1:]:
            lines.append(f"      · {extra}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--database-url", required=True)
    ap.add_argument("--out", default="artifacts/wave01_disposition_audit.json")
    ap.add_argument("--md-out", default=None)
    ap.add_argument("--superseded", default=None)
    ap.add_argument("--registry", required=True, help="发布器消费的同一份登记表（含 gate 字段）")
    ap.add_argument(
        "--evidence-acceptance",
        action="append",
        default=None,
        help="可选；与发布器同语义的 evidence acceptance 文件",
    )
    args = ap.parse_args()

    report = audit(
        args.database_url,
        registry=Path(args.registry),
        superseded_path=Path(args.superseded) if args.superseded else None,
        evidence_acceptance=list(args.evidence_acceptance or ()),
    )
    print(render(report))
    out = Path(args.out)
    if out.parent and not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nWROTE {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
