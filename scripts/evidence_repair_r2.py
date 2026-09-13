"""Evidence Repair (PILOT-REVIEW-AND-SCHEMA-FIX-01 S6) — DB application.

Applies the R2 evidence repairs captured on 2026-09-13 to the pilot DB:
  - 新华网/界面新闻 direct fetch   → 港汇恒隆 indoor ban (B1)  SECONDARY_REPUTABLE
  - Fairmont 官网 guest-services   → 和平饭店 pet policy (B3/B4) PRIMARY_DIRECT
  - 潮新闻 (Starbucks China 回应)  → 西岸梦中心店 (B6/B7)       SECONDARY_REPUTABLE
  - 新浪/澎湃 现场实探             → 西岸梦中心客服引述条例      SECONDARY_REPUTABLE

Candidates are re-pointed to the stronger bundles; corrections carry an
audit_log row each. Nothing is approved or published by this script — review
gate stays 100% human.
"""

from __future__ import annotations

import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "api"))

from sqlalchemy import select  # noqa: E402

from app.db.session import get_session_factory  # noqa: E402
from app.models import RuleCandidate, Source  # noqa: E402
from app.models.enums import (  # noqa: E402
    Directness,
    EvidenceStrength,
    IssuerVerification,
    SourceAvailability,
    SourceType,
    SpatialPrecision,
)
from app.models.evidence import EvidenceBundle, SourceArtifact  # noqa: E402

NOW = datetime.now(UTC)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def audit(db, action: str, target_type: str, target_id: str, before, after, note=None) -> None:
    """Append an audit row; the note rides in after_state.detail (AuditLog has
    no free-text column — structured state only)."""
    from app.models import AuditLog

    after = dict(after or {})
    if note:
        after["detail"] = note
    db.add(
        AuditLog(
            id=f"repair-{hashlib.md5((action + target_id + str(NOW)).encode()).hexdigest()[:12]}",
            actor_role="agent:evidence_repair",
            action=action,
            target_type=target_type,
            target_id=target_id,
            before_state=before,
            after_state=after,
        )
    )


SOURCES = [
    {
        "key": "xinhua_jiemian_gh",
        "source_type": SourceType.EXTERNAL_WEB_REFERENCE.value,
        "issuer": "新华网/界面新闻《“宠物友好”餐厅，两边不讨好》（运营方规定报道，原文已直抓）",
        "issuer_verification": IssuerVerification.VERIFIED.value,
        "source_url": "http://www.xinhuanet.com/food/20260529/7317dcff712642e9a63813374aab5b3b/c.html",
        "published_at": datetime(2026, 5, 29, tzinfo=UTC),
        "directness": Directness.SECONDARY.value,
        "excerpt": (
            "比如港汇恒隆广场、兴业太古汇自今年2月起正式实施全新宠物管理规定，"
            "明确禁止除导盲犬等工作犬以外的其他宠物进入商场室内公共区域，"
            "全面撤除“宠物友好”相关标识"
        ),
        "collector": "agent_web_reader",
        "strength": EvidenceStrength.SECONDARY_REPUTABLE.value,
        "storage": True,
        "display": True,
        "redistribution": False,
        "publisher_type": "news_media",
    },
    {
        "key": "fairmont_official_fp",
        "source_type": SourceType.OFFICIAL_OPERATOR_POLICY.value,
        "issuer": "费尔蒙上海和平饭店官网《宾客信息·宠物政策》",
        "issuer_verification": IssuerVerification.VERIFIED.value,
        "source_url": "https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html",
        "published_at": None,
        "directness": Directness.DIRECT.value,
        "excerpt": (
            "上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。"
            "导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。"
        ),
        "collector": "agent_web_reader",
        "strength": EvidenceStrength.PRIMARY_DIRECT.value,
        "storage": True,
        "display": True,
        "redistribution": False,
        "publisher_type": "operator_official",
    },
    {
        "key": "tidenews_xm",
        "source_type": SourceType.EXTERNAL_WEB_REFERENCE.value,
        "issuer": "潮新闻《星巴克回应宠物专区“让座”争议：已致歉并着手改进》（星巴克中国官方回应）",
        "issuer_verification": IssuerVerification.VERIFIED.value,
        "source_url": "https://tidenews.com.cn/news.html?id=3542194",
        "published_at": datetime(2026, 8, 27, tzinfo=UTC),
        "directness": Directness.SECONDARY.value,
        "excerpt": (
            "为此我们已向顾客本人表达了诚挚的歉意，并着手进行了改进，"
            "不在该店内继续设置宠物区域。……携宠顾客需在店外宠物友好区落座。"
        ),
        "collector": "agent_web_reader",
        "strength": EvidenceStrength.SECONDARY_REPUTABLE.value,
        "storage": True,
        "display": True,
        "redistribution": False,
        "publisher_type": "news_media",
    },
    {
        "key": "sina_xm",
        "source_type": SourceType.EXTERNAL_WEB_REFERENCE.value,
        "issuer": (
            "新浪财经/澎湃《网友称在星巴克被要求给带宠物的让座，记者现场实探》"
            "（西岸梦中心客服回应）"
        ),
        "issuer_verification": IssuerVerification.VERIFIED.value,
        "source_url": "https://finance.sina.com.cn/jjxw/2026-08-27/doc-iniptnux5511541.shtml",
        "published_at": datetime(2026, 8, 27, tzinfo=UTC),
        "directness": Directness.SECONDARY.value,
        "excerpt": (
            "从宠物友好的角度出发，西岸梦中心的户外空间和外摆区域是允许宠物活动的，"
            "但是否允许宠物进店，则要看每家门店自己的规定，西岸梦中心对此没有统一要求和规定。"
            "……从管理角度，西岸梦中心属于上海市徐汇区，"
            "因此会按照《上海市养犬管理条例》、市规大于商场规定的原则来执行。"
        ),
        "collector": "agent_web_reader",
        "strength": EvidenceStrength.SECONDARY_REPUTABLE.value,
        "storage": True,
        "display": True,
        "redistribution": False,
        "publisher_type": "news_media",
    },
]

