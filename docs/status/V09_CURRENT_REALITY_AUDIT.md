# V09 CURRENT REALITY AUDIT — Wave02 Human Review Checkpoint

- Audit 轮次：`PET_ACCESS_PLATFORM_CONTINUATION_R1 · PHASE_0`（对应 Goal 契约「波浪02 复核检查点推进」Phase 0）
- 执行方：PI-Desktop（Agent）· 执行时点：2026-09-21（UTC+8 会话）
- 决定人 / Human Reviewer：`huangdi97`（本审计**不代签、不填任何决策字段**）
- 方式：**全部只读**。DB 查询仅 SELECT；无任何写库、无 publish、无 execution、无 Human 字段写入。
- 状态分类（契约强制五类，每项只用一类）：
  - `CURRENTLY VERIFIED` = 本会话真实执行并通过（给出实测证据）
  - `HISTORICAL BASELINE` = 历史轮次已记录的事实（给出文档出处；本轮未重跑）
  - `NOT RERUN THIS SESSION` = 工具/环境本轮未再次执行
  - `DESIGN ONLY` = 仅存在于设计/文档，无实现或未验证
  - `ENGINEERING OPEN` = 已发现、有真实证据、需要工程/人工后续处理

---

## 0. 结论指标（本会话实测）

| 条目 | 值 | 状态 |
|---|---|---|
| CURRENT_HEAD | `6a2eca71d644d048f1a2556c5c1fc8e21c0078b5` | CURRENTLY VERIFIED |
| BRANCH | `master` | CURRENTLY VERIFIED |
| WORKTREE | clean（`git status`：nothing to commit） | CURRENTLY VERIFIED |
| CHECKPOINT_COMMIT | `6a2eca7`（wave02: land 10 real places + 20 review-pending candidates + packet） | CURRENTLY VERIFIED |
| DIRTY_FILES | 0 | CURRENTLY VERIFIED |
| DB_AVAILABLE | petaccess / PRODUCTION（`safety.py --probe-db`） | CURRENTLY VERIFIED |
| ALEMBIC_HEAD | `f2a1c7d9e034`（`check_production_integrity` alembic_head） | CURRENTLY VERIFIED |
| REAL_PLACE_COUNT | **30**（全 active） | CURRENTLY VERIFIED |
| ACCESS_RULE_COUNT | **26**（全 current） | CURRENTLY VERIFIED |
| RULE_EXCEPTION_COUNT | 9 | CURRENTLY VERIFIED |
| WAVE01_DISPOSITION | ALREADY_PUBLISHED 12 / SUPERSEDED 3 / EXECUTABLE 0 / BLOCKED 0 | CURRENTLY VERIFIED |
| WAVE02_NEW_PLACES | 10（20 → 30） | CURRENTLY VERIFIED |
| WAVE02_CANDIDATES | **20**，全部 `REVIEW_PENDING` | CURRENTLY VERIFIED |
| WAVE02_PUBLISHED | `published_rule_id` 非空 = 0；`access_rule_from_w02_source` = 0 | CURRENTLY VERIFIED |
| WAVE02_HUMAN_FIELDS | decisions JSON `final_decision=null / reviewer="" / decided_at=null`（20/20） | CURRENTLY VERIFIED |
| SOURCE_MONITOR | 9（9 个独立来源各 1 条，无重复） | CURRENTLY VERIFIED |
| PRODUCTION_INTEGRITY | CRITICAL=0 / HIGH=0 / MEDIUM=1（历史存量） | CURRENTLY VERIFIED |
| pytest | **825 passed / 2 skipped / 0 failed**（隔离 TEST 库 + Celery worker） | CURRENTLY VERIFIED |
| ruff | `All checks passed!` | CURRENTLY VERIFIED |
| mypy | `Success: no issues found in 87 source files` | CURRENTLY VERIFIED |
| frontend typecheck（H5） | vue-tsc --noEmit exit 0 | CURRENTLY VERIFIED |
| frontend typecheck（Admin） | vue-tsc --noEmit exit 0 | CURRENTLY VERIFIED |
| H5 build | `✓ built in 3.37s`（vue-tsc + vite） | CURRENTLY VERIFIED |
| Admin build | `✓ built in 2.19s`（vue-tsc + vite） | CURRENTLY VERIFIED |
| Playwright E2E | **16 passed / 2 failed**（详见 §5.9：2 个失败为迁移后既有用例，非 Wave02 引入） | CURRENTLY VERIFIED（结果如实记录） |
| HUMAN_ACTION_REQUIRED | `WAVE02_FINAL_DECISIONS`（本会话终止态） | CURRENTLY VERIFIED |

