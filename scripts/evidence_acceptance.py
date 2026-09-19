"""Human-authorised evidence acceptance — the *only* way past ADR-021.

Why this module exists
----------------------
ADR-021 refuses to publish an APPROVED row whose ``evidence_strength`` is
``search_snippet`` or ``social_lead``. That refusal is right and stays right: a
snippet was never verified against the operator's own page.

There is nevertheless a real case the refusal was never written for: a row whose
**source itself is governmental** — a government platform reporting what the
operator says — where no first-party page exists or is reachable *yet*. Century
Park is exactly this. The evidence is not strong, and it does not get to pretend
otherwise. What changes is that a named human reviewer accepted it *knowingly*.

So acceptance is modelled as what it is, not as a strength upgrade:

* the row keeps ``evidence_strength = search_snippet`` in the register and in the
  plan — calling it primary would be a lie that survives into the audit trail;
* a separate, reviewable artefact records who accepted it, which source, and on
  which assertion about that source;
* the assertion is **re-verified against the database on every run**, so an
  acceptance written for a ``government_service`` source cannot leak onto a row
  whose source later became ``official_operator_policy`` (or vice versa);
* the pending first-party gap must be declared, never quietly dropped. Saying
  "operator first-party verified" is forbidden outright — that is the one claim
  this mechanism exists *not* to manufacture.

Nothing here decides anything. It only makes a human decision machine-checkable.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

#: Where signed acceptances live. One file per decision, committed, reviewable.
ACCEPTANCE_DIR = REPO / "docs" / "governance" / "evidence_acceptance"

REQUIRED_FIELDS = (
    "acceptance_id",
    "reviewer",
    "decided_at",
    "candidate_id",
    "rule_id",
    "source_id",
    "declared_source_type",
    "first_party_operator_source_pending",
    "accepted_despite_evidence_strength",
)

#: The source type this mechanism may ever be used for. Narrow on purpose: it is
#: the assertion "a government platform relayed the operator's own wording".
PERMITTED_SOURCE_TYPES = frozenset({"government_service"})

#: Claiming this would be the whole failure mode — asserting first-party status
#: that nobody captured. Refused on sight.
FORBIDDEN_SOURCE_TYPES = frozenset({"official_operator_policy"})


class EvidenceAcceptanceError(Exception):
    """The acceptance record could not be trusted, so nothing is released."""


def load_acceptances(
    *paths: str | Path,
    directory: str | Path | None = None,
) -> dict[str, dict[str, Any]]:
    """``rule_id -> acceptance record``, merged from every file given.

    Later files win on a duplicate ``rule_id``, so a newer decision can replace
    an older one without editing history — but only wholesale, never by patching
    a signature field.
    """
    files: list[Path] = [Path(p) for p in paths]
    if directory is not None:
        files.extend(sorted(Path(directory).glob("*.json")))
    if not directory and not paths:
        files = sorted(ACCEPTANCE_DIR.glob("*.json")) if ACCEPTANCE_DIR.exists() else []

    out: dict[str, dict[str, Any]] = {}
    for path in files:
        if not path.exists():
            raise EvidenceAcceptanceError(f"Evidence acceptance 文件不存在：{path}")
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise EvidenceAcceptanceError(
                f"Evidence acceptance 不是合法 JSON：{path} ({exc})"
            ) from exc
        entries = doc.get("entries") if isinstance(doc, dict) else None
        if not isinstance(entries, list):
            raise EvidenceAcceptanceError(f"Evidence acceptance 缺少 entries 数组：{path}")
        for entry in entries:
            if not isinstance(entry, dict):
                raise EvidenceAcceptanceError(f"Evidence acceptance 记录不是对象：{path}")
            problems = validate_acceptance_record(entry)
            if problems:
                raise EvidenceAcceptanceError(
                    f"Evidence acceptance 记录不合法（{path}）：\n  - " + "\n  - ".join(problems)
                )
            out[str(entry["rule_id"])] = dict(entry, _file=str(path))
    return out


def validate_acceptance_record(entry: Mapping[str, Any]) -> list[str]:
    """Structural problems only — everything database-shaped is checked later.

    Returns rather than raises so one bad file reports *all* of its problems;
    the caller turns a non-empty result into a refusal.
    """
    problems: list[str] = []
    missing = [k for k in REQUIRED_FIELDS if k not in entry]
    if missing:
        problems.append(f"缺少必需字段 {missing}")
    if not str(entry.get("reviewer") or "").strip():
        problems.append("缺少具名 reviewer（匿名接受 = 无人负责）")
    if not str(entry.get("decided_at") or "").strip():
        problems.append("缺少 decided_at")

    declared = str(entry.get("declared_source_type") or "").strip()
    if declared not in PERMITTED_SOURCE_TYPES:
        problems.append(
            f"declared_source_type={declared!r} 不在允许词表 {sorted(PERMITTED_SOURCE_TYPES)} 内"
            "——本机制只用于『政府平台转述园方口径』，不得用于自宣称的一手运营方政策"
        )
    if declared in FORBIDDEN_SOURCE_TYPES:
        problems.append(
            "declared_source_type 不得为 official_operator_policy："
            "该机制永远不会声称 operator first-party verified"
        )
    if entry.get("operator_first_party_verified") is not False:
        problems.append(
            "operator_first_party_verified 必须显式为 false——"
            "缺省为 null 会让『没有反对』被读成『已经确认』"
        )
    if entry.get("first_party_operator_source_pending") is not True:
        problems.append(
            "first_party_operator_source_pending 必须为 true："
            "缺口必须随接受意见一起入档，不得静默丢弃"
        )
    strength = str(entry.get("accepted_despite_evidence_strength") or "").strip()
    if strength not in {"search_snippet", "social_lead"}:
        problems.append(
            f"accepted_despite_evidence_strength={strength!r} 不是弱证据等级——"
            "本机制不用于给强证据盖章"
        )
    return problems


def acceptance_problems(
    entry: Mapping[str, Any],
    source_row: Mapping[str, Any] | None,
) -> list[str]:
    """Does the database still say what the acceptance asserts?

    The record is a claim about a specific source; if that source changed type,
    the acceptance must stop applying. Otherwise a later evidence upgrade would
    silently inherit an acceptance written for weaker facts.
    """
    problems: list[str] = []
    if source_row is None:
        return [f"{entry.get('rule_id')}: 库中查不到 accepted 的 source {entry.get('source_id')}"]

    actual = str(source_row.get("source_type") or "").strip()
    declared = str(entry.get("declared_source_type") or "").strip()
    if actual != declared:
        problems.append(
            f"{entry.get('rule_id')}: source.source_type 已漂移"
            f"（库中={actual!r}，接受记录断言={declared!r}）——"
            "接受记录失效，必须重新审阅，不得沿用"
        )
    if actual in FORBIDDEN_SOURCE_TYPES:
        problems.append(
            f"{entry.get('rule_id')}: source.source_type={actual!r} 声称一手运营方政策，"
            "与本机制的语义冲突"
        )
    if not source_row.get("issuer"):
        problems.append(f"{entry.get('rule_id')}: source 缺少 issuer，无法判断发布主体")
    return problems


def released_weak_evidence_rows(
    rows: Sequence[Mapping[str, Any]],
    acceptances: Mapping[str, Mapping[str, Any]],
    source_rows: Mapping[str, Mapping[str, Any]],
) -> tuple[set[str], list[str]]:
    """Which rows ADR-021 no longer blocks, and why everything else still is.

    Returns ``(released, problems)``. A row is released only when every check
    passed for *its own* acceptance record; any problem for any referenced row
    is returned so the run can refuse rather than partially release.
    """
    released: set[str] = set()
    problems: list[str] = []
    for row in rows:
        rule_id = str(row.get("rule_id") or "")
        entry = acceptances.get(rule_id)
        if entry is None:
            continue
        if str(entry.get("candidate_id") or "") != str(row.get("candidate_id") or ""):
            problems.append(
                f"{rule_id}: 接受记录的 candidate_id 与登记表不一致"
                "（接受是针对某个候选的，不得跨候选沿用）"
            )
            continue
        issues = acceptance_problems(entry, source_rows.get(str(entry.get("source_id") or "")))
        if issues:
            problems.extend(issues)
            continue
        released.add(rule_id)
    return released, problems
