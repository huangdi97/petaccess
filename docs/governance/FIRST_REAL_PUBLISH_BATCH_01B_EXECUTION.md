# FIRST_REAL_PUBLISH_BATCH_01B_EXECUTION

**这是本项目第一次真实生产发布的执行报告。**

授权人：Human Reviewer `huangdi97`（`FIRST_REAL_PUBLISH_BATCH_01B_EXECUTION` 指令 §0）

```
REAL_PUBLISH_EXECUTED            = YES
TARGET_DATABASE                  = petaccess
SIGNED_REVISION                  = R2-FINAL-R3
HUMAN_REVIEWER                   = huangdi97
BATCH_ID                         = R2-FINAL-R3-BATCH-01B

BATCH_SELECTED                   = 8
REAL_ACCESS_RULE_CREATED         = 5
REAL_RULE_EXCEPTION_CREATED      = 3
REAL_NOOP_SECOND_RUN             = 8

HOLD_PUBLISHED                   = 0
REJECTED_PUBLISHED               = 0
DISNEY_PUBLISHED                 = 0
UNREACHABLE_EXCEPTION_PUBLISHED  = 0

RESOLVER_POST_REAL_PUBLISH       = PASS
ENGINE_CONSISTENCY_REAL          = PASS
CARVE_OUT_REACHABILITY_REAL      = PASS
ZERO_INERT_RULES_REAL            = PASS
EVIDENCE_LINKAGE_REAL            = PASS
SOURCE_LINKAGE_REAL              = PASS
AUDIT_LINKAGE_REAL               = PASS
CONSUMER_READ_PATH               = PASS
ADMIN_STATE_VERIFY               = PASS
PRODUCTION_IDEMPOTENCY           = PASS
WATCH_READY                      = PASS
PRE_POST_DIFF                    = PASS
FULL_REGRESSION                  = PASS

PILOT_REVIEW_PUBLISH_GATE        = PASS
30_50_PLACE_EXPANSION            = ALLOWED_NOT_STARTED
SEMANTIC_REMODEL_ISSUE           = OPEN
```

执行时间：`2026-09-17T07:18:43.380207+00:00`（发布事务）
证据目录：`artifacts/real_publish_batch01b/`

---

## 1. 授权边界（§0）

只执行了 `R2-FINAL-R3-BATCH-01B` 一个批次。没有：

- 扩大到其他 APPROVED candidate（`prepublish_evaluated = 8`，`publication_types` 只有这 8 条）
- 发布 Disney（`dl-pet-ban` / `dl-sd-op` 仍 `REVIEW_PENDING`，`published_rule_id = NULL`）
- 发布任何 HOLD / REJECTED（`hold_publishable = 0`，`rejected_publishable = 0`）
- 自动加入 deferred semantic-remodel candidate
- 修改 Human Signature（登记表 SHA256 发布前后一致：`bd216afd…`）
- 修改 Evidence / Scope / RuleLayer
- 进入 30–50 Place 扩量

## 2. 发布前冻结检查（§2）

| 项 | 值 |
|---|---|
| revision | `R2-FINAL-R3` |
| reviewer | `huangdi97` |
| 签署决策 | 23 APPROVED / 9 HOLD / 5 REJECTED |
| 清单 | `R2_FINAL_R3_BATCH_01B.json` |
| selected | 8 |
| AccessRule / RuleException | 5 / 3 |
| HOLD / REJECTED / Disney selected | 0 / 0 / 0 |
| UNREACHABLE / UNEVALUABLE selected | 0 / 0 |
| cross-layer | 0 |
| dependency_closed | true |
| 登记表 SHA256 | `bd216afd…`（发布后未变） |

## 3. 目标数据库安全（§3）

```
TARGET_DATABASE = petaccess
```

