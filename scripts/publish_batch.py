"""Explicit publish-batch selection — a manifest, not a slice.

Why this exists
---------------
``--max-approve`` is an **anti-blind-batch upper bound**, nothing more. It says
"never publish more than N rules in one run"; it cannot say "publish exactly
these twelve". Using it as a selector would mean publishing whatever the register
happened to sort first — a decision made by array order, not by a human.

The first real publish therefore selects through a versioned manifest:

    docs/governance/publish_batches/R2_FINAL_R3_BATCH_01.json

The manifest answers exactly one question — *which already-approved candidates
does this batch contain* — and nothing else. It deliberately does **not** repeat
``final_decision``: permission still comes from the signed register
(``--registry``), so a manifest can never upgrade a HOLD into a publish. Editing a
manifest cannot widen authority; it can only narrow the selection.

This module owns five refusals, which is why it is separate from the planner:

1. **Identity** — the manifest must name the revision the register is signed at,
   the reviewer who signed it, and a batch id. A manifest for R2-FINAL-R2 pointed
   at an R2-FINAL-R3 register is a cross-revision selection and is refused.
2. **Selection** — every id must exist in the register, appear once, and carry a
   human approval. HOLD and REJECTED ids are refused rather than filtered out: a
   batch that silently drops half its rows is not the batch anyone reviewed.
3. **Dependency closure** — every selected carve-out needs its base rule either
   already published or selected *earlier in the same batch*. "Earlier" is
   enforced by position because the manifest is also the execution order.
4. **No prohibition without its REACHABLE approved carve-out** — the mirror
   image. Publishing ``fp-legal-dog`` while the approved guide-dog carve-out
   stays unpublished would briefly tell a guide-dog handler "prohibited" when a
   signed rule says otherwise. So a carve-out **that can actually fire** must
   also be in this batch or already published. A deliberate partial publish needs
   an explicit override, which this round does not grant.

   *Reachable* is the whole point, and it is why this refusal was rewritten. An
   approved carve-out whose base does not semantically govern the carve-out's own
   subject is **inert**: it can never fire, so its absence changes nothing for
   any user. Gating a base on an inert carve-out would let a modelling defect
   hold real rules hostage. Such a carve-out is recorded as
   ``UNREACHABLE_APPROVED_CARVE_OUT`` → ``SEMANTIC_REMODEL_REQUIRED`` and does
   **not** block its base.
5. **Zero inert rules in the batch** — the batch may not *contain* an inert
   carve-out either. Publishing a rule that can never apply is worse than not
   publishing it: it is audited, linked and counted, and it silently promises
   access it does not deliver.

All five are *refusals*, never automatic repairs.
"""

# NOTE: no ``from __future__ import annotations``. ``@dataclass`` resolves string
# annotations through ``sys.modules[cls.__module__]``, which does not exist when
# this module is loaded by path — which is exactly how the governance tests load
# the publisher (``spec_from_file_location``).

import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]

#: The sign-off vocabulary has exactly one source (``scripts/human_decisions.py``).
#: Reachable when this module is loaded by path, as the governance tests do it.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from human_decisions import (  # noqa: E402
    APPROVAL_DECISIONS,
    HOLD,
    REJECTED,
)

#: Where versioned batch manifests live. One file per batch, committed, reviewed.
BATCH_DIR = REPO / "docs" / "governance" / "publish_batches"

#: Required keys. ``candidate_rule_ids`` holds registry ``rule_id`` values — the
#: stable human-facing identifiers (``dl-pet-ban``), not the UUID candidate ids.
#: The name is kept because it is the batch's contract; the tool resolves each one
#: to its candidate through the signed register, never through a guess.
REQUIRED_KEYS = ("revision", "batch_id", "reviewer", "candidate_rule_ids")

#: Optional keys, allowed so a manifest can explain itself without a schema change.
#: ``supersedes_planning_manifest`` / ``supersede_reason`` record that this batch
#: replaced an earlier *planning* artefact, and ``excluded_approved`` lists the
#: human-approved rows that measurement found non-executable. All three are
#: explanatory: none can widen the selection, because the selection is still the
#: ``candidate_rule_ids`` list and permission still comes from the signed
#: register. Refusing to allow them would push the reasoning out of the artefact
#: that reviewers actually read, which is worse than the small schema growth.
OPTIONAL_KEYS = (
    "note",
    "_schema",
    "supersedes_batch",
    "supersedes_planning_manifest",
    "supersede_reason",
    "excluded_approved",
    "deferred",
)