---

## 1. 仓库 / Git 状态

- HEAD：`6a2eca71d644d048f1a2556c5c1fc8e21c0078b5`，branch `master`，worktree clean。
- 最近提交链（`git log --oneline -6`）：
  - `6a2eca7 wave02: land 10 real places + 20 review-pending candidates + human review packet`
  - `aee7bb8 feat(answer): migrate all consumer surfaces onto the unified AccessAnswer`
  - `6400fc1 publish: land the R2-FINAL-R3 leftovers and close both approved registers`
  - `a3e7dae docs(governance): correct the Wave-01 closure scope …`
  - `f074ae9 feat(answer): add the unified AccessAnswer every consumer surface reads`
  - `743dc2c governance(Wave-01): record the closure quality baseline…`
- 本会话**未产生任何 commit**（审计与审核均只读；不修改已签署产物）。

状态：`CURRENTLY VERIFIED`

---

## 2. 数据库角色与迁移

- `uv run python services/api/app/db/safety.py --probe-db`（读 .env 的 DATABASE_URL 直连）：
  - `TARGET_DB = petaccess`
  - `TARGET_DB_ROLE = PRODUCTION`
  - `PROBE_SOURCE = current_database()`
- `check_production_integrity.py --db-name petaccess`：`alembic_head = f2a1c7d9e034`。
- 本会话对生产库的全部操作：只读 SELECT（place / access_rule / rule_candidate / source_monitor / data_source_job / audit_log / user / information_schema）。
- Wave02 数据管线的写入发生在历史轮次（2026-09-19，`scripts/expansion_w02_ingest.py` 经生产 API）；本会话**未回滚、未重写、未重灌**。

状态：`CURRENTLY VERIFIED`

### 2.1 注意（诚实记录，不修饰）

Wave02 数据管线报告（`docs/expansion/WAVE02_DATA_PIPELINE_REPORT_R1.md`）标注基线 alembic 为 `f2a1c7d9e034`，与本会话 `alembic_head` 一致。Wave02 本身未引入新迁移（纯数据写入）；AccessAnswer 迁移 `f074ae9/aee7bb8` 已先行落库。DB 中无名为 `audit_event` 的表（实际为 `audit_log`），本审计按真实 schema 查询。

---

## 3. 真实 Place 数

- `SELECT count(*) FROM place` → **30**，`lifecycle_status` 分布：active=30。

状态：`CURRENTLY VERIFIED`

- Wave01 既有 20 个真实场所（上海博物馆东馆、上海新天地朗廷酒店、兴业太古汇、前滩太古里、港汇恒隆广场、上海苏河湾万象天地、蟠龙天地、上海迪士尼乐园、世纪公园、上海动物园、CHARLIE'S 粉红汉堡、omitofee 上海首店等）。
- Wave02 新增 10 个（§4）：上海植物园、共青森林公园、上海世博文化公园、豫园、上海自然博物馆、上海野生动物园、上海辰山植物园、和平公园、昆山公园、顾村公园。

---

## 4. Wave01 disposition（真实重跑）

`uv run python scripts/wave01_approved_disposition_audit.py --database-url … --registry artifacts/wave01_register_reprojected.json --out <scratch>`：

```
REVISION = EXP-R1-W01-REVIEW-R1
REVIEWER = huangdi97
DATABASE = 127.0.0.1:5432/petaccess
GATE_RAN = True
ZERO_DB_MUTATION = True
APPROVED_TOTAL = 15
SUPERSEDED_APPROVED = 3
CURRENTLY_EXECUTABLE_APPROVED = 0
PUBLISH_BLOCKED_APPROVED = 0
ALREADY_PUBLISHED_APPROVED = 12
```

- 12 条 ALREADY_PUBLISHED（含世纪公园 w01-4e217d5810，历史轮次已真实发布）。
- 3 条 SUPERSEDED：`w01-305fa08c1e`、`w01-3a04d4d1aa`、`w01-6f2bfd39d7`（均被 SCOPE-REMODEL-R2 拆分语义取代）。
- 0 条 executable、0 条 blocked。
- 与 `WAVE01_FINAL_CLOSURE_REPORT.md` 的历史结论一致（HISTORICAL BASELINE 回放，本轮重跑通过）。

