# V020 M5 Reality Trace + Evidence — Report

Status: V020_M5_REALITY_TRACE_AND_EVIDENCE — 本轮实测完成（M5 Contract 批准后执行）
Last updated: 2026-09-24
基线：M2/M3/M4 已提交（HEAD `624336d`）；M5 全部改动在本轮真实实测后落盘。

## 1. 按验收项逐条状态（证据 = 本轮实际执行）

### A. Reality Trace Surface
- **A1 新路由 + 深链 — PASS**：router 新增 `/#/place/:id/reality`（name
  reality-trace，meta.title「现场轨迹」→ afterEach 标题正确）；Passport
  RealityPanel 增加「查看现场轨迹」CTA（`open-reality-trace`）链接到该路由。
  e2e `A1`：Passport → CTA → trace 页渲染 + URL 校验 + 直接深链可访问，通过。
- **A2 Trace 内容渲染 — PASS**：`RealityTraceView` 从 `client.realityTrace`
  渲染 summary（现场轨迹（≠ 规则）标题 + 后端共享词库标签）、fact_sections
  （最近记录/来源类型/时间/工作人员处理/动物相关设施）与 review_sections
  （核验/一手来源/是否存在争议），note 保留。e2e `A2/B2` 断言两分区标题与段渲染。
- **A3 观察时间线 — PASS**：`client.observations` 行渲染（freshnessLabel 时效、
  animal_scope/observed_action、staff_action、note、dispute → EvidenceStatus）；
  空时间线走 `EMPTY_STATE_COPY.REALITY`（暂无足够现场记录 —— 暂无记录不代表
  没有动物）。e2e `A3`：真实行或空块必现其一；拦截空 observations → trace-empty
  文案正确，通过。
- **A4 状态完备 — PASS**：loading（SkeletonList）/ error（StateMessage
  title=未能取得现场轨迹 + presentError，无内部字样）/ empty（REALITY copy）/
  offline 由 shell 承担；深链 back/forward 由 hash history 正常；h1（visually
  hidden）+ meta title 正确。e2e `A4`：标题断言 + 拦截 500 → 错误态 + 无
  SQLAlchemy/FastAPI/psycopg2 泄漏，通过。
- **A5 桌面布局 — PASS**：trace 页接入 `DesktopContentContainer
  mode="single-column"`；visual `reality-trace` 家族（390/768/1440）compare 全绿。

### B. Evidence Surface
- **B1 统一证据呈现 — PASS**：trace 页证据行经 `EvidenceStatus`（
  verified/pending/disputed/historical，dispute_status 映射）+ `EvidenceMeta`
  （evidence_count 条依据）+ `freshnessLabel`（时效）渲染；RealityPanel 第 70 行
  原有 `reality_verification_state` 原始枚举泄漏同步修复为 `EvidenceStatus`
  映射。e2e `B1`：页面无 VERIFIED/PENDING/DISPUTED/HISTORICAL/dispute_status/
  reality_verification_state 原始字符串，通过。
- **B2 事实与核验分离 — PASS**：`trace-facts`（观察到的事实）与 `trace-review`
  （核验姿态）分区标题不同、review 区用 sunken 表面呈现（e2e 断言两区
  backgroundColor 不同 —— 非仅颜色区分）；notes（如「平台核验只说明事实被确认，
  不改变“未观察到”的含义」）保留。e2e `A2/B2` 通过。
- **B3 规则证据保持原位 — PASS**：规则 provenance 仍在 Passport Section 7；
  trace 页仅消费 realityTrace/observations，无规则证据复制（源级检查：视图未
  调用 rules/accessAnswer）。
- **B4 a11y — PASS**：axe 对 trace 页（1440 桌面 + 390 移动）**0 critical /
  0 serious**。

### C. Contract / Backend 边界
- **C1 后端零功能新增 — PASS**：本轮 **backend 0 文件改动**（services/api 未触及）；
  结束前全量回归重跑：DISCOVERED 946 = **944 passed / 2 skipped / 0 failed**
  （72.6s；TEST DB reset + Celery + MinIO）。
