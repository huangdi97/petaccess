# Search Disambiguation — 同名店、分店、曾用名

> 本文件记录 `GET /api/v1/places?q=` 的真实行为：匹配什么、返回什么、怎么排序、为什么这样排序。
> 全部结论来自本轮实跑，不是设计意图。

## 1. 要解决的问题

一个宠物主人搜「星河咖啡」，想知道「能不能带狗进去」。改造前会发生三件事，每一件都比"搜不到"更糟：

| 现象 | 后果 |
|---|---|
| 只匹配 `canonical_name` | 搜曾用名／别称／英文名返回空列表。**空列表在用户眼里和「没有规则」是同一个画面**，而"这里没有规则"恰恰是这个产品要消灭的误解 |
| 同品牌两家店返回两个无差别同名行 | 用户把 A 店的规则读成整个品牌的规则 |
| 按名称字母序排序 | 新开、尚未收录规则的分店排在已核验总店前面。首屏第一行写「尚未收录规则」，答案在第二行 |

## 2. 数据模型

`place.alias_names`：`JSONB`，默认 `[]`（不是 `NULL`），GIN 索引 `ix_place_alias_names_gin`。

- 迁移：`services/api/migrations/versions/a7c4e1b90d33_place_alias_names.py`（幂等；`downgrade` 会 drop 列）
- 字段语义是**搜索键，不是身份**：曾用名、别称、外文名、口语简称。地点的身份永远是自有 UUID（ADR-003），别名不参与身份判定。
- Admin 写入经 `PlaceUpdate._clean_aliases` 校验：去首尾空白、丢弃空串、去重、单项 ≤200 字符。
  去重理由是实用的：同一个词写两遍不该产生两行匹配。

## 3. 匹配（API）

`services/api/app/api/v1/places.py::list_places`

```sql
place.canonical_name % :q OR place.canonical_name ILIKE :like
OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(place.alias_names) AS alias_name
           WHERE alias_name % :q OR alias_name ILIKE :like)
```

`%` 是 pg_trgm 相似度，`ILIKE` 是 CJK 兜底——纯中文串的 trigram 相似度经常不够，只靠 `%` 会漏。

命中别名时，行里必须说明**是哪个别名命中的**：`matched_alias` 只在命中**不是**来自正式名时才有值。
`_matched_alias()` 用与 SQL 相同的规则在 Python 侧复算，因此「返回的别名」和「实际命中的别名」不会说两套话。

## 4. 返回行自带的信息

`PlaceSummary` 的消歧字段：

| 字段 | 含义 | 为什么在这里 |
|---|---|---|
| `parent_place_name` | 上级场所的正式名（分店的品牌／商场里的店铺的商场） | 一眼分开同品牌两行 |
| `matched_alias` | 命中用的别名（来自正式名时为 `null`） | 用户没打过这个名字，行必须自己解释自己 |
| `alias_names` | 该场所全部别名 | Admin 复用同一投影 |
| `rule_count` | 当前生效规则条数（`status='current'`） | 「这里究竟有没有材料」 |
| `last_verified_at` | 规则最近核验时间 | 时效 |

**判定结果故意不在这里**。列表不发 verdict——verdict 属于 resolver，在列表里复制一份就是列表页和详情页对不上的经典成因。

> `parent_place_name` 原名 `branch_name`。改名原因：它的值是**父级的正式名**，所以「旗舰店」在旧名下显示成自己是自己的分店。UI 文案同时从「位于 X」改为「所属 X」——父级可能是品牌（分店），也可能是容器（商场里的店铺），只有「所属」对两种都成立。

## 5. 排序（本轮修复的缺陷）

`_search_order()`，三级，每级只裁决上一级留下的平局：

1. **匹配质量**：正式名精确相等 → 前缀 → 子串 → 仅别名命中
2. **能不能回答**：有生效规则的排在没有的前面
3. **时效**：`last_verified_at` 新的在前，`NULL` 在最后

最后以名称兜底，保证翻页稳定。

通配符在拼 `ILIKE` 模式前转义（`\`、`%`、`_`），否则用户输入一个 `%` 会匹配全表。

无 `q` 时不做相关度排序，仍按名称——浏览态需要可预测的顺序。

**这只是在给行排序，不决定规则的含义。** 排序不参与任何 verdict 计算。

### 实测

```
q=星河咖啡 → 星河咖啡·测试店  (rules=1, parent=null)          ← 有规则，在先
              星河咖啡·栖霞分店 (rules=0, parent=星河咖啡·测试店)
