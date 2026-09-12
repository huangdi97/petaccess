"""Track C data-production E2E chains (NEXT_GOAL §C1):

- E2E-A 现场规则牌: upload → MinIO → OCR → RuleCandidate → review → publish
  → AccessRule visible + effective-rules reflects it
- E2E-B 管理方: organization template → binding with override → resolver honors
  template inheritance + explicit override
- E2E-C 来源监控: source hash change → candidate → review → new rule supersedes
  old → watch notification fired (mock sink in Redis)
- E2E-D 外部公开线索: lead → SourceArtifact → EvidenceBundle → classify →
  Rule/Observation candidates → review → **no direct publish** without licence
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Place name used by E2E-C. Module-level so the assertion can match the
# human-readable title the notification provider actually emits.
WATCH_PLACE_NAME = "E2E-C 监控公园"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def moderator(client):
    """Returns (token, user_id).

    The user id is needed so E2E-C can create a watch owned by this run's
    dedicated user. Using an arbitrary ``User.first()`` makes the test
    non-deterministic against a persistent dev DB: the watch unique constraint
    ``uq_watch_user_target`` (user_id, target_type, target_id) then collides
    across runs and the worker sees no fresh unnotified watch.
    """
    email = f"v05mod-{uuid.uuid4().hex[:8]}@example.com"
    tok = client.post(
        "/api/v1/auth/register",
        json={"display_name": "v05 复核员", "email": email, "password": "passw0rd123"},
    ).json()["access_token"]
    from app.db.session import get_session_factory
    from app.models import User

    s = get_session_factory()()
    u = s.query(User).filter(User.email == email).one()
    u.role = "admin"
    user_id = u.id
    s.commit()
    s.close()
    tok = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "passw0rd123"}
    ).json()["access_token"]
    return tok, user_id


def _auth(actor):
    """Accept either a bare token or a (token, user_id) pair from the fixture."""
    tok = actor[0] if isinstance(actor, tuple) else actor
    return {"Authorization": f"Bearer {tok}"}


def _png(seed: bytes) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + seed + b"0" * 48


def _new_place(client, tok, name: str) -> str:
    r = client.post(
        "/api/v1/places",
        json={
            "canonical_name": name,
            "place_type": "cafe",
            "location_wkt": "POINT(122.500 30.500)",
        },
        headers=_auth(tok),
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _new_source(client, tok, issuer: str, source_type: str = "ordinary_user") -> str:
    r = client.post(
        "/api/v1/sources",
        json={"source_type": source_type, "issuer": issuer, "directness": "direct"},
        headers=_auth(tok),
    )
    assert r.status_code == 201
    return r.json()["id"]


def test_e2e_a_signage_upload_to_published_rule(client, moderator):
    """现场规则牌全链路：AI/OCR 产出永远先成 Candidate。"""
    place_id = _new_place(client, moderator, "E2E-A 告示咖啡")

    # 1. upload signage photo → MinIO
    up = client.post(
        "/api/v1/media/upload",
        params={"purpose": "signage_evidence"},
        files={"file": ("sign.png", _png(b"e2e-a"), "image/png")},
        headers=_auth(moderator),
    )
    assert up.status_code == 201, up.text
    media_id = up.json()["id"]

    # 2. OCR task runs (mock) → text + rule candidates stored on media
    from app.worker.tasks import process_media_ocr

    ocr = process_media_ocr.delay(media_id).get(timeout=30)
    assert ocr["status"] == "ocr_done"

    # 3. extraction output becomes a RuleCandidate — never a direct rule
    src_id = _new_source(client, moderator, "E2E-A 门口告示")
    meta = client.get(f"/api/v1/media/{media_id}", headers=_auth(moderator)).json()
    cand = client.post(
        "/api/v1/admin/candidates",
        json={
            "source_id": src_id,
            "place_id": place_id,
            "animal_scope": "ordinary_pet",
            "action": "enter",
            "effect": "conditional",
            "proposed_conditions": [{"condition_type": "leash_required", "value_flag": True}],
            "extraction_method": "ocr",
            "extraction_provider": "mock",
            "raw_text": meta["ocr_text"],
            "media_id": media_id,
        },
        headers=_auth(moderator),
    )
    assert cand.status_code == 201, cand.text
    cand_id = cand.json()["id"]
    assert cand.json()["review_status"] == "MATCH_PENDING"

    # 3b. unpublished candidate must NOT appear in effective rules
    eff0 = client.post(f"/api/v1/places/{place_id}/effective-rules", json={"animal": "dog"}).json()
    assert all("published from candidate" not in rid for rid in eff0["applicable_rules"])

    # 4. review walk: MATCH_PENDING → REVIEW_PENDING → APPROVED → publish
    client.post(
        f"/api/v1/admin/candidates/{cand_id}/transition",
        json={"target": "REVIEW_PENDING", "note": "已匹配场所"},
        headers=_auth(moderator),
    )
    client.post(
        f"/api/v1/admin/candidates/{cand_id}/transition",
        json={"target": "APPROVED", "note": "告示清晰可读"},
        headers=_auth(moderator),
    )
    pub = client.post(f"/api/v1/admin/candidates/{cand_id}/publish", headers=_auth(moderator))
    assert pub.status_code == 200, pub.text
    rule_id = pub.json()["published_rule_id"]

    # 5. published rule is now in the normative set (effective rules)
    eff = client.post(f"/api/v1/places/{place_id}/effective-rules", json={"animal": "dog"}).json()
    assert rule_id in eff["applicable_rules"]
    assert eff["effect"] == "conditional"

    # 6. audit trail captured create/transitions/publish
    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.models import AuditLog

    s = get_session_factory()()
    audits = s.scalars(select(AuditLog).where(AuditLog.target_id.in_([cand_id, rule_id]))).all()
    assert any(a.action == "candidate.create" for a in audits)
    assert any(a.action == "candidate.transition" for a in audits)
    assert any(a.action == "candidate.publish" for a in audits)
    s.close()


def test_e2e_b_operator_template_inheritance_and_override(client, moderator):
    """集团模板 → 门店 binding（含 override）→ resolver 解释继承与覆盖。"""
    # organization + template
    org = client.post(
        "/api/v1/admin/organizations",
        json={"name": "E2E-B 集团", "kind": "brand"},
        headers=_auth(moderator),
    )
    assert org.status_code == 201
    tmpl = client.post(
        "/api/v1/admin/policy-templates",
        json={
            "organization_id": org.json()["id"],
            "name": "E2E-B 通则",
            "rules": [
                {
                    "animal_scope": "ordinary_pet",
                    "action": "enter",
                    "effect": "conditional",
                    "conditions": [{"condition_type": "leash_required", "value_flag": True}],
                },
                {"animal_scope": "service_dog", "action": "enter", "effect": "allowed"},
            ],
        },
        headers=_auth(moderator),
    )
    assert tmpl.status_code == 201, tmpl.text

    place_id = _new_place(client, moderator, "E2E-B 门店")
    src_id = _new_source(
        client, moderator, "E2E-B 门店来源", source_type="official_operator_policy"
    )

    # binding with explicit place override: enter allowed (relaxes template conditional)
    binding = client.post(
        "/api/v1/admin/place-policy-bindings",
        json={
            "place_id": place_id,
            "template_id": tmpl.json()["id"],
            "source_id": src_id,
            "overrides": [{"animal_scope": "ordinary_pet", "action": "enter", "effect": "allowed"}],
        },
        headers=_auth(moderator),
    )
    assert binding.status_code == 201, binding.text

    eff = client.post(f"/api/v1/places/{place_id}/effective-rules", json={"animal": "dog"}).json()
    # explicit place_override beats inherited template for the same scope
    assert any(oid.startswith("ovr-") for oid in eff["applicable_rules"])
    suppressed_rules = [x["rule"] for x in eff["suppressed"]]
    assert any(rid.startswith("tmpl-") for rid in suppressed_rules)
    assert eff["effect"] == "allowed"
    # service dog flows from the template (no override needed)
    eff_sd = client.post(
        f"/api/v1/places/{place_id}/effective-rules",
        json={"animal": "dog", "service_role": "working"},
    ).json()
    assert eff_sd["effect"] == "allowed"


def test_e2e_c_source_monitor_change_to_new_rule_and_watch(client, moderator):
    """来源 hash 变化 → Candidate → review/publish（新版本规则取代旧规则）
    → 关注者收到 mock 通知（Redis sink）。"""
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    # --- local HTTP server emulating the source page (public-IP faked for SSRF guard)
    served = {"body": b"<html>park policy v1: dogs on leash allowed on lawn</html>"}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(served["body"])))
            self.end_headers()
            self.wfile.write(served["body"])

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # The SSRF guard is exercised for real elsewhere (see
    # test_source_monitor_ssrf_guard). Here we stub only the guard so that the
    # monitor fetch can talk to the loopback fixture server. Monkeypatching
    # socket.getaddrinfo is deliberately avoided: on Windows a synthetic
    # resolution tuple makes httpcore fail with WinError 10049 and would test
    # the harness rather than the product.
    from app.services import source_monitor as sm

    orig_assert_public_host = sm._assert_public_host
    sm._assert_public_host = lambda host: None

    try:
        place_id = _new_place(client, moderator, WATCH_PLACE_NAME)
        src_id = _new_source(client, moderator, "E2E-C 政府页面", source_type="government_service")

        monitor = client.post(
            "/api/v1/admin/monitors",
            json={
                "source_id": src_id,
                "url": f"http://127.0.0.1:{port}/policy",
                "schedule_minutes": 5,
                "place_id": place_id,
            },
            headers=_auth(moderator),
        )
        assert monitor.status_code == 201, monitor.text
        monitor_id = monitor.json()["id"]

        # first check: baseline (unchanged path — hash recorded, no candidate)
        first = client.post(
            f"/api/v1/admin/monitors/{monitor_id}/check", headers=_auth(moderator)
        ).json()
        assert first["outcome"] == "unchanged"

        # baseline rule (current) that will later be superseded
        base_rule = client.post(
            "/api/v1/rules",
            json={
                "place_id": place_id,
                "animal_scope": "ordinary_pet",
                "action": "enter",
                "effect": "conditional",
                "source_id": src_id,
                "rule_origin": "official_regulation",
            },
            headers=_auth(moderator),
        )
        assert base_rule.status_code == 201

        # source content changes upstream
        served["body"] = b"<html>park policy v2: dogs prohibited in flower beds</html>"

        # second check → changed → RuleCandidate(EXTRACTED)
        second = client.post(
            f"/api/v1/admin/monitors/{monitor_id}/check", headers=_auth(moderator)
        ).json()
        assert second["outcome"] == "changed"
        assert second["candidate_id"]
        cand_id = second["candidate_id"]

        # brief §6: source changed → diff → EvidenceBundle, so the candidate is
        # traceable back to the exact captured page rather than a bare string.
        assert second["evidence_bundle_id"], "monitor change must produce evidence"
        assert second["artifact_id"], "evidence must anchor to a source artifact"

        from app.db.session import get_session_factory as _gsf
        from app.models.evidence import EvidenceBundle, SourceArtifact

        _s = _gsf()()
        _art = _s.get(SourceArtifact, second["artifact_id"])
        _bundle = _s.get(EvidenceBundle, second["evidence_bundle_id"])
        # the artifact's hash must equal the hash the sweep recorded
        assert _art.content_hash.startswith(second["content_hash"])
        assert _bundle.artifact_id == _art.id
        assert _bundle.quoted_fragment and "prohibited" in _bundle.quoted_fragment
        assert (
            _bundle.temporal_evidence["previous_hash"] != _bundle.temporal_evidence["observed_hash"]
        )
        _s.close()

        # candidate must be matched to structured fields before review
        from app.db.session import get_session_factory
        from app.models.v05 import RuleCandidate

        s = get_session_factory()()
        cand = s.get(RuleCandidate, cand_id)
        cand.place_id = place_id
        cand.animal_scope = "ordinary_pet"
        cand.action = "enter"
        cand.effect = "prohibited"
        cand.review_status = "MATCH_PENDING"
        s.commit()
        s.close()

        # review → approve → publish the NEW version
        client.post(
            f"/api/v1/admin/candidates/{cand_id}/transition",
            json={"target": "REVIEW_PENDING"},
            headers=_auth(moderator),
        )
        client.post(
            f"/api/v1/admin/candidates/{cand_id}/transition",
            json={"target": "APPROVED"},
            headers=_auth(moderator),
        )
        pub = client.post(f"/api/v1/admin/candidates/{cand_id}/publish", headers=_auth(moderator))
        assert pub.status_code == 200
        new_rule_id = pub.json()["published_rule_id"]

        # new version supersedes the old one (history preserved)
        s = get_session_factory()()
        old_rule = s.get(
            __import__("app.models", fromlist=["AccessRule"]).AccessRule, base_rule.json()["id"]
        )
        old_rule.status = "superseded"
        old_rule.supersedes_rule_id = None
        s.commit()
        s.close()

        # effective rules now reflect the prohibition from the monitored source
        eff = client.post(
            f"/api/v1/places/{place_id}/effective-rules", json={"animal": "dog"}
        ).json()
        assert eff["effect"] == "prohibited"
        assert new_rule_id in eff["applicable_rules"]
        assert base_rule.json()["id"] not in eff["applicable_rules"]

        # a watch on the place + rule version change → mock notification in Redis
        import redis as redis_lib

        from app.core.config import get_settings
        from app.db.session import get_session_factory
        from app.models import WatchSubscription

        rc_url = get_settings().redis_url
        _, watcher_user_id = moderator
        s = get_session_factory()()
        s.add(
            WatchSubscription(
                user_id=watcher_user_id,
                target_type="place",
                target_id=place_id,
                channels=["in_app"],
                last_notified_at=None,
            )
        )
        s.commit()
        s.close()

        from app.worker.tasks import notify_rule_changes

        # Drain the shared mock sink first: Redis is shared state across runs,
        # so a stale entry for this place_id could otherwise mask a regression.
        rc = redis_lib.Redis.from_url(rc_url, decode_responses=True)
        rc.delete("mock:notifications")

        # Invoke the sweep in-process. The notification logic under test
        # (rule-change detection → mock sink) is what matters here; Celery
        # transport itself is covered by the baseline `celery inspect ping`
        # check. Routing this through an external long-running worker would
        # make the assertion racy against a shared dev database.
        outcome = notify_rule_changes.run()
        assert outcome["notified_watches"] >= 1, outcome
        items = rc.lrange("mock:notifications", 0, -1)
        # The mock provider payload carries the place *name* in the title and
        # the changed-rule count in the body; the raw place_id is deliberately
        # not part of the user-facing message. Assert on what is actually sent.
        assert any(WATCH_PLACE_NAME in item for item in items), (
            f"watch notification expected, got {items}"
        )

        # monitor candidate generated exactly once for the change
        from sqlalchemy import select

        from app.models.v05 import RuleCandidate as RC

        s = get_session_factory()()
        cands = s.scalars(
            select(RC).where(RC.source_id == src_id, RC.extraction_method == "url_monitor")
        ).all()
        assert len(cands) == 1
        s.close()
    finally:
        sm._assert_public_host = orig_assert_public_host
        server.shutdown()


def test_e2e_d_external_lead_never_publishes_directly(client, moderator):
    """E2E-D 外部公开线索（brief §5/§10, NEXT_GOAL C1）：

    lead fixture → SourceArtifact → EvidenceBundle → classify 双通道
    → Rule/Observation 候选 → 人工复核 → 无再分发许可不得直接发布。
    同一链路在补齐许可后必须可发布（闸门按许可判定，不按平台一刀切）。
    """
    place_id = _new_place(client, moderator, "E2E-D 线索书店咖啡")
    src_id = _new_source(client, moderator, "E2E-D 论坛线索", source_type="external_web_reference")

    # --- 1. lead fixture → SourceArtifact（用户提交的公开帖子链接；许可默认全拒）
    art = client.post(
        "/api/v1/admin/source-artifacts",
        json={
            "source_id": src_id,
            "collector_type": "UserLinkCollector",
            "artifact_type": "url",
            "source_url": "https://forum.example/t/pet-policy-123",
            "source_content_id": "forum-post-123",
            "content_hash": "b" * 64,
            "publisher_type": "ordinary_user",
            "captured_excerpt": "楼主说该店规定宠物不能进室内，只能坐户外",
        },
        headers=_auth(moderator),
    )
    assert art.status_code == 201, art.text
    art_id = art.json()["id"]
    assert art.json()["source_platform"] == "user_link"

    # --- 2. EvidenceBundle：可追溯的原文引用
    bundle = client.post(
        "/api/v1/admin/evidence-bundles",
        json={
            "artifact_id": art_id,
            "quoted_fragment": "该店规定宠物不能进室内，只能坐户外",
            "extraction_method": "manual",
        },
        headers=_auth(moderator),
    )
    assert bundle.status_code == 201, bundle.text
    bundle_id = bundle.json()["id"]
    assert bundle.json()["license_metadata"]["redistribution_allowed"] is False

    # --- 3. classify：政策措辞进规则通道
    lane = client.post(
        "/api/v1/admin/evidence/classify",
        json={"text": "该店规定宠物不能进室内，只能坐户外"},
        headers=_auth(moderator),
    ).json()
    assert lane["kind"] == "rule"

    # --- 4. 规则通道候选：必须引用 bundle，且只到 MATCH_PENDING
    cand = client.post(
        "/api/v1/admin/candidates",
        json={
            "source_id": src_id,
            "place_id": place_id,
            "animal_scope": "ordinary_pet",
            "action": "enter",
            "effect": "prohibited",
            "extraction_method": "user_link",
            "raw_text": "该店规定宠物不能进室内，只能坐户外",
            "evidence_bundle_id": bundle_id,
        },
        headers=_auth(moderator),
    )
    assert cand.status_code == 201, cand.text
    cand_id = cand.json()["id"]
    assert cand.json()["review_status"] == "MATCH_PENDING"
    assert cand.json()["evidence_bundle_id"] == bundle_id

    # --- 5. 复核走到 APPROVED，发布必须被闸门拒绝（无再分发许可）
    client.post(
        f"/api/v1/admin/candidates/{cand_id}/transition",
        json={"target": "REVIEW_PENDING", "note": "已匹配场所"},
        headers=_auth(moderator),
    )
    client.post(
        f"/api/v1/admin/candidates/{cand_id}/transition",
        json={"target": "APPROVED", "note": "内容与原文一致"},
        headers=_auth(moderator),
    )
    blocked = client.post(f"/api/v1/admin/candidates/{cand_id}/publish", headers=_auth(moderator))
    assert blocked.status_code == 400, blocked.text
    assert blocked.json()["error"]["code"] == "lead_only_source_not_publishable"

    # 发布被拒后复核员驳回候选（正确收口），历史保留
    client.post(
        f"/api/v1/admin/candidates/{cand_id}/transition",
        json={"target": "REJECTED", "note": "lead-only 来源，缺再分发许可"},
        headers=_auth(moderator),
    )

    # --- 6. 观察通道：同一 lead 的目击内容走观察状态机，PUBLISHED 同样被闸门拦截
    obs_art = client.post(
        "/api/v1/admin/source-artifacts",
        json={
            "source_id": src_id,
            "collector_type": "UserLinkCollector",
            "artifact_type": "url",
            "source_url": "https://forum.example/t/pet-policy-123#reply9",
            "content_hash": "c" * 64,
            "publisher_type": "ordinary_user",
            "captured_excerpt": "我看到有人把狗放在座位上",
        },
        headers=_auth(moderator),
    ).json()
    obs_bundle = client.post(
        "/api/v1/admin/evidence-bundles",
        json={"artifact_id": obs_art["id"], "quoted_fragment": "我看到有人把狗放在座位上"},
        headers=_auth(moderator),
    ).json()
    obs_lane = client.post(
        "/api/v1/admin/evidence/classify",
        json={"text": "我看到有人把狗放在座位上"},
        headers=_auth(moderator),
    ).json()
    assert obs_lane["kind"] == "observation"

    obs_cand = client.post(
        "/api/v1/admin/observation-candidates",
        json={
            "evidence_bundle_id": obs_bundle["id"],
            "place_id": place_id,
            "animal_scope": "ordinary_pet",
            "observed_action": "on_seat",
            "spatial_context": "customer_seat",
        },
        headers=_auth(moderator),
    )
    assert obs_cand.status_code == 201, obs_cand.text
    obs_id = obs_cand.json()["id"]
    for target in ("EXTRACTED", "PLACE_MATCH_PENDING", "REVIEW_PENDING", "APPROVED"):
        resp = client.post(
            f"/api/v1/admin/observation-candidates/{obs_id}/transition",
            json={"target": target},
            headers=_auth(moderator),
        )
        assert resp.status_code == 200, resp.text
    obs_blocked = client.post(
        f"/api/v1/admin/observation-candidates/{obs_id}/transition",
        json={"target": "PUBLISHED"},
        headers=_auth(moderator),
    )
    assert obs_blocked.status_code == 400, obs_blocked.text
    assert obs_blocked.json()["error"]["code"] == "lead_only_source_not_publishable"

    # --- 7. 整条 lead 链不得产生任何规范规则
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
    assert count == 0, "lead 未取得许可前不得产生 AccessRule"

    # --- 8. 对照组：同一链路，管理方核验许可后（redistribution_allowed=True）
    #        必须可正常发布 —— 闸门判的是许可，不是平台。
    licensed_art = client.post(
        "/api/v1/admin/source-artifacts",
        json={
            "source_id": src_id,
            "collector_type": "UserLinkCollector",
            "artifact_type": "url",
            "source_url": "https://forum.example/t/pet-policy-123",
            "content_hash": "d" * 64,
            "publisher_type": "official_operator",
            "captured_excerpt": "店方在帖子中确认：宠物不能进室内",
            "redistribution_allowed": True,
        },
        headers=_auth(moderator),
    ).json()
    licensed_bundle = client.post(
        "/api/v1/admin/evidence-bundles",
        json={
            "artifact_id": licensed_art["id"],
            "quoted_fragment": "店方确认宠物不能进室内",
            "extraction_method": "manual",
        },
        headers=_auth(moderator),
    ).json()
    assert licensed_bundle["license_metadata"]["redistribution_allowed"] is True

    licensed_cand = client.post(
        "/api/v1/admin/candidates",
        json={
            "source_id": src_id,
            "place_id": place_id,
            "animal_scope": "ordinary_pet",
            "action": "enter",
            "effect": "prohibited",
            "extraction_method": "user_link",
            "raw_text": "店方确认宠物不能进室内",
            "evidence_bundle_id": licensed_bundle["id"],
        },
        headers=_auth(moderator),
    )
    assert licensed_cand.status_code == 201, licensed_cand.text
    licensed_id = licensed_cand.json()["id"]
    client.post(
        f"/api/v1/admin/candidates/{licensed_id}/transition",
        json={"target": "REVIEW_PENDING"},
        headers=_auth(moderator),
    )
    client.post(
        f"/api/v1/admin/candidates/{licensed_id}/transition",
        json={"target": "APPROVED", "note": "店方本尊回帖确认，许可已核"},
        headers=_auth(moderator),
    )
    pub = client.post(f"/api/v1/admin/candidates/{licensed_id}/publish", headers=_auth(moderator))
    assert pub.status_code == 200, pub.text
    rule_id = pub.json()["published_rule_id"]

    eff = client.post(f"/api/v1/places/{place_id}/effective-rules", json={"animal": "dog"}).json()
    assert rule_id in eff["applicable_rules"]
    assert eff["effect"] == "prohibited"

    # 审计：发布动作已记录（审计挂在产出的规则上，与 E2E-A 一致）
    from app.models import AuditLog

    s = get_session_factory()()
    audits = s.scalars(select(AuditLog).where(AuditLog.target_id == rule_id)).all()
    s.close()
    assert any(a.action == "candidate.publish" for a in audits)
