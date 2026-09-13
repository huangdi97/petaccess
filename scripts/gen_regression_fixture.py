"""Generate REAL-WORLD-REGRESSION-FIXTURES (S11) from the R2 audit samples.

Run from services/api:  uv run python ../../scripts/gen_regression_fixture.py
Reads docs/reality_audit/real_pilot_samples_r2.json, runs the audit resolver
per query, records expected outcomes, sanitizes identifying fields.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "api"))

from app.tools.reality_audit import _resolve_query  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def main() -> int:
    d = json.loads(
        (REPO / "docs/reality_audit/real_pilot_samples_r2.json").read_text(encoding="utf-8")
    )

    fixture = {
        "_readme": [
            "REAL-WORLD-REGRESSION-FIXTURES (PILOT-REVIEW-AND-SCHEMA-FIX-01 S11).",
            "Sanitized abstraction of the 10 real Shanghai pilot places (R2 evidence state):",
            "identifying names/addresses/coordinates replaced by rw-XX keys; normative",
            "content (zones/rules/exceptions/queries/expected resolver outcomes) preserved",
            "for resolver regression. Expected values recorded from the actual R2 audit run",
            "(docs/reality_audit/real_pilot_02/) - regenerate via the audit tool, never hand-edit.",
        ],
        "generated_from": "docs/reality_audit/real_pilot_samples_r2.json",
        "expected_run": "REALITY-AUDIT-10-R2 (real_pilot_02)",
        "places": [],
    }

    type_key = {
        "mall": "mall",
        "scenic_area": "scenic",
        "park": "park",
        "library": "library",
        "hotel": "hotel",
        "cafe": "cafe",
    }
    for counter, sample in enumerate(d["samples"], start=1):
        ptype = type_key[sample["place"]["place_type"]]
        expected = []
        for q in sample["queries"]:
            buckets = {
                layer: [r for r in sample["rules"] if r.get("rule_layer") == layer]
                for layer in ("LEGAL", "REGULATORY_GUIDANCE", "OPERATOR_POLICY", "TEMPORARY_POLICY")
            }
            rs = _resolve_query(sample, q, buckets, {})
            expected.append(
                {
                    "animal": q.get("animal", "dog"),
                    "service_role": q.get("service_role", "none"),
                    "action": q.get("action", "enter"),
                    "zone_key": q.get("zone_key"),
                    "expected_effect": rs.effect,
                    "expected_compliance": rs.compliance_state.value,
                    "expected_exceptions": rs.applied_exceptions,
                }
            )
        fixture["places"].append(
            {
                "key": f"rw-{counter:02d}-{ptype}-{sample['sample_id'].split('-', 2)[-1]}",
                "place_type": sample["place"]["place_type"],
                "zones": sample["zones"],
                "sources": [
                    {
                        k: src[k]
                        for k in (
                            "source_key",
                            "source_type",
                            "display_allowed",
                            "redistribution_allowed",
                        )
                        if k in src
                    }
                    for src in sample["sources"]
                ],
                "rules": [{k: r[k] for k in r if k != "note"} for r in sample["rules"]],
                "queries": expected,
            }
        )

    out = REPO / "tests/fixtures/real_world_regression.json"
    out.write_text(json.dumps(fixture, ensure_ascii=False, indent=1), encoding="utf-8")
    n_q = sum(len(p["queries"]) for p in fixture["places"])
    n_e = sum(len(r.get("exceptions", [])) for p in fixture["places"] for r in p["rules"])
    print(f"fixture: {len(fixture['places'])} places, {n_q} queries, {n_e} exceptions -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
