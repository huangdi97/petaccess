# DECISIONS.md
# Frozen Architecture Decisions

- ADR-001: Product models Access, not Friendliness.
- ADR-002: Core domain = Place → Zone → AccessRule.
- ADR-003: Place identity = platform UUID; map IDs are external refs.
- ADR-004: ObservationClaim never auto-converts to AccessRule.
- ADR-005: Deterministic rule evaluator; LLM only parses/extracts.
- ADR-006: Multi-dimensional Provenance; no core single trust score.
- ADR-007: Client = uni-app x + Vue 3 + TypeScript.
- ADR-008: Map = provider adapter; Tencent first.
- ADR-009: Backend = FastAPI + PostgreSQL/PostGIS + Redis + Celery.
- ADR-010: Admin = Vue 3 + TypeScript + Vite.
- ADR-011: OpenAPI = API contract SSOT.
- ADR-012: No default continuous location history.
- ADR-013: Residential communities = public-space rules only.
- ADR-014: User-selected filtering is neutral; editorial moral ranking is not.
- ADR-015: MVP does not depend on mass social scraping.
- ADR-016: Demo data is synthetic by default.

- ADR-017: Place.location is a denormalized geography(Point,4326) representative
  point synced by app logic; all authoritative geometry lives in place_geometry
  (Point/LineString/Polygon/MultiPolygon). Context: nearby queries need an
  indexed point without polygon centroid ambiguity. Status: accepted.
- ADR-018: Client = uni-app x source (apps/client, HBuilderX-built, all five
  targets) + platform-neutral @petaccess/client-core (shared business logic) +
  @petaccess/client-h5 Vite app as the locally verifiable H5 vehicle for
  G07/G17. Context: uni-app x has no npm CLI build path (no vite-uts branch,
  HBuilderX-only), and HBuilderX cannot be installed headlessly (BLOCKER B-01).
  The H5 app reuses the identical core; no business logic duplicated. Status: accepted.
- ADR-019: SQLAlchemy String columns store enum values; DB reads return plain
  str, so role/status comparisons use str values. response_models coerce back
  to enums at the API boundary. Status: accepted.

任何重大变更追加正式 ADR：
- Context
- Decision
- Alternatives
- Evidence
- Migration impact
- Status

- ADR-020: 分层 Animal Scope 与 RuleException（SG-REAL-01）。Context: 现实法规
  常在同一句中"广范围管制 + 窄范围豁免"（如《上海市养犬管理条例》第23条禁止犬只
  进入商场，但书豁免导盲犬）。把豁免建成第二条独立规则时，resolver 看到同层两条
  规则按最严合成，工作犬被错误禁止；且 dog（生物学范围）与 ordinary_pet（语义
  范围）混用导致猫/其他动物被法规误覆盖。Decision: (1) Rule 的 animal_scope 沿用
  五值枚举，语义固定：dog/cat=生物学范围；service_dog=以用户声明的 working/
  in_training 角色为准（永不从照片/AI 推断，design #19）；ordinary_pet=宠物一般
  性条款，自动不约束服务犬角色。(2) 新增 RuleException（rule_id, animal_scope,
  effect, source_id NOT NULL, status, effective_from/to）：异常挂在 base rule 上，
  scope 匹配该异常声明的范围、窗口内、status=current、有 source 才生效；生效时
  替代 base rule 参与合成并给出解释步骤；窗口过期/withdrawn/superseded 自动回落
  base 规则；无 source 的异常永不生效；多条匹配异常效果冲突时 REVIEW_REQUIRED，
  绝不猜测。(3) 不写死 service_dog 分支——机制对任意 (scope, effect) 组合通用。
  (4) Guide dog 不引入新枚举：= service_dog + service_role=working（用户声明）。
  (5) Observation 永不参与 normative resolver（ADR-004 不变）。Alternatives:
  独立 allowed 规则（R1 现状建模，无法表达"豁免自本条"，同层冲突静默被吞）；
  evaluator 加 service_dog if（硬编码，违背通用性要求）；LEGAL 层互斥优先级
  （改 resolver 语义，影响面最大）。Evidence: docs/reality_audit/real_pilot_01
  resolver 探针：烘焙工坊/港汇/西岸导盲犬被禁止；smoke 测试六场景全过。
  Migration impact: additive（rule_exception 表 a7f3c2d91e04）；既有独立
  service_dog allowed 规则继续合法，可与 exception 并存。Status: accepted.

