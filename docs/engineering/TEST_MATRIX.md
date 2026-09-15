# Test Matrix

> 规范 §8–§31 的落点。每个不变量都能指到具体文件或具体断言，而不是「大概覆盖了」。

## 1. 分布（本轮实测）

| 目录 | 用例数 | 说明 |
|---|---|---|
| `tests/unit` | 387 | 纯函数 / 领域不变量 / 属性测试 |
| `tests/integration` | 77 | 真实 Postgres + FastAPI TestClient |
| `tests/contract` | ~20 | Provider / AI guard / schema 契约（无网络，`MockTransport`） |
| `services/api/tests` | ~17 | evaluator |
| **合计** | **501** | |

**本轮实测全量结果（2026-09-15 复跑）**

```text
$ pytest -q --durations=20
501 passed, 1 warning in 54.80s
PYTEST_EXIT=0
```

前置条件：Postgres+PostGIS up、Redis up、**Celery worker 已启动**
（`celery -A app.worker.celery_app:celery_app worker --pool=solo`）。
缺 worker 时 `test_media.py` / `test_v05_e2e.py` 的 4 个用例会一直等到超时才失败
——这是 fail-closed 的正确行为，不是代码缺陷，但它曾让全量跑看起来像"卡死"。
现已把 `timeout = 120 / timeout_method = "thread"` 写进 `pyproject.toml`
（`pytest-timeout` 已加入 dev 依赖），最慢的健康用例是 13.3s（Hypothesis），
留 9 倍余量。

最慢 5 个用例（用于判断"慢"是否异常）：

| 耗时 | 用例 |
|---|---|
| 13.33s | `test_property_invariants.py::test_mandatory_level_normalisation_is_idempotent`（Hypothesis 首次写 example DB） |
| 6.76s | `test_quality_baseline.py::test_check_monitor_failed_path_increments...`（含真实重试退避） |
| 2.20s | `test_quality_baseline.py::test_fetch_network_error_is_wrapped` |
| 1.52s | `test_operator_contribution.py::test_operator_claim_full_loop` |
| 1.07s | `test_operator_contribution.py::test_contribution_rate_limit` |

## 2. 本轮新增的测试文件

| 文件 | 覆盖 | 用例 |
|---|---|---|
| `tests/unit/test_domain_invariants.py` | §8 Animal Scope、§9 RuleLayer、§11 UNKNOWN | 27 |
| `tests/unit/test_temporal_invariants.py` | §27 时区与有效期边界 | 13 |
| `tests/integration/test_versioning_supersession.py` | §14 版本化 / 取代 | 5 |
| `tests/integration/test_publish_atomicity.py` | §16 事务原子性 | 4 |
| `tests/unit/test_idempotency_keys.py` | §17 幂等键 | 6 |
| `tests/unit/test_property_invariants.py` | §24 属性测试（Hypothesis） | 6 |
| `tests/unit/test_governance_baseline.py` | §13 / §78 治理基线保护 | 10 |
| `tests/unit/test_config_validation.py` | §75 启动配置校验 | 6 |

## 3. 不变量 → 断言

### §8 Animal Scope

- `test_guide_dog_proviso_governs_guide_dogs_only` —— 导盲犬但书只覆盖 `guide_dog`
- `test_guide_dog_exception_is_not_the_hearing_dog_exception` / `..._assistance_dog_...`
- `test_police_and_military_dogs_are_never_service_dogs`
- `test_compound_term_军警犬_splits_into_exactly_police_and_military`（超集/子集都被拒）
- `test_compound_split_members_do_not_widen_to_other_working_dogs`
- `test_ontology_parent_never_expands_the_normative_effect`
- `test_source_scope_exact_cannot_be_silently_replaced_by_a_parent_scope`
- `test_publish_refuses_the_unproven_service_dog_widening`

### §9 RuleLayer

- `test_legal_mandatory_prohibition_is_the_floor`
- `test_operator_policy_cannot_override_a_legal_prohibition_for_guide_dogs_either`
- `test_same_layer_carve_out_replaces_its_own_base_rule`
- `test_exception_derived_rule_inherits_the_base_rule_layer`（解释为何绑定必须层内）
- `test_temporary_policy_shadows_operator_policy_while_active` / `..._expired_...`
- `test_same_layer_conflict_is_recorded_not_silently_answered`

### §11 UNKNOWN

