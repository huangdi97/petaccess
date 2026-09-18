"""Canonical audit event vocabulary (§14).

Before this module the audit action was an inline string literal at every call
site, which is how the publish contract drifted: the HTTP exception publish
route wrote ``candidate.publish_exception`` while the governed CLI publisher
only ever produced ``candidate.transition``, and nothing failed. A name that
only exists in one file is not a contract.

So the vocabulary lives here, once, and:

* every writer imports the constant — no literal action names in routes;
* ``PUBLISH_AUDIT_REQUIRED`` states what a publish *must* leave behind, which
  is exactly what `scripts/verify_publish_r3.py` checks, so verifier and
  publisher cannot disagree about the shape of a complete trail again;
* backfills are labelled with :data:`AUDIT_BACKFILL_REASON` and never pretend
  to be the original event (§16).

Adding a name here is a governance decision, not a formatting change: the
verifier, the publisher and the integrity scanner all read this set.
"""

from __future__ import annotations

from enum import StrEnum

#: Marker written into ``audit_log.detail`` for rows appended after the fact.
AUDIT_BACKFILL_REASON = "CLI_AUDIT_EVENT_CONTRACT_RECONCILIATION"

#: The ``detail`` key that says "this row was reconciled, not observed".
BACKFILL_FLAG = "backfilled"

#: The ``detail`` key carrying the true publish moment of the reconciled event.
ORIGINAL_PUBLISH_AT = "original_publish_at"


class AuditEvent(StrEnum):
    """Every action name the platform is allowed to write to ``audit_log``."""

    # --- candidate lifecycle -------------------------------------------------
    CANDIDATE_CREATE = "candidate.create"
    CANDIDATE_TRANSITION = "candidate.transition"
    CANDIDATE_PUBLISH = "candidate.publish"
    CANDIDATE_PUBLISH_EXCEPTION = "candidate.publish_exception"
    CANDIDATE_SET_SCOPE = "candidate.set_scope"
    CANDIDATE_SET_RULE_LAYER = "candidate.set_rule_layer"
    CANDIDATE_SET_MANDATORY_LEVEL = "candidate.set_mandatory_level"

    # --- rule / exception ----------------------------------------------------
    RULE_CREATE = "rule.create"
    RULE_UPDATE = "rule.update"
    RULE_EXCEPTION_CREATE = "rule_exception.create"
    RULE_EXCEPTION_TRANSITION = "rule_exception.transition"

    # --- place / zone / geometry --------------------------------------------
    PLACE_CREATE = "place.create"
    PLACE_UPDATE = "place.update"
    ZONE_CREATE = "zone.create"
    GEOMETRY_CREATE = "geometry.create"
    AMENITY_CREATE = "amenity.create"
    PLACE_BINDING_CREATE = "place_binding.create"

    # --- provenance ----------------------------------------------------------
    SOURCE_CREATE = "source.create"
    ARTIFACT_CREATE = "artifact.create"
    EVIDENCE_BUNDLE_CREATE = "evidence_bundle.create"
    MONITOR_CREATE = "monitor.create"
    MONITOR_CHECK = "monitor.check"
    DATA_LICENSE_CREATE = "data_license.create"

    # --- data production / freshness (30-50 PLACE EXPANSION WAVE 01) --------
    #: A bounded collection run. Without it a finished script leaves rows behind
    #: that nothing can attribute, which is how unauditable data enters.
    DATA_SOURCE_JOB_CREATE = "data_source_job.create"
    DATA_SOURCE_JOB_FINISH = "data_source_job.finish"
    FRESHNESS_POLICY_CREATE = "freshness_policy.create"
    #: Attaching a review window to a source. Overdue means "re-verify", never
    #: "invalid" — the name deliberately says assign, not invalidate.
    SOURCE_FRESHNESS_ASSIGN = "source.freshness_assign"

    # --- observations --------------------------------------------------------
    OBSERVATION_CANDIDATE_CREATE = "observation_candidate.create"
    OBSERVATION_CANDIDATE_TRANSITION = "observation_candidate.transition"

    # --- civic / governance --------------------------------------------------
    DISPUTE_SUBMIT = "dispute.submit"
    DISPUTE_REVIEW = "dispute.review"
    DISPUTE_RESOLVE = "dispute.resolve"
    REGULATION_CREATE = "regulation.create"
    REGULATION_REVIEW = "regulation.review"
    POLICY_TEMPLATE_CREATE = "policy_template.create"
    EVENT_POLICY_CREATE = "event_policy.create"
    ORGANIZATION_CREATE = "organization.create"
    OPERATOR_CLAIM_REVIEW = "operator_claim.review"
    OPERATOR_CLAIM_APPROVE = "operator_claim.approve"
    OPERATOR_QUESTIONNAIRE_SUBMIT = "operator_questionnaire.submit"
    BOUNDARY_PROFILE_UPSERT = "boundary_profile.upsert"

    # --- media ---------------------------------------------------------------
    MEDIA_UPLOAD = "media.upload"
    MEDIA_DELETE = "media.delete"

    # --- governance ----------------------------------------------------------
    #: Appended by the governed production cleanup. Never a substitute for the
    #: original event: ``detail`` always carries the reason and the scope.
    GOVERNANCE_CLEANUP = "governance.cleanup"


#: Events a governed publish must leave behind, per published object kind.
#: ``verify_publish_r3.py`` asserts exactly these, and the publisher is expected
#: to produce them; keeping the two lists in one file is the point.
PUBLISH_AUDIT_REQUIRED: frozenset[str] = frozenset(
    {
        AuditEvent.CANDIDATE_TRANSITION.value,
        AuditEvent.CANDIDATE_PUBLISH.value,
        AuditEvent.CANDIDATE_PUBLISH_EXCEPTION.value,
    }
)


def is_canonical(action: str) -> bool:
    """True when ``action`` is part of the canonical vocabulary."""
    return action in _VALUES


def canonical_events() -> tuple[str, ...]:
    """Sorted canonical action names — what a scanner should accept."""
    return tuple(sorted(_VALUES))


_VALUES: frozenset[str] = frozenset(e.value for e in AuditEvent)
