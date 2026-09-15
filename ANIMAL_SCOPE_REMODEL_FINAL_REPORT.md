# ANIMAL_SCOPE_REMODEL_FINAL_REPORT.md

> 生成时间：2026-09-15（GMT+8）· 基线 HEAD `53c4c03`
> Workstream A（Master Goal §5）收口报告

---

## 0. 结论

```text
ANIMAL_SCOPE_REMODEL_GATE = PASS
```

接管时 A 的真实状态是 **PARTIAL + REGRESSED**（领域代码已实现，但 19 例测试因语义未对齐而红）。
本轮补齐缺失的测试面、修正旧资产、并补上三处**能力缺口**，末态：

```text
uv run pytest -q                        → 349 passed / 0 failed
uv run ruff check …                     → All checks passed!
uv run ruff format --check …            → 139 files already formatted
uv run mypy .                           → no issues in 77 source files
```

---

## 1. 缺陷本质（为什么要做这件事）

`《上海市养犬管理条例》第二十三条` 禁止犬只进入商场，但书为：

> 「盲人携带导盲犬的，不受本条规定的限制。」

但书只提 **导盲犬**。旧模型把它存成 `animal_scope='service_dog'`，理由是
`GUIDE_DOG is-a SERVICE_DOG`。于是存储行声称**所有**服务犬（助听犬、辅助犬……）
都不受法定禁止约束 —— 这是把**本体关系当法律论证**。

新增的不变量（Master Goal §5.1）：

```text
ONTOLOGY_PARENT_RELATIONSHIP
MUST_NOT
IMPLY_LEGAL_SCOPE_EXPANSION
```

---

## 2. 三处能力缺口（接管后发现并补齐）

### 2.1 缺口一：`resolve()` 无法声明精确角色

`animal_scope.py` 设计上允许 `declared_role`（"我的狗是助听犬"），但
`v05_resolver.resolve()` 的签名里没有它，`QuerySubject.declared_role` 永远拿不到值。
后果：**§5.8 的测试 3 / 4（助听犬、辅助犬不得继承导盲犬但书）无法表达** ——
underspecified 的 `service_role="working"` 会把查询扩张到 4 个角色，导盲犬规则仍被匹配到。

**修复（兼容性扩展，不破坏 allow/prohibit API）**：

| 层 | 变更 |
|---|---|
| `v05_resolver.resolve()` | 新增 optional `declared_role: str \| None = None` |
| `_scope_matches()` | threading `declared_role`；`query_subjects()` 优先用它，不做扩张 |
| `LayeredException` | 新增 `source_scope_exact` / `holder_scope`（与 `LayeredRule` 对齐） |
| `POST /places/{id}/effective-rules` | body 接受 `declared_role` |
| `packages/client-core` | `effectiveRules()` 类型 + `ActivePet.declared_role` |

语义：**underspecified 的服务犬查询**仍扩张（"找出可能适用的规则"），
**声明的精确角色**不扩张（"我是助听犬"不得继承导盲犬但书）。

### 2.2 缺口二：`RuleException` 无法写入精确 scope

ADR-025 要求 RuleException 记录 `source_scope_exact` / `subject_scope_normalized` /
`normalization_type` / `normative_effect` / `holder_scope`，但
`RuleExceptionIn` 与创建端点都没有这些字段 ⇒ **无法通过 API 建出正确建模的但书**，
只能建出"未证成的泛化"。

**修复**：`RuleExceptionIn` 新增 5 个带词表校验的字段；端点持久化 + 审计；
`_serialize_rule_exception` 返回。
并对"给了精确 scope 却没给归一化类型"直接 **422 拒绝**（平台不猜测 scope 是否具法律效力）。

### 2.3 缺口三：`policy_template_rule` 没有 scope 列

组织模板也是规则来源，但表里没有 scope 列 ⇒ 一旦 ADR-025 生效，
**模板携带的 service_dog 条目会静默失效**（被 `test_e2e_b` 抓到）。