- ADR-021: EvidenceStrength 是描述性采集姿态枚举，不是可信度评分。Context:
  S7 要求区分证据获取方式（官方直抓/现场取证/可靠转述/搜索摘要/用户提交/社媒
  线索），但 ADR-006 禁止核心可信度单一评分。Decision: 六值枚举存于
  source_artifact.evidence_strength，由 collector_type + source_type +
  directness 确定性映射（strength_for_artifact），无聚合、无加权、无数值。
  SEARCH_SNIPPET/SOCIAL_LEAD 证据的候选在 Pre-Publish Validation 被硬性拦截，
  强制先完成 Evidence Repair。Status: accepted.

- ADR-022: Pre-Publish Validation 是发布边界的六项硬门（S8）。Context: R1 试点
  证明"先修系统再扩量"需要机器可执行的发布前置检查。Decision: publish() 前依次
  检查 evidence（bundle/media 锚可追溯）、place match、schema support、
  unresolved conflict（同源同位同 scope/action 的效果变更按 supersession 自动
  解决并留痕；跨来源冲突必须人工解决）、freshness（≤STALE_DAYS）、data license
  （lead-only/不存储证据不得发布）。任一失败抛稳定错误码，永不静默降级。
  Status: accepted.

- ADR-023: `mandatory_level` 是一等公民，法定约束不得被低层静默放宽
  （BLK-LAYER-02）。Context: `AccessRule` 无 `mandatory_level` 列，而
  `v05_resolver.py` 的 `legal_mandatory` 分支要求 `mandatory_level == "mandatory"`，
  故 DB 来源的 LEGAL 规则永远进不了该分支，且在合成 effect 时被排除在
  `governing` 之外。后果：运营方 `allowed` 规则可覆盖《上海市养犬管理条例》
  第二十三条的法定禁止——R1 试点的 13 项回归夹具同样不带该字段，因此测试无法
  暴露。Decision:
  (1) 词表收敛为 `mandatory | advisory | operator_discretion`（`MandatoryLevel`），
      旧值 `discretionary` 仅在读入时归一化为 `operator_discretion`
      （`normalize_mandatory_level`），不再作为新写入的合法值。
  (2) `AccessRule` 与 `RuleCandidate` 各增 `mandatory_level`（nullable, String(20)，
      带 CHECK 约束），publish() 逐字透传，绝不默认填充。
  (3) 语义：只有 `rule_layer=LEGAL` 且 `mandatory_level=mandatory` 的规则才是
      resolver 地板；`NULL` **永不**被读作 mandatory（unknown ≠ binding）。
  (4) 地板同时覆盖禁令与条件：mandatory legal `prohibited` 不可被下层
      `allowed/conditional` 放宽；mandatory legal `conditional` 的义务不可被下层
      `allowed` 抹去（effect 至少保持 `conditional`）。下层仍可更严格
      （`prohibited` 永远优先）。
  (5) 发布边界（Pre-Publish Validation 第 4b 项）拒绝 `rule_layer=LEGAL` 而未声明
      `mandatory_level` 的候选（错误码 `legal_requires_mandatory_level`），未知取值
      拒绝（`schema_unsupported`）——机器不猜。
  (6) 同步面：API（`RuleOut/RuleIn`、`CandidateIn`、`/admin/candidates/{id}/
      mandatory-level`、publish 响应）、Admin、PetAccessJSON（dump/load 校验 +
      LEGAL 必须声明）、audit（candidate.create / publish / set_mandatory_level 的
      before/after 均含该字段）、ingest 与 review register（由 layer 确定性映射，
      LEGAL→mandatory，其余→operator_discretion，可逐行覆盖）。
  Alternatives: 保持现状并登记为已知限制（被用户明确否决——不得带已知正确性缺陷
  发布）；在 resolver 内对 LEGAL 规则硬编码默认 mandatory（猜测，违背
  "unknown ≠ allowed/prohibited"，且会把 advisory 法规误升为强制）；只加列不加
  门禁（缺口可再次静默出现）。Evidence:
  `tests/unit/test_mandatory_level.py`（22 项：词表/归一化/列与约束存在性/地板
  语义/门禁/迁移回填幂等/性质不变量）、`tests/integration/test_mandatory_level.py`
  （真实 DB 的 effective-rules 地板）、`test_publish_layer_integrity.py` F2 由
  "open" 改为 fixed。Migration impact: additive（`e3b7a1c4f920`）；两列 nullable，
  回填仅填 NULL（LEGAL→mandatory，其余已知层→operator_discretion，遗留 NULL 层保持
  NULL），归一化 `discretionary`，重复执行为 no-op。Status: accepted.

