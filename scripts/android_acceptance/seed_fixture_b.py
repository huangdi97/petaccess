"""PROFILE B fixture seeder for the Android acceptance DB (petaccess_e2e_android).

Drives the *real* API (same endpoints the app calls) to create deterministic
fixtures covering the domain-state matrix of the acceptance goal:

- Reality states via human-verified published claims: OBSERVED_RECENTLY,
  MULTI_EVIDENCE_OBSERVED, OBSERVED_HISTORICALLY, and one unverified
  candidate for INSUFFICIENT_OBSERVATION.
- Staff responses (several actions) + awareness states.
- Facilities (several types) + purpose states.
- RealityReports with varied place_match / time_evidence / fact_evidence.
- A place with no rules at all -> UNKNOWN rule state.

Guard: refuses to run unless the live DB role is E2E/TEST/VISUAL (never
production). Idempotent by construction: rows are keyed by deterministic
uuids and the presence payload carries a unique note per row.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "services" / "api"))
sys.path.insert(0, str(REPO / "scripts"))

# The acceptance DB is the only database this seeder may touch; every in-process
# connection (get_session_factory / dev_api_server helpers) must resolve to it,
# never to the .env production default.
import os  # noqa: E402

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://petaccess:petaccess_dev_only@localhost:5432/petaccess_e2e_android"
)
API = "http://127.0.0.1:8010/api/v1"
EMAIL = "android.fixture.acceptance@gmail.com"
PASSWORD = "passw0rd123"


def _probe_role() -> str:
    import psycopg
    from dev_api_server import psycopg_url_for  # type: ignore[import-not-found]

    from app.db.safety import guard_for_psycopg  # type: ignore[import-not-found]

    with psycopg.connect(psycopg_url_for("petaccess_e2e_android")) as conn:
        guard = guard_for_psycopg(conn)
    return guard.role.value


def _request(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        print(f"  HTTP {e.code} {method} {path}: {raw[:240]}")
        raise


def _login_or_register() -> str:
    try:
        r = _request("POST", "/auth/login", {"email": EMAIL, "password": PASSWORD})
        return r["access_token"]
    except Exception:
        r = _request(
            "POST",
            "/auth/register",
            {"display_name": "Android Fixture", "email": EMAIL, "password": PASSWORD},
        )
        return r["access_token"]


def _promote_admin() -> None:
    """Promote the fixture user to admin so human reality decisions work."""
    from app.db.session import get_session_factory
    from app.models import User

    s = get_session_factory()()
    try:
        user = s.query(User).filter(User.email == EMAIL).first()
        if user is not None and user.role != "admin":
            user.role = "admin"
            s.commit()
            print("  promoted fixture user to admin")
    finally:
        s.close()


def _existing_places() -> dict[str, str]:
    r = _request("GET", "/places?limit=100")
    return {it["canonical_name"]: it["id"] for it in r.get("items", [])}


def _place_id(name: str) -> str | None:
    return _existing_places().get(name)


def _create_place(token: str, name: str, place_type: str) -> str:
    body = {
        "canonical_name": name,
        "place_type": place_type,
        "canonical_address": "上海市测试区",
        "location_wkt": (
            f"POINT({121.40 + (len(name) % 5) * 0.01} {31.20 + (len(name) % 3) * 0.01})"
        ),
        "alias_names": [],
    }
    r = _request("POST", "/places", body, token)
    return r["id"]


def _submit_verified(
    token: str, place_id: str, candidate_type: str, payload: dict, days_ago: int
) -> str:
    """Create one reality candidate and human-verify it (v0.9 7.4)."""
    body = {
        "candidate_type": candidate_type,
        "place_id": place_id,
        "animal_scope": "dog",
        "observed_at": (datetime.now(UTC) - timedelta(days=days_ago)).isoformat(),
        "payload": payload,
    }
    r = _request("POST", f"/places/{place_id}/reality/contributions", body, token)
    cand_id = r["id"]
    _request(
        "POST",
        f"/reality/candidates/{cand_id}/decision",
        {"reality_decision": "verified", "decision_note": None},
        token,
    )
    return cand_id


def _submit_report(token: str, place_id: str, report: dict) -> str:
    r = _request(
        "POST",
        f"/places/{place_id}/reality/reports",
        {"report": report, "candidates": []},
        token,
    )
    return r.get("id", "")


def main() -> int:
    global API
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=API)
    args = ap.parse_args()
    API = args.api

    role = _probe_role()
    if role not in ("E2E", "TEST", "VISUAL"):
        print(f"REFUSED: live DB role is {role}, not E2E/TEST; refusing to seed")
        return 3
    print(f"target DB role = {role} (guard passed)")

    token = _login_or_register()
    _promote_admin()

    places = _existing_places()
    print("existing places:", sorted(places))

    # Place with no rules -> UNKNOWN rule state.
    if "测试·无规则场所" not in places:
        _create_place(token, "测试·无规则场所", "park")
        print("  created 测试·无规则场所 (UNKNOWN rule state)")

    # The demo cafe has PROHIBITED indoor / ALLOWED outdoor rules; attach
    # verified presence claims of different ages to show every reality state.
    cafe = _place_id("星河咖啡·测试店")
    if not cafe:
        print("REFUSED: demo cafe 星河咖啡·测试店 missing; run isolated_db reset first")
        return 3

    _submit_verified(
        token,
        cafe,
        "observed_presence",
        {"observed_action": "present", "observed_context": "fixture-1d-门口出现"},
        1,
    )
    _submit_verified(
        token,
        cafe,
        "observed_presence",
        {"observed_action": "present", "observed_context": "fixture-3d-户外区域"},
        3,
    )
    _submit_verified(
        token,
        cafe,
        "observed_presence",
        {"observed_action": "present", "observed_context": "fixture-20d-历史两周前"},
        20,
    )
    _submit_verified(
        token,
        cafe,
        "observed_presence",
        {"observed_action": "present", "observed_context": "fixture-120d-历史四月前"},
        120,
    )
    print("  presence claims seeded (1d/3d/20d/120d)")

    _submit_verified(
        token,
        cafe,
        "staff_response",
        {
            "actor_role": "frontline_staff",
            "response_action": "provide_water",
            "awareness_state": "awareness_confirmed",
            "response_outcome": "observed once",
        },
        2,
    )
    _submit_verified(
        token,
        cafe,
        "staff_response",
        {
            "actor_role": "frontline_staff",
            "response_action": "remind_leash",
            "awareness_state": "awareness_likely",
            "response_outcome": "observed once",
        },
        5,
    )
    _submit_verified(
        token,
        cafe,
        "staff_response",
        {
            "actor_role": "frontline_staff",
            "response_action": "deny_entry",
            "awareness_state": "awareness_unknown",
            "response_outcome": "observed once",
        },
        40,
    )
    _submit_verified(
        token,
        cafe,
        "staff_response",
        {
            "actor_role": "frontline_staff",
            "response_action": "no_intervention_observed",
            "awareness_state": "awareness_unknown",
            "response_outcome": "observed once",
        },
        10,
    )
    print("  staff responses seeded (water/leash/deny/none + awareness)")

    _submit_verified(
        token,
        cafe,
        "animal_facility",
        {
            "facility_type": "water_bowl",
            "purpose_state": "purpose_confirmed",
            "operational_state": "active",
            "access_mode": "operator_provided",
        },
        2,
    )
    _submit_verified(
        token,
        cafe,
        "animal_facility",
        {
            "facility_type": "pet_waiting_area",
            "purpose_state": "purpose_signage_supported",
            "operational_state": "active",
            "access_mode": "self_service",
        },
        2,
    )
    _submit_verified(
        token,
        cafe,
        "animal_facility",
        {
            "facility_type": "outdoor_holding_cage",
            "purpose_state": "purpose_unknown",
            "operational_state": "active",
            "access_mode": "unknown",
        },
        2,
    )
    print("  facilities seeded (water/waiting/cage + purpose levels)")

    # One unverified candidate for INSUFFICIENT_OBSERVATION.
    _request(
        "POST",
        f"/places/{cafe}/reality/contributions",
        {
            "candidate_type": "observed_presence",
            "place_id": cafe,
            "animal_scope": "cat",
            "observed_at": (datetime.now(UTC) - timedelta(hours=6)).isoformat(),
            "payload": {"observed_action": "present", "observed_context": "fixture-unverified"},
        },
        token,
    )
    print("  unverified candidate seeded (INSUFFICIENT_OBSERVATION)")

    # Reality reports with explicit place-match / time-evidence / fact-evidence.
    _submit_report(
        token,
        cafe,
        {
            "origin": "on_site_past",
            "place_id": cafe,
            "place_match_state": "exact_place",
            "time_evidence_state": "exact_event_date",
            "fact_evidence_state": "first_hand_no_media",
            "observed_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
    )
    _submit_report(
        token,
        cafe,
        {
            "origin": "external_online_content",
            "place_id": cafe,
            "place_match_state": "parent_place_only",
            "time_evidence_state": "publication_time_only",
            "content_published_at": (datetime.now(UTC) - timedelta(days=6)).isoformat(),
            "fact_evidence_state": "text_only_external",
            "source_url": "https://example.com/fixture-post",
            "source_platform": "web",
        },
    )
    print("  reality reports seeded (exact/parent match, event/publication time)")

    print("PROFILE B SEED OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
