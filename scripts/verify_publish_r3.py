"""Rehearsal verification for the first real publish batch.

Run **after** the batch has been executed against the rehearsal database. Every
check here reads the world the way a consumer or an auditor would — through the
API, not through the tables it already trusts — because "the row exists" is not
the same claim as "the rule works".

What it checks, and why each one is a refusal rather than a report:

* **Linkage (§15/§16).** Every newly published rule must be reachable from its
  candidate, its evidence bundle, its source and its audit trail. An orphan
  published rule is unreviewable: nobody can say where it came from.
* **Resolver (§13).** The published rules must actually change the answer, and
  the *safety* direction matters more than the coverage direction. A HOLD'd
  carve-out must never turn a police dog into an allowed animal; answering
  UNKNOWN is acceptable, contradicting a held decision is not.
* **Consistency (§14).** The layered resolver and the consumer-facing evaluator
  are two engines over the same rules. They are allowed to be differently
  *detailed*; they are not allowed to disagree about allowed-vs-prohibited.
* **Idempotency (§17).** Re-running the batch must be a NOOP, not a second copy.
* **Rollback (§18).** Withdrawing a carve-out returns the answer to the base
  rule; withdrawing the base leaves UNKNOWN, never ALLOWED.
* **Supersession (§19).** A new version of a rule supersedes the old one, exactly
  one stays current, and neither self-supersession nor a cycle is possible.
* **Watch (§20).** A rule change notifies a watcher once, and a retry does not
  notify again.

The drills mutate the rehearsal database — that is the point of it existing.

Usage:
    python scripts/verify_publish_r3.py --db-name petaccess_publish_rehearsal_r3 --json
"""

# NOTE: no ``from __future__ import annotations`` — see scripts/publish_reviewed_r1.py.

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
API_DIR = REPO / "services" / "api"

#: Default batch. Every expectation below is *derived* from the manifest rather
#: than hardcoded, because the first real batch was narrowed after the rehearsal
#: found a semantic defect: BATCH-01 held 12 rows (6 base + 6 carve-out) including
#: two Disney rows whose carve-out is a dead exception under the current domain
#: resolver. BATCH-01A holds the other 10. Hardcoding "12/6/6" here would have
#: made this script unable to verify the narrowed batch — and worse, would have
#: made "the batch got smaller" look like "the audit got worse".
DEFAULT_MANIFEST = REPO / "docs" / "governance" / "publish_batches" / "R2_FINAL_R3_BATCH_01.json"
REGISTRY = REPO / "docs" / "reality_audit" / "review_decisions_r2_final.json"

#: rule_id prefix -> place key. The batch states *rules*; the drills query
#: *places*, so this is the one translation between the two vocabularies.
PLACE_OF_PREFIX = {
    "dl": "disney",
    "fp": "fairmont",
    "lib": "library",
    "sb": "starbucks",
}

PLACE_CANONICAL_NAMES = {
    "disney": "上海迪士尼乐园",
    "fairmont": "和平饭店（费尔蒙）",
    "library": "上海图书馆东馆",
    "starbucks": "星巴克臻选上海烘焙工坊",
}

#: What each place must answer once *its* rules are published. Keyed by place so
#: narrowing a batch removes a place's expectations rather than silently leaving
#: them to be evaluated against rules the batch never published.
RESOLVER_EXPECTATIONS = {
    "fairmont": {
        "ordinary_pet": "prohibited",
        "guide_dog": "exception-applied",
    },
    "library": {
        "ordinary_pet": "prohibited",
        "guide_dog": "exception-applied",
        # Both are HOLD in the signed register. A HOLD'd carve-out must never
        # make them allowed; UNKNOWN is acceptable, ALLOWED is not.
        "police_dog": "not-allowed",
        "military_working_dog": "not-allowed",
    },
    "starbucks": {
        "ordinary_pet": "prohibited",
        "guide_dog": "exception-applied",
    },
    "disney": {
        "ordinary_pet": "prohibited",
        "guide_dog": "exception-applied",
    },
}


def _batch_rule_ids(manifest_path: Path) -> list[str]:
    return [
        str(x) for x in json.loads(manifest_path.read_text(encoding="utf-8"))["candidate_rule_ids"]
    ]


def _batch_id(manifest_path: Path) -> str:
    return str(json.loads(manifest_path.read_text(encoding="utf-8"))["batch_id"])


def _exception_rule_ids() -> set[str]:
    """rule_ids the signed register classifies as a RuleException carve-out."""
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {
        str(e["rule_id"])
        for e in registry.get("exception_plan") or []
        if e.get("mode") == "rule_exception"
    }


def places_for_batch(rule_ids: Sequence[str]) -> list[str]:
    """Place keys this batch actually publishes rules for, in canonical order."""
    keys = {
        PLACE_OF_PREFIX[rid.split("-", 1)[0]]
        for rid in rule_ids
        if rid.split("-", 1)[0] in PLACE_OF_PREFIX
    }
    return [k for k in PLACE_CANONICAL_NAMES if k in keys]


def _psycopg_url(db_name: str) -> str:
    sys.path.insert(0, str(REPO / "scripts"))
    from dev_api_server import psycopg_url_for

    url = psycopg_url_for(db_name)
    assert url, "无法从 .env 解析 DATABASE_URL"
    return url


def _sqlalchemy_url(db_name: str) -> str:
    sys.path.insert(0, str(REPO / "scripts"))
    from dev_api_server import database_url_for

    url = database_url_for(db_name)
    assert url, "无法从 .env 解析 DATABASE_URL"
    return url


def _batch_rows(manifest_path: Path) -> list[dict]:
    """The batch's rows, read from the signed register at run time.

    The manifest names rule ids only — it deliberately carries no
    ``final_decision`` — so the rows (candidate ids, layers, decisions) always
    come from the register. Nothing about the batch is trusted because it is in
    a file; the file only says *which* rows.
    """
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_rule = {str(r["rule_id"]): r for r in registry["rows"]}
    return [by_rule[rule_id] for rule_id in _batch_rule_ids(manifest_path)]


# ============================================================ HTTP helpers


