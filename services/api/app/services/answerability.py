"""Answerability Matrix (NEXT_GOAL §B17): which consumer questions can this
place answer, honestly — answerable / unknown / stale per question.

Internal computation only: no merchant scoring, no public ranking.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

QUESTION_DEFS: list[tuple[str, str]] = [
    # (question_key, description)
    ("ordinary_dog_entry", "普通犬能否进入"),
    ("indoor_outdoor", "能进哪里（室内/户外）"),
    ("leash", "是否需要牵引"),
    ("stroller_carrier", "是否需要推车/包"),
    ("size_limit", "是否有体型/体重限制"),
    ("service_dog", "服务犬通行"),
    ("seat", "能否上顾客座椅"),
    ("food_area", "能否接近食品自助区"),
    ("tableware", "是否使用顾客餐具"),
    ("source", "来源可追溯"),
    ("freshness", "规则新鲜度"),
]

STALE_DAYS = 180


@dataclass(frozen=True)
class AnswerCell:
    question: str
    state: str  # answerable | unknown | stale
    detail: str


def compute_answerability(
    *,
    rules: list[
        dict
    ],  # serialized current rules: effect/animal_scope/action/conditions/last_verified_at
    coexistence: dict[str, str],
    now: datetime,
) -> list[AnswerCell]:
    current = [r for r in rules if r.get("status", "current") == "current"]
    ordinary = [r for r in current if r.get("animal_scope") in ("ordinary_pet", "dog")]
    service = [r for r in current if r.get("animal_scope") == "service_dog"]
    cells: list[AnswerCell] = []

    def freshest(rows: list[dict]) -> datetime | None:
        stamps = [r.get("last_verified_at") for r in rows if r.get("last_verified_at")]
        return max(stamps) if stamps else None  # type: ignore[type-var]

    def stale_cell(key: str, latest: datetime | None) -> AnswerCell:
        if latest is None:
            return AnswerCell(key, "unknown", "从未核验")
        age = (now - latest).days
        if age > STALE_DAYS:
            return AnswerCell(key, "stale", f"最近核验 {age} 天前（需要复核）")
        return AnswerCell(key, "answerable", f"最近核验 {age} 天前")

    # ordinary dog entry
    if ordinary:
        cells.append(stale_cell("ordinary_dog_entry", freshest(ordinary)))
    else:
        cells.append(AnswerCell("ordinary_dog_entry", "unknown", "无普通犬规则"))
    # indoor/outdoor
    has_zone_rules = any(r.get("zone_id") for r in ordinary)
    cells.append(
        AnswerCell(
            "indoor_outdoor",
            "answerable" if has_zone_rules else "unknown",
            "有分区规则" if has_zone_rules else "无分区规则",
        )
        if ordinary
        else AnswerCell("indoor_outdoor", "unknown", "无普通犬规则")
    )

    # conditions
    def cond_answer(key: str, ctype: str) -> None:
        matched = [
            r
            for r in ordinary
            if any(
                (c.get("condition_type") or c.get("type")) == ctype
                for c in (r.get("conditions") or [])
            )
        ]
        cells.append(
            stale_cell(key, freshest(matched))
            if matched
            else AnswerCell(key, "unknown", "规则未涉及")
        )

    cond_answer("leash", "leash_required")
    cond_answer("stroller_carrier", "carrier_required")
    cond_answer("stroller_carrier", "stroller_required") if False else None
    cond_answer("size_limit", "max_weight_kg")
    # service dog
    cells.append(
        stale_cell("service_dog", freshest(service))
        if service
        else AnswerCell("service_dog", "unknown", "无服务犬规则")
    )
    # coexistence-derived questions
    for key, attr in (
        ("seat", "animal_on_customer_seat"),
        ("food_area", "animal_in_self_service_food_area"),
        ("tableware", "animal_use_customer_tableware"),
    ):
        if attr in coexistence:
            cells.append(AnswerCell(key, "answerable", f"属性={coexistence[attr]}"))
        else:
            cells.append(AnswerCell(key, "unknown", "未结构化记录"))
    # source/freshness meta
    cells.append(
        AnswerCell(
            "source",
            "answerable" if any(r.get("source_id") for r in current) else "unknown",
            "全部规则有来源" if any(r.get("source_id") for r in current) else "存在无来源规则",
        )
    )
    all_stamps = [r.get("last_verified_at") for r in current if r.get("last_verified_at")]
    cells.append(stale_cell("freshness", max(all_stamps) if all_stamps else None))  # type: ignore[type-var]
    return cells
