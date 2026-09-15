# ENV01_RESOLUTION_REPORT.md

> 生成时间：2026-09-14（GMT+8）
> 真实基线 HEAD：`53c4c0339ffcaea54b7c4cced46ad7edd28d7bb1`
> 触发：用户启动 Docker Desktop，指令「继续 ENV-01」

---

## 0. 结论先行

| 项 | 判定 |
|---|---|
| `ENV-01`（无容器运行时 ⇒ 无 PostGIS/Redis/MinIO） | **RESOLVED** |
| `alembic upgrade head` | **PASS** → head `f4c9d2e7a831` |
| 迁移 **up / down / up** 往返 | **PASS** |
| 全量 `pytest`（**不 deselect** 数据库用例） | **PASS — 319 passed / 0 failed** |
| PostGIS / Redis / Celery / MinIO 冒烟 | **PASS**（`all_ok: true`） |
| Playwright 全量 E2E | **PASS — 14 passed / 0 failed**（此前 BLOCKED_EXTERNAL） |
| Admin 端到端（Rollback / Supersession / Evidence Review / Data Quality） | **PASS** — 新增 5 个 L1 回滚集成测试；KPI 全部真实；修正 `ROLLBACK_RUNBOOK.md` 的不可执行程序 |
| `PILOT_REVIEW_PUBLISH_GATE` | **仍 NOT PASS** — 仅剩 `GOV-01`（缺具名人类评审员） |

**关键判断**：ENV-01 一解除，真实数据库立刻暴露出 **6 个此前不可能发现的真实缺陷**
（含 1 个会把法定规则静默降级的数据缺陷）。全部已修复并留测试/迁移/审计。这印证了
"不得以 deselect 宣称 PASS" 的纪律——若当初把 DB 用例 deselect 掉，这 6 个缺陷会全部带入生产。

---

## 1. 依赖栈就绪与验证

```
$ docker version          → Client 29.2.1 / Server Docker Desktop 4.64.0 (linux/amd64)
$ docker-compose up -d
  Container petaccess-db-1     Started
  Container petaccess-redis-1  Started
  Container petaccess-minio-1  Started

$ docker-compose ps
petaccess-db-1     postgis/postgis:17-3.5   Up (healthy)   0.0.0.0:5432->5432/tcp
petaccess-minio-1  minio/minio:latest       Up             0.0.0.0:9000-9001->9000-9001/tcp
petaccess-redis-1  redis:7-alpine           Up (healthy)   0.0.0.0:6379->6379/tcp
```

| 依赖 | 版本 / 证据 |
|---|---|
| PostgreSQL | **17.5**（Debian），`psycopg` 连接 **0.19s** |
| PostGIS | **3.5.2**（GEOS 3.9.0 / PROJ），扩展 `postgis` + `pg_trgm` 1.6 |
| Redis | **7.4.11**，PING / SET / GET 通过 |
| MinIO | bucket `petaccess-dev` 存在；put → presigned URL → remove 往返通过 |
| Celery | worker `--pool=solo` 就绪；任务往返 `{'status': 'worker_alive'}` |

`GET /health/components` → **`all_ok: true`**（postgres / redis / minio / celery nodes=1）。

**功能性**（非仅可达）冒烟：
- 真实空间查询：`/places/nearby?lat=31.2304&lng=121.4737&radius_m=15000` → 13 个场所，含真实距离
- MinIO：`put_object` → `presigned_get_url` → `remove_object`
- Celery：经 live worker 的 `healthcheck_task` 往返

---

## 2. 迁移与 schema

```
$ alembic current   (前) → b5e8d2c4a710
$ alembic heads          → f4c9d2e7a831 (head)
$ alembic upgrade head   → 5 个迁移依次执行，全部成功
```

**up / down / up 往返**（用户明确要求）：

```
head(f4c9d2e7a831) → downgrade c81e02ba6d45 → upgrade head   均 PASS
```

往返后核对：列已正确删除/重建、`rule_exception` 表删除/重建、数据行保留
（`access_rule` 163 行不变）、回填重新生效。

