"""Reality Audit engine + API (REALITY_AUDIT_PLAN, NEXT_GOAL §C2).

The engine must be pure, surface schema gaps instead of dropping them, and
refuse nothing about samples it cannot map — every unknown becomes a reported
gap, never a silent invention.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from app.tools.reality_audit import (
    audit_samples,
    ingest_csv,
    ingest_json,
    render_provenance,
    render_report,
    render_schema_gaps,
)

REPO_DOCS = Path(__file__).resolve().parents[2] / "docs" / "reality_audit"
NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)


def _sample(**overrides):
    base = {
        "sample_id": "t-1",
        "place": {
            "canonical_name": "样板·测试（虚构）",
            "place_type": "cafe",
            "location_wkt": "POINT(122.5 30.5)",
        },
        "zones": [{"zone_key": "indoor", "name": "室内"}],
        "sources": [
            {
                "source_key": "s1",
                "source_type": "onsite_signage",
                "issuer": "样牌",
                "last_verified_at": "2026-09-01T00:00:00+00:00",
            }
        ],
        "rules": [
            {
                "rule_id": "r1",
                "zone_key": "indoor",
                "animal_scope": "ordinary_pet",
                "action": "enter",
                "effect": "prohibited",
                "rule_layer": "OPERATOR_POLICY",
                "conditions": [],
            }
        ],
        "coexistence": [],
        "queries": [
            {"animal": "dog", "service_role": "none", "action": "enter", "zone_key": "indoor"}
        ],
        "boundary_preferences": [],
    }
    base.update(overrides)
    return base


def test_expressible_sample_passes():
    result = audit_samples([_sample()], now=NOW)
    s = result["samples"][0]
    assert s["expressible"] is True
    assert result["expressible_count"] == 1
    assert s["resolver_results"][0]["effect"] == "prohibited"
    assert s["resolver_results"][0]["compliance_state"] == "CONSISTENT"


def test_note_only_condition_becomes_schema_gap_not_silence():
    """note-only 条件必须进 unsupported_conditions 与全局 gap 注册表。"""
    sample = _sample()
    sample["rules"][0]["conditions"] = [{"condition_type": "use_pet_elevator", "value_flag": True}]
    result = audit_samples([sample], now=NOW)
    s = result["samples"][0]
    assert s["expressible"] is False
    assert s["unsupported_conditions"][0]["condition_type"] == "use_pet_elevator"
    kinds = [g["kind"] for g in result["schema_gaps"]]
    assert "note_only_condition" in kinds


def test_unknown_fields_and_attributes_reported():
    sample = _sample(typo_key=1)
    sample["coexistence"] = [{"attribute": "pet_swimming_pool", "value": "available"}]
    sample["boundary_preferences"] = [["pet_swimming_pool", "prefer"]]
    result = audit_samples([sample], now=NOW)
    s = result["samples"][0]
    assert "typo_key" in s["unknown_fields"]
    assert "pet_swimming_pool" in s["unknown_coexistence_attributes"]
    kinds = {g["kind"] for g in result["schema_gaps"]}
    assert "unmodelled_coexistence_attribute" in kinds


def test_invalid_enum_and_source_type_reported():
    sample = _sample()
    sample["rules"][0]["effect"] = "maybe"
    sample["sources"][0]["source_type"] = "social_media_scrape"
    result = audit_samples([sample], now=NOW)
    s = result["samples"][0]
    assert s["expressible"] is False
    assert s["invalid_rules"][0]["field"] == "effect"
    assert s["source_quality"][0]["valid_type"] is False


def test_freshness_stale_flag_but_rule_stays_current():
    """stale 只标记，不反转任何结论（review_due ≠ invalid）。"""
    sample = _sample()
    sample["sources"][0]["last_verified_at"] = "2025-12-01T00:00:00+00:00"
    result = audit_samples([_sample() for _ in range(1)], now=NOW)
    result = audit_samples([sample], now=NOW)
    s = result["samples"][0]
    assert s["source_quality"][0]["stale"] is True
    assert s["resolver_results"][0]["effect"] == "prohibited"


def test_service_dog_isolation_visible_in_audit():
    sample = _sample()
    sample["rules"].append(
        {
            "rule_id": "sd",
            "zone_key": "indoor",
            "animal_scope": "service_dog",
            "action": "enter",
            "effect": "allowed",
            "rule_layer": "OPERATOR_POLICY",
            "conditions": [],
        }
    )
    sample["queries"].append(
        {"animal": "dog", "service_role": "working", "action": "enter", "zone_key": "indoor"}
    )
    result = audit_samples([sample], now=NOW)
    effects = {
        tuple(q["query"].values()): q["effect"] for q in result["samples"][0]["resolver_results"]
    }
    assert "allowed" in effects.values()
    pet_query = next(
        q for q in result["samples"][0]["resolver_results"] if q["query"]["service_role"] == "none"
    )
    assert pet_query["effect"] == "prohibited"


def test_csv_ingest_matches_json_semantics():
    samples = ingest_csv(REPO_DOCS / "import_template.csv")
    assert samples and samples[0]["sample_id"] == "syn-cafe-100"
    assert len(samples[0]["rules"]) == 3
    leash = [
        c for c in samples[0]["rules"][1]["conditions"] if c["condition_type"] == "leash_required"
    ]
    assert leash and leash[0]["value_flag"] is True
    result = audit_samples(samples, now=NOW)
    assert result["samples"][0]["expressible"] is True


def test_json_ingest_template_is_loadable():
    samples = ingest_json(REPO_DOCS / "import_template.json")
    result = audit_samples(samples, now=NOW)
    assert result["sample_count"] == 1
    assert result["expressible_count"] == 1


def test_renderers_contain_real_outputs():
    samples = ingest_json(REPO_DOCS / "synthetic_samples.json")
    result = audit_samples(samples, now=NOW)
    report = render_report(result)
    gaps = render_schema_gaps(result)
    manifest = render_provenance(result, "synthetic_samples.json")
    assert "synthetic adversarial fixtures" in report
    assert result["sample_count"] == 6
    assert "SCHEMA_GAPS" in gaps
    assert manifest["real_place_claims"] == 0
    assert manifest["data_nature"] == "synthetic_adversarial_fixtures"


def test_committed_report_matches_engine():
    """仓库内的报告三件套必须由引擎真实生成（防手写漂移）。"""
    committed = (REPO_DOCS / "provenance_manifest.json").read_text(encoding="utf-8")
    manifest = json.loads(committed)
    assert manifest["tool"] == "app.tools.reality_audit"
    assert manifest["data_nature"] == "synthetic_adversarial_fixtures"
    assert manifest["real_place_claims"] == 0