- `current_database()` = `petaccess`（不是 rehearsal / visual / dev / pilot clone）
- `DATABASE_URL`（`.env`）指向 `petaccess`；API 以 `--db-name petaccess` 启动；publisher 以 `--database-name petaccess` 运行 —— 三者同一库
- alembic head = `b8d2f4a1c556`，与仓库 `services/api/migrations/versions`（18 个 revision）算出的唯一 head **一致**
- DB connectivity PASS

## 4. 快照（§4 / §22）

- `PRE_PUBLISH_SNAPSHOT.json`（SHA `22adabd1…`）—— 脚本默认**拒绝覆盖**
- `POST_PUBLISH_SNAPSHOT_BATCH_01B.json`（SHA `5a997ac2…`）
- 两者由**同一脚本** `scripts/real_publish_snapshot.py` 生成，否则不可比

差异结果（`pre_post_diff.json`）：

```
access_rule current      810 -> 815   (+5)
rule_exception current    80 ->  83   (+3)
rule_candidate           438 -> 438   (0)
audit_log               8963 -> 8982  (+16 发布 +3 monitor 初始化)
candidates moved           8 条，全部是本批成员
added rules 所在场所       全部是这 3 个场所（无越界）
deferred 4 条             未动
register / manifest SHA   未变
alembic head              未变
```

## 5. 预检与 dry-run（§5 / §6）

当前时间重跑闸门：

```
EVALUATED = 8   PASS = 8   BLOCKED = 0
gate_status_counts = {'PASS': 8}
human_decisions   = {'APPROVED': 8, 'HOLD': 0, 'REJECTED': 0}
publication_types = {'CREATE_ACCESS_RULE': 5, 'CREATE_RULE_EXCEPTION': 3}
DRY_RUN_ZERO_DB_MUTATION = True
UNREACHABLE_SELECTED = 0
ZERO_INERT_RULES     = PASS
UNREACHABLE_APPROVED_CARVE_OUT =
    fp-pets-op-firstparty->fp-sd-op-firstparty -> SEMANTIC_REMODEL_REQUIRED
    lib-pets-op->lib-sd-op-guide               -> SEMANTIC_REMODEL_REQUIRED
integrity: SELF_SUPERSEDE 0 / DUPLICATE 0 / CROSS_LAYER 0 / CYCLE 0
```

两条不可达 carve-out 被正确记为 `SEMANTIC_REMODEL_REQUIRED`，**没有**阻断其 base 发布，也**没有**被规划为 `CREATE_RULE_EXCEPTION`。

## 6. 真实写入（§7 / §8）

```
published 8   failed 0   rejected 0   held 0
counts: access_rule current 810 -> 815
        rule_exception current  80 ->  83
```

| rule_id | 类型 | 对象 id | base |
|---|---|---|---|
| fp-legal-dog | CREATE_ACCESS_RULE | `cd9139a1-…` | — |
| fp-pets-op-firstparty | CREATE_ACCESS_RULE | `e34341ae-…` | — |
| lib-legal-dog | CREATE_ACCESS_RULE | `332f17b6-…` | — |
| lib-pets-op | CREATE_ACCESS_RULE | `aba9f752-…` | — |
| sb-legal-dog | CREATE_ACCESS_RULE | `2d77f4b6-…` | — |
| fp-sd-legal | CREATE_RULE_EXCEPTION | `db5299e2-…` | `cd9139a1-…` |
| lib-sd-legal | CREATE_RULE_EXCEPTION | `a9b5e259-…` | `332f17b6-…` |
| sb-sd-legal | CREATE_RULE_EXCEPTION | `bb0a8321-…` | `2d77f4b6-…` |

## 7. base 先于 exception（§9）

真实时间戳（`created_at`）：

```
fp-sd-legal  base 07:19:00.363865  exc 07:19:00.613711  base<=exc True  current/current
lib-sd-legal base 07:19:00.474549  exc 07:19:00.660493  base<=exc True  current/current
sb-sd-legal  base 07:19:00.566790  exc 07:19:00.701256  base<=exc True  current/current
```

