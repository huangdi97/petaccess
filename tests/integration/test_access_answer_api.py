"""The unified answer endpoint, end to end (design §10 / Century Park release §7).

The unit tests pin the *derivation*. This file pins the *wire*: the route exists,
the answer survives JSON, and the two over-generalisations are absent when read
through HTTP against real rows.

The fixture is deliberately the awkward shape: one zone carries a prohibition and
a sibling zone carries nothing. That is the arrangement where a flattened
implementation would look right in the first assertion and wrong in the second.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def moderator(client):
    email = f"ans-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"display_name": "答案模型测试", "email": email, "password": "passw0rd123"},
    )
    assert r.status_code == 201, r.text

    from app.db.session import get_session_factory
    from app.models import User

    s = get_session_factory()()
    row = s.query(User).filter(User.email == email).one()
    row.role = "moderator"
    s.commit()
    s.close()
    return {"token": r.json()["access_token"]}


def _auth(m):
    return {"Authorization": f"Bearer {m['token']}"}


@pytest.fixture(scope="module")
def scene(client, moderator):
    """A place with two zones: one governed, one uncovered."""
    tag = uuid.uuid4().hex[:6]
    src = client.post(
        "/api/v1/sources",
        json={
            # The Century Park shape on purpose: a government platform relaying
            # the operator, not the operator's own page.
            "source_type": "government_service",
            "issuer": f"某政府平台转述园区口径（{tag}）",
            "issuer_verification": "verified",
            "directness": "secondary",
            "notes": "capture_method=search_snippet; needs_verification=True",
        },
        headers=_auth(moderator),
    )
    assert src.status_code == 201, src.text
    place = client.post(
        "/api/v1/places",
        json={"canonical_name": f"答案模型测试场所{tag}", "place_type": "park"},
        headers=_auth(moderator),
    )
    assert place.status_code == 201, place.text
    place_id = place.json()["id"]

    def mk_zone(name, zone_type):
        z = client.post(
            # `places.admin` carries no path prefix — the zone write lives at
            # /zones, guarded by the moderator role rather than by a prefix.
            "/api/v1/zones",
            json={"place_id": place_id, "name": name, "zone_type": zone_type},
            headers=_auth(moderator),
        )
        assert z.status_code == 201, z.text
        return z.json()["id"]

    governed = mk_zone("其他区域", "area")
    uncovered = mk_zone("宠物乐园", "pet_area")

    rule = client.post(
        "/api/v1/rules",
        json={
            "place_id": place_id,
            "zone_id": governed,
            "animal_scope": "ordinary_pet",
            "action": "enter",
            "effect": "prohibited",
            "source_id": src.json()["id"],
            "rule_layer": "OPERATOR_POLICY",
            "mandatory_level": "operator_discretion",
            "rule_origin": "operator_declared",
            "normative_effect": "prohibition",
            "source_scope_exact": "宠物",
            "subject_scope_normalized": "ordinary_pet",
            "normalization_type": "exact",
        },
        headers=_auth(moderator),
    )
    assert rule.status_code in (200, 201), rule.text
    return {
        "place_id": place_id,
        "governed": governed,
        "uncovered": uncovered,
        "rule_id": rule.json()["id"],
    }


def _answer(client, place_id, **body):
    payload = {"animal": "dog", "service_role": "none", "action": "enter"}
    payload.update(body)
    r = client.post(f"/api/v1/places/{place_id}/access-answer", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


REQUIRED_FIELDS = (
    "query_context",
    "normative_result",
    "condition_evaluation",
    "scope_summary",
    "evidence_state",
    "conflict_state",
    "rights_information",
    "matched_rule_versions",
    "explanation_items",
    "next_actions",
    "evaluated_at",
    "valid_until",
    "evaluation_version",
)


def test_shape_is_the_thirteen_fields(client, scene):
    data = _answer(client, scene["place_id"], zone_id=scene["governed"])
    for field in REQUIRED_FIELDS:
        assert field in data, f"缺少 {field}"


def test_governed_zone_is_prohibited_at_zone_level(client, scene):
    data = _answer(client, scene["place_id"], zone_id=scene["governed"])
    assert data["normative_result"]["effect"] == "prohibited"
    assert data["scope_summary"]["scope_level"] == "zone"
    assert scene["rule_id"] in data["normative_result"]["governing_rule_ids"]


def test_zone_rule_does_not_become_a_place_verdict(client, scene):
    data = _answer(client, scene["place_id"], zone_id=None)
    assert data["normative_result"]["effect"] == "unknown"
    assert data["normative_result"]["effect"] != "prohibited"
    assert data["scope_summary"]["zone"] is None


def test_uncovered_zone_is_unknown_not_allowed(client, scene):
    data = _answer(client, scene["place_id"], zone_id=scene["uncovered"])
    assert data["normative_result"]["effect"] == "unknown"
    assert data["normative_result"]["effect"] != "allowed"
    assert any("未知不等于允许" in a for a in data["next_actions"])


def test_evidence_state_reports_the_relay_and_the_pending_gap(client, scene):
    data = _answer(client, scene["place_id"], zone_id=scene["governed"])
    ev = data["evidence_state"]
    assert ev["rules"], "有管辖规则时必须给出来源"
    entry = ev["rules"][0]
    assert entry["source_type"] == "government_service"
    assert entry["source_type_semantics"] == "政府平台转述园方口径"
    assert entry["first_party_operator_source_pending"] is True
    assert ev["first_party_operator_source_pending"] is True
    assert ev["first_party_operator_source_count"] == 0


def test_no_confirmation_claim_is_reachable(client, scene):
    """A relayed government source must never read as the operator confirming."""
    import json

    data = _answer(client, scene["place_id"], zone_id=scene["governed"])
    blob = json.dumps(data, ensure_ascii=False)
    for claim in ("官方已确认", "官方确认", "运营方已确认", "一手来源已核验"):
        assert claim not in blob


def test_zone_from_another_place_is_refused(client, scene, moderator):
    other = client.post(
        "/api/v1/places",
        json={"canonical_name": f"别处{uuid.uuid4().hex[:6]}", "place_type": "park"},
        headers=_auth(moderator),
    ).json()["id"]
    r = client.post(
        f"/api/v1/places/{other}/access-answer",
        json={"animal": "dog", "action": "enter", "zone_id": scene["governed"]},
    )
    # Answering would resolve this place's rules against another place's zone.
    assert r.status_code == 404
