# Map — Spatial Workspace / Area / Lens 当前真实状态

> 2026-10-05 direct-v8 canonical visual recovery 更新。
> 本文只记录当前事实，不把“可继续实现”写成“已经完成”。

## 1. 当前结论

```text
MAP_SPATIAL_WORKSPACE          = IMPLEMENTED
MAP_FOUR_LENSES                = IMPLEMENTED
MAP_REAL_PLACE_COORDINATES     = IMPLEMENTED
MAP_ONE_SHOT_LOCATION_QUERY    = IMPLEMENTED
MAP_REAL_TILE_BASEMAP          = BLOCKED_EXTERNAL
MAP_AREA_SELECTOR              = NOT_IMPLEMENTED
```

这里最重要的变化是：**Map marker 不再以 UUID 哈希位置作为正常数据路径。**

当前数据链：

```text
PostGIS Place.location
→ GET /places / GET /places/nearby
→ PlaceSummary.latitude / longitude
→ Consumer repository
→ useMapWorkspace
→ marker / clustering / four-lens projection
```

只有 dev/test 或旧 payload 真正缺少坐标时，才允许
`synthMarkerPosition()` 作为 deterministic fallback；它不再代表生产空间事实。

## 2. 已经完成

### 2.1 Spatial Workspace

Desktop：

```text
Rail
+ Results Pane
+ Spatial Canvas
+ selected floating preview
```

Mobile：

```text
full spatial canvas
+ bottom sheet (collapsed / half / expanded)
+ bottom nav
```

List 与 Map selection 使用同一个 place id，selection 持续可见；Map 不是 Home。

### 2.2 四 Lens

同一个 `CoexistenceSnapshot` 上提供：

- Rule；
- Reality；
- Facility；
- Divergence。

Lens 只改变 consumer projection，不新增第二 resolver，也不把 Reality / Facility tone
解释成准入结论。Rule Lens 可以按准入状态筛选；其他 Lens 默认保持完整空间态势。

### 2.3 真实 representative coordinates

`PlaceSummary` 现在携带可空的：

```text
latitude
longitude
```

来自 PostGIS `Place.location` 的 WGS84 representative point。

原则：

- 有真实坐标 → 必须直接使用；
- 没有坐标 → Consumer 不得猜；
- dev/test fixture 可使用明确的稳定 fixture coordinates；
- legacy incomplete payload 才可触发 synthetic fallback；
- synthetic fallback 永远不是 provenance，也不写回数据库。

### 2.4 定位真的影响 nearby 查询

过去存在一个产品级缺陷：

```text
navigator.geolocation 更新 camera
但 nearbyPlaces() 仍固定查询 synthDemoCamera()
```

结果是“地图移动了，但查询区域没移动”。

direct-v8 已改为：

```text
camera(lat,lng)
→ nearbyPlaces(camera)
→ cache key 含 lat/lng/radius
→ /places/nearby?lat=...&lng=...
```

因此一次性定位现在真正改变空间查询，仍遵守 ADR-012：
不连续追踪、不保存用户移动轨迹。

## 3. 仍然没有完成的：真实瓦片底图

当前 `MockMap.vue` 的底图仍是 provider-neutral 的抽象城市空间画布。
它现在可以把**真实场所坐标**投影到真实相对位置，但它不是腾讯地图真实道路瓦片。

所以：

```text
REAL_COORDINATES = YES
REAL_TILE_BASEMAP = NO
```

这两件事必须分开写。

正式腾讯 GL 接线仍需要：

- `TENCENT_MAP_KEY_CLIENT` / 对应 Web key；
- Web / Windows WebView2 / Android WebView 可用域名与 CSP allowlist；
- provider terms / attribution；
- real runtime smoke；
- keyboard/touch marker interaction；
- map load failure → current list/spatial fallback；
- Windows + Android screenshot evidence。

没有外部 key 前，Agent 不应伪造“真实地图已接入”。

## 4. Area selector

Area selector 仍未实现。

如果后续做，Area 应绑定真实 jurisdiction / district / viewport spatial query，
不得在 synthetic rectangle 上假装是行政区域。至少需要：

1. 明确 Area 数据源；
2. 可追溯 geometry；
3. Area 改变 nearby/search query；
4. 区域内外回归断言；
5. 不把“未收录”解释为“允许”。

## 5. Map UX 研究约束

本轮参考成熟 map / split-view 官方模式：

- Apple Split View：selection 应持续高亮，使 list → detail/canvas 关系稳定；
- Apple Search：搜索范围必须清楚，结果尽量简化，desktop split view 中 search 与列表相邻；
- Google Maps controls：地图控件应是原生 button/form，可键盘访问，不用 div 冒充交互控件；
- Google accessible markers：marker 应可 click/focus，并有可读 title/aria 语义。

这些模式只用于加强现有冻结设计，不改变 PetAccess 语义。

## 6. 最终边界

当前可写：

```text
PetAccess Map 已是使用真实 Place coordinates 的四 Lens Spatial Workspace。
```

当前不可写：

```text
PetAccess 已完成真实腾讯地图生产接入。  ❌
```

真实瓦片 provider 是最后一个明确的 EXTERNAL integration gap；其余不应再用“没有地图 key”
作为理由保留假的位置查询或 UUID 几何。
