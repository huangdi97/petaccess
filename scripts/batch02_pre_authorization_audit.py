"""BATCH_02 pre-authorization audit — ADR-030 runtime proof + resolver matrix.

This answers one question that no document can answer: **does a newly published
LEGAL dog prohibition, with no hand-written venue-level carve-out, still exempt
a guide dog in the real resolver?**

Everything BATCH_02 ships is a LEGAL/mandatory dog prohibition grounded in
《上海市养犬管理条例》第二十三条. The manifest carries 6 AccessRules and 0
RuleExceptions — deliberately. That is only safe if the jurisdiction-level
statutory proviso (JPROV-001) actually fires. So this script does not check that
the proviso row exists; it checks what the resolver answers.

The decisive mode is ``no_place_exception``: the venue-level ``rule_exception``
rows are dropped from the exception set, leaving **only** the jurisdiction
proviso. That is exactly the state a freshly published BATCH_02 base will be in.
If a guide dog is still prohibited in that mode, ADR-030 does not do its job and
BATCH_02 must not be authorized.

Three modes are resolved from the same live rows so the comparison is honest:

    full               — venue exceptions + jurisdiction proviso (reality today)
    no_place_exception — jurisdiction proviso only (the post-BATCH_02 state)
    no_proviso         — venue exceptions only (the pre-activation state)

The subject matrix exists to catch the opposite failure: a proviso that is
*narrower* than intended is visible, but one that silently widens to every
working dog is not. Police dogs, military working dogs and the other assistance
roles are resolved explicitly for that reason.

Loaders are imported from ``verify_adr030_production_activation`` — one canonical
way to read these rows, so the two probes cannot drift.

Read-only: opens no transaction, writes nothing to the database.
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
from app.rulespec.animal_scope import rule_governs  # noqa: E402
from app.rulespec.statutory_proviso import proviso_subjects  # noqa: E402
from app.rulespec.v05_resolver import (  # noqa: E402
    LayeredRule,
    resolve,
)


@dataclass(frozen=True)
class Question:
    """A resolver question. ``declared_role`` pinning is what makes the
    over-generalisation checks meaningful — see ``animal_scope.query_subjects``."""

    label: str
    animal: str
    service_role: str
    declared_role: str | None


QUESTIONS = [
    Question("ordinary_dog", "dog", "none", None),
    Question("guide_dog", "dog", "guide_dog", "guide_dog"),
    # undeclared assistance-dog query: expands to all four assistance roles
    Question("service_dog_undeclared", "dog", "working", None),
    Question("hearing_dog", "dog", "hearing_dog", "hearing_dog"),
    Question("assistance_dog", "dog", "assistance_dog", "assistance_dog"),
    Question("other_service_dog", "dog", "other_service_dog", "other_service_dog"),
    Question("police_dog", "dog", "police_dog", "police_dog"),
    Question("military_working_dog", "dog", "military_working_dog", "military_working_dog"),
]

#: Roles that a 导盲犬 proviso must never reach unless a source says so.
OVERGENERALISATION_ROLES = (
    "hearing_dog",
    "assistance_dog",
    "other_service_dog",
    "police_dog",
    "military_working_dog",
)


def _resolve(rules, exceptions, q: Question, zone_id, now):
    legal = [r for r in rules if (r.rule_layer or "").upper() == "LEGAL"]
    operator = [r for r in rules if (r.rule_layer or "").upper() == "OPERATOR_POLICY"]
    return resolve(
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
        exceptions=list(exceptions),
        declared_role=q.declared_role,
    )


def _binding_conditions(proviso, base, now: datetime) -> dict:
    """The five ADR-030 applicability conditions, evaluated one at a time.

    Reported individually rather than collapsed into a boolean: "the proviso
    applied" is the conclusion, and a reader has to be able to see *which*
    condition carried it.
    """
    instrument = frozenset(proviso.instrument_source_ids or ())
    subjects = proviso_subjects(
        proviso.animal_scope, proviso.subject_scope_normalized, proviso.normalization_type
    )
    return {
        "1_instrument_source_matches": base.source_id in instrument,
        "2_layer_matches": (base.rule_layer or "").upper()
        == (proviso.applies_to_layer or "").upper(),
        "3_effect_matches": base.effect in frozenset(proviso.applies_to_effects or ("prohibited",)),
        "4_base_governs_proviso_subject": rule_governs(
            subjects,
            base.animal_scope,
            base.subject_scope_normalized,
            base.normalization_type,
        ),
        "5_temporal_valid": proviso.active_at(now),
    }


def _negative_control(rules, provisos, base: LayeredRule, zone_id, now: datetime) -> dict:
    """A prohibition from a *different* instrument must not inherit the proviso.

    Without this, "the proviso fires" and "the proviso fires at everything"
    look identical. The synthetic base is identical to the real one except for
    ``source_id``, so a guide dog must stay prohibited — proving the binding is
    by instrument identity and not by "this venue happens to be in Shanghai".
    """
    from dataclasses import replace

    foreign = replace(base, id=f"{base.id}-foreign-source", source_id="not-the-instrument")
    synthetic = [foreign if r.id == base.id else r for r in rules]
    res = _resolve(synthetic, provisos, QUESTIONS[1], zone_id, now)  # guide dog
    return {
        "base_id": base.id,
        "guide_dog_with_foreign_source": res.effect,
        "proviso_correctly_withheld": res.effect == "prohibited",
    }


def _entry(res, q: Question) -> dict:
    inert = [s for s in res.explanation_steps if "JURISDICTION_EXCEPTION_INERT" in s]
    return {
        "question": q.label,
        "effect": res.effect,
        "applied_exceptions": list(res.applied_exceptions),
        "inert_notes": inert,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--out", default="artifacts/batch02_audit/runtime_matrix.json")
    args = ap.parse_args()

    url = psycopg_url(
        f"postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/{args.db_name}"
    )
    now = datetime.now(UTC)

    out: dict = {
        "db": args.db_name,
        "resolved_at": now.isoformat(),
        "questions": [q.label for q in QUESTIONS],
        "proviso_rows": [],
        "places": [],
        "metrics": {},
        "problems": [],
    }

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute("select * from jurisdiction_exception")
        cols = [d.name for d in cur.description]
        out["proviso_rows"] = [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]

        provisos = load_provisos(cur)
        out["active_provisos"] = [
            {
                "id": p.id,
                "binding": p.binding,
                "animal_scope": p.animal_scope,
                "subject_scope_normalized": p.subject_scope_normalized,
                "normalization_type": p.normalization_type,
                "instrument_source_ids": [str(s) for s in p.instrument_source_ids],
                "applies_to_layer": p.applies_to_layer,
                "applies_to_effects": list(p.applies_to_effects),
                "holder_scope": p.holder_scope,
            }
            for p in provisos
        ]

        # Targets are taken from the LEGAL base rows themselves, not from the
        # place's zone list. A statutory prohibition is attached to one zone (or
        # to the place); every other zone of that place is legitimately
        # `unknown`, and asserting "prohibited" there would invent legal effect
        # where the source says nothing.
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
            modes: dict[str, dict] = {}
            for mode, excs in (
                ("full", list(place_exceptions) + list(provisos)),
                ("no_place_exception", list(provisos)),
                ("no_proviso", list(place_exceptions)),
            ):
                modes[mode] = {
                    q.label: _entry(_resolve(rules, excs, q, zone_id, now), q) for q in QUESTIONS
                }
            base_ids = [
                r.id
                for r in rules
                if (r.rule_layer or "").upper() == "LEGAL"
                and r.action == "enter"
                and (r.zone_id == zone_id)
            ]
            in_scope_bases = [
                r for r in rules if (r.rule_layer or "").upper() == "LEGAL" and r.zone_id == zone_id
            ]
            binding = [
                {
                    "base_id": b.id,
                    "proviso": prov.id,
                    "conditions": _binding_conditions(prov, b, now),
                }
                for b in in_scope_bases
                for prov in provisos
            ]
            for item in binding:
                item["all_conditions_hold"] = all(item["conditions"].values())
            controls = (
                [_negative_control(rules, provisos, b, zone_id, now) for b in in_scope_bases[:1]]
                if provisos
                else []
            )
            out["places"].append(
                {
                    "place": place_name,
                    "place_id": str(place_id),
                    "zone": zone_name,
                    "zone_id": str(zone_id) if zone_id else None,
                    "legal_base_ids": base_ids,
                    "binding_conditions": binding,
                    "negative_control": controls,
                    "place_level_exceptions": [e.id for e in place_exceptions],
                    "modes": modes,
                }
            )

    # ---------------------------------------------------------------- metrics
    decisive = "no_place_exception"
    m: dict = {}
    problems: list[str] = []

    matched = 0
    guide_wrong = 0
    ordinary_not_prohibited = 0
    overgeneralised = dict.fromkeys(OVERGENERALISATION_ROLES, 0)
    double_apply: list[str] = []
    mode_disagreement: list[str] = []

    for p in out["places"]:
        dec = p["modes"][decisive]
        full = p["modes"]["full"]
        site = f"{p['place']} @ {p['zone']}"

        if dec["ordinary_dog"]["effect"] != "prohibited":
            ordinary_not_prohibited += 1
            problems.append(
                f"{site}: ordinary dog = {dec['ordinary_dog']['effect']} "
                f"(expected prohibited) in {decisive} mode"
            )

        gd = dec["guide_dog"]["effect"]
        if gd == "prohibited":
            guide_wrong += 1
            problems.append(
                f"{site}: guide dog still prohibited with only the jurisdiction "
                f"proviso — ADR-030 did not fire"
            )
        proviso_ids = {q["id"] for q in out["active_provisos"]}
        if proviso_ids & set(dec["guide_dog"]["applied_exceptions"]):
            matched += 1

        for role in OVERGENERALISATION_ROLES:
            if dec[role]["effect"] == "allowed":
                overgeneralised[role] += 1

        # C — no double application: where a legacy venue-level exception
        # already exists, adding the proviso must not change the answer and one
        # base may not carry two exception ids at once.
        #
        # ``no_proviso`` is deliberately NOT part of this comparison. It is the
        # pre-activation counterfactual: for a brand-new base with no venue
        # exception it answers `prohibited`, and that difference is exactly what
        # ADR-030 buys. Counting it as a disagreement would punish the mechanism
        # for working. It is reported separately as ADR030_EFFECT.
        for q in ("guide_dog", "ordinary_dog"):
            effects = {mode: p["modes"][mode][q]["effect"] for mode in ("full", decisive)}
            if len(set(effects.values())) != 1:
                mode_disagreement.append(f"{site} {q}: {effects}")
        applied_full = full["guide_dog"]["applied_exceptions"]
        if len(applied_full) > 1:
            double_apply.append(f"{site}: applied_exceptions={applied_full}")

        counterfactual = p["modes"]["no_proviso"]["guide_dog"]["effect"]
        p["adr030_effect"] = {
            "guide_dog_without_proviso": counterfactual,
            "guide_dog_with_proviso": full["guide_dog"]["effect"],
            "proviso_changes_answer": counterfactual != full["guide_dog"]["effect"],
        }

    total = len(out["places"])
    m["places_resolved"] = total
    m["JURISDICTION_EXCEPTION_MATCHED"] = matched
    m["GUIDE_DOG_WRONG_PROHIBITION"] = guide_wrong
    m["ORDINARY_DOG_NOT_PROHIBITED"] = ordinary_not_prohibited
    m["PLACE_LEVEL_DUPLICATE_EXCEPTION_REQUIRED"] = "YES" if guide_wrong else "NO"
    m["DOUBLE_APPLICATION"] = len(double_apply)
    m["MODE_DISAGREEMENT"] = len(mode_disagreement)
    m["NEGATIVE_CONTROL_FAILED"] = sum(
        1
        for p in out["places"]
        for c in p["negative_control"]
        if not c["proviso_correctly_withheld"]
    )
    m["BINDING_ALL_CONDITIONS_HOLD"] = sum(
        1 for p in out["places"] for b in p["binding_conditions"] if b["all_conditions_hold"]
    )
    m["BINDING_PAIRS_EVALUATED"] = sum(len(p["binding_conditions"]) for p in out["places"])
    m["ADR030_EFFECT_ANSWER_CHANGED"] = sum(
        1 for p in out["places"] if p["adr030_effect"]["proviso_changes_answer"]
    )
    m["SERVICE_DOG_OVERGENERALIZATION"] = overgeneralised["hearing_dog"]
    m["POLICE_DOG_OVERGENERALIZATION"] = overgeneralised["police_dog"]
    m["MILITARY_DOG_OVERGENERALIZATION"] = overgeneralised["military_working_dog"]
    m["ASSISTANCE_DOG_OVERGENERALIZATION"] = overgeneralised["assistance_dog"]
    m["OTHER_SERVICE_DOG_OVERGENERALIZATION"] = overgeneralised["other_service_dog"]
    m["HEARING_DOG_OVERGENERALIZATION"] = overgeneralised["hearing_dog"]
    m["double_apply_detail"] = double_apply
    m["mode_disagreement_detail"] = mode_disagreement

    m["ADR030_RUNTIME_GATE"] = (
        "PASS"
        if (
            guide_wrong == 0
            and ordinary_not_prohibited == 0
            and m["DOUBLE_APPLICATION"] == 0
            and m["MODE_DISAGREEMENT"] == 0
            and m["POLICE_DOG_OVERGENERALIZATION"] == 0
            and m["MILITARY_DOG_OVERGENERALIZATION"] == 0
            and m["NEGATIVE_CONTROL_FAILED"] == 0
        )
        else "FAIL"
    )
    out["metrics"] = m
    out["problems"] = problems

    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )

    print(f"db = {args.db_name}   places = {total}")
    print(f"WROTE {dest}")
    for k, v in m.items():
        if not k.endswith("_detail"):
            print(f"  {k} = {v}")
    for prob in problems[:20]:
        print(f"  PROBLEM: {prob}")
    return 0 if m["ADR030_RUNTIME_GATE"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
