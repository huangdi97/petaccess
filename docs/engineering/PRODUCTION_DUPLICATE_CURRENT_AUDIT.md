# PRODUCTION DUPLICATE-CURRENT AUDIT (§29 / §30)

- 轮次：`PRODUCTION_DATA_ISOLATION_AND_INTEGRITY_CLOSURE_R1`
- 数据库：`petaccess`（role = `PRODUCTION`）
- 方式：**只读**。本文件是审计结论，不修改任何数据。
- 证据来源：`artifacts/production_integrity_baseline.json`、
  `artifacts/production_isolation/PROD_FINGERPRINT_A.json`、
  `artifacts/production_isolation/CLEANUP_PLAN_DRY_RUN.json`

## 1. §29 目标对象

§29 要求单独审计「青岚公园·演示 的重复 current 规则」。定位结果：

| 项 | 值 |
| --- | --- |
| Place | `9152b7dc-0844-52f6-957a-77bdb15d435a` — `青岚公园·演示`（park，demo seed） |
| Zone | `645e539f-af89-5724-87f0-7098573dcf59` — `A 草坪`（`zone_type = lawn`） |
| 冲突键 | `zone_id = 645e539f…`，`place_id IS NULL`（规则挂在 Zone 上），`animal_scope = ordinary_pet`，`action = walk` |
| `rule_layer` | `NULL`（两条都是空层，非 `LEGAL` / 非 `OPERATOR_POLICY`） |

### 两条 current 规则

| rule id | effect | effective_from | source_id | source issuer |
| --- | --- | --- | --- | --- |
| `decd5051-50be-5d13-8273-ca20c0374f0f` | `conditional` | （未设） | `edfd1be4-ab67-52de-bf63-28ea89e0bddc` | `演示市绿化市容管理局（虚构）` |
| `440e419e-582e-5994-bfcb-ca7dd83687d6` | `prohibited` | （未设） | `cb18ca7a-7955-56ad-97c7-f4b756905ed5` | `青岚公园入口告示（用户上传，虚构）` |

两者 `subject_scope_normalized = ordinary_pet`、`source_scope_exact = ordinary_pet`、
`supersedes_rule_id IS NULL`，`created_at` 均为 demo seed 时间 `2026-09-12T20:34:30.530241Z`。

### 为什么同时命中两个检查

`check_production_integrity.py` 的两个检查共用同一个分组键
`(place_id, zone_id, animal_scope, action, rule_layer)`：

- `DUPLICATE_CURRENT_RULE = 2` —— 同一分组下有 2 条 `status = 'current'`。
- `CONFLICTING_CURRENT_RULES = 2` —— 同组两条 current 的 `effect` 不同
  （`conditional` vs `prohibited`），对同一查询无法给出唯一答案。

即：**一个现象，两个指标**，不是两组独立问题。基线文件中两项均为 `2`，与实际相符。

### 与"合法分层"的区别（重要，避免误判）

库内另有一批 `(place_id, dog, enter)` 出现 **两条 current** 的分组
（约 120 组），但它们是 **LEGAL + OPERATOR_POLICY 分层对**：

- 一条 `rule_layer = LEGAL`、`effect = prohibited`；
- 一条 `rule_layer = OPERATOR_POLICY`、`effect = allowed`；
- 两条 `source_id` 相同。

这是本项目 **Place → Zone → AccessRule 分层模型的设计行为**（LEGAL 层与运营层并存，
由 resolver 按层序裁决），**不是重复也不是冲突**，因此完整性检查器没有把它们计入
`DUPLICATE_CURRENT_RULE` / `CONFLICTING_CURRENT_RULES`。这两项计数保持为 `2` 是**正确的**。

> 该 120 组分层的规则全部挂在将被清理的测试夹具场所上，随夹具一并删除；
> 保留集中只有 `7f5093f3`（和平饭店·费尔蒙）、`b3504140`（上海图书馆东馆）、
> `0f482974`（星巴克臻选上海烘焙工坊）三处存在 LEGAL/OPERATOR 分层，且是**不同
> `animal_scope`**（`dog` vs `ordinary_pet`），因此保留侧零冲突。

