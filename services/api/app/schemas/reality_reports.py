"""RealityReport parent-flow DTOs (Master Goal v0.2.0 §15–§27).

One ``RealityContributionIn`` is a single user Contribution: a parent
``RealityReport`` plus zero-or-more typed candidates (observed_presence /
staff_response / animal_facility), with optional ObservationEffort,
RealityConfirmation and ExternalContentReference sharing the same
origin / place-match / time / media / source / privacy / reporter context.

Invariants enforced by the schema shape (and by the handler):

- ``observed_at`` is NEVER defaulted to the submission time (ON_SITE_PAST must
  supply an explicit time; missing ⇒ 422 with a UI-facing message).
- External content keeps ``content_published_at`` / ``claimed_event_at`` /
  ``observed_at`` as three separate fields — publication time is not event
  time; the UI must phrase it as "XX日发布的内容中观察到…".
- A confirmation is evidence, never a deletion; an effort is never a
  NO_ANIMAL_PRESENCE claim (service layer enforces both).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AnimalScope,
    RealityConfirmationType,
    RealityReportModerationState,
)
from app.schemas.reality import (
    ExternalContentReferenceIn,
    ObservationEffortIn,
    RealityConfirmationIn,
    RealityReportIn,
    RealityReportOut,
)


class RealityCandidateDraft(BaseModel):
    """Candidate inside a parent-flow report — place resolves from the report.

    ``place_id`` is optional here because the report's place-match context
    supplies it (`_candidate_place` enforces that a PARENT_PLACE_ONLY report
    never pins a candidate to a tenant place).
    """

    candidate_type: str = Field(min_length=1, max_length=32)
    place_id: str | None = None
    zone_id: str | None = None
    animal_scope: AnimalScope | None = None
    observed_at: datetime | None = None
    payload: dict | None = None


class RealityContributionIn(BaseModel):
    """The full contribution payload — one report, several shared candidates."""

    report: RealityReportIn
    candidates: list[RealityCandidateDraft] = Field(default_factory=list, max_length=5)
    effort: ObservationEffortIn | None = None
    confirmation: RealityConfirmationIn | None = None
    external_content: ExternalContentReferenceIn | None = None


class RealityCandidateBrief(BaseModel):
    """Candidate receipt returned after creation (no internal fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_type: str
    place_id: str
    zone_id: str | None = None
    animal_scope: AnimalScope | None = None
    observed_at: datetime | None = None
    review_status: str
    verification_status: str


class RealityContributionOut(BaseModel):
    """Receipt of a completed parent-flow contribution.

    ``anonymous_token`` is returned exactly once so the caller can persist it;
    it is never echoed back later by any consumer endpoint.
    """

    report: RealityReportOut
    candidates: list[RealityCandidateBrief]
    effort_id: str | None = None
    confirmation_id: str | None = None
    external_content_id: str | None = None
    abuse_flags: list[str] = Field(default_factory=list)
    moderation_state: RealityReportModerationState = RealityReportModerationState.PENDING


class RealityConfirmationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    confirmation_type: RealityConfirmationType
    place_id: str
    target_claim_id: str | None = None
    target_candidate_id: str | None = None
    observed_at: datetime | None = None
    created_at: datetime


class RealityTraceSection(BaseModel):
    """One trace section for the Reality Trace page (Master Goal §14)."""

    label: str
    value: str | None = None
    note: str | None = None


class RealityTraceOut(BaseModel):
    """Reality Trace payload — fact and how the platform verifies it."""

    place_id: str
    summary: str
    fact_sections: list[RealityTraceSection] = Field(default_factory=list)
    review_sections: list[RealityTraceSection] = Field(default_factory=list)
    evidence_count: int = 0
