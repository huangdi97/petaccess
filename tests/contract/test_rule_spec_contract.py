"""Contract tests: evaluator output conforms to packages/rule-spec JSON Schemas,
and rule-spec fixtures produce the expected statuses."""

import json
from datetime import datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from app.rulespec.evaluator import evaluate
from app.rulespec.model import AnimalInput, Condition, QueryContext, Rule, RuleAction

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "packages" / "rule-spec" / "schemas"
FIXTURE_DIR = REPO_ROOT / "packages" / "rule-spec" / "fixtures"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _validators() -> dict[str, Draft202012Validator]:
    """Schemas cross-reference each other via $ref, so register them on a registry."""
    from referencing import Registry, Resource

    registry: Registry = Registry()
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(schema)
        uri = schema["$id"]
        registry = registry.with_resource(uri, resource)
    return {
        path.name: Draft202012Validator(
            json.loads(path.read_text(encoding="utf-8")), registry=registry
        )
        for path in SCHEMA_DIR.glob("*.schema.json")
    }


@pytest.fixture(scope="module")
def vals() -> dict[str, Draft202012Validator]:
    return _validators()


def test_schemas_are_valid_json_schema(vals):
    for name, v in vals.items():
        v.check_schema(json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8")))


def test_fixture_cafe_scenarios(vals):
    fixture = json.loads((FIXTURE_DIR / "cafe_indoor_outdoor.json").read_text(encoding="utf-8"))
    rules = [
        Rule(
            id=r["id"],
            animal_scope=r["animal_scope"],
            action=RuleAction(r["action"]),
            effect=r["effect"],
            status=r["status"],
            zone_id=r.get("zone_id"),
            place_id=r.get("place_id"),
            conditions=tuple(
                Condition(
                    condition_type=c["condition_type"],
                    value_flag=c.get("value_flag"),
                    value_numeric=c.get("value_numeric"),
                    value_text=c.get("value_text"),
                    value_json=c.get("value_json"),
                )
                for c in r.get("conditions", [])
            ),
            source_id=r.get("source_id"),
        )
        for r in fixture["rules"]
    ]
    result_schema = vals["applicability-result.schema.json"]
    for scenario in fixture["queries"]:
        q = scenario["query"]
        ctx = QueryContext(
            animal=AnimalInput(**q["animal"]),
            place_id=q["place_id"],
            zone_id=q.get("zone_id"),
            date_time=datetime.fromisoformat(q["date_time"]),
            intended_action=RuleAction(q["intended_action"]),
        )
        result = evaluate(ctx, rules)
        # structural contract: result must validate against applicability-result schema
        result_dict = {
            "status": result.status.value,
            "matched_rules": result.matched_rules,
            "unmet_conditions": [
                {"rule_id": u.rule_id, "condition_type": u.condition_type, "kind": u.kind}
                for u in result.unmet_conditions
            ],
            "unknown_inputs": [
                {"input": u.input, "reason": u.reason} for u in result.unknown_inputs
            ],
            "reason_codes": result.reason_codes,
            "source_refs": result.source_refs,
        }
        errors = list(result_schema.iter_errors(result_dict))
        assert not errors, f"{scenario['name']}: {errors}"
        assert result.status.value == scenario["expected_status"], scenario["name"]
