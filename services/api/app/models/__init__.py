"""Entity registry: importing this module registers all tables on Base.metadata."""

from .civic import AuditLog, DisputeCase, JurisdictionRule, WatchSubscription
from .media import MediaObject
from .observation import ObservationClaim, VerificationEvent
from .place import ExternalPlaceRef, Operator, OperatorClaim, Place, PlaceGeometry, Zone
from .rule import AccessRule, RuleCondition, Source
from .user import PetProfile, User
from .v05 import (
    AccessPath,
    Amenity,
    BoundaryPreference,
    BoundaryProfile,
    CoexistencePolicy,
    DataLicense,
    DataSourceJob,
    Entrance,
    EventPolicy,
    FreshnessPolicy,
    Organization,
    PlacePolicyBinding,
    PolicyTemplate,
    PolicyTemplateRule,
    RuleCandidate,
    SourceMonitor,
)

__all__ = [
    "AccessPath",
    "AccessRule",
    "Amenity",
    "AuditLog",
    "BoundaryPreference",
    "BoundaryProfile",
    "CoexistencePolicy",
    "DataLicense",
    "DataSourceJob",
    "DisputeCase",
    "Entrance",
    "EventPolicy",
    "ExternalPlaceRef",
    "FreshnessPolicy",
    "Organization",
    "PlacePolicyBinding",
    "PolicyTemplate",
    "PolicyTemplateRule",
    "RuleCandidate",
    "SourceMonitor",
    "JurisdictionRule",
    "MediaObject",
    "ObservationClaim",
    "Operator",
    "OperatorClaim",
    "PetProfile",
    "Place",
    "PlaceGeometry",
    "RuleCondition",
    "Source",
    "User",
    "VerificationEvent",
    "WatchSubscription",
    "Zone",
]
