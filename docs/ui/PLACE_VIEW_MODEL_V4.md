# Place View Model v4 — Place Dossier 视图模型

> 实现基准：`IMPLEMENTATION_BASE = e1c5ca7`（完成代码与测试后的实现 commit）。
> 分支最终 HEAD 以 Git 查询为准。

## 1. 为什么不再是一张无限长页面

v0.2.3 的 Place 详情是单页长文档（3000px+ 一次渲染），违背「信息密度受控」原则：
- 首屏被 Identity + Query + Decision 之外的大量内容占据；
- 规则/证据/历史版本全部平铺，用户找不到重点；
- mobile 首屏文本行数超过 22（曾经 38 行 WARN）。

v0.2.4 把 Place 重构为 **Dossier with Views**（§15–28）。

## 2. 视图模型

### 路由与 deep link

```
/#/place/:id                      → overview（默认）
/#/place/:id?view=space           → 空间
/#/place/:id?view=rules           → 规则
/#/place/:id?view=reality         → 现场
/#/place/:id?view=evidence        → 证据
```

- `view` 通过 `route.query.view` 读取，非法值回退 overview；
- deep link / back-forward / refresh 均安全（组件内 `watch(placeId)` 重置 + 重载）。

### 本地 section 导航（PlaceSectionNav）

- desktop：text tab + underline（概览 / 空间 / 规则 / 现场 / 证据）；
- mobile：横向滚动 text tab（不挤压首屏行数）；
- 每个 tab 用 `router.replace({ query: { ...route.query, view } })` 更新 URL。

### Overview 五块（§16）

| 块 | 内容 | 说明 |
| --- | --- | --- |
| Identity | name + type · address + watch/why links | desktop 才显示 actions 行 |
| Current Decision | 当前查询 + 结论（status + key condition） | 首屏核心 |
| Recent Reality | 最近现场（复用 RealityEventLog 摘要） | desktop 才有完整块 |
| Space Summary | zones 摘要（count + context note） | desktop 才显示 |
| Evidence·Source Summary | 依据/来源一行 + 最近核验 | desktop 才显示 |

mobile 首屏 = Place + tabs + Decision + Reality teaser（`firstViewportVisibleTextLines <= 22`）。

### Rules view（§23，progressive disclosure）

- 当前规则 / conditions / exceptions / rule conflicts / source / effective·freshness；
- 历史版本与纠错**默认折叠**（`historyOpen = false`，`v-show` 控制）；
- 不放 Overview。

### Reality view（§24）

- 复用共享 RealityEventLog（不自己做第二套 Reality UI）；
- 提供「查看全部现场记录 →」链接到完整 `/place/:id/reality`。

### Evidence view（§25）

- 复用 Evidence Record / Provenance 组件（不复制来源表）。

### Unknown 态（§27）

- 只渲染有数据的部分（“暂无正式规则”“暂无足够现场记录”），不渲染空 section 全家福；
- UNKNOWN != allowed/prohibited，文案不暗示结论。

## 3. 关键可测量值（oracle 实测）

| 指标 | 契约 | 实测 | 结果 |
| --- | --- | --- | --- |
| PLACE_DESKTOP_OVERVIEW_FULLPAGE_HEIGHT | <=1500 | 1181.25 | PASS |
| PLACE_MOBILE_OVERVIEW_FULLPAGE_HEIGHT | <=2000 | 465.25 | PASS |
| PLACE_MOBILE_FIRST_VIEWPORT_LINES | <=24（warn 22，FAIL >24） | 22 | PASS |
| PLACE_MOBILE_FIRST_VIEWPORT_BLOCKS | >=2 | 4 | PASS |
| PLACE_SECTION_GAP | 24–36 target，max 40 | 24 | PASS |
| PLACE_MOBILE_STATUS_REPEAT | <=2 | 1 | PASS |
| PLACE_MOBILE_HISTORY_COLLAPSED | collapsed-default | collapsed | PASS |
| PLACE_MOBILE_DECISION_VISIBLE/SIZE | visible / 23–25px | PASS | PASS |

## 4. 组件拆分

- `PlaceView.vue`：编排 + 数据加载 + view 分发（<300 行）。
- `PlaceSectionNav.vue`：本地导航。
- `PlaceOverviewPane.vue`：Overview 五块。
- `PlaceSpacePane.vue` / `PlaceRulesPane.vue` / `PlaceRealityPane.vue` / `PlaceEvidencePane.vue`：
  各自 view 的独立 pane。
- `DecisionInspector.vue`：当前决策（place variant）。

## 5. 回归证据

- human-review `place_desktop_overview` / `place_desktop_rules` / `place_desktop_unknown` /
  `place_mobile_overview` / `place_mobile_rules` 全部 VALID；
- e2e `map-passport`（B1/B2）、`h5-journey`（mode switch、双场所切换）、`reality-trace`（A1/A4）通过；
- oracle compare `place.desktop PASS=61 FAIL=0`、`place.mobile PASS=32 FAIL=0`。
