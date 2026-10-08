"""Consumer OpenAPI drift guards.

The consumer layer treats FastAPI OpenAPI as the DTO SSOT. These checks are
intentionally narrow: they protect the canonical Reality event feed and the
committed generated snapshot without making unrelated documentation wording a
release gate.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENAPI_SNAPSHOT = REPO_ROOT / "packages" / "api-client" / "openapi.json"
EVENT_PATH = "/api/v1/places/{place_id}/reality/events"


def _event_contract(schema: dict) -> tuple[set[str], set[str]]:
    event = schema["components"]["schemas"]["RealityEventOut"]
    return set(event["properties"]), set(event["required"])


def test_reality_event_feed_exists_in_live_and_committed_openapi() -> None:
    live = app.openapi()
    committed = json.loads(OPENAPI_SNAPSHOT.read_text(encoding="utf-8"))

    assert EVENT_PATH in live["paths"]
    assert EVENT_PATH in committed["paths"]
    assert "get" in live["paths"][EVENT_PATH]
    assert "get" in committed["paths"][EVENT_PATH]

    live_props, live_required = _event_contract(live)
    committed_props, committed_required = _event_contract(committed)

    critical = {
        "id",
        "event_type",
        "place_id",
        "event_at",
        "time_basis",
        "time_evidence_state",
        "origin",
        "fact_evidence_state",
        "place_match_state",
        "staff_awareness_state",
        "staff_policy_statement_verbatim",
        "facility_purpose_state",
        "dispute_open",
        "source_id",
        "evidence_bundle_id",
        "submitted_at",
        "verification_status",
        "last_verified_at",
    }
    assert critical <= live_props
    assert critical <= committed_props
    # The committed snapshot backs generated frontend DTOs. Any extra or
    # missing consumer event field is drift, even if an older "critical"
    # subset still happens to pass.
    assert live_props == committed_props
    assert live_required == committed_required


def test_reality_event_feed_is_read_only_consumer_surface() -> None:
    schema = app.openapi()
    operations = schema["paths"][EVENT_PATH]
    assert set(operations) == {"get"}
    response = operations["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert response["type"] == "array"
    assert response["items"]["$ref"] == "#/components/schemas/RealityEventOut"
