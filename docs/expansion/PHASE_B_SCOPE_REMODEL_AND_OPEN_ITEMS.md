# Phase B · 过宽来源术语拆分、世纪公园补采、地理缺口审计

> 本轮只做非人工决定部分。**未激活任何辖区级但书**，**未改写任何已签署候选**，
> **未向生产库写入任何规则数据**。

## 1. 本轮处理了什么

| 项 | 内容 | 结果 |
|---|---|---|
| B2/B3 | 迪士尼 / 上海动物园 source-scope Semantic Remodel | 机制落地 + 前后对照已证明，**产出为提案，待人工复核后建新候选** |
| B3' | 迪士尼不可达 carve-out | 与 B2 是**同一个缺陷**，拆分后自动变为可达（已证明） |
| B4 | 世纪公园一手来源补采 | **未取得一手来源**；取得 4 家独立媒体一致引述，仍不清 ADR-021 |
| B5 | `PLACE_GEO_PENDING` 审计 | 量化了消费者可见影响：2 个已发布场所**永远不出现在附近搜索里** |
| B1 | 6 条 LEGAL 犬类基底 | 仍停在 `ACTIVATE_STATUTORY_PROVISO_OR_DECLARE`（人工决定，未动） |

## 2. B2/B3：过宽来源术语的穷尽拆分

### 缺陷的精确形状

两条候选把**比任何单一 scope 都宽**的来源术语存成了 `other` 并标 `exact`：

| 场所 | 来源原文 | 存储 | 实际覆盖 |
|---|---|---|---|
| 上海迪士尼乐园 | 「动物（导盲犬除外）」 | `other` / `exact` | `{other_pet}` |
| 上海动物园 | 「动物」 | `other` / `exact` | `{other_pet}` |

`SCOPE_SUBJECTS['other'] == {other_pet}`。所以这条规则**对犬类查询不匹配任何东西**——
后果不是答错，而是**沉默**：平台对一个自家公告写明「动物不得入园」的场所回答 `unknown`，
而沉默会被读成允许。方向与 ADR-025 相反（那条是放宽但书），性质相同（来源不支持的作用域关系被当成支持）。

### 一个决定性的文本证据

迪士尼那条来源**自己**写了「导盲犬除外」。但书只有在它所限定的基底**本来覆盖**被豁免主体时才必要。
也就是说，来源文本内部就证明了：基底「动物」必然管辖导盲犬。当前存成 `other` 使这条但书变得毫无意义——
这不是语义细节争议，是原文自证。

### 为什么是拆分，而不是新增 `all_animals` scope

1. 「动物」包含平台主体词表未建模的动物（观赏鸟等）。新增 scope 只会是一个**顶着全称的近似**，
   而 ADR-025 下近似不得标 `exact`。
2. 单一 all-animals 基底**无法表达迪士尼原文**——原文自带但书。

拆分复用 ADR-028 为「军警犬」建的既有通道：每行保留逐字 `source_scope_exact`，
`normalization_type='compound_term_split'`，成员集在代码中显式声明、可审可测。`compound_term_split`
本就是 ADR-025 下两个具备法律效力的归一化之一，**没有新造通道**。

声明（`services/api/app/rulespec/broad_term_split.py`）：

```
「动物」                → (dog, cat, other)                 无内嵌但书
「动物（导盲犬除外）」   → (dog, cat, other)   requires_proviso = (guide_dog,)
```

`dog ∪ cat ∪ other` = 词表内 9 个主体，**互斥且穷尽**（有测试锁定）。

### 前后对照（canonical resolver 实测，非推理）

上海迪士尼乐园：

| 查询 | 当前 | 拆分后 |
|---|---|---|
| 普通犬 | `unknown` | `prohibited` |
| 导盲犬 | `unknown` | `conditional`（carve-out 实际生效，基底被抑制） |
| 猫 | `unknown` | `prohibited` |
| 其他宠物 | `prohibited` | `prohibited` |

上海动物园：

| 查询 | 当前 | 拆分后 |
|---|---|---|
| 普通犬 | `unknown` | `prohibited` |
| 导盲犬 | `unknown` | `prohibited`（来源无但书） |
| 猫 | `unknown` | `prohibited` |
| 其他宠物 | `prohibited` | `prohibited` |

### B3' 顺带解决：迪士尼不可达 carve-out

