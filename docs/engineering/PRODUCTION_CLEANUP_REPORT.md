# 生产库夹具清理报告（PRODUCTION_CLEANUP_REPORT）

- 轮次：`PRODUCTION_DATA_ISOLATION_AND_INTEGRITY_CLOSURE_R1`
- 目标库：`petaccess`（角色 `PRODUCTION`）
- 执行时间：2026-09-17（两批，各自独立授权 + 独立还原点）
- 结论：**两批均 committed，8 个 Batch-01B 对象零改动，无 UNKNOWN 记录被删除**

---

## 1. 授权与前置条件

授权条款 §27：可以执行真实 cleanup，但仅限 `CONFIRMED_TEST_FIXTURE`，且必须同时满足
「dry-run 已复核 / 备份与快照就位 / 目标确认为 petaccess / 清理计划确定性 / 生产批次对象已排除」。

| 前置条件 | 落实方式 | 状态 |
| --- | --- | --- |
| dry-run 已复核 | `CLEANUP_PLAN_DRY_RUN.json`，并重跑一次做结构比对（0 diff） | PASS |
| 备份与快照就位 | `petaccess_before_cleanup.dump`（`pg_dump -Fc`，1,645,813 B）+ `PROD_FINGERPRINT_A.json` | PASS |
| 目标确认 petaccess | `--confirm-database petaccess` + 服务端 `current_database()` 探针 | PASS |
| 计划确定性 | 同参数重跑，除 `at` 时间戳外逐字段相同 | PASS |
| 批次对象已排除 | 计划显式排除 8 个 Batch-01B 候选 + 5 条 base rule + 3 条 carve-out | PASS |

闸门实现：`DatabaseSafetyGuard.assert_production_cleanup_allowed()`。
这是**独立于通用破坏性断言的专用入口**——`PRODUCTION.destructive_allowed` 仍然恒为 `False`，
只有同时出示「备份文件存在 + 已审阅 dry-run 文件存在」的调用者才能通过，
不给任何其他工具开口子。

---

## 2. 第一批：业务层夹具（BATCH-01）

产物：`PRODUCTION_CLEANUP_EXECUTED.json` · 44 步 · 单事务 · `committed = true`

删除总量 **12,883 行**：

| 表 | 删除 | 表 | 删除 |
| --- | --- | --- | --- |
| `place` | 1,231 | `rule_exception` | 131 |
| `user` | 1,755 | `rule_candidate` | 412 |
| `source` | 1,355 | `evidence_bundle` | 700 |
| `access_rule` | 1,091 | `observation_claim` | 2,238 |
| `verification_event` | 1,228 | `source_artifact` | 700 |
| `media_object` | 384 | `boundary_preference` | 432 |
| `boundary_profile` | 294 | `observation_candidate` | 211 |
| `operator_claim` | 68 | `organization` | 211 |
| `policy_template` | 211 | `place_policy_binding` | 279 |
| `policy_template_rule` | 218 | `rule_condition` | 125 |
| `dispute_case` | 70 | `event_policy` | 68 |
| `source_monitor` | 85 | `watch_subscription` | 135 |
| `pet_profile` | 26 | | |

**保留核心对象**（提交后实测）：8 条 Batch-01B 候选仍 `PUBLISHED`、
5 条 base rule + 3 条 carve-out 仍 `current`、18 个场所、4 个账号、38 条候选、9,254 条审计。
`audit_log` 追加式，**一行未删**。

### 分类依据（不是"名字像测试就删"）

每条记录需要证据链支撑，四类信号：

- **E1 规范注册表字面量**：`FIXTURE_PLACES` / `FIXTURE_SOURCES` 里每个模式都带
  `tests/**` 的 `文件:行号` 出处（如 `E2E-A 告示咖啡` → `tests/integration/test_v05_e2e.py:20`）。
- **E2 测试主体**：`audit_log` 里的 actor 属于 25 个一次性测试账号族
  （`v05mod` / `evmod` / `mand` / `rb` / `exc` / `e2e` / `perf` / `复核员` …）。
- **E3 爆发窗口**：QA 集中跑批产生的创建时间簇。
- **E4 无真实所指**：来源签发方为 `云栖商业管理有限公司（演示）` / `测试条例（xxxxxx）` /
  `quality-baseline` 等。

`CONFIRMED_TEST_FIXTURE` 需要 E1，或 ≥2 条强信号。只满足弱信号的记为 `LIKELY`，
**不删**；无法判定的记为 `UNKNOWN`，**不删**。

清理前清单：1,231 `CONFIRMED` / 3 `UNKNOWN` / 10 `REAL_PRODUCTION` / 5 `HISTORICAL_GOVERNANCE`。
删除的只有 `CONFIRMED` 这一类。

---

## 3. 第二批：法律层残留（BATCH-02）

产物：`PRODUCTION_CLEANUP_BATCH02_EXECUTED.json` · 45 步 · `committed = true`

### 为什么需要第二批

第一批跑完，`TEST_FIXTURE_SOURCE_IN_PRODUCTION` 从 1,423 只降到 **68**，不是 0。
追下去发现一个结构性盲区：

- `jurisdiction_rule` **没有 `place_id`**，第一批的删除逻辑完全没碰到它；
- 而 `jurisdiction_rule.source_id` 对 `source` 是 **RESTRICT** 外键——
  于是 68 条 `jurisdiction_id='test-city'` / `authority='测试机关'` 的法律层行，
  把 68 条夹具 source 一起钉在了生产库里。

