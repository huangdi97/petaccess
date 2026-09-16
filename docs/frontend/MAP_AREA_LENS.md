# Map — Area / Lens 选择器现状

> 结论先说：**MAP_AREA_LENS = FAIL（未实现）**。本文件说明现在有什么、缺什么、为什么本轮不补，
> 以及补上需要的前置条件。不把"没做"写成"做了简化版"。

## 1. 现在真实有什么

`apps/client-h5/src/views/MapView.vue` + `packages/client-core/src/platform/map.ts`

| 能力 | 状态 | 依据 |
|---|---|---|
| 地图 / 列表双视图切换 | 实现 | `view` ref + `data-testid="map"` / `view-list` |
| 地图渲染 | **Mock** | `<MockMap>`，无真实瓦片 SDK；`MapProvider` 仅有 mock adapter |
| 相机（中心 + zoom） | 实现 | `synthDemoCamera()` → `MapCamera` |
| 定位 | 一次性 | `navigator.geolocation.getCurrentPosition`，无 watch（ADR-012） |
| 定位状态文案 | 实现 | `LOCATION_LABELS`：`IDLE / REQUESTING / GRANTED / DENIED / UNAVAILABLE` |
| 覆盖度提示 | 实现 | `coverageHint()`：`当前视野 N 个场所：X 个已有结论，Y 个信息不足或存在不一致。信息不足 ≠ 允许。` |
| 状态筛选 | 实现 | 5 个中性状态（明确允许 / 有条件 / 明确限制 / 信息不足 / 来源不一致），**不是排序** |
| 信息不足默认不隐藏 | 实现 | 无筛选时 `visiblePlaces` 返回全部；空筛选结果给出「清除筛选」 |
| 聚合 | 实现 | `clusterMarkers(markers, zoom)` |
| 底部卡片（bottom sheet） | 实现 | `selected` → 详情入口，从列表点击可打开 |
| 列表兜底 | 实现 | 地图失败不是死路：列表始终可用 |
| **Area（区域）选择器** | **未实现** | 源码中不存在 |
| **Lens（镜头）选择器** | **未实现** | 源码中不存在 |

## 2. 为什么本轮不补

### 2.1 坐标是合成的

`synthMarkerPosition(id, camera)` 从场所 UUID 的哈希导出稳定偏移：

```ts
let h = 0;
for (const c of id) h = (h * 31 + c.charCodeAt(0)) % 100000;
const dx = ((h % 41) - 20) / 20;   // -1..1
const dy = ((Math.floor(h / 41) % 37) - 18) / 18;
```

也就是说：**图钉位置与场所的真实经纬度无关**，只保证"同一个场所在同一处"。

`nearby` 接口返回 `distance_m`，但**不返回坐标**——真实 provider 在客户端解析坐标。当前只有 Mock provider。

后果：在合成坐标上画一个"区域"框，框选出来的结果**看起来是对的、实际是随机的**。
这正是这个产品最不能出的那类错误——把「演示能跑」呈现成「空间结论」。

### 2.2 Lens 还没有产品定义

「镜头」通常是"按某个维度重看图面"（例如只看服务犬相关、只看带围栏的场地）。
本项目现有硬约束里，`不做遇宠率`、`AI != final rule judge`、`UNKNOWN != allowed`。
在这些约束下，"镜头"要么是**筛选**（已有 5 个中性状态筛选），要么需要新的产品定义——
而新增维度等于新增一种可以被误读成结论的视图类型，不能由实现方自己发明。

## 3. 补上它需要什么（前置条件，按顺序）

1. **真实 Map provider**：`MapProvider` 的腾讯地图（或等价）adapter，`nearby`/`places` 返回或可解析真实坐标。
   现有 `MapProvider` 接口 + adapter 结构已就位，缺的是非 mock 实现。
   在此之前，任何"区域"能力都只是在合成坐标上做样子。
2. **规则覆盖边界（Area 的语义来源）**：Area 只有在能对应"某个行政/管辖范围"时才有意义——
   本项目里那是 `jurisdiction_rule` + `jurisdiction_code`。所以 Area 选择器应该绑定**管辖范围**，
   而不是屏幕上的一个矩形。
3. **Lens 的产品定义**：由产品/治理侧给出"镜头"清单，且每个镜头必须能被落成**筛选**而不是**评分**，
   否则会与「不做遇宠率」「AI 不做终裁」冲突。
4. **可回归的测试**：Area 选择要有"选了某区域必须返回该区域场所、且不返回区域外场所"的断言，
   不能只截一张图。

## 4. 本轮的替代做法（已做）

不做假的功能，但把"地图能诚实说什么"补齐：

- `coverageHint()` 明说当前视野内有几个场所已有结论、几个信息不足，并写明「信息不足 ≠ 允许」。
- 未收录时文案是「当前视野内暂无已收录场所。未收录不代表该场所没有规则。」——不把空视野说成"安全"。
- 定位被拒不是死路：`DENIED` / `UNAVAILABLE` 都退回默认中心，并如实说明。
- 列表始终是地图的兜底，地图挂了不影响用户拿到结论。
- 视觉回归覆盖 `map`（地图壳 + 列表兜底）与 `map-sheet`（底部卡片）三个视口，见
  `docs/frontend/VISUAL_REGRESSION_BASELINE.md`。

## 5. 判定

| 项 | 判定 |
|---|---|
| MAP_RENDER（Mock） | PASS_WITH_LIMITATIONS（无真实瓦片） |
| MAP_LIST_FALLBACK | PASS |
| MAP_COVERAGE_HINT | PASS |
| MAP_STATE_FILTER | PASS |
| MAP_LOCATION_STATES | PASS |
| **MAP_AREA_SELECTOR** | **FAIL（未实现）** |
| **MAP_LENS_SELECTOR** | **FAIL（未实现）** |

`MAP_AREA_LENS` 整体 = **FAIL**。这不是"简化实现"，是没做；写出前置条件而不是写一个会骗人的版本。