PLACE_KEYS = {
    "xinhua_jiemian_gh": "gh-grand-gateway",
    "fairmont_official_fp": "fp-peace-hotel",
    "tidenews_xm": "xm-west-bund-gate-m",
    "sina_xm": "xm-west-bund-gate-m",
}

# candidate rule_id fragment → (source_key, quote, place_name, address)
REPOINT = {
    "gh-indoor-new": (
        "xinhua_jiemian_gh",
        "比如港汇恒隆广场、兴业太古汇自今年2月起正式实施全新宠物管理规定，明确禁止除导盲犬等工作犬以外的其他宠物进入商场室内公共区域",
        "港汇恒隆广场",
        "上海市徐汇区虹桥路1号",
    ),
    "fp-pets-op": (
        "fairmont_official_fp",
        "上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。",
        "和平饭店（费尔蒙）",
        "上海市黄浦区南京东路20号",
    ),
    "fp-sd-op": (
        "fairmont_official_fp",
        "导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。",
        "和平饭店（费尔蒙）",
        "上海市黄浦区南京东路20号",
    ),
    "xm-indoor-new": (
        "tidenews_xm",
        "并着手进行了改进，不在该店内继续设置宠物区域",
        "星巴克咖啡（徐汇西岸梦中心店）",
        "上海市徐汇区龙腾大道（西岸梦中心 GATE M）",
    ),
    "xm-outdoor-media": (
        "tidenews_xm",
        "携宠顾客需在店外宠物友好区落座",
        "星巴克咖啡（徐汇西岸梦中心店）",
        "上海市徐汇区龙腾大道（西岸梦中心 GATE M）",
    ),
}

# rule_id → rule_id of the base rule carrying an operator-level exemption note
EXEMPTION_NOTES = {
    # 新华网原文本身写明运营方政策含工作犬例外
    "gh-indoor-new": (
        "原文明确『除导盲犬等工作犬以外』——运营方政策自带服务犬例外"
        "（配合 RuleException 建模）"
    ),
}


