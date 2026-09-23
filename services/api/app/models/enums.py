"""Domain enumerations frozen by docs/MASTER_DESIGN_v0.3_DEV.md.

Storage convention: values are stored as VARCHAR via native String enums
mapped in the entity modules; Python-side we use str-Enums so the API layer
can serialize them directly.
"""

from enum import StrEnum


class PlaceType(StrEnum):
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    MALL = "mall"
    STORE = "store"
    HOTEL = "hotel"
    PARK = "park"
    SQUARE = "square"
    GREENWAY = "greenway"
    BEACH = "beach"
    SCENIC_AREA = "scenic_area"
    RESIDENTIAL_COMMUNITY = "residential_community"
    OFFICE_CAMPUS = "office_campus"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    LIBRARY = "library"
    MUSEUM = "museum"
    SPORTS_VENUE = "sports_venue"
    TRANSPORT_HUB = "transport_hub"
    OTHER = "other"


class LifecycleStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    MERGED = "merged"
    ARCHIVED = "archived"


class ZoneType(StrEnum):
    AREA = "area"
    FLOOR = "floor"
    CHILDREN_AREA = "children_area"
    PET_AREA = "pet_area"
    LAWN = "lawn"
    PLAZA = "plaza"
    ROAD = "road"
    SUPERMARKET = "supermarket"
    DINING_AREA = "dining_area"
    ENTRANCE = "entrance"
    ELEVATOR = "elevator"
    OTHER = "other"


