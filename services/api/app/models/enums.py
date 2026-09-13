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
    DOG = "dog"
    CAT = "cat"
    ORDINARY_PET = "ordinary_pet"
    SERVICE_DOG = "service_dog"
    OTHER = "other"


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
    MANDATORY = "mandatory"
    ADVISORY = "advisory"
    DISCRETIONARY = "discretionary"


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