- ADR-024: 手写迁移必须用 `op.f()` 声明字面约束名；登记表与库必须发布前一致
  （ENV-01 解除轮次）。Context: 依赖栈就绪后第一次真实跑迁移与全量测试，立刻暴露
  两类问题。(a) 4 个手写迁移把已带前缀的名字传给 `op.create_check_constraint` /
  `sa.CheckConstraint`，命名约定 `ck_%(table_name)s_%(constraint_name)s` 二次加前缀，
  产生 `ck_access_rule_ck_access_rule_mandatory_level` 等 7 个双前缀约束，跨 4 张表；
  与 `metadata.create_all` 建库的命名发散，且 `downgrade()` 直接失败（实测
  `constraint "ck_rule_candidate_mandatory_level" does not exist`）。
  (b) 33 条真实候选在 `rule_candidate.rule_layer` 列存在前入库，取了
  `server_default='OPERATOR_POLICY'`，而入库脚本按 manifest 幂等跳过已存在候选，
  重跑不校正 ⇒ 登记表声明 16 条 LEGAL，库中全为 OPERATOR_POLICY ⇒ 发布将把
  16 条法定规则静默降级为运营方政策（ADR-023 的静默降级，经陈旧数据到达）。
  Decision:
  (1) 手写迁移一律用 `op.f("<最终名>")` 包裹 `create/drop_constraint` 与
      `CheckConstraint(name=...)`，与自动生成迁移保持一致；
  (2) 已受影响的库由幂等修复迁移 `f4c9d2e7a831` 原地重命名（只改名字，
      同时存在性判定 ⇒ 全新库为 no-op）；
  (3) `publish_reviewed_r1.py` 预检增加**登记表↔库一致性**校验：`rule_layer` 或
      `mandatory_level` 任一不一致即硬拒绝；`--execute` 必须能读到库状态；
      发布后同时校验 `rule_layer` 与 `mandatory_level`；
  (4) `backfill_candidate_rule_layer.py` 扩展为同时校正 `mandatory_level`，
      全部经 live API 写入以留审计；
  (5) 修正 `RuleIn` 缺遗留值归一化：抽出共享注解类型
      `NormalizedMandatoryLevel`（`Annotated[MandatoryLevel, BeforeValidator(...)]`），
      读写路径共用同一词表。
  Evidence: 全量 `pytest` **319 passed / 0 failed**；`alembic` up/down/up 往返通过；
  修复后 `REMAINING DOUBLE-PREFIXED: 0`；33 条候选层级/规范力与登记表一致
  （LEGAL/mandatory 16，`LEGAL` 缺 level = 0）；Playwright **14 passed**；
  新增 8 个预检守卫单测 + 5 个 `/extras` 集成测试。
  Migration impact: additive（`f4c9d2e7a831`，仅重命名约束）；无数据变更。
  Status: accepted.


---

## ADR-025 — 源忠实动物范围：本体父关系不得扩张法律效力

- Context: `《上海市养犬管理条例》第二十三条` 禁止犬只进入商场，但书为
  「盲人携带导盲犬的，不受本条规定的限制」。旧模型按 ADR-020 的理由
  （"导盲犬 is-a 服务犬 + service_role=working"）把该但书存成
  `animal_scope='service_dog'`，于是存储行声称**所有**服务犬都不受法定禁止约束。
  这是把**本体关系当法律论证**。同时 `allowed/prohibited/conditional` 也无法表达
  「该但书为窄主体移除基础禁止」（豁免/但书）与「场所负有积极便利义务」
  （《无障碍环境建设法》第46条「提供便利」），把义务塞进 `allowed` 会把义务抬成无条件许可。
