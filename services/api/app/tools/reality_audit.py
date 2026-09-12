"""Reality Audit engine (REALITY_AUDIT_PLAN, NEXT_GOAL §C2).

Answers one question per submitted place sample: **can our model express the
real world we captured?** The engine is pure (no DB, no LLM, no I/O) so the
CLI and the admin API run the identical code path.

Per sample it reports:
- expressible — every rule maps to valid enums and every condition type is
  either enforced (obligation/threshold/temporal) or explicitly note-only
- unsupported_conditions — conditions the schema cannot enforce (schema-gap
  candidates, never silently dropped)
- unknown_fields — input keys outside the audit schema (typo/drift detector)
- source_quality — source_type validity, verification, licence posture
- freshness — days since last verification against STALE_DAYS (review hint,
  never an invalidation: review_due ≠ invalid)
- resolver result / boundary result — the real resolver and matcher outputs
- schema_gaps — aggregated, de-duplicated gap candidates

Phase 1 input is adversarial **synthetic** samples only; the tool refuses to
fabricate real-merchant rules (REALITY_AUDIT_PLAN 第二阶段 needs lawful real
material, not invented data).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from app.models.enums import SourceType
from app.rulespec.evaluator import _OBLIGATION_CONDITIONS, _THRESHOLD_CONDITIONS
from app.rulespec.model import AnimalScope, RuleAction, RuleEffect
from app.rulespec.v05_resolver import RuleLayer
from app.services.answerability import STALE_DAYS

TEMPORAL_CONDITIONS = {"time_windows", "date_windows"}

#: attributes the product models today (NEXT_GOAL §B7 first batch + boundary)
KNOWN_COEXISTENCE_ATTRIBUTES = {
    "ordinary_pet_indoor_dining",
    "ordinary_pet_outdoor_dining",
    "animal_on_customer_seat",
    "animal_on_table_surface",
    "animal_near_food_service_area",
    "animal_in_self_service_food_area",
    "animal_use_customer_tableware",
    "dedicated_pet_tableware_available",
    "dedicated_pet_zone_available",
    "zone_separation_type",
    "ordinary_pet_entry",
}

_SAMPLE_KEYS = {
    "sample_id",
    "note",
    "place",
    "zones",
    "sources",
    "rules",
    "coexistence",
    "queries",
    "boundary_preferences",
}
_PLACE_KEYS = {"canonical_name", "place_type", "location_wkt"}
_ZONE_KEYS = {"zone_key", "name"}
_SOURCE_KEYS = {
    "source_key",
    "source_type",
    "issuer",
    "last_verified_at",
    "display_allowed",
    "redistribution_allowed",
    "storage_allowed",
}
_RULE_KEYS = {
    "rule_id",
    "zone_key",
    "animal_scope",
    "action",
    "effect",
    "rule_layer",
    "mandatory_level",
    "conditions",
    "source_key",
    "origin",
    "effective_from",
    "effective_to",
    "status",
    "note",
}
_COEXISTENCE_KEYS = {"zone_key", "attribute", "value"}
_QUERY_KEYS = {"animal", "service_role", "action", "zone_key"}

_SCOPE_VALUES = {s.value for s in AnimalScope}
_ACTION_VALUES = {a.value for a in RuleAction}
_EFFECT_VALUES = {e.value for e in RuleEffect}
_LAYER_VALUES = {ly.value for ly in RuleLayer}
_SOURCE_TYPE_VALUES = {s.value for s in SourceType}


def _condition_class(condition_type: str) -> str:
    """enforced | note_only | unknown."""
    if (
        condition_type in _OBLIGATION_CONDITIONS
        or condition_type in _THRESHOLD_CONDITIONS
        or condition_type in TEMPORAL_CONDITIONS
    ):
        return "enforced"
    return "note_only"


def _unknown_keys(payload: dict, allowed: set[str]) -> list[str]:
    return sorted(set(payload) - allowed)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def audit_samples(samples: list[dict], now: datetime | None = None) -> dict:
    """Run the full audit over samples; returns a JSON-serialisable dict."""
    now = now or datetime.now(UTC)
    per_sample: list[dict] = []
    gap_registry: dict[str, dict] = {}

    for sample in samples:
        per_sample.append(_audit_one(sample, now, gap_registry))

    expressible_count = sum(1 for s in per_sample if s["expressible"])
    return {
        "audited_at": now.isoformat(),
        "sample_count": len(samples),
        "expressible_count": expressible_count,
        "non_expressible_count": len(per_sample) - expressible_count,
        "samples": per_sample,
        "schema_gaps": sorted(gap_registry.values(), key=lambda g: g["kind"] + g["detail"]),
    }


def _audit_one(sample: dict, now: datetime, gap_registry: dict) -> dict:
    sample_id = sample.get("sample_id", "<missing>")
    gaps: list[dict] = []

    unknown_fields = _unknown_keys(sample, _SAMPLE_KEYS)
    if unknown_fields:
        gaps.append({"kind": "unknown_input_field", "detail": f"{sample_id}: {unknown_fields}"})

    zones = {z.get("zone_key"): z.get("name") for z in sample.get("zones", []) if z.get("zone_key")}
    sources = {s.get("source_key"): s for s in sample.get("sources", []) if s.get("source_key")}

    # --- rules ---------------------------------------------------------------
    unsupported_conditions: list[dict] = []
    invalid_rules: list[dict] = []
    layer_rules: dict[str, list] = {
        "LEGAL": [],
        "REGULATORY_GUIDANCE": [],
        "OPERATOR_POLICY": [],
        "TEMPORARY_POLICY": [],
    }
    for rule in sample.get("rules", []):
        rid = rule.get("rule_id", "<missing>")
        unknown_fields += [f"rules.{rid}.{k}" for k in _unknown_keys(rule, _RULE_KEYS)]
        bad = False
        for field, valid in (
            ("animal_scope", _SCOPE_VALUES),
            ("action", _ACTION_VALUES),
            ("effect", _EFFECT_VALUES),
        ):
            if rule.get(field) not in valid:
                invalid_rules.append({"rule_id": rid, "field": field, "value": rule.get(field)})
                bad = True
        layer = rule.get("rule_layer")
        if layer is not None and layer not in _LAYER_VALUES:
            invalid_rules.append({"rule_id": rid, "field": "rule_layer", "value": layer})
            bad = True
            layer = "OPERATOR_POLICY"
        for cond in rule.get("conditions", []):
            ctype = cond.get("condition_type", "")
            klass = _condition_class(ctype)
            if klass == "note_only":
                unsupported_conditions.append({"rule_id": rid, "condition_type": ctype})
                key = ("note_only_condition", ctype)
                if key not in gap_registry:
                    gap_registry[key] = {
                        "kind": "note_only_condition",
                        "detail": f"condition_type `{ctype}` is recorded but never enforced",
                        "samples": [],
                    }
                gap_registry[key]["samples"].append(sample_id)
        if not bad:
            # invalid rules are reported above but excluded from resolution so
            # one malformed rule cannot crash the audit or fabricate a verdict
            layer_rules.setdefault(layer or "OPERATOR_POLICY", []).append(rule)

    # --- coexistence ---------------------------------------------------------
    unknown_attributes: list[str] = []
    coexistence_map: dict[str, str] = {}
    for entry in sample.get("coexistence", []):
        attr = entry.get("attribute", "")
        unknown_fields += [f"coexistence.{k}" for k in _unknown_keys(entry, _COEXISTENCE_KEYS)]
        if attr not in KNOWN_COEXISTENCE_ATTRIBUTES:
            unknown_attributes.append(attr)
            key = ("unmodelled_coexistence_attribute", attr)
            if key not in gap_registry:
                gap_registry[key] = {
                    "kind": "unmodelled_coexistence_attribute",
                    "detail": f"attribute `{attr}` has no structured home",
                    "samples": [],
                }
            gap_registry[key]["samples"].append(sample_id)
        else:
            coexistence_map[attr] = entry.get("value", "")

    # --- resolver per query ---------------------------------------------------
    queries_out = []
    for query in sample.get("queries", []):
        unknown_fields += [f"queries.{k}" for k in _unknown_keys(query, _QUERY_KEYS)]
        eff = _resolve_query(sample, query, layer_rules, zones)
        queries_out.append(
            {
                "query": query,
                "effect": eff.effect,
                "compliance_state": eff.compliance_state.value,
                "applicable": [r.id for r in eff.applicable_rules],
                "suppressed": [r[0].id for r in eff.suppressed_rules],
                "conflicts": len(eff.unresolved_conflicts),
                "steps": eff.explanation_steps,
            }
        )

    # --- boundary -------------------------------------------------------------
    preferences = [tuple(p) for p in sample.get("boundary_preferences", [])]
    boundary_rows = []
    if preferences or coexistence_map:
        from app.rulespec.v05_boundary import match as boundary_match

        overall = queries_out[0]["effect"] if queries_out else "unknown"
        results = boundary_match(
            effective_effect=overall, coexistence=coexistence_map, preferences=preferences
        )
        boundary_rows = [
            {"attribute": r.attribute, "stance": r.stance, "verdict": r.verdict, "reason": r.reason}
            for r in results
        ]
        for r in results:
            if r.attribute not in KNOWN_COEXISTENCE_ATTRIBUTES:
                key = ("boundary_attribute_unknown", r.attribute)
                if key not in gap_registry:
                    gap_registry[key] = {
                        "kind": "boundary_attribute_unknown",
                        "detail": f"boundary preference `{r.attribute}` resolves UNKNOWN "
                        "(no structured source)",
                        "samples": [],
                    }
                gap_registry[key]["samples"].append(sample_id)

    # --- sources: quality + freshness ----------------------------------------
    sources_out = []
    freshness_flags = []
    for key, src in sources.items():
        stype = src.get("source_type", "")
        valid_type = stype in _SOURCE_TYPE_VALUES
        verified_at = _parse_dt(src.get("last_verified_at"))
        age_days = (now - verified_at).days if verified_at else None
        stale = age_days is None or age_days > STALE_DAYS
        if not valid_type:
            gaps.append({"kind": "invalid_source_type", "detail": f"{sample_id}/{key}: {stype}"})
        sources_out.append(
            {
                "source_key": key,
                "source_type": stype,
                "valid_type": valid_type,
                "age_days": age_days,
                "stale": stale,
                "redistribution_allowed": bool(src.get("redistribution_allowed")),
            }
        )
        if stale:
            freshness_flags.append(key)

    expressible = not (unsupported_conditions or invalid_rules)

    return {
        "sample_id": sample_id,
        "place": sample.get("place", {}),
        "expressible": expressible,
        "unsupported_conditions": unsupported_conditions,
        "invalid_rules": invalid_rules,
        "unknown_fields": sorted(set(unknown_fields)),
        "unknown_coexistence_attributes": sorted(set(unknown_attributes)),
        "source_quality": sources_out,
        "freshness": {"stale_sources": freshness_flags, "stale_days_threshold": STALE_DAYS},
        "resolver_results": queries_out,
        "boundary_results": boundary_rows,
        "schema_gaps": gaps,
    }


def _resolve_query(sample: dict, query: dict, layer_rules: dict, zones: dict):
    from app.rulespec.v05_resolver import LayeredRule, resolve

    def build(rule: dict) -> LayeredRule:
        origin = rule.get("origin") or (
            "legal" if rule.get("rule_layer") == "LEGAL" else "operator_direct"
        )
        return LayeredRule(
            id=rule.get("rule_id", "r"),
            animal_scope=rule.get("animal_scope") or "ordinary_pet",
            action=rule.get("action") or "enter",
            effect=rule.get("effect") or "unknown",
            rule_layer=rule.get("rule_layer"),
            origin=origin,
            conditions=tuple(rule.get("conditions") or ()),
            zone_id=rule.get("zone_key"),
            mandatory_level=rule.get("mandatory_level"),
            effective_from=_parse_dt(rule.get("effective_from")),
            effective_to=_parse_dt(rule.get("effective_to")),
        )

    buckets = {
        "legal": [build(r) for r in layer_rules.get("LEGAL", [])],
        "guidance": [build(r) for r in layer_rules.get("REGULATORY_GUIDANCE", [])],
        "template_rules": [],
        "operator_rules": [build(r) for r in layer_rules.get("OPERATOR_POLICY", [])],
        "event_rules": [build(r) for r in layer_rules.get("TEMPORARY_POLICY", [])],
    }
    return resolve(
        legal=buckets["legal"],
        guidance=buckets["guidance"],
        template_rules=buckets["template_rules"],
        operator_rules=buckets["operator_rules"],
        event_rules=buckets["event_rules"],
        animal=query.get("animal", "dog"),
        service_role=query.get("service_role", "none"),
        action=query.get("action", "enter"),
        zone_id=query.get("zone_key"),
        now=datetime.now(UTC),
    )


# ------------------------------------------------------------------ rendering


_DEFAULT_DATA_NATURE = (
    "synthetic adversarial fixtures only — no real-merchant rule is claimed or "
    "fabricated (REALITY_AUDIT_PLAN 第一阶段)"
)


def render_report(result: dict, data_nature: str | None = None) -> str:
    lines = [
        "# REALITY_AUDIT_REPORT.md",
        "",
        f"- Audited at: {result['audited_at']}",
        f"- Samples: {result['sample_count']} "
        f"(expressible {result['expressible_count']} / "
        f"non-expressible {result['non_expressible_count']})",
        f"- Data nature: **{data_nature or _DEFAULT_DATA_NATURE}**.",
        "",
    ]
    for s in result["samples"]:
        mark = "yes" if s["expressible"] else "NO"
        lines.append(f"## {s['sample_id']} — expressible: {mark}")
        place = s.get("place") or {}
        if place.get("canonical_name"):
            lines.append(f"- place: {place['canonical_name']} ({place.get('place_type', '?')})")
        if s["unsupported_conditions"]:
            lines.append(
                "- unsupported conditions: "
                + ", ".join(
                    f"{c['rule_id']}:{c['condition_type']}" for c in s["unsupported_conditions"]
                )
            )
        if s["invalid_rules"]:
            lines.append(
                "- invalid rules: "
                + ", ".join(
                    f"{c['rule_id']}({c['field']}={c['value']})" for c in s["invalid_rules"]
                )
            )
        if s["unknown_fields"]:
            lines.append(f"- unknown fields: {s['unknown_fields']}")
        for src in s["source_quality"]:
            state = "stale" if src["stale"] else f"{src['age_days']}d"
            lines.append(
                f"- source {src['source_key']}: {src['source_type']} "
                f"(valid={src['valid_type']}, freshness={state}, "
                f"redistribution={src['redistribution_allowed']})"
            )
        for q in s["resolver_results"]:
            lines.append(
                f"- resolver: {q['query']} → effect={q['effect']}, "
                f"compliance={q['compliance_state']}, "
                f"applicable={q['applicable']}, suppressed={q['suppressed']}"
            )
        for b in s["boundary_results"]:
            lines.append(f"- boundary: {b['attribute']} [{b['stance']}] → {b['verdict']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def render_schema_gaps(result: dict) -> str:
    lines = [
        "# SCHEMA_GAPS.md",
        "",
        f"- Generated: {result['audited_at']}",
        "- Source: reality-audit run over synthetic samples. Each entry is a "
        "schema-gap **candidate** observed by the audit engine, not a decision.",
        "",
    ]
    if not result["schema_gaps"]:
        lines.append("No schema gaps observed in this run.\n")
        return "\n".join(lines) + "\n"
    lines.append("| kind | detail | samples |")
    lines.append("|---|---|---|")
    for gap in result["schema_gaps"]:
        detail = gap["detail"].replace("|", "\\|")
        samples = ", ".join(sorted(set(gap.get("samples", []))))
        lines.append(f"| {gap['kind']} | {detail} | {samples} |")
    lines.append("")
    return "\n".join(lines) + "\n"


_ALLOWED_MANIFEST_OVERRIDES = {"data_nature", "real_place_claims", "note"}


def render_provenance(
    result: dict, input_name: str, manifest_override: dict | None = None
) -> dict:
    """Build the provenance manifest.

    Defaults describe synthetic fixtures. A run over REAL captured data must
    declare it explicitly via a `_manifest` block in the input JSON — the
    override is operator-asserted provenance, never inferred. Unknown override
    keys are ignored (typo-safe); `real_place_claims` must stay an int.
    """
    manifest = {
        "manifest_version": "1.0",
        "generated_at": result["audited_at"],
        "input": input_name,
        "data_nature": "synthetic_adversarial_fixtures",
        "real_place_claims": 0,
        "sample_ids": [s["sample_id"] for s in result["samples"]],
        "tool": "app.tools.reality_audit",
        "engine_outputs": ["REALITY_AUDIT_REPORT.md", "SCHEMA_GAPS.md"],
    }
    for key in _ALLOWED_MANIFEST_OVERRIDES:
        if manifest_override and key in manifest_override:
            manifest[key] = manifest_override[key]
    return manifest


def read_manifest_override(path: Path) -> dict | None:
    """Read the optional top-level `_manifest` block from a JSON input."""
    if path.suffix.lower() != ".json":
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("_manifest"), dict):
        override = data["_manifest"]
        return {k: v for k, v in override.items() if k in _ALLOWED_MANIFEST_OVERRIDES}
    return None


# -------------------------------------------------------------------- ingest


def ingest_json(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    samples = data.get("samples") if isinstance(data, dict) else data
    if not isinstance(samples, list):
        raise ValueError("input JSON must be an object with a `samples` list (or a list)")
    return samples


_FLAT_COLUMNS = [
    "sample_id",
    "note",
    "place_name",
    "place_type",
    "location_wkt",
    "zone_key",
    "zone_name",
    "source_key",
    "source_type",
    "issuer",
    "last_verified_at",
    "rule_id",
    "animal_scope",
    "action",
    "effect",
    "rule_layer",
    "mandatory_level",
    "origin",
    "zone_key_rule",
    "condition_type",
    "value_flag",
    "value_numeric",
    "value_text",
    "value_json",
    "coexistence_attribute",
    "coexistence_value",
    "coexistence_zone_key",
    "query_animal",
    "query_service_role",
    "query_action",
    "query_zone_key",
]


def ingest_csv(path: Path) -> list[dict]:
    """Flat CSV (see docs/reality_audit/import_template.csv) → sample list.

    One row per (rule-condition / coexistence entry / query) fragment; blank
    fragments are skipped so a row can carry several concerns.
    """
    by_id: dict[str, dict] = {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            sid = (row.get("sample_id") or "").strip()
            if not sid:
                continue
            sample = by_id.setdefault(
                sid,
                {
                    "sample_id": sid,
                    "note": row.get("note") or None,
                    "place": {
                        "canonical_name": row.get("place_name") or sid,
                        "place_type": row.get("place_type") or "other",
                        "location_wkt": row.get("location_wkt") or None,
                    },
                    "zones": [],
                    "sources": [],
                    "rules": [],
                    "coexistence": [],
                    "queries": [],
                    "boundary_preferences": [],
                },
            )
            if row.get("zone_key") and row.get("zone_name"):
                zone = {"zone_key": row["zone_key"], "name": row["zone_name"]}
                if zone not in sample["zones"]:
                    sample["zones"].append(zone)
            if row.get("source_key"):
                src = {
                    "source_key": row["source_key"],
                    "source_type": row.get("source_type") or "",
                    "issuer": row.get("issuer") or None,
                    "last_verified_at": row.get("last_verified_at") or None,
                }
                if src not in sample["sources"]:
                    sample["sources"].append(src)
            if row.get("rule_id"):
                rule = next((r for r in sample["rules"] if r["rule_id"] == row["rule_id"]), None)
                if rule is None:
                    rule = {
                        "rule_id": row["rule_id"],
                        "zone_key": row.get("zone_key_rule") or None,
                        "animal_scope": row.get("animal_scope") or None,
                        "action": row.get("action") or None,
                        "effect": row.get("effect") or None,
                        "rule_layer": row.get("rule_layer") or None,
                        "mandatory_level": row.get("mandatory_level") or None,
                        "origin": row.get("origin") or None,
                        "conditions": [],
                    }
                    sample["rules"].append(rule)
                if row.get("condition_type"):
                    cond: dict = {"condition_type": row["condition_type"]}
                    if row.get("value_flag"):
                        cond["value_flag"] = row["value_flag"].strip().lower() == "true"
                    if row.get("value_numeric"):
                        cond["value_numeric"] = float(row["value_numeric"])
                    if row.get("value_text"):
                        cond["value_text"] = row["value_text"]
                    if row.get("value_json"):
                        cond["value_json"] = json.loads(row["value_json"])
                    rule["conditions"].append(cond)
            if row.get("coexistence_attribute"):
                sample["coexistence"].append(
                    {
                        "zone_key": row.get("coexistence_zone_key") or None,
                        "attribute": row["coexistence_attribute"],
                        "value": row.get("coexistence_value") or "",
                    }
                )
            if row.get("query_animal"):
                sample["queries"].append(
                    {
                        "animal": row["query_animal"],
                        "service_role": row.get("query_service_role") or "none",
                        "action": row.get("query_action") or "enter",
                        "zone_key": row.get("query_zone_key") or None,
                    }
                )
    return list(by_id.values())


# ---------------------------------------------------------------------- CLI


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.tools.reality_audit",
        description="Reality audit: expressibility + resolver/boundary results + schema gaps",
    )
    parser.add_argument("input", help="input JSON (samples) or flat CSV path")
    parser.add_argument("--out", default=".", help="output directory for the report trio")
    args = parser.parse_args(argv)

    path = Path(args.input)
    samples = ingest_csv(path) if path.suffix.lower() == ".csv" else ingest_json(path)
    manifest_override = read_manifest_override(path)

    result = audit_samples(samples)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_nature = (manifest_override or {}).get("data_nature")
    (out_dir / "REALITY_AUDIT_REPORT.md").write_text(
        render_report(result, data_nature=data_nature), encoding="utf-8"
    )
    (out_dir / "SCHEMA_GAPS.md").write_text(render_schema_gaps(result), encoding="utf-8")
    (out_dir / "provenance_manifest.json").write_text(
        json.dumps(
            render_provenance(result, path.name, manifest_override), ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )

    print(
        f"reality audit: {result['sample_count']} samples, "
        f"{result['expressible_count']} expressible, "
        f"{len(result['schema_gaps'])} schema-gap candidates → {out_dir}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
