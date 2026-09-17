"""Pre/post real-publish snapshot for a governed publish batch.

The same script produces both sides of the comparison, because a PRE snapshot
written by one tool and a POST snapshot written by another can always be argued
away. It is read-only: it opens the database, reads, and writes one JSON file.

Two properties matter more than coverage:

* **Refuse to overwrite.** A pre-publish snapshot that can be silently replaced
  by a second run is not evidence of the state before the write. If ``--out``
  exists, this exits non-zero unless ``--replace`` is passed explicitly.
* **Fingerprint everything that must not move.** The point of the POST compare
  is not "did the 8 rules appear" (the receipt proves that) but "did anything
  *else* move" — another candidate, a signature, a HOLD, a Disney row. So every
  candidate is fingerprinted, not just the selected eight.

Usage::

    python scripts/real_publish_snapshot.py \
      --db-name petaccess \
      --out artifacts/real_publish_batch01b/PRE_PUBLISH_SNAPSHOT.json \
      --manifest docs/governance/publish_batches/R2_FINAL_R3_BATCH_01B.json \
      --registry docs/reality_audit/review_decisions_r2_final.json \
      --api-base http://127.0.0.1:8010
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import psycopg  # noqa: E402
from dev_api_server import psycopg_url_for  # noqa: E402

#: Same names the verification script uses; places are looked up by
#: ``place.canonical_name`` so PRE and POST cannot drift onto different rows.
PLACE_CANONICAL_NAMES: dict[str, str] = {
    "fairmont": "和平饭店（费尔蒙）",
    "library": "上海图书馆东馆",
    "starbucks": "星巴克臻选上海烘焙工坊",
}

#: (place key, query label) — the §11 resolver matrix, minus Disney (not in the batch).
PLACE_QUERIES: tuple[tuple[str, str], ...] = (
    ("fairmont", "ordinary_pet"),
    ("fairmont", "dog"),
    ("fairmont", "guide_dog"),
    ("library", "ordinary_pet"),
    ("library", "dog"),
    ("library", "guide_dog"),
    ("library", "police_dog"),
    ("library", "military_working_dog"),
    ("starbucks", "dog"),
    ("starbucks", "guide_dog"),
)

#: Canonical query shape, taken from ``verify_publish_r3.check_resolver``: a
#: working dog is ``service_role: working`` plus a ``declared_role``. Passing the
#: role as ``service_role`` silently answers "no applicable rules", which would
#: make a PRE/POST diff look like a real change.
QUERY_BODY: dict[str, dict[str, str]] = {
    "ordinary_pet": {"animal": "dog", "service_role": "none"},
    "dog": {"animal": "dog", "service_role": "none"},
    "guide_dog": {"animal": "dog", "service_role": "working", "declared_role": "guide_dog"},
    "police_dog": {"animal": "dog", "service_role": "working", "declared_role": "police_dog"},
    "military_working_dog": {
        "animal": "dog",
        "service_role": "working",
        "declared_role": "military_working_dog",
    },
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(cur, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    cur.execute(sql, params)
    cols = [d.name for d in cur.description]
    out = []
    for row in cur.fetchall():
        rec = {}
        for name, value in zip(cols, row, strict=False):
            rec[name] = value.isoformat() if isinstance(value, datetime) else value
        out.append(rec)
    return out


def _scalar(cur, sql: str, params: Sequence[Any] = ()) -> Any:
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else None


def db_section(conn, selected: Sequence[str], registry: dict[str, Any]) -> dict[str, Any]:
    by_rule = {str(r["rule_id"]): r for r in registry["rows"]}
    candidate_ids = [by_rule[r]["candidate_id"] for r in selected if r in by_rule]

    with conn.cursor() as cur:
        identity = {
            "current_database": _scalar(cur, "select current_database()"),
            "current_user": _scalar(cur, "select current_user"),
            "server_version": _scalar(cur, "show server_version"),
            "alembic_head": _scalar(
                cur,
                "select version_num from alembic_version",
            ),
        }

        counts = {
            "access_rule_total": _scalar(cur, "select count(*) from access_rule"),
            "access_rule_current": _scalar(
                cur, "select count(*) from access_rule where status = 'current'"
            ),
            "rule_exception_total": _scalar(cur, "select count(*) from rule_exception"),
            "rule_exception_current": _scalar(
                cur, "select count(*) from rule_exception where status = 'current'"
            ),
            "rule_candidate_total": _scalar(cur, "select count(*) from rule_candidate"),
            "audit_log_total": _scalar(cur, "select count(*) from audit_log"),
            "evidence_bundle_total": _scalar(cur, "select count(*) from evidence_bundle"),
            "source_total": _scalar(cur, "select count(*) from source"),
        }

        audit_watermark = _scalar(cur, "select max(created_at) from audit_log")
        audit_watermark = (
            audit_watermark.isoformat() if isinstance(audit_watermark, datetime) else None
        )

        # Every candidate, not just the eight: the POST compare needs to see an
        # unrelated candidate move.
        all_candidates = _rows(
            cur,
            "select id, place_id, zone_id, rule_layer, animal_scope, "
            "subject_scope_normalized, review_status, reviewer_id, review_note, "
            "published_rule_id, evidence_bundle_id, source_id, updated_at "
            "from rule_candidate order by id",
        )

        selected_candidates = _rows(
            cur,
            "select id, place_id, zone_id, rule_layer, animal_scope, "
            "subject_scope_normalized, review_status, reviewer_id, review_note, "
            "published_rule_id, evidence_bundle_id, source_id, updated_at "
            "from rule_candidate where id = any(%s) order by id",
            (list(candidate_ids),),
        )

        current_rules = _rows(
            cur,
            "select id, place_id, zone_id, rule_layer, animal_scope, "
            "source_scope_exact, subject_scope_normalized, normalization_type, "
            "normative_effect, holder_scope, effect, action, status, source_id, "
            "supersedes_rule_id, recorded_at, created_at from access_rule "
            "where status = 'current' order by id",
        )

        current_exceptions = _rows(
            cur,
            "select id, rule_id, animal_scope, source_scope_exact, "
            "subject_scope_normalized, normalization_type, normative_effect, "
            "holder_scope, effect, status, source_id, created_at "
            "from rule_exception where status = 'current' order by id",
        )

        # Lineage for the eight: candidate -> evidence bundle -> artifact -> source.
        lineage = []
        for cand in selected_candidates:
            bundle = _rows(
                cur,
                "select id, artifact_id, source_id, source_platform, source_url, "
                "evidence_class, content_hash, captured_at from evidence_bundle "
                "where id = (select evidence_bundle_id from rule_candidate where id = %s)",
                (cand["id"],),
            )
            src_rows: list[dict[str, Any]] = []
            if bundle:
                src_rows = _rows(
                    cur,
                    "select id, source_type, issuer, issuer_verification, "
                    "source_url, directness, published_at, collected_at "
                    "from source where id = %s",
                    (bundle[0].get("source_id"),),
                )
            artifacts = _rows(
                cur,
                "select id, source_platform, collector_type, artifact_type, "
                "source_url, content_hash, collected_at, publisher_type, "
                "evidence_strength from source_artifact where source_id = %s order by id",
                (bundle[0].get("source_id") if bundle else None,),
            )
            lineage.append(
                {
                    "candidate_id": cand["id"],
                    "evidence_bundle_id": cand.get("evidence_bundle_id"),
                    "source_id": cand.get("source_id"),
                    "evidence_bundle": bundle[0] if bundle else None,
                    "source": src_rows[0] if src_rows else None,
                    "artifacts": artifacts,
                }
            )

    return {
        "identity": identity,
        "counts": counts,
        "audit_watermark": audit_watermark,
        "candidates_all": all_candidates,
        "candidates_selected": selected_candidates,
        "access_rule_current": current_rules,
        "rule_exception_current": current_exceptions,
        "lineage_selected": lineage,
    }


def api_section(base: str | None, token: str | None, conn) -> dict[str, Any]:
    """Resolver + effective-rules answers, so PRE/POST can be diffed.

    Read-only. When the API is not up this records ``NOT_RUN`` rather than a
    fabricated "unchanged".
    """
    if not base:
        return {"status": "NOT_RUN", "reason": "no --api-base given"}

    import httpx

    with conn.cursor() as cur:
        places: dict[str, dict] = {}
        for key, name in PLACE_CANONICAL_NAMES.items():
            cur.execute("SELECT id FROM place WHERE canonical_name=%s", (name,))
            row = cur.fetchone()
            if not row:
                continue
            cur.execute(
                "SELECT id FROM zone WHERE place_id=%s ORDER BY created_at LIMIT 1", (row[0],)
            )
            zone = cur.fetchone()
            places[key] = {"place_id": row[0], "zone_id": zone[0] if zone else None, "name": name}

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    out: dict[str, Any] = {"status": "RUN", "places": places, "rows": [], "errors": []}
    with httpx.Client(base_url=base, timeout=30.0, trust_env=False, headers=headers) as c:
        for place, label in PLACE_QUERIES:
            info = places.get(place)
            if not info:
                out["errors"].append(f"{place}: place not found")
                continue
            body = {
                "action": "enter",
                "zone_id": info["zone_id"],
                **QUERY_BODY[label],
            }
            try:
                eff = c.post(f"/api/v1/places/{info['place_id']}/effective-rules", json=body)
                eff.raise_for_status()
                eff = eff.json()
                role = QUERY_BODY[label].get("declared_role")
                animal: dict[str, str] = {"species": "dog"}
                if role:
                    animal["service_role"] = role
                ev = c.post(
                    "/api/v1/rules/evaluate",
                    json={
                        "place_id": info["place_id"],
                        "zone_id": info["zone_id"],
                        "intended_action": "enter",
                        "animal": animal,
                    },
                )
                ev.raise_for_status()
                ev = ev.json()
            except Exception as exc:  # noqa: BLE001
                out["errors"].append(f"{place}/{label}: {type(exc).__name__}: {exc}")
                continue
            out["rows"].append(
                {
                    "place": place,
                    "query": label,
                    "place_id": info["place_id"],
                    "effective_rules_effect": eff.get("effect"),
                    "effective_rules_compliance_state": eff.get("compliance_state"),
                    "applied_exceptions": eff.get("applied_exceptions") or [],
                    "applicable_rule_count": len(eff.get("applicable_rules") or []),
                    "evaluate_status": ev.get("status"),
                }
            )
    if out["errors"]:
        out["status"] = "ERROR"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--api-base", default=None)
    ap.add_argument("--token", default=None)
    ap.add_argument("--label", default=None, help="PRE or POST")
    ap.add_argument(
        "--replace",
        action="store_true",
        help="允许覆盖已存在的快照（默认拒绝，pre-publish 快照必须不可覆盖）",
    )
    args = ap.parse_args()

    out_path = Path(args.out)
    if out_path.exists() and not args.replace:
        print(
            f"REFUSED — 快照已存在且默认不可覆盖：{out_path}\n"
            "  pre-publish 快照是发布前状态的证据，覆盖它就等于抹掉证据。\n"
            "  确需重跑请显式加 --replace。",
            file=sys.stderr,
        )
        return 2
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_path = Path(args.manifest)
    registry_path = Path(args.registry)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    selected = list(manifest["candidate_rule_ids"])

    url = psycopg_url_for(args.db_name)
    with psycopg.connect(url) as conn:
        db = db_section(conn, selected, registry)
        api = api_section(args.api_base, args.token, conn)

    doc = {
        "label": args.label or out_path.stem,
        "at": _now(),
        "database": args.db_name,
        "revision": manifest.get("revision"),
        "batch_id": manifest.get("batch_id"),
        "reviewer": manifest.get("reviewer"),
        "selected": selected,
        "registry_sha256": _sha256(registry_path),
        "manifest_sha256": _sha256(manifest_path),
        "db": db,
        "api": api,
    }
    payload = json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n"
    out_path.write_text(payload, encoding="utf-8")
    print(f"WROTE {out_path}")
    print(f"  database       = {db['identity']['current_database']}")
    print(f"  alembic_head   = {db['identity']['alembic_head']}")
    print(f"  access_rule    = {db['counts']['access_rule_current']} current")
    print(f"  rule_exception = {db['counts']['rule_exception_current']} current")
    print(f"  candidates     = {db['counts']['rule_candidate_total']}")
    print(f"  audit_log      = {db['counts']['audit_log_total']}")
    print(f"  api            = {doc['api']['status']}")
    print(f"  sha256         = {hashlib.sha256(payload.encode('utf-8')).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
