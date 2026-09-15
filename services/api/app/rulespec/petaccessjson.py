"""PetAccessJSON v0.1 (NEXT_GOAL §B16): unified internal JSON interchange for
import/export/test fixtures. Not a public API yet.

Schema mirrors schemas/petaccessjson-0.1.example.json; `petaccessjson_version`
is pinned to "0.1". Loaders validate strictly and never guess missing fields.
"""

from __future__ import annotations

from typing import Any

PETACCESSJSON_VERSION = "0.1"

REQUIRED_KEYS = ("subject", "scope", "action", "effect", "rule_layer", "validity", "source")
VALID_LAYERS = {"LEGAL", "REGULATORY_GUIDANCE", "OPERATOR_POLICY", "TEMPORARY_POLICY"}
VALID_EFFECTS = {"allowed", "prohibited", "conditional"}
VALID_SPECIES = {"dog", "cat", "other"}
VALID_ROLES = {"ordinary_pet", "service_dog"}
VALID_EXCEPT_SCOPES = {"dog", "cat", "ordinary_pet", "service_dog", "other"}
#: normative force (ADR-023). "discretionary" is the tolerated legacy spelling.
VALID_MANDATORY_LEVELS = {"mandatory", "advisory", "operator_discretion", "discretionary"}


class PetAccessJSONError(ValueError):
    pass


def dump(
    *,
    species: str,
    role: str,
    place_id: str,
    zone_id: str | None,
    action: str,
    effect: str,
    rule_layer: str,
    conditions: list[dict] | None = None,
    effective_from: str | None = None,
    effective_to: str | None = None,
    source_id: str,
    verified_at: str | None = None,
    exceptions: list[dict[str, Any]] | None = None,
    mandatory_level: str | None = None,
) -> dict[str, Any]:
    if rule_layer not in VALID_LAYERS:
        raise PetAccessJSONError(f"invalid rule_layer {rule_layer}")
    if effect not in VALID_EFFECTS:
        raise PetAccessJSONError(f"invalid effect {effect}")
    if mandatory_level is not None and mandatory_level not in VALID_MANDATORY_LEVELS:
        raise PetAccessJSONError(f"invalid mandatory_level {mandatory_level}")
    if rule_layer == "LEGAL" and mandatory_level is None:
        # a legal rule must declare its force: the resolver never guesses
        # (ADR-023 / BLK-LAYER-02)
        raise PetAccessJSONError("LEGAL rule requires mandatory_level")
    doc = {
        "petaccessjson_version": PETACCESSJSON_VERSION,
        "subject": {"species": species, "role": role},
        "scope": {"place_id": place_id, "zone_id": zone_id},
        "action": action,
        "effect": effect,
        "rule_layer": rule_layer,
        "mandatory_level": mandatory_level,
        "conditions": conditions or [],
        "validity": {"effective_from": effective_from, "effective_to": effective_to},
        "source": {"source_id": source_id, "verified_at": verified_at},
    }
    if exceptions:
        doc["exceptions"] = exceptions
    return doc


def load(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise PetAccessJSONError("document must be an object")
    version = data.get("petaccessjson_version")
    if version != PETACCESSJSON_VERSION:
        raise PetAccessJSONError(f"unsupported petaccessjson_version {version!r}")
    for key in REQUIRED_KEYS:
        if key not in data:
            raise PetAccessJSONError(f"missing required key: {key}")
    subject = data["subject"] or {}
    if subject.get("species") not in VALID_SPECIES:
        raise PetAccessJSONError("invalid subject.species")
    if subject.get("role") not in VALID_ROLES:
        raise PetAccessJSONError("invalid subject.role")
    if data["effect"] not in VALID_EFFECTS:
        raise PetAccessJSONError("invalid effect")
    if data["rule_layer"] not in VALID_LAYERS:
        raise PetAccessJSONError("invalid rule_layer")
    mandatory_level = data.get("mandatory_level")
    if mandatory_level is not None and mandatory_level not in VALID_MANDATORY_LEVELS:
        raise PetAccessJSONError("invalid mandatory_level")
    if data["rule_layer"] == "LEGAL" and mandatory_level is None:
        raise PetAccessJSONError("LEGAL rule requires mandatory_level")
    scope = data["scope"] or {}
    if not scope.get("place_id"):
        raise PetAccessJSONError("scope.place_id required")
    exceptions = data.get("exceptions")
    if exceptions is not None:
        if not isinstance(exceptions, list):
            raise PetAccessJSONError("exceptions must be a list")
        for exc in exceptions:
            if not isinstance(exc, dict):
                raise PetAccessJSONError("exception must be an object")
            if exc.get("animal_scope") not in VALID_EXCEPT_SCOPES:
                raise PetAccessJSONError("invalid exception.animal_scope")
            if exc.get("effect") not in VALID_EFFECTS:
                raise PetAccessJSONError("invalid exception.effect")
            if not exc.get("source_id"):
                # an exception without provenance is invalid, never guessed
                raise PetAccessJSONError("exception.source_id required")
    return data
