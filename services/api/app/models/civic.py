"""JurisdictionRule, DisputeCase, AuditLog, WatchSubscription (design #18, #24, #26)."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PkMixin, TimestampMixin

from .enums import (
    AnimalScope,
    DisputeCaseStatus,
    DisputeResolution,
    DisputeTargetType,
    JurisdictionLevel,
    JurisdictionReviewStatus,
    MandatoryLevel,
    RuleAction,
    RuleEffect,
    TemporaryAction,
    WatchStatus,
    WatchTargetType,
)


class JurisdictionRule(Base, PkMixin, TimestampMixin):
    """Law/regulation entries with structured time/space/scope (design #18).

    review_status strictly distinguishes:
      not_reviewed / no_explicit_rule_found / explicit_operator_discretion / reviewed_active
    'not reviewed' must never render as 'the law says nothing' (design #18).
    """

    __tablename__ = "jurisdiction_rule"
    __table_args__ = (
        Index("ix_jurisdiction_geo", "jurisdiction_level", "jurisdiction_id"),
        Index("ix_jurisdiction_review", "review_status"),
    )

    jurisdiction_level: Mapped[JurisdictionLevel] = mapped_column(String(16), nullable=False)
    jurisdiction_id: Mapped[str] = mapped_column(String(64), nullable=False)
    authority: Mapped[str] = mapped_column(String(200), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(64), nullable=False)
    document_name: Mapped[str] = mapped_column(String(300), nullable=False)
    clause_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    clause_text_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    animal_scope: Mapped[AnimalScope] = mapped_column(String(20), nullable=False)
    venue_scope: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[RuleAction | None] = mapped_column(String(24), nullable=True)
    effect: Mapped[RuleEffect | None] = mapped_column(String(16), nullable=True)
    conditions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    mandatory_level: Mapped[MandatoryLevel] = mapped_column(
        String(20), default=MandatoryLevel.MANDATORY, nullable=False
    )
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("source.id", ondelete="RESTRICT"), nullable=False
    )
    supersedes_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="current", nullable=False)
    review_status: Mapped[JurisdictionReviewStatus] = mapped_column(
        String(40), default=JurisdictionReviewStatus.NOT_REVIEWED, nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class DisputeCase(Base, PkMixin, TimestampMixin):
    __tablename__ = "dispute_case"
    __table_args__ = (
        Index("ix_dispute_status", "status"),
        Index("ix_dispute_target", "target_type", "target_id"),
    )

    target_type: Mapped[DisputeTargetType] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    claimant_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    notice_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_refs: Mapped[list | None] = mapped_column(JSON, nullable=True)
    temporary_action: Mapped[TemporaryAction] = mapped_column(
        String(24), default=TemporaryAction.NONE, nullable=False
    )
    counter_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    counter_party_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[DisputeCaseStatus] = mapped_column(
        String(32), default=DisputeCaseStatus.SUBMITTED, nullable=False
    )
    resolution: Mapped[DisputeResolution | None] = mapped_column(String(40), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    forwarded_to: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    """Append-only audit trail for high-impact operations (design #25, #27)."""

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_target", "target_type", "target_id"),
        Index("ix_audit_actor", "actor_user_id"),
        Index("ix_audit_created", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    before_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class WatchSubscription(Base, PkMixin, TimestampMixin):
    """User watches a place/zone/rule; notified when rules change (design #24)."""

    __tablename__ = "watch_subscription"
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_watch_user_target"),
        Index("ix_watch_target", "target_type", "target_id"),
        CheckConstraint("target_id IS NOT NULL", name="needs_target"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    target_type: Mapped[WatchTargetType] = mapped_column(String(16), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    channels: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[WatchStatus] = mapped_column(
        String(16), default=WatchStatus.ACTIVE, nullable=False
    )
    last_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
