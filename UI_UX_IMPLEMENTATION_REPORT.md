# UI_UX_IMPLEMENTATION_REPORT.md

> P3 前端生产化实现报告
> 对应 `WORKBUDDY_PRODUCTION_MASTER_GOAL.md` §5.10 与 `UI_UX_IMPLEMENTATION_SPEC.md` §12
> 基准 commit `716b163` · 生成时间 2026-09-14（GMT+8）

---

## 1. 结论

```text
UI_FRONTEND_PRODUCTION_GATE = PARTIAL
```

设计系统层与状态层已达成且有机读守卫；**地图交互壳、Place Detail 完整 Section、视觉回归基线未达成**，因此不能标 PASS。未达成项中有 3 项受外部条件直接阻塞（ENV-01 / B-04），1 项可立即实施但尚未做。

---

## 2. 交付清单

### 2.1 设计令牌（`packages/design-tokens`）

| 文件 | 内容 |
|---|---|
| `src/tokens.css` | color(bg/text/border/accent/map/status/skeleton) · space(1–7) · radius(sm/md/lg/pill) · font(size/weight/line-height) · elevation(0–3) · motion(fast/base/slow/ease) · layout(max-width/touch-target/tabbar) |
| `src/index.ts` | `STATUS_SEMANTICS`（6 态，强制 icon+label+ariaLabel+colorVar+bgVar）· `SOURCE_BADGES`（7 类）· `PAGE_STATES`（8 态，强制 icon+title+description）· `ANSWER_STATUS_TO_SEMANTIC` / `EFFECT_TO_SEMANTIC` 归一化 · `FORBIDDEN_COPY` / `REQUIRED_COPY` · `BREAKPOINTS` · `TOUCH_TARGET_PX` |

**此包在接管时为空的目录**——规范 §9 要求它存在，但实际无实现。本轮补齐。

### 2.2 消费方

| 应用 | 接入方式 |
|---|---|
| `apps/client-h5` | `styles.css` `@import` + 短名别名；`StatusBadge.vue` / `SourceBadge.vue` / `StateMessage.vue` / `SkeletonList.vue` / `composables/useOnline.ts` |
| `apps/admin` | `package.json` 声明依赖；`styles.css` `@import` + 别名；`StatusBadge.vue` / `SourceBadge.vue` / `StateMessage.vue` |
| `apps/client`（uni-app x） | ❌ **未接入**（需 HBuilderX，B-01） |

**关键设计**：两端都用"短名别名"承接令牌（`--bg: var(--pa-color-bg-app)`），因此**存量视图标记无需改动**即可切换到单一真源。这避免了"为了接设计系统而重写 24 个 Admin 视图"的高风险操作。

### 2.3 消除硬编码颜色

| 位置 | 处理 |
|---|---|
| Admin `styles.css` | 9 处 hex + 1 处 rgba → 令牌 |
| H5 `styles.css` | 8 处 hex + 2 处 box-shadow rgba → 令牌（阴影改用 `--pa-elevation-1/2`） |
| H5 `MatchExplainView.vue` | 内联 `style="color:#fff"` → `.tag--on-solid` 类 |
| Admin `PlacesView.vue` | 内联 `style="background:#fafbfc"` → `.panel--sunken` 类 |

新增令牌：`--pa-color-map-grid-a/b`、`--pa-color-map-pin-border`、`--pa-color-map-label-bg`、`--pa-color-skeleton-sheen`。

**机读守卫**：`test_design_tokens.py::test_app_stylesheets_and_components_have_no_hardcoded_colours` 扫描两端全部 `.css`/`.vue`，任何 hex/rgb 字面量即失败。

### 2.4 状态完整性

新增 `PAGE_STATES` 8 态词汇 + 两端 `StateMessage.vue` + H5 `SkeletonList.vue` + `useOnline.ts`，接入 HomeView / SearchView / PlaceView / BoundaryView。

**离线语义的决定**：离线**不排队写入**。理由是未经确认的核验会生成假的证据记录，而证据完整性是本产品的全部意义。因此离线时禁用提交并说明原因，而非静默缓存。

### 2.5 中性文案

`FORBIDDEN_COPY`（雷店/黑榜/红榜/恶心/脏/没素质/反宠/爱宠人士/文明指数/遇宠率/星级）由 `test_design_tokens.py` 扫描两端全部用户可见 `.vue`/`.ts`，零命中。`UNKNOWN` 措辞被断言不得表述为允许（`"尚未核验"` + `"不代表允许"`）。

---

## 3. 验证证据（本轮实测）

