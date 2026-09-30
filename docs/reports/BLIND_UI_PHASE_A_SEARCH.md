# BLIND_UI_PHASE_A_SEARCH.md — Phase A：Search 收口

> 阶段产物：`artifacts/blind-ui-recovery/reports/phase-a-*`、`compare-search.desktop.json`、`compare-search.mobile.json`

## 目标（契约 §C.10）

Search 不再是数据库后台式排版：desktop = rail + top context + results + detail 双栏；mobile = 单列列表 + bottom sheet 筛选；决策为第一视觉锚点。

## 改动

- `SearchView.vue`：`data-ui`（search-shell / results-pane / result-row / selected-row / detail-pane / filter-toggle / filter-sheet / count）；quiet clear 控件替换 `.pill`；行密度与 detail 内容宽修正。
- `DecisionInspector.vue`：内部块 data-ui + 根 data-ui 由父级 fallthrough。
- `PaBottomSheet.vue`：新增 `ui` prop（Teleport 根不收 data-** 属性）。
- `tokens.css`：新增 `--pa-layout-detail-content: 720px`；修复被误删的 layout token 块。
- `consumer/labels.ts`：`floorLabel` / `zoneConsumerLine`。

## 机器 Gate（Oracle，阶段 stage=phase-a / final）

| 契约 | PASS | WARN | FAIL |
|---|---|---|---|
| search.desktop（ready/selected，1440×900） | 22 | 0 | 0 |
| search.mobile（mobile-ready/mobile-filter，430×932） | 15 | 0 | 0 |

关键锚点实测（final probe）：rail 64–72px、top context 56–64px、result pane 380–420px、detail 内容 maxChildWidth 680–760px、detail 左距 32–48px、顶距 24–32px、detail 首屏 ≥360px、row 高 108–136px radius=0、selected tint+左指示、决策锚点 label 12–13px / decision 28–32px / supporting 14–16px；mobile row 104–132px、bottom sheet top radius 16px。

## 回归

- 受影响 e2e：32 → 37 全过（后续全量 189/189 亦含 Search 相关）。
- language：search.desktop/search.mobile 可见文本无 UUID/enum/invariant 命中。

## 证据

`artifacts/blind-ui-recovery/probes/phase-a-search.desktop.json`、`phase-a-search.mobile.json`；截图 `screens/final/search.desktop-search-ready.png`、`search.desktop-search-selected.png`、`search.mobile-search-mobile-filter.png`。
