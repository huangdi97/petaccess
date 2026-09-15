"""GOV-01 FINAL sign-off packet: structure, scope fidelity, and the no-signature rule.

The packet is the artefact a named human signs, so its shape is part of the
contract. Three things must hold, and each is easy to break by accident while
editing the generator:

N1 — **nothing is pre-signed.** Every ``final_decision`` / ``reviewer`` /
     ``reviewed_at`` in both the human file and the machine register stays
     blank (Master Goal §0.9 / ADR-005).

N2 — **the compound exception is actually split (ADR-028).** 上海图书馆 used to
     be one row claiming ``service_dog``. It must now be exactly three
     source-exact rows sharing one evidence anchor, with the compound wording
     preserved verbatim and no role outside the split's documented meaning.

N3 — **the first-party quote is the operator's own wording, not a paraphrase.**
     The headline claim of any row is its quote; if the quote drifts, the human
     signs something the source never said.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
REGISTER = REPO / "docs" / "reality_audit" / "review_decisions_r2_final.json"
HUMAN = REPO / "HUMAN_REVIEW_DECISIONS_R2_FINAL.json"
PACKET = REPO / "HUMAN_REVIEW_PACKET_R2_FINAL.md"
QUICK = REPO / "HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md"

#: the operator's own wording, as published on fairmont.com (guest-services, zh)
FAIRMONT_QUOTE_ZH = (
    "上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。"
    "导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。"
)
FAIRMONT_ZH_URL = (
    "https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html"
)

LEGAL_NORMS = {"exact", "compound_term_split"}


@pytest.fixture(scope="module")
def register() -> dict:
    assert REGISTER.exists(), "run scripts/gen_human_review_packet_r2_final.py"
    return json.loads(REGISTER.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rows(register: dict) -> list[dict]:
    return register["rows"]


@pytest.fixture(scope="module")
def by_id(rows: list[dict]) -> dict[str, dict]:
    return {r["rule_id"]: r for r in rows}


def _human_id(row: dict) -> str:
    return row["candidate_id"]


# --- N1: the AI never signs --------------------------------------------------


def test_files_exist():
    for p in (REGISTER, HUMAN, PACKET, QUICK):
        assert p.exists(), p


def test_human_decision_file_has_no_reviewer_or_timestamp():
    payload = json.loads(HUMAN.read_text(encoding="utf-8"))
    assert payload["reviewer"] == ""
    assert payload["reviewed_at"] == ""
    assert payload["decisions"], "empty decision list would make sign-off impossible"


def test_no_row_in_either_file_is_signed(rows):
    human = {
        d["candidate_id"]: d for d in json.loads(HUMAN.read_text(encoding="utf-8"))["decisions"]
    }
    for row in rows:
        cid = _human_id(row)
        assert cid in human, f"{row['rule_id']} missing from the human file"
        for field in ("final_decision", "reviewer", "reviewed_at"):
            assert not row.get(field), f"{row['rule_id']}.{field}={row.get(field)!r}"
        assert not human[cid].get("final_decision"), row["rule_id"]


def test_the_machine_register_marks_human_signoff_as_required(register):
    assert register["human_signoff_required"] is True
    assert register["revision"] == "R2-FINAL-R2"
    # supersession is stated, so an older register is never mistaken for current
    assert register["supersedes"].endswith("review_decisions_r2.json")


def test_every_row_carries_a_proposal_but_no_ruling(rows):
    counts = Counter(r["proposed_decision"] for r in rows)
    assert set(counts) <= {"RECOMMEND_APPROVE", "RECOMMEND_HOLD", "RECOMMEND_REJECT"}
    assert counts["RECOMMEND_REJECT"] >= 3
    # and the count is reported honestly in the packet itself
    packet = PACKET.read_text(encoding="utf-8")
    for decision, n in counts.items():
        assert f"| `{decision}` | **{n}** |" in packet, decision


def test_rows_are_sorted_with_rejects_first(rows):
    """Review UX invariant: what needs attention is not buried below approvals."""
    order = {"RECOMMEND_REJECT": 0, "RECOMMEND_HOLD": 1, "RECOMMEND_APPROVE": 2}
    ranks = [order[r["proposed_decision"]] for r in rows]
    assert ranks == sorted(ranks)


# --- N2: the library compound split ------------------------------------------


LIBRARY_ROWS = ("lib-sd-op-guide", "lib-sd-op-police", "lib-sd-op-military")


def test_library_exception_is_three_source_exact_rows(by_id):
    for rule_id in LIBRARY_ROWS:
        assert rule_id in by_id, rule_id
    # and the coarse composite row is gone — never coexisting with the split
    assert by_id.get("lib-sd-op") is None


def test_library_split_members_are_exactly_the_compound_term_meaning(by_id):
    guide = by_id["lib-sd-op-guide"]
    police = by_id["lib-sd-op-police"]
    military = by_id["lib-sd-op-military"]

    assert guide["source_scope_exact"] == "导盲犬"
    assert guide["subject_scope_normalized"] == "guide_dog"
    assert guide["normalization_type"] == "exact"

    # the compound wording survives verbatim on BOTH members
    assert police["source_scope_exact"] == "军警犬"
    assert military["source_scope_exact"] == "军警犬"
    assert police["normalization_type"] == "compound_term_split"
    assert military["normalization_type"] == "compound_term_split"
    assert {police["subject_scope_normalized"], military["subject_scope_normalized"]} == {
        "police_dog",
        "military_working_dog",
    }


def test_library_split_shares_one_evidence_anchor_and_no_fifth_role(by_id):
    """Same source ⇒ same quote. Only the modelled member differs."""
    anchors = {by_id[rule_id]["source_url"] for rule_id in LIBRARY_ROWS}
    assert len(anchors) == 1, "the three rows must cite the same notice"
    for rule_id in LIBRARY_ROWS:
        row = by_id[rule_id]
        assert row["normalization_type"] in LEGAL_NORMS
        assert row["evidence_strength"] == "primary_direct"
        assert row["quoted_fragment"], rule_id


def test_no_row_widens_a_service_dog_scope_without_a_legal_normalisation(rows):
    """The ADR-025 defect, checked across the whole register: any row still using
    the coarse assistance scope must have declared it a legal equivalent."""
    coarse = [r for r in rows if r["animal_scope"] == "service_dog"]
    for row in coarse:
        if row["normalization_type"] in LEGAL_NORMS:
            continue
        assert row["proposed_decision"] != "RECOMMEND_APPROVE", row["rule_id"]


# --- N3: fp-sd-op first-party quote fidelity ---------------------------------


def test_fairmont_quote_is_the_operators_own_wording(by_id):
    first = by_id["fp-sd-op-firstparty"]
    assert first["quoted_fragment"] == FAIRMONT_QUOTE_ZH
    assert first["subject_scope_normalized"] == "guide_dog"
    assert first["normalization_type"] == "exact"
    assert first["proposed_decision"] == "RECOMMEND_APPROVE"
    # the headline in the packet must be the same string a reviewer will judge
    assert FAIRMONT_QUOTE_ZH in PACKET.read_text(encoding="utf-8")


def test_fairmont_content_hash_reproduces_from_the_quote(register, by_id):
    """A content_hash that cannot be recomputed proves nothing."""
    expected = hashlib.sha256(FAIRMONT_QUOTE_ZH.encode("utf-8")).hexdigest()
    for rule_id in ("fp-sd-op-firstparty", "fp-pets-op-firstparty"):
        assert by_id[rule_id]["content_hash"] == expected, rule_id


def test_the_ota_shaped_rows_are_superseded_not_published(by_id):
    """Both OTA-anchored rows must stand down in favour of the operator's own
    page. Rejected for being superseded — the old evidence is never deleted, it
    simply stops being the basis for publication."""
    for rule_id, replacement in (
        ("fp-sd-op", "fp-sd-op-firstparty"),
        ("fp-pets-op", "fp-pets-op-firstparty"),
    ):
        old = by_id[rule_id]
        assert old["proposed_decision"] == "RECOMMEND_REJECT", rule_id
        codes = old.get("reject_reason_codes") or []
        assert "SUPERSEDED_BY_FIRST_PARTY_SOURCE" in codes, rule_id
        assert any(replacement in str(c) for c in codes), rule_id
        # the chain really is the aggregator — not something we merely suspect
        assert old["evidence_strength"] in {"search_snippet", "secondary_reputable"}


def test_pets_prohibition_and_guide_exception_share_one_first_party_anchor(by_id):
    """One operator sentence carries both holdings; two independent evidence
    chains would let them drift apart."""
    base = by_id["fp-pets-op-firstparty"]
    exception = by_id["fp-sd-op-firstparty"]
    assert base["effect"] == "prohibited"
    assert base["source_scope_exact"] == "宠物"
    assert base["subject_scope_normalized"] == "ordinary_pet"
    assert exception["effect"] == "allowed"
    assert exception["subject_scope_normalized"] == "guide_dog"
    for row in (base, exception):
        assert row["source_url"] == FAIRMONT_ZH_URL
        assert row["evidence_strength"] == "primary_direct"
        assert not row["locator_gaps"], row["rule_id"]
        assert not row["license_problems"], row["rule_id"]
        assert row["proposed_decision"] == "RECOMMEND_APPROVE"


def test_quick_table_has_one_row_per_decision_and_a_blank_decision_column(rows):
    table = QUICK.read_text(encoding="utf-8")
    assert "| **FINAL-01**" in table
    assert f"| **FINAL-{len(rows):02d}**" in table
    # the column a human fills in must start empty
    body = [ln for ln in table.splitlines() if ln.startswith("| **FINAL-")]
    assert len(body) == len(rows)
    for line in body:
        # the trailing "my decision" cell must be empty: "| … |  |"
        cells = [c.strip() for c in line.rstrip().strip("|").split("|")]
        assert cells[-1] == "", line


# --- GOV01-HUMAN-SIGNATURE-HARDEN-R1 -----------------------------------------


def test_quick_table_never_suggests_the_non_canonical_spellings():
    """The audit asked for this in so many words: no APPROVE / REJECT anywhere in
    the reviewer-facing sheet."""
    import re

    table = QUICK.read_text(encoding="utf-8")
    # RECOMMEND_* are machine proposals and stay; bare APPROVE/REJECT do not.
    bare = [m.group(0) for m in re.finditer(r"(?<!RECOMMEND_)\b(APPROVE|REJECT)\b", table)]
    assert bare == [], f"速填表出现非规范写法：{bare}"


def test_packet_and_register_agree_on_the_decision_vocabulary(register):
    from human_decisions import HUMAN_DECISIONS

    assert tuple(register["human_decisions"]) == tuple(HUMAN_DECISIONS)
    packet = PACKET.read_text(encoding="utf-8")
    for decision in HUMAN_DECISIONS:
        assert f"| `{decision}` |" in packet, decision


def test_gc_other_keep_is_not_recommended_for_a_claim_its_quote_does_not_support(by_id):
    """The pilot notice proves a pilot exists — it never says the rest of the
    park is closed to pets. That inference was ours, not the source's."""
    row = by_id["gc-other-keep"]
    assert row["proposed_decision"] == "RECOMMEND_REJECT"
    codes = row.get("reject_reason_codes") or []
    assert "CLAIM_NOT_SUPPORTED_BY_QUOTE" in codes
    assert row["effect"] == "prohibited"


