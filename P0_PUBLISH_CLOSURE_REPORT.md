# P0_PUBLISH_CLOSURE_REPORT.md

> 生成时间：2026-09-14（GMT+8）
> 真实基线 HEAD：`53c4c0339ffcaea54b7c4cced46ad7edd28d7bb1`
> 上一份生产就绪报告（`FINAL_PRODUCTION_READINESS_REPORT.md`）指向的 `716b163` **早于**当前 HEAD，
> 因此本报告以 HEAD `53c4c03` 为唯一真实基线，不沿用旧报告的结论。
> **2026-09-14 更新**：ENV-01 已解除，本报告 §2/§5/§6/§8 已据实刷新。详见 `ENV01_RESOLUTION_REPORT.md`。

---

## 0. 结论先行

| 项 | 判定 |
|---|---|
| `BLK-LAYER-02`（法定禁止可被低层规则覆盖） | **FIXED**（ADR-023，Schema 修复，非"已知限制放行"） |
| 迁移约束命名缺陷（双前缀，7 个） | **FIXED**（ADR-024，`f4c9d2e7a831`） |
| 候选层级/规范力陈旧（会把 16 条法定规则静默降级） | **FIXED**（backfill 执行 + 发布预检双重把关） |
| 33 条 RuleCandidate 人工审核工作流 | **READY_FOR_SIGNOFF**（工作表已生成且可复现；AI 未代签） |
| 第一批真实 Publish | **READY（待签署）** — 写库能力已就绪并经 up/down/up 验证 |
| `PILOT_REVIEW_PUBLISH_GATE` | **NOT PASS**（仅剩 GOV-01） |
| 30–50 Place 扩量 | **未启动**（按纪律被 P0 Gate 阻塞） |

**关键判断**：`BLK-LAYER-02` 是本轮唯一一个"必须先用 Schema 修复、不得以已知限制放行"的架构缺陷。
它已按用户指令用通用结构修复并留 ADR。**ENV-01 解除后**，剩余阻塞**仅为 GOV-01**（人），
不是代码或环境缺口。

---

## 1. 基线核对（先执行，未改动任何文件）

```text
$ git status --short
 M DECISIONS.md
 M apps/client-h5/src/components/MockMap.vue
 M apps/client-h5/src/views/HomeView.vue
 M apps/client-h5/src/views/PlaceView.vue
 M apps/client-h5/src/views/SearchView.vue
 M docs/reality_audit/review_decisions_r1.json
 M packages/client-core/src/api/client.ts
 M packages/client-core/src/platform/map.ts
 M scripts/gen_review_decisions_r1.py
 M scripts/publish_reviewed_r1.py
 M scripts/real_pilot_ingest.py
 M services/api/app/api/v1/rules.py
 M services/api/app/api/v1/v05.py
 M services/api/app/db/seed.py
 M services/api/app/models/enums.py
 M services/api/app/models/rule.py
 M services/api/app/models/v05.py
 M services/api/app/rulespec/petaccessjson.py
 M services/api/app/rulespec/v05_resolver.py
 M services/api/app/schemas/rules.py
 M services/api/app/services/candidate_service.py
 M services/api/app/services/publish_gate.py
 M services/api/app/tools/reality_audit.py
 M tests/unit/test_publish_layer_integrity.py
?? RULE_REVIEW_SHEET_R1.md
?? apps/client-h5/src/components/{BottomSheet,FilterChips}.vue
?? apps/client-h5/src/views/{NotificationsView,PrivacyView,PetProfileView,SettingsView}.vue
?? scripts/gen_review_sheet_r1.py
?? services/api/migrations/versions/e3b7a1c4f920_access_rule_mandatory_level.py
?? tests/{unit,integration}/test_mandatory_level.py
?? *.patch (4 个，前置会话遗留)

$ git diff --stat      → 空（工作区相对 index 无未暂存差异时为空）
$ git rev-parse HEAD   → 53c4c0339ffcaea54b7c4cced46ad7edd28d7bb1
$ git log --oneline -8
53c4c03 docs(p2/p3): complete the spec-required UX deliverables; refresh state and readiness docs
716b163 feat(p3/p4): admin consumes the design system; UI state completeness; real data-quality KPIs
97ff43e docs: correct two self-reported verification figures after re-measurement at HEAD 078f33d
078f33d docs: production launch pack, compliance gate, runbooks, legal drafts; final readiness report
a970a80 ui: design-token system + neutral status semantics + copy guard (P3 increment)
147f3e4 p0: review worksheet for 33 real candidates + gated publish toolchain; fix rule_layer loss on publish
08ee60c reality: PILOT-REVIEW-AND-SCHEMA-FIX-01 — RuleException mechanism ...
e299fab reality: PART B real-data pilot (10 Shanghai places) ...
```