- **C2 client 契约不漂移 — PASS**：realityTrace/observations 类型沿用既有
  client 方法（观测到 `client.observations` 返回未包裹数组，直接消费）；
  contract/version-drift 检查全绿。

### D. Engineering Gates（全绿，实测）
- **D1**：`check_engineering_quality.py` **0 FAIL**（60 REVIEW / 30 WARN）；
  ruff check PASS；ruff format（含 docs）470 文件干净；mypy 96 files / 0 errors。
- **D2**：backend 全量回归重跑 → 见 C1。
- **D3**：`pnpm lint:fe` PASS；`pnpm format:check:fe` PASS；client-h5 build
  （vue-tsc + vite）PASS；admin 未触及。
- **D4**：Playwright visual compare **45 passed**（+reality-trace 家族；
  place 家族因 RealityPanel CTA/验证行变更重生成）；Playwright e2e 全量
  **87 passed / 0 failed**（+5 条 M5 测试）。
- **D5**：零新增 ignore / exemption / ts-ignore。

### E. 交付
- **E1 本报告落盘**（此文件）。
- **E2**：PROJECT_STATE.md 更新为 M4 完结 + M5 状态；无新架构决策，不新增
  DECISIONS 条目。
- **E3 视觉基线**：reality-trace（390/768/1440 新家族）+ place-unknown /
  place-conditional（RealityPanel CTA + 验证状态行变更）重生成，compare 45 passed。

## 2. 本轮新增/变更文件

- 新增：`views/RealityTraceView.vue`（199 行）、`tests/e2e/reality-trace.spec.ts`
  （A1–A4/B1/B2 共 5 条）、视觉基线 `reality-trace-h5-{390,768,1440}`。
- 修改：`router.ts`（reality-trace 路由 + meta.title）、`components/RealityPanel.vue`
  （placeId prop + 查看现场轨迹 CTA + 原始枚举修复为 EvidenceStatus）、
  `views/PlaceView.vue`（传入 place-id）、`tests/unit/test_ui_states.py`
  （RealityTraceView 登记入 E1 守卫）、`tests/visual/consumer.spec.ts`
  （reality-trace 拍摄）、place 家族基线。

## 3. 契约状态表（schema / service / API / client / UI / tests）

| 能力 | schema | service | API | client | UI | tests |
|---|---|---|---|---|---|---|
| Reality Trace（fact/review 分离） | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | PARTIAL→IMPLEMENTED（本轮 UI 消费面建立） | IMPLEMENTED (e2e A2/B2) |
| 观察时间线 | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED (e2e A3) |
| 统一 Evidence 呈现（无原始枚举） | — | — | — | — | IMPLEMENTED | IMPLEMENTED (e2e B1) |
| 路由/深链/标题 | — | — | — | — | IMPLEMENTED | IMPLEMENTED (e2e A1/A4) |
| 状态完备（loading/empty/error/offline） | — | — | — | — | IMPLEMENTED | IMPLEMENTED (e2e A3/A4 + E1 守卫) |
| 规则 provenance | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED（留 Passport §7，未复制） | IMPLEMENTED |

状态词仅允许 IMPLEMENTED / PARTIAL / MISSING / NOT_WIRED / NOT_TESTED。

## 4. 边界遵守

- 未新增后端模型（trace API 既有 fact/review 分离，仅建 UI 消费面）。
- 规则 Evidence viewer 未迁移：规则 provenance 留 Passport Section 7。
- Contribution wizard / moderation / 真实数据 seed → M7，未触碰。
- 未引入 AI recommendation / crawler / 社媒 ingest；未扩 scanner、未新增整目录
  豁免；未重做 M2/M3/M4。

**Overall: V020_M5_REALITY_TRACE_AND_EVIDENCE = PASS**（A1–A5 / B1–B4 /
C1–C2 / D1–D5 / E1–E3 全部实测通过）。