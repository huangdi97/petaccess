"""Publish the signed review batch — plan first, then (only with --execute) write.

Two entry points, one planner
-----------------------------
``--dry-run`` and ``--execute`` run the **same** pipeline:

    signed register
      → authorisation          (Human ``final_decision``, nothing else)
      → pre-publish validation (the canonical `publish_gate`, called for real)
      → publication classification
      → dependency planning    (base AccessRule before its RuleException)
      → plan
      → dry-run: NO WRITE      |      execute: transactional write

The dry-run is not a printout of what the register says; it is the real plan the
execute path would consume, evaluated against the real database through the real
gate. That is the only way "the dry-run passed" can mean anything.

What this fixes (POST_SIGNATURE_PUBLISHER_CLOSURE_R1)
-----------------------------------------------------

**P0-01 — RuleException had no path.** An exception candidate states a carve-out
of another rule (《上海市养犬管理条例》第二十三条 prohibits dogs in 商场, its
但书 exempts guide dogs). Publishing it as an AccessRule is wrong twice over: the
resolver then sees two same-layer rules and picks the strictest, and the
carve-out silently stops working. Exceptions are now a first-class publication
type with a dependency on their base rule, and the write itself goes through
``candidate_service.publish_exception``, which refuses a cross-layer binding at
the boundary rather than trusting the plan.

**P0-02 — the plan used the AI's recommendation.** The old dry-run planned from
``proposed_decision``, so a signed HOLD could still be planned for publication if
the machine had recommended approval. Authorisation now reads ``final_decision``
only; ``proposed_decision`` is carried in the plan for comparison and never
consulted for permission.

**P0-03 — the dry-run never touched the publish gate.** It reported a clean
sign-off and planned 23 creations while having executed none of the six
Pre-Publish Validation checks. The dry-run now calls
``publish_gate.evaluate_for_publish`` against a live session, so "APPROVED" is
reported separately from "publishable" and every blocked row carries its reasons.

Hard gates enforced here (all must hold, otherwise the run aborts):

  1. HUMAN SIGN-OFF. Every row must carry ``final_decision`` AND ``reviewer``
     AND ``reviewed_at``. A machine-proposed decision is never executed on its
     own — AI does not make the final rule call (ADR-005 / Master Goal §0.9).
  2. NO WEAK EVIDENCE. A row whose ``evidence_strength`` is search_snippet or
     social_lead may not be APPROVED (ADR-021); the gate rejects it too, but
     failing here keeps the run atomic.
  3. NO BULK BLIND APPROVE. ``--max-approve`` (default 20) caps the batch, so a
     signed file that approves 23 in one shot must be split deliberately.
  4. BASE BEFORE EXCEPTION. A carve-out is never planned ahead of the rule it
     carves out of, and is blocked outright if that base is not publishable.
  5. VERIFY AFTER PUBLISH. Each published candidate is re-read: the rule must
     exist, carry the candidate's rule_layer, be linked back to the candidate,
     and be visible through /effective-rules.
  6. EXPLICIT SELECTION. ``--execute`` requires ``--batch-file``: the batch is a
     versioned manifest, never a slice of whatever the register sorts first.
     ``--max-approve`` is a second-layer safety cap over that batch, not a
     selector. See ``scripts/publish_batch.py``.

Usage:
    python scripts/publish_reviewed_r1.py --dry-run
    python scripts/publish_reviewed_r1.py --dry-run --batch-file <manifest> --max-approve 12
    python scripts/publish_reviewed_r1.py --execute --batch-file <manifest> --reviewer "姓名"
"""

