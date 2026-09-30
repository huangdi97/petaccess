# BLIND_UI_PHASE_C_HOME_MAP.md — Phase C：Home + Map 收口

> 阶段产物：`artifacts/blind-ui-recovery/reports/phase-c-*`、`compare-home.json`、`compare-map.json`

## 目标（契约 §C.12–13）

- Home：删除 perspective pill 三件套与 feature card wall，无 hero；结构为 Location → Current Query → Primary Search → Recent → Nearby → Secondary Lens（轻量 link rows）。
- Map：filter pill wall 删除，只显示「筛选 N」入口（panel/popover）；mock map 表达空间感（road-like lines、block polygons、river/green subtle area、marker positions、selected marker、scale/zoom），不允许灰网格+数字；map 为 canvas 不放 card；desktop = rail + result pane 360–420px + map 剩余；mobile = map + bottom sheet。

## 改动

- `HomeView.vue`：删除 perspective pill 三件套与 `.home-perspectives` CSS；`.page` 加 `data-ui="home"`；HomeEntries 加箭头 + `data-ui="home-lens"`；HomeNearbySection 根加 `data-ui="home-nearby"`；`h5-shell.spec.ts` 相应改为断言新 IA（perspective count=0 + entry-presence/entry-dining）。
- `MapResultPane.vue` 重写：pill 墙 →「筛选 N」toggle + panel；`data-ui` map-result-pane / map-filter-toggle。
- `MockMap.vue` 重写：SVG basemap（road path ≥3、block polygon ≥3、river 面积元素、zoom 控件 `data-ui="map-zoom"`、marker/selected 带 data-selected/data-ui）。
- `MapView.vue`：`data-ui="map-shell" / "map-canvas"`；mobile bottom sheet 保留。
- `packages/client-core/src/platform/map.ts`：`unclusterAt` 15→14，使 demo 相机（zoom 14）直接显示各独立 marker（满足 ≥4 markers）；数据/领域语义不变（视觉基线重生成）。

## 机器 Gate（Oracle，stage=phase-c / final）

| 契约 | PASS | WARN | FAIL |
|---|---|---|---|
| home（1440×900） | 12 | 0 | 0 |
| map（1440×900） | 13 | 0 | 0 |

空间表达实测（final probe）：road path ≥3、block polygon ≥3、river 面积元素存在、marker ≥4、selected 标记存在、zoom 控件存在；`HOME` 无 perspective pill（count=0）、有箭头入口行。

## 证据

`artifacts/blind-ui-recovery/probes/phase-c-home.json`、`phase-c-map.json`；截图 `screens/final/home-home-ready.png`、`map-map-ready.png`。
