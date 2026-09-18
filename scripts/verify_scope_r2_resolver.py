"""Resolve the same questions against two databases and diff the answers.

Why this exists
---------------
"SCOPE-R2 got published" is not the claim anyone cares about. The claim is that
a user asking about a guide dog at Shanghai Disneyland gets a *different, and
correct*, answer afterwards — and that no answer changed anywhere else.

This probe runs the **canonical v0.5 resolver** (the same function the API
calls, ``app.rulespec.v05_resolver.resolve`` over ``_load_layered_rules``)
against any number of databases and prints a per-question matrix plus a diff.
Nothing is written.

Usage::

    python scripts/verify_scope_r2_resolver.py --db-name petaccess --label PROD
    python scripts/verify_scope_r2_resolver.py \
        --db-name petaccess --label PROD \
        --db-name petaccess_publish_rehearsal_scope_r2 --label REHEARSAL
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "services" / "api"))

from dev_api_server import database_url_for  # noqa: E402

#: (label, animal, service_role, declared_role). ``declared_role`` pins the
#: query to one precise animal role under ADR-025 — without it a guide-dog
#: question is just a dog question.
QUESTIONS: tuple[tuple[str, str, str, str | None], ...] = (
    ("普通犬", "dog", "none", None),
    ("导盲犬", "dog", "none", "guide_dog"),
    ("猫", "cat", "none", None),
    # The query vocabulary is the *species* keys the ontology expands:
    # ``other`` -> {other_pet}. Asking with ``other_pet`` expands to the empty
    # set and every answer comes back unknown, which looks like "the rule is
    # inert" when in fact the question was malformed.
    ("其他宠物", "other", "none", None),
)

PLACES = {
    "上海迪士尼乐园": "d85a4c00-3be9-48a5-ac31-d0486451ba69",
    "上海动物园": "5eabf910-b348-44f1-a7e9-1b9a5908a5f0",
}
ZONES = {
    "上海迪士尼乐园": "2c868f71-96d3-40d9-894b-aec9315d7948",
    "上海动物园": "ba951b98-34bb-409f-a2ba-bc1176c0528c",
}


def probe(db_name: str) -> dict[str, dict[str, str]]:
    from sqlalchemy.orm import sessionmaker

    from app.api.v1.v05 import _load_layered_rules
    from app.db.session import make_engine
    from app.rulespec.v05_resolver import resolve

    url = database_url_for(db_name)
    if url is None:
        raise SystemExit(f"无法解析 {db_name} 的 DATABASE_URL")
    factory = sessionmaker(bind=make_engine(url), autoflush=False, expire_on_commit=False)
    session = factory()

    out: dict[str, dict[str, str]] = {}
    for place_name, place_id in PLACES.items():
        grouped = _load_layered_rules(session, place_id)
        zone_id = ZONES[place_name]
        row: dict[str, str] = {}
        for label, animal, service_role, declared_role in QUESTIONS:
            rs = resolve(
                legal=grouped["legal"],
                guidance=grouped["guidance"],
                template_rules=grouped["template"],
                operator_rules=grouped["operator"],
                event_rules=grouped["events"],
                animal=animal,
                service_role=service_role,
                action="enter",
                zone_id=zone_id,
                now=datetime.now(UTC),
                exceptions=grouped["exceptions"],
                declared_role=declared_role,
                holder_context=None,
            )
            row[label] = str(getattr(rs, "effect", rs))
        out[place_name] = row
    session.close()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-name", action="append", default=[], help="可重复；按给出顺序探测")
    ap.add_argument("--label", action="append", default=[], help="与 --db-name 一一对应的名字")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    if not args.db_name:
        print("至少需要一个 --db-name")
        return 2
    labels = args.label or list(args.db_name)
    if len(labels) != len(args.db_name):
        print("--label 数量必须与 --db-name 一致")
        return 2

    results: dict[str, dict[str, dict[str, str]]] = {}
    for label, db_name in zip(labels, args.db_name, strict=True):
        results[label] = probe(db_name)

    order = [q[0] for q in QUESTIONS]
    print(f"{'场所':<16}{'库':<12}" + "".join(f"{q:<10}" for q in order))
    for place in PLACES:
        for label in labels:
            row = results[label][place]
            print(f"{place:<16}{label:<12}" + "".join(f"{row[q]:<10}" for q in order))
        print()

    if len(labels) >= 2:
        base, other = labels[0], labels[1]
        print(f"== diff: {base} -> {other} ==")
        changed = 0
        for place in PLACES:
            for q in order:
                before = results[base][place][q]
                after = results[other][place][q]
                if before != after:
                    changed += 1
                    print(f"  {place} / {q}: {before} -> {after}")
        print(f"  changed_cells = {changed}")

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"WROTE {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
