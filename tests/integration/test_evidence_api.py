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


# ------------------------------------------------- v0.5 registry read surface
# The Admin v0.5 pages are read+write; every write endpoint needs a matching
# reader or an operator cannot review what they created. These tests pin the
# read surface so a future refactor cannot silently drop it.


def test_v05_registry_lists_are_reachable(client, moderator):
    """Every v0.5 registry resource exposes a paged GET for the Admin UI."""
    for path in (
        "/api/v1/admin/organizations",
        "/api/v1/admin/policy-templates",
        "/api/v1/admin/place-policy-bindings",
        "/api/v1/admin/amenities",
        "/api/v1/admin/entrances",
        "/api/v1/admin/access-paths",
        "/api/v1/admin/event-policies",
        "/api/v1/admin/data-licenses",
        "/api/v1/admin/coexistence-policies",
        "/api/v1/admin/monitors",
        "/api/v1/admin/candidates",
        "/api/v1/admin/observation-candidates",
        "/api/v1/admin/source-artifacts",
        "/api/v1/admin/evidence-bundles",
    ):
        r = client.get(path, headers=_auth(moderator))
        assert r.status_code == 200, f"{path} -> {r.status_code}"
        body = r.json()
        assert "items" in body and "total" in body, path


def test_organization_template_binding_round_trip(client, moderator):
    """create → list: the created objects come back through the readers."""
    org = client.post(
        "/api/v1/admin/organizations",
        json={"name": f"连锁-{uuid.uuid4().hex[:6]}", "kind": "chain"},
        headers=_auth(moderator),
    )
    assert org.status_code == 201, org.text
    org_id = org.json()["id"]
    assert any(
        o["id"] == org_id
        for o in client.get("/api/v1/admin/organizations", headers=_auth(moderator)).json()["items"]
    )

    tpl = client.post(
        "/api/v1/admin/policy-templates",
        json={
            "organization_id": org_id,
            "name": "标准门店政策",
            "venue_scope": "indoor",
            "rules": [
                {
                    "animal_scope": "dog",
                    "action": "enter",
                    "effect": "prohibited",
                    "conditions": None,
                }
            ],
        },
        headers=_auth(moderator),
    )
    assert tpl.status_code == 201, tpl.text
    tpl_id = tpl.json()["id"]

    templates = client.get(
        "/api/v1/admin/policy-templates",
        params={"organization_id": org_id},
        headers=_auth(moderator),
    ).json()["items"]
    mine = [t for t in templates if t["id"] == tpl_id]
    assert mine, "新建模板未出现在列表中"
    assert mine[0]["rule_count"] == 1
    # template rules are layer-locked to OPERATOR_POLICY
    assert mine[0]["rules"][0]["rule_layer"] == "OPERATOR_POLICY"

    place_id = _new_place(client, moderator)
    bind = client.post(
        "/api/v1/admin/place-policy-bindings",
        json={"place_id": place_id, "template_id": tpl_id},
        headers=_auth(moderator),
    )
    assert bind.status_code == 201, bind.text
    bindings = client.get(
        "/api/v1/admin/place-policy-bindings",
        params={"place_id": place_id},
        headers=_auth(moderator),
    ).json()["items"]
    assert any(b["id"] == bind.json()["id"] and b["is_active"] for b in bindings)


def test_event_policy_effectiveness_flag_is_computed(client, moderator):
    """is_effective_now reflects the caller's clock, not a stored column."""
    from datetime import UTC, datetime, timedelta

    place_id = _new_place(client, moderator)
    src = _new_source(client, moderator)
    now = datetime.now(UTC)
    created = client.post(
        "/api/v1/admin/event-policies",
        json={
            "place_id": place_id,
            "name": f"展会管控-{uuid.uuid4().hex[:6]}",
            "animal_scope": "dog",
            "action": "enter",
            "effect": "prohibited",
            "effective_from": (now - timedelta(hours=1)).isoformat(),
            "effective_to": (now + timedelta(hours=1)).isoformat(),
            "source_id": src,
        },
        headers=_auth(moderator),
    )
    assert created.status_code == 201, created.text
    ev_id = created.json()["id"]

    rows = client.get(
        "/api/v1/admin/event-policies",
        params={"place_id": place_id},
        headers=_auth(moderator),
    ).json()["items"]
    mine = [e for e in rows if e["id"] == ev_id]
    assert mine and mine[0]["is_effective_now"] is True


def test_active_only_binding_filter_excludes_superseded(client, moderator):
    """Re-binding deactivates the previous binding but keeps the history."""
    place_id = _new_place(client, moderator)
    org_id = client.post(
        "/api/v1/admin/organizations",
        json={"name": f"组织-{uuid.uuid4().hex[:6]}", "kind": "brand"},
        headers=_auth(moderator),
    ).json()["id"]
    tpl_id = client.post(
        "/api/v1/admin/policy-templates",
        json={"organization_id": org_id, "name": "T1", "rules": []},
        headers=_auth(moderator),
    ).json()["id"]

    first = client.post(
        "/api/v1/admin/place-policy-bindings",
        json={"place_id": place_id, "template_id": tpl_id},
        headers=_auth(moderator),
    )
    assert first.status_code == 201
    second = client.post(
        "/api/v1/admin/place-policy-bindings",
        json={"place_id": place_id, "template_id": tpl_id},
        headers=_auth(moderator),
    )
    assert second.status_code == 201

    active = client.get(
        "/api/v1/admin/place-policy-bindings",
        params={"place_id": place_id, "active_only": True},
        headers=_auth(moderator),
    ).json()["items"]
    assert [b["id"] for b in active] == [second.json()["id"]]
    # history is preserved, not deleted
    everything = client.get(
        "/api/v1/admin/place-policy-bindings",
        params={"place_id": place_id},
        headers=_auth(moderator),
    ).json()["items"]
    assert len(everything) >= 2


def test_read_endpoints_require_moderator(client, moderator):
    """The read surface is privileged: an ordinary user must be rejected."""
    email = f"plain-{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"display_name": "普通用户", "email": email, "password": "passw0rd123"},
    )
    tok = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "passw0rd123"}
    ).json()["access_token"]
    r = client.get("/api/v1/admin/organizations", headers=_auth(tok))
    assert r.status_code in (401, 403)
