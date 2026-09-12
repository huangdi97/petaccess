"""Evidence-First tests (brief §5, §6).

Covers: collector abstraction, artifact→bundle chain, original vs derived,
rule/observation lane separation, lead-only publication block, and the
data-integrity invariants the brief calls out explicitly.
"""

import uuid
from datetime import UTC, datetime

import pytest

from app.core.errors import ApiError
from app.models.evidence import (
    OBSERVATION_CANDIDATE_TRANSITIONS,
    ClaimKind,
    CollectorType,
    EvidenceBundle,
    EvidenceClass,
    ObservationCandidate,
    SourceArtifact,
    SourcePlatform,
)
from app.services import evidence_service as ev

# ------------------------------------------------------------------ helpers


def _uniq(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ------------------------------------------------------- collector contracts


def test_all_collectors_declare_platform_and_capability():
    """Every reserved collector is registered and self-describes."""
    assert set(ev.COLLECTORS) == set(CollectorType.ALL)
    for name, cls in ev.COLLECTORS.items():
        inst = cls()
        assert inst.collector_type == name
        assert inst.source_platform in SourcePlatform.ALL


def test_lead_only_platforms_are_exactly_the_social_tier():
    """社交平台必须被归类为 lead-only，官方/运营方不得是。"""
    for name in (
        CollectorType.SOCIAL_LEAD,
        CollectorType.SEARCH_DISCOVERY,
        CollectorType.USER_LINK,
    ):
        assert ev.COLLECTORS[name]().is_lead_only is True
    for name in (
        CollectorType.OFFICIAL_WEB,
        CollectorType.OPERATOR_SITE,
        CollectorType.ONSITE_EVIDENCE,
    ):
        assert ev.COLLECTORS[name]().is_lead_only is False


def test_official_collectors_are_implementable_without_credentials():
    """没有 Key 也必须能实现官方/运营方/人工/现场采集。"""
    for name in CollectorType.IMPLEMENTED_IN_V05:
        assert ev.COLLECTORS[name]().implemented_in_v05 is True
    # social lead 需要平台许可，v0.5 不得假装已实现
    assert ev.SocialLeadCollector().implemented_in_v05 is False
    assert ev.SearchDiscoveryCollector().implemented_in_v05 is False


def test_official_web_collector_produces_artifact_shape():
    art = ev.OfficialWebCollector().collect(
        url="https://example.gov/policy",
        content_hash="a" * 64,
        excerpt="养犬管理规定",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert art.source_platform == SourcePlatform.OFFICIAL_WEB
    assert art.publisher_type == "government"
    assert art.display_allowed is True
    # 政府页面不自动等于可再分发
    assert art.redistribution_allowed is False


def test_social_collector_denies_storage_by_default():
    """公开可见 ≠ 允许批量抓取/长期存储。"""
    art = ev.SocialLeadCollector().collect(url="https://xhs.example/post/1", excerpt="店内可带狗")
    assert art.storage_allowed is False
    assert art.display_allowed is False
    assert art.redistribution_allowed is False


# --------------------------------------------------------- artifact → bundle


def test_artifact_and_bundle_persist_with_chain(db_session):
    collected = ev.OperatorSiteCollector().collect(
        url="https://brand.example/pet-policy",
        content_hash="b" * 64,
        excerpt="本店允许携带小型犬入内，需使用推车。",
        published_at=datetime(2026, 2, 1, tzinfo=UTC),
    )
    artifact = ev.record_artifact(db_session, collected)
    bundle = ev.create_bundle(
        db_session,
        artifact,
        extracted_fragment="小型犬可入内（需推车）",
        extraction_method="manual",
        place_match_evidence={"method": "url_domain", "confidence": 0.9},
    )
    assert isinstance(artifact, SourceArtifact)
    assert isinstance(bundle, EvidenceBundle)
    assert bundle.artifact_id == artifact.id
    # 原始引用被保留，派生阅读单独存放
    assert bundle.quoted_fragment == collected.captured_excerpt
    assert bundle.extracted_fragment == "小型犬可入内（需推车）"
    assert bundle.evidence_class == EvidenceClass.ORIGINAL
    assert bundle.content_hash == "b" * 64
    assert bundle.captured_at is not None


def test_derived_evidence_must_cite_origin(db_session):
    """派生证据（OCR/AI）不得脱离原始证据独立存在。"""
    artifact = ev.record_artifact(
        db_session, ev.OnsiteEvidenceCollector().collect(media_id="m1", excerpt="禁止宠物入内")
    )
    original = ev.create_bundle(db_session, artifact)

    with pytest.raises(ApiError) as err:
        ev.create_bundle(db_session, artifact, evidence_class=EvidenceClass.DERIVED)
    assert err.value.code == "derived_evidence_requires_origin"

    # 引用原始证据后即可创建
    derived = ev.create_bundle(
        db_session,
        artifact,
        evidence_class=EvidenceClass.DERIVED,
        derived_from_bundle_id=original.id,
        extracted_fragment="OCR: 禁止宠物入内",
        extraction_method="ocr",
        extraction_model="mock-ocr",
    )
    assert derived.derived_from_bundle_id == original.id


def test_bundle_copies_license_metadata_from_artifact(db_session):
    """许可状态在采集时刻固化，之后改动许可不影响历史判定。"""
    artifact = ev.record_artifact(
        db_session, ev.SocialLeadCollector().collect(url="https://dy.example/x", excerpt="可带狗")
    )
    bundle = ev.create_bundle(db_session, artifact)
    assert bundle.license_metadata["storage_allowed"] is False
    assert bundle.license_metadata["redistribution_allowed"] is False


# ------------------------------------------------------ lane classification


def test_classify_routes_policy_language_to_rule_lane():
    assert ev.classify("本店禁止携带宠物进入") == ClaimKind.RULE
    assert ev.classify("Pets are not allowed indoors") == ClaimKind.RULE
    assert ev.classify(ev.ClaimDraft(kind=ClaimKind.RULE)) == ClaimKind.RULE


def test_classify_routes_first_person_sighting_to_observation_lane():
    assert ev.classify("我看到有人把狗放在椅子上") == ClaimKind.OBSERVATION
    assert ev.classify(ev.ClaimDraft(kind=ClaimKind.OBSERVATION)) == ClaimKind.OBSERVATION


def test_classify_never_auto_promotes_ambiguous_text_to_rule():
    """不确定的内容必须落到较弱的 observation 通道，不得自动升级为规则。"""
    assert ev.classify("今天下午去了那家店") == ClaimKind.OBSERVATION
    assert ev.classify("") == ClaimKind.OBSERVATION


def test_observation_phrase_wins_over_policy_word():
    """出现第一人称目击标记时不得因含政策词而误判为规则。"""
    text = "我看到告示写着禁止宠物，但当时还是有狗进来"
    assert ev.classify(text) == ClaimKind.OBSERVATION


# --------------------------------------------------------- publish guards


def test_lead_only_source_cannot_publish_without_licence(db_session):
    """外部社交线索只能进候选，缺许可不得发布。"""
    artifact = ev.record_artifact(
        db_session, ev.SocialLeadCollector().collect(url="https://xhs.example/p/9", excerpt="禁止")
    )
    bundle = ev.create_bundle(db_session, artifact, quoted_fragment="禁止携带宠物")
    with pytest.raises(ApiError) as err:
        ev.assert_publishable(bundle, kind=ClaimKind.RULE)
    assert err.value.code == "lead_only_source_not_publishable"


def test_lead_only_source_publishable_once_licensed(db_session):
    artifact = ev.record_artifact(
        db_session, ev.SocialLeadCollector().collect(url="https://xhs.example/p/9", excerpt="禁止")
    )
    bundle = ev.create_bundle(
        db_session,
        artifact,
        quoted_fragment="禁止携带宠物",
        license_metadata={"redistribution_allowed": True},
    )
    ev.assert_publishable(bundle, kind=ClaimKind.RULE)  # 不抛异常


def test_rule_bundle_needs_traceable_content(db_session):
    """规则类证据必须有原文片段或哈希，否则无法追溯。"""
    artifact = ev.record_artifact(
        db_session,
        ev.ManualVerificationCollector().collect(note="电话确认可以带狗"),
    )
    bundle = ev.create_bundle(db_session, artifact, quoted_fragment=None)
    bundle.quoted_fragment = None
    bundle.content_hash = None
    with pytest.raises(ApiError) as err:
        ev.assert_publishable(bundle, kind=ClaimKind.RULE)
    assert err.value.code == "rule_evidence_not_traceable"


def test_observation_bundle_does_not_require_hash(db_session):
    """观察类证据不适用规则追溯门槛。"""
    artifact = ev.record_artifact(
        db_session, ev.ManualVerificationCollector().collect(note="看到狗在座位上")
    )
    bundle = ev.create_bundle(db_session, artifact, quoted_fragment=None)
    bundle.quoted_fragment = None
    bundle.content_hash = None
    ev.assert_publishable(bundle, kind=ClaimKind.OBSERVATION)  # 不抛异常


# ------------------------------------------------- observation candidate lane


def test_observation_candidate_starts_discovered(db_session):
    artifact = ev.record_artifact(
        db_session, ev.ManualVerificationCollector().collect(note="看到狗在自助区")
    )
    bundle = ev.create_bundle(db_session, artifact)
    cand = ev.create_observation_candidate(
        db_session,
        bundle,
        draft=ev.ClaimDraft(
            kind=ClaimKind.OBSERVATION,
            observed_action="on_seat",
            spatial_context="self_service_area",
            animal_scope="ordinary_pet",
        ),
    )
    assert isinstance(cand, ObservationCandidate)
    assert cand.review_status == "DISCOVERED"
    assert cand.evidence_bundle_id == bundle.id
    assert cand.observed_action == "on_seat"


def test_observation_candidate_is_a_separate_table_from_rule_candidate(db_session):
    """结构性边界：观察候选不得写进 rule_candidate 表。

    Asserted per-run by candidate id rather than a global table count — the dev
    database is shared, so a global count would be order-dependent.
    """
    artifact = ev.record_artifact(
        db_session, ev.ManualVerificationCollector().collect(note="看到狗在桌面")
    )
    bundle = ev.create_bundle(db_session, artifact)
    obs = ev.create_observation_candidate(
        db_session, bundle, draft=ev.ClaimDraft(kind=ClaimKind.OBSERVATION)
    )
    db_session.flush()

    from sqlalchemy import select

    from app.models import RuleCandidate

    # the observation row lives only in its own table
    assert db_session.get(ObservationCandidate, obs.id) is not None
    assert db_session.get(RuleCandidate, obs.id) is None
    # and nothing landed in the rule lane for this run's source
    linked = db_session.scalars(
        select(RuleCandidate).where(RuleCandidate.source_id == obs.source_id)
    ).all()
    assert linked == []


def test_observation_state_machine_shape():
    assert OBSERVATION_CANDIDATE_TRANSITIONS["DISCOVERED"] == {"EXTRACTED", "REJECTED"}
    assert OBSERVATION_CANDIDATE_TRANSITIONS["APPROVED"] == {"PUBLISHED", "REJECTED"}
    assert OBSERVATION_CANDIDATE_TRANSITIONS["PUBLISHED"] == {"SUPERSEDED"}
    assert OBSERVATION_CANDIDATE_TRANSITIONS["REJECTED"] == set()
    assert OBSERVATION_CANDIDATE_TRANSITIONS["SUPERSEDED"] == set()


# ------------------------------------------------------------ full ingest


def test_ingest_and_classify_never_creates_a_rule(db_session):
    """ingest 只产出 artifact+bundle+kind；规则必须经人工复核后单独发布。"""
    from sqlalchemy import func, select

    from app.models import AccessRule

    before = db_session.scalar(select(func.count()).select_from(AccessRule)) or 0

    artifact, bundle, kind = ev.ingest_and_classify(
        db_session,
        ev.OfficialWebCollector().collect(
            url="https://gov.example/rule", content_hash="c" * 64, excerpt="公园禁止宠物入内"
        ),
        draft=ev.ClaimDraft(
            kind=ClaimKind.RULE,
            extracted_fragment="公园禁止宠物入内",
            animal_scope="ordinary_pet",
            action="enter",
            effect="prohibited",
        ),
    )
    assert kind == ClaimKind.RULE
    assert bundle.artifact_id == artifact.id

    after = db_session.scalar(select(func.count()).select_from(AccessRule)) or 0
    assert after == before, "ingest 不得直接产生 AccessRule"


def test_ingest_source_id_is_propagated(db_session):
    """source 归属沿 chain 传递，便于后台按来源追溯。"""
    from app.models import Source

    source = Source(
        source_type="official_operator_policy",
        issuer=_uniq("运营方来源"),
        directness="direct",
        collected_at=datetime.now(UTC),
    )
    db_session.add(source)
    db_session.flush()

    artifact, bundle, _ = ev.ingest_and_classify(
        db_session,
        ev.OperatorSiteCollector().collect(url="https://s.example/p", excerpt="允许"),
        draft=ev.ClaimDraft(kind=ClaimKind.RULE, extracted_fragment="允许"),
        source_id=source.id,
    )
    assert artifact.source_id == source.id
    assert bundle.source_id == source.id


def test_artifact_rejects_unknown_source_id(db_session):
    """外键把 source 归属钉死在真实来源上，不允许悬挂引用。"""
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        ev.record_artifact(
            db_session,
            ev.OperatorSiteCollector().collect(url="https://s.example/q", excerpt="允许"),
            source_id=_uniq("ghost-src"),
        )
        db_session.flush()
