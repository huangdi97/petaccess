"""Wave 01 pre-real-publish semantic bridge (§1-§19).

Computes the **safe executable set** from the 15 human-APPROVED candidates, and
writes a new versioned batch manifest. It never edits the signed register and
never runs the publisher.

Why a bridge is needed at all
-----------------------------

The previous round produced a 13-row batch. Since then, measurement against the
running system showed three classes of problem that the planning layer did not
model:

1. **Source-scope normalisation that does not hold.** 上海动物园 and 迪士尼 record
   ``source_scope_exact='动物'`` normalised to ``other`` as ``exact``. Under
   ADR-025 ``other`` is ``{other_pet}`` — one subject — while 「动物」 is every
   animal. Publishing under a claim of equivalence that is really a narrowing
   silently releases every non-pet animal from the rule.
2. **A statutory safety path that does not exist.** A LEGAL dog prohibition must
   not ship without an executable guide-dog exception, or the platform tells a
   guide-dog handler "prohibited" where the statute's own proviso says otherwise.
3. **An ingest key defect.** Conditions stored under ``type`` are unreadable by
   the canonical gate. (Fixed at the ingest boundary — see
   ``app.services.condition_ingest`` — but already-signed rows keep their bytes.)

None of these reverses a human decision. Every affected row stays ``APPROVED`` in
the signed register; it simply is not executable. The distinction the report must
keep sharp is that **APPROVED is a human fact, PUBLISHABLE is a technical one.**

What this script refuses to do
------------------------------

* write ``final_decision`` / ``reviewer`` / ``decided_at`` (signature is copied)
* mutate a signed candidate row
* run the publisher's ``--execute``
* repair a blocked row to make the batch larger

Usage
-----

    python scripts/w01_semantic_bridge.py            # evaluate + write manifest
    python scripts/w01_semantic_bridge.py --report   # evaluate only, print detail
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "services" / "api"))

# The canonical reachability judgement, reused rather than restated. A second
# implementation could disagree with the gate that enforces it.
from publish_batch import is_reachable_carveout  # noqa: E402

from app.rulespec.guide_dog_safety import (  # noqa: E402
    REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE,
    GuideDogExceptionProposal,
    probe_guide_dog_safety_path,
)
from app.rulespec.source_scope_semantics import (  # noqa: E402
    validate_source_scope_semantic_compatibility,
)

SIGNED_REGISTER = REPO / "docs" / "expansion" / "review_decisions_expansion_r1_wave01.json"
PROJECTED_REGISTER = (
    REPO / "docs" / "expansion" / "review_decisions_expansion_r1_wave01_publishable.json"
)
BATCH_DIR = REPO / "docs" / "governance" / "publish_batches"
OLD_MANIFEST = BATCH_DIR / "EXP_R1_W01_REVIEW_R1_BATCH_01.json"
NEW_MANIFEST = BATCH_DIR / "EXP_R1_W01_REVIEW_R1_BATCH_01A.json"

REVISION = "EXP-R1-W01-REVIEW-R1"
REVIEWER = "huangdi97"
APPROVAL_DECISIONS = ("APPROVED", "APPROVED_WITH_NOTE")

#: The publisher's own weak-evidence set (ADR-021), mirrored so the bridge can
#: report the execution-layer verdict without running the publisher. Kept as a
#: named constant here and asserted equal to the publisher's in the tests, so a
#: divergence is caught rather than silently tolerated.
WEAK_EVIDENCE = frozenset({"search_snippet", "social_lead"})

#: rule_ids that already have a ``current`` AccessRule in production. Used by the
#: dependency-closure check: a carve-out may attach to a base published in an
#: *earlier* batch, so "not selected this round" is not automatically a problem.
PRODUCTION_DB = "postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"


def load_published_rule_ids() -> set[str]:
    """rule_ids with a current published AccessRule, read from production.

    Read-only. Returns an empty set if production is unreachable — the closure
    check then simply requires the base to be in this batch, which is the
    conservative direction.
    """
    try:
        import psycopg

        with psycopg.connect(PRODUCTION_DB) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT rc.id FROM rule_candidate rc
                JOIN access_rule ar ON ar.id = rc.published_rule_id
                WHERE ar.status = 'current' AND rc.expansion_run_id IS NOT NULL
                """
            )
            return {f"w01-{cid.replace('-', '')[:10]}" for (cid,) in cur.fetchall()}
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"note: 无法读取已发布规则集（{exc}）；依赖闭包将要求 base 本批入选")
        return set()