#: The follow-up state for an approved carve-out that can never fire. Recorded,
#: never repaired here: the fix is a semantic remodel of the animal-scope model,
#: which is a human decision (see
#: ``docs/governance/OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL.md``). It is *not*
#: HOLD and *not* REJECTED — the human approval stands, unpublished.
SEMANTIC_REMODEL_REQUIRED = "SEMANTIC_REMODEL_REQUIRED"


class BatchManifestError(Exception):
    """The manifest could not be read or is not a manifest at all."""


def _canonical_rule_governs():
    """Import the ADR-025 scope matcher, wherever this module was loaded from.

    The reachability rule below must *reuse* the canonical semantics rather than
    restate them. A second, hand-written scope comparison would drift from
    ``animal_scope.py`` the first time the ontology moves, and then a "reachable"
    carve-out would be a claim made by a copy nobody maintains.

    The import is deferred and path-tolerant because the governance tests load
    this module by file path (``spec_from_file_location``), without the API
    package on ``sys.path``.
    """
    import sys

    api_dir = REPO / "services" / "api"
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))
    from app.rulespec.animal_scope import rule_governs

    return rule_governs


def is_reachable_carveout(
    base: Mapping[str, Any],
    exception: Mapping[str, Any],
    *,
    governs=None,
) -> bool | None:
    """Can ``exception`` ever fire, given the base it is carved out of?

    Three conditions, all necessary:

    1. **same layer** — an ``OPERATOR_POLICY`` carve-out on a ``LEGAL`` base is
       not a carve-out, it is an operator out-voting a statute.
    2. **same intended relationship** — the caller supplies the base; the
       register's ``exception_plan`` already states that this carve-out was
       written *of* that base, so the pairing is not inferred here.
    3. **the base semantically governs the carve-out's own subject** — the
       actual reachability question. A ``RuleException`` is applied only when the
       base is in scope for the query, so if the base does not cover the
       carve-out's subject the carve-out can never be reached.

    Returns ``None`` when it cannot be evaluated (a row with no recorded scope).
    ``None`` is deliberately not ``True``: "we cannot tell" must not license a
    publish, and it must not block one either — it is reported as unevaluable.
    """
    exception_subject = exception.get("subject_scope_normalized") or exception.get("animal_scope")
    if not exception_subject:
        return None
    base_layer = base.get("rule_layer")
    exception_layer = exception.get("rule_layer")
    if base_layer and exception_layer and base_layer != exception_layer:
        return False
    check = governs if governs is not None else _canonical_rule_governs()
    return bool(
        check(
            frozenset({str(exception_subject)}),
            base.get("animal_scope"),
            base.get("subject_scope_normalized"),
            base.get("normalization_type"),
        )
    )


def carve_out_reachability(
    rows: Sequence[Mapping[str, Any]],
    bindings: Mapping[str, Any],
    *,
    governs=None,
) -> dict[str, dict[str, Any]]:
    """Per carve-out: which of its same-layer bases it can actually reach.

    The result distinguishes four states, because collapsing them is exactly
    how an inert rule ships:

    * ``reachable`` — at least one same-layer base governs the carve-out subject.
    * ``unreachable`` — bases exist, were evaluated, and none governs it. The
      carve-out is published, linked, audited and inert.
    * ``unevaluable`` — scope data is missing, so nothing is claimed.
    * ``no_base`` — the register records no same-layer base at all.

    ``base_states`` keeps the *per-base* verdict, because the obligation in
    refusal 4 is a property of a (base, carve-out) pair: the same carve-out can
    be reachable from one base and inert against another.
    """
    by_rule = {str(r["rule_id"]): r for r in rows}
    check = governs if governs is not None else _canonical_rule_governs()
    out: dict[str, dict[str, Any]] = {}
    for rule_id, binding in bindings.items():
        exception_row = by_rule.get(rule_id)
        if exception_row is None:
            continue
        bases = tuple(str(b) for b in getattr(binding, "bases", ()))
        base_states: dict[str, str] = {}
        reachable: list[str] = []
        unevaluable: list[str] = []
        for base_id in bases:
            base_row = by_rule.get(base_id)
            if base_row is None:
                continue
            verdict = is_reachable_carveout(base_row, exception_row, governs=check)
            if verdict is True:
                base_states[base_id] = "reachable"
                reachable.append(base_id)
            elif verdict is None:
                base_states[base_id] = "unevaluable"
                unevaluable.append(base_id)
            else:
                base_states[base_id] = "unreachable"
        if not bases:
            state = "no_base"
        elif reachable:
            state = "reachable"
        elif unevaluable and len(unevaluable) == len(bases):
            state = "unevaluable"
        else:
            state = "unreachable"
        out[rule_id] = {
            "rule_id": rule_id,
            "bases": bases,
            "reachable_bases": tuple(reachable),
            "base_states": base_states,
            "state": state,
        }
    return out


