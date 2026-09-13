"""Generate the P0 review-decision register for the 10-place real pilot (R1).

Joins the evidence register (which carries the normative layer, scope, effect,
conditions and the R2 repair outcome) with the ingest manifest (which carries
the live candidate UUIDs) and emits ``docs/reality_audit/review_decisions_r1.json``.

The register is a *worksheet*: every row gets a machine-proposed decision plus a
machine-checkable reason, and ``final_decision`` / ``reviewer`` / ``reviewed_at``
are left null. Only a named human reviewer may fill those in — AI never makes the
final rule call (ADR-005, Master Goal §0.9). ``scripts/publish_reviewed_r1.py``
refuses to run until they are filled.

Proposal rules are declarative so the reasoning is auditable and reproducible:

  REJECT  source does not support the claim          (PLACE_ATTRIBUTION_ERROR)
  HOLD    conclusion is inferred, not stated         (INFERRED_NOT_STATED)
  HOLD    conclusion is a legal interpretation       (LEGAL_INTERPRETATION)
  HOLD    evidence repair did not confirm the claim  (EVIDENCE_NOT_VERIFIED)
  NOTE    statute scope generalised to service_dog   (STATUTE_SCOPE_GENERALIZATION)
  APPROVE otherwise

Usage: python scripts/gen_review_decisions_r1.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUDIT = REPO / "docs" / "reality_audit"
EVIDENCE = AUDIT / "real_pilot_evidence.json"
MANIFEST = AUDIT / "real_pilot_ingest_manifest.json"
OUT = AUDIT / "review_decisions_r1.json"

# --- declarative proposal rules ------------------------------------------------
REJECT: dict[str, str] = {
    "mn-outdoor-media": "PLACE_ATTRIBUTION_ERROR",
}
HOLD: dict[str, str] = {
    "dl-legal-dog": "LEGAL_INTERPRETATION",
    "gc-other-keep": "INFERRED_NOT_STATED",
    "gh-outdoor-keep": "EVIDENCE_NOT_VERIFIED",
}
NOTE: dict[str, str] = {}

# --- R2 evidence-repair outcome (EVIDENCE_REPAIR_LOG_R1.md, verified) ----------
REPAIRED_STRENGTH: dict[str, str] = {
    "73448553-cdfa-44db-8265-cb45dd325687": "secondary_reputable",  # 新华网直抓
    "4c7aba30-a7e3-4ad7-88d7-61a0ba255f27": "primary_direct",  # 费尔蒙官网直抓
    "7efddba6-7c42-4013-8918-bedbb996d702": "primary_direct",  # 费尔蒙官网直抓
    "9c8b4b26-a2cb-4efd-b188-aeee3a194951": "secondary_reputable",  # 潮新闻直抓
    "fb003b3a-3583-484b-b16f-7a6f3a1b71d0": "secondary_reputable",  # 潮新闻+澎湃
    "887f21ba-e548-457b-a3dd-30ea806d988e": "search_snippet",  # 未证实
    "ed79071d-d052-46b4-a216-dc789aae4128": "search_snippet",  # 归因错误
}
REPAIRED_SOURCE: dict[str, str] = {
    "73448553-cdfa-44db-8265-cb45dd325687": "新华网/界面新闻 2026-05-29",
    "4c7aba30-a7e3-4ad7-88d7-61a0ba255f27": "费尔蒙官网 guest-services 页",
    "7efddba6-7c42-4013-8918-bedbb996d702": "费尔蒙官网 guest-services 页",
    "9c8b4b26-a2cb-4efd-b188-aeee3a194951": "潮新闻 2026-08-27（官方回应）",
    "fb003b3a-3583-484b-b16f-7a6f3a1b71d0": "潮新闻 + 澎湃客服回应 2026-08-27",
}
# -------------------------------------------------------------------------------

WEAK = {"search_snippet", "social_lead"}


def strength_for(source: dict, candidate_id: str) -> str:
    if candidate_id in REPAIRED_STRENGTH:
        return REPAIRED_STRENGTH[candidate_id]
    if source.get("capture_method") == "web_reader_fetch" and source.get("directness") == "direct":
        return "primary_direct"
    if source.get("capture_method") == "search_snippet":
        return "social_lead" if source.get("source_type") == "ordinary_user" else "search_snippet"
    return "secondary_reputable"


def propose(rule: dict, candidate_id: str, strength: str) -> tuple[str, str]:
    rule_id = rule["rule_id"]
    if rule_id in REJECT:
        return "RECOMMEND_REJECT", REJECT[rule_id]
    if rule_id in HOLD:
        return "RECOMMEND_HOLD", HOLD[rule_id]
    if rule_id in NOTE:
        return "RECOMMEND_APPROVE_WITH_NOTE", NOTE[rule_id]
    if strength in WEAK:
        return "RECOMMEND_HOLD", "EVIDENCE_NOT_VERIFIED"
    if rule.get("rule_layer") == "LEGAL" and rule.get("animal_scope") == "service_dog":
        return "RECOMMEND_APPROVE_WITH_NOTE", "STATUTE_SCOPE_GENERALIZATION"
    return "RECOMMEND_APPROVE", "EVIDENCE_TRACEABLE"


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cand_index: dict[str, str] = manifest["rule_candidates"]

    rows: list[dict] = []
    for place in evidence["places"]:
        pkey = place["key"]
        sources = {s["key"]: s for s in place["sources"]}
        for rule in place["rules"]:
            ckey = f"{pkey}:{rule['rule_id']}"
            cid = cand_index.get(ckey)
            if cid is None:
                raise SystemExit(f"candidate id missing in manifest: {ckey}")
            src = sources[rule["source_key"]]
            strength = strength_for(src, cid)
            decision, reason = propose(rule, cid, strength)
            rows.append(
                {
                    "candidate_id": cid,
                    "place_key": pkey,
                    "place_name": place["canonical_name"],
                    "rule_id": rule["rule_id"],
                    "zone_key": rule.get("zone_key"),
                    "source_key": rule["source_key"],
                    "source_url": src.get("source_url"),
                    "issuer": src.get("issuer"),
                    "rule_layer": rule.get("rule_layer"),
                    "animal_scope": rule.get("animal_scope"),
                    "action": rule.get("action"),
                    "effect": rule.get("effect"),
                    "conditions": rule.get("conditions") or [],
                    "internal_confidence": rule.get("confidence"),
                    "evidence_strength": strength,
                    "evidence_source": REPAIRED_SOURCE.get(cid) or src.get("issuer"),
                    "license": {
                        "display_allowed": src.get("display_allowed"),
                        "redistribution_allowed": src.get("redistribution_allowed"),
                        "storage_allowed": src.get("storage_allowed"),
                    },
                    "proposed_decision": decision,
                    "proposed_reason": reason,
                    "final_decision": None,
                    "reviewer": None,
                    "reviewed_at": None,
                    "review_note": None,
                }
            )

    rows.sort(key=lambda r: (r["place_key"], r["rule_id"]))
    doc = {
        "_readme": [
            "P0 PILOT-REVIEW-PUBLISH-01 review register (worksheet).",
            "proposed_decision is a MACHINE PROPOSAL, not a ruling: a named human reviewer",
            "must set final_decision + reviewer + reviewed_at before publish_reviewed_r1.py runs.",
            "Allowed final_decision values: APPROVED | REJECTED | HOLD.",
            "Evidence strengths marked secondary_reputable/primary_direct were verified during",
            "REALITY-AUDIT-10-R2 evidence repair (docs/reality_audit/EVIDENCE_REPAIR_LOG_R1.md).",
        ],
        "generated_from": [str(EVIDENCE.relative_to(REPO)), str(MANIFEST.relative_to(REPO))],
        "human_signoff_required": True,
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["proposed_decision"]] = counts.get(r["proposed_decision"], 0) + 1
    print(
        json.dumps(
            {"written": str(OUT), "total": len(rows), "proposed": counts},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
