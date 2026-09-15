"""v0.5 domain entities (NEXT_GOAL Track B / MIGRATION_SPEC_v0.5).

New first-class entities: RuleLayer metadata on AccessRule, RuleCandidate,
DataSourceJob, SourceMonitor, FreshnessPolicy, CoexistencePolicy attributes,
BoundaryProfile/Preference, Amenity, Entrance, AccessPath, Organization +
PolicyTemplate (+rules, +place binding/override), EventPolicy, DataLicense.

Non-negotiables preserved: Observation never becomes a rule; candidates must
be APPROVED/PUBLISHED before touching the evaluator; UNKNOWN is never coerced.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin, TimestampMixin

# ---------------------------------------------------------------- organization


class Organization(Base, PkMixin, TimestampMixin):
    """Brand/corporate layer above Operator; owns PolicyTemplates (B13)."""

    __tablename__ = "organization"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), default="brand", nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    templates: Mapped[list["PolicyTemplate"]] = relationship(back_populates="organization")


class PolicyTemplate(Base, PkMixin, TimestampMixin):
    __tablename__ = "policy_template"

    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    # scope: which place types this template applies to (nullable = any)
    venue_scope: Mapped[str | None] = mapped_column(String(40), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="templates")
    rules: Mapped[list["PolicyTemplateRule"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )


class PolicyTemplateRule(Base, PkMixin, TimestampMixin):
    """Rule-shaped template entry, inherited by bound places unless overridden."""

    __tablename__ = "policy_template_rule"

    template_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("policy_template.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    animal_scope: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    effect: Mapped[str] = mapped_column(String(16), nullable=False)
    conditions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    rule_layer: Mapped[str] = mapped_column(String(30), default="OPERATOR_POLICY", nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # --- ADR-025: source-faithful scope for inherited template entries ---------
    #: what the template's source literally names (e.g. 'service_dog')
    source_scope_exact: Mapped[str | None] = mapped_column(String(64), nullable=True)
    #: the precise subject the entry governs — the legal matching unit
    subject_scope_normalized: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: exact | parent_group_for_query_only | legal_interpretation_required
    normalization_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: permission | prohibition | conditional_permission |
    #: exempt_from_prohibition | facilitation_required
    normative_effect: Mapped[str | None] = mapped_column(String(32), nullable=True)
    holder_scope: Mapped[str | None] = mapped_column(String(32), nullable=True)

    template: Mapped["PolicyTemplate"] = relationship(back_populates="rules")


class PlacePolicyBinding(Base, PkMixin, TimestampMixin):
    """Binds a place to an organization template + explicit place/zone overrides.

    overrides shape: [{"zone_id": null|"zone-x", "animal_scope": ..., "action": ...,
    "effect": ..., "conditions": [...]}] — explicit override always beats the
    inherited template entry at the same scope (never last-write-wins: both stay
    and the resolver explains precedence).
    """

    __tablename__ = "place_policy_binding"
    __table_args__ = (Index("ix_binding_place_active", "place_id", "is_active"),)

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("policy_template.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    overrides: Mapped[list | None] = mapped_column(JSON, nullable=True)
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ------------------------------------------------------------- data production


class RuleCandidate(Base, PkMixin, TimestampMixin):
    """Candidate rule produced by OCR/AI/imports/users — MUST be reviewed before
    it becomes an AccessRule (NEXT_GOAL §B3 hard boundary)."""

    __tablename__ = "rule_candidate"
    __table_args__ = (
        Index("ix_candidate_status", "review_status"),
        Index("ix_candidate_place", "place_id"),
    )

    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
    )
    place_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="SET NULL"), nullable=True
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="SET NULL"), nullable=True
    )
    animal_scope: Mapped[str | None] = mapped_column(String(20), nullable=True)
    action: Mapped[str | None] = mapped_column(String(24), nullable=True)
    effect: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # Normative layer the candidate claims (LEGAL | REGULATORY_GUIDANCE |
    # OPERATOR_POLICY | TEMPORARY_POLICY). Carried through to the published
    # AccessRule — publishing MUST NOT flatten a statutory rule to an operator
    # policy, because the resolver keys precedence/suppression on this value.
    rule_layer: Mapped[str] = mapped_column(
        String(30), default="OPERATOR_POLICY", server_default="OPERATOR_POLICY", nullable=False
    )
    # Normative force carried to the published rule (BLK-LAYER-02 / ADR-023):
    # mandatory | advisory | operator_discretion. NULL is preserved as "not
    # declared" — the publish gate refuses a LEGAL candidate without it, because
    # the resolver must never guess that a statutory prohibition is binding.
    mandatory_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # ---- ADR-025: source-faithful scope + normative effect ------------------
    # A source that says 导盲犬 governs guide_dog and nothing wider. These four
    # columns record what the source literally names, the precise AnimalRole it
    # was normalised to, whether that normalisation is a legal equivalent, and
    # what the source normatively does. Without them a guide-dog proviso gets
    # silently widened into "all service dogs allowed".
    source_scope_exact: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subject_scope_normalized: Mapped[str | None] = mapped_column(String(32), nullable=True)
    normalization_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    normative_effect: Mapped[str | None] = mapped_column(String(32), nullable=True)
    holder_scope: Mapped[str | None] = mapped_column(String(32), nullable=True)
    operator_obligations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    #: set when the candidate is a per-place projection of a jurisdiction rule
    projection_of_rule_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    proposed_conditions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(40), nullable=False)
    extraction_provider: Mapped[str | None] = mapped_column(String(60), nullable=True)
    internal_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(20), default="DISCOVERED", nullable=False)
    reviewer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_rule_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    media_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )  # media_object ref (no FK to avoid cycle with track A)
    evidence_bundle_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("evidence_bundle.id", ondelete="RESTRICT"),
        nullable=True,
    )  # candidates from the evidence chain cite their bundle (brief §5)


CANDIDATE_TRANSITIONS: dict[str, set[str]] = {
    "DISCOVERED": {"EXTRACTED", "REJECTED"},
    "EXTRACTED": {"MATCH_PENDING", "REJECTED"},
    "MATCH_PENDING": {"REVIEW_PENDING", "REJECTED"},
    "REVIEW_PENDING": {"APPROVED", "REJECTED"},
    "APPROVED": {"PUBLISHED", "REJECTED"},
    "PUBLISHED": {"SUPERSEDED"},
    "REJECTED": set(),
    "SUPERSEDED": set(),
}


class DataSourceJob(Base, PkMixin, TimestampMixin):
    """A bounded data-production run (imports, phone/onsite verify, monitor
    sweeps, AI extraction, mapping missions) with result counts + audit ref."""

    __tablename__ = "data_source_job"
    __table_args__ = (Index("ix_job_type_state", "job_type", "state"),)

    job_type: Mapped[str] = mapped_column(String(30), nullable=False)
    state: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    target_scope: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(60), nullable=True)
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_counts: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    errors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    audit_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)


class SourceMonitor(Base, PkMixin, TimestampMixin):
    """Watches an authorized source URL for changes (B5). SSRF-hardened fetch;
    change → diff artifact → RuleCandidate (never direct rule mutation)."""

    __tablename__ = "source_monitor"

    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="CASCADE"), nullable=False
    )
    monitor_type: Mapped[str] = mapped_column(String(30), default="url_hash", nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    schedule_minutes: Mapped[int] = mapped_column(default=1440, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    etag: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    failure_count: Mapped[int] = mapped_column(default=0, nullable=False)
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    place_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="SET NULL"), nullable=True
    )
    #: last fetched excerpt, retained so a detected change can be turned into a
    #: traceable EvidenceBundle (brief §6: source changed → diff → bundle)
    last_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)


class FreshnessPolicy(Base, PkMixin, TimestampMixin):
    """review_due ≠ invalid: overdue rules show '需要复核' but stay effective."""

    __tablename__ = "freshness_policy"

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    venue_scope: Mapped[str | None] = mapped_column(String(40), nullable=True)
    rule_layer: Mapped[str | None] = mapped_column(String(30), nullable=True)
    review_interval_days: Mapped[int] = mapped_column(default=90, nullable=False)


# ------------------------------------------------------------------- coexistence


class CoexistencePolicy(Base, PkMixin, TimestampMixin):
    """Structured coexistence attributes for a place/zone (B7) — neutral spatial
    facts from a source; never judgments about people."""

    __tablename__ = "coexistence_policy"
    __table_args__ = (
        UniqueConstraint(
            "place_id",
            "zone_id",
            "attribute",
            "source_id",
            name="uq_coexistence_place_zone_attr_source",
        ),
    )

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="CASCADE"), nullable=True
    )
    attribute: Mapped[str] = mapped_column(String(60), nullable=False)
    # value: allowed | prohibited | conditional | available | not_available | separated_type-x
    value: Mapped[str] = mapped_column(String(40), nullable=False)
    conditions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


COEXISTENCE_ATTRIBUTES = [
    "ordinary_pet_indoor_dining",
    "ordinary_pet_outdoor_dining",
    "animal_on_customer_seat",
    "animal_on_table_surface",
    "animal_near_food_service_area",
    "animal_in_self_service_food_area",
    "animal_use_customer_tableware",
    "dedicated_pet_tableware",
    "dedicated_pet_zone",
    "zone_separation",
]


class BoundaryProfile(Base, PkMixin, TimestampMixin):
    """User's own acceptance boundaries for animal coexistence (B8).
    First version: animal domain only. Never scores places; per-item only."""

    __tablename__ = "boundary_profile"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)

    preferences: Mapped[list["BoundaryPreference"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class BoundaryPreference(Base, PkMixin, TimestampMixin):
    """One structured preference: accept | require_prohibited | prefer | avoid."""

    __tablename__ = "boundary_preference"
    __table_args__ = (UniqueConstraint("profile_id", "attribute", name="uq_pref_profile_attr"),)

    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("boundary_profile.id", ondelete="CASCADE"), nullable=False
    )
    attribute: Mapped[str] = mapped_column(String(60), nullable=False)
    stance: Mapped[str] = mapped_column(String(30), nullable=False)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    profile: Mapped["BoundaryProfile"] = relationship(back_populates="preferences")


# ----------------------------------------------------------------- spatial extras


class Amenity(Base, PkMixin, TimestampMixin):
    """Independent of rules: what facilities exist (B10)."""

    __tablename__ = "amenity"
    __table_args__ = (Index("ix_amenity_place", "place_id", "amenity_type"),)

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="CASCADE"), nullable=True
    )
    amenity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="available", nullable=False)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


AMENITY_TYPES = [
    "PET_WATER",
    "WASTE_BAG",
    "PET_TOILET",
    "PET_WASH",
    "STROLLER_RENTAL",
    "TIE_UP",
    "PET_HOLDING",
    "PET_ELEVATOR",
    "PET_ENTRANCE",
    "PET_ACTIVITY_AREA",
]


class Entrance(Base, PkMixin, TimestampMixin):
    __tablename__ = "entrance"

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    entrance_type: Mapped[str] = mapped_column(String(30), default="GENERAL", nullable=False)
    location_wkt: Mapped[str | None] = mapped_column(Text, nullable=True)  # POINT WKT
    access_notes: Mapped[str | None] = mapped_column(String(400), nullable=True)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
    )


ENTRANCE_TYPES = ["GENERAL", "PET_DESIGNATED", "SERVICE", "PARKING_CONNECTION", "OTHER"]


class AccessPath(Base, PkMixin, TimestampMixin):
    """First version: named node-to-node route (e.g. 南门 → 2号宠物梯 → 3F宠物区),
    no path algorithms — expressive structured steps (B12)."""

    __tablename__ = "access_path"

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    from_node: Mapped[str] = mapped_column(String(160), nullable=False)
    to_node: Mapped[str] = mapped_column(String(160), nullable=False)
    steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    geometry_wkt: Mapped[str | None] = mapped_column(Text, nullable=True)
    animal_scope: Mapped[str | None] = mapped_column(String(20), nullable=True)
    conditions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    time_window: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="current", nullable=False)


class EventPolicy(Base, PkMixin, TimestampMixin):
    """Temporary/event rule with explicit validity (B14); expired events stop
    applying automatically but history is preserved."""

    __tablename__ = "event_policy"
    __table_args__ = (Index("ix_event_policy_window", "effective_from", "effective_to"),)

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    animal_scope: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    effect: Mapped[str] = mapped_column(String(16), nullable=False)
    conditions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    time_window: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recurrence: Mapped[str | None] = mapped_column(String(40), nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="current", nullable=False)


class DataLicense(Base, PkMixin, TimestampMixin):
    """Licensing separate from provenance (B15): unclear license ≠ redistributable."""

    __tablename__ = "data_license"

    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="CASCADE"), nullable=False
    )
    display_allowed: Mapped[bool] = mapped_column(default=True, nullable=False)
    storage_allowed: Mapped[bool] = mapped_column(default=True, nullable=False)
    redistribution_allowed: Mapped[bool] = mapped_column(default=False, nullable=False)
    commercial_use_allowed: Mapped[bool] = mapped_column(default=False, nullable=False)
    attribution_required: Mapped[bool] = mapped_column(default=True, nullable=False)
    license_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    license_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
