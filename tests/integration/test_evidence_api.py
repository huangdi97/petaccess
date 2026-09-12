"""Evidence chain over the real API (brief §5).

Verifies the HTTP surface and, critically, that the rule/observation boundary
survives at the API layer: an observation candidate can be approved and
published while the normative AccessRule set stays untouched.
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
    """Returns (token, user_id)."""
    email = f"evmod-{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"display_name": "证据复核员", "email": email, "password": "passw0rd123"},
    )
    from app.db.session import get_session_factory
    from app.models import User

    s = get_session_factory()()
    u = s.query(User).filter(User.email == email).one()
    u.role = "admin"
    uid = u.id
    s.commit()
    s.close()
    tok = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "passw0rd123"}
    ).json()["access_token"]
    return tok, uid


def _auth(actor):
    tok = actor[0] if isinstance(actor, tuple) else actor
    return {"Authorization": f"Bearer {tok}"}


def _new_place(client, tok) -> str:
    r = client.post(
        "/api/v1/places",
        json={
            "canonical_name": f"证据测试场所-{uuid.uuid4().hex[:6]}",
            "place_type": "cafe",
            "location_wkt": "POINT(121.471 31.231)",
        },
        headers=_auth(tok),
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _new_source(client, tok) -> str:
    r = client.post(
        "/api/v1/sources",
        json={
            "source_type": "official_operator_policy",
            "issuer": f"证据来源-{uuid.uuid4().hex[:6]}",
            "directness": "direct",
        },
        headers=_auth(tok),
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_artifact_bundle_chain_over_api(client, moderator):
    """官方来源 → artifact → bundle → 可追溯原文与许可元数据。"""
    src = _new_source(client, moderator)

    art = client.post(
        "/api/v1/admin/source-artifacts",
        json={
            "source_id": src,
            "collector_type": "OfficialWebCollector",
            "artifact_type": "url",
            "source_url": "https://gov.example/pet-rule",
            "content_hash": "d" * 64,
            "publisher_type": "government",
            "captured_excerpt": "公园内禁止携带宠物进入草坪",
        },
        headers=_auth(moderator),
    )
    assert art.status_code == 201, art.text
    art_id = art.json()["id"]
    # collector → platform 映射生效
    assert art.json()["source_platform"] == "official_web"

    bundle = client.post(
        "/api/v1/admin/evidence-bundles",
        json={
            "artifact_id": art_id,
            "quoted_fragment": "公园内禁止携带宠物进入草坪",
            "extracted_fragment": "禁止进入草坪",
            "extraction_method": "manual",
        },
        headers=_auth(moderator),
    )
    assert bundle.status_code == 201, bundle.text
    b = bundle.json()
    assert b["artifact_id"] == art_id
    assert b["evidence_class"] == "original"
    assert b["quoted_fragment"] == "公园内禁止携带宠物进入草坪"
    # 许可状态被固化
    assert b["license_metadata"]["redistribution_allowed"] is False


def test_derived_bundle_requires_origin_over_api(client, moderator):
    src = _new_source(client, moderator)
    art = client.post(
        "/api/v1/admin/source-artifacts",
        json={
            "source_id": src,
            "collector_type": "OnsiteEvidenceCollector",
            "artifact_type": "signage_photo",
            "captured_excerpt": "禁止宠物",
        },
        headers=_auth(moderator),
    ).json()

    bad = client.post(
        "/api/v1/admin/evidence-bundles",
        json={
            "artifact_id": art["id"],
            "evidence_class": "derived",
            "extraction_method": "ocr",
        },
        headers=_auth(moderator),
    )
    assert bad.status_code == 400, bad.text

    original = client.post(
        "/api/v1/admin/evidence-bundles",
        json={
            "artifact_id": art["id"],
            "quoted_fragment": "禁止宠物",
        },
        headers=_auth(moderator),
    ).json()

    good = client.post(
        "/api/v1/admin/evidence-bundles",
        json={
            "artifact_id": art["id"],
            "evidence_class": "derived",
            "derived_from_bundle_id": original["id"],
            "extracted_fragment": "OCR: 禁止宠物",
            "extraction_method": "ocr",
        },
        headers=_auth(moderator),
    )
    assert good.status_code == 201, good.text
    assert good.json()["derived_from_bundle_id"] == original["id"]


def test_classify_endpoint_routes_lanes(client, moderator):
    r1 = client.post(
        "/api/v1/admin/evidence/classify",
        json={"text": "本店规定禁止携带宠物"},
        headers=_auth(moderator),
    )
    assert r1.status_code == 200 and r1.json()["kind"] == "rule"

    r2 = client.post(
        "/api/v1/admin/evidence/classify",
        json={"text": "我看到有人把狗放在座位上"},
        headers=_auth(moderator),
    )
    assert r2.status_code == 200 and r2.json()["kind"] == "observation"


def test_observation_candidate_lifecycle_never_writes_a_rule(client, moderator):
    """观察候选走完全流程后，规范规则集必须完全不受影响。"""
    src = _new_source(client, moderator)
    place_id = _new_place(client, moderator)

    art = client.post(
        "/api/v1/admin/source-artifacts",
        json={
            "source_id": src,
            "collector_type": "ManualVerificationCollector",
            "artifact_type": "phone_note",
            "captured_excerpt": "店员说有人把狗放在椅子上",
        },
        headers=_auth(moderator),
    ).json()

    bundle = client.post(
        "/api/v1/admin/evidence-bundles",
        json={
            "artifact_id": art["id"],
            "quoted_fragment": "有人把狗放在椅子上",
        },
        headers=_auth(moderator),
    ).json()

    before = client.post(
        f"/api/v1/places/{place_id}/effective-rules", json={"animal": "dog"}
    ).json()

    cand = client.post(
        "/api/v1/admin/observation-candidates",
        json={
            "evidence_bundle_id": bundle["id"],
            "place_id": place_id,
            "animal_scope": "ordinary_pet",
            "observed_action": "on_seat",
            "spatial_context": "customer_seat",
            "raw_text": "有人把狗放在椅子上",
        },
        headers=_auth(moderator),
    )
    assert cand.status_code == 201, cand.text
    cand_id = cand.json()["id"]
    assert cand.json()["review_status"] == "DISCOVERED"

    # walk the observation lane to PUBLISHED
    for target in ("EXTRACTED", "PLACE_MATCH_PENDING", "REVIEW_PENDING", "APPROVED", "PUBLISHED"):
        resp = client.post(
            f"/api/v1/admin/observation-candidates/{cand_id}/transition",
            json={"target": target, "note": "观察复核"},
            headers=_auth(moderator),
        )
        assert resp.status_code == 200, resp.text
    assert resp.json()["review_status"] == "PUBLISHED"

    # the normative rule set must be byte-identical
    after = client.post(f"/api/v1/places/{place_id}/effective-rules", json={"animal": "dog"}).json()
    assert after == before, "observation 发布不得改变 normative resolver 结果"

    from sqlalchemy import func, select

    from app.db.session import get_session_factory
    from app.models import AccessRule

    s = get_session_factory()()
    count = (
        s.scalar(
            select(func.count()).select_from(AccessRule).where(AccessRule.place_id == place_id)
        )
        or 0
    )
    s.close()
    assert count == 0, "观察通道不得产生任何 AccessRule"


def test_observation_transition_guard_rejects_skips(client, moderator):
    """状态机不得跳跃，PUBLISHED 后不得再改。"""
    src = _new_source(client, moderator)
    art = client.post(
        "/api/v1/admin/source-artifacts",
        json={
            "source_id": src,
            "collector_type": "UserLinkCollector",
            "artifact_type": "url",
            "source_url": "https://example.com/p",
            "captured_excerpt": "看到狗在桌面",
        },
        headers=_auth(moderator),
    ).json()
    bundle = client.post(
        "/api/v1/admin/evidence-bundles",
        json={
            "artifact_id": art["id"],
            "quoted_fragment": "看到狗在桌面",
        },
        headers=_auth(moderator),
    ).json()
    cand = client.post(
        "/api/v1/admin/observation-candidates",
        json={
            "evidence_bundle_id": bundle["id"],
            "observed_action": "on_table",
        },
        headers=_auth(moderator),
    ).json()

    # DISCOVERED → PUBLISHED is illegal
    skip = client.post(
        f"/api/v1/admin/observation-candidates/{cand['id']}/transition",
        json={"target": "PUBLISHED"},
        headers=_auth(moderator),
    )
    assert skip.status_code == 400, skip.text


def test_artifact_listing_and_audit_trail(client, moderator):
    """证据写入必须有审计记录。"""
    src = _new_source(client, moderator)
    art = client.post(
        "/api/v1/admin/source-artifacts",
        json={
            "source_id": src,
            "collector_type": "OperatorSiteCollector",
            "artifact_type": "url",
            "source_url": "https://brand.example/policy",
            "captured_excerpt": "本店允许小型犬入内",
        },
        headers=_auth(moderator),
    )
    assert art.status_code == 201
    art_id = art.json()["id"]

    listing = client.get("/api/v1/admin/source-artifacts", headers=_auth(moderator))
    assert listing.status_code == 200
    assert any(item["id"] == art_id for item in listing.json()["items"])

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.models import AuditLog

    s = get_session_factory()()
    audits = s.scalars(select(AuditLog).where(AuditLog.target_id == art_id)).all()
    s.close()
    assert any(a.action == "artifact.create" for a in audits)