回填一致性核对（关键不变量）：

| 表 | 结果 |
|---|---|
| `access_rule` | 116 行 `rule_layer IS NULL` → `mandatory_level` 保持 NULL（**刻意不猜**）；47 行 OPERATOR_POLICY → operator_discretion |
| **`LEGAL` 且 `mandatory_level IS NULL`** | **0**（关键不变量成立） |
| `rule_candidate` | 145 行 OPERATOR_POLICY → operator_discretion |
| `source_artifact` | evidence_strength 回填（primary_direct 15 / search_snippet 4 / secondary_reputable 3 / social_lead 1） |

---

## 3. 解除过程中发现并修复的缺陷

真实数据库一接入，以下 6 个缺陷立即暴露。**它们在 deselect 数据库用例的做法下全部不可见。**

### 缺陷 1 — 迁移约束名双前缀（7 个，跨 4 张表）

**现象**：`ck_access_rule_ck_access_rule_mandatory_level`（应为 `ck_access_rule_mandatory_level`）。

**根因**：4 个手写迁移把**已带前缀**的名字直接传给 `op.create_check_constraint` /
`sa.CheckConstraint`，未用 `op.f()` 标记为字面名，于是命名约定
（`ck_%(table_name)s_%(constraint_name)s`）二次加前缀。仓库自动生成的迁移都用 `op.f()`，
手写的 4 个没有。

**影响**：`alembic` 路径与 `metadata.create_all` 路径的约束名发散；`alembic check`/autogenerate
会报假差异；任何按模型名引用约束的工具失效。**降级路径会直接失败**（实测：
`constraint "ck_rule_candidate_mandatory_level" does not exist`）。

**修复（双管齐下）**：
1. 修正 4 个迁移源（`op.f(...)`）→ **全新库**得到正确名字；
2. 新增幂等修复迁移 `f4c9d2e7a831`：仅重命名已受影响的库中的 7 个遗留约束，
   同时存在性判定（全新库为 no-op），**只改名字、不动数据与表达式**。

修复后：`REMAINING DOUBLE-PREFIXED: 0`。

### 缺陷 2 — 33 条候选的规范层级/规范力陈旧（**最严重**）

**现象**：登记表声明 **LEGAL 16 条**，但库中这 33 条候选**全部**为
`OPERATOR_POLICY` / `operator_discretion`。

**根因**：这些候选在 `rule_candidate.rule_layer` 列存在**之前**就已入库，列因此取了
`server_default='OPERATOR_POLICY'`；而 `real_pilot_ingest.py` 按 manifest 键**幂等跳过**
已存在候选，重跑不会校正。

**影响**：`publish()` 写入的是**候选行**的值。因此即便评审员签署登记表并发布，
**16 条法定规则也会被静默降级为运营方政策**——法定 floor 失效。这正是 ADR-023 要防的
「静默降级」，只是这次经由**陈旧数据**而非缺列到达。

**修复**：
- `scripts/backfill_candidate_rule_layer.py`（原仅处理 layer）扩展为**同时校正
  `mandatory_level`**，沿用入库时的确定性映射（LEGAL → mandatory，其余 →
  operator_discretion，证据显式值优先）；
- 全部经 **live API** 写入（`/rule-layer` + `/mandatory-level`），因此**逐条留审计**；
  已发布候选被端点拒绝（不可原地改写）；
- 执行结果：layer **18 条变更 / 15 条已正确**，level **16 条变更 / 17 条已正确**，**0 失败**；
- 复核：`LEGAL/mandatory 16`、`OPERATOR_POLICY/operator_discretion 15`、
  `TEMPORARY_POLICY/operator_discretion 2`，`LEGAL 缺 level = 0`；
  审计留痕 `candidate.set_rule_layer` 18 条、`candidate.set_mandatory_level` 20 条。

### 缺陷 3 — 发布门禁只信库中层级

**现象**：`publish_reviewed_r1.py` 的预检只读**登记表**；发布后只校验
`mandatory_level`，且**发布之后**才发现不一致（此时规则已生效）。`rule_layer` 从不校验。