状态：`CURRENTLY VERIFIED`（重跑实测）

---

## 5. Wave02 数据面核验（真实只读查询）

### 5.1 10 个新 Places

证据文件 `docs/expansion/expansion_r1_wave02_evidence.json` 含 10 个真实上海场所，每个均带：

- `geo.status = REAL_OSM_NOMINATIM`：`osm_type / osm_id / display_name / licence(ODbL) / provider / fetched_at / query / match_quality`，无 mock geo、无随机坐标、无 UUID 派生坐标。
- `place_match_evidence`（canonical_name + 官方域名 / 政府来源 / 地址消歧），如上海野生动物园标注「与上海动物园（长宁区虹桥路2381号）为不同法人/不同园区」。
- Sources / Zones / Rules / Observations 全链。

| 场所 | district | place_type | source_type | directness |
|---|---|---|---|---|
| 上海植物园 | 徐汇区 | park | official_operator_policy | direct |
| 共青森林公园 | 杨浦区 | park | official_operator_policy | direct |
| 上海世博文化公园 | 浦东新区 | park | official_operator_policy | direct |
| 豫园 | 黄浦区 | scenic_area | official_operator_policy | direct |
| 上海自然博物馆 | 静安区 | museum | official_operator_policy | direct |
| 上海野生动物园 | 浦东新区 | scenic_area | official_operator_policy | direct |
| 上海辰山植物园 | 松江区 | park | official_operator_policy | **secondary**（页存在可达，句子为外部收录带 needs_verification）|
| 和平公园 | 虹口区 | park | government_service | direct |
| 昆山公园 | 虹口区 | park | government_service | direct |
| 顾村公园 | 宝山区 | park | external_web_reference | **secondary**（本地宝转述，needs_verification）|

zones 10 个；其中和平/昆山 zone 为 `pet_pilot_area`（携宠试点区域·部分区域），世博 zone 为「全园（后滩滨江区域除外）」。

状态：`CURRENTLY VERIFIED`（证据文件 + 生产库 place/zone 计数一致：place_total=30）

### 5.2 20 条 REVIEW_PENDING candidates

生产库只读查询（`rule_candidate WHERE expansion_run_id = 'EXP-R1-W02-20260919'`）：

- 总数 20；`review_status` 分布：REVIEW_PENDING=20。
- `published_rule_id` 非空 = **0**（无任何发布）。
- `access_rule_from_w02_source = 0`：没有任何 access_rule 挂接 Wave02 来源（`access_rule_total` 保持 **26**）。
- `reviewer_id` 全部 = `ccfe8e68-9319-55a8-a01b-156eee5a49dd`（演示管理员 / `admin@demo-petaccess.com`），`review_note` = `WAVE02/EXP-R1-W02-20260919: 待人工审核（不得自动批准或发布）`。

> **诚实说明（ENGINEERING OPEN）**：`rule_candidate.reviewer_id` 非空是 transition API 的既有 schema 行为——执行 transition 的管线以演示管理员 token 调用，端点把 `user.id` 写进 reviewer_id。这是 **Wave01 已文档化的既有语义**（`WAVE01_FINAL_CLOSURE_REPORT.md` §6.3.2：DB 评审人与执行者共用 `actor_user_id`，`reviewer_id` 指向执行账号 ≠ 有人签字，**不能**从 reviewer_id 反推「是谁批的」；真人评审 huangdi97 的签章记录在 Human Decision 产物）。因此：
> - 契约判据「Human 字段仍为空」以 Human Decision 产物（`review_decisions_expansion_r1_wave02.json`）与候选 `review_status/published_rule_id` 为准，**全部为空/未决**（实测通过）。
> - 字面上的「reviewer_id 全空」在现有 schema 语义下不成立（与 Wave01 行为相同），本轮不修改该行为（改 schema/清空 reviewer_id 属跨管线写操作，超本契约只读范围；也不应把「演示管理员」误读为 huangdi97 签暑）。

状态项（候选未决事实）：`CURRENTLY VERIFIED`；字面 reviewer_id 语义：`ENGINEERING OPEN`（记录，不改）。

### 5.3 Wave02 Review Packet 三件套