q=云栖     → 云栖中心·测试商场 (rules=2)                       ← 单一命中
```

## 6. 消费者 UI（`apps/client-h5/src/views/SearchView.vue`）

| 元素 | 内容 |
|---|---|
| 标题 | 名称 + `StatusBadge` |
| 消歧行 | 「所属 {{ parent_place_name }}」（有父级才渲染） |
| 元信息 | 场所类型（已本地化）· 地址（缺失时「地址待补充」） |
| 别名行 | 「以「{{ matched_alias }}」匹配（曾用名／别称）」 |
| 规则摘要 | 「生效规则 N 条 · {{ 时效 }}」；N=0 时「尚未收录规则」 |
| 标签 | 已核验 / 独立携宠区 / 含服务犬信息 / 尚未收录规则 |

枚举一律经 `placeTypeLabel()` / `freshnessLabel()`（`packages/client-core/src/labels.ts`），不再把 `residential_community` 这类原始值打到屏上。

## 7. 演示数据

`services/api/app/db/seed.py::DEMO_PLACES`

| 场所 | 别名 |
|---|---|
| 星河咖啡·测试店（总店） | 星河咖啡 / 星河咖啡（云杉路旧址）/ Xinghe Coffee |
| 星河咖啡·栖霞分店（`parent` = 总店） | 星河咖啡 / 星河咖啡栖霞店 / Xinghe Coffee Qixia |
| 云栖中心·测试商场 | 云栖中心 / 云栖购物中心 / Yunqi Center |

分店原名「星河咖啡·云栖分店」，与「云栖中心·测试商场」在 `q=云栖` 上互相污染，改名以**自身所在街道**命名。
`key` 仍保留 `place_xinghe_cafe_yunqi`：id 由 key 派生，改 key 等于给一个已经有规则指向的场所换 id。

> 注意：`run_demo_seed()` 会清空 `rule_candidate` 等受治理表，因此**不可在有治理数据的库上重跑**。
> 本轮的分店改名是对开发库的定点 `UPDATE`，不是 reseed。

## 8. 测试

`tests/integration/test_place_search_aliases.py`（9 项，夹具自建自清，不依赖 demo seed）：

| 用例 | 断言的性质 |
|---|---|
| `test_alias_hit_returns_the_place` | 搜旧名必须命中，不是空列表 |
| `test_alias_hit_reports_which_alias_matched` | 别命中必须自报是哪个别名 |
| `test_canonical_hit_reports_no_alias` | 正常命中不得谎称走了别名 |
| `test_same_brand_returns_both_branches_labeled` | 同品牌返回两行、各自可辨；总店 `parent_place_name` 为 `null` |
| `test_results_carry_freshness_and_rule_material` | 每行都能说出有多少材料、多新 |
| `test_empty_query_still_lists_places` | 空 `q` 不是搜索，不得被过滤成空 |
| `test_no_match_is_empty_and_matched_alias_is_absent` | 真未命中可以为空，但不能沉默 |
| `test_aliases_are_trimmed_and_deduplicated` | Admin 输入清洗 |
| `test_place_alias_column_defaults_to_empty_list` | 新场所是 `[]` 不是 `NULL` |

`tests/integration/test_api.py::test_search_ranks_a_place_that_can_answer_above_one_that_cannot`
用演示数据锁住 §5 的排序回归（首行必须有规则且无父级，第二行必须是它的分店且无规则）。

## 9. 边界（明确不在本轮范围）

- **不做**"你找的是不是这家"的二次追问 UI。搜索结果已经是可消歧的两行＋「所属」，追问交互属于下一轮。
- **不做**门店营业状态、跨品牌同类推荐。搜索只回答"你打的字对应哪些场所"。
- `matched_alias` 用子串规则，不是编辑距离：写错字（「星河咖非」）靠 `%` 的 trigram 命中，此时 `matched_alias` 可能为 `null`（正式名子串没中，别名子串也没中）。这是已知的粗粒度处，未在本轮加编辑距离解释。