def test_disney_legal_projection_is_held_because_applicability_is_unproven(by_id):
    """scenic_area is not one of the categories 第二十三条 enumerates."""
    for rule_id in ("dl-legal-dog", "dl-sd-legal"):
        row = by_id[rule_id]
        assert row["rule_layer"] == "LEGAL"
        assert row["proposed_decision"] == "RECOMMEND_HOLD", rule_id
        assert row["proposed_reason"] == "STATUTORY_APPLICABILITY_NOT_EVIDENCED"
        ap = row["applicability"]
        assert ap["place_type"] == "scenic_area"
        assert ap["status"] == "NOT_EVIDENCED"
        assert ap["statutory_category"] is None


def test_disney_operator_rows_are_handled_independently_of_the_legal_hold(by_id):
    """A held legal projection must not drag the operator's own rules with it."""
    for rule_id in ("dl-pet-ban", "dl-sd-op"):
        row = by_id[rule_id]
        assert row["rule_layer"] == "OPERATOR_POLICY", rule_id
        assert row["proposed_decision"] != "RECOMMEND_REJECT", rule_id


def test_temporary_policies_are_held_until_someone_rechecks_they_still_apply(by_id):
    for rule_id in ("dj-pilot", "gc-h6-pilot"):
        row = by_id[rule_id]
        assert row["rule_layer"] == "TEMPORARY_POLICY"
        assert row["proposed_decision"] == "RECOMMEND_HOLD", rule_id
        assert row["proposed_reason"] == "TEMPORARY_STATUS_NOT_REVERIFIED"
        # displayed honestly: we know when it started, not when it ends
        assert row["effective_from"]
        assert not row["effective_to"] and not row["open_ended_reason"]


