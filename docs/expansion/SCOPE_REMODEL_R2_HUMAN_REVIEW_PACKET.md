# SCOPE-REMODEL-R2 — Human Review Packet（待签署）

生成：2026-09-18 · 执行 commit `1c10bbe` · 目标库 `petaccess` · **6 条候选均为 REVIEW_PENDING，无任何人类决定**

> 本包只提供**材料与建议**。`final_decision` / `reviewer` / `decided_at` / `decision_note` 一律为空，
> 由你在 `docs/expansion/review_decisions_scope_remodel_r2.json` 里填写。

## 0. 这份包是怎么来的

已签署的 Wave01 里，迪士尼与动物园的过宽来源术语被记成 `animal_scope=other` + `exact`，
规范闸门判为「收窄却声称等价」，**永远无法发布**。已签署候选不可原地修改，所以本轮是
**新建 6 条候选**（新 revision `SCOPE-REMODEL-R2`），旧的两条冻结候选一个字节都没动。

## 1. 必须先读的两条限定

1. **这不是穷尽拆分。** `compound_term_split` 只表示：从宽泛来源术语里拆出**当前系统可表达**
   的那些 scope。它**不**表示 `dog ∪ cat ∪ other_pet` == 来源「动物」的现实世界全集。
   鸟类、爬行类及词表外对象**没有任何行覆盖**，对它们的答案是 `UNKNOWN`，**绝不可读作 ALLOWED**。
2. **动物园的导盲犬问题是法律判断，不是我能给的结论。** 来源原文无但书 ⇒ 拆分后导盲犬
   `unknown → prohibited`；但导盲犬是否因上位法而例外，属于 `LEGAL_APPLICABILITY` 未决项。
   `JPROV-001` 的 `applies_to_layer=LEGAL` 不匹配这里的 `OPERATOR_POLICY`，救不了它。

## 2. 六条逐条（人话）

### 上海迪士尼乐园 / dog — 「动物（导盲犬除外）」不得入园 —— 犬这一类

- **Candidate ID**：`7b595de9-e0c3-4092-aab4-348c4878c296`
- **原文（逐字）**：动物（导盲犬除外）。
- `source_scope_exact` = `动物（导盲犬除外）`（逐字保留，未被改写）
- **系统现在表达了哪一部分**：来源原文的「动物」里，系统现在只表达了「犬」这一种：普通犬、导盲犬及全部犬类角色。
- **没有表达哪一部分**：来源原文里的非犬动物（如鸟类、爬行类）——但注意原文自带但书：导盲犬除外。
- **来源 / 证据**：上海迪士尼度假区官网《上海迪士尼乐园游客须知》 · https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/ · evidence_class=`original` / `operator_official`
- **监控与新鲜度**：url_hash / 1440min / active · 复审间隔 90 天（`official_operator_policy`）
- **层 / 效果 / 强制等级**：OPERATOR_POLICY / prohibited / operator_discretion
- **UNMODELED_SOURCE_SCOPE_REMAINDER**：**YES**
- **例外依赖**：depends_on_exception_proposal=w01-305fa08c1e（挂接本行，仍为提案，未发布）
- **AI 建议（非决定）**：APPROVE_AS_SPLIT（建议，非决定） — 来源原文自带但书「导盲犬除外」，dog 行与既有 carve-out w01-305fa08c1e 配套后可完整表达该但书。
- **你要判断什么**：这一行要不要发布？发布后普通犬答案 = prohibited，导盲犬由挂接的例外决定。
- **人类字段**：`final_decision=null` · `reviewer=null` · `decided_at=null` · `decision_note=null`

### 上海迪士尼乐园 / cat — 「动物（导盲犬除外）」不得入园 —— 猫这一类