def load_jurisdiction_exceptions(db_url: str = PRODUCTION_DB) -> list[dict]:
    """Activated statutory provisos (ADR-030), read-only, as §10 path C.

    The gate in ``guide_dog_safety`` has always accepted a third provenance for
    the guide-dog path — a jurisdiction-level proviso that binds by instrument
    rather than by ``rule_id`` — but nothing ever handed it one, so every LEGAL
    dog base without a same-batch carve-out was reported blocked even after
    ``JPROV-001`` was activated. The mechanism and the data were both there; the
    wiring was not, and the missing wiring looked exactly like "the proviso does
    not work".

    Only ``current`` + ``reviewed_active`` rows are returned: an unactivated
    proviso binds nothing, and returning it here would invent legal effect.
    An unreachable production degrades to "no proviso", which blocks — the
    conservative direction.
    """
    try:
        import psycopg

        with psycopg.connect(db_url) as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, animal_scope, effect, source_id, status,
                       subject_scope_normalized, normalization_type,
                       normative_effect, holder_scope, binding,
                       instrument_source_ids, applies_to_layer, applies_to_effects
                FROM jurisdiction_exception
                WHERE status = 'current' AND review_status = 'reviewed_active'
                ORDER BY id
                """
            )
            return [
                {
                    "rule_id": r[0],
                    "id": r[0],
                    "animal_scope": r[1],
                    "effect": r[2] or "allowed",
                    "source_id": str(r[3]) if r[3] is not None else None,
                    "status": r[4],
                    "subject_scope_normalized": r[5],
                    "normalization_type": r[6] or "exact",
                    "normative_effect": r[7],
                    "holder_scope": r[8],
                    "binding": r[9] or "rule",
                    "instrument_source_ids": list(r[10] or ()),
                    "applies_to_layer": r[11],
                    "applies_to_effects": list(r[12] or ("prohibited",)),
                }
                for r in cur.fetchall()
            ]
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"note: 无法读取辖区级法定例外（{exc}）；§10 路径 C 视为不存在")
        return []


#: carve-out bindings from the projected register's exception_plan, keyed by the
#: exception's rule_id → the base rule_id it was written of.
def load_bindings(projected: dict) -> dict[str, str]:
    """exception rule_id → the base rule_id it carves out of.

    An entry with ``bases: []`` is *not* skipped: it is a carve-out whose bases
    were all measured non-governing (the projector only records reachable ones),
    which is precisely the inert case §3 requires to be excluded. Returning the
    key with ``None`` keeps it visible to the reachability branch; dropping it
    here is how the Disney carve-out slipped through the first pass.
    """
    out: dict[str, str | None] = {}
    for entry in projected.get("exception_plan") or []:
        if entry.get("mode") != "rule_exception":
            continue
        rule_id = entry.get("rule_id")
        if not rule_id:
            continue
        bases = entry.get("bases") or []
        out[str(rule_id)] = str(bases[0].get("rule_id")) if bases else None
    return out  # type: ignore[return-value]


@dataclass
class BridgeVerdict:
    rule_id: str
    candidate_id: str
    place_name: str
    decision: str
    animal_scope: str
    source_scope_exact: str
    subject_scope_normalized: str
    normalization_type: str
    rule_layer: str
    effect: str
    is_exception: bool
    # --- per-check outcomes -------------------------------------------------
    scope_check: str = ""  # PASS / FAIL / n/a
    scope_reason: str = ""
    scope_follow_up: str = ""
    guide_dog_check: str = ""  # PASS / BLOCKED / n/a
    guide_dog_reason: str = ""
    prepublish_gate: str = ""  # PASS / BLOCKED
    prepublish_reason: str = ""
    execution_gate: str = ""  # PASS / BLOCKED
    execution_reason: str = ""
    reachability: str = ""  # reachable / unreachable / n/a
    blocked: bool = False
    block_reason: str = ""
    proposal: GuideDogExceptionProposal | None = None

    @property
    def executable(self) -> bool:
        return not self.blocked


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="evaluate and print, write nothing")
    ap.add_argument("--out", default=str(NEW_MANIFEST), help="manifest to write")
    ap.add_argument("--batch-id", default="EXP-R1-W01-REVIEW-R1-BATCH-01A")
    ap.add_argument("--supersedes", default=OLD_MANIFEST.name)
    ap.add_argument(
        "--supersede-reason",
        default="PRE_REAL_PUBLISH_SEMANTIC_BRIDGE",
    )
    ap.add_argument(
        "--exclude-published",
        action="store_true",
        help="drop rows an earlier batch already shipped (for a follow-up batch)",
    )
    args = ap.parse_args()

    signed = json.loads(SIGNED_REGISTER.read_text(encoding="utf-8"))
    projected = json.loads(PROJECTED_REGISTER.read_text(encoding="utf-8"))
    bindings = load_bindings(projected)
    PUBLISHED_RULE_IDS = load_published_rule_ids()
    # ADR-030 §10 path C. Read here, not at call time, so one load serves every
    # base and a failure is reported once instead of per-row.
    JURISDICTION_EXCEPTIONS = load_jurisdiction_exceptions()
    print(f"jurisdiction_provisos_active={len(JURISDICTION_EXCEPTIONS)}")

    proj_rows = {r["rule_id"]: r for r in projected["rows"]}
    signed_rows = {}
    for r in signed["rows"]:
        rid = f"w01-{r['candidate_id'].replace('-', '')[:10]}"
        signed_rows[rid] = r

    approved = [rid for rid, r in signed_rows.items() if r["final_decision"] in APPROVAL_DECISIONS]
    print(f"human_approved={len(approved)}")

    verdicts: list[BridgeVerdict] = []
    for rid in approved:
        sr = signed_rows[rid]
        pr = proj_rows.get(rid) or {}
        is_exc = rid in bindings

        v = BridgeVerdict(
            rule_id=rid,
            candidate_id=sr["candidate_id"],
            place_name=sr["place_name"],
            decision=sr["final_decision"],
            animal_scope=sr["animal_scope"],
            source_scope_exact=sr["source_scope_exact"],
            subject_scope_normalized=sr["subject_scope_normalized"],
            normalization_type=sr["normalization_type"],
            rule_layer=sr["rule_layer"],
            effect=sr["effect"],
            is_exception=is_exc,
        )

        # ---- §4-§6 source-scope semantic compatibility ----------------------
        sc = validate_source_scope_semantic_compatibility(
            sr["source_scope_exact"], sr["subject_scope_normalized"], sr["normalization_type"]
        )
        v.scope_check = "PASS" if sc.compatible else "FAIL"
        v.scope_reason = sc.reason
        v.scope_follow_up = sc.follow_up
        if not sc.compatible:
            v.blocked = True
            v.block_reason = "SOURCE_SCOPE_NORMALIZATION_NOT_SEMANTICALLY_EQUIVALENT"

        # ---- §13-§14 execution contract: the publisher's own preconditions ---
        # Distinct from the canonical gate above. The gate grades the candidate;
        # the publisher additionally refuses weak evidence atomically (ADR-021)
        # and blocks a carve-out whose base is not in the batch. Both must be
        # reported, because "gate PASS" does not imply "publisher accepts".
        strength = str(pr.get("evidence_strength") or "")
        if strength in WEAK_EVIDENCE:
            notes = (pr.get("strength_notes") or [""])[0][:80]
            v.execution_gate = "BLOCKED"
            v.execution_reason = f"ADR-021 原子前置：evidence_strength={strength}（{notes}）"
            if not v.blocked:
                v.blocked = True
                v.block_reason = "ADR021_UNVERIFIED_SEARCH_SNIPPET"
        else:
            v.execution_gate = "PASS"

        # ---- §3 / §17 carve-out reachability --------------------------------
        # A carve-out must reach a same-layer base that semantically governs its
        # own subject. An OPERATOR_POLICY guide-dog carve-out on an `other` base
        # can never fire (§2): `other` covers {other_pet}, not guide_dog. It is
        # INERT: publishing it would be audited, linked and counted while
        # silently promising access it never delivers.
        #
        # Note this is independent of the LEGAL probe below: that one asks
        # whether a *base* has a safety path; this one asks whether a *carve-out*
        # can ever fire. Both must be asked.
        if is_exc:
            base_id = bindings.get(rid)
            base_row = signed_rows.get(base_id or "")
            if base_id is None:
                # The projector recorded no governing base at all: every
                # same-layer base was measured non-governing. That is the inert
                # case itself, not a missing-binding edge case.
                v.reachability = "unreachable"
                v.blocked = True
                v.block_reason = "INREACHABLE_APPROVED_CARVE_OUT"
            elif base_row is None:
                v.reachability = "base_not_in_register"
                v.blocked = True
                v.block_reason = "CARVE_OUT_WITHOUT_APPROVED_BASE"
            else:
                verdict = is_reachable_carveout(base_row, sr)
                if verdict is True:
                    v.reachability = "reachable"
                else:
                    v.reachability = "unreachable" if verdict is False else "unevaluable"
                    v.blocked = True
                    v.block_reason = "INREACHABLE_APPROVED_CARVE_OUT"

        verdicts.append(v)

    # ---- §10-§12 LEGAL dog prohibition: executable guide-dog path -----------
    legal_dog = [
        v
        for v in verdicts
        if v.rule_layer == "LEGAL" and v.effect == "prohibited" and not v.is_exception
    ]
    print(f"legal_dog_bases={len(legal_dog)}")

    # batch-available exceptions: approved guide-dog carve-outs, by base.
    # Only reachable ones can serve as a safety path — an inert carve-out is not
    # a path, which is exactly why the LEGAL probe below re-measures rather than
    # trusting this map.
    approved_exceptions_by_base: dict[str, dict] = {}
    for rid in approved:
        base = bindings.get(rid)
        if base is None:
            continue
        sr = signed_rows[rid]
        approved_exceptions_by_base[base] = {
            "rule_id": rid,
            "base_rule_id": base,
            "animal_scope": sr["animal_scope"],
            "subject_scope_normalized": sr["subject_scope_normalized"],
            "normalization_type": sr["normalization_type"],
            "effect": _exception_effect(sr),
            "rule_layer": sr["rule_layer"],
            "source_id": (proj_rows.get(rid) or {}).get("source_id"),
            "status": "current",
            "source_scope_exact": sr["source_scope_exact"],
            "normative_effect": sr.get("normative_effect"),
            "holder_scope": "person_with_disability",
        }

    for v in legal_dog:
        base = {
            "rule_id": v.rule_id,
            "place_name": v.place_name,
            "animal_scope": v.animal_scope,
            "subject_scope_normalized": v.subject_scope_normalized,
            "normalization_type": v.normalization_type,
            "effect": v.effect,
            "rule_layer": v.rule_layer,
            "action": (proj_rows.get(v.rule_id) or {}).get("action") or "enter",
            "mandatory_level": (proj_rows.get(v.rule_id) or {}).get("mandatory_level"),
            "source_id": (proj_rows.get(v.rule_id) or {}).get("source_id"),
            "zone_id": (proj_rows.get(v.rule_id) or {}).get("zone_id"),
        }
        exc = approved_exceptions_by_base.get(v.rule_id)
        probe = probe_guide_dog_safety_path(
            base=base,
            candidate_exceptions=[exc] if exc else [],
            jurisdiction_exceptions=JURISDICTION_EXCEPTIONS,
        )
        if probe.safe_to_publish:
            v.guide_dog_check = "PASS"
            source_label = {
                "batch": "同批",
                "published": "已发布",
                "jurisdiction": "辖区级法定但书",
            }.get(probe.exception_source, probe.exception_source)
            v.guide_dog_reason = (
                f"可执行法定导盲犬例外来自{source_label}：{probe.applied_exceptions}"
            )
        else:
            v.guide_dog_check = "BLOCKED"
            v.guide_dog_reason = (
                f"ordinary_dog_prohibited={probe.ordinary_dog_prohibited}, "
                f"guide_dog_effect={probe.guide_dog_effect}, "
                f"applied_exceptions={probe.applied_exceptions}"
            )
            if not v.blocked:
                v.blocked = True
                v.block_reason = probe.block_reason
            v.proposal = GuideDogExceptionProposal(
                for_base_rule_id=v.rule_id,
                place_name=v.place_name,
                reason=REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE,
            )

    print(f"legal_dog_with_exception={sum(1 for v in legal_dog if v.guide_dog_check == 'PASS')}")
    print(f"legal_dog_blocked={sum(1 for v in legal_dog if v.guide_dog_check == 'BLOCKED')}")

    # ---- report -------------------------------------------------------------
    print("\n--- verdicts ---")
    for v in verdicts:
        mark = "OK " if v.executable else "BLOCK"
        kind = "EXC" if v.is_exception else "BASE"
        print(
            f"{mark} {kind} {v.rule_id} {v.place_name[:22]:24} "
            f"{v.animal_scope:13} scope={v.scope_check:4} gdog={v.guide_dog_check or '-':7} "
            f"exec={v.execution_gate:7} reach={v.reachability or '-':11} {v.block_reason}"
        )

    # ---- §14 the four layers, never collapsed into one number --------------
    policy_pass = [
        v for v in verdicts if v.scope_check != "FAIL" and v.guide_dog_check != "BLOCKED"
    ]
    exec_pass = [v for v in verdicts if v.execution_gate == "PASS"]
    final_set = [v for v in verdicts if v.executable]
    print("\n--- layered accounting (§14) ---")
    print(f"HUMAN_APPROVED              = {len(verdicts)}")
    print(f"PREPUBLISH_POLICY_PASS      = {len(policy_pass)}")
    print(f"EXECUTION_CONTRACT_PASS     = {len(exec_pass)}")
    print(f"FINAL_EXECUTABLE            = {len(final_set)}")
    print(f"  of which AccessRule       = {sum(1 for v in final_set if not v.is_exception)}")
    print(f"  of which RuleException    = {sum(1 for v in final_set if v.is_exception)}")
    print(f"EXCLUDED_APPROVED           = {len(verdicts) - len(final_set)}")

    if args.report:
        return

    # ---- build the manifest in dependency order ----------------------------
    executable = [v for v in verdicts if v.executable]
    if args.exclude_published:
        # A later batch of the same revision ships only what the earlier one did
        # not. Re-publishing is a no-op at the publisher, but listing it again
        # would make the manifest claim to do work it does not do.
        executable = [v for v in executable if v.rule_id not in PUBLISHED_RULE_IDS]
        removed = len([v for v in verdicts if v.executable]) - len(executable)
        print(f"already_published_removed={removed}")
    bases = [v for v in executable if not v.is_exception]
    exceptions = [v for v in executable if v.is_exception]

    # ---- §17 dependency closure --------------------------------------------
    # Every selected carve-out must have its base either selected earlier in this
    # same batch or already published. A carve-out on a base that is *not* being
    # published this round has nothing to attach to — the publisher would create
    # an orphan exception. Checked here so the manifest never carries one.
    selected_ids = {v.rule_id for v in executable}
    closure_problems: list[str] = []
    for v in exceptions:
        base_id = bindings.get(v.rule_id)
        if base_id is None:
            closure_problems.append(f"{v.rule_id}: 无 base 绑定")
        elif base_id not in selected_ids and base_id not in PUBLISHED_RULE_IDS:
            closure_problems.append(f"{v.rule_id}: base {base_id} 既未入选本批，也未处于已发布状态")
    print(f"\nBATCH_DEPENDENCY_CLOSED = {'PASS' if not closure_problems else 'FAIL'}")
    for p in closure_problems:
        print(f"  ! {p}")
    if closure_problems:
        raise SystemExit(4)

    ordered: list[str] = [v.rule_id for v in bases]
    for v in exceptions:
        base = bindings.get(v.rule_id)
        if base and base in ordered:
            idx = ordered.index(base) + 1
            ordered.insert(idx, v.rule_id)
        else:
            ordered.append(v.rule_id)

    excluded = [
        {
            "rule_id": v.rule_id,
            "place_name": v.place_name,
            "human_decision": v.decision,
            "reason": v.block_reason,
            "detail": v.scope_reason if v.scope_check == "FAIL" else v.guide_dog_reason,
        }
        for v in verdicts
        if not v.executable
    ]

    # `excluded_approved` distinguishes the two ways an approved row can be left
    # out: it is not executable (with the measured reason), or an earlier batch
    # already shipped it. Collapsing those into one list without the reason is
    # how "excluded" starts to read like "rejected".
    def _detail(v: BridgeVerdict) -> str:
        if v.scope_check == "FAIL":
            return v.scope_reason
        if v.guide_dog_reason:
            return v.guide_dog_reason
        return v.execution_reason or v.block_reason

    excluded = [
        {
            "rule_id": v.rule_id,
            "place_name": v.place_name,
            "human_decision": v.decision,
            "reason": v.block_reason,
            "detail": _detail(v),
        }
        for v in verdicts
        if not v.executable
    ]
    already_shipped = [v for v in verdicts if v.executable and v.rule_id in PUBLISHED_RULE_IDS]
    if args.exclude_published:
        excluded.extend(
            {
                "rule_id": v.rule_id,
                "place_name": v.place_name,
                "human_decision": v.decision,
                "reason": "ALREADY_PUBLISHED_IN_EARLIER_BATCH",
                "detail": _detail(v) or "已由前序批次发布",
            }
            for v in already_shipped
        )
    excluded_count = len(excluded)

    manifest = {
        "_schema": (
            "publish batch manifest v1 — revision / batch_id / reviewer / "
            "candidate_rule_ids (registry rule_id values, in execution dependency "
            "order). Permission is NOT stored here: final_decision is read from the "
            "signed register."
        ),
        "revision": REVISION,
        "batch_id": args.batch_id,
        "reviewer": REVIEWER,
        "supersedes_planning_manifest": args.supersedes,
        "supersede_reason": args.supersede_reason,
        "note": (
            f"Wave-01 safe batch. {len(ordered)} of the {len(verdicts)} human-APPROVED "
            f"candidates ({len(bases)} AccessRule + {len(exceptions)} RuleException); "
            f"{excluded_count} approved rows are not in this batch "
            f"({len(already_shipped)} already shipped, "
            f"{len([v for v in verdicts if not v.executable])} not executable) — "
            "none of which reverses a human decision; every excluded row stays "
            "APPROVED in the signed register. "
            "Exclusions and their measured reasons are listed in `excluded_approved`. "
            "The base-before-exception ordering is the execution order."
        ),
        "excluded_approved": excluded,
        "candidate_rule_ids": ordered,
    }
    out_path = Path(args.out).resolve()
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out_path.relative_to(REPO)} size={len(ordered)}")


def _exception_effect(sr: dict) -> str:
    """The effect a carve-out applies. ``exempt_from_prohibition`` ⇒ allowed."""
    ne = sr.get("normative_effect")
    if ne == "exempt_from_prohibition":
        return "allowed"
    return "allowed" if sr.get("effect") in ("allowed", "conditional") else "allowed"


if __name__ == "__main__":
    main()
