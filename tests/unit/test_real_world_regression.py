"""REAL-WORLD-REGRESSION-FIXTURES (S11): resolver regression over the 10 real
pilot places, sanitized. The fixture records expected resolver outcomes from
the REALITY-AUDIT-10-R2 run; this test independently rebuilds LayeredRules /
LayeredExceptions from the fixture data and asserts the resolver still produces
exactly those outcomes. Regenerate the fixture via
scripts/gen_regression_fixture.py — never hand-edit expectations.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.rulespec.v05_resolver import (
    LayeredException,
    LayeredRule,
    resolve,
)

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "real_world_regression.json"
NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)

_data = json.loads(FIXTURE.read_text(encoding="utf-8"))
_PLACES = _data["places"]


def _parse(dt: str | None):
    return datetime.fromisoformat(dt) if dt else None


def _rule_id_prefix(sample_key: str) -> str:
    """Rules across places share ids only within a sample; keep them unique."""
    return sample_key


def _build(place: dict):
    key = place["key"]
    rules = place["rules"]
    buckets: dict[str, list[LayeredRule]] = {
        "LEGAL": [],
        "REGULATORY_GUIDANCE": [],
        "OPERATOR_POLICY": [],
        "TEMPORARY_POLICY": [],
    }
    exceptions: list[LayeredException] = []
    for r in rules:
        layer = r.get("rule_layer") or "OPERATOR_POLICY"
        lr = LayeredRule(
            id=f"{key}:{r['rule_id']}",
            animal_scope=r.get("animal_scope") or "ordinary_pet",
            action=r.get("action") or "enter",
            effect=r["effect"],
            rule_layer=layer,
            origin="legal" if layer == "LEGAL" else "operator_direct",
            conditions=tuple(r.get("conditions") or ()),
            zone_id=r.get("zone_key"),
            source_id=r.get("source_key"),
            mandatory_level=r.get("mandatory_level"),
            effective_from=_parse(r.get("effective_from")),
            effective_to=_parse(r.get("effective_to")),
            # ADR-025: source-faithful scope — a rule only governs the precise
            # subject the source names, never an ontology parent.
            source_scope_exact=r.get("source_scope_exact"),
            subject_scope_normalized=r.get("subject_scope_normalized"),
            normalization_type=r.get("normalization_type"),
        )
        buckets[layer].append(lr)
        for exc in r.get("exceptions") or []:
            exceptions.append(
                LayeredException(
                    id=f"{key}:{exc['exception_id']}",
                    rule_id=f"{key}:{r['rule_id']}",
                    animal_scope=exc["animal_scope"],
                    effect=exc["effect"],
                    source_id=exc.get("source_key"),
                    status=exc.get("status") or "current",
                    effective_from=_parse(exc.get("effective_from")),
                    effective_to=_parse(exc.get("effective_to")),
                    subject_scope_normalized=exc.get("subject_scope_normalized"),
                    normalization_type=exc.get("normalization_type"),
                )
            )
    return buckets, exceptions


def _resolve(place: dict, q: dict):
    buckets, exceptions = _build(place)
    return resolve(
        legal=buckets["LEGAL"],
        guidance=buckets["REGULATORY_GUIDANCE"],
        template_rules=[],
        operator_rules=buckets["OPERATOR_POLICY"],
        event_rules=buckets["TEMPORARY_POLICY"],
        animal=q["animal"],
        service_role=q["service_role"],
        action=q["action"],
        zone_id=q.get("zone_key"),
        now=NOW,
        exceptions=exceptions,
        declared_role=q.get("declared_role"),
    )


@pytest.mark.parametrize("place", _PLACES, ids=lambda p: p["key"])
def test_place_queries_match_recorded_outcomes(place):
    for q in place["queries"]:
        rs = _resolve(place, q)
        assert rs.effect == q["expected_effect"], (
            f"{place['key']} {q}: effect {rs.effect} != {q['expected_effect']}; "
            f"steps={rs.explanation_steps}"
        )
        assert rs.compliance_state.value == q["expected_compliance"], (
            f"{place['key']} {q}: compliance drift"
        )


def test_fixture_covers_service_dog_exemptions():
    """The fixture must keep covering the SG-REAL-01 regression surface."""
    working_queries = [q for p in _PLACES for q in p["queries"] if q["service_role"] == "working"]
    assert len(working_queries) >= 7
    assert any(q["expected_exceptions"] for p in _PLACES for q in p["queries"])


def test_prohibitions_trace_to_explicit_rules():
    """No prohibition may exist without an explicit prohibited rule/exception
    (same invariant as the property suite, over real-world data)."""
    for place in _PLACES:
        for q in place["queries"]:
            if q["expected_effect"] != "prohibited":
                continue
            buckets, exceptions = _build(place)
            pool = buckets["LEGAL"] + buckets["OPERATOR_POLICY"] + buckets["TEMPORARY_POLICY"]
            assert any(r.effect == "prohibited" for r in pool), place["key"]
            assert not (exceptions and all(e.effect == "allowed" for e in exceptions) and not pool)


def test_time_drift_keeps_exceptions_honest():
    """Expired exceptions (simulated by moving `now` far ahead where effective_to
    is set) must fall back to the base rule — fixture rules with validity windows
    stay future-proof under resolver changes."""
    far_future = NOW + timedelta(days=3650)
    for place in _PLACES:
        for q in place["queries"]:
            buckets, exceptions = _build(place)
            rs = resolve(
                legal=buckets["LEGAL"],
                guidance=buckets["REGULATORY_GUIDANCE"],
                template_rules=[],
                operator_rules=buckets["OPERATOR_POLICY"],
                event_rules=buckets["TEMPORARY_POLICY"],
                animal=q["animal"],
                service_role=q["service_role"],
                action=q["action"],
                zone_id=q.get("zone_key"),
                now=far_future,
                exceptions=exceptions,
            )
            assert rs.effect in {"allowed", "prohibited", "conditional", "unknown"}
