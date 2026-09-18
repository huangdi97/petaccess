# SCOPE-REMODEL-R2 — 迪士尼导盲犬 carve-out 救济候选 · 人工审查包

> 待裁决：**1 行**。签署文件 `docs/expansion/review_decisions_scope_remodel_r2_carveout.json`
> （`final_decision` / `reviewer` / `decided_at` / `decision_note` 全为 `null`）。
> 这是**新候选 + 新审查**，不是对旧签名的改写。

## 1. 为什么会有这一行

| | |
|---|---|
| 冻结候选 | `w01-305fa08c1e`（Wave01 已签署 APPROVED，迪士尼导盲犬 carve-out） |
| 它的问题 | `proposed_conditions` 用遗留键 `type`，canonical 发布闸门读不了 → `schema_unsupported`，**永远发布不出去** |
| 为什么不改它 | ADR-029 §9：已签署候选不得原地改写。救济只能是「新候选 + 新人工审查」 |
| 后果 | 迪士尼 dog 禁令（`sr2-7b595de9e0`，huangdi97 已 APPROVED）不能发布——发布了就会带着「已批准但发布不出去」的导盲犬例外上线，解析器会对导盲犬给出 **prohibited**（上一轮在演练库实测到的错误状态，见 `SCOPE_REMODEL_R2_BATCH_01_BLOCKED.json`） |

## 2. 这一行是什么

| 字段 | 值 |
|---|---|
| candidate_id | `69e0916a-2f13-4b1e-b601-f8731e6869d1` |
| rule_id | `sr2-69e0916a2f` |
| 场所 / 区域 | 上海迪士尼乐园 / 全园 |
| 主体 | `service_dog` → `guide_dog`（`normalization_type=exact`） |
| 效果 | `conditional`，`normative_effect=exempt_from_prohibition` |
| 层 / 强制级 | `OPERATOR_POLICY` / `operator_discretion` |
| 来源术语 | 「导盲犬」（`source_type=official_operator_policy`） |
| 持有人 | `person_with_disability` |
| 挂到 base | `sr2-7b595de9e0`（迪士尼 dog 禁令，新基底） |
| 条件 | `leash_required`（须时刻栓有系绳并在主人看管下）；`other_structured_note`（部分游乐项目也可能不允许导盲犬进入） |

**相对冻结候选的唯一改动**：条件键 `type` → `condition_type`，由 canonical ingest 边界
`app.services.condition_ingest.normalize_conditions` 翻译。来源、证据包、scope 三列、层、
效果、持有人范围全部逐字搬运。

## 3. 机器已经实测过的（不是推断）

| 检查 | 结果 |
|---|---|
| 发布器自己的闸门（同一 `DatabaseGate`）· 冻结原候选 | **BLOCKED**（`schema_unsupported`） |
| 发布器自己的闸门 · 新救济候选 | **PASS** |
| 落库条件键 | `canonical=True`、`legacy=False`、`review_status=REVIEW_PENDING` |
| 可达性 `is_reachable_carveout(dog base, guide_dog)` | **True**（不再是惰性例外） |
| 冻结候选是否被改动 | **未改动**（行 sha256 `94cea72f…` 前后一致） |
| 新增行 | `rule_candidate` 74 → 75，其余表 0 |

## 4. 请裁决（四选一）

- **APPROVED** → 与 `sr2-7b595de9e0` 组成同批发布，导盲犬答案由「unknown」变为
  「conditional（满足条件可进入）」，普通犬仍为 prohibited。
- **APPROVED_WITH_NOTE** → 同上，但必须填 `decision_note`。
- **HOLD** → 迪士尼 dog 禁令继续不发布（现状不变，导盲犬仍是 unknown，不会错误禁止）。
- **REJECTED** → 同上，并记录否决理由。

## 5. 签完之后会发生什么（我不会提前做）

1. `scripts/scope_remodel_r2_carveout_publish_register.py --execute` —— 把「迪士尼 dog 基底 +
   新但书」投影进**同一张**可发布登记表（跨文件依赖对批次校验不可见，必须同表）；
2. 生成显式 batch manifest（base 在前、例外在后）；
3. 克隆演练库真执行 + 幂等复跑 + 解析器实测（导盲犬必须 ≠ prohibited）+ 证据/审计验证；
4. 生产 dry-run（零突变）→ 再交给你授权真实发布。

> 冻结候选 `w01-305fa08c1e` 仍是 APPROVED，不在本表内、不受本表影响。
> 本表也**不影响**上海动物园 dog（HOLD，`HIGHER_LEVEL_GUIDE_DOG_LEGAL_APPLICABILITY_UNRESOLVED`）。
