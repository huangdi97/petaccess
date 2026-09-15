# UNFINISHED_TASK_MATRIX.md

> 生成时间：2026-09-15（GMT+8）· 基线 HEAD `53c4c03` · 接管后执行结果
> 状态词表：`DONE` / `PARTIAL` / `NOT_DONE` / `BLOCKED_HUMAN` / `BLOCKED_EXTERNAL` / `REGRESSED`
> 本矩阵是后续执行的唯一依据；每行 Evidence 都是**本轮实测**。

---

## A. Workstream A — Animal Scope 精确修复

| Workstream | Item | Status | Evidence | Next |
|---|---|---|---|---|
| A Scope | 本体父关系不扩张法律效力（invariant） | **DONE** | `app/rulespec/animal_scope.py`；`tests/unit/test_animal_scope.py::test_06*`（5 例）+ property 300 例 | — |
| A Scope | AnimalRole 分类（含 POLICE / MILITARY 独立） | **DONE** | `models/enums.py::AnimalRole`（7 角色）；`test_07/08/08b` | — |
| A Scope | `source_scope_exact` / `subject_scope_normalized` / `normalization_type` | **DONE** | 迁移 `a2d5e8b91c47` + 修复迁移 `c1f7a3e8d502`；`rule_exception` 16 列实测齐备 | — |
| A Scope | Guide dog 精确 scope（不泛化为 service_dog） | **DONE** | `test_01/02/03/04`；R2 登记表 8 条 `guide_dog`；`test_guide_dog_carve_out_does_not_extend_to_other_service_roles` | — |
| A Scope | 国家无障碍规则（FACILITATION_REQUIRED + holder_scope） | **DONE** | `NormativeEffect.FACILITATION_REQUIRED`；`NORMATIVE_TO_EFFECT` 映射为 conditional；`test_05/05b/05c` | 生产数据接入需人类评审 |
| A Scope | 上海地方条例建模（Base Rule + RuleException，非 SERVICE_DOG ALLOWED） | **DONE** | `test_01/02`；`LayeredException.normative_effect=exempt_from_prohibition` | — |
| A Scope | Operator Policy 精确 scope（Disney / 前滩太古里 / 上海图书馆） | **DONE** | `test_09`（Disney + leash）、`test_10`（图书馆 3 个精确 scope） | 图书馆需拆 3 条（已在 R2 标 HOLD） |
| A Scope | `gh-outdoor-keep` 拒绝且不得入发布队列 | **DONE** | R2 登记表 `RECOMMEND_REJECT` + `INSUFFICIENT_PLACE_ZONE_EVIDENCE` / `LEGAL_SCOPE_CONFLICT`；`test_11` | 拿到运营方 Zone policy 后新建 Candidate |
| A Scope | §5.8 十一项 Scope Tests | **DONE** | `tests/unit/test_animal_scope.py`（19 例 + 2 property） | — |
| A Scope | §5.8 配套：unit / property / integration / migration / API contract | **DONE** | `pytest` 349 passed；迁移 up 实测；`test_rule_exceptions`（integration 6 例） | — |
| A Scope | §5.8 配套：Admin / PetAccessJSON | **PARTIAL** | `petaccessjson` 已带 `VALID_MANDATORY_LEVELS`；Admin 候选详情消费 scope 字段 —— **Admin 侧 scope 表单尚未加** | 加 Admin scope 编辑（非 A Gate 阻塞） |
| A Scope | v1 evaluator（`POST /rules/evaluate`）精确 scope | **PARTIAL** | 仍按 `AnimalScope` 粗粒度匹配；未接 ADR-025 精确角色 | 记入 TECH_DEBT（见 A 报告 §6） |
| **A Gate** | `ANIMAL_SCOPE_REMODEL_GATE` | **PASS** | 见 `ANIMAL_SCOPE_REMODEL_FINAL_REPORT.md` | — |

---

## B. Workstream B — P0 Human Review / Publish Closure

| Workstream | Item | Status | Evidence | Next |
|---|---|---|---|---|
| B Review | R1 → **R2** 登记表与包（建议全部重算，不继承） | **DONE** | `docs/reality_audit/review_decisions_r2.json`（33 条）；`HUMAN_REVIEW_PACKET_R2.md`；`HUMAN_REVIEW_QUICK_TABLE_R2.md`；`HUMAN_REVIEW_DECISIONS_R2.json`；`scripts/gen_human_review_packet_r2.py` | — |
| B Review | 33 条人类最终决定 | **BLOCKED_HUMAN（GOV-01）** | R2 登记表 `final_decision` / `reviewer` / `reviewed_at` **全空**；`test_11b_no_registry_row_is_pre_signed_by_the_agent` 固定该不变量 | 具名评审员逐条签署 |
| B Publish | Pre-Publish dry-run | **BLOCKED_HUMAN** | 门禁在未签署时硬拒绝（退出码 3），设计使然 | 签署后执行 |
| B Publish | 首批 Publish（10–20 条最强证据） | **BLOCKED_HUMAN** | 写库能力已就绪（迁移往返通过）；发布预检双重把关就位 | 签署后执行 |
| B Publish | Withdraw / Supersession / Watch 演练 | **PARTIAL** | Rollback L1 有 5 个真实 DB 集成测试（`test_rollback_l1.py`）；supersession 由 `test_v05_e2e::test_e2e_c` 覆盖；**watch 通知幂等性未在真实批次上演练** | 依赖首批 Publish |
| B Publish | GOV-01 解除判定 | **未解除** | 正式 review decisions 文件三项全空 | 见 `BLOCKERS.md` |
| **B Gate** | `PILOT_REVIEW_PUBLISH_GATE` | **BLOCKED_HUMAN** | 仅剩具名人类签署 | — |

