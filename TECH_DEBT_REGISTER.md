# TECH_DEBT_REGISTER.md

日期：2026-09-13（PART A · A15）。原则：能修的修了（见"本轮已修"）；修不了的如实登记，不藏。

## 本轮已修（从扫描到修复）

| 项 | 处置 |
|---|---|
| 前端 0 lint/format 工具链 | 引入 ESLint 10（vue flat/essential + ts recommended）+ Prettier 3；**实际运行**并通过 |
| 前端 dead code（6 处 unused import/var） | 删除：EvidenceView `platformPreview`、PlacesView `onMounted`、RegulationsView `get`、PlaceView `STATUS_GLYPHS`/`PlaceSummary`、MineView `Shell` 导入、AppShell `mode`/`MODE_LABELS` |
| `Shell.vue` 单词组件名 | 重命名 `AppShell.vue`（7 个视图同步更新） |
| `pnpm-workspace.yaml` 字面占位符 `allowBuilds: esbuild: set this to true or false` | 置为 `esbuild: true`（esbuild postinstall 需要） |
| 生成 API client 与 OpenAPI 不一致 | 实查：提交版缺全部 v0.5 端点（answerability/effective-rules/boundary-match 等 0 命中）。已 `pnpm client:gen` 重新生成，双端 build 复验 PASS |
| dev JWT secret 30 字节（RFC 7518 告警） | 30→49 字节；测试警告 60→1 |
| verifications HTTP 层无测试（docstring 谎报覆盖） | 补 5 个集成测试；test_api.py docstring 修正 |
| `candidate_service.publish()` 并发竞态（双 reviewer 可重复发布规则） | 原子 CAS（`WHERE review_status='APPROVED'`）+ 并发测试锁定 |
| `tests/e2e/__init__.py` 游离文件 | 见 TD-04（随 git mv 检查保留，无运行影响） |

## 登记项（未在本轮修，含理由）

| ID | 项 | 影响 | 建议 | 理由 |
|---|---|---|---|---|
| TD-01 | `services/worker/` 空壳（仅 pyproject.toml，声明 `packages=["worker"]`，实际 Celery 代码在 `services/api/app/worker/`） | 结构混乱：uv workspace 成员指向不存在的包 | 合并 workspace 或移除空壳成员（需 `uv.lock` 重排） | 改动 workspace 定义影响打包/安装链，属结构性重构，独立成 Gates 更安全 |
| TD-02 | `packages/design-tokens/` 空目录；`apps/client/adapters/` 空目录 | 死目录 | 补内容或删除 | design-tokens 属设计系统决策；adapters 属 uni-app x 平台层（B-01 外部阻塞），本轮不越权发明 |
| TD-03 | v0.3 API 路由覆盖偏低（places 48% / disputes 44% / rules 56% / regulations 57% / admin 53%）+ `worker/tasks.py` 46% | 回归防护薄（业务语义已有 integration/E2E 背书） | 按"每修一个 bug 补一层 HTTP 测试"节奏渐进补齐 | 见 TEST_COVERAGE_REPORT 解释；为凑数写无断言测试违背 A5 原则 |
| TD-04 | `tests/e2e/__init__.py`（Playwright 目录里的 Python 包标记） | 轻微困惑 | 删除（pytest testpaths 不含该目录） | 保留于登记：删除属低风险但需一次回归确认，本轮聚焦更高价值项 |
| TD-05 | 无 face / license plate redaction 能力 | 真实数据扩量（PART B 扩量/100+）前的隐私缺口 | 接入 OCR/AI 管线时加脱敏步骤或建立素材准入策略 | 本地 RC 无真实用户素材；PART B 第一轮以"不采集含人脸/车牌素材"为执行约束 |
| TD-06 | 无 resolver batch 批量端点（多场所评估逐次调用） | 规模化时列表页 N×单次成本 | 数据量上来后加 batch 端点（evaluator 本身可批量，GOAL §20） | 当前 4–50 场所规模下 p95≤28ms，无实际瓶颈 |
| TD-07 | client-core 手写 v0.5 DTO（`EffectiveRuleSet` 等接口与后端 schema 重复） | 类型双写漂移风险 | 由生成 `schema.d.ts` 的 operations 类型替代（A1"no duplicated API DTO"） | 涉及 20+ 视图类型迁移，独立重构任务 |
| TD-08 | `observability.py` failed-job 落盘在 Redis 不可用时静默跳过 | Redis 故障期间失败任务不可见（任务本身仍失败/重试可见） | 记录降级计数或落本地文件 | 结构性小改进，非缺陷；可靠性主链（有界重试/幂等/失败可见）已验证 |
| TD-09 | PART B 试点中 7/33 规则候选引用 search_snippet 采集来源（页面未直接抓取核验：解放日报、OTA、CBNData、西岸报道URL待归档） | Evidence Completeness 78.8% < 90%，B15 停止条件已触发（扩量暂停） | 人工核验原文页/定位 URL/补抓 hash，升级 capture_method 后方可 APPROVED；扩量前完成 | 如实登记；见 REAL_DATA_PILOT_10_REPORT.md §7 与 REAL_DATA_FINAL_REPORT.md §9 |

