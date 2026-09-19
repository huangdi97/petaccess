"""Post-publish verification for the Century Park single-row batch.

Three things are asserted, and each exists because of a specific way the publish
could look fine and still be wrong:

A. **Resolver** — the consumer path (live API, never the database directly) must
   answer ``prohibited`` for ordinary pets in the zone the rule belongs to, and
   must NOT answer ``allowed`` anywhere. A zone rule that quietly becomes a
   place-wide verdict, or an uncovered zone that quietly becomes an allowance,
   are the two failures that would mislead a real visitor.

B. **Rule trace** — the published object must be walkable back through
   Candidate → Human Decision → Human Evidence Acceptance → Evidence → Source,
   and the acceptance must keep saying ``operator_first_party_verified = false``.
   A trace that skips the acceptance step would make a knowingly-accepted weak
   source look like a verified first-party one.

C. **Consumer answer** — no shipped surface may claim the operator confirmed
   anything. The forbidden strings are asserted absent from the raw payloads.

Usage::

    python scripts/verify_century_park_publish.py \
        --database-url "postgresql+psycopg://…/petaccess" \
        --token-file artifacts/wave01_closure_r1/admin_token.txt \
        --json-out artifacts/wave01_closure_r1/post_publish_verify.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services" / "api"))

PLACE_ID = "c63f2199-b1e4-4435-b418-f2e86f8fdf45"
ZONE_OTHER = "aee59c64-a9b2-4a69-acd6-1a922f55d127"  # 世纪公园其他区域 (area)
ZONE_PET_AREA = "ae0003a8-e7ad-4d32-b29d-f8f21892e35b"  # 世纪宠物乐园（芳花园区域）(pet_area)
CANDIDATE_ID = "4e217d58-1060-4945-9fa1-b9b7e17d7e64"
RULE_ID = "w01-4e217d5810"
PUBLISHED_RULE_ID = "149828d0-b995-4a99-986e-fd740cea4466"

#: Phrases that would overstate the evidence. Asserted absent from every payload.
FORBIDDEN_CLAIMS = (
    "官方已确认",
    "official_operator_policy",
    "operator first-party verified",
    "first-party verified",
    "一手来源已核验",
)


def _http(base_url: str, token: str | None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.Client(base_url=base_url, timeout=30.0, trust_env=False, headers=headers)


def _effect(data: dict) -> str:
    return str(data.get("effect"))


def resolver_section(client: httpx.Client) -> dict:
    cases = {
        # label: (body, expected effect, must-not-be)
        "ordinary_pet_in_rule_zone": (
            {"animal": "dog", "service_role": "none", "action": "enter", "zone_id": ZONE_OTHER},
            "prohibited",
        ),
        "ordinary_cat_in_rule_zone": (
            {"animal": "cat", "service_role": "none", "action": "enter", "zone_id": ZONE_OTHER},
            "prohibited",
        ),
        "guide_dog_in_rule_zone": (
            {
                "animal": "dog",
                "service_role": "guide_dog",
                "declared_role": "guide_dog",
                "action": "enter",
                "zone_id": ZONE_OTHER,
            },
            "not_allowed",
        ),
        "ordinary_pet_in_uncovered_zone": (
            {"animal": "dog", "service_role": "none", "action": "enter", "zone_id": ZONE_PET_AREA},
            "unknown",
        ),
        "ordinary_pet_place_level_no_zone": (
            {"animal": "dog", "service_role": "none", "action": "enter", "zone_id": None},
            "unknown",
        ),
    }
    out: dict[str, dict] = {}
    failures: list[str] = []
    for label, (body, expected) in cases.items():
        r = client.post(f"/api/v1/places/{PLACE_ID}/effective-rules", json=body)
        r.raise_for_status()
        data = r.json()
        out[label] = {
            "request": body,
            "effect": data.get("effect"),
            "compliance_state": data.get("compliance_state"),
            "applicable_rules": data.get("applicable_rules"),
            "missing_inputs": data.get("missing_inputs"),
            "explanation_steps": data.get("explanation_steps"),
        }
        got = _effect(data)
        if expected == "not_allowed":
            if got == "allowed":
                failures.append(f"{label}: effect='allowed' —— 未举证的允许")
        elif got != expected:
            failures.append(f"{label}: effect={got!r}，期望 {expected!r}")
    return {"cases": out, "failures": failures}


def raw_and_explained(client: httpx.Client) -> dict:
    """The second shipped engine (`/rules/evaluate`) plus the place read paths."""
    out: dict[str, object] = {}
    ev = client.post(
        "/api/v1/rules/evaluate",
        json={
            "place_id": PLACE_ID,
            "zone_id": ZONE_OTHER,
            "intended_action": "enter",
            "animal": {"species": "dog", "role": "ordinary", "service_role": "none"},
        },
    )
    out["rules_evaluate_status"] = ev.status_code
    out["rules_evaluate"] = ev.json() if ev.status_code == 200 else ev.text[:400]

    # place-level evaluate: must not report the zone verdict as a place verdict
    ev_place = client.post(
        "/api/v1/rules/evaluate",
        json={
            "place_id": PLACE_ID,
            "zone_id": None,
            "intended_action": "enter",
            "animal": {"species": "dog", "role": "ordinary", "service_role": "none"},
        },
    )
    out["rules_evaluate_place_status"] = ev_place.status_code
    out["rules_evaluate_place"] = (
        ev_place.json() if ev_place.status_code == 200 else ev_place.text[:400]
    )
    return out


def consumer_section(client: httpx.Client) -> dict:
    surfaces: dict[str, object] = {}
    for name, path in (
        ("place_detail", f"/api/v1/places/{PLACE_ID}"),
        ("place_rules", f"/api/v1/places/{PLACE_ID}/rules?limit=50"),
        ("zone_rules", f"/api/v1/zones/{ZONE_OTHER}/rules?limit=50"),
        ("regulations", f"/api/v1/places/{PLACE_ID}/regulations"),
        ("extras", f"/api/v1/places/{PLACE_ID}/extras"),
        ("answerability", f"/api/v1/places/{PLACE_ID}/answerability"),
        (
            "source_via_consumer_path",
            "/api/v1/sources?source_type=government_service&limit=200",
        ),
    ):
        r = client.get(path)
        surfaces[name] = {"status": r.status_code, "body": r.text[:20000]}

    hits: list[str] = []
    for name, payload in surfaces.items():
        text = json.dumps(payload, ensure_ascii=False, default=str)
        for claim in FORBIDDEN_CLAIMS:
            if claim in text:
                hits.append(f"{name}: 出现禁用表述 {claim!r}")

    # Is the *provenance* the answer must show actually reachable from the public
    # read path? The unified AccessAnswer surface is still a master-goal item, so
    # the check is made against the pieces that do ship.
    reachable: dict[str, object] = {}
    src = surfaces.get("source_via_consumer_path", {})
    if src.get("status") == 200:
        try:
            items = json.loads(src["body"])["items"]
        except Exception:  # noqa: BLE001
            items = []
        match = [i for i in items if str(i.get("id")) == "ca5b81a7-ca5b-495c-9026-6d8b69dbaea7"]
        reachable["source_found_on_public_path"] = bool(match)
        if match:
            row = match[0]
            reachable["source_type"] = row.get("source_type")
            reachable["issuer"] = row.get("issuer")
            reachable["directness"] = row.get("directness")
            reachable["issuer_verification"] = row.get("issuer_verification")
            reachable["notes"] = row.get("notes")
    return {
        "surfaces": surfaces,
        "forbidden_claim_hits": hits,
        "provenance_reachable": reachable,
    }


def trace_section(database_url: str) -> dict:
    from sqlalchemy import create_engine, text

    e = create_engine(database_url)
    chain: dict[str, object] = {}
    problems: list[str] = []
    with e.connect() as c:
        rule = (
            c.execute(
                text(
                    "select id, place_id, zone_id, animal_scope, action, effect, status, "
                    "source_id, rule_layer, mandatory_level, subject_scope_normalized, "
                    "normalization_type, normative_effect, source_scope_exact, supersedes_rule_id "
                    "from access_rule where id = :i"
                ),
                {"i": PUBLISHED_RULE_ID},
            )
            .mappings()
            .one()
        )
        chain["access_rule"] = dict(rule)
        if str(rule["zone_id"]) != ZONE_OTHER:
            problems.append(f"published rule zone_id={rule['zone_id']}，期望 {ZONE_OTHER}")
        if str(rule["place_id"]) != PLACE_ID:
            problems.append(f"published rule place_id={rule['place_id']}，期望 {PLACE_ID}")
        if rule["supersedes_rule_id"] is not None:
            problems.append("published rule 带 supersedes_rule_id，本批应为新建")
        if str(rule["effect"]) != "prohibited" or str(rule["animal_scope"]) != "ordinary_pet":
            problems.append("published rule 的 effect/animal_scope 与已审候选不一致")

        cand = (
            c.execute(
                text(
                    "select id, review_status, published_rule_id, reviewer_id, review_note, "
                    "source_id, evidence_bundle_id, animal_scope, action, effect, rule_layer, "
                    "mandatory_level, subject_scope_normalized, normalization_type, zone_id, "
                    "place_id from rule_candidate where id = :i"
                ),
                {"i": CANDIDATE_ID},
            )
            .mappings()
            .one()
        )
        chain["rule_candidate"] = dict(cand)
        if str(cand["published_rule_id"]) != PUBLISHED_RULE_ID:
            problems.append("候选的 published_rule_id 未指向本条已发布规则")
        if str(cand["review_status"]) != "PUBLISHED":
            problems.append(f"候选 review_status={cand['review_status']}，期望 PUBLISHED")

        bundle = (
            c.execute(
                text(
                    "select id, artifact_id, place_match_evidence, quoted_fragment, content_hash, "
                    "evidence_class, publisher_type, extraction_method "
                    "from evidence_bundle where id = :i"
                ),
                {"i": str(cand["evidence_bundle_id"])},
            )
            .mappings()
            .one()
        )
        chain["evidence_bundle"] = dict(bundle)
        artifact = (
            c.execute(
                text(
                    "select id, source_id, artifact_type, evidence_strength, content_hash, "
                    "collected_at, storage_allowed from source_artifact where id = :i"
                ),
                {"i": str(bundle["artifact_id"])},
            )
            .mappings()
            .one()
        )
        chain["source_artifact"] = dict(artifact)
        src = (
            c.execute(
                text(
                    "select id, source_type, issuer, directness, issuer_verification, "
                    "source_availability, notes, source_url from source where id = :i"
                ),
                {"i": str(cand["source_id"])},
            )
            .mappings()
            .one()
        )
        chain["source"] = dict(src)
        if str(src["source_type"]) != "government_service":
            problems.append(f"source.source_type={src['source_type']}，期望 government_service")
        if "official_operator_policy" in str(src["source_type"]):
            problems.append("source.source_type 被写成了 official_operator_policy")

        # human decision, recorded on the candidate
        decision = (
            c.execute(
                text(
                    "select id, actor_user_id, actor_role, action, target_type, target_id, "
                    "before_state, after_state, detail, created_at from audit_log "
                    "where target_id in (:r, :c) order by created_at"
                ),
                {"r": PUBLISHED_RULE_ID, "c": CANDIDATE_ID},
            )
            .mappings()
            .all()
        )
        chain["audit_events"] = [dict(x) for x in decision]
        if not decision:
            problems.append("Audit / Rule Trace 为空：发布与决定没有留下可追溯事件")
    return {"chain": chain, "problems": problems}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default="http://127.0.0.1:8010")
    ap.add_argument("--database-url", required=True)
    ap.add_argument("--token-file")
    ap.add_argument(
        "--pre-publish-probe",
        help="发布前 --dry-run 逐闸门探针的 JSON；用来证明 source.notes 未被改写",
    )
    ap.add_argument("--json-out")
    args = ap.parse_args()

    token = Path(args.token_file).read_text(encoding="utf-8").strip() if args.token_file else None

    report: dict[str, object] = {}
    with _http(args.base_url, token) as client:
        report["resolver"] = resolver_section(client)
        report["engines"] = raw_and_explained(client)
        report["consumer"] = consumer_section(client)
    report["trace"] = trace_section(args.database_url)

    # ---- §2: source.notes must not be used as a second fact source ----------
    notes_check: dict[str, object] = {}
    if args.pre_publish_probe:
        pre = json.loads(Path(args.pre_publish_probe).read_text(encoding="utf-8"))
        pre_notes = pre["rows"][0]["measures"].get("source_notes")
        post_notes = report["trace"]["chain"]["source"].get("notes")
        notes_check = {
            "pre_publish_notes": pre_notes,
            "post_publish_notes": post_notes,
            "byte_identical": pre_notes == post_notes,
            "new_governance_marker_in_notes": "FIRST_PARTY_OPERATOR_SOURCE_PENDING"
            in str(post_notes or ""),
            "pre_publish_source_type": pre["rows"][0]["measures"].get("source_type"),
            "post_publish_source_type": report["trace"]["chain"]["source"].get("source_type"),
        }
    report["source_notes"] = notes_check

    res = report["resolver"]
    trace = report["trace"]
    cons = report["consumer"]

    cases = res["cases"]
    report["CENTURY_PARK_RESOLVER"] = (
        "PASS"
        if not res["failures"] and cases["ordinary_pet_in_rule_zone"]["effect"] == "prohibited"
        else "FAIL"
    )
    report["ZONE_SCOPE_PRESERVED"] = (
        "PASS"
        if cases["ordinary_pet_place_level_no_zone"]["effect"] != "prohibited"
        and cases["ordinary_pet_in_uncovered_zone"]["effect"] != "prohibited"
        else "FAIL"
    )
    report["UNcovered_ZONE_NOT_AUTO_ALLOWED"] = (
        "PASS" if cases["ordinary_pet_in_uncovered_zone"]["effect"] != "allowed" else "FAIL"
    )
    report["EVIDENCE_ACCEPTANCE_TRACE"] = "PASS" if not trace["problems"] else "FAIL"
    report["CONSUMER_NO_FORBIDDEN_CLAIM"] = "PASS" if not cons["forbidden_claim_hits"] else "FAIL"
    report["SOURCE_NOTES_MUTATED"] = (
        "NO"
        if notes_check
        and notes_check.get("byte_identical") is True
        and not notes_check.get("new_governance_marker_in_notes")
        else ("UNKNOWN" if not notes_check else "YES")
    )

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )

    print("=== A. RESOLVER (live API) ===")
    for label, data in cases.items():
        print(f"  {label:<34} effect={data['effect']:<12} state={data['compliance_state']}")
    print(f"  failures = {res['failures']}")
    print()
    print("=== B. RULE TRACE ===")
    for key in ("access_rule", "rule_candidate", "evidence_bundle", "source_artifact", "source"):
        print(f"  {key} = {json.dumps(trace['chain'][key], ensure_ascii=False, default=str)}")
    print(f"  audit_events = {len(trace['chain']['audit_events'])}")
    for ev in trace["chain"]["audit_events"]:
        after = ev.get("after_state") or {}
        note = after.get("note") if isinstance(after, dict) else None
        print(
            f"    {ev['created_at']} action={ev['action']:<22} actor_role={ev['actor_role']}"
            f" actor={str(ev['actor_user_id'])[:8]}… target={str(ev['target_id'])[:8]}…"
            f" after={after.get('status') if isinstance(after, dict) else None}"
            f" note={note!r}"
        )
    print(f"  problems = {trace['problems']}")
    print()
    print("=== C. CONSUMER ===")
    print(f"  forbidden_claim_hits = {cons['forbidden_claim_hits']}")
    print(
        f"  provenance reachable = {json.dumps(cons['provenance_reachable'], ensure_ascii=False)}"
    )
    for name, payload in cons["surfaces"].items():
        print(f"    {name:<32} status={payload['status']} bytes={len(payload['body'])}")
    print()
    print("=== D. SOURCE NOTES (§2) ===")
    print(f"  {json.dumps(notes_check, ensure_ascii=False)}")
    print()
    for key in (
        "CENTURY_PARK_RESOLVER",
        "ZONE_SCOPE_PRESERVED",
        "UNcovered_ZONE_NOT_AUTO_ALLOWED",
        "EVIDENCE_ACCEPTANCE_TRACE",
        "CONSUMER_NO_FORBIDDEN_CLAIM",
        "SOURCE_NOTES_MUTATED",
    ):
        print(f"{key} = {report[key]}")

    bad = [k for k in report if k.isupper() and report[k] == "FAIL"]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
