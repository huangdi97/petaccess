# DISNEY_SCOPE_EXCEPTION_SEMANTIC_ISSUE

**STATUS = OPEN**（本轮不修复）

> **2026-09-17 更新**：本缺陷已被确认为一个**缺陷族**（费尔蒙、上图各有一条同形状的
> 不可达 carve-out，另有 2 条 HOLD）。家族级的清单、方案与关闭条件统一收录在
> **`OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL.md`**；本文件保留为**迪士尼实例**的原始记录。
> 另：本文 §5 提到的 `R2_FINAL_R3_BATCH_01A` 现已被升级后的闸门**拒绝**（2 条惰性 carve-out），
> 首批正式候选为 `R2_FINAL_R3_BATCH_01B.json`（8 条）。详见 `FIRST_REAL_PUBLISH_BATCH_01B_CLOSURE.md`。

- `SIGNED_REVISION = R2-FINAL-R3`
- `HUMAN_REVIEWER = huangdi97`
- 受影响候选：`dl-pet-ban`（base）、`dl-sd-op`（RuleException）
- 人类决定：**保持 `APPROVED`**，仅 `NOT_SELECTED_FOR_BATCH_01A`。
  不改为 HOLD、不改为 REJECTED、不重新签署、不重写 Evidence、不修改 RuleException binding。
- 记录日期：2026-09-17

---

## 1. 现象

在 `R2-FINAL-R3-BATCH-01` 的 rehearsal（12 条，含迪士尼两条）中：

| 查询 | 期望 | 实际（domain resolver） | verdict |
| --- | --- | --- | --- |
| disney / ordinary_pet | prohibited | `prohibited` | PASS |
| disney / guide_dog | exception-applied | `unknown`，`applied_exceptions=[]` | **FAIL** |

解析步骤原文：`"no in-scope rules in any layer"`。

同一时刻另一条引擎路径 `/rules/evaluate`：

| 查询 | resolver | `/rules/evaluate` | 结论 |
| --- | --- | --- | --- |
| disney / service_role=none | `prohibited` | `RESTRICTED`（`explicit_prohibition`） | 一致 |
| disney / service_role=working | `unknown` | `MATCH`（`conditional_conditions_met`） | **不一致** |

证据：`artifacts/publish_rehearsal_r3_verification.json`
（`RESOLVER_POST_PUBLISH = FAIL`、`ENGINE_CONSISTENCY = FAIL`，mismatch 与 disagreement 均只有迪士尼一条）。

---

## 2. 数据事实（source-faithful）

| rule_id | 层 | `animal_scope` | `subject_scope_normalized` | `source_scope_exact` | `normalization_type` |
| --- | --- | --- | --- | --- | --- |
| `dl-pet-ban` | OPERATOR_POLICY | `ordinary_pet` | `ordinary_pet` | `ordinary_pet` | `exact` |
| `dl-sd-op` | OPERATOR_POLICY | `service_dog` | `guide_dog` | `导盲犬` | `exact` |

两者 `normalization_type = exact`，即**都是对来源原文的直接记录，不是推断**。问题不在数据录入。

---

## 3. 矛盾所在

`services/api/app/rulespec/animal_scope.py`（ADR-025）：

```python
ORDINARY_PET_SUBJECTS: frozenset[str] = frozenset(
    {AnimalRole.ORDINARY_DOG.value, ORDINARY_CAT, OTHER_PET}
)
```

语义作用域 `ordinary_pet` **依法只覆盖** `{ordinary_dog, ordinary_cat, other_pet}`，
明确不含 `guide_dog` / `hearing_dog` / `assistance_dog` / `other_service_dog`。
这是 ADR-025 的核心不变式：

```
ONTOLOGY_PARENT_RELATIONSHIP MUST_NOT IMPLY_LEGAL_SCOPE_EXPANSION
```

domain resolver 的规则：**只有 base 对当前查询 subject 成立时，才应用其 RuleException。**

于是：

1. `dl-pet-ban`（`ordinary_pet`）对 `guide_dog` 查询**不成立**；
2. 因此挂在它上面的 `dl-sd-op`（`guide_dog`）**永远不会被应用**；
3. `guide_dog` 查询在迪士尼得到 `UNKNOWN`——不是 `ALLOWED`，也不是带例外的 `PROHIBITED`。