## 扫描方法与结果

- TODO/FIXME/HACK/XXX：tracked 文件全扫 → **代码 0 命中**（仅 GOAL/ZCODE 文档中的纪律性文字）。
- `pass`/`NotImplementedError`：4 处，全部合法（异常类体、抽象接口方法 pragma、
  mock 通知 best-effort、failed-job 降级）。
- mock-only production path：Mock Provider 均有显式开关与 factory（`FEATURE_REAL_*`），无伪装。
- unused env：`.env`/`.env.example` 键与 `core/config.py` 字段一致（抽查 JWT/S3/MAP/AI 组）。
- duplicate schema：唯一发现即 TD-07（已登记）。

结论：无 unexplained TODO；所有遗留项登记在册且有处置建议。

---

## 2026-09-14 追加（P0-PUBLISH-CLOSURE + UI-CORE-CLOSURE 轮次）

### 本轮已修

| 项 | 处置 |
|---|---|
| `format:check:fe`（Prettier）在基线 HEAD 上**已为红** | 实测发现 **7 个未改动文件**（`apps/admin/src/views/RulesView.vue`、`apps/client-h5/src/components/{SkeletonList,SourceBadge}.vue`、`apps/client-h5/src/styles.css`、`packages/design-tokens/src/index.ts`、`tests/fixtures/real_world_regression.json`、`docs/reality_audit/*/provenance_manifest.json`）在 HEAD 状态即不通过。**本轮全部修复**，`prettier --check .` 现为全绿。 |
| `.prettierignore` 的 `docs/reality_audit/*.json` 为**单层** glob | 未能覆盖 `docs/reality_audit/<run>/provenance_manifest.json` 等嵌套证据产物 ⇒ 守卫对生成物生效。改为 `docs/reality_audit/**/*.json`；并新增 `tests/fixtures/*.json`（该夹具自述"regenerate via the audit tool, never hand-edit"）。**不重写证据产物**。 |
| `ContributeView.vue` 的"拍规则牌"是**空壳** | 原 `<input type="file">` 无任何处理逻辑（选了文件即丢弃）。重写为真实 `POST /media/upload`（magic-byte 校验 / 大小限制 / 随机对象键 / 重复检测）+ `GET /media/{id}` 取 OCR 预览 + 提交时携带 `evidence_refs`。 |
| `App.vue` 底部导航"贡献"指向 `/pet/new` | 指向错误（新建宠物档案页）。修正为 **地图 / 搜索 / 宠物 / 我的**；贡献入口保留在 Place Detail 与 `AppShell`。 |
| E2E 规范与实现漂移 | `h5-journey.spec.ts` 首例断言首页默认可见"附近场所"标题；新 IA 默认进入地图视图，标题仅在切换列表后出现 ⇒ 规范已陈旧。已改为先断言地图壳、再切列表断言标题。 |
| `PlaceView.vue` 死代码 | `effectStatus` 定义后从未使用（模板用 `StatusBadge` 的 `effect` prop）⇒ ESLint 报错。已删除。 |
| `SettingsView.vue` 触发**禁用语守卫** | 文案含禁用词（用于否定句"不做…预测"），但守卫为纯子串匹配 ⇒ `test_no_forbidden_copy_in_user_facing_sources` 失败。已改写为不含该词的表述。**未放宽守卫**。 |