class Client:
    def __init__(self, base: str, token: str | None = None) -> None:
        import httpx

        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._c = httpx.Client(base_url=base, timeout=30.0, trust_env=False, headers=headers)

    def post(self, path: str, body: dict | None = None) -> Any:
        r = self._c.post(path, json=body if body is not None else {})
        if r.status_code >= 400:
            raise RuntimeError(f"POST {path} -> {r.status_code}: {r.text[:300]}")
        return r.json() if r.content else None

    def get(self, path: str) -> Any:
        r = self._c.get(path)
        if r.status_code >= 400:
            raise RuntimeError(f"GET {path} -> {r.status_code}: {r.text[:300]}")
        return r.json()


def admin_token(base_public: str, email: str, password: str) -> str:
    import httpx

    r = httpx.post(
        f"{base_public}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=20.0,
        trust_env=False,
    )
    r.raise_for_status()
    return str(r.json()["access_token"])


# ============================================================ pristine guard


def pristine_problems(conn, rows: list[dict]) -> list[str]:
    """Refuse to run the drills on a database that already carries drill damage.

    A rollback drill that runs twice proves nothing the second time — the base is
    already withdrawn, so "the answer fell back to UNKNOWN" is a fact about the
    previous run, not this one. Every check below is therefore about *state*, not
    about counts that drift as the source database grows.
    """
    problems: list[str] = []
    candidate_ids = [str(r["candidate_id"]) for r in rows]
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, review_status FROM rule_candidate WHERE id = ANY(%s)"
            " AND review_status <> 'PUBLISHED'",
            (candidate_ids,),
        )
        not_published = cur.fetchall()
        for cid, status in not_published:
            problems.append(f"候选 {cid} 状态={status}，本批尚未发布")

        cur.execute("SELECT count(*) FROM rule_candidate WHERE raw_text LIKE 'rehearsal %'")
        leftovers = int(cur.fetchone()[0])
        if leftovers:
            problems.append(f"库中存在 {leftovers} 条上次演练留下的 fixture 候选")

        cur.execute(
            "SELECT count(*) FROM rule_exception WHERE status <> 'current'"
            " AND rule_id IN (SELECT published_rule_id FROM rule_candidate WHERE id = ANY(%s))",
            (candidate_ids,),
        )
        withdrawn = int(cur.fetchone()[0])
        if withdrawn:
            problems.append(f"本批有 {withdrawn} 条例外已非 current（上次 rollback 演练痕迹）")

        cur.execute(
            "SELECT count(*) FROM access_rule WHERE status <> 'current'"
            " AND id IN (SELECT published_rule_id FROM rule_candidate WHERE id = ANY(%s))",
            (candidate_ids,),
        )
        not_current = int(cur.fetchone()[0])
        if not_current:
            problems.append(f"本批有 {not_current} 条规则已非 current（上次 rollback 演练痕迹）")
    return problems


# ============================================================ §15 / §16 linkage


