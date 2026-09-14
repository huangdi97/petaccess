# FRONTEND_ACCEPTANCE.md

> 宠物准入与公共空间共处规则平台 · 前端验收矩阵
> 对应 `WORKBUDDY_PRODUCTION_MASTER_GOAL.md` §4.11 / §5.4–§5.9
> 基准 commit `716b163` · 生成时间 2026-09-14（GMT+8）

状态口径遵循 `AGENTS.md`：`PASS` = 实际执行成功；`PARTIAL` = 有缺失；`NOT_RUN` = 没跑；`BLOCKED_EXTERNAL` = 外部条件缺失。**未实际执行的项一律不得标 PASS。**

---

## 1. Consumer 页面验收

| 页面 | 规范要求 | 状态 | 证据 / 缺口 |
|---|---|---|---|
| Splash / boot | 启动态 | `PARTIAL` | 有加载骨架，无品牌启动页 |
| onboarding | 首次使用说明 | `PASS` | `OnboardingView.vue` |
| location permission | 定位授权 | `NOT_IMPLEMENTED` | 使用合成演示坐标；真实定位需地图 provider（B-04） |
| map home | 地图 + 附近列表 | `PARTIAL` | 有 Mock 地图壳与列表；缺 clustering / bottom sheet / filter chips / coverage hint |
| search | 名称/类别/附近 | `PARTIAL` | 名称搜索已实现；类别与 nearby 未接；筛选 chips 未实现 |
| filters | 10 类筛选 | `NOT_IMPLEMENTED` | 依赖数据层 |
| list view | 列表 | `PASS` | HomeView / SearchView 列表 |
| place card | 名称/类型/结论/条件/来源/核验时间 | `PARTIAL` | 有名称/类型/状态徽标；缺"最关键 1–2 条件"与最近核验时间 |
| place detail | 10 个 Section | `PARTIAL` | 实现 4/10：当前答案、分区规则、来源与核验、现场观察。缺共处边界、怎么进入、设施、历史、纠错入口 |
| zone detail | 分区详情 | `PARTIAL` | 分区规则内联展示，无独立分区页 |
| route / path | 进入路径 | `NOT_IMPLEMENTED` | `AccessPath` 表已存在，前端未接 |
| pet profile | 档案（含 AI 建议需确认） | `PASS` | `PetNewView.vue`，AI 结果标注"AI 建议" |
| boundary profile | 逐项边界 | `PASS` | `BoundaryView.vue`，逐项、不汇总 |
| contribution | 四种入口 | `PASS` | `ContributeView.vue`，无自由评论区 |
| photo evidence upload | 拍规则牌 | `PASS` | 上传 + OCR 预览 + 用户确认场所 |
| contribution status | 贡献状态跟踪 | `PARTIAL` | 仅即时反馈，无独立跟踪页 |
| watch / favorites | 关注 | `PARTIAL` | Mine 有入口与列表数据，无独立页 |
| notifications | 通知中心 | `NOT_IMPLEMENTED` | 通知 provider 为 mock |
| settings | 设置页 | `NOT_IMPLEMENTED` | — |
| privacy / data controls | 隐私与数据控制 | `PARTIAL` | Mine 有隐私说明文案；无账号删除 / 数据导出 UI |
| about / data methodology | 关于与方法 | `NOT_IMPLEMENTED` | 文档已有（`docs/legal/DATA_METHODOLOGY_DRAFT.md`），无页面 |
| correction / dispute | 纠错/异议 | `PASS` | PlaceView → 提交异议 |
| empty / loading / error / offline | 四态 | `PASS` | `StateMessage.vue` + `SkeletonList.vue` + `useOnline.ts`，已接入 4 个核心页 |

---

## 2. 状态完整性验收（Master Goal §5.5）

每个核心页面必须具备 10 个状态。逐页核对：

| 页面 | loading | skeleton | empty | success | partial | stale | conflict | error | offline | permission |
|---|---|---|---|---|---|---|---|---|---|---|
| HomeView | ✅ | ✅ | ✅ | ✅ | ⬜ | ✅¹ | ✅¹ | ✅ | ✅ | ⬜ |
| SearchView | ✅ | ✅ | ✅ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ✅ | ⬜ |
| PlaceView | ✅ | ✅ | ✅ | ✅ | ⬜ | ✅¹ | ✅¹ | ✅ | ⬜ | ✅² |
| BoundaryView | ✅ | ✅ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ✅ | ✅² |
| MatchExplainView | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ✅¹ | ✅¹ | ✅ | ⬜ | ⬜ |
| ContributeView | ✅ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅² |
| PetNewView | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ |
| MineView | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ⬜ | ⬜ | ✅ | ⬜ | ✅² |
| Admin Dashboard | ✅ | ✅ | ✅ | ✅ | ⬜ | ✅¹ | ✅¹ | ✅ | ⬜ | ✅³ |

说明：
- ¹ 通过 `StatusBadge` 语义呈现（STALE / CONFLICT），不是独立页面态。
- ² 以登录提示形式呈现，非全页态。
- ³ 通过 `require_role` 权限门返回 403，前端展示错误态。
- ⬜ = 未实现。**这是本轮未达成的部分，不做掩饰。**