### 登记项（本轮未修，含理由）

| ID | 项 | 影响 | 建议 | 理由 |
|---|---|---|---|---|
| TD-10 | `client-core` 手写 DTO 进一步增加（本轮新增 `PetIn`/`PetView`/`MediaView`/`MediaMetaView`/`WatchView`/`PlaceExtras` 等） | 与 TD-07 同源：类型双写漂移风险扩大 | 由生成 `schema.d.ts` 的 operations 类型统一替代 | 与 TD-07 合并处理；本轮为解除前端阻塞必须先补类型，单独重构 20+ 视图类型风险更高 |
| TD-11 | `tests/e2e/h5-journey.spec.ts` 全部用例依赖 API :8010 + 种子数据 | `ENV-01` 期间该文件**不可运行**，回归能力为零 | 已通过新增 `h5-shell.spec.ts`（离线安全，7 passed）部分补足；建议后续为 journey 用例引入可注入的 API mock 层 | 完整 mock 需与 `client-core` 的 HTTP 层协同设计，属独立任务 |
| TD-12 | 20 个 `db_session` 用例 + 55 个 `tests/integration` 用例无跳过标记 | 无 PostGIS 时**挂起**（连接超时 10.2s/次）而非快速失败，拖垮全量测试 | 加 `pytest.mark.db` + `conftest` 探测不可达即 skip（fail-closed，仍需显式声明"未验证"） | 加标记会改变测试语义与统计口径；须与"不得以 deselect 宣称 PASS"的纪律一并设计，独立成任务更安全 |
| TD-13 | Admin 端到端（Publish / Rollback / Supersession / Evidence Review / Data Quality）未验证 | P4 保持 PARTIAL | 解 `ENV-01` 后按 `P0_PUBLISH_CLOSURE_REPORT.md` §9 执行 | 纯外部条件阻塞，代码侧已就绪 |
| TD-14 | 深色主题未实现（P2） | 夜间可用性缺失 | 令牌已按 `color.bg.*`/`color.text.*`/`color.status.*` 组织，具备实现基础 | 按用户明确指令排在最后（P2） |

---

## 2026-09-14 追加（ENV-01 解除轮次）

依赖栈就绪后第一次真实跑迁移 + 全量测试，立即暴露 7 个此前**不可能发现**的缺陷。
**全部已修**（详见 `ENV01_RESOLUTION_REPORT.md`）。这也说明「deselect DB 用例后宣称 PASS」
的做法会把这些缺陷全部带入生产。

### 本轮已修

| 项 | 处置 |
|---|---|
| 7 个双前缀约束名（跨 4 表） | 4 个手写迁移改用 `op.f()`；新增幂等修复迁移 `f4c9d2e7a831` 原地重命名。ADR-024 |
| 33 条候选 `rule_layer`/`mandatory_level` 陈旧（**会把 16 条法定规则静默降级**） | `backfill_candidate_rule_layer.py` 扩展为同时校正 level，经 live API 写入留审计；已执行（layer 18 变更 / level 16 变更 / 0 失败） |
| 发布门禁只信库中层级、发布后才校验 | 新增登记表↔库一致性预检（不一致即硬拒绝）+ `--execute` 强制可读库状态 + 发布后同时校验 `rule_layer`；+8 单元测试 |
| `RuleIn` 缺遗留值归一化（写入 422、读取正常） | 抽出共享注解类型 `NormalizedMandatoryLevel`，读写共用 |
| `/places/{id}/extras` 抛 `AttributeError`（`AccessPath` 无 `zone_id`） | 修正谓词构造；补 5 个集成测试（该端点此前零覆盖） |
| Place Detail 分区徽标复用场所级结果（把「明确限制」显示为「尚未核验」） | 改为按需分区评估 + 缓存 + 失败诚实降级 |
| E2E 无法运行（`vite preview` 不继承 `server.proxy`） | `preview.proxy` + `VITE_API_PROXY` 可覆盖；E2E 用绝对基址构建，流程写入 README |
| `scripts/` 未纳入 lint 门禁（6 处 E501 长期漏检） | 修复全部 6 处（隐式字符串拼接，生成物逐字节不变）；`scripts` 纳入 `lint.sh` |

