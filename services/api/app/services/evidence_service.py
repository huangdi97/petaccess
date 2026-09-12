"""Evidence-First collection service (brief §5, §6, DATA_PIPELINE_SPEC).

Responsibilities
----------------
1. ``SourceCollector`` implementations turn an external input into a
   ``SourceArtifact`` + ``EvidenceBundle`` pair. Collectors never create rules.
2. ``classify`` decides whether captured content belongs to the **rule** lane
   (店方规定 / 官方公告 / 工作人员明确政策) or the **observation** lane
   (someone saw a pet on a seat). The two lanes have separate tables, so the
   boundary is structural.
3. Lead-only platforms (小红书 / 抖音 / 微博 / 点评 …) may produce a candidate
   for review but are blocked from direct publication without a licence.

Non-negotiables enforced here:
- derived evidence always cites the original bundle it came from
- a candidate must cite an EvidenceBundle
- lead-only sources cannot publish without ``redistribution``/``display`` licence
- no bulk persistence of external-platform content without an explicit licence
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.evidence import (
    ClaimKind,
    CollectorType,
    EvidenceBundle,
    EvidenceClass,
    ObservationCandidate,
    SourceArtifact,
    SourcePlatform,
)

# ------------------------------------------------------------------ contracts


@dataclass
class CollectedArtifact:
    """Neutral output every collector produces (brief §5.2 SourceArtifact)."""

    source_platform: str
    artifact_type: str
    collector_type: str
    source_url: str | None = None
    source_content_id: str | None = None
    media_id: str | None = None
    snapshot_ref: str | None = None
    content_hash: str | None = None
    publisher_type: str = "unknown"
    published_at: datetime | None = None
    captured_excerpt: str | None = None
    #: licence posture; conservative defaults (display/redistribution denied)
    storage_allowed: bool = True
    display_allowed: bool = False
    redistribution_allowed: bool = False
    retention_until: datetime | None = None


@dataclass
class ClaimDraft:
    """Candidate-shaped claim extracted from a bundle, awaiting classification."""

    kind: str  # ClaimKind.RULE | ClaimKind.OBSERVATION
    quoted_fragment: str | None = None
    extracted_fragment: str | None = None
    animal_scope: str | None = None
    action: str | None = None
    effect: str | None = None
    observed_action: str | None = None
    spatial_context: str | None = None
    extraction_method: str | None = None
    extraction_model: str | None = None
    extraction_model_version: str | None = None
    derivation_confidence: float | None = None
    proposed_conditions: list = field(default_factory=list)


class SourceCollector:
    """Base collector. Subclasses declare the platform + whether they are
    implementable without external credentials (brief §5.3)."""

    collector_type: str = "SourceCollector"
    source_platform: str = SourcePlatform.PLATFORM_UPLOAD
    #: True when this collector only needs local/authorised input in v0.5
    implemented_in_v05: bool = False

    def collect(self, **kwargs) -> CollectedArtifact:  # pragma: no cover - interface
        raise NotImplementedError

    #: whether this collector may write content straight into review.
    #: lead-only collectors still require human review and a licence gate.
    @property
    def is_lead_only(self) -> bool:
        return self.source_platform in SourcePlatform.LEAD_ONLY


class OfficialWebCollector(SourceCollector):
    """Government / official notice pages. Authorised, non-lead."""

    collector_type = CollectorType.OFFICIAL_WEB
    source_platform = SourcePlatform.OFFICIAL_WEB
    implemented_in_v05 = True

    def collect(  # type: ignore[override]
        self,
        *,
        url: str,
        content_hash: str | None = None,
        excerpt: str | None = None,
        published_at: datetime | None = None,
    ) -> CollectedArtifact:
        return CollectedArtifact(
            source_platform=self.source_platform,
            artifact_type="url",
            collector_type=self.collector_type,
            source_url=url,
            content_hash=content_hash,
            publisher_type="government",
            published_at=published_at,
            captured_excerpt=excerpt,
            display_allowed=True,
            redistribution_allowed=False,
        )


class OperatorSiteCollector(SourceCollector):
    """Brand / store official site or public account announcement."""

    collector_type = CollectorType.OPERATOR_SITE
    source_platform = SourcePlatform.OPERATOR_SITE
    implemented_in_v05 = True

    def collect(  # type: ignore[override]
        self,
        *,
        url: str,
        content_hash: str | None = None,
        excerpt: str | None = None,
        published_at: datetime | None = None,
    ) -> CollectedArtifact:
        return CollectedArtifact(
            source_platform=self.source_platform,
            artifact_type="url",
            collector_type=self.collector_type,
            source_url=url,
            content_hash=content_hash,
            publisher_type="official_operator",
            published_at=published_at,
            captured_excerpt=excerpt,
            display_allowed=True,
            redistribution_allowed=False,
        )


class ManualVerificationCollector(SourceCollector):
    """Phone call / staff conversation recorded by a verifier."""

    collector_type = CollectorType.MANUAL_VERIFICATION
    source_platform = SourcePlatform.MANUAL_VERIFICATION
    implemented_in_v05 = True

    def collect(  # type: ignore[override]
        self,
        *,
        note: str,
        publisher_type: str = "staff",
        published_at: datetime | None = None,
    ) -> CollectedArtifact:
        return CollectedArtifact(
            source_platform=self.source_platform,
            artifact_type="phone_note",
            collector_type=self.collector_type,
            publisher_type=publisher_type,
            published_at=published_at,
            captured_excerpt=note,
            display_allowed=False,
            redistribution_allowed=False,
        )


class OnsiteEvidenceCollector(SourceCollector):
    """Signage photo / onsite observation captured at the venue."""

    collector_type = CollectorType.ONSITE_EVIDENCE
    source_platform = SourcePlatform.ONSITE
    implemented_in_v05 = True

    def collect(  # type: ignore[override]
        self,
        *,
        media_id: str | None = None,
        content_hash: str | None = None,
        excerpt: str | None = None,
        artifact_type: str = "signage_photo",
    ) -> CollectedArtifact:
        return CollectedArtifact(
            source_platform=self.source_platform,
            artifact_type=artifact_type,
            collector_type=self.collector_type,
            media_id=media_id,
            content_hash=content_hash,
            publisher_type="staff",
            captured_excerpt=excerpt,
            display_allowed=False,
            redistribution_allowed=False,
        )


class SocialLeadCollector(SourceCollector):
    """小红书 / 抖音 / 微博 / 点评 — **lead discovery only** in v0.5.

    Content must not be bulk-persisted or redistributed without an explicit
    API/licence. This collector therefore defaults every licence flag to deny
    and is treated as lead-only by ``classify``.
    """

    collector_type = CollectorType.SOCIAL_LEAD
    source_platform = SourcePlatform.SOCIAL_PLATFORM
    implemented_in_v05 = False  # requires platform API/licence

    def collect(  # type: ignore[override]
        self,
        *,
        url: str,
        excerpt: str | None = None,
        source_content_id: str | None = None,
    ) -> CollectedArtifact:
        return CollectedArtifact(
            source_platform=self.source_platform,
            artifact_type="url",
            collector_type=self.collector_type,
            source_url=url,
            source_content_id=source_content_id,
            publisher_type="ordinary_user",
            captured_excerpt=excerpt,
            storage_allowed=False,
            display_allowed=False,
            redistribution_allowed=False,
        )


class SearchDiscoveryCollector(SourceCollector):
    """Search-result lead: points at a source, stores no redistributable copy."""

    collector_type = CollectorType.SEARCH_DISCOVERY
    source_platform = SourcePlatform.SEARCH_DISCOVERY
    implemented_in_v05 = False

    def collect(self, *, url: str, excerpt: str | None = None) -> CollectedArtifact:  # type: ignore[override]
        return CollectedArtifact(
            source_platform=self.source_platform,
            artifact_type="url",
            collector_type=self.collector_type,
            source_url=url,
            captured_excerpt=excerpt,
            storage_allowed=False,
            display_allowed=False,
            redistribution_allowed=False,
        )


class UserLinkCollector(SourceCollector):
    """A user submitted a link. Lead until verified."""

    collector_type = CollectorType.USER_LINK
    source_platform = SourcePlatform.USER_LINK
    implemented_in_v05 = True

    def collect(self, *, url: str, excerpt: str | None = None) -> CollectedArtifact:  # type: ignore[override]
        return CollectedArtifact(
            source_platform=self.source_platform,
            artifact_type="url",
            collector_type=self.collector_type,
            source_url=url,
            captured_excerpt=excerpt,
            publisher_type="ordinary_user",
            display_allowed=False,
            redistribution_allowed=False,
        )


COLLECTORS: dict[str, type[SourceCollector]] = {
    CollectorType.OFFICIAL_WEB: OfficialWebCollector,
    CollectorType.OPERATOR_SITE: OperatorSiteCollector,
    CollectorType.SEARCH_DISCOVERY: SearchDiscoveryCollector,
    CollectorType.SOCIAL_LEAD: SocialLeadCollector,
    CollectorType.USER_LINK: UserLinkCollector,
    CollectorType.MANUAL_VERIFICATION: ManualVerificationCollector,
    CollectorType.ONSITE_EVIDENCE: OnsiteEvidenceCollector,
}


# -------------------------------------------------------------- persistence


def record_artifact(
    db: Session,
    collected: CollectedArtifact,
    *,
    source_id: str | None = None,
    data_source_job_id: str | None = None,
    now: datetime | None = None,
) -> SourceArtifact:
    """Freeze a collector's output as an original-evidence row."""
    artifact = SourceArtifact(
        source_id=source_id,
        source_platform=collected.source_platform,
        collector_type=collected.collector_type,
        artifact_type=collected.artifact_type,
        source_url=collected.source_url,
        source_content_id=collected.source_content_id,
        media_id=collected.media_id,
        snapshot_ref=collected.snapshot_ref,
        content_hash=collected.content_hash,
        collected_at=now or datetime.now(UTC),
        publisher_type=collected.publisher_type,
        published_at=collected.published_at,
        captured_excerpt=collected.captured_excerpt,
        storage_allowed=collected.storage_allowed,
        display_allowed=collected.display_allowed,
        redistribution_allowed=collected.redistribution_allowed,
        retention_until=collected.retention_until,
        data_source_job_id=data_source_job_id,
    )
    db.add(artifact)
    db.flush()
    return artifact


