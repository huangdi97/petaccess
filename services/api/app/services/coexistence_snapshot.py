"""v0.9-R1 CoexistenceSnapshot — the one consumer aggregate for a place.

Design v0.9 §9 / AC9: Home / Search / Map / Place must all consume the SAME
snapshot; no surface recomputes rule or reality. This module assembles:

    RuleAnswer            (from app.rulespec.access_answer build_access_answer)
    RealityAnswer         (from app.services.reality_summary summarize)
    StaffResponseSummary  (action counts, facts only)
    FacilitySummary       (facility facts, freshness attached)
    RuleRealityDivergence (app.services.rule_reality_divergence)
    EvidenceSummary       (rule-side evidence + reality-side evidence counts)

The assembly is *pure*: every fact arrives as an argument, so the builder is
unit-testable without a database, and the HTTP layer holds no rule/reality
logic. Nothing here rewrites a rule, a claim, or a divergence verdict — it only
bundles them with an explicit ``generated_at``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from app.services.rule_reality_divergence import Divergence, divergence

#: Bump when the shape or derivation rules change. Consumers key off this.
COEXISTENCE_SNAPSHOT_VERSION = "coexistence-snapshot/1"


@dataclass(frozen=True)
class EvidenceSummary:
    """Both halves of the evidence story, kept side by side."""

    rule_evidence: list[dict[str, Any]]  # access_answer.evidence_state.rules
    rule_first_party_pending: bool
    reality_evidence_count: int
    reality_distinct_source_count: int
    reality_verification_state: str | None


@dataclass(frozen=True)
class CoexistenceSnapshot:
    """Immutable bundle — one place, one generated_at, both fact layers.

    ``divergence`` is derived from the rule effect + reality state already
    computed by their owning engines; this module never re-decides either.
    """

    place_id: str
    generated_at: datetime
    version: str
    rule_answer: dict[str, Any]
    reality_answer: dict[str, Any]
    staff_response_summary: list[dict[str, Any]]
    facility_summary: list[dict[str, Any]]
    divergence: Divergence
    evidence_summary: EvidenceSummary


def build_coexistence_snapshot(
    *,
    place_id: str,
    rule_answer: dict[str, Any],
    reality_answer: dict[str, Any],
    staff_response_summary: list[dict[str, Any]],
    facility_summary: list[dict[str, Any]],
    now: datetime | None = None,
) -> CoexistenceSnapshot:
    """Assemble one snapshot. Pure: takes plain values, returns plain values.

    ``rule_answer`` is the output of ``build_access_answer``; ``reality_answer``
    the output of the consumer reality aggregate (its ``state`` field is one of
    the six RealitySummary states). Both are treated as opaque facts here —
    the divergence verdict is the only thing computed in this module, and it
    only *describes*; it never alters either answer.
    """
    now = now or datetime.now(UTC)

    rule_effect = str((rule_answer.get("normative_result") or {}).get("effect") or "unknown")
    reality_state = str(reality_answer.get("state") or "INSUFFICIENT_OBSERVATION")

    rule_evidence_state = rule_answer.get("evidence_state") or {}
    reality_evidence_count = int(reality_answer.get("evidence_count") or 0)
    reality_distinct_sources = int(reality_answer.get("distinct_source_count") or 0)

    return CoexistenceSnapshot(
        place_id=place_id,
        generated_at=now,
        version=COEXISTENCE_SNAPSHOT_VERSION,
        rule_answer=rule_answer,
        reality_answer=reality_answer,
        staff_response_summary=staff_response_summary,
        facility_summary=facility_summary,
        divergence=divergence(
            rule_effect=rule_effect,
            reality_state=reality_state,
        ),
        evidence_summary=EvidenceSummary(
            rule_evidence=list(rule_evidence_state.get("rules") or []),
            rule_first_party_pending=bool(
                rule_evidence_state.get("first_party_operator_source_pending")
            ),
            reality_evidence_count=reality_evidence_count,
            reality_distinct_source_count=reality_distinct_sources,
            reality_verification_state=reality_answer.get("verification_state"),
        ),
    )


def to_plain(snapshot: CoexistenceSnapshot) -> dict[str, Any]:
    """JSON-safe copy of the snapshot (datetimes → ISO, dataclasses → dict)."""

    def plain(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: plain(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [plain(v) for v in value]
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Divergence):
            return asdict(value)
        if hasattr(value, "__dataclass_fields__"):
            return asdict(value)
        return value

    return {
        "place_id": snapshot.place_id,
        "generated_at": snapshot.generated_at.isoformat(),
        "version": snapshot.version,
        "rule_answer": plain(snapshot.rule_answer),
        "reality_answer": plain(snapshot.reality_answer),
        "staff_response_summary": plain(snapshot.staff_response_summary),
        "facility_summary": plain(snapshot.facility_summary),
        "divergence": asdict(snapshot.divergence),
        "evidence_summary": asdict(snapshot.evidence_summary),
    }
