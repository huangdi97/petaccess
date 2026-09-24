# V020 M3 Consumer Core — Report

Status: V020_M3_CONSUMER_CORE — 本轮实测完成（M3 Contract 批准后执行）
Last updated: 2026-09-24
基线：M2-A..G 已提交（HEAD `315a99a`）；M3 全部改动在本轮真实实测后落盘。

## 1. 按验收项逐条状态（证据 = 本轮实际执行）

### A. Consumer Route Foundation
- **A1 404 catch-all — PASS**：router 新增 `/:pathMatch(.*)*` → `NotFoundView.vue`
  （统一 empty 样式 + 返回首页 CTA + 隐藏 h1）。e2e `A1 — unknown paths…`：
  `/#/definitely-not-a-page` 渲染 not-found、文案正确、`consumer-app-shell` 仍在 → 非白屏。
- **A2 滚动/路径基础 — PASS**：`main.ts` 增加 `scrollBehavior`（back/forward 恢复
  savedPosition，新导航回顶）；既有 reduced-motion 守卫（
  `test_skeleton_animation_is_disabled_under_reduced_motion`）全绿；M3 未新增动画。
- **A3 路由元信息 — PASS**：全部核心路由带 `meta.title`，`router.afterEach` 设置
  `document.title`；e2e `A3 — every core route sets a document title` 断言
  `首页 · PetAccess` / `搜索场所 · PetAccess` / `页面不存在 · PetAccess` 通过。

### B. Data / Query / State Foundation
- **B1 Search 深链回填 — PASS**：SearchView `q` 初始值来自 `route.query.q`；home 的
  `?q=` 直达自动查询、`?lens=presence` 提示正确。e2e `B1` 通过。
- **B2 前进/后退同步 — PASS**：`syncRouteQuery` 在每次搜索后 push 去重 query；
  `watch(route.query.q)` 回填并重查（自 push 有 guard 防环）。e2e `B2`：
  back 后 q 清空、forward 后恢复 `q=咖啡` 且结果重新可见，通过。
- **B3 无重复 server state — PASS**：session 仍是唯一 SSOT；无新增 store 副本；
  duplicate-state 相关门禁 0 FAIL。
- **B4 API boundary — PASS**：新增数据读取全部经 generated client（
  `client.coexistenceSnapshot`、既有 search/nearby/accessAnswer）；全仓 raw
  `fetch(` 数维持 2 处（其中 1 处为代码注释）未新增。

### C. Unified CoexistenceSnapshot Consumption（ADR-029 兑现）
- **C1 — PASS**：新增消费面（Search 桌面 preview）经 `client.coexistenceSnapshot`
  读取；PlacePreview 仅以 props 呈现（labels.ts / reality.ts / copy-empty.ts 共享词汇），
  无第二套 rule/reality 模型。行级 rule 摘要收敛为共享 `ruleSummaryLabel`
  （client-core labels），列表与 preview 措辞同源。
- **C2 契约同步 — PASS**：contract/version-drift 检查全绿；generated client 类型
  未手写漂移（新增仅共享 label 函数，不涉及 DTO）。

### D. Home / Search Final Integration
- **D1 PlacePreview — PASS**：`components/domain/PlacePreview.vue`（typed props：
  place/status/snapshot/loading/error；展示 Place + Rule 摘要 + Reality 元信息 +
  Freshness + Evidence summary + 查看完整场所 CTA）。
- **D2 Search 桌面 split-view — PASS**：≥md 时 `DesktopContentContainer mode="split"`
  左列表 + 右 PlacePreview；结果行 mouseenter/focus 联动预览，桌面首条自动选中；
  移动端布局不变（390 基线未变）。
- **D3 视觉基线 — PASS**：search-fixture / search-empty 桌面（768/1440）基线与
  应用到的 home 家庭重生成，compare 42 passed；DOM audit 无横向溢出、tap ≥44px。
- **D4 Home 数据段（fixture-only）— PASS（范围如实记录）**：fixture 形态的
  数据段回归基线由 home-fixture（最近查看 / 附近已核验 / 规则待核实）与
  home-empty（0 场所）成对覆盖；`test_production_fail_closed` 保持 PASS——
  production 0-place 渲染 empty 且绝不 seed 假场所。§21 的 你可能关心 / 近期现场 /
  差异 需要真实的贡献流数据（M7 才允许），M3 如实不伪造（见边界节）。

### E. Global Loading / Empty / Error / Offline 收口
- **E1 源级守卫扩展 — PASS**：`test_ui_states` 的 REQUIRED_PER_VIEW 覆盖全部
  数据驱动视图（home/search/place/map/contribute/mine/pets/notifications/
  boundary/match-explain），新增 DECLARED_STATIC（about/privacy/settings/
  onboarding/not-found `@ui-static`、pet-new `@ui-form`），并断言**每个路由视图
  必须落入两者之一**。本轮真实接线：MineView/MatchExplainView 接入 StateMessage +
  presentDescription；5 个静态/表单视图加显式声明。单测 8 passed。
- **E2 统一错误呈现 — PASS**：新增共享 `presentDescription`（errors.ts）；首页
  数据错误此前泄漏原始后端消息（e2e 抓到：`Internal Server Error: psycopg2…`），
  已改为统一呈现；e2e `E2` 拦截 500 并断言页面不含
  SQLAlchemy/FastAPI/Tauri/Rust/psycopg2/Internal Server Error 等字样。
