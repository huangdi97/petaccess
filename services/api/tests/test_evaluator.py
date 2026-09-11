"""Phase 2 evaluator unit tests (GOAL #7 ten-case matrix)."""

from datetime import UTC, datetime

from app.rulespec.model import (
    AnimalInput,
    AnimalScope,
    ApplicabilityResult,
    Condition,
    QueryContext,
    ResultStatus,
    Rule,
    RuleAction,
    RuleEffect,
    RuleStatus,
)

NOW = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
PLACE = "place-xinghe-cafe"
ZONE_INDOOR = "zone-cafe-indoor"
ZONE_OUTDOOR = "zone-cafe-outdoor"


def ctx(
    *,
    animal: AnimalInput | None = None,
    zone: str | None = None,
    action: RuleAction = RuleAction.ENTER,
    when: datetime = NOW,
) -> QueryContext:
    return QueryContext(
        animal=animal or AnimalInput(species="dog", service_role="none", weight_kg=9.5),
        place_id=PLACE,
        zone_id=zone,
        date_time=when,
        intended_action=action,
    )


def rule(
    id_: str,
    *,
    scope: AnimalScope = AnimalScope.ORDINARY_PET,
    action: RuleAction = RuleAction.ENTER,
    effect: RuleEffect = RuleEffect.ALLOWED,
    zone: str | None = None,
    status: RuleStatus = RuleStatus.CURRENT,
    conditions: tuple[Condition, ...] = (),
    place: str = PLACE,
) -> Rule:
    return Rule(
        id=id_,
        animal_scope=scope,
        action=action,
        effect=effect,
        status=status,
        zone_id=zone,
        place_id=place,
        conditions=conditions,
        source_id=f"src-{id_}",
    )


# 1. 室内禁止 / 户外允许
def test_indoor_prohibited_outdoor_allowed():
    rules = [
        rule("r-in", effect=RuleEffect.PROHIBITED, zone=ZONE_INDOOR),
        rule(
            "r-out",
            effect=RuleEffect.CONDITIONAL,
            zone=ZONE_OUTDOOR,
            conditions=(Condition("leash_required", value_flag=True),),
        ),
    ]
    r_in = evaluate(ctx(zone=ZONE_INDOOR), rules)
    assert r_in.status == ResultStatus.RESTRICTED
    assert r_in.reason_codes == ["explicit_prohibition"]
    # leash_required is an obligation; query did not affirm it → CONDITIONAL
    r_out = evaluate(ctx(zone=ZONE_OUTDOOR), rules)
    assert r_out.status == ResultStatus.CONDITIONAL
    assert any(u.condition_type == "leash_required" for u in r_out.unmet_conditions)


# 2. 10kg 上限
def test_weight_cap_met():
    r = rule(
        "r-weight",
        effect=RuleEffect.CONDITIONAL,
        conditions=(Condition("max_weight_kg", value_numeric=10.0),),
    )
    res = evaluate(ctx(animal=AnimalInput(species="dog", service_role="none", weight_kg=9.5)), [r])
    assert res.status == ResultStatus.MATCH


def test_weight_cap_exceeded():
    r = rule(
        "r-weight",
        effect=RuleEffect.CONDITIONAL,
        conditions=(Condition("max_weight_kg", value_numeric=10.0),),
    )
    res = evaluate(ctx(animal=AnimalInput(species="dog", service_role="none", weight_kg=12.0)), [r])
    assert res.status == ResultStatus.CONDITIONAL
    assert any(u.condition_type == "max_weight_kg" for u in res.unmet_conditions)


# 3. 未知体重 → UNKNOWN，绝不猜
def test_unknown_weight_is_unknown_not_allowed():
    r = rule(
        "r-weight",
        effect=RuleEffect.CONDITIONAL,
        conditions=(Condition("max_weight_kg", value_numeric=10.0),),
    )
    res = evaluate(ctx(animal=AnimalInput(species="dog", service_role="none", weight_kg=None)), [r])
    assert res.status == ResultStatus.UNKNOWN
    assert res.reason_codes == ["missing_query_input"]
    assert any(u.input == "weight_kg" for u in res.unknown_inputs)


# 4. 时段
def test_time_window_outside_is_conditional():
    r = rule(
        "r-night",
        effect=RuleEffect.CONDITIONAL,
        conditions=(
            Condition(
                "time_windows",
                value_json=[{"days": [0, 1, 2, 3, 4, 5, 6], "start": "21:00", "end": "23:30"}],
            ),
        ),
    )
    res = evaluate(ctx(when=NOW.replace(hour=12)), [r])
    assert res.status == ResultStatus.CONDITIONAL