- **Candidate ID**：`4580ab21-60c2-4bfb-9a2c-47cde25c5678`
- **原文（逐字）**：动物（导盲犬除外）。
- `source_scope_exact` = `动物（导盲犬除外）`（逐字保留，未被改写）
- **系统现在表达了哪一部分**：来源原文的「动物」里，系统现在只表达了「猫」这一类。
- **没有表达哪一部分**：犬、其他宠物，以及词表外的动物。
- **来源 / 证据**：上海迪士尼度假区官网《上海迪士尼乐园游客须知》 · https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/ · evidence_class=`original` / `operator_official`
- **监控与新鲜度**：url_hash / 1440min / active · 复审间隔 90 天（`official_operator_policy`）
- **层 / 效果 / 强制等级**：OPERATOR_POLICY / prohibited / operator_discretion
- **UNMODELED_SOURCE_SCOPE_REMAINDER**：**YES**
- **例外依赖**：none
- **AI 建议（非决定）**：APPROVE_AS_SPLIT（建议，非决定） — 来源术语覆盖猫，当前词表可表达。
- **你要判断什么**：这一行要不要发布？发布后猫的答案 = prohibited。
- **人类字段**：`final_decision=null` · `reviewer=null` · `decided_at=null` · `decision_note=null`

### 上海迪士尼乐园 / other — 「动物（导盲犬除外）」不得入园 —— 其他宠物这一类

- **Candidate ID**：`4ca5e55a-6aaf-4ef5-9e0d-cdefbfac98cd`
- **原文（逐字）**：动物（导盲犬除外）。
- `source_scope_exact` = `动物（导盲犬除外）`（逐字保留，未被改写）
- **系统现在表达了哪一部分**：来源原文的「动物」里，系统现在只表达了「其他宠物」（other_pet）这一类。
- **没有表达哪一部分**：犬、猫，以及词表外的动物。注意 other 不等于「剩下的全部动物」，它只是 other_pet。
- **来源 / 证据**：上海迪士尼度假区官网《上海迪士尼乐园游客须知》 · https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/ · evidence_class=`original` / `operator_official`
- **监控与新鲜度**：url_hash / 1440min / active · 复审间隔 90 天（`official_operator_policy`）
- **层 / 效果 / 强制等级**：OPERATOR_POLICY / prohibited / operator_discretion
- **UNMODELED_SOURCE_SCOPE_REMAINDER**：**YES**
- **例外依赖**：none
- **AI 建议（非决定）**：APPROVE_AS_SPLIT（建议，非决定） — other = {other_pet}；仅覆盖词表内的「其他宠物」，不等于来源术语全域。
- **你要判断什么**：这一行要不要发布？发布后其他宠物的答案 = prohibited。
- **人类字段**：`final_decision=null` · `reviewer=null` · `decided_at=null` · `decision_note=null`

### 上海动物园 / dog — 「请不要携带动物入园」—— 犬这一类

- **Candidate ID**：`a4e2ba26-f542-4ee6-a088-c073096db733`
- **原文（逐字）**：3、请不要携带动物入园 为避免动物间交叉感染，把你的爱宠托了吧！
- `source_scope_exact` = `动物`（逐字保留，未被改写）
- **系统现在表达了哪一部分**：来源原文的「动物」里，系统现在只表达了「犬」这一种：普通犬与全部犬类角色，含导盲犬。
- **没有表达哪一部分**：猫、其他宠物，以及词表外的动物。
- **来源 / 证据**：上海动物园官网《温馨提示》 · https://www.shanghaizoo.cn/sites/shanghaizoo/shanghaizoo_wap/tishi.html · evidence_class=`original` / `operator_official`
- **监控与新鲜度**：url_hash / 1440min / active · 复审间隔 90 天（`official_operator_policy`）
- **层 / 效果 / 强制等级**：OPERATOR_POLICY / prohibited / operator_discretion
- **UNMODELED_SOURCE_SCOPE_REMAINDER**：**YES**
- **法律适用未决**：LEGAL_APPLICABILITY_UNRESOLVED：OPERATOR_POLICY 来源说「禁止」；导盲犬是否因上位法而例外 = 未解决，需人工裁决。JPROV-001 的 applies_to_layer=LEGAL 不适用于本行层。
- **例外依赖**：none
- **AI 建议（非决定）**：APPROVE_WITH_LEGAL_CAVEAT（建议，非决定） — 来源原文无但书，拆分后导盲犬由 unknown 变 prohibited；但是否受更高层法律/法定权利影响属法律判断，不由本建议认定。
- **你要判断什么**：**这一行需要法律判断**：来源原文没有任何但书，所以导盲犬也会是 prohibited；但导盲犬是否因上位法而例外，不由我判定。
- **人类字段**：`final_decision=null` · `reviewer=null` · `decided_at=null` · `decision_note=null`

