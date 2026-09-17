# OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL

**STATUS = OPEN**（本轮**不决定** OPTION 1 / 2 / 3）

- `SIGNED_REVISION = R2-FINAL-R3`
- `HUMAN_REVIEWER = huangdi97`
- 记录日期：2026-09-17
- 影响面：6 条候选（4 条已批准 + 2 条 HOLD），跨 3 个场所
- 处理方式：`DEFERRED_APPROVED_SEMANTIC_REMODEL`
  —— **不是 HOLD，不是 REJECTED，不改签署登记表**
- 相关文档：`DISNEY_SCOPE_EXCEPTION_SEMANTIC_ISSUE.md`（同一缺陷的迪士尼实例，本文件是它的超集）

---

## 1. 一句话

「宠物禁止，导盲犬除外」这种运营写法，被我们建模成了
`ordinary_pet` 的 base + `guide_dog` 的 `RuleException`。
但在 ADR-025 下 `ordinary_pet` 依法**不覆盖** `guide_dog`，
所以那条 carve-out **永远不会被应用**——它发布后就是一条惰性规则。

**本轮的立场：不接受"最终用户答案目前正确"作为发布不可达 `RuleException` 的理由。**
答案正确是由另一条独立的 LEGAL 层规则给出的，它不是"这条 carve-out 生效了"的证据。

---

## 2. 受影响规则（全部 6 条）

| rule_id | 角色 | 层 | base | base scope | 自己 scope | 状态 | 可达性 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `dl-sd-op` | carve-out | OPERATOR_POLICY | `dl-pet-ban` | `ordinary_pet` | `guide_dog` | APPROVED | ❌ 不可达 |
| `fp-sd-op-firstparty` | carve-out | OPERATOR_POLICY | `fp-pets-op-firstparty` | `ordinary_pet` | `guide_dog` | APPROVED | ❌ 不可达 |
| `lib-sd-op-guide` | carve-out | OPERATOR_POLICY | `lib-pets-op` | `ordinary_pet` | `guide_dog` | APPROVED | ❌ 不可达 |
| `lib-sd-op-police` | carve-out | OPERATOR_POLICY | `lib-pets-op` | `ordinary_pet` | `police_dog` | **HOLD** | ❌ 不可达 |
| `lib-sd-op-military` | carve-out | OPERATOR_POLICY | `lib-pets-op` | `ordinary_pet` | `military_working_dog` | **HOLD** | ❌ 不可达 |
| `dl-pet-ban` | base | OPERATOR_POLICY | — | `ordinary_pet` | `ordinary_pet` | APPROVED | （其唯一 carve-out 不可达） |

可达性由 `scripts/publish_batch.py::carve_out_reachability` **实测**得出，
它复用 `services/api/app/rulespec/animal_scope.py::rule_governs`（ADR-025 唯一权威），
不复制第二套作用域算法。

对照（同批中可达的 3 条，说明该判定不是"什么都不通过"）：

| carve-out | base | base scope | 可达 |
| --- | --- | --- | --- |
| `fp-sd-legal` | `fp-legal-dog` | `dog` | ✅ |
| `lib-sd-legal` | `lib-legal-dog` | `dog` | ✅ |
| `sb-sd-legal` | `sb-legal-dog` | `dog` | ✅ |

---

## 3. 为什么不可达（机制）

```python
ORDINARY_PET_SUBJECTS = {ordinary_dog, ordinary_cat, other_pet}   # 不含 guide_dog
```

domain resolver 的规则：**只有 base 对当前查询 subject 成立时，才应用其 RuleException。**

于是 `ordinary_pet` base 对 `guide_dog` 查询不成立 ⇒ 挂在它上面的 `guide_dog` 例外永不生效。

这不是录入错误：所有 6 行的 `normalization_type` 都是 `exact`（或对 HOLD 两行是
`compound_term_split`），即**都是对来源原文的直接记录**。问题在**建模形状**，不在数据。

---

## 4. 为什么"答案正确"不能作为放行理由

费尔蒙 / 上图 / 星巴克同时发布了 LEGAL 层：`dog` base（prohibited）+ `guide_dog` exception。
**用户拿到的正确答案来自这一层**，与运营层那条不可达例外无关。

后果：

- 用户可见答案正确 ≠ 运营层 carve-out 生效；
- 那条 carve-out 仍然会被**发布、链接、审计、计数**，并在报表里表现为"已发布的导盲犬例外"；
- 一旦 LEGAL 层以后被撤回或改期，运营层不会接住它——缺口是隐藏的。

