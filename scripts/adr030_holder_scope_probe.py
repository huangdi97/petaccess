"""ADR-031 runtime probe: the holder half of the 但书, over real rows.

Where ``batch02_pre_authorization_audit.py`` asked *"does the jurisdiction
proviso fire at all?"*, this asks the harder question the earlier audit left
open: **does it fire only for the handler the statute names?**

《上海市养犬管理条例》第二十三条 is 「禁止携带犬只进入…」 + 「盲人携带导盲犬的，
不受本条规定的限制。」 The earlier audit proved the subject half (导盲犬) works.
The holder half (盲人) was stored but never enforced — this probe measures it
after the fix, on the real rows, with the canonical resolver.

Every LEGAL base is resolved against a matrix of seven questions × three holder
contexts, in two exception modes:

    full               — venue exceptions + the jurisdiction proviso (reality)
    no_place_exception — the proviso only (the state a freshly published base
                         is in; the decisive mode)

and the counters that must all be zero are:

    GUIDE_DOG_MATCHING_HOLDER_WRONG_PROHIBITION   a statutory right refused
    GUIDE_DOG_UNKNOWN_HOLDER_UNCONDITIONAL_ALLOW  a condition never evaluated
    SERVICE_DOG_OVERGENERALIZATION                existence semantics
    POLICE_DOG / MILITARY_DOG_OVERGENERALIZATION  the proviso widening
    DOUBLE_APPLIED_EXCEPTION                      one effect, twice

It also audits the already-published LEGAL guide-dog carve-outs (§15) — read
only, nothing is migrated:

    EXISTING_LEGAL_GUIDE_EXCEPTIONS / WITH_CORRECT_HOLDER_SCOPE /
    MISSING_HOLDER_SCOPE

Read-only: opens no transaction and writes nothing to the database.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))
sys.path.insert(0, str(REPO / "scripts"))

import psycopg  # noqa: E402
from verify_adr030_production_activation import (  # noqa: E402
    load_exceptions,
    load_provisos,
    load_rules,
)

from app.core.config import psycopg_url  # noqa: E402
from app.models.enums import HolderScope  # noqa: E402
from app.rulespec.holder_scope import HolderContext  # noqa: E402

MATCHING = HolderContext.of(HolderScope.PERSON_WITH_DISABILITY.value)
NON_MATCHING = HolderContext.of()
UNKNOWN = None  # no context supplied — the default for every public query


@dataclass(frozen=True)
class Q:
    label: str
    service_role: str
    declared_role: str | None
    holder: HolderContext | None


QUESTIONS: list[Q] = [
    Q("ordinary_dog", "none", None, MATCHING),
    Q("guide_dog_matching_holder", "guide_dog", "guide_dog", MATCHING),
    Q("guide_dog_unknown_holder", "guide_dog", "guide_dog", UNKNOWN),
    Q("guide_dog_nonmatching_holder", "guide_dog", "guide_dog", NON_MATCHING),
    Q("service_dog_generic", "working", None, MATCHING),
    Q("police_dog", "police_dog", "police_dog", MATCHING),
    Q("military_working_dog", "military_working_dog", "military_working_dog", MATCHING),
    Q("hearing_dog", "hearing_dog", "hearing_dog", MATCHING),
]

#: Roles a 导盲犬 proviso must never reach unless a source says so.
NEVER_ALLOWED = ("service_dog_generic", "police_dog", "military_working_dog", "hearing_dog")


def _resolve(rules, exceptions, q: Q, zone_id, now):
    from app.rulespec.v05_resolver import resolve

    legal = [r for r in rules if (r.rule_layer or "").upper() == "LEGAL"]
    operator = [r for r in rules if (r.rule_layer or "").upper() == "OPERATOR_POLICY"]
    return resolve(
        legal=legal,
        guidance=[],
        template_rules=[],
        operator_rules=operator,
        event_rules=[],
        animal="dog",
        service_role=q.service_role,
        action="enter",
        zone_id=zone_id,
        now=now,
        exceptions=list(exceptions),
        declared_role=q.declared_role,
        holder_context=q.holder,
    )


def _entry(res) -> dict:
    return {
        "effect": res.effect,
        "applied_exceptions": list(res.applied_exceptions),
        "pending_exceptions": list(res.pending_exceptions),
        "duplicate_exceptions": list(res.duplicate_exceptions),
        "missing_inputs": list(res.missing_inputs),
        "holder_trace": [
            s for s in res.explanation_steps if "holder condition" in s or "withheld" in s
        ],
    }


def audit_published_legal_guide_exceptions(cur) -> dict:
    """§15: every published LEGAL guide-dog carve-out, and its holder column.

    Read-only and deliberately non-destructive: these rows are history. The
    audit only counts, so a migration decision stays a human one (§16).
    """
    cur.execute(
        """
        select re.id, re.rule_id, re.holder_scope, re.source_scope_exact,
               re.subject_scope_normalized, re.normalization_type,
               upper(coalesce(ar.rule_layer, '')), ar.source_id,
               p.canonical_name
        from rule_exception re
        join access_rule ar on ar.id = re.rule_id
        join place p on p.id = ar.place_id
        where re.status = 'current' and upper(coalesce(ar.rule_layer, '')) = 'LEGAL'
          and (re.subject_scope_normalized = 'guide_dog'
               or coalesce(re.source_scope_exact, '') like '%导盲犬%')
        order by p.canonical_name, re.id
        """
    )
    rows = cur.fetchall()
    items = [
        {
            "exception_id": r[0],
            "base_rule_id": r[1],
            "holder_scope": r[2],
            "source_scope_exact": r[3],
            "subject_scope_normalized": r[4],
            "normalization_type": r[5],
            "rule_layer": r[6],
            "source_id": r[7],
            "place": r[8],
        }
        for r in rows
    ]
    return {
        "EXISTING_LEGAL_GUIDE_EXCEPTIONS": len(items),
        "WITH_CORRECT_HOLDER_SCOPE": sum(
            1 for i in items if i["holder_scope"] == HolderScope.PERSON_WITH_DISABILITY.value
        ),
        "MISSING_HOLDER_SCOPE": sum(1 for i in items if not i["holder_scope"]),
        "items": items,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--out", default="artifacts/adr031/holder_probe.json")
    args = ap.parse_args()

    url = psycopg_url(
        f"postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/{args.db_name}"
    )
    now = datetime.now(UTC)
    out: dict = {
        "db": args.db_name,
        "resolved_at": now.isoformat(),
        "questions": [q.label for q in QUESTIONS],
        "places": [],
        "published_legal_guide_exceptions": {},
        "metrics": {},
        "problems": [],
    }
    problems: list[str] = out["problems"]

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        provisos = load_provisos(cur)
        out["active_provisos"] = [
            {
                "id": p.id,
                "holder_scope": p.holder_scope,
                "subject_scope_normalized": p.subject_scope_normalized,
                "normalization_type": p.normalization_type,
                "binding": p.binding,
                "instrument_source_ids": [str(s) for s in p.instrument_source_ids],
                "applies_to_layer": p.applies_to_layer,
            }
            for p in provisos
        ]
        out["published_legal_guide_exceptions"] = audit_published_legal_guide_exceptions(cur)

        # Targets come from the LEGAL base rows themselves: a statutory
        # prohibition is attached to one zone (or the place), and every other
        # zone of that place is legitimately `unknown`.
        cur.execute(
            """
            select distinct ar.place_id, p_.canonical_name, ar.zone_id,
                   coalesce(z.name, '(place-wide)')
            from access_rule ar
            join place p_ on p_.id = ar.place_id
            left join zone z on z.id = ar.zone_id
            where ar.status = 'current' and upper(ar.rule_layer) = 'LEGAL'
            order by p_.canonical_name, 4
            """
        )
        targets = cur.fetchall()

        for place_id, place_name, zone_id, zone_name in targets:
            rules = load_rules(cur, place_id)
            place_exceptions = load_exceptions(cur, place_id)
            modes = {
                mode: {
                    q.label: _entry(_resolve(rules, excs, q, zone_id, now)) for q in QUESTIONS
                }
                for mode, excs in (
                    ("full", list(place_exceptions) + list(provisos)),
                    ("no_place_exception", list(provisos)),
                )
            }
            out["places"].append(
                {
                    "place": place_name,
                    "place_id": str(place_id),
                    "zone": zone_name,
                    "zone_id": str(zone_id) if zone_id else None,
                    "legal_base_ids": [
                        r.id
                        for r in rules
                        if (r.rule_layer or "").upper() == "LEGAL" and r.zone_id == zone_id
                    ],
                    "place_level_exceptions": [e.id for e in place_exceptions],
                    "modes": modes,
                }
            )

    # ---------------------------------------------------------------- metrics
    decisive = "no_place_exception"
    counters = {
        "GUIDE_DOG_MATCHING_HOLDER_WRONG_PROHIBITION": 0,
        "GUIDE_DOG_UNKNOWN_HOLDER_UNCONDITIONAL_ALLOW": 0,
        "GUIDE_DOG_NONMATCHING_HOLDER_STILL_ALLOWED": 0,
        "SERVICE_DOG_OVERGENERALIZATION": 0,
        "POLICE_DOG_OVERGENERALIZATION": 0,
        "MILITARY_DOG_OVERGENERALIZATION": 0,
        "HEARING_DOG_OVERGENERALIZATION": 0,
        "DOUBLE_APPLIED_EXCEPTION": 0,
        "ORDINARY_DOG_NOT_PROHIBITED": 0,
        "UNKNOWN_HOLDER_NOT_CONDITIONAL": 0,
    }

    for p in out["places"]:
        site = f"{p['place']} @ {p['zone']}"
        for mode in ("full", decisive):
            m = p["modes"][mode]
            if m["ordinary_dog"]["effect"] != "prohibited":
                counters["ORDINARY_DOG_NOT_PROHIBITED"] += 1
                problems.append(f"{site} [{mode}]: ordinary dog = {m['ordinary_dog']['effect']}")
            if m["guide_dog_matching_holder"]["effect"] == "prohibited":
                counters["GUIDE_DOG_MATCHING_HOLDER_WRONG_PROHIBITION"] += 1
                problems.append(f"{site} [{mode}]: guide dog + matching holder still prohibited")
            if m["guide_dog_unknown_holder"]["effect"] == "allowed":
                counters["GUIDE_DOG_UNKNOWN_HOLDER_UNCONDITIONAL_ALLOW"] += 1
                problems.append(f"{site} [{mode}]: guide dog allowed with no holder context")
            if m["guide_dog_unknown_holder"]["effect"] not in ("conditional", "prohibited"):
                counters["UNKNOWN_HOLDER_NOT_CONDITIONAL"] += 1
            if m["guide_dog_nonmatching_holder"]["applied_exceptions"]:
                counters["GUIDE_DOG_NONMATCHING_HOLDER_STILL_ALLOWED"] += 1
                problems.append(f"{site} [{mode}]: proviso applied to a non-matching holder")
            for role in NEVER_ALLOWED:
                key = {
                    "service_dog_generic": "SERVICE_DOG_OVERGENERALIZATION",
                    "police_dog": "POLICE_DOG_OVERGENERALIZATION",
                    "military_working_dog": "MILITARY_DOG_OVERGENERALIZATION",
                    "hearing_dog": "HEARING_DOG_OVERGENERALIZATION",
                }[role]
                if m[role]["effect"] == "allowed":
                    counters[key] += 1
                    problems.append(f"{site} [{mode}]: {role} allowed")
            if sum(1 for _ in m["guide_dog_matching_holder"]["applied_exceptions"]) > 1:
                counters["DOUBLE_APPLIED_EXCEPTION"] += 1
                problems.append(
                    f"{site} [{mode}]: {m['guide_dog_matching_holder']['applied_exceptions']}"
                )

    m_out = out["metrics"]
    m_out.update(counters)
    m_out["LEGAL_BASES_PROBED"] = len(out["places"])
    m_out["JURISDICTION_EXCEPTION_MATCHED"] = sum(
        1
        for p in out["places"]
        if any(
            pid in p["modes"][decisive]["guide_dog_matching_holder"]["applied_exceptions"]
            for pid in {q["id"] for q in out["active_provisos"]}
        )
    )
    m_out["HOLDER_CONDITION_ACTIVE_ON_PROVISOS"] = sum(
        1 for q in out["active_provisos"] if q["holder_scope"]
    )
    m_out["ADR030_HOLDER_SCOPE_RUNTIME_GATE"] = (
        "PASS" if not any(counters.values()) else "FAIL"
    )

    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )

    print(f"db = {args.db_name}   legal bases = {len(out['places'])}")
    print(f"WROTE {dest}")
    for k, v in m_out.items():
        print(f"  {k} = {v}")
    audit = out["published_legal_guide_exceptions"]
    for k in ("EXISTING_LEGAL_GUIDE_EXCEPTIONS", "WITH_CORRECT_HOLDER_SCOPE", "MISSING_HOLDER_SCOPE"):
        print(f"  {k} = {audit[k]}")
    for prob in problems[:20]:
        print(f"  PROBLEM: {prob}")
    return 0 if m_out["ADR030_HOLDER_SCOPE_RUNTIME_GATE"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
