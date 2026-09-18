"""Condition ingest boundary — one canonical key, one place to translate (ADR-029).

The defect this closes
----------------------

Wave 01 fed candidates whose conditions were written as::

    {"type": "leash_required", "value": true}

The canonical publisher schema requires ``condition_type``. Ten of the 31
Wave-01 candidates used the legacy key, so the ingest produced rows the gate
could not read — and the failure surfaced *at publish time*, long after the
human had approved them.

The tempting fix is to teach every reader both keys. That is what the previous
round did in ``candidate_service.publish`` (``cond.get("condition_type") or
cond.get("type")``), and it is the wrong shape: it puts a *translation of a
legacy input format* inside the domain layer, permanently. Two canonical keys
then circulate forever, every new reader must remember both, and the next
consumer that forgets one silently treats a leashed-pet rule as unconditional.

The rule (§8): **translation happens once, at the boundary where foreign data
enters.** Inside the platform there is exactly one key, ``condition_type``.

Where the boundary is
---------------------

:func:`normalize_conditions` is called by the ingestion entry point
(:func:`app.services.candidate_service.create_from_extraction`) and by any
importer that reads an external extract. It:

* rewrites legacy ``type`` → ``condition_type``;
* refuses when *both* keys are present and disagree (ambiguous input is not
  guessed — it is refused);
* refuses unknown condition types against the canonical enum, so a typo cannot
  become a rule that never fires;
* preserves every other key (``value``, ``note`` …) untouched.

Signed candidates are never rewritten
-------------------------------------

This function is an *ingest* adapter. It does not run over stored rows. A
candidate that a human already signed keeps its bytes; if its conditions use the
legacy key, the correct remedy is a new candidate and a new review (§9), never
an in-place edit under an existing signature.
"""

from __future__ import annotations

from typing import Any

from app.models.enums import RuleConditionType

__all__ = [
    "ConditionIngestError",
    "CANONICAL_CONDITION_KEY",
    "LEGACY_CONDITION_KEY",
    "normalize_conditions",
]

#: The one key the platform reads. Nothing downstream may accept another.
CANONICAL_CONDITION_KEY = "condition_type"
#: The only legacy spelling tolerated, and only at this boundary.
LEGACY_CONDITION_KEY = "type"


class ConditionIngestError(ValueError):
    """Raised when an incoming condition cannot be normalised without guessing."""


def normalize_conditions(conditions: list | None) -> list:
    """Translate incoming conditions to the canonical schema (ingest boundary).

    Deterministic and total: every returned dict has ``condition_type`` and
    nothing else changed. Raises :class:`ConditionIngestError` rather than
    guessing when the input is ambiguous or names an unknown condition.

    ``None`` and ``[]`` both yield ``[]`` — an absent condition list is not an
    error, it is an unconditional condition set.
    """
    if not conditions:
        return []
    if not isinstance(conditions, list):
        raise ConditionIngestError(f"conditions 必须是列表，收到 {type(conditions).__name__}")

    valid = {e.value for e in RuleConditionType}
    out: list[dict[str, Any]] = []
    for index, raw in enumerate(conditions):
        if not isinstance(raw, dict):
            raise ConditionIngestError(f"第 {index} 个 condition 不是对象：{raw!r}")

        has_canonical = CANONICAL_CONDITION_KEY in raw
        has_legacy = LEGACY_CONDITION_KEY in raw

        if (
            has_canonical
            and has_legacy
            and raw[CANONICAL_CONDITION_KEY] != raw[LEGACY_CONDITION_KEY]
        ):
            raise ConditionIngestError(
                f"第 {index} 个 condition 同时含 {CANONICAL_CONDITION_KEY} 与 "
                f"{LEGACY_CONDITION_KEY} 且取值不同"
                f"（{raw[CANONICAL_CONDITION_KEY]!r} vs {raw[LEGACY_CONDITION_KEY]!r}）——"
                "歧义输入不猜测，拒绝导入。"
            )

        key = CANONICAL_CONDITION_KEY if has_canonical else LEGACY_CONDITION_KEY
        if key not in raw:
            raise ConditionIngestError(
                f"第 {index} 个 condition 缺少 {CANONICAL_CONDITION_KEY}"
                f"（旧 schema 用 {LEGACY_CONDITION_KEY}）：{raw!r}"
            )

        condition_type = raw[key]
        if condition_type not in valid:
            raise ConditionIngestError(
                f"第 {index} 个 condition 的 {CANONICAL_CONDITION_KEY}="
                f"{condition_type!r} 不在规范词表内——拼写错误不得成为永不生效的规则。"
            )

        # Rebuild with the canonical key first, then every other key verbatim.
        normalized = {CANONICAL_CONDITION_KEY: condition_type}
        for k, v in raw.items():
            if k in (CANONICAL_CONDITION_KEY, LEGACY_CONDITION_KEY):
                continue
            normalized[k] = v
        out.append(normalized)
    return out