- `docs/expansion/WAVE02_HUMAN_REVIEW_PACKET.md`（按场所分组逐条）
- `docs/expansion/WAVE02_HUMAN_REVIEW_QUICK_TABLE.md`（速查表）
- `docs/expansion/review_decisions_expansion_r1_wave02.json`（20 行决策登记表）

`review_decisions_expansion_r1_wave02.json` 实测：`revision=EXP-R1-W02-REVIEW-R1`，每行 `final_decision=null / reviewer="" / decided_at=null / decision_note=""`，顶部 `reviewer:"" / decided_at:""`。**Human 决策字段全空**。

状态：`CURRENTLY VERIFIED`

### 5.4 §29 全门禁 probe（只读重跑）

`uv run python scripts/wave02_section29_gates.py --database-url … --out <scratch>`，实测 13 项 × 20 候选：

```
SOURCE_SCOPE_SEMANTICS PASS 20   LEGAL_OPERATOR_LAYERING PASS 20
ZONE_SCOPE             PASS 20   EXCEPTION_REACHABILITY  PASS 20
ADR030                 PASS 20   ADR031                  PASS 20
EVIDENCE               PASS 20   FRESHNESS               PASS 20
LICENSE                PASS 20   CONFLICT                PASS 20
SUPERSESSION           PASS 20   GUIDE_DOG_SAFETY        PASS 20
CONDITION_SCHEMA       PASS 20
CANDIDATES=20 ZERO_DB_MUTATION=True
```

状态：`CURRENTLY VERIFIED`

### 5.5 生产完整性

`uv run python scripts/check_production_integrity.py --db-name petaccess --out <scratch>`（23 项检查）：

```
PRODUCTION_INTEGRITY_SCAN = PASS
CRITICAL = 0   HIGH = 0
MEDIUM   = 1   AUDIT_TARGET_ID_UNUSABLE（2647 行 / 4 组，历史存量，与 Wave02 无关）
severity_counts = {'MEDIUM': 1}
```

状态：`CURRENTLY VERIFIED`

### 5.6 SourceMonitor = 9

`source_monitor` 中 `expansion_run_id='EXP-R1-W02-20260919'` 共 **9 条**，9 个不同 source_id 各 1 条（和平/昆山共享虹口 pilot source），`source_monitor_total=22`（其余为历史轮次 monitor）。匹配管线报告 `SOURCE_MONITOR_REQUIRED=9 / CREATED=9`。

状态：`CURRENTLY VERIFIED`

### 5.7 无 publish / execution 记录新增

- `access_rule` 总数 = 26（与 Wave02 前一致），无新增发布。
- `rule_candidate.published_rule_id`（W02）= 0。
- `audit_log`（总计 9885 行）在 Wave02 时段的 action 分布：
  `candidate.create ×20 / candidate.transition ×20 / place.update ×10 / source.freshness_assign ×10 / data_source_job.create ×1`
  —— **没有任何 publish / publish_exception / execution 记录**。
- `data_source_job` W02：COMPLETED ×3（ingest / correction / 相关 job 均完成，无执行类 job）。

状态：`CURRENTLY VERIFIED`

### 5.8 测试与质量门禁实测

| 项目 | 命令 | 结果 |
|---|---|---|
| pytest | `DATABASE_URL=<petaccess_test> uv run pytest -q`（含 Celery worker） | **825 passed / 2 skipped / 0 failed**；70.66s |
| ruff | `uv run ruff check .` | `All checks passed!` |
| mypy | `uv run mypy services/api` | `Success: no issues found in 87 source files` |
| H5 typecheck | `pnpm --filter @petaccess/client-h5 exec vue-tsc --noEmit` | exit 0 |
| Admin typecheck | `pnpm --filter @petaccess/admin exec vue-tsc --noEmit` | exit 0 |
| H5 build | `pnpm --filter @petaccess/client-h5 build` | `✓ built in 3.37s` |
| Admin build | `pnpm --filter @petaccess/admin build` | `✓ built in 2.19s` |