**修复**：
- 新增 `fetch_candidate_state()`：分页拉取库中候选（端点 `limit` 上限 200，已改为分页，
  避免队列增长后静默漏检）；
- `preflight()` 增加**登记表↔库一致性**校验：`rule_layer` 或 `mandatory_level` 任一不一致
  → **硬拒绝**并提示先跑 backfill；
- `--execute` 模式强制要求库状态可读（读不到即退出码 4），杜绝「未校验即发布」；
- 发布后**同时**校验 `rule_layer` 与 `mandatory_level`（新增 `verify_rule_layer` 失败项）。
- 新增 8 个单元测试（`tests/unit/test_publish_preflight_crosscheck.py`）固定该守卫，
  含「库中陈旧层级必须拦住发布」与「缺少库状态时跳过校验」两类。

### 缺陷 4 — `RuleIn` 缺遗留值归一化

**现象**：`POST /rules` 传 `mandatory_level="discretionary"` → **422**；
但读取路径（`RuleOut`）能正常归一化。读写词表不一致。

**根因**：归一化只加在 `RuleOut` 上，`RuleIn` 声明的是裸枚举。

**修复**：抽出共享注解类型 `NormalizedMandatoryLevel`
（`Annotated[MandatoryLevel, BeforeValidator(...)]`，`app/schemas/common.py`），
在 `RuleIn` 与 `RuleOut` 共用，并删除 `RuleOut` 的重复校验器。
未知值仍被枚举校验拒绝（符合预期）。

### 缺陷 5 — `/places/{id}/extras` 抛 `AttributeError`

**现象**：`AttributeError: type object 'AccessPath' has no attribute 'zone_id'`。

**根因**：辅助函数 `_in_place()` 假定所有模型都有 `zone_id`；`AccessPath` 只按场所归属
（入口之间的路径不属于单个分区）。

**修复**：`_in_place(model, *, zoned=True)`，`AccessPath` 显式 `zoned=False`。
补集成测试 `tests/integration/test_place_extras.py`（5 用例）——该端点此前**零测试覆盖**，
正是漏网原因。

修复后真实数据验证：星河咖啡 coexistence 4、青岚公园 amenities 2 + event 1、
云栖中心 entrances 1 + access_paths 1。

### 缺陷 6 — Place Detail 分区徽标复用场所级结果

**现象**：E2E 点击「查看」后，室内堂食区显示 **「尚未核验」**，而 API 明确返回
该分区 `effect = prohibited`。

**根因**：分区徽标读取的是**场所级** `effective`（其 effect 为 `unknown`），
从未按 `zone_id` 评估。这是**会误导用户**的正确性问题：把「明确限制」显示成「尚未核验」。

**修复**：新增按需分区评估（`toggleZone()` + `zoneEffects` 缓存 + `zoneSemantic()`），
失败时诚实显示 UNKNOWN 并标注「该分区未能取得结论」。

**E2E 修正**：`h5-journey.spec.ts` 相应更新为展开分区后断言 `明确限制`；
另修正 3 处因 UI-CORE-CLOSURE 重写而漂移的断言（首页默认视图、`我的宠物：`文案、快速确认按钮文案）。

### 缺陷 7 — E2E 无法运行（配置缺口）

**现象**：`vite preview` **不继承** `server.proxy`，而 H5 产物用相对 `/api/v1`，
导致所有数据驱动断言 404 —— 看起来像应用缺陷。

**修复**：
- `vite.config.ts` 同时声明 `preview.proxy`，目标可用 `VITE_API_PROXY` 覆盖；
- E2E 产物以**绝对基址**构建（API 的 CORS 已放行 `http://127.0.0.1:5175`），
  流程写入 `README.md`，可复现。

---

## 4. 验证门禁（本轮实测）

