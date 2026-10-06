"""Consumer rule-lead boundary: user input becomes review candidate, never Rule."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import get_session_factory
from app.main import app
from app.models import AccessRule, RuleCandidate, Zone
from app.models.media import MediaObject


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def signed_user(client) -> dict[str, str]:
    email = f"rule-lead-{uuid.uuid4().hex[:8]}@example.com"
    registered = client.post(
        "/api/v1/auth/register",
        json={"display_name": "规则线索测试用户", "email": email, "password": "passw0rd123"},
    )
    assert registered.status_code == 201, registered.text
    return {"Authorization": f"Bearer {registered.json()['access_token']}"}


def _place_id(client) -> str:
    response = client.get("/api/v1/places", params={"q": "云栖", "limit": 10})
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert items
    return items[0]["id"]


def test_rule_lead_creates_review_candidate_without_publishing_rule(client, signed_user):
    place_id = _place_id(client)
    factory = get_session_factory()
    with factory() as db:
        before_rules = db.scalar(
            select(func.count()).select_from(AccessRule).where(AccessRule.place_id == place_id)
        )

    response = client.post(
        f"/api/v1/places/{place_id}/rule-leads",
        headers=signed_user,
        json={
            "animal_scope": "ordinary_pet",
            "effect": "conditional",
            "proposed_conditions": ["carrier_required"],
            "raw_text": "入口告示写明普通宠物需装入宠物包。",
            "proximity_verified": True,
            "distance_bucket": "<100m",
            "accuracy_bucket": "10-50m",
        },
    )
    assert response.status_code == 201, response.text
    receipt = response.json()
    assert receipt["review_status"] == "REVIEW_PENDING"

    with factory() as db:
        candidate = db.get(RuleCandidate, receipt["id"])
        assert candidate is not None
        assert candidate.place_id == place_id
        assert candidate.review_status == "REVIEW_PENDING"
        assert candidate.effect == "conditional"
        assert candidate.proposed_conditions == [{"condition_type": "carrier_required"}]
        after_rules = db.scalar(
            select(func.count()).select_from(AccessRule).where(AccessRule.place_id == place_id)
        )
    assert after_rules == before_rules


def test_changed_rule_lead_persists_explicit_supersession_target(client, signed_user):
    factory = get_session_factory()
    with factory() as db:
        target = db.scalars(
            select(AccessRule).where(AccessRule.status == "current").limit(1)
        ).first()
        assert target is not None
        place_id = target.place_id
        assert place_id

    response = client.post(
        f"/api/v1/places/{place_id}/rule-leads",
        headers=signed_user,
        json={
            "animal_scope": target.animal_scope,
            "effect": "conditional",
            "proposed_conditions": ["carrier_required"],
            "raw_text": "用户报告这条现行规则已经变化。",
            "current_rule_id": target.id,
        },
    )
    assert response.status_code == 201, response.text

    with factory() as db:
        candidate = db.get(RuleCandidate, response.json()["id"])
        assert candidate is not None
        assert candidate.supersedes_rule_id == target.id


def test_changed_zone_rule_lead_preserves_zone_scope(client, signed_user):
    factory = get_session_factory()
    with factory() as db:
        target = db.scalars(
            select(AccessRule).where(
                AccessRule.status == "current",
                AccessRule.zone_id.isnot(None),
            ).limit(1)
        ).first()
        assert target is not None
        zone = db.get(Zone, target.zone_id)
        assert zone is not None
        place_id = zone.place_id
        target_id = target.id
        target_zone_id = target.zone_id
        animal_scope = target.animal_scope

    response = client.post(
        f"/api/v1/places/{place_id}/rule-leads",
        headers=signed_user,
        json={
            "animal_scope": animal_scope,
            "effect": "conditional",
            "proposed_conditions": ["carrier_required"],
            "raw_text": "用户报告该区域现行规则发生变化。",
            "current_rule_id": target_id,
        },
    )
    assert response.status_code == 201, response.text

    with factory() as db:
        candidate = db.get(RuleCandidate, response.json()["id"])
        assert candidate is not None
        assert candidate.supersedes_rule_id == target_id
        assert candidate.place_id == place_id
        assert candidate.zone_id == target_zone_id


def test_changed_rule_lead_rejects_scope_mismatch(client, signed_user):
    factory = get_session_factory()
    with factory() as db:
        target = db.scalars(
            select(AccessRule).where(
                AccessRule.status == "current",
                AccessRule.zone_id.isnot(None),
            ).limit(1)
        ).first()
        assert target is not None
        target_zone = db.get(Zone, target.zone_id)
        assert target_zone is not None
        other_zone = db.scalars(
            select(Zone).where(
                Zone.place_id == target_zone.place_id,
                Zone.id != target_zone.id,
            ).limit(1)
        ).first()
        if other_zone is None:
            pytest.skip("seed has only one zone for the target place")
        place_id = target_zone.place_id

    response = client.post(
        f"/api/v1/places/{place_id}/rule-leads",
        headers=signed_user,
        json={
            "animal_scope": target.animal_scope,
            "effect": "conditional",
            "current_rule_id": target.id,
            "zone_id": other_zone.id,
        },
    )
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "supersession_scope_mismatch"


def test_changed_rule_lead_rejects_noncurrent_target(client, signed_user):
    factory = get_session_factory()
    with factory() as db:
        target = db.scalars(
            select(AccessRule).where(AccessRule.status == "current").limit(1)
        ).first()
        assert target is not None
        place_id = target.place_id
        target.status = "superseded"
        db.commit()
        target_id = target.id

    try:
        response = client.post(
            f"/api/v1/places/{place_id}/rule-leads",
            headers=signed_user,
            json={
                "animal_scope": "dog",
                "effect": "allowed",
                "current_rule_id": target_id,
            },
        )
        assert response.status_code == 409, response.text
        assert response.json()["error"]["code"] == "supersession_target_not_current"
    finally:
        with factory() as db:
            restored = db.get(AccessRule, target_id)
            assert restored is not None
            restored.status = "current"
            db.commit()


def test_signage_only_rule_lead_enters_extraction_without_guessed_rule(client, signed_user):
    place_id = _place_id(client)
    me = client.get("/api/v1/auth/me", headers=signed_user)
    assert me.status_code == 200, me.text
    user_id = me.json()["id"]

    factory = get_session_factory()
    with factory() as db:
        media = MediaObject(
            owner_type="place",
            owner_id=place_id,
            created_by_user_id=user_id,
            purpose="signage_evidence",
            privacy_class="private",
            bucket="test",
            object_key=f"test/signage-{uuid.uuid4().hex}.png",
            mime_type="image/png",
            byte_size=68,
            sha256=uuid.uuid4().hex + uuid.uuid4().hex,
            original_filename="signage.png",
            upload_status="stored",
            moderation_status="pending",
        )
        db.add(media)
        db.commit()
        db.refresh(media)
        media_id = media.id

    response = client.post(
        f"/api/v1/places/{place_id}/rule-leads",
        headers=signed_user,
        json={
            "media_id": media_id,
            "raw_text": "规则牌照片；OCR 尚未完成人工核对。",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["review_status"] == "EXTRACTED"

    with factory() as db:
        candidate = db.get(RuleCandidate, response.json()["id"])
        assert candidate is not None
        assert candidate.media_id == media_id
        assert candidate.effect is None
        assert candidate.animal_scope is None
        assert candidate.action is None
        assert candidate.extraction_method == "user_upload"


def test_rule_lead_requires_authentication(client):
    place_id = _place_id(client)
    response = client.post(
        f"/api/v1/places/{place_id}/rule-leads",
        json={"animal_scope": "dog", "effect": "allowed"},
    )
    assert response.status_code == 401


def test_unified_contribution_activity_includes_rule_lead_and_correction(client, signed_user):
    place_id = _place_id(client)
    correction = client.post(
        "/api/v1/verifications",
        headers=signed_user,
        json={
            "place_id": place_id,
            "rule_id": None,
            "event_type": "place_correction",
            "result": "uncertain",
            "note": "地址楼层需要人工核验",
        },
    )
    assert correction.status_code == 201, correction.text

    response = client.get("/api/v1/me/contribution-activity", headers=signed_user)
    assert response.status_code == 200, response.text
    rows = response.json()
    assert any(row["kind"] == "rule_lead" and "规则" in row["summary"] for row in rows)
    assert any(
        row["kind"] == "verification" and row["summary"] == "场所信息纠错" for row in rows
    )
    assert all("place_name" in row for row in rows)
