"""Canonical Human Decision vocabulary — one source of truth for sign-off.

Why this module exists (found during GOV01-HUMAN-SIGNATURE-HARDEN-R1):

The sign-off packet printed one vocabulary and the publisher read another.
``HUMAN_REVIEW_QUICK_TABLE`` invited the reviewer to write ``APPROVE`` /
``REJECT`` while the machine consumed ``APPROVED`` / ``REJECTED`` — two spellings
of the same intent, no mapping between them. Worse, ``APPROVED_WITH_NOTE`` was
declared legal in the register's prose but accepted by neither code path: the
preflight called it "未填", and had it ever reached ``run()`` the single-line
``target = "APPROVED" if fd == "APPROVED" else "REJECTED"`` would have quietly
**rejected** a row the reviewer had approved.

So the vocabulary is now declared once, here, and both the generator and the
publisher import it. Adding a spelling anywhere else is what caused the drift.

Binding rules:
  * APPROVED / APPROVED_WITH_NOTE both publish as an approval; the latter must
    carry a ``review_note`` so the caveat travels with the decision.
  * HOLD is a real decision, never a blank — it is written down, not skipped.
  * REJECTED blocks publication for that row.
"""

from __future__ import annotations

APPROVED = "APPROVED"
APPROVED_WITH_NOTE = "APPROVED_WITH_NOTE"
HOLD = "HOLD"
REJECTED = "REJECTED"

#: Every accepted value, in display order. This is the machine enum.
HUMAN_DECISIONS: tuple[str, ...] = (APPROVED, APPROVED_WITH_NOTE, HOLD, REJECTED)

#: Decisions that carry an approval (都按批准发布).
APPROVAL_DECISIONS: frozenset[str] = frozenset({APPROVED, APPROVED_WITH_NOTE})

#: Decisions the publisher actually writes to the API.
EXECUTABLE_DECISIONS: frozenset[str] = frozenset({APPROVED, APPROVED_WITH_NOTE, REJECTED})

#: Reviewer-facing aliases accepted on input and normalised before use.
#: The packet no longer *prints* these, but a human pasting values out of an
#: older table or a spreadsheet must not be silently mis-read. Anything outside
#: this mapping including the canonical names is left untouched so preflight can
#: report it rather than guess.
INPUT_ALIASES: dict[str, str] = {
    "APPROVE": APPROVED,
    "APPROVED": APPROVED,
    "APPROVE_WITH_NOTE": APPROVED_WITH_NOTE,
    "APPROVED_WITH_NOTE": APPROVED_WITH_NOTE,
    "HOLD": HOLD,
    "REJECT": REJECTED,
    "REJECTED": REJECTED,
}

#: Chinese labels for the packet tables.
LABELS_ZH: dict[str, str] = {
    APPROVED: "批准",
    APPROVED_WITH_NOTE: "批准（附注意见）",
    HOLD: "挂起（证据不足）",
    REJECTED: "拒绝",
}


def normalise(value: str | None) -> str | None:
    """Map a human-typed spelling to its canonical value.

    Whitespace and case are forgiven; unknown values are returned untouched so
    the caller can refuse them explicitly instead of guessing.
    """
    if value is None:
        return None
    cleaned = value.strip().upper().replace("-", "_").replace(" ", "_")
    return INPUT_ALIASES.get(cleaned, cleaned)


def is_valid(value: str | None) -> bool:
    return value in HUMAN_DECISIONS