## 8. 发布后数据库（§10）

```
orphan exception        = 0
self supersede          = 0
duplicate current rule  = 1  （发布前就存在，见 §14 发现 1）
8 条 candidate           = PUBLISHED
deferred 4 条            = REVIEW_PENDING / published_rule_id NULL
```

## 9. 解析器 / 引擎一致性（§11 / §12 / §13）

真实 `petaccess` 上的实测答案：

| 场所 | ordinary_pet | dog | guide_dog | police_dog | military |
|---|---|---|---|---|---|
| 费尔蒙 | prohibited | prohibited | **allowed（例外生效）** | prohibited | prohibited |
| 上海图书馆 | prohibited | prohibited | **allowed（例外生效）** | prohibited | prohibited |
| 星巴克臻选 | prohibited | prohibited | **allowed（例外生效）** | prohibited | prohibited |

- `mismatches = 0`，`RESOLVER_POST_REAL_PUBLISH = PASS`
- 四路引擎（domain resolver / effective-rules API / `/rules/evaluate` / AccessAnswer）`disagreements = 0`，`ENGINE_CONSISTENCY_REAL = PASS`
- place 级（不带 zone）仍为 `unknown` —— zone 规则没有被压平成 place 总状态
- 3/3 carve-out：`base_governs_carve_out_subject = True`，`exceptions_attached = 1`，`inert = 0`

## 10. 血缘与审计（§14 / §15）

- `EVIDENCE_LINKAGE = PASS`、`SOURCE_LINKAGE = PASS`、`AUDIT_LINKAGE = PASS`
- 8/8 可反查：Published object → Candidate → Human Review → EvidenceBundle → Artifact → Source
- 审计：5 `candidate.publish` + 3 `candidate.publish_exception` + 16 `candidate.transition`
- 3 条例外审计均带 `base_rule_id`
- **Human Reviewer 与 Execution Actor 分开记录**：8 条 transition note 署名 `huangdi97`；`actor_user_id` 有 3 个不同值（human / pipeline / publisher），8 条 `REVIEW_PENDING → APPROVED` before→after 状态对完整

## 11. 消费端 / Admin（§16 / §17）

- 三个场所：search 命中、place detail 200、effective-rules `allowed` 且 `applied_exceptions ≥ 1`、Why/解释步骤 ≥ 2、`/rules/evaluate` 有状态、regulations 与 answerability 200
- `CONSUMER_READ_PATH = PASS`
- Admin `/admin/candidates?review_status=PUBLISHED` **分页取全量 243 条**后确认 8 条均为 `PUBLISHED` 且带 `published_rule_id`

> 注意：第一版冒烟只看了第 1 页（50/438）就下了 PASS 结论 —— 那是**假阳性**（8 条都不在首页，`continue` 跳过了判定）。已改为按 `review_status` 过滤后翻完整页再判定。

## 12. 幂等（§18）

第二次 `--execute`：

```
published = 0   failed = 0
access_rule current 815、rule_exception current 83、audit_log 8979 —— 未变
dry-run: NOOP_COUNT = 8（全部 NOOP_ALREADY_EXISTS），CREATE 各 0
8 条的审计数仍为 5 / 3 / 16 —— 第二次没有伪造 publish
```

`PRODUCTION_IDEMPOTENCY = PASS`

## 13. 回滚 / Watch（§19 / §20）

- **没有**在生产上执行回滚。只记录了入口与 ID：
  - AccessRule：`PATCH /api/v1/rules/{rule_id}`
  - RuleException：`POST /api/v1/admin/rule-exceptions/{id}/transition`
  - 需回滚的 5 个 rule id 与 3 个 exception id 已写入 `REAL_PUBLISH_RECEIPT.json`
  - 回滚 / 替换 / Watch 三项在 `petaccess_publish_rehearsal_r3` 上已演练 PASS
