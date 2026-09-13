"""Evidence-First multi-source collection (brief §5, NEXT_GOAL §B3/B4/B5/B15).

Principle: every published fact must be traceable back to an original artifact.
AI/OCR output is *derived* evidence and never replaces the original.

    SourceCollector → SourceArtifact → EvidenceBundle → Claim → Candidate

Two deliberately distinct layers:

- ``SourceArtifact`` — what a collector actually obtained (URL, page snapshot,
  official notice, onsite signage photo, uploaded image, video keyframe). It
  records the licence/privacy posture of the *fetch* itself.
- ``EvidenceBundle`` — the reviewed, attributable statement derived from one or
  more artifacts: who published it, when, what fragment was quoted, how it was
  matched to a place, which extractor produced the derived reading.

An EvidenceBundle is the only thing a RuleCandidate / ObservationCandidate may
cite. A candidate without an evidence bundle cannot be approved.

External social platforms (小红书 / 抖音 / 微博 / 点评 …) are positioned at
**lead discovery** in v0.5: they may create a SourceArtifact + candidate for
manual review, but never publish a rule directly, and content is not stored or
redistributed in bulk without an explicit licence (see DataLicense).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin, TimestampMixin

# --------------------------------------------------------------------- vocab


class SourcePlatform:
    """Where an artifact came from. External platforms are lead-only."""

    OFFICIAL_WEB = "official_web"
    OPERATOR_SITE = "operator_site"
    SEARCH_DISCOVERY = "search_discovery"
    SOCIAL_PLATFORM = "social_platform"
    USER_LINK = "user_link"
    MANUAL_VERIFICATION = "manual_verification"
    ONSITE = "onsite"
    PLATFORM_UPLOAD = "platform_upload"

    ALL = [
        OFFICIAL_WEB,
        OPERATOR_SITE,
        SEARCH_DISCOVERY,
        SOCIAL_PLATFORM,
        USER_LINK,
        MANUAL_VERIFICATION,
        ONSITE,
        PLATFORM_UPLOAD,
    ]

    #: platforms whose content is lead-discovery only in v0.5 — never a direct
    #: published rule, and never bulk-stored/redistributed without a licence
    LEAD_ONLY = [SOCIAL_PLATFORM, SEARCH_DISCOVERY, USER_LINK]


class PublisherType:
    GOVERNMENT = "government"
    OFFICIAL_OPERATOR = "official_operator"
    STAFF = "staff"
    TRUSTED_VERIFIER = "trusted_verifier"
    ORDINARY_USER = "ordinary_user"
    UNKNOWN = "unknown"

    ALL = [GOVERNMENT, OFFICIAL_OPERATOR, STAFF, TRUSTED_VERIFIER, ORDINARY_USER, UNKNOWN]


class EvidenceClass:
    """Original vs derived (brief §5.5).

    Only ORIGINAL carries independent weight; DERIVED must always point at the
    artifact it was computed from so the chain stays auditable.
    """

    ORIGINAL = "original"
    DERIVED = "derived"

    ALL = [ORIGINAL, DERIVED]


class ExtractionMethod:
    MANUAL = "manual"
    OCR = "ocr"
    AI_VISION = "ai_vision"
    AI_TEXT = "ai_text"
    URL_MONITOR = "url_monitor"
    IMPORT = "import"
    PHONE = "phone"
    ONSITE_VISIT = "onsite_visit"

    ALL = [MANUAL, OCR, AI_VISION, AI_TEXT, URL_MONITOR, IMPORT, PHONE, ONSITE_VISIT]


class CollectorType:
    """Reserved collector axis (brief §5.3). Not all are implemented in v0.5."""

    OFFICIAL_WEB = "OfficialWebCollector"
    OPERATOR_SITE = "OperatorSiteCollector"
    SEARCH_DISCOVERY = "SearchDiscoveryCollector"
    SOCIAL_LEAD = "SocialLeadCollector"
    USER_LINK = "UserLinkCollector"
    MANUAL_VERIFICATION = "ManualVerificationCollector"
    ONSITE_EVIDENCE = "OnsiteEvidenceCollector"

    ALL = [
        OFFICIAL_WEB,
        OPERATOR_SITE,
        SEARCH_DISCOVERY,
        SOCIAL_LEAD,
        USER_LINK,
        MANUAL_VERIFICATION,
        ONSITE_EVIDENCE,
    ]

    #: implementable in v0.5 without external licences/keys
    IMPLEMENTED_IN_V05 = [OFFICIAL_WEB, OPERATOR_SITE, MANUAL_VERIFICATION, ONSITE_EVIDENCE]


class ClaimKind:
    """Rule vs observation split (brief §5.4)."""

    RULE = "rule"  # 店方规定 / 官方公告 / 工作人员明确政策
    OBSERVATION = "observation"  # 某人看到宠物在座椅/桌面/自助区

    ALL = [RULE, OBSERVATION]


# ------------------------------------------------------------------ artifact


class SourceArtifact(Base, PkMixin, TimestampMixin):
    """A raw thing a collector obtained. The original-evidence anchor.

    Deliberately stores *references* (object key, snapshot ref) rather than
    inline blobs, so licence and TTL rules can be applied per artifact.
    """

    __tablename__ = "source_artifact"
    __table_args__ = (
        Index("ix_artifact_source", "source_id"),
        Index("ix_artifact_hash", "content_hash"),
        Index("ix_artifact_collected", "collected_at"),
    )

    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )
    source_platform: Mapped[str] = mapped_column(String(40), nullable=False)
    collector_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    artifact_type: Mapped[str] = mapped_column(
        String(40), nullable=False
    )  # url | page_snapshot | official_notice | signage_photo
    # | uploaded_image | video_keyframe | phone_note

    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_content_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    #: link to media_object when the artifact is stored media (no FK: media may
    #: be purged by TTL while the audit record must survive)
    media_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    #: opaque pointer to a stored page snapshot / screenshot
    snapshot_ref: Mapped[str | None] = mapped_column(String(400), nullable=True)

    #: hash of the *captured bytes* — the change-detection anchor
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    publisher_type: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    #: captured excerpt kept on the artifact itself (bounded, for review)
    captured_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    #: descriptive capture posture (EvidenceStrength) — NOT a trust score; a
    #: NULL here means "captured before the classification existed" (legacy row)
    evidence_strength: Mapped[str | None] = mapped_column(String(24), nullable=True)

    #: licence posture at collection time (denormalised from DataLicense for audit)
    storage_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    redistribution_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    retention_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    data_source_job_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("data_source_job.id", ondelete="SET NULL"), nullable=True
    )

    bundles: Mapped[list[EvidenceBundle]] = relationship(back_populates="artifact")


# -------------------------------------------------------------------- bundle


class EvidenceBundle(Base, PkMixin, TimestampMixin):
    """Attributable evidence statement derived from one source artifact.

    A candidate cites a bundle; a bundle cites an artifact. Removing the middle
    layer would let derived AI output masquerade as an original source, which
    the brief explicitly forbids.
    """

    __tablename__ = "evidence_bundle"
    __table_args__ = (
        Index("ix_evidence_artifact", "artifact_id"),
        Index("ix_evidence_source", "source_id"),
        Index("ix_evidence_class", "evidence_class"),
        Index("ix_evidence_captured", "captured_at"),
    )

    artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source_artifact.id", ondelete="RESTRICT"), nullable=False
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )

    # --- attribution ---
    source_platform: Mapped[str] = mapped_column(String(40), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    publisher_type: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)

    # --- temporality: when it was said vs when we saw it ---
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # --- the statement itself ---
    quoted_fragment: Mapped[str | None] = mapped_column(Text, nullable=True)  # exact original words
    extracted_fragment: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # normalised/derived reading
    evidence_class: Mapped[str] = mapped_column(String(20), default="original", nullable=False)

    # --- integrity ---
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    screenshot_ref: Mapped[str | None] = mapped_column(String(400), nullable=True)
    snapshot_ref: Mapped[str | None] = mapped_column(String(400), nullable=True)

    # --- matching / extraction provenance ---
    place_match_evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    temporal_evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(40), nullable=True)
    extraction_model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    extraction_model_version: Mapped[str | None] = mapped_column(String(40), nullable=True)

    #: derived evidence must cite the original bundle it was computed from
    derived_from_bundle_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # --- review ---
    reviewer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    review_log: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # --- licence / privacy metadata (copied for audit even if licence changes) ---
    license_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    privacy_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    artifact: Mapped[SourceArtifact] = relationship(back_populates="bundles")


# ------------------------------------------------------- candidate separation


class ObservationCandidate(Base, PkMixin, TimestampMixin):
    """Observed-practice candidate — a *separate* lane from RuleCandidate.

    "Someone saw a pet on a seat" is an observation, never a rule. Keeping the
    two tables apart makes the hard boundary structural rather than a convention
    that a future contributor could accidentally break.
    """

    __tablename__ = "observation_candidate"
    __table_args__ = (
        Index("ix_obs_candidate_status", "review_status"),
        Index("ix_obs_candidate_place", "place_id"),
    )

    evidence_bundle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evidence_bundle.id", ondelete="RESTRICT"), nullable=False
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )
    place_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="SET NULL"), nullable=True
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="SET NULL"), nullable=True
    )

    animal_scope: Mapped[str | None] = mapped_column(String(20), nullable=True)
    observed_action: Mapped[str | None] = mapped_column(String(40), nullable=True)
    #: spatial context the observation concerns (seat / table / self-service area…)
    spatial_context: Mapped[str | None] = mapped_column(String(40), nullable=True)

    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(40), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    review_status: Mapped[str] = mapped_column(String(20), default="DISCOVERED", nullable=False)
    reviewer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    #: set when the reviewed observation is promoted into an ObservationClaim
    published_claim_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    derivation_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    duplicate_of_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


OBSERVATION_CANDIDATE_TRANSITIONS: dict[str, set[str]] = {
    "DISCOVERED": {"EXTRACTED", "REJECTED"},
    "EXTRACTED": {"PLACE_MATCH_PENDING", "REJECTED"},
    "PLACE_MATCH_PENDING": {"REVIEW_PENDING", "REJECTED"},
    "REVIEW_PENDING": {"APPROVED", "REJECTED"},
    "APPROVED": {"PUBLISHED", "REJECTED"},
    "PUBLISHED": {"SUPERSEDED"},
    "REJECTED": set(),
    "SUPERSEDED": set(),
}
