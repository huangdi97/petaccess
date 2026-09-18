"""Propose — and prove — the source-scope Semantic Remodel for Wave01 (Phase B).

Read-only against production. It does three things and writes one file:

1. Reads the candidates whose ``source_scope_exact`` is broader than any single
   stored scope (上海动物园「动物」, 上海迪士尼乐园「动物（导盲犬除外）」).
2. Emits the row specs a declared ``compound_term_split`` asks for, and checks
   the decomposition is *complete* (exhaustive + inline proviso covered).
3. Runs the **canonical resolver** on the current row and on the proposed rows
   for four queries, so the change is demonstrated as an answer difference
   rather than asserted.

It never writes to a database and never mutates a signed candidate: a signed
candidate is immutable, so the remodel must ship as *new* candidates in a new
revision with a fresh human review. This script only produces that proposal.

Usage:
    .venv/Scripts/python.exe scripts/w01_scope_remodel_proposal.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, "services/api")

import psycopg  # noqa: E402

from app.core.config import psycopg_url  # noqa: E402
from app.rulespec.broad_term_split import (  # noqa: E402
    SEMANTIC_REMODEL_REQUIRED,
    declared_split,
    propose_split_rows,
    split_subjects,
    validate_split_group,
)
from app.rulespec.source_scope_semantics import (  # noqa: E402
    validate_source_scope_semantic_compatibility,
)
from app.rulespec.v05_resolver import (  # noqa: E402
    LayeredException,
    LayeredRule,
    resolve,
)

PRODUCTION_DB = "postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"
NOW = datetime.now(UTC)

#: (registry rule_id prefix, label). The Disney pair is listed together because
#: the base and its carve-out have to be remodelled as one unit — the carve-out
#: is only reachable once the base actually governs guide dogs.
TARGETS = [
    ("3a04d4d1aa", "上海迪士尼乐园 · 基底"),
    ("305fa08c1e", "上海迪士尼乐园 · 导盲犬 carve-out"),
    ("6f2bfd39d7", "上海动物园 · 基底"),
]

QUERIES = [
    ("普通犬", "dog", "none", None),
    ("导盲犬", "dog", "working", "guide_dog"),
    ("猫", "cat", "none", None),
    ("其他宠物", "other", "none", None),
]


def _rule(row: dict, *, suffix: str = "", scope: str | None = None, norm: str | None = None):
    """A LayeredRule for a candidate row, optionally with the proposed scope."""
    return LayeredRule(
        id=f"{row['id']}{suffix}",
        animal_scope=scope if scope is not None else row["animal_scope"],
        action=row["action"],
        effect=row["effect"],
        rule_layer=row["rule_layer"],
        origin="operator_direct",
        source_id=row["source_id"],
        effective_from=None,
        effective_to=None,
        mandatory_level=row["mandatory_level"],
        zone_id=row["zone_id"],
        source_scope_exact=row["source_scope_exact"],
        subject_scope_normalized=(scope if scope is not None else row["subject_scope_normalized"]),
        normalization_type=norm if norm is not None else row["normalization_type"],
    )


def _exception(row: dict, base_id: str) -> LayeredException:
    return LayeredException(
        id=row["id"],
        rule_id=base_id,
        animal_scope=row["animal_scope"],
        effect=row["effect"],
        source_id=row["source_id"],
        status="current",
        effective_from=None,
        effective_to=None,
        source_scope_exact=row["source_scope_exact"],
        subject_scope_normalized=row["subject_scope_normalized"],
        normalization_type=row["normalization_type"],
        normative_effect=row.get("normative_effect"),
        holder_scope=row.get("holder_scope"),
    )


def probe(rules: list, exceptions: list) -> list[dict]:
    operator = [r for r in rules if (r.rule_layer or "").upper() == "OPERATOR_POLICY"]
    legal = [r for r in rules if (r.rule_layer or "").upper() == "LEGAL"]
    out = []
    for label, animal, service_role, declared_role in QUERIES:
        res = resolve(
            legal=legal,
            guidance=[],
            template_rules=[],
            operator_rules=operator,
            event_rules=[],
            animal=animal,
            service_role=service_role,
            action="enter",
            zone_id=rules[0].zone_id if rules else None,
            now=NOW,
            exceptions=exceptions,
            declared_role=declared_role,
        )
        out.append(
            {
                "query": label,
                "effect": res.effect,
                "applied_exceptions": list(res.applied_exceptions),
                "applicable_rule_ids": [r.id for r in res.applicable_rules],
            }
        )
    return out


def load(cur, prefix: str) -> dict | None:
    cur.execute(
        """
        select id, place_id, zone_id, animal_scope, action, effect, rule_layer,
               mandatory_level, source_scope_exact, subject_scope_normalized,
               normalization_type, source_id, normative_effect, holder_scope
        from rule_candidate where replace(id,'-','') like %s
        """,
        (prefix + "%",),
    )
    row = cur.fetchone()
    if row is None:
        return None
    keys = [
        "id",
        "place_id",
        "zone_id",
        "animal_scope",
        "action",
        "effect",
        "rule_layer",
        "mandatory_level",
        "source_scope_exact",
        "subject_scope_normalized",
        "normalization_type",
        "source_id",
        "normative_effect",
        "holder_scope",
    ]
    return dict(zip(keys, row, strict=True))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/expansion/scope_remodel_proposals_r2.json")
    args = ap.parse_args()

    url = psycopg_url(PRODUCTION_DB)
    report: dict = {
        "generated_at": NOW.isoformat(),
        "source_db": "petaccess (read-only)",
        "mutations": 0,
        "targets": [],
        "open_questions": [],
    }

    with psycopg.connect(url) as conn, conn.cursor() as cur:
        rows = {p: load(cur, p) for p, _ in TARGETS}
        missing = [p for p, r in rows.items() if r is None]
        if missing:
            raise SystemExit(f"REFUSED: candidates not found: {missing}")

        disney_base = rows["3a04d4d1aa"]
        disney_exc = rows["305fa08c1e"]
        zoo_base = rows["6f2bfd39d7"]

        before_disney = probe(
            [_rule(disney_base)],
            [_exception(disney_exc, disney_base["id"])],
        )
        before_zoo = probe([_rule(zoo_base)], [])

        # ---- Disney: base「动物（导盲犬除外）」 + its guide-dog carve-out -----
        split = declared_split(disney_base["source_scope_exact"])
        assert split is not None
        specs = propose_split_rows(disney_base["source_scope_exact"])
        after_rules = [
            _rule(
                disney_base,
                suffix=f"#{s['subject_scope_normalized']}",
                scope=s["subject_scope_normalized"],
                norm=s["normalization_type"],
            )
            for s in specs
        ]
        dog_row = next(r for r in after_rules if r.subject_scope_normalized == "dog")
        after_disney = probe(after_rules, [_exception(disney_exc, dog_row.id)])
        group = validate_split_group(
            disney_base["source_scope_exact"],
            [s["subject_scope_normalized"] for s in specs],
            carve_out_subjects=(disney_exc["subject_scope_normalized"],),
        )

        report["targets"].append(
            {
                "place": "上海迪士尼乐园",
                "candidate_rule_id": "w01-3a04d4d1aa",
                "candidate_uuid": disney_base["id"],
                "source_scope_exact": disney_base["source_scope_exact"],
                "current": {
                    "animal_scope": disney_base["animal_scope"],
                    "subject_scope_normalized": disney_base["subject_scope_normalized"],
                    "normalization_type": disney_base["normalization_type"],
                    "gate": (
                        lambda v: {
                            "compatible": v.compatible,
                            "change": v.change,
                            "reason": v.reason,
                        }
                    )(
                        validate_source_scope_semantic_compatibility(
                            disney_base["source_scope_exact"],
                            disney_base["subject_scope_normalized"],
                            disney_base["normalization_type"],
                        )
                    ),
                },
                "proposed_rows": specs,
                "proposed_carve_out": {
                    "candidate_rule_id": "w01-305fa08c1e",
                    "subject_scope_normalized": disney_exc["subject_scope_normalized"],
                    "attaches_to": "dog",
                },
                "group_verdict": {
                    "ok": group.ok,
                    "reason": group.reason,
                    "missing_members": list(group.missing_members),
                    "missing_proviso": list(group.missing_proviso),
                },
                "declared_coverage": sorted(split_subjects(split)),
                "before": before_disney,
                "after": after_disney,
            }
        )

        # ---- 上海动物园: 「动物」, no inline proviso -------------------------
        zsplit = declared_split(zoo_base["source_scope_exact"])
        assert zsplit is not None
        zspecs = propose_split_rows(zoo_base["source_scope_exact"])
        after_zoo = probe(
            [
                _rule(
                    zoo_base,
                    suffix=f"#{s['subject_scope_normalized']}",
                    scope=s["subject_scope_normalized"],
                    norm=s["normalization_type"],
                )
                for s in zspecs
            ],
            [],
        )
        zgroup = validate_split_group(
            zoo_base["source_scope_exact"],
            [s["subject_scope_normalized"] for s in zspecs],
        )
        report["targets"].append(
            {
                "place": "上海动物园",
                "candidate_rule_id": "w01-6f2bfd39d7",
                "candidate_uuid": zoo_base["id"],
                "source_scope_exact": zoo_base["source_scope_exact"],
                "current": {
                    "animal_scope": zoo_base["animal_scope"],
                    "subject_scope_normalized": zoo_base["subject_scope_normalized"],
                    "normalization_type": zoo_base["normalization_type"],
                    "gate": (
                        lambda v: {
                            "compatible": v.compatible,
                            "change": v.change,
                            "reason": v.reason,
                        }
                    )(
                        validate_source_scope_semantic_compatibility(
                            zoo_base["source_scope_exact"],
                            zoo_base["subject_scope_normalized"],
                            zoo_base["normalization_type"],
                        )
                    ),
                },
                "proposed_rows": zspecs,
                "proposed_carve_out": None,
                "group_verdict": {
                    "ok": zgroup.ok,
                    "reason": zgroup.reason,
                    "missing_members": list(zgroup.missing_members),
                    "missing_proviso": list(zgroup.missing_proviso),
                },
                "declared_coverage": sorted(split_subjects(zsplit)),
                "before": before_zoo,
                "after": after_zoo,
            }
        )

    report["open_questions"] = [
        {
            "id": "ZOO_GUIDE_DOG_AFTER_REMODEL",
            "question": (
                "上海动物园「动物」拆分后，导盲犬将由 unknown 变为 prohibited（来源原文无但书）。"
                "该结论是否受《无障碍环境建设法》等上位法影响，属法律判断，须人工确认。"
            ),
            "action": "HUMAN_DECISION",
        },
        {
            "id": "VOCABULARY_NON_PET_ANIMALS",
            "question": (
                "「动物」含平台主体词表未建模的动物（如观赏鸟、爬行类）。"
                "拆分只覆盖词表内 9 个主体；超出部分平台继续沉默（unknown），不算允许。"
            ),
            "action": "DOCUMENTED_LIMITATION",
        },
    ]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- console contrast -------------------------------------------------
    for t in report["targets"]:
        print(f"\n=== {t['place']}  {t['candidate_rule_id']} ===")
        print(f"来源术语: 「{t['source_scope_exact']}」")
        print(
            f"当前存储: animal_scope={t['current']['animal_scope']} "
            f"subject={t['current']['subject_scope_normalized']} "
            f"norm={t['current']['normalization_type']} "
            "→ gate compatible="
            f"{t['current']['gate']['compatible']} ({t['current']['gate']['change']})"
        )
        print(f"声明拆分: {[s['subject_scope_normalized'] for s in t['proposed_rows']]}")
        print(f"拆分完整性: ok={t['group_verdict']['ok']} — {t['group_verdict']['reason']}")
        print(f"覆盖主体 ({len(t['declared_coverage'])}): {t['declared_coverage']}")
        print(f"{'query':<10} {'before':<24} {'after':<24}")
        for b, a in zip(t["before"], t["after"], strict=True):
            print(f"{b['query']:<10} {b['effect']:<24} {a['effect']:<24}")
        if t["after"][1]["applied_exceptions"]:
            print(f"  导盲犬 after: 例外生效 {t['after'][1]['applied_exceptions']}")

    print(f"\nSCOPE_REMODEL_MUTATIONS = {report['mutations']}")
    print(f"SCOPE_REMODEL_FOLLOW_UP = {SEMANTIC_REMODEL_REQUIRED}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
