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
    assert register["revision"] == "R2-FINAL"
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


def test_fairmont_content_hash_reproduces_from_the_quote(register):
    """A content_hash that cannot be recomputed proves nothing."""
    meta = register["fp_sd_op_source_search"]
    assert meta["quote_zh"] == FAIRMONT_QUOTE_ZH
    assert meta["hash_formula"] == "sha256(captured_excerpt)"
    expected = hashlib.sha256(FAIRMONT_QUOTE_ZH.encode("utf-8")).hexdigest()
    assert meta["content_hash"] == expected


def test_the_ota_shaped_row_is_superseded_not_published(by_id):
    """Rejection must be for the right reason: this row models the same sentence
    as the coarse unproven widening — not because a first-party source is absent."""
    old = by_id["fp-sd-op"]
    assert old["proposed_decision"] == "RECOMMEND_REJECT"
    assert "SUPERSEDED_BY_SOURCE_FAITHFUL_ROW" in (old.get("reject_reason_codes") or [])
    assert old["subject_scope_normalized"] != "guide_dog"


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