---

## C. Workstream C — Consumer UX Baseline v1

| Workstream | Item | Status | Evidence | Next |
|---|---|---|---|---|
| C UX | Decision Home（search-first，非 Map-first） | **DONE** | `apps/client-h5/src/views/HomeView.vue` 重写；E2E `decision home is search-first...` | — |
| C UX | 地图为一级 Tab（`/map`） | **DONE** | 新增 `views/MapView.vue` + `/map` 路由 + 底部导航 `首页/地图/贡献/我的` | — |
| C UX | 首页六项修正（§12） | **DONE** | `已核验：<动物 · 区域>`、`规则待核实`、中性徽标、`进入前需满足`、`为什么？`、贡献降级为页脚 | — |
| C UX | 三个查询视角（§13，默认「看场所规则」） | **DONE** | `PERSPECTIVES` + `aria-pressed`；E2E 断言默认态 | 共处偏好跳转 `/boundary`（v1 口径） |
| C UX | 携带动物渐进询问（§14） | **PARTIAL** | 已有 PetProfile CRUD + `declared_role` 通道；**"体重→肩高→数量→推车"的渐进式提问 UI 未实现** | 需单开增量 |
| C UX | 共处偏好输出（§15，符合/不符合/未知，无评分） | **DONE** | `BoundaryView` 逐项判定 + 「不是对场所的评分」；E2E 覆盖 | — |
| C UX | Search（名称/分店/地址/别名/旧名 + 消歧 + 四类错误区分） | **PARTIAL** | `SearchView` 已具备名称搜索 + nearby 回退 + 8 筛选；**别名/旧名与四类错误区分未实现** | 需单开增量 |
| C UX | Recent History（2–3 条，重新求值，未登录可用，可清空） | **DONE** | `HomeView` localStorage 上限 3 + 清空 + 每次打开重新求值 | — |
| C UX | Place Detail / Rule Passport（10 段） | **DONE** | `PlaceView` 10 段（UI-CORE-CLOSURE P0-1）+ 分区按需评估 | — |
| C UX | Rule Trace（消费 resolver explanation） | **DONE** | `/place/:id/why` + `MatchExplainView`；E2E `explainable match shows derivation steps` | — |
| C UX | Map Tab（Area→Lens→Filter→Marker→Sheet→Detail；失败回退列表；定位拒绝→手动区域） | **PARTIAL** | 地图壳 + 聚类 + BottomSheet + list 回退 + 定位拒绝文案齐备；**Area/Lens 选择器与「手动选择区域」控件未实现** | 需单开增量 |
| C UX | Contribution 统一流程（§21） | **DONE** | `ContributeView` 四入口 + 无场所时不猜（新增守卫 + E2E） | — |
| C UX | Mini Program / App / H5 一致性 | **PARTIAL** | H5 与 client-core 一致；App（uni-app x）侧未同步新 IA | 需单开增量 |
| C UX | UI States（§25 十一态） | **DONE** | `UI_STATE_MATRIX.md` + `StateMessage` / `SkeletonList`；离线 E2E 覆盖 | — |
| C UX | Accessibility（§26） | **PARTIAL** | 44px 目标、语义标签、`aria-pressed`、不靠颜色单独表达已具备；**200% zoom / reduced-motion 未系统验证** | 需 a11y 审计 |
| C UX | Consumer UX Tests（§27 十一项 + 视觉回归） | **PARTIAL** | E2E 16 passed（含 anonymous search→answer、branch、zone、share、map fallback、guide scope）；**视觉回归截图基线未建立** | 需接入截图基线 |
| C UX | build / lint / typecheck / backend regression | **DONE** | H5 build ✓、Admin build ✓、ESLint 0、Prettier ✓、vue-tsc 0、`pytest` 349 passed | — |
| **C Gate** | `CONSUMER_UX_BASELINE_V1_GATE` | **PASS（带明列 PARTIAL）** | 见 `CONSUMER_UX_BASELINE_V1_IMPLEMENTATION_REPORT.md` §Gate | 6 项 PARTIAL 见 C 报告 §4 |

---

## D. 30–50 Place 扩量

| Item | Status | Evidence | Next |
|---|---|---|---|
| 启动 `WORKBUDDY_REALITY_AUDIT_30_50_GOAL.md` | **NOT_ALLOWED** | `ANIMAL_SCOPE_REMODEL_GATE = PASS` 但 `PILOT_REVIEW_PUBLISH_GATE = BLOCKED_HUMAN` | **两 Gate 同时 PASS 才允许** |

---

## E. 本轮顺带发现的技术债

| ID | 内容 | 处置 |
|---|---|---|
| T-01 | 迁移"部分应用后打标"（`rule_exception` 缺 5 列） | **FIXED**（`c1f7a3e8d502`） |
| T-02 | ADR-025 精确 scope 未同步旧测试/旧数据 | **FIXED**（见 A 报告） |
| T-03 | 审计引擎忽略注入 `now`（time bomb） | **FIXED** |
| T-04 | v1 evaluator 未接 ADR-025 精确角色 | 记入 `TECH_DEBT_REGISTER.md` |
| T-05 | `policy_template_rule` 缺 scope 列（模板 servicedog 静默失效） | **FIXED**（`d4a8b2f6c903`） |
| T-06 | `CLAUDE`/文档中 `docs/reality_audit/review_decisions_r1.json` 与 R2 并存 | 已在 R2 登记表 `supersedes` 字段显式声明 |