class IndoorOutdoor(StrEnum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    SEMI_OPEN = "semi_open"
    UNKNOWN = "unknown"


class AnimalScope(StrEnum):
    """Coarse scope kept for the public API surface (ADR-025).

    New records must also carry the precise ``AnimalRole`` in
    ``subject_scope_normalized`` — ``AnimalScope`` alone cannot express the
    difference between a guide dog and, say, a police dog.
    """

    DOG = "dog"
    CAT = "cat"
    ORDINARY_PET = "ordinary_pet"
    SERVICE_DOG = "service_dog"
    OTHER = "other"


class AnimalRole(StrEnum):
    """Precise animal-role taxonomy — the modelling unit for legal scope.

    Source fidelity rule (ADR-025): a source that says 导盲犬 governs
    ``GUIDE_DOG`` and **nothing wider**. Ontology (``GUIDE_DOG`` is-a
    ``SERVICE_DOG``) is a *query* convenience; it must never widen a
    source-specific legal effect.
    """

    ORDINARY_DOG = "ordinary_dog"
    GUIDE_DOG = "guide_dog"
    HEARING_DOG = "hearing_dog"
    ASSISTANCE_DOG = "assistance_dog"
    OTHER_SERVICE_DOG = "other_service_dog"
    POLICE_DOG = "police_dog"
    MILITARY_WORKING_DOG = "military_working_dog"


#: Roles that are service dogs in the assistance sense (query parent only).
SERVICE_DOG_ROLES: frozenset[str] = frozenset(
    {
        AnimalRole.GUIDE_DOG.value,
        AnimalRole.HEARING_DOG.value,
        AnimalRole.ASSISTANCE_DOG.value,
        AnimalRole.OTHER_SERVICE_DOG.value,
    }
)

#: Police and military working dogs are **working** dogs but are NOT service
#: dogs (they do not assist a person with a disability). Never fold them into
#: the service-dog parent.
WORKING_DOG_ROLES: frozenset[str] = frozenset(
    {*SERVICE_DOG_ROLES, AnimalRole.POLICE_DOG.value, AnimalRole.MILITARY_WORKING_DOG.value}
)

#: Leaf roles a query may expand to when the caller asks for the generic
#: "dog" scope. Order is irrelevant; the set is the point.
ALL_ANIMAL_ROLES: frozenset[str] = frozenset(r.value for r in AnimalRole)


class NormalizationType(StrEnum):
    """How a source scope was turned into a stored subject scope (ADR-025).

    Only the types in ``LEGAL_NORMALIZATION_TYPES`` (``EXACT`` and
    ``COMPOUND_TERM_SPLIT``) authorise the stored scope to stand in for the
    source's legal effect. The others are explicitly *not* legal equivalents.
    """

    #: stored scope == the scope the source literally names
    EXACT = "exact"
    #: stored scope is a query convenience (parent group); carries NO legal effect
    PARENT_GROUP_FOR_QUERY_ONLY = "parent_group_for_query_only"
    #: widening requires a legal interpretation that has not been made
    LEGAL_INTERPRETATION_REQUIRED = "legal_interpretation_required"
    #: The source used a **compound term** (e.g. 军警犬 = military + police dogs)
    #: and this row is ONE member of a documented, exhaustive split of that term.
    #: It carries legal effect, but only for its own member: the union of the
    #: split rows must equal the source's set, and nothing outside it may be
    #: added. ``source_scope_exact`` keeps the compound wording verbatim so the
    #: split stays auditable — this is NOT a licence to widen to "other working
    #: dogs". (ADR-028)
    COMPOUND_TERM_SPLIT = "compound_term_split"


#: normalisation types that DO confer legal effect (i.e. the stored scope is a
#: faithful reading of the source). Kept explicit so a new type cannot become
#: legal by accident.
LEGAL_NORMALIZATION_TYPES: frozenset[str] = frozenset(
    {
        NormalizationType.EXACT.value,
        NormalizationType.COMPOUND_TERM_SPLIT.value,
    }
)


class NormativeEffect(StrEnum):
    """What the source normatively does — a layer beside ``RuleEffect``.

    ``RuleEffect`` (allowed/prohibited/conditional) answers "may this subject
    enter?". It cannot express "the base prohibition does not apply to this
    subject" (a carve-out) or "the venue must actively accommodate this
    subject" (a duty). Forcing those into ``allowed`` silently inflates a
    duty into an unconditional permission, so they get their own layer
    (ADR-025). The API keeps returning ``effect``; ``normative_effect`` is
    additive.
    """

    PERMISSION = "permission"
    PROHIBITION = "prohibition"
    CONDITIONAL_PERMISSION = "conditional_permission"
    #: the rule removes a base prohibition for a narrow subject (但书/豁免)
    EXEMPT_FROM_PROHIBITION = "exempt_from_prohibition"
    #: the venue has a positive duty to accommodate (无障碍「提供便利」)
    FACILITATION_REQUIRED = "facilitation_required"


class HolderScope(StrEnum):
    """Who must be holding/using the animal for the norm to apply."""

    ANY_HANDLER = "any_handler"
    PERSON_WITH_DISABILITY = "person_with_disability"


#: ``RuleEffect`` values that a ``NormativeEffect`` may be reduced to for the
#: legacy 3-value API. ``FACILITATION_REQUIRED`` deliberately maps to
#: ``conditional`` — never ``allowed`` — because a duty is not a permission.
NORMATIVE_TO_EFFECT: dict[str, str] = {
    NormativeEffect.PERMISSION.value: "allowed",
    NormativeEffect.PROHIBITION.value: "prohibited",
    NormativeEffect.CONDITIONAL_PERMISSION.value: "conditional",
    NormativeEffect.EXEMPT_FROM_PROHIBITION.value: "allowed",
    NormativeEffect.FACILITATION_REQUIRED.value: "conditional",
}


class RuleAction(StrEnum):
    ENTER = "enter"
    PASS_THROUGH = "pass_through"
    STAY = "stay"
    WALK = "walk"
    OFF_LEASH = "off_leash"
    GROUND_CONTACT = "ground_contact"
    RIDE_ELEVATOR = "ride_elevator"
    RIDE_TRANSPORT = "ride_transport"
    USE_FACILITY = "use_facility"
    DINE = "dine"
    STAY_OVERNIGHT = "stay_overnight"


class RuleEffect(StrEnum):
    ALLOWED = "allowed"
    PROHIBITED = "prohibited"
    CONDITIONAL = "conditional"


class RuleStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    CURRENT = "current"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    DISPUTED = "disputed"
    ARCHIVED = "archived"


class RuleOrigin(StrEnum):
    OFFICIAL_REGULATION = "official_regulation"
    OPERATOR_DECLARED = "operator_declared"
    ONSITE_SIGNAGE = "onsite_signage"
    VERIFIED_VERIFIER = "verified_verifier"
    COMMUNITY_CONTRIBUTION = "community_contribution"
    IMPORTED = "imported"


class SourceType(StrEnum):
    STATUTE_OR_REGULATION = "statute_or_regulation"
    GOVERNMENT_SERVICE = "government_service"
    OFFICIAL_OPERATOR_POLICY = "official_operator_policy"
    ONSITE_SIGNAGE = "onsite_signage"
    CERTIFIED_VERIFIER = "certified_verifier"
    ORDINARY_USER = "ordinary_user"
    EXTERNAL_WEB_REFERENCE = "external_web_reference"
    IMPORTED_DATASET = "imported_dataset"


class IssuerVerification(StrEnum):
    VERIFIED = "verified"
    SELF_DECLARED = "self_declared"
    UNVERIFIED = "unverified"


class SourceAvailability(StrEnum):
    AVAILABLE_ONLINE = "available_online"
    AVAILABLE_OFFLINE = "available_offline"
    ARCHIVED = "archived"
    UNAVAILABLE = "unavailable"


class EvidenceStrength(StrEnum):
    """Descriptive capture posture of an artifact — NOT a trust score.

    Internal, reviewable classification of HOW evidence was captured. Never
    aggregated into a composite credibility number (design #13: no single
    trust score; PILOT-REVIEW-AND-SCHEMA-FIX-01 S7).
    """

    PRIMARY_DIRECT = "primary_direct"  # issuer's own channel, fetched verbatim
    PRIMARY_CAPTURED = "primary_captured"  # on-site capture (signage photo etc.)
    SECONDARY_REPUTABLE = "secondary_reputable"  # reputable news reporting issuer statement
    SEARCH_SNIPPET = "search_snippet"  # search-result snippet only; page not verified
    USER_SUBMITTED = "user_submitted"  # user content with stored artifact
    SOCIAL_LEAD = "social_lead"  # lead-only social content; never publishable


class Directness(StrEnum):
    DIRECT = "direct"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class SpatialPrecision(StrEnum):
    PRECISE = "precise"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


class GeometryType(StrEnum):
    POINT = "point"
    LINESTRING = "linestring"
    POLYGON = "polygon"
    MULTIPOLYGON = "multipolygon"


class ObservationStaffAction(StrEnum):
    """Only observable actions - subjective inference words are forbidden (design #14)."""

    EXPLICITLY_ALLOWED = "explicitly_allowed"
    EXPLICITLY_REFUSED = "explicitly_refused"
    ASKED_TO_REMOVE = "asked_to_remove"
    NO_INTERACTION_OBSERVED = "no_interaction_observed"
    INTERACTION_UNKNOWN = "interaction_unknown"


class OccurredPrecision(StrEnum):
    EXACT_TIME = "exact_time"
    SAME_HOUR = "same_hour"
    SAME_DAY = "same_day"
    SAME_WEEK = "same_week"
    APPROXIMATE = "approximate"


class PlaceConfidence(StrEnum):
    CONFIRMED_ON_SITE = "confirmed_on_site"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class ObservationDisputeStatus(StrEnum):
    NONE = "none"
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"


class VerificationEventType(StrEnum):
    RULE_CONFIRMED = "rule_confirmed"
    RULE_CHANGED = "rule_changed"
    SIGNAGE_UPLOADED = "signage_uploaded"
    FIELD_CHECK = "field_check"


class VerificationResult(StrEnum):
    STILL_VALID = "still_valid"
    CHANGED = "changed"
    UNCERTAIN = "uncertain"


class UserRole(StrEnum):
    USER = "user"
    OPERATOR = "operator"
    TRUSTED_VERIFIER = "trusted_verifier"
    MODERATOR = "moderator"
    ADMIN = "admin"


class UserStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class OperatorClaimStatus(StrEnum):
    SUBMITTED = "submitted"
    VERIFYING = "verifying"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"


class OperatorOrgType(StrEnum):
    COMPANY = "company"
    GOVERNMENT = "government"
    PROPERTY_MGMT = "property_mgmt"
    INDIVIDUAL_OWNER = "individual_owner"
    OTHER = "other"


class JurisdictionLevel(StrEnum):
    NATIONAL = "national"
    PROVINCIAL = "provincial"
    MUNICIPAL = "municipal"
    DISTRICT = "district"


class JurisdictionReviewStatus(StrEnum):
    """Three-way split of 'no rule' is mandatory (design #18)."""

    NOT_REVIEWED = "not_reviewed"
    NO_EXPLICIT_RULE_FOUND = "no_explicit_rule_found"
    EXPLICIT_OPERATOR_DISCRETION = "explicit_operator_discretion"
    REVIEWED_ACTIVE = "reviewed_active"


class MandatoryLevel(StrEnum):
    """Normative force of a rule/regulation (RULE_RESOLVER_SPEC, ADR-023).

    - ``mandatory``           — a binding constraint. The resolver treats a
      mandatory LEGAL rule as the floor: no lower layer may silently relax it.
    - ``advisory``            — guidance that informs but does not bind.
    - ``operator_discretion`` — the operator/venue decides; the default for
      operator-origin rules.

    The legacy value ``discretionary`` is still accepted on read (existing rows,
    fixtures) and is normalised to ``operator_discretion`` by
    ``app.rulespec.v05_resolver.normalize_mandatory_level``. It is intentionally
    NOT a member here so new writes cannot reintroduce the second spelling.
    """

    MANDATORY = "mandatory"
    ADVISORY = "advisory"
    OPERATOR_DISCRETION = "operator_discretion"


#: legacy spellings still found in old rows / fixtures → canonical value
LEGACY_MANDATORY_LEVELS: dict[str, str] = {
    "discretionary": MandatoryLevel.OPERATOR_DISCRETION.value,
}


def normalize_mandatory_level(value: str | None) -> str | None:
    """Map a stored mandatory_level onto the canonical vocabulary.

    Returns ``None`` unchanged (unknown level — never coerced to a value).
    """
    if value is None:
        return None
    return LEGACY_MANDATORY_LEVELS.get(str(value), str(value))


class DisputeCaseStatus(StrEnum):
    SUBMITTED = "submitted"
    EVIDENCE_PENDING = "evidence_pending"
    TEMPORARY_ACTION_APPLIED = "temporary_action_applied"
    FORWARDED = "forwarded"
    COUNTER_STATEMENT_RECEIVED = "counter_statement_received"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    WITHDRAWN = "withdrawn"


class DisputeTargetType(StrEnum):
    ACCESS_RULE = "access_rule"
    OBSERVATION_CLAIM = "observation_claim"


class TemporaryAction(StrEnum):
    NONE = "none"
    MARK_UNVERIFIED = "mark_unverified"
    MARK_DISPUTED = "mark_disputed"
    HIDE_CONTENT = "hide_content"


class DisputeResolution(StrEnum):
    RULE_RESTORED = "rule_restored"
    RULE_CORRECTED = "rule_corrected"
    CONTENT_ARCHIVED = "content_archived"
    CONTENT_DELETED = "content_deleted"
    OBSERVATION_UPHELD = "observation_upheld"
    OBSERVATION_CORRECTED = "observation_corrected"
    NO_CHANGE = "no_change"


class WatchTargetType(StrEnum):
    PLACE = "place"
    ZONE = "zone"
    RULE = "rule"


class WatchStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    UNSUBSCRIBED = "unsubscribed"


class PetSpecies(StrEnum):
    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


class ServiceRole(StrEnum):
    """User-declared only. Never derived from photo/AI (design #5.2, #19)."""

    NONE = "none"
    IN_TRAINING = "in_training"
    WORKING = "working"
    UNKNOWN = "unknown"


class PersistencePermission(StrEnum):
    ALLOWED = "allowed"
    RESTRICTED = "restricted"
    FORBIDDEN = "forbidden"


class RuleConditionType(StrEnum):
    """Frozen first-version condition set (design #11)."""

    LEASH_REQUIRED = "leash_required"
    MUZZLE_REQUIRED = "muzzle_required"
    CARRIER_REQUIRED = "carrier_required"
    STROLLER_REQUIRED = "stroller_required"
    NO_GROUND = "no_ground"
    REGISTRATION_REQUIRED = "registration_required"
    VACCINATION_REQUIRED = "vaccination_required"
    MAX_WEIGHT_KG = "max_weight_kg"
    MIN_WEIGHT_KG = "min_weight_kg"
    MAX_SHOULDER_HEIGHT_CM = "max_shoulder_height_cm"
    MAX_COUNT = "max_count"
    RESERVATION_REQUIRED = "reservation_required"
    ADVANCE_NOTICE_REQUIRED = "advance_notice_required"
    DESIGNATED_ENTRANCE = "designated_entrance"
    DESIGNATED_ELEVATOR = "designated_elevator"
    DESIGNATED_ROUTE = "designated_route"
    TIME_WINDOWS = "time_windows"
    DATE_WINDOWS = "date_windows"
    SEASON = "season"
    FEE = "fee"
    ROOM_RESTRICTION = "room_restriction"
    OTHER_STRUCTURED_NOTE = "other_structured_note"


# ---------------------------------------------------------------------------
# v0.9-R1 Reality Layer (design v0.9 §7) — parallel fact, never normative
#
# Reality = what is *observed* on site. ObservedPresence / StaffResponse /
# AnimalFacility are parallel facts: they co-exist with rules, never mutate
# them, and never feed the deterministic evaluator.
# ---------------------------------------------------------------------------


class RealityCandidateType(StrEnum):
    """What kind of reality fact a candidate carries (single-table subtype)."""

    OBSERVED_PRESENCE = "observed_presence"
    STAFF_RESPONSE = "staff_response"
    ANIMAL_FACILITY = "animal_facility"


class RealityDecision(StrEnum):
    """Human reality-review decision — VERIFIED is human-only, never AI (v0.9 §7.4)."""

    VERIFIED = "verified"
    VERIFIED_WITH_NOTE = "verified_with_note"
    HOLD = "hold"
    REJECTED = "rejected"


#: Decisions that make a reality candidate publishable as a RealityClaim.
REALITY_VERIFIED_DECISIONS: frozenset[str] = frozenset(
    {RealityDecision.VERIFIED.value, RealityDecision.VERIFIED_WITH_NOTE.value}
)


class RealityFreshnessState(StrEnum):
    """Age bucket of a reality fact (v0.9 §7.5).

    ``EXPIRED_FOR_SUMMARY`` means the fact must be excluded from any "recent"
    consumer summary. It is NOT "no animal" — absence of a record is never
    evidence of absence.
    """

    FRESH = "fresh"
    RECENT = "recent"
    AGING = "aging"
    HISTORICAL = "historical"
    EXPIRED_FOR_SUMMARY = "expired_for_summary"


class ObservedAction(StrEnum):
    """Observable actions of an animal at a place (v0.9 §7.1)."""

    ENTERED = "entered"
    PRESENT = "present"
    STAYED = "stayed"
    DINED_NEAR_TABLE = "dined_near_table"
    ON_CUSTOMER_SEAT = "on_customer_seat"
    ON_TABLE_SURFACE = "on_table_surface"
    NEAR_FOOD_SERVICE = "near_food_service"
    IN_SELF_SERVICE_FOOD_AREA = "in_self_service_food_area"
    LEASHED = "leashed"
    OFF_LEASH = "off_leash"
    IN_CARRIER = "in_carrier"
    IN_STROLLER = "in_stroller"


class StaffActorRole(StrEnum):
    """Role of the staff member — role only, never personal identity (v0.9 §7.2)."""

    OWNER = "owner"
    MANAGER = "manager"
    FRONTLINE_STAFF = "frontline_staff"
    SERVER = "server"
    SECURITY = "security"
    CLEANING_STAFF = "cleaning_staff"
    FRONT_DESK = "front_desk"
    UNKNOWN_STAFF = "unknown_staff"


class StaffResponseAction(StrEnum):
    """What staff actually did in a concrete event — never an attitude score.

    A StaffResponseObservation documents one behaviour; it is NOT an operator
    policy, and repeated observations never become rules.
    """

    PROACTIVE_ACCOMMODATION = "proactive_accommodation"
    PROVIDE_WATER = "provide_water"
    PROVIDE_CONTAINER_OR_STROLLER = "provide_container_or_stroller"
    DIRECT_TO_ALLOWED_ZONE = "direct_to_allowed_zone"
    REMIND_LEASH = "remind_leash"
    REQUIRE_CARRIER = "require_carrier"
    REQUEST_RELOCATION = "request_relocation"
    REQUEST_WAIT_OUTSIDE = "request_wait_outside"
    DENY_ENTRY = "deny_entry"
    REQUEST_EXIT = "request_exit"
    POLICY_EXPLANATION = "policy_explanation"
    ESCALATE_TO_MANAGER = "escalate_to_manager"
    NO_INTERVENTION_OBSERVED = "no_intervention_observed"
    UNKNOWN = "unknown"


class AnimalFacilityType(StrEnum):
    """Physical animal-related facility at a place (v0.9 §7.3).

    A facility being present NEVER implies an entry policy: an outdoor holding
    cage does not mean "indoor pets prohibited".
    """

    OUTDOOR_HOLDING_CAGE = "outdoor_holding_cage"
    KENNEL = "kennel"
    TETHER_POINT = "tether_point"
    PET_WAITING_AREA = "pet_waiting_area"
    PET_PARKING = "pet_parking"
    WATER_BOWL = "water_bowl"
    PET_STROLLER = "pet_stroller"
    CARRIER_STORAGE = "carrier_storage"
    PET_ENTRANCE = "pet_entrance"
    PET_ELEVATOR = "pet_elevator"
    DEDICATED_PET_ZONE = "dedicated_pet_zone"
    WASTE_BAG_STATION = "waste_bag_station"
    CLEANING_STATION = "cleaning_station"
    WASHING_POINT = "washing_point"
    DEDICATED_PET_TABLEWARE = "dedicated_pet_tableware"
    OTHER = "other"


class FacilityOperationalState(StrEnum):
    """Operational status of a facility (v0.9 §7.3)."""

    ACTIVE = "active"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    REMOVED = "removed"
    UNKNOWN = "unknown"


class FacilityAccessMode(StrEnum):
    """Who may use the facility (v0.9 §7.3)."""

    OPERATOR_PROVIDED = "operator_provided"
    SELF_SERVICE = "self_service"
    STAFF_ASSISTED = "staff_assisted"
    UNKNOWN = "unknown"


class RealityVerificationStatus(StrEnum):
    """Verification posture of a published reality claim (v0.9 §7.4).

    Consumer-visible reality claims must carry Evidence + Review + Freshness;
    this status tracks how far the review went. ``DERIVED_AI_ONLY`` marks
    extraction that must still pass human review before becoming visible.
    """

    HUMAN_VERIFIED = "human_verified"
    HUMAN_VERIFIED_WITH_NOTE = "human_verified_with_note"
    DERIVED_AI_ONLY = "derived_ai_only"
    UNVERIFIED = "unverified"


# ---------------------------------------------------------------------------
# v0.9-R1 Reality Contribution deepening (goal addendum, 2026-09-22) —
# RealityReport parent + ten new state models. All additive.
# ---------------------------------------------------------------------------


class ObservationOrigin(StrEnum):
    """Where a reality report came from (addendum PHASE 4).

    The UI never exposes this technical enum; it drives how strongly the
    report's time/place evidence may be trusted downstream.
    """

    ON_SITE_NOW = "on_site_now"  # user is currently on site
    ON_SITE_PAST = "on_site_past"  # user was there before, reporting late
    EXTERNAL_ONLINE_CONTENT = "external_online_content"  # seen on social/web
    OPERATOR_PROVIDED = "operator_provided"  # submitted by the venue itself
    OFFICIAL_PUBLIC_CONTENT = "official_public_content"  # official public video/notice


class PlaceMatchState(StrEnum):
    """Precision of the place match for a report (addendum PHASE 5).

    ``PARENT_PLACE_ONLY`` means we know the container (e.g. a mall) but not the
    exact tenant — this must never be presented as a whole-venue fact.
    """

    EXACT_PLACE = "exact_place"
    EXACT_SUBPLACE = "exact_subplace"
    PARENT_PLACE_ONLY = "parent_place_only"
    AREA_ONLY = "area_only"
    UNRESOLVED = "unresolved"
    CONFLICTED = "conflicted"


class PlaceMatchEvidenceType(StrEnum):
    """Evidence kinds that justify a place match (addendum PHASE 5, ≥6 kinds)."""

    GPS_PROXIMITY = "gps_proximity"
    POI_METADATA = "poi_metadata"
    VIDEO_CHECK_IN = "video_check_in"
    OCR_TEXT = "ocr_text"
    ADDRESS_TEXT = "address_text"
    USER_CONFIRMATION = "user_confirmation"
    OPERATOR_METADATA = "operator_metadata"
    SOURCE_URL = "source_url"


class TimeEvidenceState(StrEnum):
    """Precision of *when* the event happened (addendum PHASE 6).

    Publication time is never automatically treated as event time: a video
    published on 9-20 must be described as "observed in a video published on
    9-20", never "present on site on 9-20", unless event time is separately
    evidenced.
    """

    LIVE_DEVICE_TIME = "live_device_time"
    EXACT_EVENT_TIME = "exact_event_time"
    EXACT_EVENT_DATE = "exact_event_date"
    APPROXIMATE_DATE = "approximate_date"
    PUBLICATION_TIME_ONLY = "publication_time_only"
    UNKNOWN = "unknown"


class TimeCertainty(StrEnum):
    """Separate certainty axis for the claimed event time."""

    EXACT = "exact"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


class FactEvidenceState(StrEnum):
    """Multi-axis evidence classification — never a single "credibility 87" (addendum PHASE 7)."""

    DIRECT_MEDIA = "direct_media"  # first-party raw media captured by the reporter
    FIRST_HAND_NO_MEDIA = "first_hand_no_media"  # first-hand account, no media
    EXTERNAL_MEDIA = "external_media"  # media from an external post/video
    TEXT_ONLY_EXTERNAL = "text_only_external"  # external post, text only
    OPERATOR_STATEMENT = "operator_statement"  # venue operator statement
    OFFICIAL_STATEMENT = "official_statement"  # official public statement
    INFERRED_FROM_CONTEXT = "inferred_from_context"  # contextual inference
    INSUFFICIENT = "insufficient"


class ObservationEffortDurationBucket(StrEnum):
    """How long the observer was on site (addendum PHASE 8)."""

    LT_10_MIN = "lt_10_min"
    MIN_10_30 = "min_10_30"
    MIN_30_120 = "min_30_120"
    GT_120_MIN = "gt_120_min"
    UNKNOWN = "unknown"


class StaffAwarenessState(StrEnum):
    """Whether staff were *observed* to be aware of the animal (addendum PHASE 9).

    Only ``AWARENESS_CONFIRMED`` combined with a no-intervention response action
    may be phrased as "staff saw it and did not intervene further"; everything
    else stays "no staff intervention was observed in this record".
    """

    AWARENESS_CONFIRMED = "awareness_confirmed"
    AWARENESS_LIKELY = "awareness_likely"
    AWARENESS_UNKNOWN = "awareness_unknown"


class FacilityPurposeState(StrEnum):
    """How confidently the purpose of a facility is established (addendum PHASE 10).

    A cage photographed outside a shop with no sign and no staff statement must
    stay "疑似动物安置设施，用途待核验" — never "confirmed outdoor holding cage".
    """

    PURPOSE_CONFIRMED = "purpose_confirmed"
    PURPOSE_STAFF_STATED = "purpose_staff_stated"
    PURPOSE_SIGNAGE_SUPPORTED = "purpose_signage_supported"
    PURPOSE_USER_INFERRED = "purpose_user_inferred"
    PURPOSE_UNKNOWN = "purpose_unknown"


class RealityConfirmationType(StrEnum):
    """Lightweight on-site confirmation of a published reality fact (addendum PHASE 11).

    A confirmation is evidence, never a deletion: ``NOT_SEEN_NOW`` adds a new
    observation and must NOT remove the older one.
    """

    STILL_PRESENT = "still_present"
    NOT_SEEN_NOW = "not_seen_now"
    FACILITY_STILL_PRESENT = "facility_still_present"
    FACILITY_REMOVED = "facility_removed"
    SIGN_STILL_PRESENT = "sign_still_present"
    SIGN_CHANGED = "sign_changed"


class RealityReportPrivacyState(StrEnum):
    """Media/report privacy (addendum P7: media is private by default)."""

    PRIVATE = "private"
    PUBLIC = "public"
    RESTRICTED = "restricted"


class RealityReportModerationState(StrEnum):
    """Moderation posture of a report (addendum PHASE 12–13 Anti-Abuse)."""

    PENDING = "pending"
    FLAGGED = "flagged"
    APPROVED = "approved"
    REJECTED = "rejected"
    REMOVED = "removed"


class ExternalContentPlatform(StrEnum):
    """Platform of an external online content source (addendum P8)."""

    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    DIANPING = "dianping"
    WEIBO = "weibo"
    BILIBILI = "bilibili"
    WEB = "web"
    OTHER = "other"


class ContributionAbuseFlag(StrEnum):
    """Anti-abuse flags attached to a report (addendum PHASE 13)."""

    NONE = "none"
    RATE_LIMITED = "rate_limited"
    DUPLICATE = "duplicate"
    NEAR_DUPLICATE = "near_duplicate"
    SPAM = "spam"
    PLACE_MISMATCH = "place_mismatch"
    OLD_VIDEO = "old_video"
    RECYCLED_CONTENT = "recycled_content"
    MEDIA_MANIPULATION = "media_manipulation"
    MALICIOUS_MASS_REPORT = "malicious_mass_report"