---

## 2. P0-1 环境状态（Docker / PostGIS / Redis / MinIO）

### 2026-09-14：**ENV-01 已解除**

用户启动 Docker Desktop 后，依赖栈已就绪并通过验证：

| 探针 | 结果 |
|---|---|
| `docker version` | Client 29.2.1 / Server Docker Desktop 4.64.0（linux/amd64） |
| `docker-compose up -d` | `petaccess-db-1`（postgis/postgis:17-3.5，healthy）、`petaccess-redis-1`（redis:7-alpine，healthy）、`petaccess-minio-1`（运行中） |
| 宿主端口映射 | 5432 / 6379 / 9000-9001 |
| PostgreSQL + PostGIS | **17.5 + 3.5.2**（+ pg_trgm 1.6）；`psycopg` 连接 **0.19s** |
| Redis | **7.4.11**（PING/SET/GET 通过） |
| MinIO | bucket `petaccess-dev` 可读写（put / presigned / remove 往返） |
| Celery | worker `--pool=solo` 任务往返通过 |
| `/health/components` | **`all_ok: true`** |

因此以下现已**全部可执行**：`alembic upgrade head`、全量 `pytest`（含 DB）、
migration up/down/up、PostGIS/Redis/Celery/MinIO 冒烟。

### 解除前的阻塞记录（历史，保留以说明纪律）

`docker ps` → 命名管道不存在；`docker-compose v5.1.0` 在但守护进程不在；5432/6379/9000 无监听；
`psycopg` 连 `localhost:5432` → `ConnectionTimeout` **10.2s**；`sc.exe`/`wsl.exe` 被安全策略黑名单。

**处置纪律**：当时一律登记为 `BLOCKED_EXTERNAL`，**未以 deselect 后宣称 full PASS**。
这一纪律的价值在解除后立即显现——真实数据库一次暴露 **7 个**此前不可见的缺陷（见 §3.6）。

---

## 3. P0-2 BLK-LAYER-02 修复（核心交付）

### 3.1 缺陷本质

旧 resolver 的 `legal_mandatory` 分支要求 `mandatory_level == "mandatory"`，而 `AccessRule`
**根本没有这一列** ⇒ 对数据库来源的规则该分支**永不可达**。后果已被测试钉住：

> 运营方 `allowed` 规则会**胜过**《上海市养犬管理条例》第 23 条的法定禁止。

### 3.2 修复方案（通用结构，非特例补丁）

选择**方案 A：Schema 修复 + ADR**，明确**不采用**"按现状发布并登记为已知限制"。

| 层 | 变更 |
|---|---|
| 词表 | `app/models/enums.py` 新增一等公民 `MandatoryLevel`：`mandatory` / `advisory` / `operator_discretion`；`normalize_mandatory_level()` 归一化遗留值 `discretionary → operator_discretion` |
| Schema | `AccessRule.mandatory_level`（nullable, String(20)）+ CheckConstraint `ck_access_rule_mandatory_level`；`RuleCandidate.mandatory_level` |
| Resolver | `v05_resolver` 改为从 `app.models.enums` 导入词表（删除本地重复定义）；`_is_mandatory()` 走归一化；**法定强制禁止**与**法定强制条件**均构成 floor；遮蔽逻辑扩展 `drops_obligation` 分支；当存在 `mandatory_conditional` 时 effect 合成 `allowed → conditional` |
| 发布门禁 | `publish_gate` 新增检查 4b：`rule_layer == LEGAL` 且 `mandatory_level` 为空 ⇒ **拒绝发布**（绝不猜测默认值） |
| 迁移 | `e3b7a1c4f920`（`down_revision d1a4f7c93b28`）：**additive** 加两列 nullable；回填**幂等**（LEGAL→`mandatory`；已知层→`operator_discretion`；`rule_layer` 为 NULL 的遗留行保持 NULL）；归一化 `discretionary`；重复执行为 no-op |
| API | `CandidateIn.mandatory_level`、`CandidateMandatoryIn`、`_candidate_dict`、create 校验+审计、publish 响应/审计带 `rule_layer`+`mandatory_level`、`_load_layered_rules` 透传；**新增** `PATCH /admin/candidates/{id}/mandatory-level`（校验+审计） |
| Admin | 候选详情/发布路径消费该字段 |
| 交换格式 | `petaccessjson` 的 `VALID_MANDATORY_LEVELS`；dump/load 强制 LEGAL 必须带 `mandatory_level` |
| 脚本 | `gen_review_decisions_r1.py` 增加 `mandatory_for()`（LEGAL→mandatory 确定性映射）；`publish_reviewed_r1.py` 预检拒绝 LEGAL 无 level，发布后校验 level 保留 |
| 文档 | `DECISIONS.md` 新增 **ADR-023**（上下文/决策/备选/证据/迁移影响/状态 accepted） |