上一轮判定 `w01-305fa08c1e` 为 `INREACHABLE_APPROVED_CARVE_OUT`（惰性例外）。
根因即上表：基底 `other` 不管辖 `guide_dog`，例外无处切入。**基底修好，例外自动可达**，
本轮已用 resolver 证明（同一条 carve-out、同一条基底，仅改 scope，`applied_exceptions` 由 `[]` 变为生效）。

### 顺手修掉的一个真实缺陷

上一轮建的 §6 闸门 `validate_source_scope_semantic_compatibility` 只做**等价性**检验。
`compound_term_split` 行按定义就是"声明拆分的成员、不是等价"，用等价检验会**拒掉所有拆分行**
（含 ADR-028 既有的「军警犬」）。已改为按归一化类型分派：拆分行走成员检验，等价行走等价检验。

### 落地方式（受限）

已签署候选不可原地改。所以本次**不发布任何东西**，只产出提案
`docs/expansion/scope_remodel_proposals_r2.json`；真正的落地须在**新 revision 建新候选 + 新人工审查**。

## 3. B4：世纪公园一手来源补采 —— 未取得一手来源

当前证据 `evidence_strength = search_snippet`，URL 为市政文旅门户的推广文章
（上海市文化和旅游事业发展中心，**转述**世纪公园口径），故被 ADR-021 拦下。

补采结果：

- 检索到 **4 家相互独立的媒体**（东方网/新民晚报、新闻晨报、人民网上海频道、解放日报·上观）
  一致引述同一句话：「除世纪宠物乐园区域外，世纪公园其他区域仍禁止携带宠物入园」，
  且均归因于世纪公园管理方。
- **未找到一手来源**：世纪公园自有渠道（微信公众号「上海世纪公园」的游园须知/公告）无稳定网页入口；
  检索到的《24小时开放公约》与游园须知文本**均未提及宠物**。

结论：**交叉印证提升了置信度，但不满足 ADR-021**。ADR-021 卡的不是"这句话真不真"，
而是"证据是否可核验的一手记录"。多家媒体转述同一口径仍属二手。

因此该候选**继续不发布**，记为：

```
CENTURY_PARK_PRIMARY_SOURCE = STILL_MISSING
next action = 现场采集（入口告示牌照片 / 园方公众号原文快照）—— 人工/外勤动作
```

## 4. B5：`PLACE_GEO_PENDING` 的消费者可见影响（量化）

20 个场所中 **10 个无坐标**。其中：

- **上海博物馆东馆**（2 条已发布规则）
- **兴业太古汇**（1 条已发布规则）

`/places/nearby` 的 SQL 带 `Place.location.isnot(None)` +
`ST_DWithin(Place.location, ...)`，无坐标行**被结构性排除**。
⇒ 刚发布的这两个场所**永远不会出现在"附近"结果里**，且**没有任何提示**。
用户不会看到"这里可能漏了"，只会看到列表里没有它。

这是沉默降级，不是错误答案，但与平台"沉默不等于允许"的立场不一致。
是否把无坐标场所单列展示属产品决定，**本轮不擅自改 API 语义**，仅记录：

```
PLACE_GEO_PENDING = OPEN
consumer_impact   = /places/nearby 静默排除 10 个场所（含 2 个已发布规则的场所）
rule              = 来源未公布坐标时不推断坐标（§72-§73）—— 本轮不违反
```

## 5. 本轮产物

- `services/api/app/rulespec/broad_term_split.py` —— 拆分声明、单行检验、整组完整性检验
- `services/api/app/rulespec/source_scope_semantics.py` —— 按归一化类型分派（修缺陷）
- `scripts/w01_scope_remodel_proposal.py` —— 只读提案 + 前后 resolver 对照
- `docs/expansion/scope_remodel_proposals_r2.json` —— 提案（含每组拆分完整性判定）
- `tests/unit/test_broad_term_split.py` —— 24 条回归锁

## 6. 停闸

```
B1  ACTIVATE_STATUTORY_PROVISO_OR_DECLARE   = 人工决定（未动）
B2  SCOPE_REMODEL_PROPOSAL_READY           = 待人工复核后建新 revision 候选
B4  CENTURY_PARK_PRIMARY_SOURCE            = STILL_MISSING（需现场采集）
B5  PLACE_GEO_PENDING                      = OPEN（产品决定：是否单列无坐标场所）
```