### 登记项（本轮未修，含理由）

| ID | 项 | 影响 | 建议 | 理由 |
|---|---|---|---|---|
| TD-15 | `rule_candidate.rule_layer` / `mandatory_level`、`source_artifact.evidence_strength`、`rule_exception` 的三个 CHECK 约束**只在迁移中存在**，模型未声明 | `metadata.create_all` 建库（如测试用的临时库）缺少这些完整性约束，DB 层守卫缺失 | 把约束补进模型 `__table_args__`，使两条建库路径等价 | 补进模型会改变 `create_all` 行为，需先确认无依赖「约束不存在」的测试；独立任务 |
| TD-16 | `real_pilot_ingest.py` 按 manifest 键幂等**跳过**已存在候选 | 证据变更后重跑不会校正已有候选 ⇒ 需专用 backfill 脚本（本轮即如此） | 增加显式 `--reconcile` 模式（仅限 `REVIEW_PENDING`，拒绝改写已审批/已发布候选） | 改变 bootstrap 脚本的「不mutate」语义需谨慎；已由 backfill 脚本 + 发布预检双保险 |
| TD-17 | 全量测试需 Redis + Celery worker 才能通过（3 个 OCR/TTL 用例） | 只起 DB 不起 worker 时会有 3 个失败，容易被误判为缺陷 | 为这 3 个用例加显式前置探测，worker 不可达时 skip 并标注（fail-closed，仍需声明「未验证」） | 与 TD-12 同源：需与「不得以 deselect 宣称 PASS」的纪律一并设计 |
| TD-18 | Admin 端到端（Publish / Rollback / Supersession / Evidence Review / Data Quality）未验证 | P4 保持 PARTIAL | 解 GOV-01 后随首批发布一并验证 | 阻塞在人类签署，非代码缺口 |
| TD-19 | 无 staging 部署编排 | P27 为 PARTIAL | 依赖栈已可运行，可补 compose override / 部署脚本 | 属独立交付物；当前聚焦 P0 发布闭环 |
| TD-20 | **admin 路由前缀不一致**：`rules`/`places`/`sources`/`operators`/`regulations`/`disputes` 的 `admin = APIRouter(tags=[...])` **无** `prefix="/admin"`，而 `v05` 与 `admin.py` 有 ⇒ 管理员写入落在非 admin 路径（如 `POST /api/v1/rules`、`PATCH /api/v1/rules/{id}`） | 路径语义误导；`ROLLBACK_RUNBOOK.md` 早期版本即因此写错端点（已修正）。权限仍由 `require_role` 强制，**不是**越权漏洞 | 统一为 `prefix="/admin"` 并保留旧路径的过渡别名（deprecation 一个版本） | 改路径是**破坏性 API 变更**，影响已生成的 `schema.d.ts` 与前端调用；须与版本策略一并规划，不适合在发布闭环中顺手改 |
| TD-21 | **L2 批次回退辅助脚本缺失**：`scripts/list_batch_rules.py`、`scripts/withdraw_batch.py` 均不存在 | 批次回退只能按 L1 逐条执行（手册 §3 已如实标注） | 实现两脚本（读快照 → 逐条 PATCH → 逐条审计），并在真实发布后演练 | 无已发布批次（GOV-01 未签署）⇒ 无法端到端验证；先实现未验证的脚本不如等真实批次 |
| TD-22 | 文档一致性无自动校验 | 本轮发现 `ROLLBACK_RUNBOOK.md` 引用了 3 个不存在的端点/脚本（已修）；此类漂移只能靠人工发现 | 加一个守卫测试：扫描 `*.md` 中的 `/api/v1/...` 与 `scripts/*.py` 引用，比对 OpenAPI 与文件系统 | 需先定义"允许的前缀引用"白名单以避免误报（本轮审计 20 条引用中 5 条为前缀/模块引用） |


---

## 2026-09-15 接管新增 / 关闭

