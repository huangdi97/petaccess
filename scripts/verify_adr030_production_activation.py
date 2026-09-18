"""Read-only A/B probe for the ADR-030 proviso, against whatever DB you point it at.

The activation being verified is one row in ``jurisdiction_exception``. Nothing
about that is self-evident from the database alone: the row changes what the
resolver answers for **every** venue whose LEGAL prohibition is grounded in the
same instrument. So this script does not assert "the row exists" — it asserts the
*answer changed in exactly the right places and nowhere else*.

It therefore resolves every in-scope question twice, from the same live rows:

    A (``with_proviso=False``) — the jurisdiction proviso is dropped from the
      exception set. This is the pre-activation state, replayed after the fact.
    B (``with_proviso=True``)  — the activated proviso is included.

Only the canonical resolver decides; no expectation is hardcoded per venue.
The two invariants checked are the ones ADR-030 promises:

    1. an ordinary dog must answer **identically** in A and B
       (the proviso must not widen beyond 导盲犬);
    2. a guide dog must never answer ``prohibited`` **because of** a LEGAL base
       grounded in the instrument — and if it stays prohibited, the reason must
       be visible (inert proviso ⇒ the base does not govern guide dogs at all).

Read-only: it opens no transaction and writes nothing.
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

import psycopg  # noqa: E402

from app.core.config import psycopg_url  # noqa: E402
from app.rulespec.v05_resolver import (  # noqa: E402
    LayeredException,
    LayeredRule,
    resolve,
)


@dataclass(frozen=True)
class Question:
    label: str
    animal: str
    service_role: str
    declared_role: str | None


QUESTIONS = [
    Question("普通犬", "dog", "none", None),
    Question("导盲犬", "dog", "guide_dog", "guide_dog"),
]


def load_provisos(cur) -> list[LayeredException]:
    cur.execute(
        """
        select id, animal_scope, effect, source_id, status,
               effective_from, effective_to,
               subject_scope_normalized, normalization_type, normative_effect,
               holder_scope, binding, instrument_source_ids,
               applies_to_layer, applies_to_effects
        from jurisdiction_exception
        where status = 'current' and review_status = 'reviewed_active'
        order by id
        """
    )
    return [
        LayeredException(
            id=r[0],
            rule_id="",
            animal_scope=r[1],
            effect=r[2] or "allowed",
            source_id=r[3],
            status=r[4],
            effective_from=r[5],
            effective_to=r[6],
            subject_scope_normalized=r[7],
            normalization_type=r[8] or "exact",
            normative_effect=r[9],
            holder_scope=r[10],
            binding=r[11],
            instrument_source_ids=tuple(r[12] or ()),
            applies_to_layer=r[13],
            applies_to_effects=tuple(r[14] or ("prohibited",)),
        )
        for r in cur.fetchall()
    ]


def load_places(cur) -> list[str]:
    """Places that actually have a current LEGAL rule — the only ones in scope."""
    cur.execute(
        """
        select distinct p.id, p.canonical_name
        from access_rule ar join place p on p.id = ar.place_id
        where ar.status = 'current' and upper(ar.rule_layer) = 'LEGAL'
        order by p.canonical_name
        """
    )
    return cur.fetchall()


def load_rules(cur, place_id: str) -> list[LayeredRule]:
    cur.execute(
        """
        select ar.id, ar.animal_scope, ar.action, ar.effect, ar.rule_layer, ar.rule_origin,
               ar.source_id, ar.effective_from, ar.effective_to,
               ar.mandatory_level, ar.zone_id,
               ar.source_scope_exact, ar.subject_scope_normalized, ar.normalization_type
        from access_rule ar
        where ar.place_id = %s and ar.status = 'current'
        """,
        (place_id,),
    )
    return [
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
        for r in cur.fetchall()
    ]


def load_exceptions(cur, place_id: str) -> list[LayeredException]:
    cur.execute(
        """
        select re.id, re.rule_id, re.animal_scope, re.effect, re.source_id, re.status,
               re.effective_from, re.effective_to, re.source_scope_exact,
               re.subject_scope_normalized, re.normalization_type,
               re.normative_effect, re.holder_scope
        from rule_exception re join access_rule ar on ar.id = re.rule_id
        where ar.place_id = %s and re.status = 'current'
        """,
        (place_id,),
    )
    return [
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
            normative_effect=r[11],
            holder_scope=r[12],
        )
        for r in cur.fetchall()
    ]


def load_zones(cur, place_id: str) -> list[tuple[str, str]]:
    cur.execute(
        "select id, name from zone where place_id = %s order by name",
        (place_id,),
    )
    rows = cur.fetchall()
    # A place with no zones still resolves — at place level.
    return [(r[0], r[1]) for r in rows] or [(None, "(place-wide)")]


def _run(rules, exceptions, provisos, *, with_proviso: bool, q: Question, zone_id, now):
    legal = [r for r in rules if (r.rule_layer or "").upper() == "LEGAL"]
    operator = [r for r in rules if (r.rule_layer or "").upper() == "OPERATOR_POLICY"]
    excs = list(exceptions) + (list(provisos) if with_proviso else [])
    res = resolve(
        legal=legal,
        guidance=[],
        template_rules=[],
        operator_rules=operator,
        event_rules=[],
        animal=q.animal,
        service_role=q.service_role,
        action="enter",
        zone_id=zone_id,
        now=now,
        exceptions=excs,
        declared_role=q.declared_role,
    )
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    url = psycopg_url(
        f"postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/{args.db_name}"
    )
    now = datetime.now(UTC)
    out: dict = {"db": args.db_name, "provisos": [], "places": [], "problems": []}

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        provisos = load_provisos(cur)
        out["provisos"] = [
            {
                "id": p.id,
                "binding": p.binding,
                "instrument_source_ids": list(p.instrument_source_ids),
                "applies_to_layer": p.applies_to_layer,
                "applies_to_effects": list(p.applies_to_effects),
            }
            for p in provisos
        ]

        cur.execute(
            """
            select ar.id, ar.source_id, ar.animal_scope, ar.effect,
                   ar.subject_scope_normalized,
                   ar.normalization_type, p_.canonical_name
            from access_rule ar join place p_ on p_.id = ar.place_id
            where ar.status = 'current' and upper(ar.rule_layer) = 'LEGAL'
            order by p_.canonical_name, ar.id
            """
        )
        legal_rows = cur.fetchall()
        instrument_ids = {s for p in provisos for s in p.instrument_source_ids}
        out["legal_bases"] = [
            {
                "rule_id": r[0][:8],
                "place": r[6],
                "source_id": str(r[1])[:8] if r[1] else None,
                "animal_scope": r[2],
                "effect": r[3],
                "grounded_in_instrument": str(r[1]) in instrument_ids if r[1] else False,
            }
            for r in legal_rows
        ]

        for place_id, place_name in load_places(cur):
            rules = load_rules(cur, place_id)
            exceptions = load_exceptions(cur, place_id)
            for zone_id, zone_name in load_zones(cur, place_id):
                entry: dict = {
                    "place": place_name,
                    "zone": zone_name,
                    "questions": [],
                }
                for q in QUESTIONS:
                    before = _run(
                        rules,
                        exceptions,
                        provisos,
                        with_proviso=False,
                        q=q,
                        zone_id=zone_id,
                        now=now,
                    )
                    after = _run(
                        rules,
                        exceptions,
                        provisos,
                        with_proviso=True,
                        q=q,
                        zone_id=zone_id,
                        now=now,
                    )
                    inert = [
                        s for s in after.explanation_steps if "JURISDICTION_EXCEPTION_INERT" in s
                    ]
                    delta = {
                        "question": q.label,
                        "before": before.effect,
                        "after": after.effect,
                        "changed": before.effect != after.effect,
                        "applied_exceptions": list(after.applied_exceptions),
                        "inert_notes": inert,
                    }
                    entry["questions"].append(delta)

                    # invariant 1: the proviso must not move an ordinary dog
                    if q.label == "普通犬" and before.effect != after.effect:
                        out["problems"].append(
                            f"{place_name} @ {zone_name} 普通犬: {before.effect} → "
                            f"{after.effect} (proviso widened beyond 导盲犬)"
                        )
                    # invariant 2: a guide dog may never be left prohibited by a
                    # base the proviso reaches. If it is still prohibited, the
                    # proviso must have declared itself inert for a visible reason.
                    if q.label == "导盲犬" and after.effect == "prohibited":
                        grounded = any(
                            b["grounded_in_instrument"] and b["place"] == place_name
                            for b in out["legal_bases"]
                        )
                        if grounded and not inert:
                            out["problems"].append(
                                f"{place_name} @ {zone_name} 导盲犬: still prohibited with no "
                                "inert note — the proviso failed to fire"
                            )
                out["places"].append(entry)

    out["verdict"] = "PASS" if not out["problems"] else "FAIL"
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"db = {out['db']}")
        print(f"active provisos = {len(out['provisos'])}")
        for b in out["legal_bases"]:
            print(
                f"  LEGAL {b['rule_id']} {b['place']} src={b['source_id']} "
                f"scope={b['animal_scope']} effect={b['effect']} "
                f"in_instrument={b['grounded_in_instrument']}"
            )
        for p in out["places"]:
            for q in p["questions"]:
                flag = "CHANGED" if q["changed"] else "same"
                print(
                    f"  {p['place']} @ {p['zone']} {q['question']}: "
                    f"{q['before']} → {q['after']} [{flag}]"
                )
        print(f"verdict = {out['verdict']}")
        for prob in out["problems"]:
            print(f"  PROBLEM: {prob}")
    return 0 if not out["problems"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