def carve_out_state(
    reach: Mapping[str, Mapping[str, Any]],
    exception_id: str,
    base_id: str,
) -> str:
    """The (base, carve-out) verdict, as a string — never a boolean.

    ``"unknown"`` covers a pair the reachability map never saw, which happens
    when a register row or a binding is missing. It is deliberately not
    ``"unreachable"``: "we have no idea" and "we measured it and it cannot fire"
    lead to different follow-ups, and only the second one may release a base.
    """
    entry = reach.get(exception_id)
    if entry is None:
        return "unknown"
    states = entry.get("base_states") or {}
    state = states.get(base_id)
    return str(state) if state else "unknown"


@dataclass(frozen=True)
class BatchManifest:
    """A parsed, schema-checked batch. Selection order is execution order."""

    path: str
    revision: str
    batch_id: str
    reviewer: str
    rule_ids: tuple[str, ...]
    note: str = ""
    raw: Mapping[str, Any] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.rule_ids)


def load_manifest(path: str | Path) -> BatchManifest:
    """Parse a manifest file. Raises ``BatchManifestError`` on anything unusable.

    Structural problems raise because there is nothing sensible to plan without a
    batch; semantic problems (a HOLD in the list, a broken dependency) are returned
    as findings by :func:`validate_manifest` so the operator sees *all* of them at
    once rather than one per re-run.
    """
    p = Path(path)
    if not p.exists():
        raise BatchManifestError(f"批次清单不存在：{p}")
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BatchManifestError(f"批次清单不是合法 JSON：{p} ({exc})") from exc
    if not isinstance(doc, dict):
        raise BatchManifestError(f"批次清单顶层必须是对象：{p}")

    missing = [k for k in REQUIRED_KEYS if k not in doc]
    if missing:
        raise BatchManifestError(f"批次清单缺少必需字段 {missing}：{p}")

    ids = doc["candidate_rule_ids"]
    if not isinstance(ids, list) or not ids:
        raise BatchManifestError(f"candidate_rule_ids 必须是非空数组：{p}")
    for item in ids:
        if not isinstance(item, str) or not item.strip():
            raise BatchManifestError(f"candidate_rule_ids 只能包含非空字符串，得到 {item!r}：{p}")

    for key in ("revision", "batch_id", "reviewer"):
        value = doc[key]
        if not isinstance(value, str) or not value.strip():
            raise BatchManifestError(f"{key} 必须是非空字符串，得到 {value!r}：{p}")

    unknown = set(doc) - set(REQUIRED_KEYS) - set(OPTIONAL_KEYS)
    if unknown:
        raise BatchManifestError(
            f"批次清单含未知字段 {sorted(unknown)}（疑似拼写错误，拒绝静默忽略）：{p}"
        )

    return BatchManifest(
        path=str(p),
        revision=str(doc["revision"]).strip(),
        batch_id=str(doc["batch_id"]).strip(),
        reviewer=str(doc["reviewer"]).strip(),
        rule_ids=tuple(str(x).strip() for x in ids),
        note=str(doc.get("note") or ""),
        raw=doc,
    )


def duplicate_ids(manifest: BatchManifest) -> list[str]:
    """Ids listed more than once, in first-seen order. A duplicate is a refusal."""
    seen: set[str] = set()
    dupes: list[str] = []
    for rule_id in manifest.rule_ids:
        if rule_id in seen and rule_id not in dupes:
            dupes.append(rule_id)
        seen.add(rule_id)
    return dupes


