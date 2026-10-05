# Map — Spatial Workspace / Area / Lens 当前真实状态

> 2026-10-05 direct-v8 canonical visual recovery 更新。
> 本文只记录当前事实，不把“可继续实现”写成“已经完成”。

## 1. 当前结论

```text
MAP_SPATIAL_WORKSPACE          = IMPLEMENTED
MAP_FOUR_LENSES                = IMPLEMENTED
MAP_REAL_PLACE_COORDINATES     = IMPLEMENTED
MAP_ONE_SHOT_LOCATION_QUERY    = IMPLEMENTED
MAP_REAL_TILE_RENDERER_CODE    = IMPLEMENTED
MAP_REAL_TILE_RUNTIME          = BLOCKED_EXTERNAL
MAP_WGS84_TO_GCJ02_BOUNDARY    = IMPLEMENTED
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

## 3. Real Map：代码链已接通，真实运行仍是 External Blocker

当前分支已经不再停在“以后换 provider”的接口注释，而是有两套真实可切换 renderer：

```text
feature_real_map=false / key 缺失
→ MockMap（简化空间底图，真实 PetAccess 坐标）

feature_real_map=true
+ MAP_PROVIDER=tencent
+ TENCENT_MAP_KEY_CLIENT
+ TENCENT_MAP_KEY_SERVER
→ TencentMap（真实腾讯 GL 瓦片）
```

新增链路：

```text
PostGIS EPSG:4326 governed coordinate
→ /ai/map/translate
→ Tencent WebService coord/v1/translate type=1
→ GCJ-02 presentation coordinate
→ Tencent JavaScript API GL real basemap
→ PetAccess-owned accessible marker overlay
```

这里刻意不把 GCJ-02 写回数据库。PetAccess 的事实坐标继续以
`Place.location / PlaceGeometry = EPSG:4326` 为治理事实；provider 坐标只属于 render boundary。

官方依据：

- Tencent JavaScript API GL 基础入门：
  https://lbs.qq.com/webApi/javascriptGL/glGuide/glBasic
  - 浏览器通过 `https://map.qq.com/api/gljs?v=1.exp&key=...` 加载；
  - SDK 使用 GCJ-02；
  - GPS / 其它坐标需要先转换。
- Tencent WebService 坐标转换：
  https://lbs.qq.com/service/webService/webServiceGuide/webServiceTranslate
  - `/ws/coord/v1/translate`；
  - `type=1` = GPS 坐标；
  - 支持批量转换。

安全边界：

- `TENCENT_MAP_KEY_CLIENT` 是 JavaScript GL 本来就会暴露在浏览器请求中的 Web key，
  只能在 `feature_real_map=true` 且 server/client key 都完整时从 public map config 返回；
  部署时必须在腾讯控制台限制允许域名。
- `TENCENT_MAP_KEY_SERVER` 永不发到客户端；WGS84→GCJ-02 由 API 代理转换。
- Tauri CSP 已显式 allowlist 腾讯地图 GL / tile 域名，不开放任意第三方脚本。
- SDK 加载 / 坐标转换失败时自动退回 MockMap；List / Rule / Reality / Evidence 不丢失。

**还没有完成的是外部运行验收，不是源码 adapter：**

- 需要真实 `TENCENT_MAP_KEY_CLIENT / SERVER`；
- 需要 Web 真瓦片截图；
- Windows WebView2 真瓦片 smoke；
- Android WebView 真瓦片 smoke；
- 如 SDK 实际请求域名超出当前 CSP allowlist，只允许依据真实 console/CSP error 精确补域名；
- 需要确认 attribution、touch/keyboard、SDK load failure fallback。

因此当前应写：

```text
REAL_TILE_RENDERER_CODE = IMPLEMENTED
REAL_TILE_RUNTIME = BLOCKED_EXTERNAL_KEY
```

不能写：

```text
REAL_TILE_BASEMAP_RUNTIME = PASS  ❌
```

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