- pytest 说明：项目强制测试隔离（`tests/conftest.py` 拒绝 PRODUCTION 库，`PRODUCTION_DATABASE_REFUSED`）。实测流程：`scripts/isolated_db.py --role TEST --reset` 重建隔离库 → `DATABASE_URL=…petaccess_test` 运行。首轮 6 个失败全部为环境因素而非代码缺陷：
  - 3 个 `test_production_fail_closed` 失败：Windows GBK 编码导致子进程输出解码崩溃（`UnicodeDecodeError: 'gbk' codec…`，`proc.stdout=None`）；以 `PYTHONUTF8=1` 重跑即过。
  - 3 个 Celery 集成用例（`test_media.py`、`test_v05_e2e.py` 的 OCR/TTL 任务）：依赖运行中的 Celery worker；本会话启动 worker（`celery -A app.worker.celery_app worker --pool=solo`）后重跑 `3 passed`。
  - 全量重跑（带 worker）：**825 passed / 2 skipped / 0 failed**，与 Wave01 收口基线一致（HISTORICAL BASELINE 回放→本轮实测）。

状态：`CURRENTLY VERIFIED`

### 5.9 Playwright E2E（真实执行，如实记录）

命令：`pnpm exec playwright test --reporter=line`（自包含：`isolated_db.py --role E2E --reset` 重建 `petaccess_e2e` + 自启 API :8010 + vite preview :5175；global-setup 校验 TARGET_DB=petaccess_e2e）。

结果：**16 passed / 2 failed**（44.4s）。两个失败：

1. `h5-journey.spec.ts:28 place detail shows one-sentence answer with zones and provenance`
2. `h5-journey.spec.ts:51 mode switch re-evaluates: service dog → allowed`

根因一致：E2E 种子咖啡馆（星河咖啡·测试店，deterministic UUID `8412b521-…`）的 place 级 access-answer 实测返回 `normative_result.effect=unknown → 「信息不足」`，而该 spec 断言期望「有条件进入」。zone 级规则完备（室内堂食区 ordinary_pet=prohibited、户外座位区 ordinary_pet=conditional+leash、服务犬=allowed），但 place 级聚合按「不把 zone 折叠成 place 结论」的迁移语义返回 unknown。

定性（证据）：
- spec 文件最后修改 `9765fe5`（2026-09-16，visual baseline 提交）；`aee7bb8`（AccessAnswer 迁移）时该 spec 已含相同断言。
- Wave02 提交 `6a2eca7` 的 diff **完全不含** answer.ts / PlaceView.vue / access API / seed.py / tests/e2e 改动（仅 docs + scripts + source_scope_semantics + 一个单测）。
- 因此 2 个失败是 AccessAnswer 迁移（`f074ae9/aee7bb8`）后「测试期望 vs place 级玄义」的**既有不一致**，非 Wave02 引入，亦非本会话可修复范围（本契约只读；修复 E2E 属后续 Wave02 决策后的工程项）。

状态（Playwright 本身执行）：`CURRENTLY VERIFIED`；该 2 用例 = `ENGINEERING OPEN`（既有，非本轮引入）。

### 5.10 编码环境说明（诚实记录）

- 本机（Windows / GBK 控制台）下 python 子进程输出偶发 `UnicodeDecodeError`（GBK vs UTF-8）。已在 pytest/脚本运行时以 `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8` 规避；这只影响日志/测试子进程解码，不影响 DB 数据与构建产物。
- 首轮 pytest 6 个失败即为该环境因素（§5.8），经 UTF8 + worker 修复后全量重跑 0 failed。

---

## 6. 审计结论

- 契约基线事实全部经本会话只读实测确认：HEAD/worktree、30 Places、26 access_rule、20 REVIEW_PENDING candidates、Human 决策字段全空、SourceMonitor=9、生产完整性 CRITICAL=0/HIGH=0、AccessAnswer 迁移已就位、测试/构建门禁实测通过。
- **Wave02 无任何发布**；**无任何人代签**；**无伪造记录**。
- 唯一需要人工注意的真实语义项：§5.2 的 `reviewer_id`（演示管理员）属既有 schema 行为，不构成 huangdi97 签名；签暑判据一律以决策登记表与 review_status/published_rule_id 为准。
- Playwright 2 个失败为迁移后既有 E2E 不一致（ENGINEERING OPEN），与 Wave02 数据无关，不影响 20 条候选的签发判断；建议 Wave02 决策后作为独立工程项处理（保持「不把 zone 折叠成 place 结论」语义的前提下修正 spec 期望或在 place 页面补充说明）。

## 7. 终止态

```
HUMAN_ACTION_REQUIRED = WAVE02_FINAL_DECISIONS
```

Phase 0（本审计）完成；Phase 1（20 条候选 AI 审核与签署建议表）见：
`docs/expansion/WAVE02_REVIEW_RECOMMENDATIONS.md`