def create_bundle(
    db: Session,
    artifact: SourceArtifact,
    *,
    source_id: str | None = None,
    quoted_fragment: str | None = None,
    extracted_fragment: str | None = None,
    evidence_class: str = EvidenceClass.ORIGINAL,
    extraction_method: str | None = None,
    extraction_model: str | None = None,
    extraction_model_version: str | None = None,
    place_match_evidence: dict | None = None,
    temporal_evidence: dict | None = None,
    derived_from_bundle_id: str | None = None,
    license_metadata: dict | None = None,
    privacy_notes: str | None = None,
    now: datetime | None = None,
) -> EvidenceBundle:
    """Create the attributable evidence statement a candidate will cite.

    Derived bundles MUST point at the original bundle they were computed from —
    this is what stops an AI reading from masquerading as a source.
    """
    if evidence_class == EvidenceClass.DERIVED and not derived_from_bundle_id:
        raise ApiError(
            "派生证据必须引用其原始证据",
            code="derived_evidence_requires_origin",
        )
    bundle = EvidenceBundle(
        artifact_id=artifact.id,
        source_id=source_id or artifact.source_id,
        source_platform=artifact.source_platform,
        source_url=artifact.source_url,
        publisher_type=artifact.publisher_type,
        published_at=artifact.published_at,
        captured_at=now or datetime.now(UTC),
        quoted_fragment=quoted_fragment or artifact.captured_excerpt,
        extracted_fragment=extracted_fragment,
        evidence_class=evidence_class,
        content_hash=artifact.content_hash,
        screenshot_ref=artifact.snapshot_ref,
        snapshot_ref=artifact.snapshot_ref,
        place_match_evidence=place_match_evidence,
        temporal_evidence=temporal_evidence,
        extraction_method=extraction_method,
        extraction_model=extraction_model,
        extraction_model_version=extraction_model_version,
        derived_from_bundle_id=derived_from_bundle_id,
        license_metadata=license_metadata
        or {
            "storage_allowed": artifact.storage_allowed,
            "display_allowed": artifact.display_allowed,
            "redistribution_allowed": artifact.redistribution_allowed,
        },
        privacy_notes=privacy_notes,
    )
    db.add(bundle)
    db.flush()
    return bundle