def check_linkage(
    conn,
    rows: list[dict],
    *,
    exception_rule_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Every published rule must be traceable to candidate, evidence, source, audit.

    The expected audit counts are derived from the batch itself — N rows planned,
    of which the register classifies some as carve-outs — so a narrowed batch is
    verified on its own terms instead of against a remembered number.
    """
    exceptions = {str(x) for x in (exception_rule_ids or set())}
    expected_exception = sum(1 for r in rows if str(r["rule_id"]) in exceptions)
    expected_access_rule = len(rows) - expected_exception
    expected_transition = len(rows)
    candidate_ids = [str(r["candidate_id"]) for r in rows]
    out: dict[str, Any] = {"rules": [], "problems": [], "audit_problems": []}
    out["expected"] = {
        "rows": expected_transition,
        "access_rule": expected_access_rule,
        "rule_exception": expected_exception,
    }

    def problem(message: str, *, audit: bool = False) -> None:
        """Record a finding, and let it also count against the audit verdict."""
        out["problems"].append(message)
        if audit:
            out["audit_problems"].append(message)

    with conn.cursor() as cur:
        for row in rows:
            rule_id = str(row["rule_id"])
            cid = str(row["candidate_id"])
            cur.execute(
                "SELECT review_status, published_rule_id, source_id, evidence_bundle_id,"
                " rule_layer, mandatory_level FROM rule_candidate WHERE id=%s",
                (cid,),
            )
            cand = cur.fetchone()
            entry: dict[str, Any] = {"rule_id": rule_id, "candidate_id": cid}
            if cand is None:
                out["problems"].append(f"{rule_id}: 候选不存在")
                out["rules"].append(entry)
                continue
            status, published_rule_id, source_id, bundle_id, layer, mandatory = cand
            entry |= {
                "candidate_status": status,
                "published_rule_id": published_rule_id,
                "source_id": source_id,
                "evidence_bundle_id": bundle_id,
                "rule_layer": layer,
                "mandatory_level": mandatory,
            }
            if status != "PUBLISHED":
                out["problems"].append(f"{rule_id}: 候选状态={status}，未完成发布")
            if not published_rule_id:
                out["problems"].append(f"{rule_id}: 候选未记录 published_rule_id（孤儿发布）")

            # candidate -> source
            cur.execute(
                "SELECT id, source_type, issuer, source_url, source_availability"
                " FROM source WHERE id=%s",
                (source_id,),
            )
            src = cur.fetchone()
            entry["source"] = (
                {
                    "id": src[0],
                    "type": src[1],
                    "issuer": src[2],
                    "url": src[3],
                    "availability": src[4],
                }
                if src
                else None
            )
            if src is None:
                out["problems"].append(f"{rule_id}: 证据链断裂 — source {source_id} 不存在")

            # candidate -> evidence bundle -> artifact
            if bundle_id:
                cur.execute(
                    "SELECT id, artifact_id, source_id, content_hash"
                    " FROM evidence_bundle WHERE id=%s",
                    (bundle_id,),
                )
                bundle = cur.fetchone()
                entry["evidence_bundle"] = (
                    {
                        "id": bundle[0],
                        "artifact_id": bundle[1],
                        "source_id": bundle[2],
                        "content_hash": (bundle[3] or "")[:12],
                    }
                    if bundle
                    else None
                )
                if bundle is None:
                    out["problems"].append(
                        f"{rule_id}: 证据链断裂 — evidence_bundle {bundle_id} 不存在"
                    )
                else:
                    cur.execute(
                        "SELECT id, artifact_type, source_url, content_hash"
                        " FROM source_artifact WHERE id=%s",
                        (bundle[1],),
                    )
                    art = cur.fetchone()
                    entry["source_artifact"] = (
                        {
                            "id": art[0],
                            "type": art[1],
                            "url": art[2],
                            "content_hash": (art[3] or "")[:12],
                        }
                        if art
                        else None
                    )
                    if art is None:
                        out["problems"].append(
                            f"{rule_id}: 证据链断裂 — source_artifact {bundle[1]} 不存在"
                        )
            else:
                entry["evidence_bundle"] = None
                out["problems"].append(f"{rule_id}: 候选没有 evidence_bundle（无法回溯到原文）")

            out["rules"].append(entry)

        # audit linkage: every planned row must have transition + publish audit
        # rows. The two actions record their subject differently: `transition`
        # puts the candidate in `target_id` (it is the audited object) while
        # `publish` names it inside `after_state`. Matching on one shape for both
        # is how a complete audit trail can look like a missing one.
        cur.execute(
            "SELECT action, count(*) FROM audit_log WHERE"
            " (action='candidate.transition' AND target_type='rule_candidate'"
            "  AND target_id = ANY(%(ids)s))"
            " OR (action IN ('candidate.publish','candidate.publish_exception')"
            "  AND after_state->>'candidate_id' = ANY(%(ids)s))"
            " GROUP BY action ORDER BY action",
            {"ids": candidate_ids},
        )
        audit_by_action = {a: int(n) for a, n in cur.fetchall()}
        out["audit_by_action"] = audit_by_action
        for action, expected in (
            ("candidate.transition", expected_transition),
            ("candidate.publish", expected_access_rule),
            ("candidate.publish_exception", expected_exception),
        ):
            if audit_by_action.get(action, 0) < expected:
                problem(
                    f"审计不足：{action} 只有 {audit_by_action.get(action, 0)} 条，应为 {expected}",
                    audit=True,
                )

        cur.execute(
            "SELECT count(*) FROM audit_log WHERE action='candidate.publish_exception'"
            " AND after_state->>'base_rule_id' IS NOT NULL"
        )
        out["audit_exception_with_base"] = int(cur.fetchone()[0])
        if out["audit_exception_with_base"] < expected_exception:
            problem("例外发布审计缺少 base 依赖记录", audit=True)

        # reviewer (human) vs actor (executor) must be separately recorded
        cur.execute(
            "SELECT count(DISTINCT actor_user_id), count(DISTINCT after_state->>'status'),"
            " count(DISTINCT after_state->>'note') FROM audit_log"
            " WHERE action='candidate.transition' AND target_id = ANY(%s)",
            (candidate_ids,),
        )
        actors, statuses, notes = cur.fetchone()
        out["distinct_actors"] = int(actors)
        out["previous_statuses_recorded"] = int(statuses)
        out["transition_notes"] = int(notes)
        cur.execute(
            "SELECT count(*) FROM audit_log WHERE action='candidate.transition'"
            " AND target_id = ANY(%s) AND after_state->>'note' LIKE '%%huangdi97%%'",
            (candidate_ids,),
        )
        out["notes_naming_reviewer"] = int(cur.fetchone()[0])
        if out["notes_naming_reviewer"] < expected_transition:
            problem("审计中的人类评审员署名缺失：transition note 未记录 huangdi97", audit=True)
        # before/after state transition, not just an after-image
        cur.execute(
            "SELECT count(*) FROM audit_log WHERE action='candidate.transition'"
            " AND target_id = ANY(%s) AND before_state->>'status' = 'REVIEW_PENDING'"
            " AND after_state->>'status' = 'APPROVED'",
            (candidate_ids,),
        )
        out["transition_before_after_pairs"] = int(cur.fetchone()[0])
        if out["transition_before_after_pairs"] < expected_transition:
            problem("transition 审计缺少 before→after 状态对", audit=True)
    out["SOURCE_LINKAGE"] = (
        "PASS" if not any("source" in p or "孤儿" in p for p in out["problems"]) else "FAIL"
    )
    out["EVIDENCE_LINKAGE"] = (
        "PASS"
        if not any("证据链" in p or "evidence_bundle" in p for p in out["problems"])
        else "FAIL"
    )
    out["AUDIT_LINKAGE"] = "PASS" if not out["audit_problems"] else "FAIL"
    return out


# ============================================================ §13 resolver matrix


def check_resolver(
    client: Client,
    places: dict[str, dict],
    *,
    expectations: Mapping[tuple[str, str], str] | None = None,
) -> dict[str, Any]:
    """Query each place and assert the documented behaviour.

    ``expected`` is what §13 asks for. A mismatch is recorded, not smoothed over:
    the point of the rehearsal is to find out whether the published rules actually
    answer the way they were reviewed to.

    The expectation table is passed in because it belongs to the *batch*, not to
    this script: a batch that excludes a place must not keep asserting that
    place's documented answer, which would fail for the honest reason that the
    rules were never published.
    """
    expectations = dict(expectations or {})
    queries = {
        "ordinary_pet": {"animal": "dog", "service_role": "none"},
        "guide_dog": {"animal": "dog", "service_role": "working", "declared_role": "guide_dog"},
        "police_dog": {"animal": "dog", "service_role": "working", "declared_role": "police_dog"},
        "military_working_dog": {
            "animal": "dog",
            "service_role": "working",
            "declared_role": "military_working_dog",
        },
    }
    out: dict[str, Any] = {"observations": [], "mismatches": []}
    for place, info in places.items():
        for label, query in queries.items():
            body = {"action": "enter", "zone_id": info["zone_id"], **query}
            eff = client.post(f"/api/v1/places/{info['place_id']}/effective-rules", body)
            observation = {
                "place": place,
                "query": label,
                "zone_id": info["zone_id"],
                "effect": eff.get("effect"),
                "compliance_state": eff.get("compliance_state"),
                "applied_exceptions": eff.get("applied_exceptions") or [],
                "applicable_rule_count": len(eff.get("applicable_rules") or []),
                "explanation_steps": eff.get("explanation_steps") or [],
            }
            expected = expectations.get((place, label))
            observation["expected"] = expected
            if expected == "exception-applied":
                observation["verdict"] = (
                    "PASS"
                    if observation["applied_exceptions"] and observation["effect"] != "unknown"
                    else "FAIL"
                )
            elif expected == "not-allowed":
                observation["verdict"] = "PASS" if observation["effect"] != "allowed" else "FAIL"
            elif expected == "prohibited":
                observation["verdict"] = "PASS" if observation["effect"] == "prohibited" else "FAIL"
            else:
                observation["verdict"] = "OBSERVED"
            if observation["verdict"] == "FAIL":
                out["mismatches"].append(
                    f"{place}/{label}: 期望 {expected}，实际 effect={observation['effect']}"
                    f" applied_exceptions={observation['applied_exceptions']}"
                )
            out["observations"].append(observation)

        # the place-level (no zone) answer must NOT flatten a zone-scoped rule
        body = {
            "action": "enter",
            "animal": "dog",
            "service_role": "working",
            "declared_role": "guide_dog",
        }
        eff = client.post(f"/api/v1/places/{info['place_id']}/effective-rules", body)
        out["observations"].append(
            {
                "place": place,
                "query": "guide_dog_place_level_no_zone",
                "zone_id": None,
                "effect": eff.get("effect"),
                "compliance_state": eff.get("compliance_state"),
                "note": "zone 级规则不得压平成 place 总状态",
            }
        )
    out["RESOLVER_POST_PUBLISH"] = "PASS" if not out["mismatches"] else "FAIL"
    return out


# ================================== carve-out reachability (the Disney defect class)


def check_carve_out_reachability(conn, rows: list[dict]) -> dict[str, Any]:
    """Can each published carve-out actually fire on the subject it was written for?

    A ``RuleException`` is only reachable when the base rule it carves out of
    *governs* the carve-out's own subject. Under ADR-025 the semantic scope
    ``ordinary_pet`` covers ``{ordinary_dog, ordinary_cat, other_pet}`` and
    deliberately excludes the service roles — so a ``guide_dog`` carve-out bound
    to an ``ordinary_pet`` base can never apply. It is published, linked, audited
    and inert.

    That is exactly the Disney failure, and it is not unique to Disney: the same
    shape exists wherever an operator wrote 「宠物禁止，导盲犬除外」. Measuring it
    keeps it a fact rather than a suspicion, and stops a place whose *answer* is
    carried by another layer from being mistaken for a place whose carve-out
    works.
    """
    sys.path.insert(0, str(API_DIR))
    from app.rulespec.animal_scope import rule_governs

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_rule = {str(r["rule_id"]): r for r in registry["rows"]}
    exception_bases: dict[str, list[str]] = {}
    for entry in registry.get("exception_plan") or []:
        if entry.get("mode") != "rule_exception":
            continue
        exception_bases[str(entry["rule_id"])] = [
            str(b["rule_id"]) for b in entry.get("bases") or [] if b.get("same_layer")
        ]

    out: dict[str, Any] = {"carve_outs": [], "inert": [], "unevaluable": []}
    with conn.cursor() as cur:
        for row in rows:
            rule_id = str(row["rule_id"])
            bases = exception_bases.get(rule_id)
            if not bases:
                continue
            cur.execute(
                "SELECT subject_scope_normalized FROM rule_candidate WHERE id=%s",
                (str(row["candidate_id"]),),
            )
            got = cur.fetchone()
            carve_out_subject = got[0] if got else None
            for base_id in bases:
                base_row = by_rule.get(base_id)
                if base_row is None:
                    continue
                cur.execute(
                    "SELECT published_rule_id FROM rule_candidate WHERE id=%s",
                    (str(base_row["candidate_id"]),),
                )
                published = cur.fetchone()
                if not published or not published[0]:
                    continue
                cur.execute(
                    "SELECT ar.animal_scope, ar.subject_scope_normalized, ar.normalization_type,"
                    " (SELECT count(*) FROM rule_exception re WHERE re.rule_id=ar.id"
                    "  AND re.status='current')"
                    " FROM access_rule ar WHERE ar.id=%s",
                    (published[0],),
                )
                base = cur.fetchone()
                if base is None:
                    continue
                if carve_out_subject is None:
                    # Scope data is missing, so nothing is claimed. It is NOT
                    # counted as inert: "we could not measure it" and "we
                    # measured it and it cannot fire" are different findings,
                    # and only the second may release a base.
                    out["unevaluable"].append(
                        {
                            "rule_id": rule_id,
                            "base": base_id,
                            "base_scope": None,
                            "carve_out_scope": None,
                            "base_governs_carve_out_subject": None,
                            "exceptions_attached": 0,
                        }
                    )
                    continue
                governs = rule_governs(
                    frozenset({carve_out_subject}),
                    base[0],
                    base[1],
                    base[2],
                )
                entry = {
                    "rule_id": rule_id,
                    "base": base_id,
                    "base_scope": base[1],
                    "carve_out_scope": carve_out_subject,
                    "base_governs_carve_out_subject": governs,
                    "exceptions_attached": int(base[3]),
                }
                out["carve_outs"].append(entry)
                if not governs:
                    out["inert"].append(entry)
    #: §14 ZERO INERT RULES. An inert carve-out is a FAIL, not a limitation:
    #: "the batch published a rule that can never apply" is not a caveat, it is
    #: the defect this gate exists to stop. Unevaluable is a limitation, because
    #: it is a measurement gap rather than a measured defect — and it still does
    #: not count as a pass.
    out["UNREACHABLE_SELECTED"] = len(out["inert"])
    out["UNEVALUABLE_SELECTED"] = len(out["unevaluable"])
    if out["inert"]:
        out["CARVE_OUT_REACHABILITY"] = "FAIL"
        out["ZERO_INERT_RULES"] = "FAIL"
    elif out["unevaluable"]:
        out["CARVE_OUT_REACHABILITY"] = "PASS_WITH_LIMITATIONS"
        out["ZERO_INERT_RULES"] = "PASS_WITH_LIMITATIONS"
    else:
        out["CARVE_OUT_REACHABILITY"] = "PASS"
        out["ZERO_INERT_RULES"] = "PASS"
    return out


# ============================================================ §14 engine consistency


def check_engine_consistency(client: Client, places: dict[str, dict]) -> dict[str, Any]:
    """Layered resolver vs consumer-facing evaluator, on the same question.

    Only allowed-vs-not-allowed is compared. The two engines legitimately differ
    in vocabulary (``conditional`` vs MATCH, ``unknown`` vs UNKNOWN); they must not
    differ in whether an animal may enter.
    """
    out: dict[str, Any] = {"rows": [], "disagreements": []}
    for place, info in places.items():
        for role in ("none", "working"):
            eff = client.post(
                f"/api/v1/places/{info['place_id']}/effective-rules",
                {
                    "action": "enter",
                    "zone_id": info["zone_id"],
                    "animal": "dog",
                    "service_role": role,
                },
            )
            evaluated = client.post(
                "/api/v1/rules/evaluate",
                {
                    "place_id": info["place_id"],
                    "zone_id": info["zone_id"],
                    "intended_action": "enter",
                    "animal": {"species": "dog", "service_role": role},
                },
            )
            resolver_allows = eff.get("effect") in ("allowed", "conditional")
            evaluator_allows = evaluated.get("status") in ("MATCH", "ALLOWED")
            out["rows"].append(
                {
                    "place": place,
                    "service_role": role,
                    "resolver_effect": eff.get("effect"),
                    "evaluator_status": evaluated.get("status"),
                    "evaluator_reason_codes": evaluated.get("reason_codes"),
                    "resolver_allows": resolver_allows,
                    "evaluator_allows": evaluator_allows,
                }
            )
            if resolver_allows != evaluator_allows:
                out["disagreements"].append(
                    f"{place}/service_role={role}: resolver={eff.get('effect')}"
                    f" vs evaluate={evaluated.get('status')}"
                )
    out["EFFECTIVE_RULES_API"] = "PASS"
    out["ENGINE_CONSISTENCY"] = "PASS" if not out["disagreements"] else "FAIL"
    return out


# ============================================================ §18 rollback drill


def rollback_drill(client: Client, conn, places: dict[str, dict]) -> dict[str, Any]:
    """Withdraw the Starbucks carve-out, then the base; prove nothing is deleted."""
    out: dict[str, Any] = {"steps": [], "problems": []}
    sb = places["starbucks"]
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM rule_exception WHERE rule_id IN"
            " (SELECT id FROM access_rule WHERE place_id=%s AND rule_layer='LEGAL')",
            (sb["place_id"],),
        )
        exc_ids = [r[0] for r in cur.fetchall()]
        cur.execute(
            "SELECT id FROM access_rule WHERE place_id=%s"
            " AND rule_layer='LEGAL' AND status='current'",
            (sb["place_id"],),
        )
        base_ids = [r[0] for r in cur.fetchall()]

    if len(exc_ids) != 1 or len(base_ids) != 1:
        out["problems"].append(f"rollback 目标不唯一：exceptions={exc_ids} bases={base_ids}")
        out["ROLLBACK_DRILL"] = "FAIL"
        return out
    exc_id, base_id = exc_ids[0], base_ids[0]
    out["target"] = {"base_rule_id": base_id, "rule_exception_id": exc_id}

    def snapshot(label: str) -> dict[str, Any]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT (SELECT count(*) FROM access_rule WHERE id=%s),"
                " (SELECT count(*) FROM rule_exception WHERE id=%s),"
                " (SELECT count(*) FROM evidence_bundle WHERE id IN"
                "   (SELECT evidence_bundle_id FROM rule_candidate WHERE published_rule_id=%s)),"
                " (SELECT count(*) FROM source WHERE id IN"
                "   (SELECT source_id FROM access_rule WHERE id=%s)),"
                " (SELECT count(*) FROM audit_log WHERE after_state->>'base_rule_id'=%s"
                "   OR target_id=%s OR target_id=%s)",
                (base_id, exc_id, base_id, base_id, base_id, base_id, exc_id),
            )
            rule_row, exc_row, bundles, sources, audits = cur.fetchone()
        return {
            "step": label,
            "access_rule_row_present": bool(rule_row),
            "rule_exception_row_present": bool(exc_row),
            "evidence_bundles": int(bundles),
            "sources": int(sources),
            "audit_rows": int(audits),
        }

    out["steps"].append(snapshot("before"))
    for key, value in out["steps"][0].items():
        if key.startswith(("access_rule_row", "rule_exception_row")) and not value:
            out["problems"].append(f"rollback 前缺少 {key}")

    # --- step 1: withdraw the carve-out through the API -----------------------
    client.post(
        f"/api/v1/admin/rule-exceptions/{exc_id}/transition",
        {"target": "withdrawn", "note": "rehearsal rollback drill — carve-out withdrawn"},
    )
    eff = client.post(
        f"/api/v1/places/{sb['place_id']}/effective-rules",
        {
            "action": "enter",
            "zone_id": sb["zone_id"],
            "animal": "dog",
            "service_role": "working",
            "declared_role": "guide_dog",
        },
    )
    out["after_exception_withdrawn"] = {
        "effect": eff.get("effect"),
        "applied_exceptions": eff.get("applied_exceptions") or [],
        "verdict": "FAIL" if eff.get("effect") == "allowed" else "PASS",
    }
    if eff.get("effect") == "allowed":
        out["problems"].append("撤回例外后 guide_dog 仍为 allowed —— 撤回未生效")
    out["steps"].append(snapshot("after_exception_withdrawn"))

    # --- step 2: withdraw the base rule (no API path exists — DB drill) -------
    with conn.cursor() as cur:
        cur.execute("UPDATE access_rule SET status='withdrawn' WHERE id=%s", (base_id,))
    eff = client.post(
        f"/api/v1/places/{sb['place_id']}/effective-rules",
        {
            "action": "enter",
            "zone_id": sb["zone_id"],
            "animal": "dog",
            "service_role": "working",
            "declared_role": "guide_dog",
        },
    )
    out["after_base_withdrawn"] = {
        "effect": eff.get("effect"),
        "compliance_state": eff.get("compliance_state"),
        "verdict": "PASS" if eff.get("effect") == "unknown" else "FAIL",
    }
    if eff.get("effect") != "unknown":
        out["problems"].append(f"撤回 base 后应回落 UNKNOWN，实际 {eff.get('effect')!r}")
    eff_ordinary = client.post(
        f"/api/v1/places/{sb['place_id']}/effective-rules",
        {"action": "enter", "zone_id": sb["zone_id"], "animal": "dog", "service_role": "none"},
    )
    out["after_base_withdrawn_ordinary"] = {"effect": eff_ordinary.get("effect")}
    if eff.get("effect") == "allowed":
        out["problems"].append("WITHDRAWN → ALLOWED：撤回规则不得变成允许")
    out["steps"].append(snapshot("after_base_withdrawn"))

    final = out["steps"][-1]
    for key in ("access_rule_row_present", "rule_exception_row_present"):
        if not final[key]:
            out["problems"].append(f"rollback 后 {key} = False —— 历史被删除")
    if final["audit_rows"] < out["steps"][0]["audit_rows"]:
        out["problems"].append("rollback 后审计行数减少")

    out["ROLLBACK_DRILL"] = "PASS" if not out["problems"] else "FAIL"
    return out


# ============================================================ §19 supersession drill


def supersession_drill(client: Client, conn, places: dict[str, dict]) -> dict[str, Any]:
    """Build a V2 fixture, publish it through the real path, and inspect history."""
    import uuid

    out: dict[str, Any] = {"problems": []}
    lib = places["library"]
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ar.id, ar.source_id, ar.zone_id, ar.animal_scope, ar.action, ar.rule_layer,"
            " ar.mandatory_level, ar.source_scope_exact, ar.subject_scope_normalized,"
            " ar.normalization_type, rc.evidence_bundle_id, rc.id"
            " FROM access_rule ar JOIN rule_candidate rc ON rc.published_rule_id = ar.id"
            " WHERE ar.place_id=%s AND ar.rule_layer='LEGAL' AND ar.status='current'"
            " ORDER BY ar.recorded_at DESC LIMIT 1",
            (lib["place_id"],),
        )
        row = cur.fetchone()
    if row is None:
        out["problems"].append("找不到 V1（library LEGAL current 规则）")
        out["SUPERSESSION_DRILL"] = "FAIL"
        return out
    (
        v1_id,
        source_id,
        zone_id,
        scope,
        action,
        layer,
        mandatory,
        exact,
        normalized,
        norm_type,
        bundle_id,
        v1_candidate,
    ) = row
    out["v1"] = {"rule_id": v1_id, "source_id": source_id, "layer": layer}

    # ---- fixture: a V2 candidate identical in owner+scope+action ------------
    v2_candidate = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO rule_candidate (id, source_id, place_id, zone_id, animal_scope, action,"
            " effect, rule_layer, mandatory_level, extraction_method, review_status,"
            " evidence_bundle_id, source_scope_exact, subject_scope_normalized, normalization_type,"
            " raw_text, created_at, updated_at)"
            " SELECT %s, source_id, place_id, zone_id, animal_scope, action, effect, rule_layer,"
            " mandatory_level, 'import', 'APPROVED', evidence_bundle_id, source_scope_exact,"
            " subject_scope_normalized, normalization_type, %s, now(), now()"
            " FROM rule_candidate WHERE id=%s",
            (v2_candidate, "rehearsal supersession drill V2", v1_candidate),
        )
    out["v2_candidate_id"] = v2_candidate

    published = client.post(f"/api/v1/admin/candidates/{v2_candidate}/publish", {})
    v2_id = published.get("published_rule_id")
    out["v2"] = {"rule_id": v2_id, "layer": published.get("rule_layer")}
    if not v2_id or v2_id == v1_id:
        out["problems"].append("V2 发布未产生新规则")
        out["SUPERSESSION_DRILL"] = "FAIL"
        return out

    with conn.cursor() as cur:
        cur.execute("SELECT status, supersedes_rule_id FROM access_rule WHERE id=%s", (v1_id,))
        v1_status, v1_supersedes = cur.fetchone()
        cur.execute("SELECT status, supersedes_rule_id FROM access_rule WHERE id=%s", (v2_id,))
        v2_status, v2_supersedes = cur.fetchone()
        cur.execute(
            "SELECT count(*) FROM access_rule WHERE zone_id=%s AND source_id=%s"
            " AND animal_scope=%s AND action=%s AND status='current'",
            (zone_id, source_id, scope, action),
        )
        current_count = int(cur.fetchone()[0])

    out["v1_status"] = v1_status
    out["v2_status"] = v2_status
    out["v2_supersedes"] = v2_supersedes
    out["current_versions_for_identity"] = current_count

    if v1_status != "superseded":
        out["problems"].append(f"V1 状态应为 superseded，实际 {v1_status!r}")
    if v2_status != "current":
        out["problems"].append(f"V2 状态应为 current，实际 {v2_status!r}")
    if v2_supersedes != v1_id:
        out["problems"].append("V2.supersedes_rule_id 未指向 V1")
    if v1_supersedes == v1_id:
        out["problems"].append("V1 把自己列为 supersedes 目标")
    if v2_supersedes == v2_id:
        out["problems"].append("self-supersede：V2 把自己列为 supersedes 目标")
    if current_count != 1:
        out["problems"].append(f"同一身份存在 {current_count} 条 current 版本，应恰好 1 条")

    # ---- cycle check with the publisher's own detector ---------------------
    sys.path.insert(0, str(REPO / "scripts"))
    import publish_reviewed_r1 as pub

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, supersedes_rule_id FROM access_rule"
            " WHERE supersedes_rule_id IS NOT NULL AND place_id=%s",
            (lib["place_id"],),
        )
        edges = {str(a): str(b) for a, b in cur.fetchall()}
    cycles = pub.supersession_cycles(edges)
    out["supersession_edges"] = len(edges)
    out["cycles"] = [" -> ".join(c) for c in cycles]
    if cycles:
        out["problems"].append(f"检测到 supersede 环：{cycles}")

    out["SUPERSESSION_DRILL"] = "PASS" if not out["problems"] else "FAIL"
    return out


# ============================================================ §20 watch drill


def watch_drill(
    db_name: str, client: Client, places: dict[str, dict], user_id: str
) -> dict[str, Any]:
    """Rule change → notification once; retry → no duplicate; mock sink only."""
    out: dict[str, Any] = {"problems": []}
    os.environ["DATABASE_URL"] = _sqlalchemy_url(db_name)
    sys.path.insert(0, str(API_DIR))

    import redis as _redis

    from app.core.config import get_settings

    sink = _redis.Redis.from_url(get_settings().redis_url, decode_responses=True)
    #: Captured before any sweep: the mock sink is append-only and shared across
    #: runs, so "how many messages exist" says nothing without a baseline.
    out["sink_baseline"] = len(sink.lrange("mock:notifications", 0, -1))
    library_name = places["library"]["name"]

    from app.db.session import get_session_factory
    from app.models import WatchSubscription
    from app.models.enums import WatchStatus, WatchTargetType
    from app.worker.tasks import notify_rule_changes

    lib = places["library"]
    session = get_session_factory()()
    try:
        existing = (
            session.query(WatchSubscription)
            .filter_by(
                user_id=user_id, target_type=WatchTargetType.PLACE, target_id=lib["place_id"]
            )
            .one_or_none()
        )
        if existing is None:
            watch = WatchSubscription(
                user_id=user_id,
                target_type=WatchTargetType.PLACE,
                target_id=lib["place_id"],
                channels=["in_app"],
                status=WatchStatus.ACTIVE,
                last_notified_at=None,
            )
            session.add(watch)
        else:
            watch = existing
            watch.status = WatchStatus.ACTIVE
            watch.last_notified_at = None
        session.commit()
        out["fixture_watch_id"] = str(watch.id)
        out["last_notified_before"] = None

        # Simulate the source-change lane with the real service code: a fetched
        # page becomes an artifact + bundle, never a direct rule mutation.
        from app.models import SourceMonitor
        from app.services.evidence_service import record_monitor_change
        from app.services.source_monitor import FetchResult

        monitor = session.query(SourceMonitor).filter_by(place_id=lib["place_id"]).one_or_none()
        out["monitor_fixture"] = "existing" if monitor else "none"
        if monitor is None:
            out["source_change_step"] = (
                "SKIPPED — 该场所没有 SourceMonitor 记录；SSRF 守卫禁止抓取本机地址，"
                "因此不构造假的外部抓取。变更→证据链由 verification fixture 直接提供。"
            )
        else:
            changed = record_monitor_change(
                session,
                monitor,
                fetch_result=FetchResult(
                    ok=True,
                    content_hash="rehearsal-drill-hash-0000000000000000000000000000",
                    etag=None,
                    last_modified=None,
                    body_excerpt="rehearsal drill: 模拟来源页面变更",
                    error_code=None,
                ),
                previous_hash=monitor.content_hash,
                diff_note="rehearsal watch drill",
            )
            session.commit()
            out["source_change_step"] = (
                "artifact+bundle created" if changed else "no usable content"
            )

        first = notify_rule_changes()
        out["first_sweep"] = first
        session.expire_all()
        out["last_notified_after_sweep1"] = str(
            session.get(WatchSubscription, watch.id).last_notified_at
        )
        second = notify_rule_changes()
        out["retry_sweep"] = second
        session.expire_all()
        out["last_notified_after_sweep2"] = str(
            session.get(WatchSubscription, watch.id).last_notified_at
        )
    finally:
        session.close()

    r = sink
    delivered = r.lrange("mock:notifications", 0, -1)
    out["mock_sink_total_messages"] = len(delivered)

    # The sweep is global: it notifies *every* eligible watch, and the cloned
    # database carries dozens of pre-existing subscriptions whose rules also
    # changed recently. So the assertion is scoped to this drill's own watch —
    # counting global notifications would be measuring other people's watches.
    mine: list[dict] = []
    for raw in delivered[out["sink_baseline"] :]:
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if item.get("user_id") == user_id and library_name in str(item.get("title") or ""):
            mine.append(item)
    out["drill_notifications"] = mine
    out["mock_sink_new_messages"] = len(delivered) - out["sink_baseline"]

    if len(mine) != 1:
        out["problems"].append(
            f"本次演练的订阅收到 {len(mine)} 次通知，应恰好 1 次"
            "（首次 sweep 通知一次，retry 不得重复）"
        )
    if int(first.get("notified_watches", 0)) < 1:
        out["problems"].append("首次 sweep 未产生任何通知")
    if not (first.get("notified_watches", 0) and second.get("notified_watches", 0) == 0):
        out["sweep_counts_note"] = (
            "全局 notified_watches 计数受库中既有订阅影响，不能作为幂等证据；"
            "幂等结论以本次订阅的 drill_notifications 为准（应恰好 1 条）"
        )

    out["WATCH_DRILL"] = "PASS" if not out["problems"] else "FAIL"
    return out


# ============================================================ main


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-name", default="petaccess_publish_rehearsal_r3")
    ap.add_argument("--api", default="http://127.0.0.1:8010")
    ap.add_argument(
        "--batch-file",
        default=str(DEFAULT_MANIFEST),
        help="被验证的批次清单；审计期望与解析矩阵都从它派生",
    )
    ap.add_argument("--email", default="admin@demo-petaccess.com")
    ap.add_argument("--password", default="admin12345")
    ap.add_argument("--out", default=None)
    ap.add_argument(
        "--skip-drills",
        action="store_true",
        help="只跑 linkage / resolver / engine 一致性（不改造 rehearsal 库状态）",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    token = admin_token(args.api, args.email, args.password)
    # paths below carry the full `/api/v1/...` prefix, so the client base is the host root
    client = Client(args.api, token)

    import psycopg

    conn = psycopg.connect(_psycopg_url(args.db_name), autocommit=True)

    manifest = Path(args.batch_file)
    batch_id = _batch_id(manifest)
    batch_rule_ids = _batch_rule_ids(manifest)

    # Resolve every known place: the rollback / supersession / watch drills have
    # fixed targets, independent of which batch is being verified.
    all_places: dict[str, dict] = {}
    with conn.cursor() as cur:
        for key, name in PLACE_CANONICAL_NAMES.items():
            cur.execute("SELECT id FROM place WHERE canonical_name=%s", (name,))
            place_id = cur.fetchone()[0]
            cur.execute(
                "SELECT id FROM zone WHERE place_id=%s ORDER BY created_at LIMIT 1", (place_id,)
            )
            zone_id = cur.fetchone()[0]
            all_places[key] = {"place_id": place_id, "zone_id": zone_id, "name": name}

    #: Only the places this batch publishes for are graded. Resolver and engine
    #: consistency are claims about *published* rules, so a place the batch never
    #: touched is not evidence either way — and for Disney specifically it would
    #: grade a known open defect against a batch that deliberately excludes it.
    batch_place_keys = places_for_batch(batch_rule_ids)
    places: dict[str, dict] = {k: all_places[k] for k in batch_place_keys}
    expectations = {
        (place, query): verdict
        for place in batch_place_keys
        for query, verdict in RESOLVER_EXPECTATIONS.get(place, {}).items()
    }

    rows = _batch_rows(manifest)
    if not args.skip_drills:
        dirty = pristine_problems(conn, rows)
        if dirty:
            print("REFUSED — rehearsal 库不是干净的『已发布、未演练』状态：")
            for problem in dirty:
                print(f"  - {problem}")
            print("\n先重建：python scripts/rehearsal_db.py --clone --confirm，再执行本批次。")
            conn.close()
            return 4

    report: dict[str, Any] = {
        "batch_id": batch_id,
        "manifest": str(manifest),
        "selected": batch_rule_ids,
        "places_verified": batch_place_keys,
        "db_name": args.db_name,
        "at": datetime.now(UTC).isoformat(),
        "places": places,
        "linkage": check_linkage(conn, rows, exception_rule_ids=_exception_rule_ids()),
        "resolver": check_resolver(client, places, expectations=expectations),
        "engine_consistency": check_engine_consistency(client, places),
        "carve_out_reachability": check_carve_out_reachability(conn, rows),
    }
    if args.skip_drills:
        report["rollback"] = {"ROLLBACK_DRILL": "NOT_RUN", "problems": []}
        report["supersession"] = {"SUPERSESSION_DRILL": "NOT_RUN", "problems": []}
        report["watch"] = {"WATCH_DRILL": "NOT_RUN", "problems": []}
    else:
        # The drills have fixed targets (the Starbucks dependency pair, the
        # library's LEGAL rule), so they read the full place map rather than the
        # graded subset — a narrowed batch must not disable a rollback drill.
        report["rollback"] = rollback_drill(client, conn, all_places)
        report["supersession"] = supersession_drill(client, conn, all_places)
        me = client.get("/api/v1/auth/me")
        report["watch"] = watch_drill(args.db_name, client, all_places, str(me["id"]))

    checks = {
        "SOURCE_LINKAGE": report["linkage"]["SOURCE_LINKAGE"],
        "EVIDENCE_LINKAGE": report["linkage"]["EVIDENCE_LINKAGE"],
        "AUDIT_LINKAGE": report["linkage"]["AUDIT_LINKAGE"],
        "RESOLVER_POST_PUBLISH": report["resolver"]["RESOLVER_POST_PUBLISH"],
        "EFFECTIVE_RULES_API": report["engine_consistency"]["EFFECTIVE_RULES_API"],
        "ENGINE_CONSISTENCY": report["engine_consistency"]["ENGINE_CONSISTENCY"],
        "CARVE_OUT_REACHABILITY": report["carve_out_reachability"]["CARVE_OUT_REACHABILITY"],
        "ZERO_INERT_RULES": report["carve_out_reachability"]["ZERO_INERT_RULES"],
        "ROLLBACK_DRILL": report["rollback"]["ROLLBACK_DRILL"],
        "SUPERSESSION_DRILL": report["supersession"]["SUPERSESSION_DRILL"],
        "WATCH_DRILL": report["watch"]["WATCH_DRILL"],
    }
    report["checks"] = checks

    if args.out:
        Path(args.out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for key, value in checks.items():
            print(f"{key:<26} = {value}")
        reach = report["carve_out_reachability"]
        print(
            f"  [carve_out] 已发布 carve-out {len(reach['carve_outs'])} 条，"
            f"可达 {len(reach['carve_outs']) - len(reach['inert'])} 条，"
            f"UNREACHABLE_SELECTED = {reach['UNREACHABLE_SELECTED']}，"
            f"UNEVALUABLE_SELECTED = {reach['UNEVALUABLE_SELECTED']}"
        )
        for entry in reach["inert"]:
            print(
                f"  [carve_out] {entry['rule_id']} (subject={entry['carve_out_scope']}) "
                f"绑定 base {entry['base']} (scope={entry['base_scope']}) "
                "—— base 不覆盖该 subject，此 carve-out 永不生效"
            )
        for section in ("resolver", "engine_consistency", "rollback", "supersession", "watch"):
            problems = report[section].get("problems") or report[section].get("mismatches") or []
            for problem in problems:
                print(f"  [{section}] {problem}")
            for disagreement in report[section].get("disagreements") or []:
                print(f"  [{section}] {disagreement}")

    #: §14 is not allowed to degrade into a caveat: a batch that published a
    #: rule which can never apply has failed, full stop. Every other check may
    #: still legitimately report PASS_WITH_LIMITATIONS; these two may not.
    strict = ("CARVE_OUT_REACHABILITY", "ZERO_INERT_RULES")
    conn.close()
    ok = all(v in ("PASS", "PASS_WITH_LIMITATIONS") for v in checks.values()) and all(
        checks[name] == "PASS" for name in strict
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