**机器可读守卫**：`tests/unit/test_ui_states.py` 断言核心页必须引用 skeleton / state / offline 三件套，且 `PAGE_STATES` 每个状态必须同时具备 icon + title + description（禁止 color-only）。

---

## 3. 响应式验收（Master Goal §5.6）

| 断点 | 要求 | 状态 |
|---|---|---|
| mobile portrait (0–479) | 主要目标形态 | `PASS`（H5 布局上限 480px，居中） |
| mobile landscape (480–767) | 基本可用 | `NOT_RUN`（无实机/模拟器验证） |
| tablet (768–1023) | 合理 | `NOT_RUN` |
| desktop H5 (1024+) | 可用 | `PASS`（`BREAKPOINTS` 定义 xl；页面居中呈现） |
| Admin desktop | 可用 | `PASS`（`.two-col` 在 900px 以下折叠为单列） |

`NOT_RUN` 项原因：Playwright 视觉回归需可运行 API（ENV-01），当前无法采集多断点截图。

---

## 4. 可访问性验收（Master Goal §5.7 / UI_UX_SPEC §10）

| 项 | 要求 | 状态 | 证据 |
|---|---|---|---|
| keyboard | H5 / Admin 可键盘操作 | `PARTIAL` | 原生表单控件 + RouterLink 可聚焦；无自动化键盘遍历测试 |
| focus states | 焦点可见 | `PASS` | `:focus-visible { outline: 2px solid var(--pa-color-focus) }`，两端均有 |
| aria where supported | 语义标签 | `PASS` | `role="status"`、`aria-busy`、`aria-hidden`、`visually-hidden` |
| text contrast | 对比度 | `PARTIAL` | 令牌取值为深色文字 + 浅底，未做自动化对比度审计 |
| touch target | ≥44px | `PASS` | `--pa-layout-touch-target: 44px`，应用于 button/.pill/.tabbar a |
| font scaling | 字号缩放 | `PARTIAL` | 使用相对单位与系统字体栈；未做 200% 缩放测试 |
| not color-only | 禁止仅靠颜色 | `PASS` | `StatusBadge` 强制 icon+label+aria；`PAGE_STATES` 强制 icon+title+description；`test_design_tokens.py` / `test_ui_states.py` 机读断言 |
| reduced motion | 减弱动效 | `PASS` | 令牌层 `--pa-motion-*` 归零；骨架微光 `animation: none`（两端） |

---

## 5. 视觉回归验收（Master Goal §5.8 / UI_UX_SPEC §11）

| 目标截图 | 状态 |
|---|---|
| map shell | `NOT_RUN` |
| list | `NOT_RUN` |
| detail | `NOT_RUN` |
| boundary | `NOT_RUN` |
| contribution | `NOT_RUN` |
| admin review | `NOT_RUN` |

**为何全部 NOT_RUN**：9 个目标页面中有 6 个需要 API 返回真实数据才能渲染出有意义的状态；ENV-01（无 PostGIS）使 API 不可启动，截图只会得到错误页。**不伪造截图基线。**

---

## 6. 前端性能验收（Master Goal §5.9）

| 项 | 状态 | 证据 |
|---|---|---|
| lazy load | `PASS` | 全部路由 `() => import(...)`，Admin 与 H5 均为路由级分包 |
| 构建体积 | `PASS` | H5 index 102.31 kB (gzip 39.66 kB)；Admin index 102.94 kB (gzip 40.27 kB) |
| map marker rendering | `NOT_RUN` | 无真实地图，无 marker 压力场景 |
| virtual list | `NOT_RUN` | 数据量未达阈值 |
| image compression | `NOT_RUN` | 无生产图片管线 |
| avoid duplicate API | `PARTIAL` | PlaceView 顺序发起 6 个请求，未做并发合并 |
| cache strategy | `PARTIAL` | 会话级缓存，无 HTTP 缓存策略 |
| loading states | `PASS` | 已全面接入 |

**未做生产压测、未验证 SLO。**

---

## 7. 判定

```text
PRODUCT_UX_FREEZE      = PARTIAL
UI_FRONTEND_PRODUCTION_GATE = PARTIAL
```

**已达成的部分**
- 设计令牌成为唯一真源，并被 H5 与 Admin **共同**消费（机读守卫）
- 状态三通道语义强制化，禁止 color-only（机读守卫）
- 中性文案机读守卫（禁用词零命中）
- 核心页 loading / empty / error / offline 四态完整
- 可访问性基线（focus / touch / aria / reduced-motion）
- 两端类型检查与构建通过

**未达成的部分**
- 视觉回归基线（ENV-01）
- 地图交互壳（B-04）
- Place Detail 完整 10 Section
- 多断点与真机 QA
- 部分页面态（PARTIAL / PERMISSION_DENIED 全页态）
- 通知中心 / 设置页 / 关于页 / 隐私控制页

**结论**：`PRODUCT_UX_FREEZE` 不能标 PASS。在视觉回归基线建立、地图 provider 接入、Place Detail 补齐之前，前端不应对外宣称"达到可公开 Beta 的完整产品质量"。