def main() -> int:
    db = get_session_factory()()
    created = {"sources": 0, "artifacts": 0, "bundles": 0, "repointed": 0}

    # canonical places from the pilot manifest
    manifest = __import__("json").loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs/reality_audit/real_pilot_ingest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    places_by_key = manifest["places"]

    source_ids: dict[str, str] = {}
    for sd in SOURCES:
        existing = db.scalars(select(Source).where(Source.source_url == sd["source_url"])).first()
        if existing is None:
            existing = Source(
                source_type=sd["source_type"],
                issuer=sd["issuer"],
                issuer_verification=sd["issuer_verification"],
                source_url=sd["source_url"],
                collected_at=NOW,
                observed_at=NOW,
                published_at=sd["published_at"],
                source_availability=SourceAvailability.AVAILABLE_ONLINE,
                directness=sd["directness"],
                spatial_precision=SpatialPrecision.PRECISE,
                notes=f"capture_method=web_reader_fetch; repair=R2; strength={sd['strength']}",
            )
            db.add(existing)
            db.flush()
            created["sources"] += 1
        source_ids[sd["key"]] = existing.id

        art = db.scalars(
            select(SourceArtifact).where(
                SourceArtifact.source_id == existing.id,
                SourceArtifact.collector_type == sd["collector"],
            )
        ).first()
        if art is None:
            art = SourceArtifact(
                source_id=existing.id,
                source_platform=sd["collector"],
                collector_type=sd["collector"],
                artifact_type="web_page_text",
                source_url=sd["source_url"],
                content_hash=sha(sd["excerpt"]),
                collected_at=NOW,
                publisher_type=sd["publisher_type"],
                published_at=sd["published_at"],
                captured_excerpt=sd["excerpt"],
                storage_allowed=sd["storage"],
                display_allowed=sd["display"],
                redistribution_allowed=sd["redistribution"],
                evidence_strength=sd["strength"],
            )
            db.add(art)
            db.flush()
            created["artifacts"] += 1

        pkey = PLACE_KEYS[sd["key"]]
        place_id = places_by_key[pkey]
        bundle = db.scalars(
            select(EvidenceBundle).where(
                EvidenceBundle.artifact_id == art.id,
                EvidenceBundle.quoted_fragment == sd["excerpt"],
            )
        ).first()
        if bundle is None:
            bundle = EvidenceBundle(
                artifact_id=art.id,
                source_id=existing.id,
                source_platform=sd["collector"],
                source_url=sd["source_url"],
                quoted_fragment=sd["excerpt"],
                evidence_class="original",
                content_hash=sha(sd["excerpt"]),
                captured_at=NOW,
                extraction_method="agent_assisted_extraction_2026_09_13",
                extraction_model="zcode-agent",
                place_match_evidence={
                    "matched_by": "canonical_name_and_address",
                    "place_id": place_id,
                    "note": "R2 修复：原文页直接抓取并核验",
                },
                temporal_evidence={
                    "published_at": sd["published_at"].isoformat() if sd["published_at"] else None,
                    "captured_at": NOW.isoformat(),
                },
            )
            db.add(bundle)
            db.flush()
            created["bundles"] += 1
        sd["bundle_id"] = bundle.id

    # re-point candidates to the stronger bundles
    candidates = db.scalars(
        select(RuleCandidate).where(
            RuleCandidate.extraction_method == "agent_assisted_extraction_2026_09_13"
        )
    ).all()
    by_rule_note = {c.id: c for c in candidates}
    # candidates map by their ingest manifest keys: rule_candidates[f"{pkey}:{rule_id}"]
    cand_by_key = manifest["rule_candidates"]
    key_for = {
        "gh-indoor-new": "gh-grand-gateway:gh-indoor-new",
        "fp-pets-op": "fp-peace-hotel:fp-pets-op",
        "fp-sd-op": "fp-peace-hotel:fp-sd-op",
        "xm-indoor-new": "xm-west-bund-gate-m:xm-indoor-new",
        "xm-outdoor-media": "xm-west-bund-gate-m:xm-outdoor-media",
    }
    for rule_id, (skey, quote, place_name, _address) in REPOINT.items():
        cand_id = cand_by_key[key_for[rule_id]]
        cand = by_rule_note[cand_id]
        new_bundle_id = next(sd["bundle_id"] for sd in SOURCES if sd["key"] == skey)
        old_bundle_id = cand.evidence_bundle_id
        if old_bundle_id == new_bundle_id:
            continue
        cand.evidence_bundle_id = new_bundle_id
        audit(
            db,
            "evidence.repair",
            "rule_candidate",
            cand.id,
            {"evidence_bundle_id": old_bundle_id},
            {"evidence_bundle_id": new_bundle_id},
            note=f"R2 Evidence Repair: 改挂直接抓取来源（{place_name}），引文：{quote[:60]}",
        )
        created["repointed"] += 1
        if rule_id in EXEMPTION_NOTES:
            cand.review_note = EXEMPTION_NOTES[rule_id]

    # 和平饭店服务动物条款：官方原文为准（无限制），修正候选 effect
    fp_sd = by_rule_note[cand_by_key["fp-peace-hotel:fp-sd-op"]]
    if fp_sd.effect == "conditional":
        before = fp_sd.effect
        fp_sd.effect = "allowed"
        audit(
            db,
            "evidence.repair.correction",
            "rule_candidate",
            fp_sd.id,
            {"effect": before},
            {"effect": "allowed"},
            note="官方原文：导盲犬可随时进入酒店，且无需支付额外费用或受任何限制",
        )

    # 记录未修复/矛盾项
    mn_cand = by_rule_note[cand_by_key["mn-kaidi-hongkou:mn-outdoor-media"]]
    audit(
        db,
        "evidence.repair.contradiction",
        "rule_candidate",
        mn_cand.id,
        None,
        {"status": "misattributed_lead"},
        note=(
            "CBNData 原文（255703）未报道凯德虹口宠物友好店；『凯德虹口』指宠物用品店狗道。"
            "建议人工 REJECT 或改挂真实来源"
        ),
    )
    gh_outdoor = by_rule_note[cand_by_key["gh-grand-gateway:gh-outdoor-keep"]]
    audit(
        db,
        "evidence.repair.no_change",
        "rule_candidate",
        gh_outdoor.id,
        None,
        {"status": "needs_verification"},
        note="新华网原文仅证实室内公共区域禁令，『户外保留』未被证实；维持 Needs Verification",
    )

    db.commit()
    import json

    print(json.dumps({"created": created, "at": NOW.isoformat()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