| 检查 | 命令 | 结果 |
|---|---|---|
| Lint | `ruff check .` | ✅ All checks passed |
| 类型（后端） | `mypy services/api/app` | ✅ 74 files, no issues |
| 类型（H5） | `vue-tsc --noEmit` | ✅ |
| 类型（Admin） | `vue-tsc --noEmit` | ✅ |
| 构建（H5） | `vite build` | ✅ 63 modules, index 102.31 kB (gzip 39.66 kB) |
| 构建（Admin） | `vite build` | ✅ index 102.94 kB (gzip 40.27 kB) |
| 令牌入产物 | `grep -o -- '--pa-[a-z0-9-]*' dist/assets/*.css` | ✅ **65 个令牌**（H5 与 Admin 均 65） |
| 状态类入产物 | `grep -o 'state-message[a-z_-]*\|skeleton[a-z_-]*'` | ✅ 全部命中 |
| 设计系统守卫 | `pytest tests/unit/test_design_tokens.py` | ✅ 10 passed |
| 状态守卫 | `pytest tests/unit/test_ui_states.py` | ✅ 8 passed |
| 数据质量守卫 | `pytest tests/unit/test_quality_metrics.py` | ✅ 19 passed |
| DB-free 全量 | `pytest tests/unit tests/contract --deselect <20>` | ✅ **194 passed, 20 deselected** |

> **构建环境说明**：默认 `pnpm build` 写 `dist/` 会触发本机沙箱批量删除保护（Vite `prepareOutDir` 需清 72 个旧文件 > 阈值 50）。`vue-tsc` 在清目录前已通过；改用全新 `--outDir` 后两端构建成功，临时目录已清理。

---

## 4. 与规范逐条对照

| 规范条款 | 要求 | 状态 |
|---|---|---|
| §1 视觉定位 | 中性 / 城市工具 / 非萌宠社区 | `PASS`（令牌色板为中性灰蓝，无粉色/爪印/卡通） |
| §2.1 地图首页 | 搜索/模式/地图/cluster/bottom sheet/filter chips/定位/toggle/coverage hint | `PARTIAL`（仅地图壳 + 列表） |
| §2.2 搜索 | name/category/nearby + 10 类筛选 | `PARTIAL`（仅 name） |
| §2.3 Place Card | 名称/类型/结论/1–2 条件/来源/核验时间 | `PARTIAL`（缺条件与核验时间） |
| §2.4 Place Detail | 10 Section | `PARTIAL`（4/10） |
| §3 Status 语义 | 6 态，icon+text+color | `PASS`（机读强制） |
| §4 Source Badge | 7 类前台徽标 | `PASS` |
| §5 Boundary Profile UX | 不问"你讨厌宠物吗"，逐项 接受/不接受/不在意 | `PASS` |
| §6 Pet Profile UX | AI 建议需用户确认，不自动写 confirmed | `PASS` |
| §7 Contribution UX | 4 入口，无自由评论区 | `PASS` |
| §8 Neutral Copy | 推荐词 + 禁用词 | `PASS`（机读扫描） |
| §9 Design Tokens | 令牌体系 | `PASS`（两端消费） |
| §10 Accessibility | 8 项 | `PARTIAL`（keyboard/contrast/font-scaling 未自动化） |
| §11 UI QA | Playwright 9 页截图 | `NOT_RUN`（ENV-01） |
| §12 输出 | 5 份文档 | `PASS`（`DESIGN_SYSTEM.md` / `UI_STATE_MATRIX.md` / `COPY_GUIDE.md` / `UX_FLOW.md` / `FRONTEND_QA_REPORT.md`） |

---

## 5. 未达成项与原因

| # | 未达成 | 阻塞源 | 可解除性 |
|---|---|---|---|
| 1 | 视觉回归基线（9 页截图） | ENV-01（无 PostGIS ⇒ API 不可启动） | 解 ENV-01 后可做 |
| 2 | 地图交互壳（cluster / bottom sheet / filter chips / 定位 / toggle / coverage hint） | B-04（腾讯地图 Key） | 需 Key；无 Key 时可用 Mock 实现部分交互 |
| 3 | Place Detail 完整 10 Section | 部分需后端字段接线（表已存在） | **可立即实施** |
| 4 | 搜索筛选 chips | 数据层 | 解 ENV-01 后 |
| 5 | 多断点 / 真机 QA | 无设备与可运行环境 | 需外部 |
| 6 | 暗色主题 | 无 | **可立即实施**（令牌已按 `[data-theme]` 覆盖设计） |
| 7 | 令牌接入 `apps/client`（uni-app x） | B-01（HBuilderX） | 需外部 |
| 8 | 通知中心 / 设置页 / 关于页 / 隐私控制页 | 无 | **可立即实施** |

第 3、6、8 项无外部阻塞，是本轮之后最直接的推进方向。

---

## 6. 诚实边界

本轮**未伪造**：视觉回归截图基线、真机 QA 结果、多断点实测数据、暗色主题实现、uni-app x 端接入、平台提审状态。所有 `NOT_RUN` 与 `PARTIAL` 均如实标注，未以"接近完成"表述替代。