- Watch：3 个 source 各建了 1 个 SourceMonitor（经真实 admin 接口）。**没有触发 check，没有制造假的来源变化，没有发任何通知。**
  - 法律源 `f20bdb2c-…` 原本已有 5 个 monitor，现 6 个

## 14. 本轮真实发现（不粉饰）

**发现 1：一条发布前就存在的重复 current 规则**

`青岚公园·演示` 某 zone 上有 2 条 `ordinary_pet / walk / rule_layer NULL` 的 current AccessRule（不同 source，均创建于 2026-09-12）。**PRE 快照里同样存在**，本批未引入、未改动。按 §10 严格说"不得存在 duplicate current"，但它是既有状态，不在本批授权范围内 —— 记为 open，不自动修。

**发现 2：一条测试硬编码了"还没发布过"的状态**

`tests/integration/test_publish_exception.py::test_the_cli_dry_run_leaves_the_database_untouched`
断言全登记表 dry-run 的 `rule_exception_create_count == 11`。第一次真实发布后，同样命令得到 **6**：

- 3 条已发布 → NOOP
- 2 条（`fp-sd-op-firstparty` / `lib-sd-op-guide`）因 base 已发布被 planner 阻断（"例外不得被间接带入"）

这是**测试缺陷**，不是产品回归。我没有把 11 改成 6，而是把断言改为从状态推导的不变量：

> carve-out 只有在同一次运行也在创建其 base 时才可被创建

并补充"每条 APPROVED 行必须恰好被计入 create / NOOP / BLOCKED 之一"。现在发布前后都成立。

**发现 3：defer 的两条 carve-out 现在被 planner 阻断（值得留意）**

`fp-sd-op-firstparty` / `lib-sd-op-guide` 因 base 已发布（NOOP）而在全登记表模式下变 BLOCKED。对这两条来说结果是对的 —— 它们本来就是不可达的惰性规则，不该被发布。

但同一个阻断条件对**可达**的 carve-out 也会生效：如果哪天某条可达 carve-out 被留在批次外而其 base 先发布，它也无法再通过全登记表路径补发，只能走显式批次。这是既有设计（"真实发布 = 显式 batch manifest"）的推论，但值得独立记一笔。

**发现 4：基础设施不稳定**

执行期间 Docker Desktop 反复退出（WSL 后端随工具调用结束被回收），数据库一度不可达。处理方式：改用常驻 backend 进程恢复后，在**同一次调用内**确认 `current_database() = petaccess` 且 alembic head 匹配，再执行唯一一次写入。写入本身在 DB healthy 状态下完成，事务要么整体提交要么整体回滚。

**发现 5：PRE 快照的 resolver 查询形状**

第一版快照脚本把工作犬写成 `service_role: "guide_dog"`，规范写法是 `service_role: "working"` + `declared_role: "guide_dog"`。因为发布前这 3 个场所 **0 条 current 规则**（已用 PRE 快照数据证明），所以 PRE 的 `unknown` 结论仍成立。脚本已修正，POST 用的是规范形状。

**发现 6：回归套件会往 `petaccess` 写测试夹具**

POST 快照之后又跑了全量回归，库从 815/83 涨到 843/87。查证结果是**全部为测试夹具**，产生于 07:32–07:40（pytest 集成测试 + E2E 期间）：`回滚测试场所*`、`强制级别测试场所*`、`例外测试商场*`、`例外隔离商场*`、`E2E-A 告示咖啡`、`E2E-C 监控公园`、`E2E-D 线索书店咖啡`、`认领演示商店`、`质量基线测试咖啡`。

已确认它**没有碰到本批发布结果**：

- 8 个发布对象的 `updated_at` 仍是 `07:19:00`（发布时刻），全部 `current`
- 三个试点场所在回归期间新增规则数 = **0 / 0 / 0**
- 8 条 candidate 仍全部 `PUBLISHED`
- deferred 4 条仍 `REVIEW_PENDING` / `published_rule_id = NULL`

