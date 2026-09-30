# Blind-Model UI — Responsive Model（响应式变换模型）

> 原则（契约 §C.15）：响应式是**布局模式变换**（非等比缩放）：Search ≥1100 list-detail、768–1099 紧凑 list-detail/reduced inspector、<768 单列 drill-down；Place ≥1100 dossier+inspector、<1100 单列；Map desktop pane+map、mobile map+bottom sheet。

## 1. 断点模型（consumer-h5）

| 宽度 | 模式 | Search | Place | Map |
|---|---|---|---|---|
| ≥1100（1440/1280） | desktop list-detail / dossier+inspector / pane+map | 双栏（results + detail） | dossier + sticky inspector | 结果窗格 380–420px + 地图画布 |
| 768–1099（800/768/1024） | 紧凑双栏 / reduced | 双栏收窄 / inspector 压缩 | dossier 单列优先 | pane+map（pane 收窄） |
| <768（430/390/360） | 单列 drill-down / map+bottom sheet | 单列列表，无 detail pane，bottom sheet 筛选 | 单列 dossier | 全屏地图 + 选中场所 bottom sheet |

## 2. 机器验证矩阵

| 套件 | 宽度 | 验证内容 | 结果 |
|---|---|---|---|
| `tests/e2e/responsive.spec.ts`（e2e 189 的一部分） | 360 / 390 / 430 / 768 / 1024 / 1280 / 1440 / 1920 | 7 个 Consumer 页 + settings 的 no-horizontal-overflow | 全 PASS |
| `playwright.ui-reconstruction.config.ts`（ui-360/430/800/1280/1440 五个 project） | 360 / 430 / 800 / 1280 / 1440 | capture + phase1/3 + a11y + leakage（LEAKAGE_SCOPE=all） | 180/180 PASS |
| `tests/ui-oracle/oracle.spec.ts`（oracle-mobile project） | 430×932（hasTouch） | search.mobile / place.mobile 契约几何 | search.mobile 15/15、place.mobile 11 PASS+1 WARN |
| `tests/ui-oracle/oracle.spec.ts`（oracle-desktop） | 1440×900 | desktop 契约 | 全部 PASS |

## 3. 布局模式的 DOM 证据（来自 final probes）

- Search desktop（1440）：`search-results-pane`（380–420px）+ `search-detail-pane`（detail 内容 maxChildWidth 680–760px）并存；`search-detail-content` 首屏 ≥360px。
- Search mobile（430）：`search-results-pane` 单列、row 104–132px、决策高于 metadata；筛选走 `search-filter-sheet`（bottom sheet，top radius 16px）。
- Place desktop：`place-dossier` 65–72% + `place-inspector` 300–360px sticky。
- Place mobile：`place-dossier` 单列；首屏 42 行文本 → 契约 WARN（warnAt=30），按 progressive disclosure 策略记录。
- Map desktop：`map-canvas` 为主表面 + 结果窗格 + `map-preview-float`；mobile：`map-canvas` 全宽 + `BottomSheet`（选中场所）。

## 4. 契约中的响应式表达

- `docs/ui/contracts/RESPONSIVE_TRANSFORMATION_CONTRACT.md`：布局模式变换的语言描述。
- JSON 契约按 viewport 拆分为 desktop/mobile 两份（search.desktop/search.mobile、place.desktop/place.mobile），同一页面在两种模式下拥有各自的几何/结构规则 → “非等比缩放”由不同契约约束强制。
- density 诊断：`firstViewportVisibleTextLines` 预算只应用于 <1000px 契约（desktop list-detail 合法地展示更多文本行），桌面密度以契约规则为准。

## 5. 已知记录

- place.mobile 首屏 42 行 → WARN（progressive disclosure 叙事，优先保留信息而非删除）。
- search.mobile 首屏 38 行 → density 诊断 WARN（契约未 FAIL）。
- 无横向溢出：responsive.spec 在 8 个宽度 × 8 页面全 PASS。