这两个字符串都是 `tests/integration/test_operator_contribution.py:236,246,247` 里的字面量，
`reviewed_by` 是一次性测试账号 UUID，且这批 source 除 `jurisdiction_rule` 外**无任何引用**。
证据充分，按 `CONFIRMED` 处理。

删除：**68 条 `jurisdiction_rule` + 68 条 `source` = 136 行**。
4 条 demo 法律层规则（`jurisdiction_id` 非 `test-city`）正确存活。

> **教训**：「某张表没被 FK 连到 place」不等于「这张表干净」。
> 清理必须沿着**外键引用图**走，而不是沿着"看起来和 place 有关"走。

### 同时修正的一个脚本缺陷

原 `run_plan` 先 `conn.commit()` 再跑 `reconcile_preconditions()`——
不变式失败时打印"事务已回滚"，数据其实已经落库，是**假回滚**。
改为把不变式校验作为 `precommit_check` 回调，在 COMMIT 之前判定，失败才 rollback。

另：不变式 `fixture_places == 0 → 拒绝` 会误伤后续批次（第二批时已无 fixture place 可证），
改为「计划要删 place 时才要求 fixture 证据」+「空计划拒绝提交」。

---

## 4. 清理前后对比

| 表 | 清理前 | 清理后 |
| --- | --- | --- |
| `place` | 1,249 | 18 |
| `user` | 1,759 | 4 |
| `source` | 1,449 | 26 |
| `access_rule` | 1,119 | 28 |
| `rule_exception` | 134 | 3 |
| `rule_candidate` | 450 | 38 |
| `evidence_bundle` | 733 | 33 |
| `audit_log` | 9,254 | 9,254（不删） |

完整性扫描 23 项，前后对比：

| 检查项 | 清理前 | 清理后 |
| --- | --- | --- |
| `TEST_FIXTURE_PLACE_IN_PRODUCTION` | 1,231 | **0** |
| `TEST_FIXTURE_SOURCE_IN_PRODUCTION` | 1,423 | **0** |
| `TEST_ACCOUNT_IN_PRODUCTION` | 1,636 | **0** |
| `PUBLISHED_WITHOUT_EVIDENCE` | 64 | **0** |
| `PUBLISHED_WITHOUT_SOURCE` | — | **0** |
| `PUBLISHED_WITHOUT_AUDIT` | 251 → 0（口径修正后） | **0** |
| `HOLD_OR_REJECTED_PUBLISHED` | 0 | 0 |
| `ORPHAN_RULE_EXCEPTION` | 0 | 0 |
| `SELF_SUPERSEDE` / `SUPERSESSION_CYCLE` | 0 | 0 |

---

## 5. 清理差异证明（A → B）

产物：`CLEANUP_DIFF.json` → **`CLEANUP_DIFF = PASS`**

| 断言 | 结果 |
| --- | --- |
| 没有任何表行数增长 | PASS（所有 delta ≤ 0） |
| 人工登记表 sha256 不变 | PASS |
| 批次清单 sha256 不变 | PASS |
| Batch-01B 对象集合不变 | PASS |
| 已发布 access_rule / rule_exception 集合不变 | PASS |
| 重复 current 组不变 | PASS |
| `access_rule` / `rule_exception` / `rule_candidate` 键集只减不增、只删不改 | PASS |
| 库身份（alembic / server）不变 | PASS |

---

## 6. 明确保留、本轮不删的东西

按 §30「UNKNOWN 不自动删除」，以下对象**故意留在生产库**，需要在后续轮次由人类裁决：

1. **3 个 UNKNOWN 场所**（证据不足，无法归类）：
   - `DBG咖啡1789275599`（`466969e5`）
   - `T商场6ad9c1`（`19db2566`，带 1 条 `dog`/`enter`/`prohibited` 规则）
   - `T3商场d14555`（`1aa219c1`，带 1 条同名规则）
2. **5 个 demo seed 场所**：`星河咖啡·测试店` / `星河咖啡·栖霞分店` / `青岚公园·演示` /
   `云栖中心·测试商场` / `松风社区·演示`。它们是发布前就存在的演示数据，
   其中 `青岚公园·演示` 承载 §29 的重复 current 问题，**删了就没有现场可复核**。
3. **4 条 demo 法律层规则**（`jurisdiction_rule`）。
4. **`audit_log` 全量 9,254 条**——追加式，不可删。

因此 §0「`petaccess` 只承载真实业务数据」**本轮未 100% 达成**，
剩余差额就是上面这 4 类。这是一个诚实的 limitation，不通过放宽判定标准来消化。

---

## 7. 还原方式

两批各有独立 `pg_dump -Fc` 还原点，按倒序回滚：

```bash
# 先撤第二批
docker cp artifacts/production_isolation/petaccess_after_batch01.dump petaccess-db-1:/tmp/r.dump
docker exec petaccess-db-1 pg_restore -U petaccess -d petaccess --clean --if-exists /tmp/r.dump

# 再撤第一批（回到最初状态）
docker cp artifacts/production_isolation/petaccess_before_cleanup.dump petaccess-db-1:/tmp/r2.dump
docker exec petaccess-db-1 pg_restore -U petaccess -d petaccess --clean --if-exists /tmp/r2.dump
```