def approved_exception_map(
    doc: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, list[str]]:
    """``base_rule_id -> [approved carve-out rule ids]``, from the register alone.

    Derived, never hand-maintained: the register's ``exception_plan`` already
    states each carve-out's same-layer bases, and the human decision for that
    carve-out is in ``rows``. Anything the human did not approve (HOLD / REJECTED)
    is deliberately absent — a HOLD is not a carve-out anyone signed, so its base
    is not obliged to wait for it. That is precisely why ``lib-sd-op-police`` and
    ``lib-sd-op-military`` must *not* gate ``lib-pets-op``.

    This answers *was it approved* only. Whether an approved carve-out can ever
    fire is a separate, measured question — see :func:`carve_out_reachability`.
    Conflating the two is what let an inert carve-out block a real base.
    """
    decisions = {str(r["rule_id"]): r.get("final_decision") for r in rows}
    mapping: dict[str, list[str]] = {}
    for entry in doc.get("exception_plan") or []:
        if entry.get("mode") != "rule_exception":
            continue
        rule_id = str(entry["rule_id"])
        if decisions.get(rule_id) not in APPROVAL_DECISIONS:
            continue
        for base in entry.get("bases") or []:
            if not base.get("same_layer"):
                continue
            mapping.setdefault(str(base["rule_id"]), []).append(rule_id)
    return {base: sorted(set(ids)) for base, ids in mapping.items()}