### 上海动物园 / cat — 「请不要携带动物入园」—— 猫这一类

- **Candidate ID**：`27893d75-aa05-422f-9797-2120e81db2ec`
- **原文（逐字）**：3、请不要携带动物入园 为避免动物间交叉感染，把你的爱宠托了吧！
- `source_scope_exact` = `动物`（逐字保留，未被改写）
- **系统现在表达了哪一部分**：来源原文的「动物」里，系统现在只表达了「猫」这一类。
- **没有表达哪一部分**：犬、其他宠物，以及词表外的动物。
- **来源 / 证据**：上海动物园官网《温馨提示》 · https://www.shanghaizoo.cn/sites/shanghaizoo/shanghaizoo_wap/tishi.html · evidence_class=`original` / `operator_official`
- **监控与新鲜度**：url_hash / 1440min / active · 复审间隔 90 天（`official_operator_policy`）
- **层 / 效果 / 强制等级**：OPERATOR_POLICY / prohibited / operator_discretion
- **UNMODELED_SOURCE_SCOPE_REMAINDER**：**YES**
- **例外依赖**：none
- **AI 建议（非决定）**：APPROVE_AS_SPLIT（建议，非决定） — 来源术语覆盖猫，当前词表可表达。
- **你要判断什么**：这一行要不要发布？发布后猫的答案 = prohibited。
- **人类字段**：`final_decision=null` · `reviewer=null` · `decided_at=null` · `decision_note=null`

### 上海动物园 / other — 「请不要携带动物入园」—— 其他宠物这一类

- **Candidate ID**：`2a3de3ab-de8d-4074-a4d0-3039c715893d`
- **原文（逐字）**：3、请不要携带动物入园 为避免动物间交叉感染，把你的爱宠托了吧！
- `source_scope_exact` = `动物`（逐字保留，未被改写）
- **系统现在表达了哪一部分**：来源原文的「动物」里，系统现在只表达了「其他宠物」（other_pet）这一类。
- **没有表达哪一部分**：犬、猫，以及词表外的动物。
- **来源 / 证据**：上海动物园官网《温馨提示》 · https://www.shanghaizoo.cn/sites/shanghaizoo/shanghaizoo_wap/tishi.html · evidence_class=`original` / `operator_official`
- **监控与新鲜度**：url_hash / 1440min / active · 复审间隔 90 天（`official_operator_policy`）
- **层 / 效果 / 强制等级**：OPERATOR_POLICY / prohibited / operator_discretion
- **UNMODELED_SOURCE_SCOPE_REMAINDER**：**YES**
- **例外依赖**：none
- **AI 建议（非决定）**：APPROVE_AS_SPLIT（建议，非决定） — other = {other_pet}；仅覆盖词表内的「其他宠物」，不等于来源术语全域。
- **你要判断什么**：这一行要不要发布？发布后其他宠物的答案 = prohibited。
- **人类字段**：`final_decision=null` · `reviewer=null` · `decided_at=null` · `decision_note=null`

## 3. 迪士尼导盲犬 carve-out 的挂接

既有 `w01-305fa08c1e`（导盲犬例外，已 APPROVED）原挂在冻结的 `other` 基底上，
实测 `is_reachable_carveout = False`（永远打不到，沉默会被读成禁止）。
新 `dog` 基底上实测 **True**。登记表 `exception_plan` 已把挂接点改到
`7b595de9-e0c3-4092-aab4-348c4878c296`。
**该例外仍然是提案/审查材料，未发布。**

## 4. 建议不等于决定

`ai_recommendation` 是建议，不得被复制进 `final_decision`。本轮没有、也不会自动签署。