# ------------------------------------------------------------- classification

#: rule-lane indicators: the publisher states a *policy*, not an observation
_RULE_SIGNALS = (
    "禁止",
    "谢绝",
    "不得",
    "允许",
    "可携带",
    "政策",
    "规定",
    "公告",
    "通则",
    "仅限",
    "prohibited",
    "allowed",
    "policy",
    "regulation",
)

#: observation-lane indicators: someone describes what they *saw*
_OBSERVATION_SIGNALS = (
    "看到",
    "见到",
    "当时",
    "我拍",
    "亲眼",
    "saw",
    "observed",
    "witnessed",
)


def classify(draft: ClaimDraft | str) -> str:
    """Route captured content to the rule or observation lane (brief §5.4).

    Explicit ``ClaimDraft.kind`` always wins. For raw text the decision is
    deliberately conservative: only clear policy language is routed to the rule
    lane; everything else stays an observation, because mis-filing an
    observation as a rule would put unverified claims into the normative set.
    """
    if isinstance(draft, ClaimDraft):
        if draft.kind in (ClaimKind.RULE, ClaimKind.OBSERVATION):
            return draft.kind
        text = f"{draft.quoted_fragment or ''} {draft.extracted_fragment or ''}"
    else:
        text = draft

    lowered = text.lower()
    if any(sig in text or sig in lowered for sig in _OBSERVATION_SIGNALS):
        return ClaimKind.OBSERVATION
    if any(sig in text or sig in lowered for sig in _RULE_SIGNALS):
        return ClaimKind.RULE
    # unknown provenance defaults to the weaker lane — never auto-promote
    return ClaimKind.OBSERVATION


