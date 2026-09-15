"""AccessRule, RuleCondition, Source entities (design #10-13, #40)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin, TimestampMixin

from .enums import (
    AnimalScope,
    Directness,
    IssuerVerification,
    RuleAction,
    RuleConditionType,
    RuleEffect,
    RuleOrigin,
    RuleStatus,
    SourceAvailability,
    SourceType,
    SpatialPrecision,
)

if TYPE_CHECKING:
    from .place import Place, Zone

CONDITION_TYPES = [e.value for e in RuleConditionType]


class Source(Base, PkMixin, TimestampMixin):
    """Multi-dimensional provenance; no single trust score (design #13, ADR-006)."""

    __tablename__ = "source"

    source_type: Mapped[SourceType] = mapped_column(String(40), nullable=False, index=True)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer_verification: Mapped[IssuerVerification] = mapped_column(
        String(20), default=IssuerVerification.UNVERIFIED, nullable=False
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_snapshot_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_availability: Mapped[SourceAvailability] = mapped_column(
        String(24), default=SourceAvailability.AVAILABLE_ONLINE, nullable=False
    )
    directness: Mapped[Directness] = mapped_column(String(16), nullable=False)
    spatial_precision: Mapped[SpatialPrecision] = mapped_column(
        String(16), default=SpatialPrecision.UNKNOWN, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    rules: Mapped[list["AccessRule"]] = relationship(back_populates="source")


class AccessRule(Base, PkMixin, TimestampMixin):
    """What a source says SHOULD happen; observations never become rules (ADR-004)."""

    __tablename__ = "access_rule"
    __table_args__ = (
        # A rule is owned by a place/zone, OR is a jurisdiction-level rule that
        # applies by place_type (ADR-025). Exactly one of those shapes.
        CheckConstraint(
            "(place_id IS NOT NULL) OR (zone_id IS NOT NULL) OR (jurisdiction_code IS NOT NULL)",
            name="needs_owner",
        ),
        CheckConstraint("supersedes_rule_id != id", name="supersedes_not_self"),
        # BLK-LAYER-02 / ADR-023: mandatory_level is a closed vocabulary. The
        # legacy spelling 'discretionary' is tolerated so a pre-existing row can
        # still validate; the additive migration normalises it.
        CheckConstraint(
            "mandatory_level IS NULL OR mandatory_level IN "
            "('mandatory','advisory','operator_discretion','discretionary')",
            name="mandatory_level",
        ),
        # ADR-025: scope normalisation must be declared, and a query-only parent
        # group may never stand in for a source-specific legal scope.
        CheckConstraint(
            "normalization_type IS NULL OR normalization_type IN "
            "('exact','parent_group_for_query_only','legal_interpretation_required',"
            "'compound_term_split')",
            name="normalization_type",
        ),
        CheckConstraint(
            "normative_effect IS NULL OR normative_effect IN "
            "('permission','prohibition','conditional_permission',"
            "'exempt_from_prohibition','facilitation_required')",
            name="normative_effect",
        ),
        CheckConstraint(
            "holder_scope IS NULL OR holder_scope IN ('any_handler','person_with_disability')",
            name="holder_scope",
        ),
        Index("ix_access_rule_place_status", "place_id", "status"),
        Index("ix_access_rule_zone_status", "zone_id", "status"),
        Index("ix_access_rule_scope_action", "animal_scope", "action"),
        Index("ix_access_rule_review_due", "review_due_at"),
        Index("ix_access_rule_jurisdiction", "jurisdiction_code", "status"),
    )

    place_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("place.id", ondelete="CASCADE"), nullable=True, index=True
    )
    zone_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("zone.id", ondelete="CASCADE"), nullable=True, index=True
    )
    animal_scope: Mapped[AnimalScope] = mapped_column(String(20), nullable=False)
    action: Mapped[RuleAction] = mapped_column(String(24), nullable=False)
    effect: Mapped[RuleEffect] = mapped_column(String(16), nullable=False)
    # ---- ADR-025: source-faithful scope + normative effect ------------------
    #: what the source literally names (e.g. 'guide_dog'); never widened
    source_scope_exact: Mapped[str | None] = mapped_column(String(64), nullable=True)
    #: the precise AnimalRole this rule governs (query/legal matching unit)
    subject_scope_normalized: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: how source_scope_exact became subject_scope_normalized
    normalization_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: what the source normatively does (carve-out / duty / plain effect)
    normative_effect: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: who must be holding the animal (无障碍法第46条 ⇒ person_with_disability)
    holder_scope: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: positive duties the venue owes (identification equipment, protective
    #: measures…); a list, because the source may name several
    operator_obligations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    #: jurisdiction-level rules only: ISO 3166-2-ish code, e.g. 'CN-SH'
    jurisdiction_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    #: jurisdiction-level rules only: which place_types it applies to
    applies_to_place_types: Mapped[list | None] = mapped_column(JSON, nullable=True)
    #: per-place projections point back at the jurisdiction rule they copy
    projection_of_rule_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
    )
    rule_origin: Mapped[RuleOrigin] = mapped_column(String(40), nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[RuleStatus] = mapped_column(
        String(20), default=RuleStatus.PENDING_REVIEW, nullable=False
    )
    supersedes_rule_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("access_rule.id", ondelete="SET NULL"), nullable=True
    )
    # Free text may only supplement, never drive matching (design #11)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- v0.5 additive metadata (MIGRATION_SPEC_v0.5) ---
    # rule_layer: LEGAL | REGULATORY_GUIDANCE | OPERATOR_POLICY | TEMPORARY_POLICY
    # NULL means legacy row → resolver reports REVIEW_REQUIRED (never guessed).
    rule_layer: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Normative force of this rule (BLK-LAYER-02 / ADR-023):
    # mandatory | advisory | operator_discretion.
    # The resolver only treats a LEGAL rule as its floor when this is
    # 'mandatory'; NULL is NEVER interpreted as mandatory (unknown ≠ binding).
    # The publish boundary requires a LEGAL candidate to declare it, so a
    # statutory prohibition cannot silently become relaxable.
    mandatory_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    origin_authority: Mapped[str | None] = mapped_column(String(160), nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    policy_template_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    event_policy_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    freshness_policy_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    place: Mapped["Place | None"] = relationship(back_populates="rules", foreign_keys=[place_id])
    zone: Mapped["Zone | None"] = relationship(back_populates="rules", foreign_keys=[zone_id])
    source: Mapped["Source"] = relationship(back_populates="rules")
    conditions: Mapped[list["RuleCondition"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )


class RuleCondition(Base, PkMixin, TimestampMixin):
    """Structured condition attached to a rule (design #11).

    value semantics by condition type:
      - flags (leash_required etc.): value_flag
      - numeric (max_weight_kg etc.): value_numeric
      - windows (time_windows/date_windows/season): value_json
      - text refs (designated_entrance etc.): value_text
    """

    __tablename__ = "rule_condition"
    __table_args__ = (Index("ix_rule_condition_rule", "rule_id"),)

    rule_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("access_rule.id", ondelete="CASCADE"), nullable=False
    )
    condition_type: Mapped[RuleConditionType] = mapped_column(String(40), nullable=False)
    value_flag: Mapped[bool | None] = mapped_column(nullable=True)
    value_numeric: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    value_text: Mapped[str | None] = mapped_column(String(200), nullable=True)
    value_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    rule: Mapped["AccessRule"] = relationship(back_populates="conditions")


class RuleException(Base, PkMixin, TimestampMixin):
    """A carve-out attached to a base rule (SG-REAL-01; PILOT-REVIEW S3).

    The same normative statement may govern a broad scope while exempting a
    narrower one — e.g. 《上海市养犬管理条例》第二十三条 prohibits dogs in
    商场 while its 但书 exempts guide dogs. Modelling the exemption as a
    second standalone rule cannot express "exempt FROM this rule"; the resolver
    saw two same-layer rules and silently picked the strictest.

    Semantics (ADR layered-animal-scope, DECISIONS.md):
      - animal_scope is the scope the exception GOVERNS (service_dog for guide
        dogs — the user-declared working role, never derived from photos).
      - effect is what applies to that scope instead of the base effect.
      - source_id is NOT NULL: an exception without provenance is invalid.
      - Only status='current' exceptions apply; expired windows fall back to
        the base rule; withdrawn/superseded never apply.
      - Observations never take part in resolution (ADR-004).
    """

    __tablename__ = "rule_exception"
    __table_args__ = (
        Index("ix_rule_exception_rule", "rule_id"),
        Index("ix_rule_exception_status", "status"),
        # ADR-025: a carve-out must declare the precise scope it names.
        CheckConstraint(
            "normalization_type IS NULL OR normalization_type IN "
            "('exact','parent_group_for_query_only','legal_interpretation_required',"
            "'compound_term_split')",
            name="normalization_type",
        ),
        CheckConstraint(
            "normative_effect IS NULL OR normative_effect IN "
            "('permission','prohibition','conditional_permission',"
            "'exempt_from_prohibition','facilitation_required')",
            name="normative_effect",
        ),
    )

    rule_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("access_rule.id", ondelete="CASCADE"), nullable=False
    )
    animal_scope: Mapped[AnimalScope] = mapped_column(String(20), nullable=False)
    effect: Mapped[RuleEffect] = mapped_column(String(16), nullable=False)
    # ---- ADR-025: the carve-out is source-faithful too -----------------------
    #: what the source literally names (e.g. 'guide_dog')
    source_scope_exact: Mapped[str | None] = mapped_column(String(64), nullable=True)
    #: precise AnimalRole the carve-out governs; matching uses this
    subject_scope_normalized: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: exact | parent_group_for_query_only | legal_interpretation_required
    normalization_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: exempt_from_prohibition for a 但书/豁免; permission for a plain grant
    normative_effect: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: any_handler | person_with_disability
    holder_scope: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[RuleStatus] = mapped_column(
        String(20), default=RuleStatus.CURRENT, nullable=False
    )
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
