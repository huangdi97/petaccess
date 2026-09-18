# ADR-030：辖区级法定例外（statutory proviso）机制

- 状态：**已实现（机制）** / **数据待人工激活**
- 日期：2026-09-18
- 关联：ADR-025（作用域与法律效力）、ADR-029（来源作用域语义等价）、
  `docs/governance/OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL.md`
- 触发：Master Goal Phase B 第 1 步

## 1. 问题

《上海市养犬管理条例》第二十三条禁止犬只进入商场、博物馆、餐厅等场所，随后规定：
**「盲人携带导盲犬的，不受本条规定的限制。」**

这个但书是**法律文件自身的一部分**，不是任何某一个场所的运营政策。平台当前的模型只有
`rule_exception`，它按 `rule_id` 绑定到**具体某一条基底规则**：

```
rule_exception.rule_id → access_rule.id
```

后果（已实测，见 `WAVE01_PRE_REAL_PUBLISH_SEMANTIC_BRIDGE_REPORT.md`）：

| 现状 | 后果 |
|---|---|
| 但书被建模成 3 条场所级 `rule_exception`，分别绑到和平饭店 / 上图东馆 / 星巴克烘焙工坊 | 每新增一条 LEGAL 禁犬规则，都必须**再补一条**例外 |
| 新基底没有绑定例外 | 导盲犬查询 `effect=prohibited`、`applied_exceptions=[]` |

第二条是最严重的：**平台援引了某条法律，却给出比那条法律更窄的答案，并且还挂着出处。**
这比「不知道」更糟。Wave01 的 6 条 LEGAL 犬类基底正是因此被判
`REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE` 而拦下。

## 2. 决定

引入 **`JurisdictionException`（辖区级法定例外）**：一种**按法律文件同一性绑定**的
carve-out，而不是按 `rule_id` 绑定。

一次绑定必须**同时**满足以下全部条件，任一不满足即不生效（fail-closed）：

| # | 判据 | 理由 |
|---|---|---|
| 1 | 但书自身有 `source_id`，且 `status='current'`、在有效期内、 `review_status='reviewed_active'` | 无出处的例外永不生效（沿用 `LayeredException.has_source`） |
| 2 | 查询主体精确匹配但书的 `subject_scope_normalized`（走 canonical `rule_governs`，要求 `normalization_type='exact'`） | ADR-025：听导盲犬的但书不能扩给全部服务犬 |
| 3 | `base.source_id ∈ 但书.instrument_source_ids` | **法律文件同一性**——见 §3 |
| 4 | `base.rule_layer == 但书.applies_to_layer`（LEGAL）且 `base.effect ∈ applies_to_effects`（`prohibited`） | 但书豁免的是**法定禁止**，不是运营政策 |
| 5 | 基底**语义上治理**但书的主体（canonical `rule_governs`） | 可达性定理，见 §4 |

## 3. 为什么按「法律文件同一性」而不是按 `source_id` 单一绑定

生产库里《上海市养犬管理条例》有 **2 个 `source` 行**：

| source_id | 出处 |
|---|---|
| `f20bdb2c…` | 上海市公安网转载（第二十三条页） |
| `a11aff10…` | 上海市人民政府门户（全文） |

而已发布的 5 条 LEGAL 禁犬规则**分别引用了不同的那一个**：

- `f20bdb2c…` ← 和平饭店 `cd9139a1…`、上图东馆 `332f17b6…`、星巴克 `2d77f4b6…`
- `a11aff10…` ← 兴业太古汇 `47a1d679…`、上博东馆 `ca0b01c2…`

⇒ 若按单一 `source_id` 绑定，**有一半规则会漏掉**。

而「这两个 URL 是同一部法律」是**编辑判断**，不能靠 URL 相似度推断。因此：
`instrument_source_ids` 是一个**显式声明、须经人工审阅**的列表——
「以下 source 行属于同一部法律文件」。空列表 ⇒ 永不生效。

> 对比：辖区级**规则**已有先例——`access_rule.jurisdiction_code` +
> `applies_to_place_types`（`_load_layered_rules` 已支持）。本 ADR 补的是辖区级**例外**。

## 4. 惰性例外：绝不把「沉默」改写成「允许」

第 5 条是安全关键。若基底作用域是 `other`（只覆盖 `{other_pet}`），它对导盲犬**沉默**
（`unknown`）。此时若套用但书，会把 `unknown` 变成 `allowed` —— **凭空发明法律效力**。

因此：基底不治理但书主体 ⇒ 该但书对这条基底**惰性**（`JURISDICTION_EXCEPTION_INERT`），
**不应用**，只在解释步骤里记录。这与已确立的定理一致：
`other` 基底遇 guide_dog 查询解析为 `unknown` 而非 `prohibited`。

## 5. 治理约束

- **系统绝不自动生成或激活辖区级例外。** 新增记录默认
  `status='proposed'`、`review_status='not_reviewed'`，两个条件都满足才会被 resolver 读取。
- 「激活上海市养犬管理条例第二十三条但书」是**辖区级法律效力变更**，属于
  **Human Decision**，须由 reviewer 显式签署后方可置为 `current` + `reviewed_active`。
- 本轮只交付机制；数据以**待审候选**形式产出，不写入生效状态。

## 6. 影响面

- `services/api/app/models/civic.py`：新增 `JurisdictionException`
- `services/api/app/rulespec/statutory_proviso.py`（新）：纯函数绑定判据
- `services/api/app/rulespec/v05_resolver.py`：`LayeredException` 增 4 字段；
  `resolve()` 增加 instrument 绑定分支 + 惰性记录
- `services/api/app/rulespec/guide_dog_safety.py`：路径 C 支持 instrument 绑定
- `services/api/app/api/v1/v05.py`：`_load_layered_rules` 加载已激活的辖区级例外

## 7. 被否掉的替代方案

| 方案 | 否决理由 |
|---|---|
| 每次新增基底时自动复制一条 `rule_exception` | 等于让系统替法律补但书；且复制品与原法条无绑定关系，无法审计 |
| 在 resolver 里硬编码 `if service_role=='working': allowed` | 绕开 Source 与作用域，ADR-025 明确禁止 |
| 按 `source.issuer` 模糊匹配判断"同一部法律" | 推断而非声明，属于不可审计的法律判断 |
| 把但书建成一条 access_rule 挂在 LEGAL 层 | 会与禁入基底在同一层构成 allowed-vs-prohibited 冲突（POTENTIAL_CONFLICT），而不是豁免 |