### 3.3 兼容性（用户明确要求）

- ✅ 与 `RuleLayer`（LEGAL / REGULATORY_GUIDANCE / OPERATOR_POLICY / TEMPORARY_POLICY）正交兼容
- ✅ 与 `RuleException` / supersession 兼容（遮蔽逻辑扩展而非替换）
- ✅ 迁移 **additive**、回填 **幂等**
- ✅ 归一化遗留词表，旧数据不破

### 3.4 测试覆盖

| 文件 | 内容 |
|---|---|
| `tests/unit/test_mandatory_level.py`（**22 用例**） | 词表与归一化、列与约束存在性、floor 语义（禁止 + 条件）、发布门禁（fake session）、迁移回填幂等（SQLite）、Hypothesis 性质不变量 |
| `tests/integration/test_mandatory_level.py` | 真实 DB 的 effective-rules floor、`mandatory-level` 端点校验+审计、遗留值往返（**需 PostGIS，本轮 BLOCKED**） |
| `tests/unit/test_publish_layer_integrity.py` | F2 由 "open" 改为 **fixed, ADR-023** |

### 3.5 相比旧 resolver 的实质改进

旧实现只能保护"法定强制**禁止**"。新实现同时保护"法定强制**条件**"——
下层运营方的 `allowed` 不能再把一个法定强制条件静默降级为无条件允许。这是本次修复的净增能力。

### 3.6 ENV-01 解除后暴露的缺陷（全部已修，详见 `ENV01_RESOLUTION_REPORT.md`）

依赖栈就绪后第一次真实跑迁移与全量测试，立即暴露 **7 个**此前不可能发现的缺陷。
其中 2 个直接削弱 BLK-LAYER-02 的修复效果：

| # | 缺陷 | 严重性 |
|---|---|---|
| 1 | 7 个双前缀约束名（跨 4 表）：手写迁移未用 `op.f()` ⇒ 与 `create_all` 命名发散，且 `downgrade()` 实测失败 | 中（迁移可逆性/一致性） |
| 2 | **33 条候选层级/规范力陈旧**：登记表 16 条 LEGAL，库中全为 OPERATOR_POLICY ⇒ 发布将把 16 条法定规则**静默降级** | **高（直接击穿 ADR-023）** |
| 3 | 发布门禁只信库中层级，且**发布后**才校验 ⇒ 静默降级无法被阻止 | **高** |
| 4 | `RuleIn` 缺遗留值归一化：写 `discretionary` 报 422，读取路径却正常 | 中（读写词表不一致） |
| 5 | `/places/{id}/extras` 抛 `AttributeError`（`AccessPath` 无 `zone_id`）；该端点**零测试覆盖** | 中（新端点不可用） |
| 6 | Place Detail 分区徽标复用场所级结果，把「明确限制」显示为「尚未核验」 | **高（误导用户）** |
| 7 | E2E 无法运行：`vite preview` 不继承 `server.proxy` ⇒ 404 被误读为应用缺陷 | 中（门禁不可用） |

**修复方式**：修正迁移源 + 幂等修复迁移（`f4c9d2e7a831`）；扩展 backfill 脚本并执行（layer 18 / level 16 变更，0 失败）；
发布预检新增**登记表↔库一致性**校验 + 发布后同时校验 `rule_layer`；共享归一化注解类型；
修正 `_in_place()` 谓词并补 5 个集成测试；分区按需评估 + 缓存；补 `preview.proxy` 与 E2E 流程文档。
新增 **8 个预检守卫单测** 固定该守卫。