| 门禁 | 命令 | 结果 |
|---|---|---|
| 全量 pytest（含 DB） | `pytest` | **PASS — 319 passed / 0 failed** |
| Ruff lint | `ruff check services/api services/worker tests scripts` | **PASS** |
| Ruff format | `ruff format --check ...` | **PASS — 131 files** |
| Mypy | `mypy .`（services/api） | **PASS — 76 source files** |
| Playwright（全量） | `playwright test` | **PASS — 14 passed / 0 failed** |
| H5 构建 | `vue-tsc --noEmit && vite build` | **PASS** |
| ESLint / Prettier | `eslint .` / `prettier --check .` | **PASS** |
| 迁移往返 | `alembic downgrade … && alembic upgrade head` | **PASS** |

**测试计数变化**：306 → **319**（+8 预检守卫单测、+5 extras 集成测试）。
其中 DB 依赖用例 **从 0 可执行变为 75 个全部通过**（55 integration + 20 `db_session`）。

---

## 5. Admin 端到端验证（真实 DB）

用户原指令「三、Admin：继续 Publish、Rollback、Supersession、Evidence Review、Data Quality、
E2E on real DB」——ENV-01 解除后具备执行条件。结果如下。

### 5.1 能力盘点与实测

| 能力 | 端点 | 实测 |
|---|---|---|
| Publish | `POST /admin/candidates/{id}/publish` | 已有 69 条 PUBLISHED（历史批次）；R1 的 33 条受 GOV-01 阻塞，未动 |
| **Rollback（L1 撤回）** | `PATCH /rules/{rule_id}` `{"status":"withdrawn"}` | **新增 5 个集成测试，全绿**（见 5.2） |
| Supersession | 由 `publish()` 自动处理（同来源同归属同 scope/action） | 已由 `tests/integration/test_v05_e2e.py::test_e2e_c` 覆盖 |
| Evidence Review | `/admin/audit`、`/admin/ai-queue`、`/admin/observations`、`/admin/conflicts` | 全部 200，返回真实数据 |
| Data Quality | `/admin/quality` | 200，KPI 全部真实（见 5.3） |
| Worker 可观测 | `/admin/worker/jobs` | `workers_online: ['pa-smoke@Kaiser']`、`failed_jobs: []` |

### 5.2 发现：`ROLLBACK_RUNBOOK.md` 的 L1 程序**不可执行**

手册 §2 引用的 `POST /api/v1/admin/rules/{rule_id}/withdraw`、`GET /api/v1/admin/rules/{rule_id}`
与审计动作名 `rule.withdraw` **均不存在**；§3 引用的 `scripts/list_batch_rules.py`、
`scripts/withdraw_batch.py` 也不存在。若照手册在事故中执行，会直接 404。

**根因**：`rules.admin = APIRouter(tags=["admin:rules"])` **没有** `prefix="/admin"`。
本仓库 6 个模块（rules/places/sources/operators/regulations/disputes）的 admin 路由都无前缀，
只有 `v05.admin` 与 `admin.py` 有 —— 手册作者按后者推断，于是写错了路径。

**真实能力**：`PATCH /api/v1/rules/{rule_id}` + `{"status":"withdrawn"}`，审计为 `rule.update`。

**处置**：
1. 新增 `tests/integration/test_rollback_l1.py`（**5 用例，真实 DB**）固定手册承诺的行为：
   - 撤回后场所答案回落 **UNKNOWN 而非 allowed**（手册明示的验收判据）
   - 行与证据链**保留**（撤回 ≠ 删除），仍出现在 `/places/{id}/rules` 且 `status=withdrawn`
   - `audit_log` 出现 `rule.update`，含 `before_state.status=current` / `after_state.status=withdrawn`
   - 匿名调用被拒（401/403）且规则不受影响
   - 不存在的规则 → 404
2. 修正 `ROLLBACK_RUNBOOK.md`：§2 改为真实路径与真实审计动作名；§3 如实标注 L2 脚本缺失、
   快照文件按需生成；L3 健康检查路径 `/api/health` → `/health`；新增 §8「已知不一致」。
3. 演练状态表更新：**L1 从 `NOT_RUN` → 真实 DB 已演练**。
4. 登记技术债 TD-20（admin 前缀不一致，属破坏性变更，不顺手改）、TD-21（L2 脚本缺失）、
   TD-22（文档一致性无自动校验）。