def test_rows_with_a_broken_source_chain_cannot_pass_on_a_label(by_id):
    """These used to clear as EVIDENCE_TRACEABLE with no locatable artefact."""
    for rule_id in ("xm-indoor-new", "xm-outdoor-media", "gh-indoor-new"):
        row = by_id[rule_id]
        assert row["proposed_decision"] == "RECOMMEND_HOLD", rule_id
        assert row["proposed_reason"] == "EVIDENCE_CHAIN_INCOMPLETE"
        assert row["evidence_strength"] in {"search_snippet", "secondary_reputable"}


def test_every_row_prints_the_full_provenance_block(rows):
    packet = PACKET.read_text(encoding="utf-8")
    required = (
        "candidate_id",
        "place",
        "action / effect",
        "source_scope_exact",
        "subject_scope_normalized",
        "normalization_type",
        "RuleLayer",
        "MandatoryLevel",
        "EvidenceStrength",
        "Source issuer",
        "Source URL",
        "关键原文引文",
        "place_match_evidence",
        "DataLicense",
        "conflict",
        "exception",
        "effective_from / to",
        "freshness",
        "AI recommendation",
        "recommendation reason",
        "final_decision",
    )
    detail_rows = packet.split("### FINAL-")[1:]
    assert len(detail_rows) == len(rows)
    for chunk in detail_rows:
        for heading in required:
            assert heading in chunk, heading


