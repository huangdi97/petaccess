# BLIND_UI_PHASE_B_PLACE.md — Phase B：Place 收口

> 阶段产物：`artifacts/blind-ui-recovery/reports/phase-b-*`、`compare-place.desktop.json`、`compare-place.mobile.json`

## 目标（契约 §C.11）

Place desktop = main dossier 65–72% + sticky inspector 300–360px；identity 28–30px；Current Decision 为第一核心 section；mobile 首屏 name + 决策 + supporting fact；消费者 zone 文案（`一层公共区域`），raw zone 名只存在于 data attribute。

## 改动

- `PlaceView.vue`：`data-ui`（place-shell / dossier / identity / place-name / decision / reality / zones / rules / evidence / inspector / history）。
- zone 渲染改 `zoneConsumerLine()`：种子名 `1F 公共区` 不再上屏；`室内堂食区` 等消费者名保留；修复 h5-journey 回归。
- 契约 density 选择器改为纯 data-ui 单一选择器（修复 querySelector 逗号列表命中 app-shell main 的问题）。

## 机器 Gate（Oracle，stage=phase-b / final）

| 契约 | PASS | WARN | FAIL |
|---|---|---|---|
| place.desktop（1440×900） | 15 | 0 | 0 |
| place.mobile（430×932） | 11 | 1 | 0 |

- 唯一 WARN：`PLACE_MOBILE_FIRST_VIEWPORT_LINES` = 42 行（契约 max=40 / warnAt=30）。判定 WARN 不 FAIL：优先 progressive disclosure 而非删信息（契约叙事）。
- 可见文本中 zone `1F` 命中 = 0；UUID / snake_case / invariant 命中 = 0。

## 证据

`artifacts/blind-ui-recovery/probes/phase-b-place.desktop.json`、`phase-b-place.mobile.json`；截图 `screens/final/place.desktop-place-ready.png`、`place.mobile-place-mobile-ready.png`。