**修复**：模型 + `TemplateRuleIn` + 创建端点 + `_load_layered_rules` 全链路补列，
新增迁移 `d4a8b2f6c903`（additive、幂等、保守回填）。

---

## 3. 数据面修正（不猜测、不泛化）

### 3.1 迁移 `a2d5e8b91c47` 被"部分应用后打标"（T-01）

实测：

```text
alembic_version = a2d5e8b91c47
access_rule      source_scope_exact: 存在
rule_candidate   source_scope_exact: 存在
rule_exception   source_scope_exact: 缺失   ← UndefinedColumn，一次打红 10 个测试
```

**修复**：新增幂等修复迁移 `c1f7a3e8d502`（沿用 ADR-024 先例；两种库状态均正确）。
实测修复后 `rule_exception` 列齐备（16 列），约束齐备（8 个）。

### 3.2 回填策略（保守，绝不扩张）

| 原 `animal_scope` | `subject_scope_normalized` | `normalization_type` |
|---|---|---|
| `dog` | `dog` | `exact` |
| `ordinary_pet` | `ordinary_pet` | `exact` |
| `service_dog` | **NULL** | **`legal_interpretation_required`** |
| 其他 | 不变 | 不变 |

即：**`service_dog` 恰恰就是那个未经证成的泛化，因此在人工重新建模前不产生任何法律效力。**
实测 `rule_exception` 10 行全部落入 `service_dog / NULL / legal_interpretation_required`；
`normative_effect` 只在 `exact` 时才从 `effect` 派生，避免把待审推断写进规范层。

### 3.3 §5.7 `gh-outdoor-keep`

证据仍只是 `search_snippet`（`解放日报` 报道室内禁令），无法支持
「港汇恒隆 outdoor 普通宠物 conditional allowed」。已在 R2 登记表标记：

```text
proposed_decision = RECOMMEND_REJECT
reject_reason_codes = [INSUFFICIENT_PLACE_ZONE_EVIDENCE, LEGAL_SCOPE_CONFLICT]
```

Source / Evidence / Audit / Reject reason 全部保留；`test_11` 固定该不变量。
未来拿到运营方明确 Zone policy 时**新建 Candidate**，不恢复旧错误 Candidate。

---

## 4. 新增的 Scope 测试面（Master Goal §5.8）

`tests/unit/test_animal_scope.py` —— 19 个确定用例 + 2 个 property（各 300 例）：

| §5.8 | 用例 | 断言要点 |
|---|---|---|
| 1 | `test_01_ordinary_dog_in_mall_is_prohibited` | 普通犬 → prohibited |
| 2 | `test_02_guide_dog_in_mall_gets_the_local_exception` | 导盲犬 → 本地例外生效 |
| 3 | `test_03_hearing_dog_does_not_inherit_...` | 助听犬 → prohibited（不继承） |
| 4 | `test_04_assistance_dog_does_not_inherit_...` | 辅助犬 / 其他服务犬 → prohibited |
| 5 | `test_05*` | 国家无障碍规则匹配 4 个援助角色、不匹配军警犬；`FACILITATION_REQUIRED → conditional`（**不是 allowed**）；holder_scope 限定 |
| 6 | `test_06/06b/06c/06d` | 本体父关系不扩张；仅 same-scope 合法；非 exact 归一化无法律效力；查询侧扩张的作用边界 |
| 7 | `test_07_police_dog_is_not_a_service_dog` | 警犬 ∉ 服务犬；仍是犬 |
| 8 | `test_08/08b` | 军用工作犬 ∉ 服务犬；分类完备且互斥 |
| 9 | `test_09_disney_guide_dog_keeps_the_leash_condition` | 导盲犬 + leash 保留；助听犬无该政策 |
| 10 | `test_10_shanghai_library_precise_scopes` | 导盲犬/警犬/军用工作犬分别表达；未列角色保持禁止 |
| 11 | `test_11/11b` | `gh-outdoor-keep` 被拒且有两条 reason code；**无任何行被 Agent 预签** |
| — | property ×2 | 精确角色 scope 不超出该角色；声明角色不扩张查询 |