这是既有设定的推论 —— 回归套件与"生产"共用同一个 `petaccess` 库（发布前 810 条 current 规则里就含这类夹具）。**不是本轮引入的问题**，但它意味着正式库与测试库未分离，跑一次回归就会往正式库写演示数据。建议后续单独处理，本轮不在授权范围内。

## 15. 全量回归（§23，本轮真实数字）

| 门禁 | 结果 |
|---|---|
| pytest | **606 passed** |
| ruff check | All checks passed |
| ruff format --check | 179 files already formatted |
| mypy | Success: no issues found in 77 source files |
| ESLint | pass |
| Prettier | All matched files use Prettier code style |
| H5 build（E2E 版） | pass |
| H5 build（视觉版） | pass |
| Admin build | pass |
| E2E | **18 passed** |
| visual | **47 passed** |
| a11y | **TOTAL issues: 0** |
| Publisher critical ×3 | **109 passed / 109 passed / 109 passed** |

本轮改动的文件：

- `scripts/real_publish_snapshot.py`（新增）
- `tests/integration/test_publish_exception.py`（把硬编码数改为状态推导的不变量）
- `artifacts/real_publish_batch01b/*`（证据）

`apps/` 下零改动。

## 16. 门禁结论（§24）

全部满足：签名在位、预检当前 PASS、真实发布完成、5+3 正确、解析器 PASS、引擎一致性 PASS、carve-out 可达 PASS、Evidence / Source / Audit 血缘 PASS、消费端读路径 PASS、Admin 状态 PASS、生产幂等 PASS、回滚/替换/Watch 演练已 PASS、全量回归绿。

```
PILOT_REVIEW_PUBLISH_GATE = PASS
```

## 17. 后续状态（§25 / §26）

```
30_50_PLACE_EXPANSION = ALLOWED_NOT_STARTED
```

状态从 `NOT_ALLOWED` 更新为 `ALLOWED_NOT_STARTED`。**本轮不启动扩量**，等下一轮单独授权。

```
SEMANTIC_REMODEL_ISSUE = OPEN
```

不因本次发布成功而关闭：

- Disney：`dl-pet-ban` / `dl-sd-op`
- 运营层不可达 carve-out：`fp-sd-op-firstparty` / `lib-sd-op-guide`
- 相关 HOLD：`lib-sd-op-police` / `lib-sd-op-military`

详见 `docs/governance/OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL.md`（Option 1/2/3 仍未决定）。

---

## 证据文件

| 文件 | 内容 |
|---|---|
| `artifacts/real_publish_batch01b/REAL_PUBLISH_RECEIPT.json` | §21 发布回执 |
| `artifacts/real_publish_batch01b/PRE_PUBLISH_SNAPSHOT.json` | §4 发布前快照 |
| `artifacts/real_publish_batch01b/POST_PUBLISH_SNAPSHOT_BATCH_01B.json` | §22 发布后快照 |
| `artifacts/real_publish_batch01b/pre_post_diff.json` | §22 差异比对 |
| `artifacts/real_publish_batch01b/prepublish_real_dryrun.json` | §5/§6 预检 |
| `artifacts/real_publish_batch01b/real_execute_stdout.txt` | §7 真实执行回执 |
| `artifacts/real_publish_batch01b/PUBLISHED_RULES_SNAPSHOT_BATCH_01B.json` | 发布对象快照 |
| `artifacts/real_publish_batch01b/real_execute_second_run.txt` | §18 第二次执行 |
| `artifacts/real_publish_batch01b/idempotency_dryrun.txt` | §18 NOOP=8 |
| `artifacts/real_publish_batch01b/real_verify_batch01b.json` | §11–§15 验收 |
| `artifacts/real_publish_batch01b/consumer_smoke.json` | §16 消费端冒烟 |
| `artifacts/real_publish_batch01b/watch_init.json` | §20 Watch 初始化 |
| `artifacts/real_publish_batch01b/a11y_real_publish.json` | §23 a11y |
