# 生产库污染审计（PRODUCTION_CONTAMINATION_AUDIT）

> 只读审计：`petaccess` 里到底有多少东西是测试留下的，凭什么这么判。
> 轮次：`PRODUCTION_DATA_ISOLATION_AND_INTEGRITY_CLOSURE_R1`。
> 全部结论来自只读脚本，审计过程本身不改数据。

## 1. 方法与证据标准（`scripts/production_fixture_cleanup.py`）

名字可疑**永远不够**。判定为 `CONFIRMED_TEST_FIXTURE` 需要以下之一：

- **E1 规范夹具注册表**：场所名 / 来源签发方是 `tests/**` 里的 f-string 字面量
  （每条都带着 `file:line`）；
- **E2 测试账号**：`audit_log.actor_user_id` 属于只为一次测试存在的账号族
  （`v05mod-*` / `rb-*` / `mand-*` / `e2e-*` / …）；
- **E3 爆发窗口**：`created_at` 落在 QA 爆发期内；
- **E4 无真实指涉**：它触达的所有 source / evidence bundle 本身也是测试账号建的。

非 place 对象（source / bundle / artifact / media / organization / template）删除
要求 **E2 且「没有幸存者还在引用它」**。两条不能同时成立的，一律留下并报告。

分类输出：`CONFIRMED_TEST_FIXTURE` / `LIKELY_TEST_FIXTURE` / `REAL_PRODUCTION` /
`HISTORICAL_GOVERNANCE` / `UNKNOWN`。

> `audit_log.target_id` 对 `source` 与 `zone` 不可用（2647 行存的是字面量字符串
> `'None'`），所以这两类不用 audit join 取证，source 改用**规范签发方**取证。
> 这个取舍直接决定了第一批的来源删除数（1449 → 94）。

## 2. 清单（`artifacts/production_isolation/PRODUCTION_FIXTURE_INVENTORY.json`）

| 分类 | Place 数 |
|---|---|
| `CONFIRMED_TEST_FIXTURE` | **1231** |
| `UNKNOWN` | 3 |
| `REAL_PRODUCTION` | 10 |
| `HISTORICAL_GOVERNANCE` | 5 |

其它表（清理前）：`user` 1759、`source` 1449、`access_rule` 1119（其中 `current` 843）、
`rule_exception` 134（`current` 87）、`rule_candidate` 450、`evidence_bundle` 733、
`observation_claim` 2238、`media_object` 384、`audit_log` 9254。

### 真实一侧

- **10 个真实试点场所**（登记表 `docs/reality_audit/review_decisions_r2_final.json` 的
  `registry_place_names`）：Manner 咖啡（凯德虹口店）、上海图书馆东馆、上海迪士尼乐园、
  前滩太古里、和平饭店（费尔蒙）、大吉路公园、广场公园（黄浦段）、
  星巴克咖啡（徐汇西岸梦中心店）、星巴克臻选上海烘焙工坊、港汇恒隆广场。
- **4 个真实账号**：`admin@demo-petaccess.com`、`operator@demo.local`、
  `real-pilot-admin@example.com`、`scope-split-ops@example.com`。
- 登记表 37 条候选（8 条 `PUBLISHED` = Batch-01B，29 条 `REVIEW_PENDING`）。

### 843 条 `current` 规则为什么基本是夹具

按来源签发方分组（`access_rule.status='current'`）：

| 签发方 | 规则数 |
|---|---|
| 云栖商业管理有限公司（演示） | 143 |
| E2E-C 政府页面 | 85 |
| E2E-D 论坛线索 | 66 |
| 测试条例（集成夹具） | 65 |
| E2E-A 门口告示 | 57 |
| quality-baseline | 54 |
| 测试条例（xxxxxx）× 约 40 个 | 各 2 |
| 上海市人大常委会《上海市养犬管理条例》第二十三条 | **3（真实）** |
| 星河咖啡门店告示（虚构）/ 松风物业（演示）/ 演示市绿化市容局（虚构） | 少量（demo seed） |

幸存下来的 28 条规则＝ 5 条 Batch-01B + 3 条真实 LEGAL 规则（上海市养犬管理条例，
落在和平饭店·费尔蒙 / 上海图书馆东馆 / 星巴克臻选）+ 20 条 demo seed 规则。

## 3. §29/§30 重复 current 规则单独审计

结论见 `docs/engineering/PRODUCTION_DUPLICATE_CURRENT_AUDIT.md`。摘要：

- 目标 = Place `9152b7dc` 青岚公园·演示 → Zone `645e539f`「A 草坪」
  （`place_id IS NULL`，规则挂在 Zone 上），`ordinary_pet / walk`，`rule_layer` 为空。
- 两条 current：`decd5051`（`conditional`，2026-05-15）与 `440e419e`（`prohibited`，2026-08-13）。
- 一个现象打中两个指标：`DUPLICATE_CURRENT_RULE = 2` 与 `CONFLICTING_CURRENT_RULES = 2`。
- 分类 `C_DEMO_VIRTUAL_NO_REAL_REFERENT` → `MANUAL_REVIEW_REQUIRED`，**不自动删除**。

### 顺带澄清：LEGAL + OPERATOR 双 current 不是冲突

库里另有约 120 组 `(place, dog, enter)` 存在两条 current，但它们是
**LEGAL（prohibited） + OPERATOR_POLICY（allowed）分层对**，同一 `source_id`。
这是分层模型的设计行为（LEGAL 层与运营层并存，由 resolver 按层序裁决），
完整性检查器**没有**把它们计入重复/冲突。所以这两个指标保持为 2 是正确的。

## 4. 清理后的残留（诚实说明）

清理完成后 `petaccess` **仍然**保留：

- **5 个 demo seed 场所**，名字里带「测试」「演示」：云栖中心·测试商场、星河咖啡·测试店、
  星河咖啡·栖霞分店、松风社区·演示、青岚公园·演示。它们属于 demo 种子，
  与 10 个真实场所一起被白名单排除。
- **3 个 `UNKNOWN` 场所**（按 §30/§58「UNKNOWN 不自动删除」）：
  `DBG咖啡1789275599`、`T商场6ad9c1`、`T3商场d14555`。

因此 §0「`petaccess` 只承载真实业务数据」本轮**未 100% 达成**——这是刻意的取舍，
不是遗漏。要真正达成需要人类决定 demo seed 的去留（见重复审计报告第 2 节的三选项）。