def assert_publishable(
    bundle: EvidenceBundle, *, kind: str, license_metadata: dict | None = None
) -> None:
    """Guard rails checked before a claim may leave review (brief §5.3/§6).

    Lead-only platforms and licence-denied artifacts may be *reviewed* but must
    not be published — public visibility is not permission to redistribute.
    """
    if bundle.source_platform in SourcePlatform.LEAD_ONLY:
        meta = license_metadata or bundle.license_metadata or {}
        if not meta.get("redistribution_allowed", False):
            raise ApiError(
                f"来源平台 {bundle.source_platform} 仅作线索发现；缺少再分发许可，不得直接发布",
                code="lead_only_source_not_publishable",
            )
    if kind == ClaimKind.RULE and not bundle.content_hash and not bundle.quoted_fragment:
        raise ApiError(
            "规则类证据缺少原文片段或内容哈希，无法追溯",
            code="rule_evidence_not_traceable",
        )


# ------------------------------------------------------------- candidate lanes


def create_observation_candidate(
    db: Session,
    bundle: EvidenceBundle,
    *,
    draft: ClaimDraft,
    source_id: str | None = None,
    place_id: str | None = None,
    zone_id: str | None = None,
    occurred_at: datetime | None = None,
    raw_text: str | None = None,
) -> ObservationCandidate:
    """Observation-lane candidate. Never touches the normative rule set."""
    candidate = ObservationCandidate(
        evidence_bundle_id=bundle.id,
        source_id=source_id or bundle.source_id,
        place_id=place_id,
        zone_id=zone_id,
        animal_scope=draft.animal_scope,
        observed_action=draft.observed_action,
        spatial_context=draft.spatial_context,
        occurred_at=occurred_at or bundle.published_at,
        extraction_method=draft.extraction_method or bundle.extraction_method,
        raw_text=(raw_text or bundle.extracted_fragment or bundle.quoted_fragment or "")[:4000]
        or None,
        review_status="DISCOVERED",
        derivation_confidence=draft.derivation_confidence,
    )
    db.add(candidate)
    db.flush()
    return candidate


def ingest_and_classify(
    db: Session,
    collected: CollectedArtifact,
    *,
    draft: ClaimDraft,
    source_id: str | None = None,
    place_id: str | None = None,
    zone_id: str | None = None,
    data_source_job_id: str | None = None,
) -> tuple[SourceArtifact, EvidenceBundle, str]:
    """Full ingest path: artifact → bundle → classification.

    Returns (artifact, bundle, kind). Rule-lane callers then hand the bundle to
    the existing RuleCandidate service; observation-lane callers call
    ``create_observation_candidate``. This function itself never creates a rule.
    """
    artifact = record_artifact(
        db, collected, source_id=source_id, data_source_job_id=data_source_job_id
    )
    bundle = create_bundle(
        db,
        artifact,
        source_id=source_id,
        quoted_fragment=draft.quoted_fragment,
        extracted_fragment=draft.extracted_fragment,
        extraction_method=draft.extraction_method,
        extraction_model=draft.extraction_model,
        extraction_model_version=draft.extraction_model_version,
    )
    kind = classify(draft)
    return artifact, bundle, kind
