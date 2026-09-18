"""A/B drill for the ADR-030 jurisdiction proviso, against real cloned data.

The Wave01 blocker was: a *new* LEGAL dog prohibition has no per-venue
``rule_exception`` bound to it, so a guide-dog query resolved ``prohibited``
while citing the statute that exempts guide dogs.

This drill reproduces that state deliberately — it drops the five place-scoped
exceptions that already exist in the database, which is exactly the situation a
newly published base is in — and then asks the resolver the same question twice:

    A. with only place-scoped exceptions  → the blocker
    B. plus the activated jurisdiction proviso → the Phase B fix

Both runs use the canonical resolver over real rows; nothing is simulated.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))

from app.core.config import psycopg_url  # noqa: E402
from app.rulespec.v05_resolver import (  # noqa: E402
    LayeredException,
    LayeredRule,
    resolve,
)

NOW = datetime(2026, 9, 18, 12, 0, tzinfo=UTC)


def load(db_name: str) -> dict:
    import psycopg

    url = psycopg_url(f"postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/{db_name}")
    out = {"places": {}, "bases": [], "place_exceptions": [], "provisos": []}
    with psycopg.connect(url) as c, c.cursor() as cur:
        # every LEGAL prohibition, with its place and zone
        cur.execute(
            """
            select ar.id, ar.animal_scope, ar.action, ar.effect, ar.rule_layer,
                   ar.zone_id, ar.source_id, ar.mandatory_level,
                   ar.subject_scope_normalized, ar.normalization_type,
                   p.canonical_name, z.name
            from access_rule ar
            join place p on p.id = ar.place_id
            left join zone z on z.id = ar.zone_id
            where ar.status = 'current'
            order by p.canonical_name, ar.id
            """
        )
        for r in cur.fetchall():
            out["bases"].append(
                LayeredRule(
                    id=r[0],
                    animal_scope=r[1],
                    action=r[2],
                    effect=r[3],
                    rule_layer=r[4],
                    origin="legal" if r[4] == "LEGAL" else "operator_direct",
                    zone_id=r[5],
                    source_id=r[6],
                    mandatory_level=r[7],
                    subject_scope_normalized=r[8],
                    normalization_type=r[9],
                )
            )
            out["places"][r[0]] = (r[10], r[11])
        cur.execute(
            """
            select id, rule_id, animal_scope, effect, source_id, status,
                   subject_scope_normalized, normalization_type, normative_effect, holder_scope
            from rule_exception
            """
        )
        for r in cur.fetchall():
            out["place_exceptions"].append(
                LayeredException(
                    id=r[0],
                    rule_id=r[1],
                    animal_scope=r[2],
                    effect=r[3],
                    source_id=r[4],
                    status=r[5],
                    subject_scope_normalized=r[6],
                    normalization_type=r[7],
                    normative_effect=r[8],
                    holder_scope=r[9],
                )
            )
        cur.execute(
            """
            select id, animal_scope, effect, source_id, status,
                   subject_scope_normalized, normalization_type, normative_effect, holder_scope,
                   binding, instrument_source_ids, applies_to_layer, applies_to_effects
            from jurisdiction_exception
            where status = 'current' and review_status = 'reviewed_active'
            """
        )
        for r in cur.fetchall():
            out["provisos"].append(
                LayeredException(
                    id=r[0],
                    rule_id="",
                    animal_scope=r[1],
                    effect=r[2],
                    source_id=r[3],
                    status=r[4],
                    subject_scope_normalized=r[5],
                    normalization_type=r[6],
                    normative_effect=r[7],
                    holder_scope=r[8],
                    binding=r[9],
                    instrument_source_ids=tuple(r[10] or ()),
                    applies_to_layer=r[11],
                    applies_to_effects=tuple(r[12] or ("prohibited",)),
                )
            )
    return out


def _run(base: LayeredRule, excs: list[LayeredException], *, animal, service_role, declared_role):
    """One resolver call. Exceptions are filtered to the ones claiming this base:
    either it names them, or they bind by instrument (``rule_id == ""``)."""
    return resolve(
        legal=[base],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal=animal,
        service_role=service_role,
        action="enter",
        zone_id=base.zone_id,
        now=NOW,
        exceptions=[e for e in excs if e.rule_id == base.id or e.binding != "rule"],
        declared_role=declared_role,
    )


def probe(data: dict, exceptions: list[LayeredException], *, drop_place_exceptions: bool):
    rows = []
    for base in data["bases"]:
        if base.rule_layer != "LEGAL":
            continue
        place_name, zone_name = data["places"][base.id]
        excs = ([] if drop_place_exceptions else list(data["place_exceptions"])) + list(exceptions)

        ordinary = _run(base, excs, animal="dog", service_role="none", declared_role=None)
        guide = _run(base, excs, animal="dog", service_role="working", declared_role="guide_dog")
        rows.append(
            {
                "place": place_name,
                "zone": zone_name,
                "base_rule": base.id,
                "base_source": base.source_id,
                "ordinary_dog": ordinary.effect,
                "guide_dog": guide.effect,
                "applied": sorted(guide.applied_exceptions),
                "compliance": str(guide.compliance_state),
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-name", default="petaccess_publish_rehearsal_adr030")
    ap.add_argument("--compare-production", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    data = load(args.db_name)

    # A: the Wave01 blocker — a new base has no per-venue exception bound to it
    scenario_a = probe(data, [], drop_place_exceptions=True)
    # B: the Phase B fix — the instrument proviso covers it
    scenario_b = probe(data, data["provisos"], drop_place_exceptions=True)

    report = {
        "db": args.db_name,
        "provisos_loaded": [p.id for p in data["provisos"]],
        "A_place_exceptions_removed_no_proviso": scenario_a,
        "B_place_exceptions_removed_with_proviso": scenario_b,
        "A_guide_dog_prohibited": sum(r["guide_dog"] == "prohibited" for r in scenario_a),
        "B_guide_dog_prohibited": sum(r["guide_dog"] == "prohibited" for r in scenario_b),
        "B_guide_dog_allowed": sum(r["guide_dog"] == "allowed" for r in scenario_b),
        "B_ordinary_dog_still_prohibited": sum(
            r["ordinary_dog"] == "prohibited" for r in scenario_b
        ),
    }

    if args.compare_production:
        prod = load("petaccess")
        report["production_provisos_activated"] = [p.id for p in prod["provisos"]]
        report["production_guide_dog_with_existing_exceptions"] = [
            {"place": r["place"], "guide_dog": r["guide_dog"], "applied": r["applied"]}
            for r in probe(prod, [], drop_place_exceptions=False)
        ]

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"db = {report['db']}   provisos = {report['provisos_loaded']}")
        print()
        print(f"{'place':<22}{'zone':<10}{'ordinary':<12}{'A guide':<12}{'B guide':<12}")
        for a, b in zip(scenario_a, scenario_b, strict=False):
            print(
                f"{a['place']:<22}{str(a['zone'])[:8]:<10}{b['ordinary_dog']:<12}"
                f"{a['guide_dog']:<12}{b['guide_dog']:<12}"
            )
        print()
        print(f"A_guide_dog_prohibited          = {report['A_guide_dog_prohibited']}")
        print(f"B_guide_dog_prohibited          = {report['B_guide_dog_prohibited']}")
        print(f"B_guide_dog_allowed             = {report['B_guide_dog_allowed']}")
        print(f"B_ordinary_dog_still_prohibited = {report['B_ordinary_dog_still_prohibited']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