**纪律价值**：这 7 个缺陷在"deselect 掉 DB 用例、宣称 full PASS"的做法下**全部不可见**。

---

## 4. P0-3 33 条候选的人工审核工作流

### 4.1 工作表（可复现生成）

`scripts/gen_review_sheet_r1.py` → `RULE_REVIEW_SHEET_R1.md`，本轮重跑输出：

```json
{ "written": "RULE_REVIEW_SHEET_R1.md", "total": 33,
  "recommended": { "APPROVE": 21, "APPROVE_WITH_NOTE": 8, "HOLD（pending）": 3, "REJECT": 1 },
  "candidates_with_conflicts": 12 }
```

每行字段（按用户要求）：candidate / place / proposed rule / evidence / source / evidence strength /
conflicts / **AI 建议** / 理由 / **final_decision（空）** / **reviewer（空）** / **reviewed_at（空）**。

### 4.2 纪律落实

- **AI 不代签**：`final_decision` / `reviewer` / `reviewed_at` 三列留空，由具名人类评审员填写。
- **Manner 误归因** → 建议 `REJECT`（`mn-outdoor-media`：把媒体转述误当作场所规则）。
- **弱证据**（`search_snippet` / `social_lead`）→ 建议 `HOLD（pending）`，**不强行放行**（ADR-021）。
- 3 条 ObservationCandidate 保持 lead-only，**不在本表内**，永不进入规则发布。

### 4.3 门禁验证（GOV-01 红线）

```text
$ python scripts/publish_reviewed_r1.py --dry-run
=== DRY RUN（不写库）===
发布前置条件未满足（33 项）——以下为需要人类评审员处理的事项：
  - 70cc7579-… dj-pilot: final_decision 未填
  ...（共 33 行，全部 final_decision 未填）
held: [3 条 pending 候选]
published: []   failed: []
EXIT=3
```

**结论**：门禁在未获签署时**硬拒绝**，退出码 3。这是设计预期，不是失败。

---

## 5. P0-4 / P0-5 首批 Publish 与扩量门禁

| 步骤 | 状态 | 原因 |
|---|---|---|
| 具名人类签署 33 行 | **BLOCKED_EXTERNAL (GOV-01)** | 需一名具名评审员；AI 代签即项目明令禁止的行为 |
| 首批 10–20 条真实 Publish | **READY（待签署）** | 写库能力已就绪（迁移 up/down/up 通过）；发布预检**双重把关**：登记表校验 + 登记表↔库一致性校验 |
| 发布后校验（linkage / evidence / audit / resolver / effective-rules / client / rollback / supersession / watch） | **NOT_RUN** | 依赖上一步 |
| `PILOT_REVIEW_PUBLISH_GATE` | **NOT PASS** | 仅剩 GOV-01 |
| 30–50 Place 扩量 | **未启动** | 按用户指令与纪律，Gate 未 PASS 前不扩量 |

**ENV-01 解除后新增的两道把关**（ADR-024）：

1. 预检比对**登记表 ↔ 库中候选**的 `rule_layer` 与 `mandatory_level`，任一不一致即**硬拒绝**，
   并提示先运行 `scripts/backfill_candidate_rule_layer.py`；
2. `--execute` 模式**强制**要求库状态可读（读不到即退出码 4），杜绝「未校验即发布」。

这直接封堵了本轮发现的**最严重缺陷**：33 条候选的层级在库中陈旧（全为 OPERATOR_POLICY），
而登记表声明 16 条 LEGAL —— 若不设此校验，签署后发布会把 16 条法定规则**静默降级**为运营方政策。

---

## 6. 验证门禁实测结果（ENV-01 解除后，2026-09-14）