- Decision:
  (1) 新增精确分类 `AnimalRole`
      （`ORDINARY_DOG` / `GUIDE_DOG` / `HEARING_DOG` / `ASSISTANCE_DOG` /
      `OTHER_SERVICE_DOG` / `POLICE_DOG` / `MILITARY_WORKING_DOG`）；
      `POLICE_DOG` 与 `MILITARY_WORKING_DOG` **不属于**服务犬（不辅助残障人士）。
  (2) 新增 `source_scope_exact` / `subject_scope_normalized` / `normalization_type`
      （`exact` | `parent_group_for_query_only` | `legal_interpretation_required`）。
      **只有 `exact` 才赋予法律效力**；裸 `service_dog`（无归一化）不产生任何效力。
      本体父关系**仅**用于查询侧扩张（搜索 / 分类 / UI 分组）。
  (3) 新增 `NormativeEffect`
      （`permission` / `prohibition` / `conditional_permission` /
      `exempt_from_prohibition` / `facilitation_required`）与 `HolderScope`
      （`any_handler` / `person_with_disability`），作为 `RuleEffect` 旁挂的规范层；
      `NORMATIVE_TO_EFFECT` 把 `facilitation_required` 降为 `conditional`，**绝不降为 `allowed`**。
  (4) resolver 新增 optional `declared_role`：用户声明"我是助听犬"时不做查询扩张，
      因此**助听犬不继承导盲犬但书**；未声明时仍扩张（"找出可能适用的规则"）。
  (5) 迁移 `a2d5e8b91c47` additive；回填**保守且绝不扩张**：`dog`/`ordinary_pet` → `exact`，
      `service_dog` → NULL + `legal_interpretation_required`（正是那个未证成的泛化，
      在人工重新建模前不生效）。
  (6) 不变量（测试固定）：
      `ONTOLOGY_PARENT_RELATIONSHIP MUST_NOT IMPLY_LEGAL_SCOPE_EXPANSION`。
- Evidence: `tests/unit/test_animal_scope.py`（19 例 + 2 property 各 300 例）；
  `tests/unit/test_rule_exceptions.py`、`tests/integration/test_rule_exceptions.py`；
  全量 `pytest` 349 passed / 0 failed；`ruff` / `mypy` / ESLint / Prettier / 两端 build / E2E 16 passed。
- Migration impact: `a2d5e8b91c47`（additive）+ 修复迁移 `c1f7a3e8d502`
  （补 `rule_exception` 漏列）+ `d4a8b2f6c903`（`policy_template_rule` 补 scope 列）。
- Status: accepted.

## ADR-026 — 已应用迁移被后补修改 ⇒ 必须用幂等修复迁移，且迁移必须可重入

- Context: 2026-09-15 接管时实测：`alembic_version` 已到 `a2d5e8b91c47`，但
  `access_rule` / `rule_candidate` 有 ADR-025 的 5 个 scope 列，`rule_exception` **没有**。
  根因：该迁移先在两张表上被应用（打上版本号），之后才把 `rule_exception` 补进同一个文件，
  而 Alembic 不会重跑已应用的 revision。后果是任何读 `RuleException` 的路径直接
  `UndefinedColumn`，一次性打红 10 个测试，而版本表看起来完全健康。
- Decision:
  (1) **不修改已应用的迁移**（会重演同一缺陷），而是新增幂等修复迁移 `c1f7a3e8d502`：
      逐列做存在性判定后再 `add_column`，逐约束判定后再 `create_check_constraint`，
      回填语句全部以 `... IS NULL` 守卫 ⇒ 全新库为 no-op、旧库补齐。
  (2) 手写迁移一律使用 `op.f()` 显式约束名（沿用 ADR-024），避免命名约定二次加前缀。
  (3) 迁移的 `upgrade()` 必须具备**可重入性**：任何 `add/drop` 前先 inspect，
      使"部分应用"不再可能静默存在。
- Evidence: `c1f7a3e8d502` 后实测 `rule_exception` 16 列 / 8 约束齐备；
  `alembic upgrade head` → `d4a8b2f6c903`；全量 `pytest` 349 passed。
