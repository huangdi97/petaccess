# ADR-031 · LEGACY_EXCEPTION_MIGRATION_PLAN（只出计划，未执行）

生成时间：2026-09-18
轮次：`ADR030_HOLDER_SCOPE_AND_SERVICE_ROLE_SEMANTICS_CLOSURE_R1`
状态：**PLAN ONLY — 未经授权不迁移，不删除，不原地篡改**

---

## 1. 审计结果（只读，来自生产库）

```
EXISTING_LEGAL_GUIDE_EXCEPTIONS = 5
WITH_CORRECT_HOLDER_SCOPE       = 5
MISSING_HOLDER_SCOPE            = 0
```

5 条已发布的 LEGAL 导盲犬例外，全部携带正确的 `holder_scope = person_with_disability`，
`subject_scope_normalized = guide_dog`，`normalization_type = exact`：

| # | rule_exception id | 场所 | source_scope_exact | source_id 前缀 |
|---|---|---|---|---|
| 1 | `39cbdef1-179d-441a-8001-6122ca18bce8` | 上海博物馆东馆 | 导盲犬 | `a11aff10` |
| 2 | `a9b5e259-d61a-4813-92b1-a18eebbf52a5` | 上海图书馆东馆 | 导盲犬 | `f20bdb2c` |
| 3 | `64262b3b-d97f-4501-a059-c502deb75e9d` | 兴业太古汇 | 导盲犬 | `a11aff10` |
| 4 | `db5299e2-ecde-48ca-a7ef-e323b48a13e0` | 和平饭店（费尔蒙） | 导盲犬 | `f20bdb2c` |
| 5 | `bb0a8321-75bf-4ae9-b00b-35564a0e2706` | 星巴克臻选上海烘焙工坊 | 导盲犬 | `f20bdb2c` |

结论：**没有一条需要补 holder 条件**（`MISSING_HOLDER_SCOPE = 0`）。上一轮报告的
"holder 缺口"是 *resolver 不读* 这个字段，不是 *行里没写*。修复点在运行时，不在数据。

---

## 2. 这 5 条与 JPROV-001 的关系

它们与 `JPROV-001` 说的是**同一句法条但书**（《上海市养犬管理条例》第二十三条
「盲人携带导盲犬的，不受本条规定的限制。」）：

- JPROV-001：按**法律文件同一性**绑定（`instrument_source_ids = [f20bdb2c, a11aff10]`），一次声明，覆盖所有同一法条的 LEGAL 禁犬基底；
- 5 条历史行：ADR-030 之前按 `rule_id` 逐场所复制的同一内容。

因此存在**同一规范内容的两处表示**。这不是错误（历史行是当时唯一可行的建模），
但 canonical source of truth 应当收敛到 JPROV-001。

---

## 3. 当前是否已重复生效？（§17 的实测答案）

**没有。** `scripts/adr030_holder_scope_probe.py` 在 `full` 模式（场所级例外 + JPROV-001）
下实测：

```
DOUBLE_APPLIED_EXCEPTION = 0
```

机制：resolver 对同一 base 只保留**一个**生效例外（`applied_exceptions` 长度恒为 1），
第二条以 `duplicate_exceptions` 记录为 provenance，逻辑效果只计算一次。

---

## 4. 迁移策略（待授权）

原则：**保留历史，不 DELETE，不原地篡改；退出 current 走正式语义。**

### 阶段 A（本轮已完成，零数据变更）
- 确立 JPROV-001 为辖区级 canonical source of truth；
- resolver 保证"效果唯一、provenance 可追溯"。

### 阶段 B（需新 revision + 新人工审查，尚未做）
1. 为 5 条历史行各生成一条 `superseded` 语义记录：
   `superseded_by = JPROV-001`，`reason = ADR030_CANONICAL_PROVISO`，
   `reviewer` / `decided_at` 由人类填写。
2. 不删行、不改 `source_id`、不改 `holder_scope`、不改 `rule_id` 绑定。
3. 迁移前必须复跑本轮探针，确认 `full` 与 `no_place_exception` 两模式答案不变。

### 阶段 C（迁移后的验证，尚未做）
- `DOUBLE_APPLIED_EXCEPTION = 0` 仍成立；
- 5 个场所的 `guide_dog + matching holder` 仍 `allowed`、且 `applied_exceptions = ['JPROV-001']`；
- 生产指纹除治理区外不变。

### 明确不做
- 不用 UPDATE 直接把历史行改成 `status='withdrawn'`（绕过 supersession 语义 = 抹掉历史）；
- 不为了让数字好看而删除任何行；
- 不因 JPROV-001 存在就阻止未来新增场所级例外（OPERATOR_POLICY 例外是另一层，§14）。

---

## 5. 为什么"缺失 holder_scope = 0"仍不能跳过 B/C

`WITH_CORRECT_HOLDER_SCOPE = 5` 说明**数据是对的**，但历史行的规范内容仍与
JPROV-001 重复。两条路都能得出正确答案时，读者（和未来的 reviewer）无法判断
哪条是权威。收敛到一处是治理问题，不是正确性问题。

---

## 6. 触发条件

本计划**不自动执行**。只有在人类明确授权"执行 ADR-031 legacy 迁移"时才进入阶段 B，
且必须与一次新的人工审查（新 revision）绑定。
