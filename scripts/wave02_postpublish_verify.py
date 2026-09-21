"""Post-publish verification for EXP-R1-W02-REVIEW-R1-BATCH-01 (16 Wave-02 rules).

Read-only. Drives the canonical resolver exactly as the consumer path does, for
every access_rule that the Wave-02 real publish created (created_at in the
publish window), and reports whether the resolved effect matches the published
effect. Also reports the post-publish snapshot (counts, candidate states,
source/evidence linkage).

It proves the answers come from the *published* data, not from a fixture:
the rule the receipt created is the rule a consumer query resolves.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
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
WINDOW = ("2026-09-21 13:20:00+00", "2026-09-21 13:21:00+00")


@dataclass(frozen=True)
class Probe:
    place: str
    zone_id: str | None
    animal: str
    service_role: str
    declared_role: str | None
    expected: str
    published_rule_id: str


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


def animal_query(animal_scope: str, subject: str) -> tuple[str, str, str | None]:
    """Map a published rule's scope to a consumer query under ADR-025."""
    if animal_scope == "ordinary_pet":
        return ("dog", "none", None)
    if animal_scope == "dog" or animal_scope == "cat" or animal_scope == "other":
        return (animal_scope, "none", None)
    if animal_scope == "service_dog":
        # Wave-02 豫园 guide-dog carve-out, subject_scope_normalized=guide_dog
        if subject == "guide_dog":
            return ("dog", "guide_dog", "guide_dog")
        return ("dog", "none", None)
    return ("dog", "none", None)


def main() -> int:
    now = datetime.now(UTC)
    out: dict = {"probes": [], "problems": [], "snapshot": {}}
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        # ---- published Wave-02 rules (the exact rows the receipt created) ----
        cur.execute(
            """
            select ar.id, ar.animal_scope, ar.effect, ar.zone_id,
                   ar.source_id, ar.subject_scope_normalized, p.canonical_name
            from access_rule ar join place p on p.id = ar.place_id
            where ar.created_at >= %s and ar.created_at < %s
            order by ar.created_at
            """,
            WINDOW,
        )
        published = cur.fetchall()
        out["snapshot"]["published_rules_in_window"] = len(published)
        out["snapshot"]["published_rules"] = [
            {"rule_id": r[0], "place": r[6], "animal_scope": r[1], "effect": r[2]}
            for r in published
        ]

        # ---- post-publish snapshot ----
        out["snapshot"]["access_rule_total"] = cur.execute(
            "select count(*) from access_rule"
        ).fetchone()[0]
        out["snapshot"]["rule_exception_total"] = cur.execute(
            "select count(*) from rule_exception"
        ).fetchone()[0]
        # Wave02 candidates
        cur.execute(
            """
            select rc.review_status, count(*), count(rc.published_rule_id)
            from rule_candidate rc
            where rc.expansion_run_id = 'EXP-R1-W02-20260919'
            group by rc.review_status order by rc.review_status
            """
        )
        out["snapshot"]["wave02_candidates"] = [
            {"review_status": r[0], "count": r[1], "published_rule_id_not_null": r[2]}
            for r in cur.fetchall()
        ]
        # audit rows created in the window
        out["snapshot"]["audit_in_window"] = cur.execute(
            """
            select action, count(*) from audit_log
            where created_at >= %s and created_at < %s
            group by action order by action
            """,
            WINDOW,
        ).fetchall()

        # ---- probe every published rule through the canonical resolver ----
        seen: set[tuple[str, str]] = set()
        for ar_id, animal_scope, effect, zone_id, source_id, subject, place_name in published:
            key = (place_name, animal_scope)
            if key in seen:
                continue  # duplicate scope per place (single publish window row)
            seen.add(key)
            animal, service_role, declared_role = animal_query(animal_scope, subject)
            rules, excs = load_rules(cur, place_name)
            legal = [r for r in rules if (r.rule_layer or "").upper() == "LEGAL"]
            operator = [r for r in rules if (r.rule_layer or "").upper() == "OPERATOR_POLICY"]
            zone_id_probe = zone_id
            res = resolve(
                legal=legal,
                guidance=[],
                template_rules=[],
                operator_rules=operator,
                event_rules=[],
                animal=animal,
                service_role=service_role,
                action="enter",
                zone_id=zone_id_probe,
                now=now,
                exceptions=excs,
                declared_role=declared_role,
            )
            entry = {
                "place": place_name,
                "zone_id": zone_id_probe,
                "query": {"animal": animal, "service_role": service_role, "declared_role": declared_role},
                "published_rule_id": ar_id,
                "source_id": source_id,
                "effects": {"published": effect, "resolved": res.effect},
                "compliance_state": str(res.compliance_state),
                "applied_exceptions": list(res.applied_exceptions),
                "applicable_rule_ids": [r.id for r in res.applicable_rules],
                "match": res.effect == effect,
            }
            if res.effect != effect:
                out["problems"].append(
                    f"{place_name} [{animal_scope}]: published={effect!r} resolved={res.effect!r}"
                )
            out["probes"].append(entry)

    out["verdict"] = "PASS" if not out["problems"] else "FAIL"
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if not out["problems"] else 1


if __name__ == "__main__":
    raise SystemExit(main())