换句话说：`dl-sd-op` 作为"carve-out"在语义上不成立。
如果来源原文里的「宠物」本就不含导盲犬，那么「导盲犬除外」并不是从宠物禁令中**挖出**的一块，
而是一条**独立的、平行的允许**。

同时第二条引擎路径使用了较粗的 `service_dog` 作用域做匹配，对同一问题给出 `MATCH`，
与 resolver 的 `UNKNOWN` 直接冲突——这是**引擎语义不一致**，不是发布脚本的错误。

---

## 4. 它是什么，不是什么

**是：**

- ENGINE SEMANTIC INCONSISTENCY（两条 evaluate 路径对同一问题给出不同答案）
- RuleException 建模与本体作用域之间的语义不匹配

**不是：**

- 发布脚本错误
- Human Signature 错误
- RuleException ordering 错误
- Evidence 缺失

---

## 5. 为什么本批移除、而不是修 Resolver

人类决策：**方案 B——不在第一次真实发布前修改 Resolver / domain semantics 来强行让测试通过。**

本轮明确禁止：

1. 让 `ordinary_pet` 包含 `guide_dog`；
2. 让任何 `RuleException` 无条件跳过 base 的适用性判断；
3. 把粗粒度 `service_dog` scope 当作 source-faithful 的 `guide_dog`。

三者都会**扩大规范作用域**——即让一条规则对人/动物产生原文没有说过的法律效力。
这与 ADR-025 的方向相反，且属于语义变更，需要 source review + domain review + 新测试 + 人类重审 + rehearsal，
不得在发布窗口内"顺手"完成。

`R2_FINAL_R3_BATCH_01.json` 保留为 rehearsal 历史证据，**不覆盖**。
首批正式候选为 `docs/governance/publish_batches/R2_FINAL_R3_BATCH_01A.json`（10 条，迪士尼 0 条）。

---

## 6. 同一缺陷族：本批内还有两条（重要）

新增的可达性度量（`verify_publish_r3.py` 的 `CARVE_OUT_REACHABILITY`）证明：
**这不是迪士尼独有的问题**，而是「宠物禁止，导盲犬除外」这一写法的通病。

`artifacts/batch01a/publish_rehearsal_r3_verification.json`：

| carve-out | base | base scope | carve-out scope | base 是否覆盖该 subject |
| --- | --- | --- | --- | --- |
| `fp-sd-legal` | `fp-legal-dog` | `dog` | `guide_dog` | ✅ 是 |
| `fp-sd-op-firstparty` | `fp-pets-op-firstparty` | `ordinary_pet` | `guide_dog` | ❌ **否（永不生效）** |
| `lib-sd-legal` | `lib-legal-dog` | `dog` | `guide_dog` | ✅ 是 |
| `lib-sd-op-guide` | `lib-pets-op` | `ordinary_pet` | `guide_dog` | ❌ **否（永不生效）** |
| `sb-sd-legal` | `sb-legal-dog` | `dog` | `guide_dog` | ✅ 是 |

即：**Batch 01A 的 5 条例外中，2 条在语义上不可达。**

与迪士尼的区别，也是它不构成用户可见错误的原因：

- 迪士尼只有 OPERATOR_POLICY 一层（`dl-legal-dog` / `dl-sd-legal` 均为 HOLD），
  所以 carve-out 不可达 ⇒ 答案是 `UNKNOWN`（错误的用户状态）。
- 费尔蒙 / 上图同时发布了 LEGAL 层（`dog` → prohibited，`guide_dog` → allowed），
  LEGAL carve-out 可达并给出了正确答案 `allowed`。
  运营层那条例外虽然不可达，但**当前不影响用户拿到的答案**。

因此：

- `RESOLVER_POST_PUBLISH`（用户可见答案）在 Batch 01A 全部 PASS；
- 但任务书 §7 中「FAIRMONT：guide_dog operator policy → operator exception correct」
  与「LIBRARY：allowed through valid same-layer exceptions」这两条断言，**严格说并未达成**——
  生效的是 LEGAL 层例外，不是运营层例外。