- Migration impact: additive；不改数据语义。
- Status: accepted.

## ADR-027 — Consumer UX Baseline v1：首页是 Decision Home，地图是一级 Tab

- Context: `UI_CORE_CLOSURE_REPORT.md` 的页面级交付真实存在，但首页实现是 **Map Home**
  （`view` 默认 `map`），与冻结方向「Search-first / 首页不是 Map-first / 首页是 Decision Home」
  直接冲突；地图也没有独立路由。同时 `PlaceView` 的分区结论、核验范围等语义
  需要一个统一的入口把「已核验 / 待核实」讲清楚。
- Decision:
  (1) 首页改为 **Decision Home**（`apps/client-h5/src/views/HomeView.vue` 重写）：
      覆盖范围头 → 「去之前，查清规则」→ 搜索框 → 三个查询视角
      （`看场所规则` 默认 / `携带动物` / `共处偏好`）→ 最近查看 → 类别 → 附近已核验 / 规则待核实
      → 贡献降级为页脚。
  (2) 地图前移为 `views/MapView.vue` 并新增一级路由 `/map`；底部导航
      `首页 / 地图 / 贡献 / 我的`。
  (3) 六项修正：核验范围精确到「动物 · 区域」；`待核实场所` → `规则待核实`；
      状态中性（不大面积绿）；条件表述为「进入前需满足」；每条答案带「为什么？」；
      贡献降低视觉优先级。
  (4) `UNKNOWN ≠ ALLOWED` 与「规则待核实」的语义在页面**前置声明**，不依赖数据是否加载成功。
  (5) 消费端接通 ADR-025：`ActivePet.declared_role` → `client.effectiveRules(declared_role)`
      → resolver 不扩张查询。
  (6) `贡献` 可无场所打开（Tab 需要），此时**不猜场所**，显式要求先选定。
- Evidence: E2E 16 passed（含 3 个新增 Consumer UX 用例）；H5/Admin build、ESLint 0、
  Prettier、vue-tsc 0；`pytest` 349 passed。
- Migration impact: 无（前端 + `client-core` 类型）。
- Status: accepted.

## ADR-028 — Reality Layer：观察事实经人工裁决成为消费端可见声明，AI 永不写 reality_decision

- Context: v0.9-R1 需要把「现实观察」（动物在场、工作人员反应、设施状态）与
  规则（place → zone → access_rule）分开呈现，但项目此前只有规则面，观察只能
  以 ObservationClaim 存在且 ADR-004 禁止其自动转规则。消费端「现实怎么样」没有
  独立、可展示、带时效的答案模型。
- Decision:
  (1) 新增四张表（`reality_candidate` / `observed_presence` /
      `staff_response_observation` / `animal_facility`，迁移 `2c7ea6ca8e30`，
      additive-only）：candidate 是待审队列（AI 可产出，`DERIVED_AI_ONLY`），
      发布表只承载人工 VERIFIED 声明，三者共用 Evidence + Review + Freshness 姿态。
  (2) **reality_decision 只允许人类写入**（MODERATOR 角色端点为唯一入口，
      reviewer/decided_at 落库 + `reality.decision` 审计）；VERIFIED /
      VERIFIED_WITH_NOTE 才发布 claim，HOLD / REJECTED 不发布。
  (3) 新鲜度是一等事实：`reality_summary.freshness_for` 按显式阈值分桶
      （7/30/90/365 天），过期事实绝不呈现为「近期」；`FRESH→fresh` 等在
      API 边界映射为枚举存入。
  (4) 摘要词汇冷冻：空记录 = `INSUFFICIENT_OBSERVATION ≠ 没有动物`；
      单次观察永不上升为「经常/高频」（需要多来源阈值，未定义前只报计数与
      last-seen）；存在未人工核验记录时摘要降级 `INSUFFICIENT_OBSERVATION`。
  (5) 工作人员身份永不暴露：`staff_response_observation` 只存 `actor_role`。
  (6) Observation ≠ Rule（ADR-004 不变）：reality 表永不写入 evaluator 输入。