- **E3 Error boundary 实证 — PASS（源级 + 实证）**：`AppBoundary` 已包住全部
  RouterView（ConsumerAppShell），断言 onErrorCaptured 捕获 →
  `data-testid="app-error-boundary"` 兜底 + 重载，AppShell 不白屏；e2e 错误面
  （E2）验证 shell 可见。生产代码刻意无可触发异常视图，边界逻辑由源级守卫锁定。
- **E4 a11y — PASS**：axe-core 对 M3 新增/变更面（search split 桌面 / not-found /
  mine / match-explain）**0 critical / 0 serious**（修复了桌面 rail
  `__version-env` 用 disabled 色导致的对比度问题，改 text-muted）；移动端 6 家族
  复扫仍 0/0。

### F. Consumer Contract 收口 + 交付
- **F1 本报告落盘**：见下 §4 契约状态表。
- **F2 状态更新**：PROJECT_STATE.md 更新为 M3 完结；无新架构决策（CoexistenceSnapshot
  统一消费已在 ADR-029 决策），不新增 DECISIONS 条目。
- **F3 后端改动限定**：本轮零后端改动（0 文件触及 services/api）；未新增功能模型，
  遵守 §39 禁令。

### G. Engineering Gates（全绿，实测）
- **G1**：`check_engineering_quality.py` **0 FAIL**（60 REVIEW / 29 WARN）；
  ruff check PASS；ruff format（含 docs）468 文件干净；mypy 96 files / 0 errors。
- **G2**：backend 全量回归**重跑**：DISCOVERED 946 = **944 passed / 2 skipped /
  0 failed**（41.7s；preflight: TEST DB reset + Celery solo worker + MinIO）。
- **G3**：`pnpm lint:fe` PASS；`pnpm format:check:fe` PASS；client-h5 build
  （vue-tsc + vite）PASS；admin build PASS。
- **G4**：Playwright visual（consumer）compare **42 passed**；Playwright e2e 全量
  **75 passed / 0 failed**（新增 5 条 M3 routes 测试）。
- **G5**：零新增 ignore / exemption / ts-ignore。

## 2. 本轮新增/变更文件

- 新增：`components/domain/PlacePreview.vue`、`views/NotFoundView.vue`、
  `tests/e2e/consumer-routes.spec.ts`
- 修改：`router.ts`（meta + catch-all）、`main.ts`（scrollBehavior + title）、
  `SearchView.vue`（深链/同步/back-forward + split preview）、`errors.ts`
  （presentDescription）、`HomeView.vue` / `MatchExplainView.vue` / `MineView.vue`
  （统一错误呈现）、5 个静态视图（@ui-static/@ui-form 声明）、`DesktopRail.vue`
  （a11y 对比度）、`client-core/labels.ts`（ruleSummaryLabel）、
  `tests/unit/test_ui_states.py`（E1 守卫）、4 张桌面 search 视觉基线。

## 3. 性能基线（约同 M2，无退化）

main 134.4 kB（gzip 51.9）；HomeView 10.2 kB；SearchView 10.0 kB（+split preview
逻辑，+0.1 kB）；PlacePreview 独立 chunk ~3 kB。无无证据微优化。

## 4. 契约状态表（schema / service / API / client / UI / tests）

| 能力 | schema | service | API | client | UI | tests |
|---|---|---|---|---|---|---|
| CoexistenceSnapshot 聚合 | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED (Place/Preview) | IMPLEMENTED |
| 消费者统一消费（ADR-029） | — | — | IMPLEMENTED | IMPLEMENTED | PARTIAL→IMPLEMENTED（Search preview 接入；Home/Map 列表面仍走 list 端点） | IMPLEMENTED |
| Search 深链 / 路由 query 同步 | — | — | — | — | IMPLEMENTED | IMPLEMENTED (e2e B1/B2) |
| 404 / route meta / scroll | — | — | — | — | IMPLEMENTED | IMPLEMENTED (e2e A1/A3) |
| 统一错误呈现（无内部泄露） | — | — | — | — | IMPLEMENTED | IMPLEMENTED (e2e E2) |
| 视图状态守卫 | — | — | — | — | IMPLEMENTED | IMPLEMENTED (unit E1) |

状态词仅允许 IMPLEMENTED / PARTIAL / MISSING / NOT_WIRED / NOT_TESTED。

## 5. 边界遵守

- 未重做 M2；Map / Place Passport → M4，Reality Trace / Evidence viewer → M5，
  完整 Contribution wizard → M7（未触碰）。
- 未引入 AI recommendation / moderation / crawler / 真实数据 seed。
- 未扩 scanner、未新增整目录豁免。
- Home 你可能关心 / 近期现场 / 差异 数据段：**如实记录为 M7 数据流依赖**，本轮仅以
  fixture-only 基线（home-fixture/home-empty）覆盖既有段型，未伪造生产数据。

**Overall: V020_M3_CONSUMER_CORE = PASS**（A1–A3 / B1–B4 / C1–C2 / D1–D4 /
E1–E4 / F1–F3 / G1–G5 全部实测通过）。