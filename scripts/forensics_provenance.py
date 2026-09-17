"""Read-only provenance forensics for governed databases (§4 / §7 / §10).

The production closure round needs one question answered for every suspicious
object, over and over: *why does this row exist*? Name-based guessing ("it has
a number in it, therefore it is a fixture") is exactly what §12 forbids, so
this tool collects the evidence that makes the classification decidable:

* the object itself plus its place/zone/operator parents,
* the Source and EvidenceBundle it hangs from (issuer, URL, artifact),
* every RuleCandidate that produced it and the audit trail around those
  candidates,
* any hit in the canonical fixture/seed registries in this repository,
* any Git reference to its identifier.

Classification itself is a human decision recorded elsewhere; this script only
produces the evidence, and it never writes to the database.

Usage::

    python scripts/forensics_provenance.py --db-name petaccess \\
        --rule-id decd5051-... --rule-id 440e419e-... \\
        --place-id <uuid> --out artifacts/.../L1_FORENSICS.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for extra in (str(ROOT / "scripts"), str(ROOT / "services" / "api")):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import psycopg  # noqa: E402
from dev_api_server import psycopg_url_for  # noqa: E402

from app.db.safety import DatabaseSafetyError, guard_for_psycopg  # noqa: E402

#: Directories that define what "fixture" and "demo seed" mean in this repo.
#: A hit here is positive evidence of provenance, not a suspicion.
REGISTRY_GLOBS: tuple[str, ...] = (
    "tests/fixtures/**/*",
    "tests/**/fixtures/**/*",
    "scripts/seed*.py",
    "scripts/*seed*.py",
    "scripts/*fixture*.py",
    "services/api/app/db/seed*.py",
    "docs/reality_audit/*.json",
    "docs/governance/publish_batches/*.json",
)

#: Name shapes that are *hints* only — never a deletion reason on their own.
SUSPICIOUS_NAME_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"(?i)(demo|sample|example|fixture|dummy|mock)", "generic_demo_word"),
    (r"(?i)演示", "chinese_demo_word"),
    (r"(?i)(test|qa|e2e|visual)[-_ ]?\d*", "test_prefix"),
    (r"\d{6,}$", "long_numeric_suffix"),
    (r"(?i)^(t|dbg|tmp|xxx)\d*", "short_dev_prefix"),
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _rows(cur: Any, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    cur.execute(sql, params)
    cols = [d.name for d in cur.description]
    out: list[dict[str, Any]] = []
    for row in cur.fetchall():
        rec: dict[str, Any] = {}
        for name, value in zip(cols, row, strict=False):
            rec[name] = value.isoformat() if isinstance(value, datetime) else value
        out.append(rec)
    return out


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def git_references(identifier: str) -> dict[str, Any]:
    """Any committed file that mentions the identifier, plus the defining file."""
    if not identifier:
        return {"checked": False}
    short = identifier.split("-")[0]
    try:
        proc = subprocess.run(
            ["git", "grep", "-l", "-F", "--", short],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - env
        return {"checked": False, "error": str(exc)}
    files = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    return {
        "checked": True,
        "token": short,
        "file_count": len(files),
        "files": sorted(files)[:40],
        "truncated": len(files) > 40,
    }


def registry_hits(identifier: str, name: str | None) -> dict[str, Any]:
    """Scan the canonical fixture/seed registries for the id or the name."""
    hits: list[dict[str, str]] = []
    for pattern in REGISTRY_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            needle = identifier or ""
            if needle and needle in text:
                hits.append({"path": str(path.relative_to(ROOT)), "matched": "id"})
                continue
            if name and name in text:
                hits.append({"path": str(path.relative_to(ROOT)), "matched": "name"})
    return {"hit_count": len(hits), "hits": hits[:40], "truncated": len(hits) > 40}


def name_hints(name: str | None) -> list[str]:
    if not name:
        return []
    return [label for pattern, label in SUSPICIOUS_NAME_PATTERNS if re.search(pattern, name)]


def rule_provenance(cur: Any, rule_id: str) -> dict[str, Any]:
    rules = _rows(cur, "select * from access_rule where id = %s", (rule_id,))
    if not rules:
        return {"rule_id": rule_id, "found": False}
    rule = rules[0]

    place = (
        _rows(
            cur,
            "select id, canonical_name, place_type, lifecycle_status, created_at, source_id "
            "from place where id = %s",
            (rule.get("place_id"),),
        )
        if rule.get("place_id")
        else []
    )
    zone = (
        _rows(cur, "select * from zone where id = %s", (rule.get("zone_id"),))
        if rule.get("zone_id")
        else []
    )
    source = (
        _rows(
            cur,
            "select id, source_type, issuer, issuer_verification, source_url, "
            "source_snapshot_ref, published_at, collected_at, directness, "
            "spatial_precision, notes from source where id = %s",
            (rule.get("source_id"),),
        )
        if rule.get("source_id")
        else []
    )
    candidates = _rows(
        cur,
        "select id, review_status, reviewer_id, review_note, published_rule_id, "
        "extraction_method, extraction_provider, internal_confidence, rule_layer, "
        "mandatory_level, animal_scope, action, effect, evidence_bundle_id, "
        "created_at, updated_at "
        "from rule_candidate where published_rule_id = %s order by created_at",
        (rule_id,),
    )
    evidence: list[dict[str, Any]] = []
    for cand in candidates:
        if cand.get("evidence_bundle_id"):
            evidence += _rows(
                cur,
                "select id, source_id, artifact_id, evidence_class, extraction_method, "
                "extraction_model, reviewer_id, quoted_fragment, captured_at, published_at "
                "from evidence_bundle where id = %s",
                (cand["evidence_bundle_id"],),
            )
    artifacts = (
        _rows(cur, "select * from source_artifact where source_id = %s", (rule.get("source_id"),))
        if rule.get("source_id")
        else []
    )
    candidates = _rows(
        cur,
        "select id, review_status, reviewer_id, review_note, published_rule_id, "
        "extraction_method, extraction_provider, internal_confidence, rule_layer, "
        "mandatory_level, animal_scope, action, effect, created_at, updated_at "
        "from rule_candidate where published_rule_id = %s order by created_at",
        (rule_id,),
    )
    audits: list[dict[str, Any]] = []
    for cand in candidates:
        audits.extend(
            _rows(
                cur,
                "select id, actor_user_id, actor_role, action, target_type, target_id, "
                "request_id, created_at, detail from audit_log "
                "where target_id = %s order by created_at",
                (cand["id"],),
            )
        )
    audits.extend(
        _rows(
            cur,
            "select id, actor_user_id, actor_role, action, target_type, target_id, "
            "request_id, created_at, detail from audit_log "
            "where target_id = %s order by created_at",
            (rule_id,),
        )
    )
    exceptions = _rows(
        cur,
        "select id, rule_id, animal_scope, effect, source_id, status, effective_from, "
        "effective_to, note, created_at from rule_exception where rule_id = %s",
        (rule_id,),
    )
    # Supersession is a back-pointer only: the newer row records
    # `supersedes_rule_id`, so "who supersedes me" is a reverse lookup.
    superseded_by = _rows(
        cur,
        "select id, status, effect, rule_layer, animal_scope, effective_from, updated_at "
        "from access_rule where supersedes_rule_id = %s",
        (rule_id,),
    )
    supersedes = (
        _rows(
            cur,
            "select id, status, effect, updated_at from access_rule where id = %s",
            (rule.get("supersedes_rule_id"),),
        )
        if rule.get("supersedes_rule_id")
        else []
    )
    return {
        "rule_id": rule_id,
        "found": True,
        "rule": rule,
        "place": place[0] if place else None,
        "zone": zone[0] if zone else None,
        "source": source[0] if source else None,
        "evidence_bundles": evidence,
        "artifacts": artifacts,
        "candidates": candidates,
        "audit_trail": audits,
        "rule_exceptions": exceptions,
        "supersedes": supersedes[0] if supersedes else None,
        "superseded_by": superseded_by,
        "registry_hits": registry_hits(rule_id, None),
        "git_references": git_references(rule_id),
    }


def place_provenance(cur: Any, place_id: str) -> dict[str, Any]:
    places = _rows(cur, "select * from place where id = %s", (place_id,))
    if not places:
        return {"place_id": place_id, "found": False}
    place = places[0]
    zones = _rows(cur, "select * from zone where place_id = %s order by created_at", (place_id,))
    zone_ids = [z["id"] for z in zones]
    # `access_rule` has no evidence_bundle_id: evidence hangs off the candidate
    # that was published, so it is joined through rule_candidate below.
    rules = _rows(
        cur,
        "select id, zone_id, rule_layer, animal_scope, action, effect, mandatory_level, "
        "status, source_id, created_at, updated_at, note "
        "from access_rule where place_id = %s order by created_at",
        (place_id,),
    )
    if zone_ids:
        rules += _rows(
            cur,
            "select id, zone_id, rule_layer, animal_scope, action, effect, mandatory_level, "
            "status, source_id, created_at, updated_at, note "
            "from access_rule where zone_id = any(%s) and (place_id is null or place_id <> %s) "
            "order by created_at",
            (zone_ids, place_id),
        )
    rule_ids = [r["id"] for r in rules]
    exceptions = (
        _rows(
            cur,
            "select id, rule_id, animal_scope, effect, source_id, status, created_at "
            "from rule_exception where rule_id = any(%s)",
            (rule_ids,),
        )
        if rule_ids
        else []
    )
    candidates = _rows(
        cur,
        "select id, review_status, reviewer_id, review_note, published_rule_id, "
        "extraction_method, rule_layer, animal_scope, action, effect, created_at, updated_at "
        "from rule_candidate where place_id = %s order by created_at",
        (place_id,),
    )
    if zone_ids:
        candidates += _rows(
            cur,
            "select id, review_status, reviewer_id, review_note, published_rule_id, "
            "extraction_method, rule_layer, animal_scope, action, effect, created_at, updated_at "
            "from rule_candidate where zone_id = any(%s) and (place_id is null or place_id <> %s) "
            "order by created_at",
            (zone_ids, place_id),
        )
    audits = _rows(
        cur,
        "select id, actor_user_id, actor_role, action, target_type, target_id, "
        "request_id, created_at from audit_log where target_id = %s order by created_at",
        (place_id,),
    )
    for cand in candidates:
        audits += _rows(
            cur,
            "select id, actor_user_id, actor_role, action, target_type, target_id, "
            "request_id, created_at from audit_log where target_id = %s order by created_at",
            (cand["id"],),
        )
    observations = _rows(
        cur,
        "select * from observation_candidate where place_id = %s order by created_at",
        (place_id,),
    )
    monitors = _rows(cur, "select * from source_monitor where place_id = %s", (place_id,))
    external_refs = _rows(cur, "select * from external_place_ref where place_id = %s", (place_id,))
    source_ids = {r["source_id"] for r in rules if r.get("source_id")}
    sources = (
        _rows(
            cur,
            "select id, source_type, issuer, source_url, published_at, collected_at, "
            "directness, notes from source where id = any(%s)",
            (sorted(source_ids),),
        )
        if source_ids
        else []
    )
    # Does any *other* place still depend on these sources? §8 forbids deleting a
    # shared real source just because a demo rule pointed at it.
    shared: list[dict[str, Any]] = []
    for src in sources:
        other_rules = _rows(
            cur,
            "select count(*)::int as n from access_rule where source_id = %s "
            "and (place_id is null or place_id <> %s)",
            (src["id"], place_id),
        )
        other_cands = _rows(
            cur,
            "select count(*)::int as n from rule_candidate where source_id = %s "
            "and (place_id is null or place_id <> %s)",
            (src["id"], place_id),
        )
        shared.append(
            {
                "source": src,
                "other_place_rule_refs": other_rules[0]["n"] if other_rules else 0,
                "other_place_candidate_refs": other_cands[0]["n"] if other_cands else 0,
            }
        )
    return {
        "place_id": place_id,
        "found": True,
        "place": place,
        "name_hints": name_hints(place.get("canonical_name")),
        "zone_count": len(zones),
        "zones": zones,
        "rule_count": len(rules),
        "rules": rules,
        "exception_count": len(exceptions),
        "exceptions": exceptions,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "observation_count": len(observations),
        "observations": observations,
        "source_monitors": monitors,
        "external_refs": external_refs,
        "sources": shared,
        "audit_trail": audits,
        "registry_hits": registry_hits(place_id, place.get("canonical_name")),
        "git_references": git_references(place_id),
        "name_git_references": git_references(place.get("canonical_name") or ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--rule-id", action="append", default=[])
    ap.add_argument("--place-id", action="append", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--replace", action="store_true")
    args = ap.parse_args()

    out_path = Path(args.out)
    if out_path.exists() and not args.replace:
        print(
            f"REFUSED — 取证产物已存在且默认不可覆盖：{out_path}\n"
            "  取证结果是分类决定的证据，覆盖它等于销毁证据。确需重跑请加 --replace。",
            file=sys.stderr,
        )
        return 2
    out_path.parent.mkdir(parents=True, exist_ok=True)

    doc: dict[str, Any] = {
        "at": _now(),
        "database": args.db_name,
        "rules": [],
        "places": [],
    }
    try:
        url = psycopg_url_for(args.db_name)
        if not url:
            print("无法解析数据库 URL", file=sys.stderr)
            return 3
        with psycopg.connect(url) as conn:
            guard = guard_for_psycopg(conn)
            doc["role"] = guard.role.value
            with conn.cursor() as cur:
                for rule_id in args.rule_id:
                    doc["rules"].append(rule_provenance(cur, rule_id))
                for place_id in args.place_id:
                    doc["places"].append(place_provenance(cur, place_id))
    except DatabaseSafetyError as exc:
        print(f"DATABASE_SAFETY_REFUSED: {exc}", file=sys.stderr)
        return 3

    out_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, default=_jsonable) + "\n",
        encoding="utf-8",
    )
    print(f"WROTE {out_path}")
    print(f"  database = {doc['database']}  role = {doc['role']}")
    print(f"  rules    = {len(doc['rules'])}")
    print(f"  places   = {len(doc['places'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