def published_rule_ids(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """Rule ids whose candidate the database already reports as PUBLISHED."""
    return [
        str(r["rule_id"])
        for r in rows
        if (r.get("_db_review_status") or r.get("review_status")) == "PUBLISHED"
    ]


@dataclass
class BatchValidation:
    """Everything provable about a manifest against a register and the database."""

    batch_id: str
    revision: str
    selected: tuple[str, ...]
    access_rule_ids: tuple[str, ...] = ()
    exception_ids: tuple[str, ...] = ()
    dependency_closed: bool = False
    dependency_order: tuple[str, ...] = ()
    hold_selected: tuple[str, ...] = ()
    rejected_selected: tuple[str, ...] = ()
    unapproved_selected: tuple[str, ...] = ()
    cross_layer: tuple[str, ...] = ()
    bases_missing_approved_exception: tuple[str, ...] = ()
    #: ``base->carve_out`` pairs the human approved but that can never fire.
    #: Recorded as ``SEMANTIC_REMODEL_REQUIRED``; they do **not** block the base.
    unreachable_approved_carve_outs: tuple[str, ...] = ()
    #: ``base->carve_out`` pairs we could not measure. Conservative: they still
    #: block, because "we cannot prove the carve-out is inert" is not a licence.
    unevaluable_approved_carve_outs: tuple[str, ...] = ()
    #: Selected carve-outs that cannot fire. A hard refusal — see refusal 5.
    inert_selected_exceptions: tuple[str, ...] = ()
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    @property
    def zero_inert_rules(self) -> bool:
        """True only when every selected carve-out was *measured* reachable."""
        return not self.inert_selected_exceptions

    def summary(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "revision": self.revision,
            "selected": len(self.selected),
            "access_rule": len(self.access_rule_ids),
            "rule_exception": len(self.exception_ids),
            "dependency_closed": self.dependency_closed,
            "hold_selected": len(self.hold_selected),
            "rejected_selected": len(self.rejected_selected),
            "unapproved_selected": len(self.unapproved_selected),
            "cross_layer": len(self.cross_layer),
            "bases_missing_approved_exception": len(self.bases_missing_approved_exception),
            "unreachable_approved_carve_outs": [
                f"{pair}::{SEMANTIC_REMODEL_REQUIRED}"
                for pair in self.unreachable_approved_carve_outs
            ],
            "unevaluable_approved_carve_outs": len(self.unevaluable_approved_carve_outs),
            "inert_selected_exceptions": len(self.inert_selected_exceptions),
            "problems": list(self.problems),
        }

    def render(self) -> str:
        checks = [
            f"BATCH_ID                    = {self.batch_id}",
            f"BATCH_REVISION              = {self.revision}",
            f"BATCH_SELECTED              = {len(self.selected)}",
            f"BATCH_ACCESS_RULE           = {len(self.access_rule_ids)}",
            f"BATCH_RULE_EXCEPTION        = {len(self.exception_ids)}",
            f"BATCH_DEPENDENCY_CLOSED     = {'PASS' if self.dependency_closed else 'FAIL'}",
            f"HOLD_SELECTED               = {len(self.hold_selected)}",
            f"REJECTED_SELECTED           = {len(self.rejected_selected)}",
            f"UNAPPROVED_SELECTED         = {len(self.unapproved_selected)}",
            f"CROSS_LAYER_EXCEPTION       = {len(self.cross_layer)}",
            f"BASE_WITHOUT_APPROVED_EXCEPTION = {len(self.bases_missing_approved_exception)}",
            f"UNREACHABLE_SELECTED        = {len(self.inert_selected_exceptions)}",
            f"ZERO_INERT_RULES               = {'PASS' if self.zero_inert_rules else 'FAIL'}",
        ]
        if self.dependency_order:
            checks.append("BATCH_EXECUTION_ORDER        = " + " -> ".join(self.dependency_order))
        for pair in self.unreachable_approved_carve_outs:
            checks.append(
                f"  UNREACHABLE_APPROVED_CARVE_OUT = {pair} -> {SEMANTIC_REMODEL_REQUIRED}"
            )
        for pair in self.unevaluable_approved_carve_outs:
            checks.append(f"  UNEVALUABLE_APPROVED_CARVE_OUT = {pair}（阻断：无法证明其惰性）")
        if self.problems:
            checks.append("")
            checks.append(f"BATCH_VALIDATION = FAIL（{len(self.problems)} 项）")
            checks.extend(f"  - {p}" for p in self.problems)
        else:
            checks.append("BATCH_VALIDATION = PASS")
        return "\n".join(checks)


def validate_manifest(
    manifest: BatchManifest,
    rows: Sequence[Mapping[str, Any]],
    *,
    bindings: Mapping[str, Any] | None = None,
    register_revision: str = "",
    published_rule_ids: Sequence[str] = (),
    approved_exception_map: Mapping[str, Sequence[str]] | None = None,
    require_base_exception: bool = True,
) -> BatchValidation:
    """Check the manifest against the signed register and the database.

    Pure: every database fact arrives as an argument, so the refusals are
    exhaustively testable without a live cluster.

    ``bindings`` maps ``rule_id -> ExceptionBinding`` (``.bases`` are the same-layer
    bases). ``approved_exception_map`` maps ``base_rule_id -> [exception rule ids
    the human approved]`` and drives the "no prohibition without its *reachable*
    carve-out" check; the reachability half is measured here from ``rows``.
    """
    by_rule = {str(r["rule_id"]): r for r in rows}
    published = {str(x) for x in published_rule_ids}

    result = BatchValidation(
        batch_id=manifest.batch_id,
        revision=manifest.revision,
        selected=manifest.rule_ids,
    )
    problems = result.problems
    #: Dependency refusals are tracked apart from the rest so ``dependency_closed``
    #: is a fact, not a substring search over the problem list.
    dependency_problems: list[str] = []

    # ---- 1. identity: the manifest must describe the register in hand ---------
    if register_revision and manifest.revision != register_revision:
        problems.append(
            f"跨版本选择：清单 revision={manifest.revision!r} 与签署登记表 "
            f"revision={register_revision!r} 不一致"
        )

    signed_reviewers = sorted({str(r["reviewer"]) for r in rows if r.get("reviewer")})
    if len(signed_reviewers) == 1 and manifest.reviewer != signed_reviewers[0]:
        problems.append(
            f"清单 reviewer={manifest.reviewer!r} 与登记表署名={signed_reviewers[0]!r} 不一致"
        )

    # ---- 2. selection ---------------------------------------------------------
    for rule_id in duplicate_ids(manifest):
        problems.append(f"{rule_id}: 在清单中重复出现（重复选择 = 拒绝）")

    seen: set[str] = set()
    selected_rows: list[Mapping[str, Any]] = []
    for rule_id in manifest.rule_ids:
        if rule_id in seen:
            continue
        seen.add(rule_id)
        row = by_rule.get(rule_id)
        if row is None:
            problems.append(f"{rule_id}: 登记表中不存在该 rule_id（未知 id = 拒绝）")
            continue
        decision = row.get("final_decision")
        if decision == HOLD:
            result.hold_selected += (rule_id,)
            problems.append(f"{rule_id}: 人类决定为 HOLD，不得进入发布批次")
            continue
        if decision == REJECTED:
            result.rejected_selected += (rule_id,)
            problems.append(f"{rule_id}: 人类决定为 REJECTED，不得进入发布批次")
            continue
        if decision not in APPROVAL_DECISIONS:
            result.unapproved_selected += (rule_id,)
            problems.append(f"{rule_id}: final_decision={decision!r} 不在批准词表内")
            continue
        selected_rows.append(row)

    # ---- 3. dependency closure ------------------------------------------------
    selected_ids = {str(r["rule_id"]) for r in selected_rows}
    #: Position in the manifest is execution order, so "earlier" is well defined.
    position = {rule_id: i for i, rule_id in enumerate(manifest.rule_ids)}
    bindings = dict(bindings or {})
    order: list[str] = []

    for row in selected_rows:
        rule_id = str(row["rule_id"])
        binding = bindings.get(rule_id)
        if binding is None:
            result.access_rule_ids += (rule_id,)
            order.append(rule_id)
            continue

        result.exception_ids += (rule_id,)
        bases = tuple(str(b) for b in getattr(binding, "bases", ()))
        if not bases:
            dependency_problems.append(
                f"{rule_id}: 作为例外候选没有同层 base，无法确定 carve-out 目标"
                "（跨层 base 只作历史，不构成依赖）"
            )
            continue
        layer = str(row.get("rule_layer") or "")
        for base_id in bases:
            base_row = by_rule.get(base_id)
            base_layer = str((base_row or {}).get("rule_layer") or "")
            if base_row is not None and base_layer != layer:
                result.cross_layer += (f"{rule_id}->{base_id}",)
                dependency_problems.append(
                    f"{rule_id}({layer}) 绑定 {base_id}({base_layer})：跨层例外绑定 = 拒绝"
                )
                continue
            if base_id in selected_ids:
                if position.get(base_id, 1 << 30) > position.get(rule_id, -1):
                    dependency_problems.append(
                        f"{rule_id}: base {base_id} 在清单中排在其后——例外不得先于 base 执行"
                    )
                continue
            if base_id in published:
                continue
            dependency_problems.append(
                f"{rule_id}: base {base_id} 既未 Published，也未在同批中先于例外被选择"
                "（依赖闭包不成立）"
            )
        order.append(f"{rule_id}<-{'+'.join(bases)}")

    result.dependency_order = tuple(order)
    problems.extend(dependency_problems)
    result.dependency_closed = not dependency_problems

    # ---- 4. no prohibition shipped without its REACHABLE approved carve-out ---
    #: Measured register-wide, not just over the selection: whether a carve-out
    #: can fire is a property of the domain model, and a batch must not be able
    #: to hide that fact by leaving the partner out.
    reach = carve_out_reachability(rows, bindings)
    if require_base_exception:
        exception_map = dict(approved_exception_map or {})
        for row in selected_rows:
            rule_id = str(row["rule_id"])
            if bindings.get(rule_id) is not None:
                continue  # the row *is* a carve-out; bases are handled below
            for exception_id in exception_map.get(rule_id, ()):
                if exception_id in selected_ids or exception_id in published:
                    continue
                state = carve_out_state(reach, exception_id, rule_id)
                if state == "reachable":
                    result.bases_missing_approved_exception += (f"{rule_id}->{exception_id}",)
                    problems.append(
                        f"{rule_id}: 该 base 有一条人类已批准且语义可达的例外 {exception_id}，"
                        "但既不在本批也未发布——会出现"
                        "『禁令已发布但批准的例外缺失』的错误用户状态。"
                        "如确需部分发布，必须显式 override + 人工授权（本批禁止）。"
                    )
                elif state == "unreachable":
                    #: The carve-out is inert: its base does not govern the subject
                    #: it was written for, so publishing the base without it changes
                    #: nothing for any user. Blocking here would let a modelling
                    #: defect hold a real rule hostage — so it is recorded, not
                    #: enforced.
                    result.unreachable_approved_carve_outs += (f"{rule_id}->{exception_id}",)
                else:
                    #: Unknown / unevaluable. Conservative: treat as an obligation.
                    result.unevaluable_approved_carve_outs += (f"{rule_id}->{exception_id}",)
                    problems.append(
                        f"{rule_id}: 已批准例外 {exception_id} 的可达性无法判定"
                        f"（state={state}）——无法证明其惰性，故不放行该 base。"
                        "补齐 subject_scope_normalized / normalization_type 后重跑。"
                    )

    # ---- 5. zero inert rules in the batch -----------------------------------
    #: A carve-out that cannot fire is worse than no carve-out: it is published,
    #: linked, audited and counted, and it silently promises access it never
    #: delivers. Refusal 4 lets an inert *unselected* carve-out release its base;
    #: this refusal stops an inert carve-out from being *shipped*.
    for rule_id in result.exception_ids:
        entry = reach.get(rule_id)
        if entry is None:
            continue
        state = str(entry["state"])
        if state == "reachable":
            continue
        result.inert_selected_exceptions += (f"{rule_id}:{state}",)
        problems.append(
            f"{rule_id}: 该例外语义不可达（state={state}，"
            f"bases={list(entry['bases'])}）——发布后永不生效，属于惰性规则。"
            f"记录为 {SEMANTIC_REMODEL_REQUIRED}，需语义改造后才能进批；"
            "不得为了让批次通过而放宽 base 作用域或跳过适用性判断。"
        )

    return result
