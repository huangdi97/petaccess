# B2 · 过宽来源术语拆分 —— 新 revision 人工审查包

- 生成时间：2026-09-18
- 状态：**待人工审查**（未写入任何候选行、未改任何已签署行）
- 机器可读提案：`docs/expansion/scope_remodel_proposals_r2.json`
- 机制实现：`services/api/app/rulespec/broad_term_split.py`（24 条回归锁已合入）

## 为什么必须是"新 revision"，而不是改一行

已签署的候选**不可原地修改**（这是本项目的一等约束）。Wave01 的
`EXP-R1-W01-REVIEW-R1` 已由 `huangdi97` 签署冻结，其中：

| rule_id | 场所 | 层 | 效果 | 人类决定 | 现状 |
|---|---|---|---|---|---|
| `w01-3a04d4d1aa` | 上海迪士尼乐园 | OPERATOR_POLICY | prohibited | **APPROVED** | 不可执行 |
| `w01-305fa08c1e` | 上海迪士尼乐园 | OPERATOR_POLICY | conditional | **APPROVED** | 不可执行 |
| `w01-6f2bfd39d7` | 上海动物园 | OPERATOR_POLICY | prohibited | **APPROVED** | 不可执行 |

三条**保持 APPROVED**。它们不是被否决，而是在当前数据形状下不可执行；
要让它们可执行，必须新建候选（新 revision）+ 新的人工审查。

## 缺陷的精确形状

两条基底都把来源原文的全域术语归一为 `other`，并标成 `exact`（声称等价）：

| 场所 | `source_scope_exact` | 存储 scope | 归一类型 | 实际后果 |
|---|---|---|---|---|
| 上海动物园 | 动物 | `other` | `exact` | 「动物」= 全部动物；`other` = `{other_pet}`。收窄，不是等价 |
| 上海迪士尼乐园 | 动物（导盲犬除外） | `other` | `exact` | 同上，**且内嵌但书未建模为 RuleException** |

**收窄禁令的后果是沉默而不是答错**：`other` 基底对犬类/猫类查询返回 `unknown`，
而沉默会被用户读成"允许"。实测 before：

| 查询 | 迪士尼 | 动物园 |
|---|---|---|
| 普通犬 | unknown | unknown |
| 导盲犬 | unknown | unknown |
| 猫 | unknown | unknown |
| 其他宠物 | prohibited | prohibited |

## 提案（新候选行，逐字保留来源原文）

### 上海迪士尼乐园 · 3 行基底 + 1 行但书

| # | `source_scope_exact` | `subject_scope_normalized` | `normalization_type` |
|---|---|---|---|
| 1 | 动物（导盲犬除外） | `dog` | `compound_term_split` |
| 2 | 动物（导盲犬除外） | `cat` | `compound_term_split` |
| 3 | 动物（导盲犬除外） | `other` | `compound_term_split` |

- 拆分完整性：`dog ∪ cat ∪ other` = 词表内 9 个主体，互斥且穷尽（`validate_split_group` 校验通过）。
- 内嵌但书：写「导盲犬除外」本身就证明基底覆盖导盲犬（但书只对本来被覆盖的主体才必要），
  故 `requires_proviso=(guide_dog,)`，由既有 APPROVED 的 `w01-305fa08c1e` 作为 carve-out 挂到 **`dog`** 行。
- **来源自证**：这是本次拆分的依据，不是推测。

### 上海动物园 · 3 行基底，无但书

| # | `source_scope_exact` | `subject_scope_normalized` | `normalization_type` |
|---|---|---|---|
| 1 | 动物 | `dog` | `compound_term_split` |
| 2 | 动物 | `cat` | `compound_term_split` |
| 3 | 动物 | `other` | `compound_term_split` |

来源原文**没有**但书，因此不生成 carve-out。

## 拆分后实测（resolver 实际输出，非推断）

| 查询 | 迪士尼 before → after | 动物园 before → after |
|---|---|---|
| 普通犬 | unknown → **prohibited** | unknown → **prohibited** |
| 导盲犬 | unknown → **conditional**（carve-out 生效） | unknown → **prohibited**（来源无但书） |
| 猫 | unknown → **prohibited** | unknown → **prohibited** |
| 其他宠物 | prohibited → prohibited | prohibited → prohibited |

两点必读：

1. **迪士尼那个"不可达的已批准 carve-out"和 scope 收窄是同一个缺陷。** 基底拆好之后它自动可达
   ——不需要为它单独再想办法。
2. **辖区级法定但书救不了迪士尼。** `JPROV-001` 的 `applies_to_layer = LEGAL`，
   而迪士尼基底是 `OPERATOR_POLICY`，层不匹配 ⇒ 不绑定、不生效（这是设计，不是缺陷）。
   所以迪士尼只能走本次拆分。

## 需要人工判断的两件事

| id | 问题 | 归口 |
|---|---|---|
| `ZOO_GUIDE_DOG_AFTER_REMODEL` | 动物园拆分后，导盲犬由 `unknown` 变为 **`prohibited`**。该结论是否受《无障碍环境建设法》等上位法影响，属法律判断 | HUMAN_DECISION |
| `VOCABULARY_NON_PET_ANIMALS` | 「动物」含平台主体词表未建模的动物（观赏鸟、爬行类等）。拆分只覆盖词表内 9 个主体，超出部分继续沉默（`unknown`），**不算允许** | DOCUMENTED_LIMITATION |

`ZOO_GUIDE_DOG_AFTER_REMODEL` 尤其重要：把沉默变成明确的 `prohibited` 是**收窄**，
方向正确（沉默会被读成允许），但对导盲犬给出 `prohibited` 是一个会被真实用户读到的法律结论。
我不做这个判断，只把它摆到台面上。

## 落地步骤（需你发起）

1. 新 revision 的候选行写入（AI 可做，属待审候选产出）；
2. **新的人工审查** —— 逐行 APPROVED / HOLD / REJECTED；
3. 新的 batch manifest + 发布。

在步骤 2 完成前，这三条 old revision 的 APPROVED 行依旧不可执行。