- `CARVE_OUT_REACHABILITY = PASS_WITH_LIMITATIONS`（2 条不可达），已在报告中显式记录，不掩盖。

同样的形状还出现在两条 HOLD 上：`lib-sd-op-police` / `lib-sd-op-military`
（均绑定 `lib-pets-op`，`ordinary_pet`）。它们目前是 HOLD，不进入发布，
但任何后续方案都必须一并解决，否则会出现"改了一半"的本体。

---

## 7. 后续可行模型（本轮不决定）

### OPTION 1 — 重新审视 base 的 subject scope

若运营方原文中的「宠物」语义**实际上覆盖所有动物**（含导盲犬），
则 base 的 scope 应比 `ordinary_pet` 更宽（例如 `dog` 或 `all_animals`）。

- 依据：**必须以 source wording 为准**，不得由本体推断。
- 需要：source review（`source_scope_exact` 与原文逐字比对）→ 变更候选 scope
  → 人类重审 → 新测试 → rehearsal。
- 风险：扩宽 base 会让更多 subject 落入禁令，必须与例外同时验证。

### OPTION 2 — 不再建模为 RuleException

若 `ordinary_pet` 明确定义为不含 service/guide dog，
则 `dl-sd-op` 就不应是一条 carve-out，而应作为**独立的 source-faithful allowance**（一条自己的 AccessRule）。

- 依据：ADR-025 的不变式本身。
- 需要：domain review 决定"独立 allowed 规则"在分层模型里的位置与优先级；
  目前 LEGAL 层的 `dog` base + `guide_dog` exception 已是这种形状（base scope = `dog`），
  说明该形状在本体里是**可行且已验证**的。
- 影响：3 条已批准例外（`dl-sd-op` / `fp-sd-op-firstparty` / `lib-sd-op-guide`）
  与 2 条 HOLD 都需要重新建模与重审。

### OPTION 3 — 引入新的 exact source category

若现有本体缺少一个"来源原文就是这样写的"精确类别，提出 ADR。

- 需要：ADR → 本体变更 → 迁移全部受影响行 → 人类重审 → rehearsal。
- 这是最重的一条路，只有在 OPTION 1/2 都被 source review 否掉后才走。

### 附带必修项（与 OPTION 无关）

`/rules/evaluate` 使用粗粒度 `service_dog` 作用域，与 domain resolver 不一致。
无论采用哪个 OPTION，**两条引擎路径必须对同一问题给出同一答案**，
否则"引擎不一致"会一直是一个悬空的正确性风险。

---

## 8. 关闭条件

本 issue 只有在以下全部完成后才能关闭：

1. source review 确定原文语义（OPTION 1 / 2 / 3 之一被采纳）；
2. domain review + 必要的 ADR；
3. 新增/更新测试覆盖受影响行；
4. 语义变更经过 **Human re-review**（huangdi97 或继任评审员重新签署）；
5. 在 rehearsal 库上重跑：resolver 矩阵 + 引擎一致性 + 新增的 carve-out 可达性度量；
6. `CARVE_OUT_REACHABILITY = PASS`（不可达数 = 0）。

---

## 9. 证据索引

| 文件 | 内容 |
| --- | --- |
| `docs/governance/publish_batches/R2_FINAL_R3_BATCH_01.json` | 12 条原始批次（含迪士尼），保留为历史 |
| `docs/governance/publish_batches/R2_FINAL_R3_BATCH_01A.json` | 10 条正式首批候选（迪士尼 0 条） |
| `artifacts/publish_rehearsal_r3_verification.json` | BATCH-01 rehearsal：迪士尼 mismatch 与引擎 disagreement 原文 |
| `artifacts/batch01a/publish_rehearsal_r3_verification.json` | BATCH-01A rehearsal：可达性度量与全部门禁 |
| `artifacts/batch01a_dryrun.json` | BATCH-01A dry-run：真实 publish gate 10/10 PASS |
| `services/api/app/rulespec/animal_scope.py` | `ORDINARY_PET_SUBJECTS` 定义与 ADR-025 不变式 |