- Alternatives: 复用 ObservationClaim + 元数据补时效；直接在 place 上加观察枚举列。
  前者语义混用（claim 是用户声明的争议可撤销事实，非可发布的核验声明）、后者
  使「观察」退化为属性、两者都无法表达「谁核验的、何时核验、新鲜度如何」。
- Evidence: `tests/test_reality_summary.py`（新鲜度边界、摘要状态机、
  人为裁决红线）；`pytest` 28 passed；`ruff` / `mypy` 0 errors。
- Migration impact: additive（`2c7ea6ca8e30`，4 表 + FK + 索引，downgrade 完整）。
- Status: accepted.

---

## ADR-029 — 统一消费快照：CoexistenceSnapshot 是 Home/Search/Map/Place 的唯一聚合，
  Divergence 只描述差异、永不改写规则与现实

- Context: v0.9-R1 消费端必须同时呈现规则面（AccessAnswer）与现实面
  （RealityAnswer）。若每个页面各自调用两个端点再自行拼装，会出现两类漂移：
  (a) 同一状态在 Home、Map、Place 被三套话术描述；(b) 页面「自己算」规则结论
  （AGENTS 红线「禁止页面自行算 Rule」）。此外「规则说禁止但现场有动物」这类
  跨层差异此前没有统一词汇，页面只能各自发明。
- Decision:
  (1) 新增 `app/services/coexistence_snapshot.py`：纯函数 `build_coexistence_snapshot`
      把 RuleAnswer + RealityAnswer + StaffResponseSummary + FacilitySummary +
      RuleRealityDivergence + EvidenceSummary 装进一个不可变快照（含 version 字段）；
      `to_plain` 负责 JSON 安全序列化。Home / Search / Map / Place 一律消费
      `POST /api/v1/places/{id}/coexistence` 这一端点，禁止各自重新计算。
  (2) 新增 `app/services/rule_reality_divergence.py`：六状态词汇冷冻
      （RULE_REALITY_ALIGNED / RULE_PROHIBITS_BUT_OBSERVED /
      RULE_ALLOWS_BUT_NO_RECENT_RECORD / RULE_UNKNOWN_BUT_OBSERVED /
      RULE_CONDITIONAL_AND_OBSERVED / INSUFFICIENT_DATA）。Divergence **只描述
      差异**：它从 rule_answer/reality_answer 派生、echo 输入、绝不修改任何一层；
      NO_RECENT_RECORD 一律带「≠ 没有动物」措辞；UNKNOWN 规则 + 观察到 =
      RULE_UNKNOWN_BUT_OBSERVED，绝不转成允许/禁止；DISPUTED / 未核验 → INSUFFICIENT_DATA。
  (3) 现实贡献独立于规则贡献：新增 `POST /api/v1/places/{id}/reality/contributions`
      （登录即可，不要求 MODERATOR），三条结构化分支
      （observed_presence / staff_response / animal_facility）落成 REVIEW_PENDING
      候选，`verification_status=UNVERIFIED`，`reality_decision` 保持空 —— AI 永不写。
  (4) Admin 侧 Reality 三页面（Dashboard / CandidateQueue / Claims）直连既有
      `/admin/reality/*` 端点；候选裁决唯一入口是人工决策端点。
- Alternatives: 让每个页面自行组合 AccessAnswer + RealityAnswer（拒绝：页面再解释
  一次状态就多一份无审查解释）；把 Divergence 并入 RealitySummary（拒绝：Divergence
  是规则×现实的双层关系，不属于任何一层）；贡献直接写发布表（拒绝：违反 ADR-028
  人工裁决纪律）。
- Evidence: `services/api/tests/test_rule_reality_divergence.py`（37 用例：六状态
  全可达 + 24 组笛卡尔积完备且确定性 + 红线）；`test_coexistence_snapshot.py`
  （10 用例：六合一捆绑、to_plain JSON 安全、Divergence 只描述）；本会话非 DB
  门禁：pytest 75 passed / ruff 全绿 / mypy 96 files 0 errors / H5·Admin
  vue-tsc + build 通过（全量 DB 回归待 Docker 恢复后执行，见
  `docs/reality/TEST_TREE_INVENTORY.md`）。
- Migration impact: 无（纯代码 + 既有 Reality 表）。
- Status: accepted.