### 5.3 数据质量 KPI（真实数据实测）

```json
{
  "rules":       {"total": 252, "current": 207, "source_coverage": 1.0, "never_verified": 196},
  "candidates":  {"total": 180, "by_status": {"REVIEW_PENDING": 33, "APPROVED": 44,
                                              "PUBLISHED": 69, "REJECTED": 27, "MATCH_PENDING": 7},
                  "by_layer": {"LEGAL": 23, "OPERATOR_POLICY": 155, "TEMPORARY_POLICY": 2},
                  "evidence_coverage": 0.717},
  "evidence":    {"artifacts_total": 264, "bundles_total": 272,
                  "hash_coverage": 0.676, "license_coverage": 0.934},
  "provenance":  {"sources_total": 396, "official_ratio": 0.72},
  "contributions": {"observations": 718, "verifications": 384},
  "queues":      {"operator_claims_pending": 1, "disputes_open": 1}
}
```

注意 `by_layer.LEGAL = 23`：**backfill 生效的直接证据**（修复前该值仅为 4）。
`conflicts = 0`、`failed_jobs = []`。

### 5.4 文档一致性审计（附带）

对全部 `*.md` 做了两次机器扫描：
- 引用的 `scripts/*` → 16 个引用中**仅 2 个缺失**（即 L2 两脚本，已如实标注）；
- 引用的 `/api/v1/...` → 20 条引用中**仅回滚端点一处为真实漂移**（已修），其余为前缀/模块引用。

即：除本轮回滚程序外，未发现其它端点级文档漂移。

---

## 6. 本轮附带修复的门禁范围缺口

`scripts/lint.sh` 只覆盖 `services/api services/worker tests`，**未含 `scripts/`**，
因此 6 处 E501（1 处为本轮引入、5 处为此前遗留）长期未被门禁捕获。
已修复全部 6 处（用隐式字符串拼接，**保证生成物逐字节不变**——已用 diff 验证
`RULE_REVIEW_SHEET_R1.md` 输出一致），并把 `scripts` 纳入 `lint.sh`。

---

## 7. 剩余阻塞

| ID | 内容 | 状态 |
|---|---|---|
| **GOV-01** | 缺具名人类评审员对 33 条候选逐条签署 | **仍成立**（治理红线，AI 不得代签） |
| TD-20 | admin 路由前缀不一致（破坏性变更，不顺手改） | 已登记 |
| TD-21 | L2 批次回退脚本缺失（无已发布批次可演练） | 已登记 |
| BLK-LEGAL-01 | 法律文本未经执业律师审阅 | 仍成立 |
| BLK-PLAT-01 | 平台审核未提交 | 仍成立 |
| B-01…B-07 | 工具链 / 凭证 / 资质 | 仍成立 |

**`PILOT_REVIEW_PUBLISH_GATE = NOT PASS`**：ENV-01 已解除，写库能力已就绪且经往返验证；
唯一剩余条件是**人类签署**。签署后即可执行：

```bash
python scripts/publish_reviewed_r1.py --dry-run      # 现含登记表↔库一致性校验
python scripts/publish_reviewed_r1.py --execute --reviewer "<具名>"
```

预检现在会**双重把关**：既检查登记表本身（签署/弱证据/LEGAL 必须有 level/批次上限），
也检查**库中候选与登记表一致**。

---

## 8. 当前运行中的进程（供后续使用）

| 服务 | 地址 | 说明 |
|---|---|---|
| PostGIS / Redis / MinIO | 5432 / 6379 / 9000-9001 | `docker-compose` 托管，由用户启动 |
| API | `http://127.0.0.1:8010` | 本轮为验证临时启动（`uvicorn`） |
| Celery worker | — | 本轮为验证临时启动（`--pool=solo`） |

临时启动的 API 与 worker 属验证用途；正式开发请按 `README.md` 的
「E2E 前置」或 `scripts/dev.sh` 重启。