| 门禁 | 命令 | 结果 |
|---|---|---|
| Ruff lint | `ruff check services/api services/worker tests scripts` | **PASS** — All checks passed |
| Ruff format | `ruff format --check …` | **PASS** — 131 files already formatted |
| Mypy | `mypy .`（services/api） | **PASS** — no issues in **76** source files |
| **全量 pytest（含 DB，不 deselect）** | `pytest` | **PASS — 319 passed / 0 failed** |
| 迁移 up/down/up | `alembic downgrade c81e02ba6d45 && alembic upgrade head` | **PASS** — head `f4c9d2e7a831` |
| 依赖服务冒烟 | `/health/components` | **PASS** — `all_ok: true`（postgres/redis/minio/celery） |
| **Playwright 全量 E2E** | `playwright test` | **PASS — 14 passed / 0 failed** |
| OpenAPI 面 | `app.openapi()` | **89** paths（admin **31**）；`/places/{id}/extras`、`/admin/candidates/{id}/mandatory-level` 均在 |
| ESLint | `eslint .` | **PASS** — 0 problems |
| Prettier | `prettier --check .` | **PASS** |
| H5 build | `vue-tsc --noEmit && vite build` | **PASS** |
| Admin build | `vue-tsc --noEmit` + `vite build` | **PASS** |

**测试计数演进**：R2 基线 238 → 本轮前 306（deselect 20 个 DB 用例）→ **319 全绿（0 deselect）**。
DB 依赖用例从 **0 可执行** 变为 **75 个全部通过**（55 集成 + 20 `db_session`）。

---

## 7. 环境处置记录（沙箱）

Admin 构建首次失败于 `prepareOutDir → emptyDir`：

```text
[safe-delete] 操作失败: spawnSync ...genie-trash\win32-x64.exe ETIMEDOUT
    at trashViaBinary (node-safe-delete-shim.cjs)
    at emptyDir (vite/dist/node/chunks/dep-Dm0c1Wj2.js)
```

这是**沙箱删除守卫**（单次删除 > 50 文件触发）导致的环境故障，**不是代码问题**——
证据是 `vue-tsc --noEmit` 在清目录**之前**已通过。按既定处置：

```bash
cd apps/admin
./node_modules/.bin/vue-tsc --noEmit                      # 真实类型检查 → 0 error
./node_modules/.bin/vite build --outDir "$TMPDIR/pa-admin-verify"   # 输出到 OS 临时目录（守卫豁免）
# 校验产物后清理
```

**退出码保持工具真实退出码，未降低任何断言、未改写任何退出码。**

---

## 8. 遗留阻塞（如实登记）

| ID | 内容 | 状态 | 解除条件 |
|---|---|---|---|
| **GOV-01** | 缺具名人类评审员 | **仍成立（唯一剩余阻塞）** | 具名评审员填写 `review_decisions_r1.json` 的 `final_decision` / `reviewer` / `reviewed_at` |
| ~~ENV-01~~ | ~~无容器运行时 ⇒ 无 PostGIS / Redis / MinIO~~ | **RESOLVED（2026-09-14）** | — |
| BLK-LAYER-02 | 法定约束可被低层放宽 | **FIXED**（ADR-023） | — |
| BLK-LAYER-01 | 发布时 rule_layer 丢失 | **FIXED** | — |
| ADR-024 | 约束命名 + 登记表↔库一致性 | **FIXED**（`f4c9d2e7a831`） | — |
| BLK-LEGAL-01 | 法律文本未经执业律师审阅 | 仍成立 | 律师出具意见 |
| BLK-PLAT-01 | 平台审核未提交 | 仍成立 | 注册主体并提交审核 |
| B-01…B-07 | 工具链 / 凭证 / 资质 | 仍成立 | 见 `BLOCKERS.md` |

---

## 9. 下一步（ENV-01 已解除；仅剩人类签署）

1. **（已完成）** 依赖栈启动 → `alembic upgrade head` → head `f4c9d2e7a831` → up/down/up 往返验证。
2. **（已完成）** 全量 `pytest`（**不 deselect**）→ **319 passed / 0 failed**。
3. **（待人类）** 具名评审员签署 `RULE_REVIEW_SHEET_R1.md` 33 行，回填
   `docs/reality_audit/review_decisions_r1.json`；随后
   `python scripts/publish_reviewed_r1.py --dry-run` 应返回 `signed=true` 且库一致性校验通过。
4. **（待签署后）** `python scripts/publish_reviewed_r1.py --execute --reviewer "<具名>"`，
   首批 10–20 条真实 Publish，逐项校验 linkage / evidence / audit / resolver /
   effective-rules / client / rollback / supersession / watch。
5. 上述全部通过后 `PILOT_REVIEW_PUBLISH_GATE = PASS`，方可进入 30–50 Place 扩量。