def test_time_window_inside_is_match():
    r = rule(
        "r-night",
        effect=RuleEffect.CONDITIONAL,
        conditions=(
            Condition(
                "time_windows",
                value_json=[{"days": [0, 1, 2, 3, 4, 5, 6], "start": "21:00", "end": "23:30"}],
            ),
        ),
    )
    res = evaluate(ctx(when=NOW.replace(hour=22)), [r])
    assert res.status == ResultStatus.MATCH


def test_overnight_time_window_wraparound():
    r = rule(
        "r-overnight",
        effect=RuleEffect.CONDITIONAL,
        conditions=(
            Condition(
                "time_windows",
                value_json=[{"days": [0, 1, 2, 3, 4, 5, 6], "start": "22:00", "end": "02:00"}],
            ),
        ),
    )
    res = evaluate(ctx(when=NOW.replace(hour=1)), [r])
    assert res.status == ResultStatus.MATCH


# 5. 服务犬独立于普通宠物
def test_service_dog_not_governed_by_ordinary_pet_rule():
    r = rule("r-pet", effect=RuleEffect.PROHIBITED)
    res = evaluate(ctx(animal=AnimalInput(species="dog", service_role="working")), [r])
    assert res.status == ResultStatus.UNKNOWN  # ordinary_pet rule does not govern


def test_service_dog_rule_applies():
    r = rule("r-sd", scope=AnimalScope.SERVICE_DOG, effect=RuleEffect.ALLOWED)
    res = evaluate(ctx(animal=AnimalInput(species="dog", service_role="working")), [r])
    assert res.status == ResultStatus.MATCH


def test_ordinary_pet_query_not_governed_by_service_dog_rule():
    r = rule("r-sd", scope=AnimalScope.SERVICE_DOG, effect=RuleEffect.ALLOWED)
    res = evaluate(ctx(animal=AnimalInput(species="dog", service_role="none")), [r])
    assert res.status == ResultStatus.UNKNOWN


# 6. Zone 规则优先于 Place 规则（覆盖语义）
def test_zone_rule_beats_place_rule():
    place_allowed = rule("r-place-allow", effect=RuleEffect.ALLOWED)
    zone_prohibited = rule("r-zone-no", effect=RuleEffect.PROHIBITED, zone=ZONE_INDOOR)
    res = evaluate(ctx(zone=ZONE_INDOOR), [place_allowed, zone_prohibited])
    assert res.status == ResultStatus.RESTRICTED


# 7. superseded 规则不生效
def test_superseded_rule_ignored():
    r = rule("r-old", effect=RuleEffect.PROHIBITED, status=RuleStatus.SUPERSEDED)
    r_new = rule("r-new", effect=RuleEffect.ALLOWED, status=RuleStatus.CURRENT)
    res = evaluate(ctx(), [r, r_new])
    assert res.status == ResultStatus.MATCH
    assert res.matched_rules == ["r-new"]


# 8. 冲突
def test_conflict_allowed_vs_prohibited():
    r1 = rule("r1", effect=RuleEffect.ALLOWED)
    r2 = rule("r2", effect=RuleEffect.PROHIBITED)
    res = evaluate(ctx(), [r1, r2])
    assert res.status == ResultStatus.CONFLICT
    assert res.reason_codes == ["conflicting_rules_allowed_vs_prohibited"]


# 9. 无规则 → UNKNOWN
def test_no_rules_is_unknown():
    res = evaluate(ctx(), [])
    assert res.status == ResultStatus.UNKNOWN
    assert res.reason_codes == ["no_rule_in_scope"]


# 10. Observation 与 Rule 共存但不改变 evaluator
def test_observations_never_feed_evaluator():
    r = rule(
        "r-out",
        effect=RuleEffect.CONDITIONAL,
        zone=ZONE_OUTDOOR,
        conditions=(Condition("leash_required", value_flag=True),),
    )
    # an observation claiming someone walked in off-leash unbothered must NOT change the result
    res = evaluate(ctx(zone=ZONE_OUTDOOR), [r])
    assert res.status == ResultStatus.CONDITIONAL
    assert all("observation" not in u.condition_type for u in res.unmet_conditions)


def evaluate(ctx_: QueryContext, rules: list[Rule]) -> ApplicabilityResult:
    from app.rulespec.evaluator import evaluate as _evaluate

    return _evaluate(ctx_, rules)