同时补齐原有测试面（按 ADR-025 精确建模，非放宽）：

- `tests/unit/test_rule_exceptions.py`：具名 `_precise_exception()`；property 改为独立镜像
  `_expected_legal_scope()`（不 import 生产模块，以便捕捉生产规则漂移）
- `tests/integration/test_rule_exceptions.py`：+3 例（导盲犬不延伸到其他服务角色；
  裸 `service_dog` 不生效；精确 scope 缺归一化类型 → 422）；新增 `_new_place_rule()` 隔离开销
- `tests/unit/test_v05_resolver.py`：+2 例（legacy `service_dog` 不生效；`declared_role` 不继承）
- `tests/fixtures/real_world_regression.json`：13 处 scope 字段按来源忠实补全
  （法规但书 → `guide_dog/exact`；运营方页面 → `service_dog/exact`）
- `tests/unit/test_reality_audit.py` / `tests/integration/test_v05_e2e.py`：按精确 scope 建模

---

## 5. 与旧模型的行为差异（净增能力）

| 场景 | 旧行为 | 新行为 |
|---|---|---|
| 法规写「导盲犬」，查询助听犬 | **allowed**（错误） | **prohibited** |
| 法规写「导盲犬」，查询"服务犬"（未声明） | allowed | allowed（查询侧扩张，且答案可解释） |
| 裸 `service_dog` 规则（无归一化） | 对所有服务犬生效 | **不产生任何效力**，强制人工重新建模 |
| 国家无障碍「提供便利」义务 | 会被写成 `allowed`（义务被抬成许可） | `FACILITATION_REQUIRED` → API 呈现 `conditional` |
| `policy_template_rule` 的 service_dog 条目 | 生效 | **修复后**可携带精确 scope 并生效（补列） |

---

## 6. 未完成 / 已知限制（如实登记）

| 项 | 说明 |
|---|---|
| v1 evaluator（`POST /rules/evaluate`）精确 scope | 仍按 `AnimalScope` 粗粒度匹配，未接 ADR-025 精确角色。resolver（`effective-rules`）是 ADR-025 的权威路径；v1 evaluator 属遗留三值 API。已登记 TECH_DEBT（T-04） |
| Admin 侧 scope 编辑表单 | 后端/交换格式/PetAccessJSON 已支持；Admin 候选详情只读消费。不影响 A Gate |
| 生产数据 | 上述规则仍未 Publish（GOV-01 未签），因此**生产口径仍不含这些修复**；A Gate 只证明建模与门禁正确 |
| 上海图书馆 | 原文同时列导盲犬与军警犬，单行无法忠实表达 ⇒ R2 标 `RECOMMEND_HOLD`（需拆 3 条） |

---

## 7. 证据清单

```text
services/api/app/rulespec/animal_scope.py
services/api/app/rulespec/v05_resolver.py
services/api/app/models/enums.py
services/api/app/api/v1/v05.py
services/api/app/tools/reality_audit.py
services/api/migrations/versions/a2d5e8b91c47_source_faithful_scope_and_normative_effect.py
services/api/migrations/versions/c1f7a3e8d502_repair_rule_exception_scope_columns.py
services/api/migrations/versions/d4a8b2f6c903_template_scope_columns.py
tests/unit/test_animal_scope.py
tests/unit/test_rule_exceptions.py
tests/unit/test_v05_resolver.py
tests/unit/test_real_world_regression.py
tests/integration/test_rule_exceptions.py
tests/integration/test_v05_e2e.py
tests/fixtures/real_world_regression.json
docs/reality_audit/review_decisions_r2.json
```