- `test_no_governing_rule_is_unknown_and_never_allowed` / `test_unknown_is_not_prohibited`
- `test_a_rule_whose_scope_is_not_a_legal_equivalent_yields_unknown`
- `test_withdrawn_exception_does_not_restore_an_allowance`
- `test_expired_exception_window_falls_back_to_the_base_rule`
- `test_exception_without_source_never_applies`
- `test_only_current_exceptions_apply`（参数化 4 种非 current 状态）

### §10 RuleException

`tests/unit/test_rule_exception_binding.py`（25 例）+ `test_rule_exceptions.py`：
层内绑定、禁止跨层/跨场所/跨 zone/自绑定、HOLD/REJECT 基类无可执行例外、
来源与层与强制级与 scope 保留、`dl-sd-op→dl-pet-ban` 等具体配对。

### §12 / §13 证据与人工评审

- `publish_gate.py` 的顺序化 fail-closed 检查有 `test_publish_*` 系列覆盖
- `test_governance_baseline.py`：37 行 / 23-9-5 / 签署字段全空 / 跨层 0 /
  HOLD 基类无可执行例外 / dry-run 把 HOLD 全部挂起 / 快照比对
- `test_publish_preflight_crosscheck.py`：未签署登记表不得发布、HOLD 不交叉校验、
  `APPROVED_WITH_NOTE` 当作批准而非拒绝

### §14 / §15 版本化与回滚

- `test_versioning_supersession.py`：V1→V2 取代、旧版本不覆写、自取代被 DB 拒绝、
  两个 current 可检测、被取代规则不参与求解
- `tests/integration/test_rollback_l1.py`（既有）：撤回回落 UNKNOWN 而非 allowed、
  行与证据保留、审计留痕、权限、404

### §16 / §17 原子性与幂等

- `test_publish_atomicity.py`：分两次写会留下半发布状态（用 savepoint 演示，不污染库）、
  单事务回滚不留痕、成功事务两条都在、孤儿例外无法提交
- `test_idempotency_keys.py`：键派生确定、scope 不冲突、空键不是键、Redis 不可达不抛出

### §24 属性测试（Hypothesis）

`test_property_invariants.py`：
- 输入顺序置换 → 结果不变（`test_resolution_is_independent_of_input_ordering`）
- 同一例外应用两次 → 幂等
- `normalize_mandatory_level` 幂等
- `PetAccessJSON` dump/load 往返字段一致
- 未知版本被拒、LEGAL 未声明强制级被拒

### §27 时间

- 119 个持久化 datetime 列全部 tz-aware（机器校验，含「扫描确实看到了表」的自检）
- naive/aware 混用必须抛 `TypeError` 而不是静默比较
- `effective_from` / `effective_to` 边界含端点、±1 微秒
- Asia/Shanghai 午夜与 UTC 的同一瞬间；America/New_York DST 前后偏移变化

### §29 变异测试（脚本，非 pytest）

`scripts/mutation_probe.py` —— 4 个变异全部被捕获：

| 变异 | 保护 |
|---|---|
| `legal_floor_removed` | `test_domain_invariants.py` + `test_v05_resolver.py` |
| `unknown_becomes_allowed` | 同上 |
| `hold_becomes_publishable` | `test_governance_baseline.py` |
| `cross_layer_binding_allowed` | 生成器 `validate_exception_binding()` 直接拒绝写出 |

运行方式：`.venv/Scripts/python.exe scripts/mutation_probe.py`（退出码非 0 表示有不变量没被真正测到）。
**它会在 `finally` 里按字节还原源码。**

## 4. 已知缺口

| # | 缺口 | 状态 |
|---|---|---|
| 1 | 并发测试（§26） | 未实现——需要真实并发事务夹具（`FOR UPDATE` / 双 session），本轮未加 |
| 2 | 可视化回归（§63） | 未实现，见 `docs/frontend/VISUAL_REGRESSION_MATRIX.md` |
| 3 | 端到端 Admin E2E | 无 |
| 4 | 依赖 worker 的用例在 worker 缺失时超时很久（分钟级） | 已收敛：加 `pytest-timeout`（120s/thread）后失败快速且带堆栈；仍未加 skip（保持 fail-closed）。启动方式写入 `docs/engineering/LOCAL_DEV_WINDOWS.md` |
| 5 | 开发库已被历史测试累积到 850 place / 750 rule | P2 卫生问题；本轮已清理自己产生的 45 place + 45 source，并把新夹具改为 `flush()` 随事务回滚 |