一条发布后永不生效的规则比不发布更糟：它占着证据链、占着审计、占着用户的信任，
却不提供任何效力。这正是 `ZERO INERT RULES` 成为一等闸门的原因。

---

## 5. 明确禁止的"捷径"

以下三条都会**扩大规范作用域**（让规则产生来源原文没说过的法律效力），
与 ADR-025 方向相反，一律禁止：

1. **不得**让 `ordinary_pet` 包含 `guide_dog`（或其他 service role）；
2. **不得**让任何 `RuleException` 跳过 base 的适用性判断（无条件生效）；
3. **不得**把粗粒度 `service_dog` 作用域当作 source-faithful 的 `guide_dog`。

也不得为了让批次通过而放宽 `max-approve`、改动 `ExceptionBinding`、或重写 Evidence。

---

## 6. 后续可行模型（本轮**不决定**）

### OPTION 1 — 重新审视 base 的 subject scope

若运营方原文中的「宠物」语义**实际上覆盖所有动物**（含导盲犬），
则 base scope 应比 `ordinary_pet` 更宽（例如 `dog` 或 `all_animals`）。

- 依据必须是 **source wording 逐字比对**，不得由本体推断。
- 需要：source review → 变更候选 scope → 人类重审 → 新测试 → rehearsal。
- 风险：扩宽 base 会让更多 subject 落入禁令，必须与例外同时验证。

### OPTION 2 — 不再建模为 RuleException

若 `ordinary_pet` 明确不含 service/guide dog，则这些不应是 carve-out，
而应是**独立的 source-faithful allowance**（各自一条 AccessRule）。

- 依据：ADR-025 不变式本身。
- 该形状在本体里**已经可行且已验证**：LEGAL 层正是 `dog` base + `guide_dog` exception。
- 影响：3 条已批准 + 2 条 HOLD 都需重新建模与重审。

### OPTION 3 — 引入新的 exact source category

若现有本体缺少"来源原文就是这样写的"精确类别，提 ADR。

- 需要：ADR → 本体变更 → 迁移全部受影响行 → 人类重审 → rehearsal。
- 最重的一条路，只有 OPTION 1/2 都被 source review 否掉后才走。

### 附带必修项（与 OPTION 无关）

`/rules/evaluate` 使用粗粒度 `service_dog` 作用域，与 domain resolver 不一致
（迪士尼实例中：resolver `UNKNOWN` vs `/rules/evaluate` `MATCH`）。
无论采用哪个 OPTION，**两条引擎路径必须对同一问题给出同一答案**。

---

## 7. 本轮已完成的治理改动

1. **闸门升级**：`scripts/publish_batch.py` 的第 4 条拒绝从
   "No prohibition without its approved carve-out"
   升级为
   **"No prohibition without its *REACHABLE* approved carve-out"**。
   - 可达 ⇒ 照旧阻断 base；
   - **不可达 ⇒ 记为 `UNREACHABLE_APPROVED_CARVE_OUT` → `SEMANTIC_REMODEL_REQUIRED`，不阻断 base**；
   - 无法判定 ⇒ 仍阻断（"无法证明其惰性"不等于"惰性"）。
2. **新增第 5 条拒绝：ZERO INERT RULES**。批次**内**不得含不可达 carve-out。
3. **新增一等闸门** `ZERO_INERT_RULES`（`scripts/verify_publish_r3.py`），
   与 `CARVE_OUT_REACHABILITY` 一样**不接受 `PASS_WITH_LIMITATIONS`**。
4. 结果：`R2-FINAL-R3-BATCH-01`（12 条，3 条惰性）与 `R2-FINAL-R3-BATCH-01A`（10 条，2 条惰性）
   **现在都被闸门拒绝**，并已有测试锁定这一事实（防止闸门变软）。
   两个清单作为演练历史保留，不删除、不覆盖。

---

## 8. 关闭条件

本文件只有在以下**全部**完成后才能关闭：

1. source review 确定原文语义，OPTION 1 / 2 / 3 之一被采纳并记录 ADR；
2. 6 条受影响规则（含 2 条 HOLD）按采纳方案重新建模；
3. 人类重新签署（新 revision，不得就地改写 R2-FINAL-R3）；
4. `carve_out_reachability` 对这 6 条全部给出 `reachable`（或它们已不再是 carve-out）；
5. 两条引擎路径对同一问题给出同一答案（迪士尼实例不再分歧）；
6. 新批次 rehearsal 全绿后发布。

在此之前，这 6 条保持 `DEFERRED_APPROVED_SEMANTIC_REMODEL`。
