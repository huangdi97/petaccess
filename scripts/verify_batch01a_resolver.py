"""Post-publish resolver probe for EXP-R1-W01-REVIEW-R1-BATCH-01A.

Loads the *live* rows from ``petaccess`` (PRODUCTION, read-only) and drives the
canonical resolver exactly as the consumer path does. Three questions per place:

  * 兴业太古汇        — ordinary dog (must be prohibited), guide dog (must be allowed)
  * 上海博物馆东馆     — ordinary pet, dog, guide dog

The point of the probe is that the answer must come from the *published* data,
not from a fixture. It therefore proves three separate things at once:
the base rule matches, the carve-out is reachable, and the carve-out fires.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))

import psycopg  # noqa: E402

from app.core.config import psycopg_url  # noqa: E402
from app.rulespec.v05_resolver import (  # noqa: E402
    LayeredException,
    LayeredRule,
    resolve,
)

DB_URL = psycopg_url("postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess")


@dataclass(frozen=True)
class Probe:
    label: str
    place: str
    animal: str
    service_role: str
    declared_role: str | None
    expected: str


PROBES = [
    Probe("兴业太古汇 · 普通犬", "兴业太古汇", "dog", "none", None, "prohibited"),
    Probe("兴业太古汇 · 导盲犬", "兴业太古汇", "dog", "guide_dog", "guide_dog", "allowed"),
    Probe("上海博物馆东馆 · 普通宠物", "上海博物馆东馆", "cat", "none", None, "prohibited"),
    Probe("上海博物馆东馆 · 普通犬", "上海博物馆东馆", "dog", "none", None, "prohibited"),
    Probe("上海博物馆东馆 · 导盲犬", "上海博物馆东馆", "dog", "guide_dog", "guide_dog", "allowed"),
]


def load_zones(cur, place_name: str) -> list[tuple[str, str]]:
    """(zone_id, zone_name) for a place. A real query is scoped to a zone."""
    cur.execute(
        """
        select z.id, z.name from zone z join place p on p.id = z.place_id
        where p.canonical_name = %s order by z.name
        """,
        (place_name,),
    )
    return [(r[0], r[1]) for r in cur.fetchall()]


def load_rules(cur, place_name: str) -> tuple[list[LayeredRule], list[LayeredException]]:
    cur.execute(
        """
        select ar.id, ar.animal_scope, ar.action, ar.effect, ar.rule_layer, ar.rule_origin,
               ar.source_id, ar.effective_from, ar.effective_to,
               ar.mandatory_level, ar.zone_id,
               ar.source_scope_exact, ar.subject_scope_normalized, ar.normalization_type
        from access_rule ar join place p on p.id = ar.place_id
        where p.canonical_name = %s and ar.status = 'current'
        """,
        (place_name,),
    )
    rules = []
    for r in cur.fetchall():
        rules.append(
            LayeredRule(
                id=r[0],
                animal_scope=r[1],
                action=r[2],
                effect=r[3],
                rule_layer=r[4],
                origin=r[5] or "operator_direct",
                source_id=r[6],
                effective_from=r[7],
                effective_to=r[8],
                mandatory_level=r[9],
                zone_id=r[10],
                source_scope_exact=r[11],
                subject_scope_normalized=r[12],
                normalization_type=r[13],
            )
        )
    cur.execute(
        """
        select re.id, re.rule_id, re.animal_scope, re.effect, re.source_id, re.status,
               re.effective_from, re.effective_to, re.source_scope_exact,
               re.subject_scope_normalized, re.normalization_type
        from rule_exception re join access_rule ar on ar.id = re.rule_id
        join place p on p.id = ar.place_id
        where p.canonical_name = %s and re.status = 'current'
        """,
        (place_name,),
    )
    excs = [
        LayeredException(
            id=r[0],
            rule_id=r[1],
            animal_scope=r[2],
            effect=r[3],
            source_id=r[4],
            status=r[5],
            effective_from=r[6],
            effective_to=r[7],
            source_scope_exact=r[8],
            subject_scope_normalized=r[9],
            normalization_type=r[10],
        )
        for r in cur.fetchall()
    ]
    return rules, excs


def main() -> int:
    now = datetime.now(UTC)
    out = {"probes": [], "problems": []}
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        for pr in PROBES:
            rules, excs = load_rules(cur, pr.place)
            legal = [r for r in rules if (r.rule_layer or "").upper() == "LEGAL"]
            operator = [r for r in rules if (r.rule_layer or "").upper() == "OPERATOR_POLICY"]
            # A consumer query is always made *at a place*; the resolver then runs
            # per zone. Resolving with zone_id=None would only match place-wide
            # rules and silently drop every zone-scoped one.
            for zone_id, zone_name in load_zones(cur, pr.place):
                res = resolve(
                    legal=legal,
                    guidance=[],
                    template_rules=[],
                    operator_rules=operator,
                    event_rules=[],
                    animal=pr.animal,
                    service_role=pr.service_role,
                    action="enter",
                    zone_id=zone_id,
                    now=now,
                    exceptions=excs,
                    declared_role=pr.declared_role,
                )
                entry = {
                    "probe": pr.label,
                    "place": pr.place,
                    "zone": zone_name,
                    "zone_id": zone_id,
                    "query": {
                        "animal": pr.animal,
                        "service_role": pr.service_role,
                        "declared_role": pr.declared_role,
                    },
                    "rules_loaded": len(rules),
                    "exceptions_loaded": len(excs),
                    "effect": res.effect,
                    "compliance_state": str(res.compliance_state),
                    "applied_exceptions": list(res.applied_exceptions),
                    "applicable_rule_ids": [r.id for r in res.applicable_rules],
                    "expected": pr.expected,
                    "match": res.effect == pr.expected,
                }
                if res.effect != pr.expected:
                    out["problems"].append(
                        f"{pr.label} @ {zone_name}: got {res.effect!r}, expected {pr.expected!r}"
                    )
                out["probes"].append(entry)

    out["verdict"] = "PASS" if not out["problems"] else "FAIL"
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if not out["problems"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