def test_exception_plan_covers_every_operator_carve_out(rows):
    """Not just the library: the plan must enumerate all operators' carve-outs."""
    packet = PACKET.read_text(encoding="utf-8")
    section = packet.split("### 1.7 RuleException")[1].split("**发布顺序")[0]
    for rule_id in (
        "lib-sd-op-guide",
        "lib-sd-op-police",
        "lib-sd-op-military",
        "dl-sd-op",
        "qt-sd-op",
        "fp-sd-op-firstparty",
    ):
        assert f"`{rule_id}`" in section, rule_id


def test_exception_plan_never_asks_to_publish_a_rejected_row(rows):
    """A candidate we recommend rejecting is not a publish step."""
    packet = PACKET.read_text(encoding="utf-8")
    section = packet.split("### 1.7 RuleException")[1].split("**发布顺序")[0]
    rejected = {r["rule_id"] for r in rows if r["proposed_decision"] == "RECOMMEND_REJECT"}
    body = [ln for ln in section.splitlines() if ln.startswith("| `")]
    for line in body:
        cited = line.split("|")[1].strip().strip("`")
        assert cited not in rejected, f"{cited} 已建议拒绝，却出现在发布计划中"


def test_no_row_claims_a_strength_the_chain_does_not_support(rows):
    rows_with_conflict = [r["rule_id"] for r in rows if r["evidence_strength_conflict"]]
    assert rows_with_conflict, (
        "应至少检出 fp-pets-op / fp-sd-op 这类「登记表自述 primary_direct、"
        "证据链实为 OTA 聚合」的行"
    )
    for row in rows:
        if row["evidence_strength"] in {"search_snippet", "social_lead"}:
            assert row["proposed_decision"] != "RECOMMEND_APPROVE", row["rule_id"]
