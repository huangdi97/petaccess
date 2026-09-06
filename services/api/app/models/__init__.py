"""Entity registry: importing this module registers all tables on Base.metadata."""

from .civic import AuditLog, DisputeCase, JurisdictionRule, WatchSubscription
from .observation import ObservationClaim, VerificationEvent
from .place import ExternalPlaceRef, Operator, OperatorClaim, Place, PlaceGeometry, Zone
from .rule import AccessRule, RuleCondition, Source
from .user import PetProfile, User

__all__ = [
    "AccessRule",
    "AuditLog",
    "DisputeCase",
    "ExternalPlaceRef",
    "JurisdictionRule",
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
