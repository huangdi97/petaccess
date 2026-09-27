# V020 M3 UI CURRENT STATE AUDIT

> 修改前视觉取证（UI-0）——真实渲染、真实 viewport、真实状态。Commit: `049fc39`。

## 方法

- 服务栈：`petaccess_visual`（visual_db_reset.py 确定性 demo seed：5 places / 15 zones / 8 sources / 4 jurisdiction rules / 3 observations）→ API `:8011`（role VISUAL）→ H5 `vite preview :5175`。
- 运行：`npx playwright test --config playwright.ui-audit.config.ts`（新增 `tests/ui-audit/capture.spec.ts`），5 projects（ui-360 / ui-430 / ui-800 / ui-1280 / ui-1440）× 14 scenarios。
- 结果：**70 / 70 passed**（每个 scenario 有 testid 断言：shell 存在、empty 可见、ERROR 态可见、offline banner 可见、search empty 文案等），产出 70 张 PNG（35–240 KB，非空、非白屏，文件尺寸与 viewport 一致）。
- Gallery：`artifacts/ui-audit/UI_CURRENT_STATE_GALLERY.html`（70 rows；每行含 Screenshot/页面/状态/Viewport/Commit/Timestamp）。

## 截图矩阵（真实）

| 页面 | 状态 | viewport 覆盖 |
|---|---|---|
| Home | ready / loading / empty / error / offline | 360 / 430 / 800 / 1280 / 1440 |
| Search | ready / loading / empty / error / offline | 360 / 430 / 800 / 1280 / 1440 |
| Map | ready | 5 viewports |
| Place（云栖中心·测试商场） | ready | 5 viewports |
| Contribution | ready（未选场所门禁态） | 5 viewports |
| Mine | ready（未登录态） | 5 viewports |
| AppShell | 随各页含 nav（mobile tabbar <768px / desktop rail ≥768px） | 5 viewports |

## 逐 viewport 观察记录（基于真实截图审查）

### 360 / 430（mobile）
- AppShell：底部 tabbar（首页/地图/贡献/我的）存在；safe-area padding 生效。
- Home：第一屏 = 上海·试点 topline → 大标题 → 搜索 panel → 4 个 entry 卡（2×2）→ 3 个视角 pill → 类别 pill → 结果卡。**首屏内容堆叠较重**：标题 + 搜索 + 4 entry + 两组 pill 在同一屏内；entry 是带边框卡（border + radius-md + 无填充背景），与结果卡（panel）形成两套"卡"语言。
- Home 结果卡：每卡 1 个 StatusBadge + 「进入前需满足：…」+ 「为什么？」pill —— 卡内有多个 pill/徽标；「已核验」与「规则待核实」分区标题下各一排卡。
- Search：搜索 panel + 最近搜索 pills + lens hint + 档案信息 + FilterChips（8 个筛选）+ 结果卡；**筛选 chip 行较长但 wrap 正常**；结果卡含 name + StatusBadge + meta + ruleSummaryLabel + 最多 4 个 tag + conflict badge —— **徽标/标签密度高**（§69 pill abuse 风险点）。
- Home empty：产品空态（标题/描述/探索地图/贡献线索）完整，无白屏。
- Home error：统一 ERROR 态 + 重试，无 SQL/内部信息泄漏。
- Offline：GlobalOfflineBanner 显示，页面内容保留。

### 800（tablet）
- 无横向溢出（VIS-002 已修复）；内容列在 800px 内正常排布；desktop rail 在 ≥768px 出现，bottom tabbar 消失。
- Home entry 变为 4 列一行；Search 结果单列（split preview 在 ≥768px 才启用，800 时结果列 + preview 并排，预览 sticky 顶部）。
- **800px 时 Home/Search 内容仍较满**，信息密度与 1440 相同，未利用宽度做层级。

### 1280 / 1440（desktop）
- Desktop rail（首页/地图/贡献/我的/关于 + 版本）存在；内容区 margin-left = rail 宽。
- **Search 是唯一真正 split 的桌面页面**（结果列表 + PlacePreview 右侧）；Home 是宽度拉满的单列，未形成桌面 hierarchy（§18 "mobile H5 被放大" 风险点）。
- Home 标题/搜索/entry 居中感弱；结果卡横跨整个内容宽度，行内 name+status 两端对齐，信息利用率一般。

## 现状结论

- **AppShell 骨架完整**（nav / route frame / safe area / offline banner / toast / dialog / version），职责正确（不含 Rule/Reality 计算），M3 只需视觉精修。
- **Home / Search 结构完整、状态矩阵完整**（ready/loading/empty/error/offline 全绿），但存在以下 M3 深化点：
  1. 双重 chrome：页面仍用旧 `components/AppShell.vue`（ModeBar + 宠物档案 panel）包裹内容，与 ConsumerAppShell 并存 → 桌面端出现"rail + ModeBar + panel"三层 chrome，信息重复（宠物档案在 Home 顶部与 Search 档案块重复出现）。
  2. Home 首屏堆叠：标题/搜索/4 entry/2 组 pill 同屏，缺少层级节奏；entry 卡与结果卡两套卡语言。
  3. Search 结果行徽标密度高（最多 5–6 个 tag/badge/pill）。
  4. Search 桌面 split 是唯一桌面化表面；Home/其他页仍为宽单列。
  5. Home/Search 均未在行级展示 Reality 摘要与 Freshness/Evidence 层（Rule 之外的第二事实层不显式可见）；Divergence 仅在桌面 preview 可见。
- 状态标记（逐页）：
  - AppShell：`M3-PARTIAL`（骨架正确，视觉精修）
  - Home：`M3-PARTIAL`（结构完整，首屏层级/卡语言/Reality 可见性待深化）
  - Search：`M3-PARTIAL`（深链/状态完整，结果行密度/桌面 hierarchy 待深化）
  - Map：`FUTURE-M4`（本轮仅共享层影响）
  - Place Passport：`FUTURE-M4`
  - Reality Trace / Evidence：`FUTURE-M5`
  - Contribution：`FUTURE-M7`
  - Mine / Settings / Privacy：`FINAL`（既有收口，不动）