## 2. §30 分类

按 §30 的 A/B/C/D 分类标准：

| 判据 | 结果 |
| --- | --- |
| A —— 真实场所、真实来源、真实冲突 → 需人工裁决实质 | 否。两条 source 的 issuer 均含「虚构」字样 |
| B —— 真实场所、测试夹具来源 | 否。所属 Place 属于 demo seed 集 |
| C —— 演示/虚构数据、无真实指涉 | **是** |
| D —— 历史遗留、已被后续状态取代 | 否。两条都还是 `current` |

### 分类结论

```
CLASSIFICATION         = C_DEMO_VIRTUAL_NO_REAL_REFERENT
PLACE_CLASS            = DEMO_SEED_PLACE (在本轮 §0 口径下属于"非真实业务数据")
DISPOSITION            = MANUAL_REVIEW_REQUIRED
AUTO_DELETE            = NO
```

**判定为 `MANUAL_REVIEW_REQUIRED`，本轮不自动删除、也不自动改写。** 依据：

1. §30 明确要求「模糊 ⇒ `MANUAL_REVIEW_REQUIRED`」，不得自动处置；
2. cleanup 计划的 `DEMO_SEED_PLACES` 白名单（含「青岚公园·演示」）把该 Place 与
   其 Zone/Rule 整体排除在删除集之外，两条规则均在
   `CLEANUP_PLAN_DRY_RUN.json → surviving_access_rules` 中（`decd5051` / `440e419e`
   均可见）。所以不管是否执行 cleanup，这两条都会保留；
3. 「两条 current 规则对同一 (Zone, ordinary_pet, walk) 给出 `conditional` 与
   `prohibited` 两种互斥答案」是一个**语义问题**，不是数据污染问题。修它要动的是
   demo seed 的定义或 demo 数据的语义，属于人类决策，不应由本轮 Agent 顺手改掉。

### 需要人类裁决的选项（本轮不决定）

| 选项 | 含义 | 影响 |
| --- | --- | --- |
| 1. 把 demo seed 从 `petaccess` 迁出 | 让 `petaccess` 真正做到 §0 的"只有真实业务数据" | 需另建 demo 环境；`petaccess` 将不再有演示场所 |
| 2. 保留 demo seed，但在 demo Zone 上收敛为单条 current | 保留演示能力，消除互斥 | 需明确哪条为准（`prohibited` 更保守） |
| 3. 保留现状，标记为已知 demo 语义缺陷 | 零改动 | `DUPLICATE_CURRENT_RULE` 将持续为 2，Gate 需以 limitation 记录 |

## 3. 本轮 Gate 影响

- 该对象**不构成** `PRODUCTION_DATA_INTEGRITY` 的 CRITICAL 阻断项（已分类、未见未处理）。
- 它使 `DUPLICATE_CURRENT_RULE = 2` / `CONFLICTING_CURRENT_RULES = 2` 长期非零，
  且**本轮不会消失**。Gate 报告中必须显式记录为已知遗留，不得声称"完整性检查全 0"。
- 与 §1/§2 的冻结无关：这两条规则不属于 Batch-01B 的 8 个对象。

## 4. 复现命令（只读）

```bash
export PATH="/c/Program Files/Git/cmd:/c/Program Files/Git/mingw64/bin:/usr/bin:/bin:$PATH"

docker exec petaccess-db-1 psql -U petaccess -d petaccess -c "
select coalesce(zone_id::text,'-') as zone_id, animal_scope, action, rule_layer,
       count(*) filter (where status='current') as current_n,
       count(distinct effect) filter (where status='current') as distinct_effects
from access_rule
where zone_id = '645e539f-af89-5724-87f0-7098573dcf59'
group by 1,2,3,4;"
```

预期：1 行，`current_n = 2`，`distinct_effects = 2`。