| ID | 内容 | 严重性 | 状态 | 备注 |
|---|---|---|---|---|
| T-01 | 迁移 `a2d5e8b91c47` 被"部分应用后打标"：`alembic_version` 已到该 revision，但 `rule_exception` 缺 5 个 ADR-025 列 ⇒ 读 `RuleException` 全部 `UndefinedColumn`（一次打红 10 个测试，版本表却看起来健康） | 高 | **FIXED** | 新增幂等修复迁移 `c1f7a3e8d502`（ADR-026）；`rule_exception` 16 列 / 8 约束实测齐备 |
| T-02 | ADR-025 精确 scope 已生效，但 9 例测试与回归夹具仍按旧的"本体泛化"写（导盲犬 → service_dog） | 高 | **FIXED** | 按源忠实 scope 重新建模，见 `ANIMAL_SCOPE_REMODEL_FINAL_REPORT.md` |
| T-03 | `reality_audit._resolve_query()` 用 `datetime.now()` 而非注入的 `now` ⇒ 审计不可复现，`syn-event-006` 随真实日期漂移而失败（time bomb） | 中 | **FIXED** | threading `now`；样本有效期改宽窗口并在 note 注明 |
| T-04 | v1 evaluator（`POST /rules/evaluate`）仍按 `AnimalScope` 粗粒度匹配，未接 ADR-025 精确角色；`declared_role` 目前只作用于 resolver 路径 | 中 | **OPEN** | resolver（`effective-rules`）是 ADR-025 权威路径；v1 evaluator 属遗留三值 API。补接时需同步 `rulespec/model.py::Rule` 的 scope 字段 |
| T-05 | `policy_template_rule` 缺 ADR-025 scope 列 ⇒ 模板携带的 `service_dog` 条目在 ADR-025 生效后静默失效（被 `test_e2e_b` 抓到） | 中 | **FIXED** | 迁移 `d4a8b2f6c903` + 模型/Schema/创建端点/读取路径全链路补列 |
| T-06 | `docs/reality_audit/review_decisions_r1.json` 与 `_r2.json` 并存，容易误读"哪份有效" | 低 | **MITIGATED** | R2 登记表带 `revision` + `supersedes` 字段；`publish_reviewed_r1.py` 默认读 R2（`--registry` 可覆盖）；R2 包文本首行声明"取代 R1" |
| T-07 | Consumer UX Baseline v1 的 6 项 PARTIAL：渐进式携宠询问（§14）、搜索别名/旧名/消歧（§16）、Map Area/Lens 与手动选区（§20）、App（uni-app x）IA 同步（§22–23）、a11y 系统审计（§26）、视觉回归截图基线（§27） | 低 | **OPEN** | 均不触及冻结方向；逐条明列于 `CONSUMER_UX_BASELINE_V1_IMPLEMENTATION_REPORT.md` §4 |
| T-08 | `scripts/lint.sh` 覆盖范围与 `ruff` 手工调用不一致的风险（本轮已手工跑 `ruff check services/api services/worker tests scripts`） | 低 | **FIXED（流程）** | 本轮明确把 `scripts/` 纳入 lint 命令；建议后续固化进 CI / `lint.sh` |

---

## 2026-09-22 会话新增（v0.9-R1 Reality Layer）

| ID | 内容 | 严重性 | 状态 | 备注 |
|---|---|---|---|---|
| R-01 | Reality migration `2c7ea6ca8e30` 的 `fk_staff_response_observation_evidence_bundle_id_evidence_bundle` 名超 63 字符，PostgreSQL 截断为 `..._eviden_d504`（语义 SET NULL 不受影响，但 alembic autogenerate 可见名称漂移） | 中 | **OPEN** | 真实 DB 核验发现（`docs/reality/REALITY_DB_MIGRATION_VERIFICATION.md` 附言 A.4）；处置：新增幂等修复迁移 rename constraint（ADR-026，不修改已应用迁移），待 Docker 稳定后落库 + 回归 |
| R-02 | AC4 downgrade→re-upgrade drill 未完成：Docker daemon 在本会话窗口内两次崩溃（恢复约 17 分钟后再次消失），persistence drill 的 candidate RESTRICT / zone SET NULL 两项与 downgrade drill 被中断 | 中 | **OPEN（BLOCKED_EXTERNAL）** | 脚本 `scripts/reality_db_persistence_drill.py` 已改 savepoint 版可重跑；列入 `REALITY_DB_MIGRATION_VERIFICATION.md` 附言 A.5 清单 |