# NOTE: deliberately no ``from __future__ import annotations``. PEP 563 turns
# every annotation into a string, and ``@dataclass`` then resolves those through
# ``sys.modules[cls.__module__]`` — which does not exist when a module is loaded
# by path, the way this repo's tests load this script (``spec_from_file_location``
# without registering it in ``sys.modules``). Runtime annotations keep the plan
# dataclasses importable from a test harness as well as from the CLI.

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

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
from publish_batch import (  # noqa: E402
    BatchManifest,
    BatchManifestError,
    BatchValidation,
    load_manifest,
    validate_manifest,
)
from publish_batch import (
    approved_exception_map as batch_approved_exception_map,
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

# ------------------------------------------------------------- publication types
#: A base rule is created.
CREATE_ACCESS_RULE = "CREATE_ACCESS_RULE"
#: A base rule is created and it replaces an existing current same-issuer rule.
SUPERSEDE_ACCESS_RULE = "SUPERSEDE_ACCESS_RULE"
#: A carve-out is attached to a newly or previously published base rule.
CREATE_RULE_EXCEPTION = "CREATE_RULE_EXCEPTION"
#: Nothing to do — the candidate is already published.
NOOP_ALREADY_EXISTS = "NOOP_ALREADY_EXISTS"
#: Refused, with reasons.
BLOCKED = "BLOCKED"
#: Human said HOLD. Never publishable, in this round or any other.
HOLD_NOT_PUBLISHABLE = "HOLD_NOT_PUBLISHABLE"
#: Human said REJECTED. Never publishable, in this round or any other.
REJECTED_NOT_PUBLISHABLE = "REJECTED_NOT_PUBLISHABLE"

#: Types that would write something.
WRITING_TYPES = frozenset({CREATE_ACCESS_RULE, SUPERSEDE_ACCESS_RULE, CREATE_RULE_EXCEPTION})
#: Types that are never publishable.
NEVER_PUBLISHABLE = frozenset({HOLD_NOT_PUBLISHABLE, REJECTED_NOT_PUBLISHABLE})

#: Gate outcome values.
GATE_PASS = "PASS"
GATE_BLOCKED = "BLOCKED"
GATE_NOT_RUN = "NOT_RUN"


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


def load_registry() -> dict:
    return json.loads(DECISIONS.read_text(encoding="utf-8"))


def load_rows() -> list[dict]:
    return load_registry()["rows"]


def signed_reviewer(rows: Sequence[Mapping[str, Any]]) -> str:
    """The single named human who signed this batch, or "" if not signed."""
    reviewers = sorted({str(r["reviewer"]) for r in rows if r.get("reviewer")})
    return reviewers[0] if len(reviewers) == 1 else ""


# ============================================================ batch selection


def select_rows(rows: Sequence[Mapping[str, Any]], manifest: BatchManifest) -> list[dict]:
    """The batch's rows, **in manifest order** — which is also execution order.

    Only rows the manifest names come back. Everything else in the register
    (the other approved candidates, and every HOLD and REJECTED row) is not
    planned at all, so there is nothing for it to fall through into. The manifest
    narrows; it never widens — permission is still read from the register.
    """
    by_rule = {str(r["rule_id"]): r for r in rows}
    selected: list[dict] = []
    seen: set[str] = set()
    for rule_id in manifest.rule_ids:
        if rule_id in seen:
            continue
        seen.add(rule_id)
        row = by_rule.get(rule_id)
        if row is not None:
            selected.append(dict(row))
    return selected


def _published_rule_ids(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """Rule ids whose candidate the database reports as PUBLISHED."""
    return [
        str(r["rule_id"])
        for r in rows
        if (r.get("_db_review_status") or r.get("review_status")) == "PUBLISHED"
    ]


# ============================================================ exception bindings


@dataclass(frozen=True)
class ExceptionBinding:
    """Canonical carve-out metadata for one candidate.

    Read from the register's ``exception_plan`` — which the packet generator
    derives from the database evidence chain and which is guarded at generation
    time by ``validate_exception_binding``. **Not** a hardcoded id list: a new
    carve-out in a future batch is recognised because it carries this metadata,
    not because someone remembered to add its name here.

    ``bases`` are same-layer only. Anything the layer-blind algorithm would have
    attached across layers is kept in ``dropped_cross_layer`` as history and is
    deliberately NOT a dependency — an OPERATOR_POLICY carve-out attached to a
    LEGAL prohibition would let an operator's "we allow it" out-vote a statute
    (RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE).
    """

    rule_id: str
    bases: tuple[str, ...]
    layer: str | None
    dropped_cross_layer: tuple[str, ...] = ()


def canonical_exception_bindings(doc: Mapping[str, Any]) -> dict[str, ExceptionBinding]:
    """Every carve-out in the register, keyed by rule_id, same-layer bindings only."""
    bindings: dict[str, ExceptionBinding] = {}
    for entry in doc.get("exception_plan") or []:
        if entry.get("mode") != "rule_exception":
            continue
        same_layer = tuple(
            str(b.get("rule_id")) for b in entry.get("bases") or [] if b.get("same_layer")
        )
        crossed = tuple(
            str(b.get("rule_id")) for b in entry.get("bases") or [] if not b.get("same_layer")
        )
        bindings[str(entry["rule_id"])] = ExceptionBinding(
            rule_id=str(entry["rule_id"]),
            bases=same_layer,
            layer=entry.get("layer"),
            dropped_cross_layer=crossed
            + tuple(str(x) for x in entry.get("cross_layer_dropped") or []),
        )
    return bindings


def binding_closure_problems(doc: Mapping[str, Any]) -> list[str]:
    """The register must be internally consistent about carve-out bindings.

    Two ways this file could lie: a binding marked same-layer that is not, or a
    base whose layer disagrees with the carve-out's. Either would let a carve-out
    be planned against the wrong layer, so both are refusals.
    """
    problems: list[str] = []
    layers = {str(r["rule_id"]): r.get("rule_layer") for r in doc.get("rows") or []}
    for entry in doc.get("exception_plan") or []:
        rule_id = str(entry["rule_id"])
        for base in entry.get("bases") or []:
            base_id = str(base.get("rule_id"))
            if not base.get("same_layer"):
                problems.append(f"{rule_id}: 绑定表含跨层 base {base_id}")
            elif base.get("layer") != entry.get("layer"):
                problems.append(
                    f"{rule_id}: base {base_id} 层={base.get('layer')!r}"
                    f" 与例外层={entry.get('layer')!r} 不一致"
                )
            elif layers.get(base_id) != entry.get("layer"):
                problems.append(f"{rule_id}: base {base_id} 在登记表中的层与绑定表不一致")
    return problems


# ============================================================ the gate boundary


@dataclass(frozen=True)
class GateOutcome:
    """What the canonical pre-publish gate said about one candidate."""

    status: str
    reasons: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.status == GATE_PASS


class Gate(Protocol):
    """Port for pre-publish validation, so planning stays testable without a DB."""

    def evaluate(self, *, candidate_id: str, rule_id: str) -> GateOutcome: ...


class NullGate:
    """Used only where no database is available; reports NOT_RUN, never PASS."""

    def evaluate(self, *, candidate_id: str, rule_id: str) -> GateOutcome:
        return GateOutcome(status=GATE_NOT_RUN, reasons=("未连接数据库，未执行发布闸门",))


class MappingGate:
    """Deterministic gate for tests: rule_id -> GateOutcome (default PASS)."""

    def __init__(self, outcomes: Mapping[str, GateOutcome] | None = None, default: str = GATE_PASS):
        self._outcomes = dict(outcomes or {})
        self._default = default

    def evaluate(self, *, candidate_id: str, rule_id: str) -> GateOutcome:
        return self._outcomes.get(rule_id, GateOutcome(status=self._default))


class DatabaseGate:
    """The **real** gate: ``publish_gate.evaluate_for_publish`` on a live session.

    Deliberately not a re-implementation. If this class ever grows checks of its
    own, the dry-run stops predicting the publish — which is the entire point of
    running it.
    """

    def __init__(self, session: Any, *, now: datetime | None = None) -> None:
        self._session = session
        self._now = now

    def evaluate(self, *, candidate_id: str, rule_id: str) -> GateOutcome:
        from app.models import RuleCandidate
        from app.services.publish_gate import evaluate_for_publish

        candidate = self._session.get(RuleCandidate, candidate_id)
        if candidate is None:
            return GateOutcome(status=GATE_BLOCKED, reasons=("库中不存在该候选",))
        violations = evaluate_for_publish(self._session, candidate, now=self._now)
        if not violations:
            return GateOutcome(status=GATE_PASS)
        return GateOutcome(status=GATE_BLOCKED, reasons=tuple(v.message for v in violations))


# ============================================================ authorised planning


@dataclass
class PlanStep:
    """One row of the publication plan."""

    order: int
    candidate_id: str
    rule_id: str
    place_name: str
    zone_name: str | None
    layer: str | None
    mandatory_level: str | None
    human_decision: str
    proposed_decision: str | None
    human_overrides_ai: bool
    publication_type: str
    depends_on: tuple[str, ...] = ()
    gate_status: str = GATE_NOT_RUN
    gate_reasons: tuple[str, ...] = ()
    supersedes: tuple[str, ...] = ()
    blocked_reasons: tuple[str, ...] = ()

    @property
    def publishable(self) -> bool:
        return self.publication_type in WRITING_TYPES


@dataclass
class Plan:
    revision: str
    reviewer: str
    steps: list[PlanStep] = field(default_factory=list)
    gate_ran: bool = False

    def of(self, *types: str) -> list[PlanStep]:
        return [s for s in self.steps if s.publication_type in types]

    @property
    def writable(self) -> list[PlanStep]:
        return [s for s in self.steps if s.publishable]

    def summary(self) -> dict[str, Any]:
        counts = Counter(s.publication_type for s in self.steps)
        evaluated = [s for s in self.steps if s.gate_status != GATE_NOT_RUN]
        return {
            "revision": self.revision,
            "reviewer": self.reviewer,
            "signed": bool(self.reviewer) and all(s.human_decision for s in self.steps),
            "gate_ran": self.gate_ran,
            "total": len(self.steps),
            "human_decisions": {
                key: sum(1 for s in self.steps if s.human_decision == key)
                for key in (APPROVED, APPROVED_WITH_NOTE, HOLD, REJECTED)
            },
            "prepublish_evaluated": len(evaluated),
            "prepublish_pass": sum(1 for s in evaluated if s.gate_status == GATE_PASS),
            "prepublish_blocked": sum(1 for s in evaluated if s.gate_status == GATE_BLOCKED),
            "gate_status_counts": dict(Counter(s.gate_status for s in evaluated)),
            "access_rule_create_count": counts.get(CREATE_ACCESS_RULE, 0),
            "access_rule_supersede_count": counts.get(SUPERSEDE_ACCESS_RULE, 0),
            "rule_exception_create_count": counts.get(CREATE_RULE_EXCEPTION, 0),
            "noop_count": counts.get(NOOP_ALREADY_EXISTS, 0),
            "blocked_count": counts.get(BLOCKED, 0),
            "hold_publishable": sum(
                1
                for s in self.steps
                if s.publication_type == HOLD_NOT_PUBLISHABLE and s.publishable
            ),
            "rejected_publishable": sum(
                1
                for s in self.steps
                if s.publication_type == REJECTED_NOT_PUBLISHABLE and s.publishable
            ),
            "human_overrides_ai": sum(1 for s in self.steps if s.human_overrides_ai),
            "publication_types": dict(counts),
        }


def machine_agrees(row: Mapping[str, Any]) -> bool:
    """Does the machine's recommendation match the human's decision?

    Used only to *display* the disagreement. It never authorises anything.
    """
    decision = row.get("final_decision")
    proposed = row.get("proposed_decision")
    if not proposed:
        return True
    if decision in APPROVAL_DECISIONS:
        return proposed in ("RECOMMEND_APPROVE", "RECOMMEND_APPROVE_WITH_NOTE")
    if decision == HOLD:
        return proposed == "RECOMMEND_HOLD"
    if decision == REJECTED:
        return proposed == "RECOMMEND_REJECT"
    return False


def authorise(row: Mapping[str, Any]) -> str:
    """Human authorisation, from ``final_decision`` and from nothing else.

    ``proposed_decision`` is the machine's opinion. It appears in the plan so a
    reviewer can see where they disagreed with it, and it is never allowed to
    grant permission: an APPROVED the machine wanted to HOLD gets published, and
    a HOLD the machine wanted to approve does not.
    """
    decision = row.get("final_decision")
    if decision in APPROVAL_DECISIONS:
        return "PURSUE"
    if decision == HOLD:
        return "HOLD"
    if decision == REJECTED:
        return "REJECT"
    return "UNSIGNED"


def _supersede_targets(row: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(x) for x in row.get("_supersedes_existing") or ())


def build_plan(
    rows: Sequence[Mapping[str, Any]],
    *,
    bindings: Mapping[str, ExceptionBinding] | None = None,
    gate: Gate | None = None,
    revision: str = "",
    reviewer: str = "",
    already_published: Iterable[str] = (),
) -> Plan:
    """Turn signed rows into an ordered publication plan.

    Pure with respect to the world: every database fact it needs arrives as an
    argument (``gate``, ``_supersedes_existing`` on the row, ``already_published``),
    so the planner is exhaustively unit-testable and the execute path consumes the
    very same object the dry-run printed.

    Ordering is deterministic and dependency-correct: publishable steps first,
    bases before the carve-outs that depend on them, ties broken by ``rule_id``.
    Two runs over one register therefore produce identical plans.
    """
    bindings = dict(bindings or {})
    published = {str(x) for x in already_published}
    steps: list[PlanStep] = []
    by_rule: dict[str, PlanStep] = {}
    layer_of = {str(r["rule_id"]): r.get("rule_layer") for r in rows}

    for row in rows:
        rule_id = str(row["rule_id"])
        auth = authorise(row)
        binding = bindings.get(rule_id)
        outcome = (
            gate.evaluate(candidate_id=str(row["candidate_id"]), rule_id=rule_id)
            if gate is not None and auth == "PURSUE"
            else GateOutcome(status=GATE_NOT_RUN)
        )
        proposed = row.get("proposed_decision")
        step = PlanStep(
            order=0,
            candidate_id=str(row["candidate_id"]),
            rule_id=rule_id,
            place_name=str(row.get("place_name") or ""),
            zone_name=row.get("zone_name"),
            layer=row.get("rule_layer"),
            mandatory_level=row.get("mandatory_level"),
            human_decision=str(row.get("final_decision") or ""),
            proposed_decision=proposed,
            human_overrides_ai=bool(proposed) and not machine_agrees(row),
            publication_type=BLOCKED,
            gate_status=outcome.status,
            gate_reasons=outcome.reasons,
            supersedes=_supersede_targets(row),
        )
        if auth == "HOLD":
            step.publication_type = HOLD_NOT_PUBLISHABLE
        elif auth == "REJECT":
            step.publication_type = REJECTED_NOT_PUBLISHABLE
        elif auth == "UNSIGNED":
            step.publication_type = BLOCKED
            step.blocked_reasons = ("未签署（final_decision 不在词表内），不得进入发布计划",)
        elif str(row["candidate_id"]) in published:
            step.publication_type = NOOP_ALREADY_EXISTS
            step.blocked_reasons = ("候选已处于 PUBLISHED，无需重复发布",)
        elif outcome.status == GATE_BLOCKED:
            step.publication_type = BLOCKED
            step.blocked_reasons = outcome.reasons or ("发布前校验未通过",)
        elif binding is not None:
            step.publication_type = CREATE_RULE_EXCEPTION
            step.depends_on = binding.bases
        elif step.supersedes:
            step.publication_type = SUPERSEDE_ACCESS_RULE
        else:
            step.publication_type = CREATE_ACCESS_RULE
        steps.append(step)
        by_rule[rule_id] = step

    # ---- dependency closure: a carve-out may not outlive a missing base -------
    for step in steps:
        if step.publication_type != CREATE_RULE_EXCEPTION:
            continue
        blocked: list[str] = []
        if not step.depends_on:
            blocked.append("例外候选没有同层 base，无法作为 carve-out 发布")
        for base_id in step.depends_on:
            base = by_rule.get(base_id)
            if base is None:
                blocked.append(f"base {base_id} 不在本批登记表中，且库中无对应现行规则")
                continue
            base_layer = layer_of.get(base_id)
            if base_layer != step.layer:
                blocked.append(
                    f"base {base_id} 层={base_layer!r} 与例外层={step.layer!r} 不一致，"
                    "跨层绑定被拒绝"
                )
            elif base.publication_type not in WRITING_TYPES:
                blocked.append(
                    f"base {base_id} 不可发布（{base.publication_type}），例外不得被间接带入"
                )
        if blocked:
            step.publication_type = BLOCKED
            step.blocked_reasons = tuple(blocked)

    # ---- ordering: publishable first, base before exception, ties by rule_id --
    def sort_key(step: PlanStep) -> tuple[int, int, str]:
        writable = 0 if step.publishable else 1
        level = 1 if step.publication_type == CREATE_RULE_EXCEPTION else 0
        return (writable, level, step.rule_id)

    ordered = sorted(steps, key=sort_key)
    for index, step in enumerate(ordered, start=1):
        step.order = index

    return Plan(
        revision=revision,
        reviewer=reviewer,
        steps=ordered,
        gate_ran=gate is not None and not isinstance(gate, NullGate),
    )


# ============================================================ plan integrity


def target_identity(step: PlanStep, rows_by_rule: Mapping[str, Mapping[str, Any]]) -> tuple:
    """What a step would write, as a collision key.

    Two steps with the same identity would fight over one rule (or one carve-out)
    — a duplicate publication, not two publications.
    """
    row = rows_by_rule.get(step.rule_id, {})
    owner = row.get("zone_id") or row.get("zone_key") or row.get("place_key")
    return (
        step.publication_type,
        owner,
        row.get("source_key") or row.get("source_id"),
        row.get("subject_scope_normalized"),
        row.get("action"),
        step.layer,
        row.get("effect"),
    )


def self_supersede_violations(
    steps: Sequence[PlanStep], *, created_ids: Iterable[str] = ()
) -> list[str]:
    """A publication must never supersede itself.

    Two concrete ways that could happen, both refused here:

    * a step's supersede set contains a rule this same plan is creating —
      two steps racing over one identity;
    * literal ``rule_id == supersedes_rule_id`` — a rule recorded as superseding
      itself, which makes its own history unreadable.
    """
    created = {str(x) for x in created_ids}
    problems: list[str] = []
    for step in steps:
        if step.rule_id in step.supersedes:
            problems.append(f"{step.rule_id}: 规则把自己列为 supersedes 目标")
        overlap = created.intersection(step.supersedes)
        if overlap:
            problems.append(
                f"{step.rule_id}: supersede 目标包含本批正在创建的规则 {sorted(overlap)}"
            )
    return problems


def duplicate_plan_violations(
    steps: Sequence[PlanStep], rows_by_rule: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    """No candidate and no write target may appear twice in the plan."""
    problems: list[str] = []
    for candidate_id, count in Counter(s.candidate_id for s in steps if s.publishable).items():
        if count > 1:
            problems.append(f"候选 {candidate_id} 在计划中出现 {count} 次")
    seen: dict[tuple, list[str]] = {}
    for step in steps:
        if not step.publishable:
            continue
        seen.setdefault(target_identity(step, rows_by_rule), []).append(step.rule_id)
    for _, rule_ids in seen.items():
        if len(rule_ids) > 1:
            problems.append(f"同一写入目标被计划多次：{sorted(rule_ids)}")
    return problems


def cross_layer_violations(
    steps: Sequence[PlanStep], rows_by_rule: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    """A carve-out must bind inside its own layer, and only there."""
    problems: list[str] = []
    for step in steps:
        if step.publication_type not in (CREATE_RULE_EXCEPTION, BLOCKED):
            continue
        for base_id in step.depends_on:
            base_layer = rows_by_rule.get(base_id, {}).get("rule_layer")
            if base_layer != step.layer:
                problems.append(
                    f"{step.rule_id}({step.layer}) 绑定 {base_id}({base_layer})：跨层例外绑定"
                )
    return problems


def supersession_cycles(edges: Mapping[str, str]) -> list[list[str]]:
    """``supersedes_rule_id`` chains must be a forest, never a loop.

    A cycle makes "which rule is current" unanswerable.
    """
    cycles: list[list[str]] = []
    for start in edges:
        seen: list[str] = []
        node: str | None = start
        while node is not None and node in edges:
            if node in seen:
                cycles.append([*seen[seen.index(node) :], node])
                break
            seen.append(node)
            node = edges[node]
    return cycles


def plan_integrity(
    plan: Plan,
    *,
    rows_by_rule: Mapping[str, Mapping[str, Any]],
    supersession_edges: Mapping[str, str] | None = None,
    created_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """The refusal set that a managed dry-run must report as all zero."""
    self_supersede = self_supersede_violations(plan.steps, created_ids=created_ids)
    duplicates = duplicate_plan_violations(plan.steps, rows_by_rule)
    cross_layer = cross_layer_violations(plan.steps, rows_by_rule)
    cycles = supersession_cycles(supersession_edges or {})
    return {
        "SELF_SUPERSEDE": len(self_supersede),
        "DUPLICATE_PUBLICATION_PLAN": len(duplicates),
        "CROSS_LAYER_EXCEPTION": len(cross_layer),
        "SUPERSESSION_CYCLE": len(cycles),
        "details": {
            "self_supersede": self_supersede,
            "duplicate_plan": duplicates,
            "cross_layer_exception": cross_layer,
            "supersession_cycle": [" -> ".join(c) for c in cycles],
        },
    }


# ============================================================ preflight (register side)


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


# ============================================================ execution


def bucketize(plan: Plan) -> dict[str, list[dict]]:
    """Legacy buckets, derived from the plan so the two views cannot disagree."""
    result: dict[str, list[dict]] = {
        "approved": [],
        "rejected": [],
        "held": [],
        "published": [],
        "failed": [],
    }
    for step in plan.steps:
        if step.publication_type == HOLD_NOT_PUBLISHABLE:
            result["held"].append({"candidate_id": step.candidate_id, "rule_id": step.rule_id})
        elif step.publication_type == REJECTED_NOT_PUBLISHABLE:
            result["rejected"].append({"candidate_id": step.candidate_id, "rule_id": step.rule_id})
        elif step.publication_type in (CREATE_ACCESS_RULE, SUPERSEDE_ACCESS_RULE):
            result["approved"].append(
                {"candidate_id": step.candidate_id, "rule_id": step.rule_id, "layer": step.layer}
            )
        elif step.publication_type == CREATE_RULE_EXCEPTION:
            result["approved"].append(
                {
                    "candidate_id": step.candidate_id,
                    "rule_id": step.rule_id,
                    "layer": step.layer,
                    "publication_type": CREATE_RULE_EXCEPTION,
                }
            )
    return result


def run(
    rows: list[dict],
    api: Api | None,
    execute: bool,
    *,
    bindings: Mapping[str, ExceptionBinding] | None = None,
    gate: Gate | None = None,
    already_published: Iterable[str] = (),
) -> dict:
    """Legacy entry point — a thin wrapper over the one planner.

    Kept because callers (and the governance tests) use it to prove that HOLD rows
    never fall through into the publish branch. It no longer holds a private copy
    of the decision logic: the dry-run branch reads ``final_decision`` — via
    ``build_plan`` — exactly as ``--execute`` does. Planning from the machine's
    ``proposed_decision`` is what let a signed HOLD stay publishable.
    """
    plan = build_plan(rows, bindings=bindings, gate=gate, already_published=already_published)
    if not execute:
        return bucketize(plan)
    return execute_plan(plan, api)


def execute_plan(
    plan: Plan,
    api: Api | None,
    *,
    prepublished_bases: Mapping[str, str] | None = None,
) -> dict[str, list[dict]]:
    """Write the plan, in order, base before carve-out.

    A blocked or unsigned row is skipped rather than published; ``main()``
    refuses to reach this function with a gate that never ran.

    ``prepublished_bases`` maps ``rule_id -> access_rule.id`` for bases that were
    published by an *earlier* batch. The batch validator already proved that such
    a base satisfies the dependency closure; without this map the executor would
    have no id to attach the carve-out to and would fail a closure the manifest
    had already proven closed.
    """
    prepublished = {str(k): str(v) for k, v in (prepublished_bases or {}).items()}
    result: dict[str, list[dict]] = {
        "approved": [],
        "rejected": [],
        "held": [],
        "published": [],
        "failed": [],
    }
    for step in plan.steps:
        if step.publication_type in NEVER_PUBLISHABLE or step.publication_type == BLOCKED:
            continue
        if step.publication_type == NOOP_ALREADY_EXISTS:
            continue
        assert api is not None, "execute requires an API client"
        cid = step.candidate_id
        try:
            api.post(
                f"/api/v1/admin/candidates/{cid}/transition",
                {"target": APPROVED, "note": f"human review by {plan.reviewer}"},
            )
        except RuntimeError as exc:
            result["failed"].append(
                {
                    "candidate_id": cid,
                    "rule_id": step.rule_id,
                    "stage": "transition",
                    "error": str(exc),
                }
            )
            continue

        if step.publication_type == CREATE_RULE_EXCEPTION:
            base_rule_id = published_base_for(step, result, prepublished)
            if base_rule_id is None:
                result["failed"].append(
                    {
                        "candidate_id": cid,
                        "rule_id": step.rule_id,
                        "stage": "resolve_base",
                        "error": f"base {list(step.depends_on)} 尚未发布，无法附加例外",
                    }
                )
                continue
            try:
                out = api.post(
                    f"/api/v1/admin/candidates/{cid}/publish",
                    {"exception_of_rule_id": base_rule_id},
                )
            except RuntimeError as exc:
                result["failed"].append(
                    {
                        "candidate_id": cid,
                        "rule_id": step.rule_id,
                        "stage": "publish_exception",
                        "error": str(exc),
                    }
                )
                continue
            result["published"].append(
                {
                    "candidate_id": cid,
                    "rule_id": step.rule_id,
                    "publication_type": CREATE_RULE_EXCEPTION,
                    "base_rule_id": out.get("published_rule_id"),
                    "rule_exception_id": out.get("rule_exception_id"),
                }
            )
            continue

        try:
            out = api.post(f"/api/v1/admin/candidates/{cid}/publish")
        except RuntimeError as exc:
            result["failed"].append(
                {
                    "candidate_id": cid,
                    "rule_id": step.rule_id,
                    "stage": "publish",
                    "error": str(exc),
                }
            )
            continue
        result["approved"].append({"candidate_id": cid, "rule_id": step.rule_id})
        result["published"].append(
            {
                "candidate_id": cid,
                "rule_id": step.rule_id,
                "publication_type": step.publication_type,
                "published_rule_id": out.get("published_rule_id"),
                "layer_preserved": out.get("rule_layer") == step.layer,
                "mandatory_preserved": out.get("mandatory_level") == step.mandatory_level,
            }
        )
    return result


def published_base_for(
    step: PlanStep,
    result: Mapping[str, list[dict]],
    prepublished: Mapping[str, str] | None = None,
) -> str | None:
    """Which AccessRule should this carve-out attach to?

    The base published earlier in this same batch, or — when the base was
    published by an earlier batch — its already-known ``access_rule.id``. There is
    no other source: the base is stated by the register's binding, never guessed
    from place/source.
    """
    for base_id in step.depends_on:
        for entry in result.get("published", []):
            if entry.get("rule_id") == base_id and entry.get("published_rule_id"):
                return str(entry["published_rule_id"])
        known = (prepublished or {}).get(base_id)
        if known:
            return str(known)
    return None


# ============================================================ reporting


def render_plan(plan: Plan, integrity: Mapping[str, Any]) -> str:
    summary = plan.summary()
    lines = [
        "=== DRY RUN PLAN（不写库）===",
        f"REVISION                    = {summary['revision']}",
        f"REVIEWER                    = {summary['reviewer']}",
        f"SIGNED                      = {summary['signed']}",
        f"TOTAL                       = {summary['total']}",
        f"APPROVED                    = {summary['human_decisions'][APPROVED]}",
        f"APPROVED_WITH_NOTE          = {summary['human_decisions'][APPROVED_WITH_NOTE]}",
        f"HOLD                        = {summary['human_decisions'][HOLD]}",
        f"REJECTED                    = {summary['human_decisions'][REJECTED]}",
        "",
        f"PREPUBLISH_GATE_RAN         = {summary['gate_ran']}",
        f"PREPUBLISH_APPROVED_EVALUATED = {summary['prepublish_evaluated']}",
        f"PREPUBLISH_PASS             = {summary['prepublish_pass']}",
        f"PREPUBLISH_BLOCKED          = {summary['prepublish_blocked']}",
        "",
        f"ACCESS_RULE_CREATE_COUNT    = {summary['access_rule_create_count']}",
        f"ACCESS_RULE_SUPERSEDE_COUNT = {summary['access_rule_supersede_count']}",
        f"RULE_EXCEPTION_CREATE_COUNT = {summary['rule_exception_create_count']}",
        f"NOOP_COUNT                  = {summary['noop_count']}",
        f"BLOCKED_COUNT               = {summary['blocked_count']}",
        "",
        f"HOLD_PUBLISHABLE            = {summary['hold_publishable']}",
        f"REJECTED_PUBLISHABLE        = {summary['rejected_publishable']}",
        f"CROSS_LAYER_EXCEPTION       = {integrity['CROSS_LAYER_EXCEPTION']}",
        f"SELF_SUPERSEDE              = {integrity['SELF_SUPERSEDE']}",
        f"DUPLICATE_PLAN              = {integrity['DUPLICATE_PUBLICATION_PLAN']}",
        f"SUPERSESSION_CYCLE          = {integrity['SUPERSESSION_CYCLE']}",
        f"HUMAN_OVERRIDES_AI          = {summary['human_overrides_ai']}",
        "",
        f"{'#':>3}  {'rule':<26} {'place':<20} {'layer':<16} {'human':<9} "
        f"{'publication_type':<22} {'gate':<8} depends_on / reasons",
    ]
    for step in plan.steps:
        reasons = "; ".join(step.gate_reasons or step.blocked_reasons)
        depends = "dep=" + ",".join(step.depends_on) if step.depends_on else ""
        extra = " | ".join(x for x in (depends, reasons) if x)
        place = step.place_name[:18]
        lines.append(
            f"{step.order:>3}  {step.rule_id:<26} {place:<20} {str(step.layer):<16} "
            f"{step.human_decision:<9} {step.publication_type:<22} {step.gate_status:<8} "
            f"{extra[:64]}"
        )
    return "\n".join(lines)


def plan_as_json(plan: Plan, integrity: Mapping[str, Any], extra: Mapping[str, Any]) -> dict:
    return {
        "summary": {**plan.summary(), **dict(extra)},
        "integrity": integrity,
        "plan": [
            {
                "order": s.order,
                "candidate_id": s.candidate_id,
                "rule_id": s.rule_id,
                "place": s.place_name,
                "zone": s.zone_name,
                "layer": s.layer,
                "mandatory_level": s.mandatory_level,
                "human_decision": s.human_decision,
                "proposed_decision": s.proposed_decision,
                "human_overrides_ai": s.human_overrides_ai,
                "publication_type": s.publication_type,
                "depends_on": list(s.depends_on),
                "gate_result": s.gate_status,
                "gate_reasons": list(s.gate_reasons),
                "supersedes": list(s.supersedes),
                "blocked_reasons": list(s.blocked_reasons),
                "publishable": s.publishable,
            }
            for s in plan.steps
        ],
    }


# ============================================================ database plumbing

#: Tables whose row counts prove a dry-run wrote nothing.
_COUNTED_TABLES = ("access_rule", "rule_exception", "rule_candidate", "audit_log")


def build_session(database_url: str | None):
    """A session for the dry-run's gate evaluation.

    The dry-run never commits and never mutates; the caller compares table counts
    around it and reports ``DRY_RUN_ZERO_DB_MUTATION``.
    """
    sys.path.insert(0, str(REPO / "services" / "api"))
    from sqlalchemy.orm import sessionmaker

    from app.db.session import make_engine

    return sessionmaker(bind=make_engine(database_url), autoflush=False, expire_on_commit=False)()


def table_counts(session) -> dict[str, int]:
    from sqlalchemy import text

    return {
        table: int(session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one())
        for table in _COUNTED_TABLES
    }


def annotate_from_db(rows: Sequence[MutableMapping[str, Any]], session) -> dict[str, str]:
    """Attach database-derived planning facts to each row, and return supersede edges.

    Done as a separate pass so the planner stays a pure function of its inputs:
    tests hand it the same facts without a database. Returns ``rule_id ->
    superseded_rule_id`` for existing rules so supersession cycles can be detected.
    """
    from sqlalchemy import select

    from app.models import AccessRule, RuleCandidate

    edges: dict[str, str] = {}
    for row in rows:
        candidate = session.get(RuleCandidate, row["candidate_id"])
        if candidate is None:
            row["_supersedes_existing"] = []
            continue
        row["place_id"] = candidate.place_id
        row["zone_id"] = candidate.zone_id
        row["source_id"] = candidate.source_id
        row["animal_scope"] = candidate.animal_scope
        row["action"] = candidate.action
        row["effect"] = candidate.effect
        row["_db_review_status"] = candidate.review_status
        row["published_rule_id"] = candidate.published_rule_id
        owner = (
            AccessRule.zone_id == candidate.zone_id
            if candidate.zone_id
            else AccessRule.place_id == candidate.place_id
        )
        found = session.scalars(
            select(AccessRule).where(
                owner,
                AccessRule.status == "current",
                AccessRule.source_id == candidate.source_id,
                AccessRule.animal_scope == candidate.animal_scope,
                AccessRule.action == candidate.action,
            )
        ).all()
        row["_supersedes_existing"] = sorted(str(r.id) for r in found)
        for existing in found:
            if existing.supersedes_rule_id:
                edges[str(existing.id)] = str(existing.supersedes_rule_id)
    return edges


def fetch_candidate_state(api: Api) -> dict[str, dict]:
    """candidate_id -> {rule_layer, mandatory_level, review_status} from the API.

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


# ============================================================ CLI


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--reviewer", default=None, help="具名人类评审员；必须与登记表署名一致")
    ap.add_argument("--token", default=None, help="admin JWT；缺省读 .env 的 PILOT_ADMIN_TOKEN")
    ap.add_argument("--max-approve", type=int, default=20)
    ap.add_argument(
        "--batch-file",
        default=None,
        help=(
            "显式批次清单（docs/governance/publish_batches/*.json）。"
            "--execute 必须提供；--max-approve 只是其上的第二层 safety cap，不是选择器。"
        ),
    )
    ap.add_argument(
        "--registry",
        default=None,
        help="评审登记表路径（缺省：按 R2-FINAL → R2 → R1 取最新登记表）",
    )
    ap.add_argument(
        "--database-url",
        default=None,
        help="发布闸门使用的数据库（缺省：环境变量 DATABASE_URL 或应用设置）",
    )
    ap.add_argument(
        "--database-name",
        default=None,
        help=(
            "只改库名（从 .env 的 DATABASE_URL 派生，不回显凭据）。"
            "rehearsal 演练时用来让闸门与 API 指向同一个库。"
        ),
    )
    ap.add_argument("--json", action="store_true", help="额外输出机器可读的完整计划")
    ap.add_argument(
        "--production-confirm",
        action="store_true",
        help=(
            "显式确认：--execute 允许打在 PRODUCTION（petaccess）上。"
            "缺省拒绝——正式库写入必须是显式选择，而不是脚本默认落点（§17）。"
        ),
    )
    ap.add_argument(
        "--snapshot-out",
        default=None,
        help=(
            "发布回执写到哪里（缺省 PUBLISHED_RULES_SNAPSHOT_R1.json）。"
            "rehearsal 演练必须指向 artifacts/，否则会把演练结果写成看起来像正式回执的文件。"
        ),
    )
    args = ap.parse_args()

    global DECISIONS
    if args.registry:
        DECISIONS = Path(args.registry)
    print(f"登记表：{DECISIONS}")

    if args.database_name:
        # Bookkeeping guard, not a convenience: rehearsing against a cloned
        # database while the pre-publish gate read the *real* one would make the
        # rehearsal report a check it never performed.
        from dev_api_server import database_url_for

        resolved = database_url_for(args.database_name)
        if resolved is None:
            print(f"REFUSED — 无法从 .env 解析 DATABASE_URL，不能只改库名到 {args.database_name}")
            return 4
        args.database_url = resolved
        print(f"发布闸门数据库：{args.database_name}")

    if not (args.dry_run ^ args.execute):
        print("必须且只能指定 --dry-run 或 --execute")
        return 2

    if args.execute and not args.batch_file:
        # Checked before the database guard on purpose: this is a usage error and
        # its message is the actionable one. Reporting "wrong database role" for a
        # bare `--execute` would send the operator to change their target instead
        # of telling them the command is incomplete.
        print(
            "REFUSED — --execute 必须同时提供 --batch-file。\n"
            "裸 --execute 会把登记表里所有 APPROVED 一次发出，"
            "而『发哪几条』必须由人类显式选定（见 docs/governance/PUBLISH_PLAN_MODEL.md）。"
        )
        return 4

    if args.execute:
        # §17: the publish target must be an explicit choice. A rehearsal clone is
        # allowed (that is what REHEARSAL exists for); anything else is refused, so
        # a mistyped `--database-name` cannot turn into an unrecoverable write on a
        # database nobody intended to touch.
        import os as _os

        from app.db.safety import DatabaseRole, DatabaseSafetyError, guard_for_url

        effective = args.database_url or _os.environ.get("DATABASE_URL")
        if not effective:
            from app.core.config import get_settings

            effective = get_settings().database_url
        try:
            guard = guard_for_url(effective)
        except DatabaseSafetyError as exc:
            print(f"REFUSED — 无法判定发布目标库的角色：{exc}")
            return 4
        print(guard.banner("PUBLISH_TARGET_DB"))
        if guard.role is DatabaseRole.PRODUCTION and not args.production_confirm:
            print(
                "REFUSED — 发布目标是 PRODUCTION，但未显式确认。\n"
                "  正式库写入必须显式加 --production-confirm（§17）。\n"
                "  演练请指向 REHEARSAL 角色的库。"
            )
            return 4
        if guard.role not in (DatabaseRole.PRODUCTION, DatabaseRole.REHEARSAL):
            print(
                f"REFUSED — 发布/演练只允许打在 PRODUCTION 或 REHEARSAL 上，"
                f"实际是 {guard.role.value}（{guard.database_name!r}）。"
            )
            return 4

    doc = load_registry()
    all_rows = doc["rows"]
    register_revision = str(doc.get("revision") or "")

    # The register's own binding table must be self-consistent before we trust it
    # to classify anything as a carve-out.
    closure = binding_closure_problems(doc)
    if closure:
        print("REFUSED — 登记表的 RuleException 绑定表不自洽：")
        for problem in closure:
            print(f"  - {problem}")
        return 4

    bindings = canonical_exception_bindings(doc)

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

    # ---- real gate, real database ------------------------------------------
    session = None
    before_counts: dict[str, int] = {}
    edges: dict[str, str] = {}
    try:
        session = build_session(args.database_url)
    except Exception as exc:  # environment dependent
        print(f"提示：未能连接数据库（{exc}）；发布闸门将以 NOT_RUN 报告。")
    if session is not None:
        # Annotate the *whole* register, not just the batch: supersede edges and
        # "is this base already published" are register-wide facts, and a batch
        # must not be able to hide a collision by leaving its partner out.
        edges = annotate_from_db(all_rows, session)
        before_counts = table_counts(session)
        gate: Gate = DatabaseGate(session)
    else:
        gate = NullGate()

    # ---- explicit batch selection (never a slice of the register) -----------
    manifest: BatchManifest | None = None
    batch: BatchValidation | None = None
    if args.batch_file:
        try:
            manifest = load_manifest(args.batch_file)
        except BatchManifestError as exc:
            print(f"REFUSED — {exc}")
            return 4
        batch = validate_manifest(
            manifest,
            all_rows,
            bindings=bindings,
            register_revision=register_revision,
            published_rule_ids=_published_rule_ids(all_rows),
            approved_exception_map=batch_approved_exception_map(doc, all_rows),
        )
        print(batch.render())
        print("")
        if not batch.ok:
            print("REFUSED — 批次校验未通过，任何写入都不会发生。")
            return 4

    rows = select_rows(all_rows, manifest) if manifest is not None else all_rows

    problems = preflight(rows, args.reviewer, args.max_approve, db_state)

    plan = build_plan(
        rows,
        bindings=bindings,
        gate=gate,
        revision=register_revision,
        reviewer=signed_reviewer(rows),
        already_published={
            r["candidate_id"]
            for r in rows
            if (r.get("_db_review_status") or r.get("review_status")) == "PUBLISHED"
        },
    )
    #: Rules *this plan* would write. Read from the rows, but only for candidates
    #: the plan actually considers writable: once a batch has run, every candidate
    #: records the rule it created, and counting those as "created by this plan"
    #: made a clean NOOP re-run look like six rules racing over their own
    #: identities (SELF_SUPERSEDE = 6, refusal for the wrong reason). A NOOP step
    #: writes nothing, so nothing of its own can be a supersede target.
    writable_candidates = {step.candidate_id for step in plan.writable}
    created_ids: set[str] = {
        str(row["published_rule_id"])
        for row in rows
        if row.get("published_rule_id") and str(row["candidate_id"]) in writable_candidates
    }
    integrity = plan_integrity(
        plan,
        rows_by_rule={str(r["rule_id"]): r for r in rows},
        supersession_edges=edges,
        created_ids=created_ids,
    )

    zero_mutation = True
    if session is not None:
        zero_mutation = table_counts(session) == before_counts

    print(render_plan(plan, integrity))
    print("")
    if problems:
        print(f"发布前置条件未满足（{len(problems)} 项）——以下为需要人类评审员处理的事项：")
        for problem in problems:
            print(f"  - {problem}")
    if args.json:
        print(
            json.dumps(
                plan_as_json(
                    plan,
                    integrity,
                    {
                        "mode": "dry-run" if args.dry_run else "execute",
                        "at": _now(),
                        "registry": _registry_display(),
                        "db_gate": session is not None,
                        "db_cross_checked": db_state is not None,
                        "DRY_RUN_ZERO_DB_MUTATION": zero_mutation,
                        "preflight_problems": problems,
                        "counts_before": before_counts,
                        "batch": batch.summary() if batch is not None else None,
                        "selection": "manifest" if manifest is not None else "whole-register",
                    },
                ),
                ensure_ascii=False,
                indent=2,
            )
        )

    if args.dry_run:
        return 0 if not problems else 3

    # ---- execute: never without the real gate -------------------------------
    if problems:
        print("PREFLIGHT FAILED — 未满足发布前置条件：")
        for problem in problems:
            print(f"  - {problem}")
        return 3
    if not plan.gate_ran:
        print("REFUSED — 发布闸门未真实执行（数据库不可用），不得写库。")
        return 4
    if integrity["SELF_SUPERSEDE"] or integrity["DUPLICATE_PUBLICATION_PLAN"]:
        print("REFUSED — 计划自检未通过（self-supersede / duplicate plan）")
        return 4

    # Bases published by an earlier batch are still valid carve-out anchors; the
    # batch validator proved the closure, so the executor needs their ids.
    prepublished_bases = {
        str(r["rule_id"]): str(r["published_rule_id"]) for r in rows if r.get("published_rule_id")
    }
    result = execute_plan(plan, api, prepublished_bases=prepublished_bases)
    summary = {
        "mode": "execute",
        "at": _now(),
        "reviewer": plan.reviewer,
        "batch_id": batch.batch_id if batch is not None else None,
        "selection": "manifest" if manifest is not None else "whole-register",
        "counts": {k: len(v) for k, v in result.items()},
    }
    print(json.dumps({"summary": summary, "detail": result}, ensure_ascii=False, indent=2))
    snapshot = Path(args.snapshot_out) if args.snapshot_out else SNAPSHOT
    if snapshot.parent and not snapshot.parent.exists():
        snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(
        json.dumps({"summary": summary, "detail": result}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if not result["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
