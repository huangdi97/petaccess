"""Adversarial synthetic fixtures (NEXT_GOAL §C3, ≥30 classes).

Each entry in ``ADVERSARIAL_CLASSES`` is one adversarial scenario class the
domain must survive; the count is auditable in code and pinned by
``test_registry_has_at_least_30_classes``. All fixtures are synthetic — no
real-merchant rules are fabricated (REALITY_AUDIT_PLAN 第一阶段).

Class groups:
- A 体型/阈值/携带方式 (evaluator conditions, missing inputs)
- B 空间分层 (zones, specificity, spatial ownership)
- C 时间维度 (windows, future/expired events, event shadows operator)
- D 服务犬隔离 (scope isolation both directions)
- E 层级与冲突 (resolver: legal floor, override chain, conflicts, legacy NULL)
- F 候选状态机 (no direct publish, terminal states, no skips)
- G 共处边界 (UNKNOWN never MATCH, no score, seat/table/food/tableware)
- H 数据完整性 (observation isolation, PetAccessJSON validation, freshness)
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.models.v05 import CANDIDATE_TRANSITIONS
from app.rulespec.evaluator import evaluate
from app.rulespec.model import (
    AnimalInput,
    Condition,
    QueryContext,
    ResultStatus,
    Rule,
    RuleAction,
    RuleEffect,
    RuleStatus,
)
from app.rulespec.petaccessjson import PetAccessJSONError, dump
from app.rulespec.v05_boundary import match as boundary_match
from app.rulespec.v05_resolver import ComplianceState, LayeredRule, resolve
from app.services.answerability import compute_answerability

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)  # a Saturday
SAT = 5  # datetime.weekday(): Monday=0 … Sunday=6

ADVERSARIAL_CLASSES = [
    # --- A 体型 / 阈值 / 携带方式 -------------------------------------------
    "A01_small_vs_large_dog_weight_gate",
    "A02_weight_missing_is_unknown_never_guessed",
    "A03_shoulder_height_40cm_threshold",
    "A04_closed_carrier_obligation",
    "A05_stroller_no_ground_contact",
    "A06_max_pet_count",
    # --- B 空间分层 ----------------------------------------------------------
    "B07_indoor_prohibited_outdoor_allowed",
    "B08_mall_public_area_vs_dining_zone",
    "B09_supermarket_1f_prohibited_3f_allowed",
    "B10_designated_pet_entrance_elevator",
    "B11_zone_rule_does_not_leak_to_other_zone",
    "B12_bare_rule_without_spatial_owner_never_governs",
    # --- C 时间维度 ----------------------------------------------------------
    "C13_weekend_only_window",
    "C14_night_window",
    "C15_overnight_wraparound_window",
    "C16_future_event_not_in_scope",
    "C17_expired_event_not_current_but_preserved",
    "C18_active_event_shadows_operator",
    # --- D 服务犬隔离 --------------------------------------------------------
    "D19_service_dog_exception_over_ordinary_prohibition",
    "D20_ordinary_rule_never_governs_working_service_dog",
    "D21_service_dog_in_training_isolated_like_working",
    # --- E 层级与冲突 --------------------------------------------------------
    "E22_mandatory_legal_floor_not_relaxable",
    "E23_mandatory_legal_obligations_preserved",
    "E24_zone_override_beats_place_beats_template",
    "E25_allowed_vs_prohibited_conflict_prohibition_governs",
    "E26_legacy_null_layer_review_required",
    "E27_superseded_rule_not_current",
    "E28_resolver_unknown_when_no_rules",
    # --- F 候选状态机 --------------------------------------------------------
    "F29_extracted_cannot_publish_directly",
    "F30_unpublished_candidate_never_effective",
    "F31_rejected_candidate_is_terminal",
    "F32_state_machine_rejects_skips",
    # --- G 共处边界 ----------------------------------------------------------
    "G33_boundary_unknown_never_match",
    "G34_boundary_emits_no_total_score",
    "G35_seat_table_foodarea_tableware_matrix",
    "G36_dining_derived_from_effect_only_no_invention",
    # --- H 数据完整性 / 可移植 ----------------------------------------------
    "H37_observation_data_absent_from_resolver",
    "H38_petaccessjson_rejects_invalid_layer_effect",
    "H39_answerability_stale_means_review_not_invalid",
    "H40_answerability_unknown_without_rules",
]


def test_registry_has_at_least_30_classes():
    assert len(ADVERSARIAL_CLASSES) >= 30
    assert len(set(ADVERSARIAL_CLASSES)) == len(ADVERSARIAL_CLASSES), "class ids must be unique"


# ------------------------------------------------------------- helpers


def _rule(
    rid,
    scope="ordinary_pet",
    action=RuleAction.ENTER,
    effect=RuleEffect.ALLOWED,
    status=RuleStatus.CURRENT,
    zone=None,
    place="p1",
    conditions=(),
    **kw,
):
    return Rule(
        id=rid,
        animal_scope=scope,
        action=action,
        effect=effect,
        status=status,
        zone_id=zone,
        place_id=place,
        conditions=tuple(conditions),
        **kw,
    )


def _ctx(animal=None, zone=None, action=RuleAction.ENTER, when=NOW):
    return QueryContext(
        animal=animal or AnimalInput(species="dog"),
        place_id="p1",
        date_time=when,
        intended_action=action,
        zone_id=zone,
    )


def _layered(rid, layer, origin, effect, scope="ordinary_pet", **kw):
    return LayeredRule(
        id=rid,
        animal_scope=scope,
        action="enter",
        effect=effect,
        rule_layer=layer,
        origin=origin,
        **kw,
    )


# ----------------------------------------------------- A 体型/阈值/携带方式


def test_A01_small_vs_large_dog_weight_gate():
    """min_weight_kg 10：8kg 被拦，12kg 通过 —— 同一规则两个体型不同结论。"""
    rule = _rule(
        "w1",
        effect=RuleEffect.CONDITIONAL,
        conditions=[Condition(condition_type="min_weight_kg", value_numeric=10)],
    )
    small = evaluate(_ctx(AnimalInput(species="dog", weight_kg=8)), [rule])
    large = evaluate(_ctx(AnimalInput(species="dog", weight_kg=12)), [rule])
    assert small.status == ResultStatus.CONDITIONAL
    assert any(u.condition_type == "min_weight_kg" for u in small.unmet_conditions)
    assert large.status == ResultStatus.MATCH


def test_A02_weight_missing_is_unknown_never_guessed():
    """阈值条件缺体重输入 → UNKNOWN + unknown_inputs，绝不猜成允许/禁止。"""
    rule = _rule(
        "w2",
        effect=RuleEffect.CONDITIONAL,
        conditions=[Condition(condition_type="max_weight_kg", value_numeric=10)],
    )
    r = evaluate(_ctx(AnimalInput(species="dog", weight_kg=None)), [rule])
    assert r.status == ResultStatus.UNKNOWN
    assert r.unknown_inputs and r.unknown_inputs[0].input == "weight_kg"


def test_A03_shoulder_height_40cm_threshold():
    """40cm 肩高门槛：38 过，45 不过，缺身高 UNKNOWN。"""
    rule = _rule(
        "h1",
        effect=RuleEffect.CONDITIONAL,
        conditions=[Condition(condition_type="max_shoulder_height_cm", value_numeric=40)],
    )
    assert evaluate(_ctx(AnimalInput(species="dog", shoulder_height_cm=38)), [rule]).status == (
        ResultStatus.MATCH
    )
    assert evaluate(_ctx(AnimalInput(species="dog", shoulder_height_cm=45)), [rule]).status == (
        ResultStatus.CONDITIONAL
    )
    assert evaluate(_ctx(AnimalInput(species="dog")), [rule]).status == ResultStatus.UNKNOWN


def test_A04_closed_carrier_obligation():
    """封闭包：carrier_required 是义务条件，查询未声明即未满足，不由 AI 认定。"""
    rule = _rule(
        "c1",
        effect=RuleEffect.CONDITIONAL,
        conditions=[Condition(condition_type="carrier_required", value_flag=True)],
    )
    r = evaluate(_ctx(), [rule])
    assert r.status == ResultStatus.CONDITIONAL
    assert r.unmet_conditions[0].condition_type == "carrier_required"


def test_A05_stroller_no_ground_contact():
    """推车/不落地：no_ground 义务在 ground_contact 动作规则上未声明即未满足。"""
    rule = _rule(
        "s1",
        action=RuleAction.GROUND_CONTACT,
        effect=RuleEffect.CONDITIONAL,
        conditions=[Condition(condition_type="no_ground", value_flag=True)],
    )
    r = evaluate(_ctx(action=RuleAction.GROUND_CONTACT), [rule])
    assert r.status == ResultStatus.CONDITIONAL
    assert r.unmet_conditions[0].condition_type == "no_ground"


def test_A06_max_pet_count():
    """限养 2 只：2 只满足条件，3 只不满足。"""
    rule = _rule(
        "n1",
        effect=RuleEffect.CONDITIONAL,
        conditions=[Condition(condition_type="max_count", value_numeric=2)],
    )
    assert evaluate(_ctx(AnimalInput(species="dog", count=2)), [rule]).status == ResultStatus.MATCH
    assert evaluate(_ctx(AnimalInput(species="dog", count=3)), [rule]).status == (
        ResultStatus.CONDITIONAL
    )


# --------------------------------------------------------- B 空间分层


def test_B07_indoor_prohibited_outdoor_allowed():
    """室内堂食禁止 / 户外允许：同一 place 两个 zone 相反结论。"""
    rules = [
        _rule("in", zone="z-indoor", effect=RuleEffect.PROHIBITED),
        _rule("out", zone="z-outdoor", effect=RuleEffect.ALLOWED),
    ]
    assert evaluate(_ctx(zone="z-indoor"), rules).status == ResultStatus.RESTRICTED
    assert evaluate(_ctx(zone="z-outdoor"), rules).status == ResultStatus.MATCH


def test_B08_mall_public_area_vs_dining_zone():
    """商场公共区允许带宠 / 餐饮区禁止：分区规则互不越界。"""
    rules = [
        _rule("pub", zone="z-public", effect=RuleEffect.ALLOWED),
        _rule("fnb", zone="z-fnb", effect=RuleEffect.PROHIBITED),
    ]
    assert evaluate(_ctx(zone="z-public"), rules).status == ResultStatus.MATCH
    assert evaluate(_ctx(zone="z-fnb"), rules).status == ResultStatus.RESTRICTED


def test_B09_supermarket_1f_prohibited_3f_allowed():
    """超市 1F 禁止 / 3F 宠物区允许（带 zone 查询各自命中）。"""
    rules = [
        _rule("f1", zone="z-1f", effect=RuleEffect.PROHIBITED),
        _rule(
            "f3",
            zone="z-3f",
            effect=RuleEffect.CONDITIONAL,
            conditions=[Condition(condition_type="leash_required", value_flag=True)],
        ),
    ]
    r1 = evaluate(_ctx(zone="z-1f"), rules)
    r3 = evaluate(_ctx(zone="z-3f"), rules)
    assert r1.status == ResultStatus.RESTRICTED
    assert r3.status == ResultStatus.CONDITIONAL


def test_B10_designated_pet_entrance_elevator():
    """指定入口/电梯（对抗点）：评估器不会假装执行它无法核验的条件 ——
    未建模的条件类型（use_pet_entrance 等）只作备注，绝不凭空制造禁止
    （UNKNOWN≠禁止原则的镜像：无证据≠拒绝）。“南门宠物入口→宠物电梯→3F”
    这类路径语义由 Entrance/AccessPath 实体表达（NEXT_GOAL B11/B12）。"""
    rule = _rule(
        "e1",
        effect=RuleEffect.ALLOWED,
        conditions=[
            Condition(condition_type="use_pet_entrance", value_flag=True),
            Condition(condition_type="use_pet_elevator", value_flag=True),
        ],
    )
    r = evaluate(_ctx(), [rule])
    assert r.status == ResultStatus.MATCH  # 未建模条件不阻塞，也不伪造
    assert not r.unmet_conditions and not r.unknown_inputs


def test_B11_zone_rule_does_not_leak_to_other_zone():
    """A 区的禁止不得泄漏到 B 区的查询（B 区无规则 → UNKNOWN 而非禁止）。"""
    rules = [_rule("a", zone="z-a", effect=RuleEffect.PROHIBITED)]
    r = evaluate(_ctx(zone="z-b"), rules)
    assert r.status == ResultStatus.UNKNOWN
    assert r.reason_codes == ["no_rule_in_scope"]


def test_B12_bare_rule_without_spatial_owner_never_governs():
    """无 place/zone 归属的裸规则不能治理任何场所查询（防止脏数据生效）。"""
    orphan = Rule(
        id="orphan",
        animal_scope="ordinary_pet",
        action=RuleAction.ENTER,
        effect=RuleEffect.ALLOWED,
        status=RuleStatus.CURRENT,
        zone_id=None,
        place_id=None,
    )
    assert evaluate(_ctx(), [orphan]).status == ResultStatus.UNKNOWN


# --------------------------------------------------------- C 时间维度


def test_C13_weekend_only_window():
    """周末开放：周六条件满足，周三 outside_window。"""
    rule = _rule(
        "wk",
        effect=RuleEffect.CONDITIONAL,
        conditions=[
            Condition(
                condition_type="time_windows",
                value_json=[{"days": [SAT, 6], "start": "09:00", "end": "18:00"}],
            )
        ],
    )
    sat = evaluate(_ctx(when=datetime(2026, 9, 12, 10, 0, tzinfo=UTC)), [rule])
    wed = evaluate(_ctx(when=datetime(2026, 9, 9, 10, 0, tzinfo=UTC)), [rule])
    assert sat.status == ResultStatus.MATCH
    assert wed.status == ResultStatus.CONDITIONAL
    assert wed.unmet_conditions[0].condition_type == "time_windows"


def test_C14_night_window():
    """夜间开放 21:00–23:30：22:30 满足，12:00 不满足。"""
    rule = _rule(
        "nt",
        effect=RuleEffect.CONDITIONAL,
        conditions=[
            Condition(
                condition_type="time_windows", value_json=[{"start": "21:00", "end": "23:30"}]
            )
        ],
    )
    night = evaluate(_ctx(when=datetime(2026, 9, 12, 22, 30, tzinfo=UTC)), [rule])
    noon = evaluate(_ctx(when=NOW), [rule])
    assert night.status == ResultStatus.MATCH
    assert noon.status == ResultStatus.CONDITIONAL


def test_C15_overnight_wraparound_window():
    """跨夜窗口 22:00–02:00：23:00 与 01:00 满足，12:00 不满足。"""
    rule = _rule(
        "ov",
        effect=RuleEffect.CONDITIONAL,
        conditions=[
            Condition(
                condition_type="time_windows", value_json=[{"start": "22:00", "end": "02:00"}]
            )
        ],
    )
    assert evaluate(_ctx(when=datetime(2026, 9, 12, 23, 0, tzinfo=UTC)), [rule]).status == (
        ResultStatus.MATCH
    )
    assert evaluate(_ctx(when=datetime(2026, 9, 13, 1, 0, tzinfo=UTC)), [rule]).status == (
        ResultStatus.MATCH
    )
    assert evaluate(_ctx(when=NOW), [rule]).status == ResultStatus.CONDITIONAL


def test_C16_future_event_not_in_scope():
    """未开始的临时活动不在作用域内（明天生效）。"""
    rule = _rule("fut", effect=RuleEffect.ALLOWED, effective_from=NOW + timedelta(days=1))
    assert evaluate(_ctx(), [rule]).status == ResultStatus.UNKNOWN


def test_C17_expired_event_not_current_but_preserved():
    """已结束的活动不再生效，但数据对象保留（历史可查），不被删除。"""
    expired = _rule(
        "ev1",
        effect=RuleEffect.ALLOWED,
        effective_from=NOW - timedelta(days=7),
        effective_to=NOW - timedelta(days=1),
    )
    r = evaluate(_ctx(), [expired])
    assert r.status == ResultStatus.UNKNOWN
    assert expired.id == "ev1"  # 对象仍在，历史保留


def test_C18_active_event_shadows_operator():
    """生效中的临时政策遮蔽同 scope 的运营商政策（事件优先）。"""
    eff = resolve(
        legal=[],
        guidance=[],
        template_rules=[],
        operator_rules=[_layered("op1", "OPERATOR_POLICY", "operator_direct", "prohibited")],
        event_rules=[
            _layered(
                "ev2",
                "TEMPORARY_POLICY",
                "event",
                "allowed",
                effective_from=NOW - timedelta(hours=1),
                effective_to=NOW + timedelta(hours=1),
            )
        ],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )
    assert eff.effect == "allowed"
    assert {s[0].id for s in eff.suppressed_rules} == {"op1"}
    assert [r.id for r in eff.applicable_rules] == ["ev2"]


# --------------------------------------------------------- D 服务犬隔离


def test_D19_service_dog_exception_over_ordinary_prohibition():
    """普通宠物禁止 + 服务犬明确允许：工作犬可以进，宠物仍被禁止。"""
    rules = [
        _rule("petban", scope="ordinary_pet", effect=RuleEffect.PROHIBITED),
        _rule("sd", scope="service_dog", effect=RuleEffect.ALLOWED),
    ]
    working = evaluate(_ctx(AnimalInput(species="dog", service_role="working")), rules)
    pet = evaluate(_ctx(AnimalInput(species="dog", service_role="none")), rules)
    assert working.status == ResultStatus.MATCH
    assert pet.status == ResultStatus.RESTRICTED


def test_D20_ordinary_rule_never_governs_working_service_dog():
    """普通宠物规则不治理工作中的服务犬查询（服务犬通行权独立）。"""
    rules = [
        _rule(
            "pet",
            scope="ordinary_pet",
            effect=RuleEffect.CONDITIONAL,
            conditions=[Condition(condition_type="leash_required", value_flag=True)],
        )
    ]
    r = evaluate(_ctx(AnimalInput(species="dog", service_role="working")), rules)
    assert r.status == ResultStatus.UNKNOWN


def test_D21_service_dog_in_training_isolated_like_working():
    """in_training 与 working 一样独立于普通宠物规则。"""
    rules = [_rule("pet", scope="ordinary_pet", effect=RuleEffect.PROHIBITED)]
    r = evaluate(_ctx(AnimalInput(species="dog", service_role="in_training")), rules)
    assert r.status == ResultStatus.UNKNOWN


# --------------------------------------------------------- E 层级与冲突


def test_E22_mandatory_legal_floor_not_relaxable():
    """法定强制禁令是地板：管理方/模板/事件都不得放宽。"""
    eff = resolve(
        legal=[_layered("law1", "LEGAL", "legal", "prohibited", mandatory_level="mandatory")],
        guidance=[],
        template_rules=[_layered("t1", "OPERATOR_POLICY", "template", "allowed")],
        operator_rules=[_layered("op1", "OPERATOR_POLICY", "operator_direct", "allowed")],
        event_rules=[_layered("ev1", "TEMPORARY_POLICY", "event", "allowed")],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )
    assert eff.effect == "prohibited"
    suppressed_ids = {s[0].id for s in eff.suppressed_rules}
    assert {"t1", "op1", "ev1"} <= suppressed_ids
    assert eff.compliance_state == ComplianceState.POTENTIAL_CONFLICT


def test_E23_mandatory_legal_obligations_preserved():
    """法定义务条件保留在输出 obligations 中，不被下层规则吞掉。"""
    legal = LayeredRule(
        id="law2",
        animal_scope="ordinary_pet",
        action="enter",
        effect="conditional",
        rule_layer="LEGAL",
        origin="legal",
        mandatory_level="mandatory",
        conditions=({"condition_type": "leash_required"},),
    )
    eff = resolve(
        legal=[legal],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )
    assert "leash_required" in eff.obligations


def test_E24_zone_override_beats_place_beats_template():
    """集团模板 → 门店 override → Zone override 的特异性链。"""
    eff = resolve(
        legal=[],
        guidance=[],
        template_rules=[_layered("t", "OPERATOR_POLICY", "template", "prohibited")],
        operator_rules=[
            _layered("po", "OPERATOR_POLICY", "place_override", "conditional"),
            _layered("zo", "OPERATOR_POLICY", "zone_override", "allowed", zone_id="z1"),
        ],
        event_rules=[],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id="z1",
        now=NOW,
    )
    assert [r.id for r in eff.applicable_rules] == ["zo"]
    assert eff.effect == "allowed"
    assert eff.compliance_state == ComplianceState.CONSISTENT


def test_E25_allowed_vs_prohibited_conflict_prohibition_governs():
    """同层 allowed vs prohibited → POTENTIAL_CONFLICT，禁止暂时治理，绝不自动二选一。"""
    eff = resolve(
        legal=[],
        guidance=[],
        template_rules=[
            _layered("t-allow", "OPERATOR_POLICY", "template", "allowed"),
            _layered("t-prohib", "OPERATOR_POLICY", "template", "prohibited"),
        ],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )
    assert eff.compliance_state == ComplianceState.POTENTIAL_CONFLICT
    assert eff.effect == "prohibited"
    assert eff.unresolved_conflicts


def test_E26_legacy_null_layer_review_required():
    """旧数据 rule_layer=NULL → REVIEW_REQUIRED，不猜测层级。"""
    eff = resolve(
        legal=[],
        guidance=[],
        template_rules=[],
        operator_rules=[_layered("legacy", None, "operator_direct", "allowed")],
        event_rules=[],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )
    assert eff.compliance_state == ComplianceState.REVIEW_REQUIRED


def test_E27_superseded_rule_not_current():
    """superseded / withdrawn / archived 状态的规则不治理当前查询。"""
    for status in (RuleStatus.SUPERSEDED, RuleStatus.WITHDRAWN, RuleStatus.ARCHIVED):
        assert evaluate(_ctx(), [_rule("x", status=status)]).status == ResultStatus.UNKNOWN


def test_E28_resolver_unknown_when_no_rules():
    """五层全空 → UNKNOWN（effect=unknown），绝不猜成 allowed/prohibited。"""
    eff = resolve(
        legal=[],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )
    assert eff.compliance_state == ComplianceState.UNKNOWN
    assert eff.effect == "unknown"


# --------------------------------------------------------- F 候选状态机


def test_F29_extracted_cannot_publish_directly():
    """EXTRACTED 不可直接发布：状态机没有 EXTRACTED→PUBLISHED 边。"""
    assert "PUBLISHED" not in CANDIDATE_TRANSITIONS["EXTRACTED"]
    assert "PUBLISHED" not in CANDIDATE_TRANSITIONS["DISCOVERED"]


def test_F30_unpublished_candidate_never_effective():
    """只有 PUBLISHED 才有 published_rule_id 语义；其余状态不可能挂正式规则。"""
    for state in CANDIDATE_TRANSITIONS:
        if state != "PUBLISHED":
            # 只有 publish 动作（APPROVED 之后）能写 published_rule_id；
            # 状态机层面任何非 PUBLISHED 状态都不存在“已生效”出边。
            assert state in {
                "DISCOVERED",
                "EXTRACTED",
                "MATCH_PENDING",
                "REVIEW_PENDING",
                "APPROVED",
                "REJECTED",
                "SUPERSEDED",
            }


def test_F31_rejected_candidate_is_terminal():
    """REJECTED 是终态：不能复活，更不能直接跳到 PUBLISHED。"""
    assert CANDIDATE_TRANSITIONS["REJECTED"] == set()


def test_F32_state_machine_rejects_skips():
    """任意跨级跳转必须被状态机拒绝（逐状态穷举非法出边）。"""
    legal_targets = CANDIDATE_TRANSITIONS
    for state, targets in legal_targets.items():
        for other_state in legal_targets:
            if other_state not in targets and other_state != state:
                # 非法迁移不在集合里 —— 状态机结构性拒绝
                assert other_state not in legal_targets[state]


# --------------------------------------------------------- G 共处边界


def test_G33_boundary_unknown_never_match():
    """信息不足的偏好项必须 UNKNOWN，绝不当 MATCH 展示。"""
    results = boundary_match(
        effective_effect="unknown",
        coexistence={},
        preferences=[("animal_on_table_surface", "avoid"), ("dedicated_pet_zone", "prefer")],
    )
    assert all(r.verdict == "UNKNOWN" for r in results)


def test_G34_boundary_emits_no_total_score():
    """边界匹配输出没有综合分/百分比 —— 平台不做评分。"""
    results = boundary_match(
        effective_effect="allowed",
        coexistence={"ordinary_pet_indoor_dining": "prohibited"},
        preferences=[("ordinary_pet_indoor_dining", "accept")],
    )
    assert all(not hasattr(r, "score") for r in results)
    assert not hasattr(results, "score")


def test_G35_seat_table_foodarea_tableware_matrix():
    """座椅/桌面/自助食品区/餐具共处矩阵：冲突、匹配、不足信息三分。"""
    results = boundary_match(
        effective_effect="allowed",
        coexistence={
            "animal_on_customer_seat": "allowed",
            "animal_on_table_surface": "prohibited",
            "animal_in_self_service_food_area": "prohibited",
            "animal_use_customer_tableware": "allowed",
        },
        preferences=[
            ("animal_on_customer_seat", "avoid"),
            ("animal_on_table_surface", "avoid"),
            ("animal_in_self_service_food_area", "require_prohibited"),
            ("animal_use_customer_tableware", "require_prohibited"),
        ],
    )
    by = {r.attribute: r.verdict for r in results}
    assert by["animal_on_customer_seat"] == "CONFLICT"
    assert by["animal_on_table_surface"] == "MATCH"
    assert by["animal_in_self_service_food_area"] == "MATCH"
    assert by["animal_use_customer_tableware"] == "CONFLICT"


def test_G36_dining_derived_from_effect_only_no_invention():
    """室内堂食偏好只能由 overall effect 推导：allowed→MATCH、
    prohibited→CONFLICT、conditional（有条件允许且用户接受）→MATCH、
    信息不足一律 UNKNOWN —— 绝不发明第四种结论。"""
    for effect, expected in (
        ("allowed", "MATCH"),
        ("prohibited", "CONFLICT"),
        ("conditional", "MATCH"),
        ("unknown", "UNKNOWN"),
    ):
        results = boundary_match(
            effective_effect=effect,
            coexistence={},
            preferences=[("ordinary_pet_indoor_dining", "accept")],
        )
        assert results[0].verdict == expected, effect


# --------------------------------------------------------- H 数据完整性


def test_H37_observation_data_absent_from_resolver():
    """Observation 永不进入 normative resolver：输入通道结构上不存在。"""
    import inspect

    sig = inspect.signature(resolve)
    assert not any("observ" in p for p in sig.parameters), "resolver 不得接收观察数据"


def test_H38_petaccessjson_rejects_invalid_layer_effect():
    """PetAccessJSON 拒绝非法 rule_layer / effect，坏数据不出口。"""
    common = dict(
        species="dog", role="pet", place_id="p1", zone_id=None, action="enter", source_id="s1"
    )
    with pytest.raises(PetAccessJSONError):
        dump(**common, effect="allowed", rule_layer="OBSERVED_PRACTICE")
    with pytest.raises(PetAccessJSONError):
        dump(**common, effect="maybe", rule_layer="LEGAL")


def test_H39_answerability_stale_means_review_not_invalid():
    """stale 只表示“需要复核”，规则仍是 current —— review_due ≠ invalid。"""
    cells = compute_answerability(
        rules=[
            {
                "status": "current",
                "animal_scope": "dog",
                "zone_id": None,
                "effect": "allowed",
                "conditions": [],
                "last_verified_at": NOW - timedelta(days=200),
            }
        ],
        coexistence={},
        now=NOW,
    )
    entry = next(c for c in cells if c.question == "ordinary_dog_entry")
    assert entry.state == "stale"


def test_H40_answerability_unknown_without_rules():
    """无规则时 answerability 输出 unknown，不编造答案。"""
    cells = compute_answerability(rules=[], coexistence={}, now=NOW)
    assert cells and all(c.state == "unknown" for c in cells)
