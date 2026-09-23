# V010 EMPTY STATE REPORT — 2026-09-24

> 状态标记 (Status Legend): **CURRENT VERIFIED** 本会话(2026-09-24)实际执行并核验 | **HISTORICAL** 此前会话执行、本轮未重跑 | **NOT RERUN** 未重跑(原因已注明) | **BLOCKED** 无法执行(原因已注明)

## 状态总表 (Status Table)

| 项 | 结果 | 标记 |
|---|---|---|
| Backend 空集合（5 endpoints） | 200 empty | CURRENT VERIFIED |
| Backend 缺失资源（2 endpoints） | 404 | CURRENT VERIFIED |
| Consumer E2E empty-state spec | 3/3 PASS | CURRENT VERIFIED |
| No fake places | 成立（空 TEST db 实测，skip-seed） | CURRENT VERIFIED |
| UNKNOWN != ALLOWED 不变量 | 保持 | CURRENT VERIFIED |

## 1. A6 矩阵 — Backend（空 TEST db，skip-seed，dev_api_server :8012）

200（空集合）:

- `GET /api/v1/places` -> `200 {"items":[],"total":0}`
- `GET /api/v1/places/nearby` -> 200 empty
- `GET /api/v1/sources` -> 200 empty
- `GET /api/v1/regulations` -> 200 empty
- `GET /api/v1/places/{missing}/rules` -> 200 empty

404（缺失资源）:

- `GET /api/v1/places/{missing}` -> 404
- `GET /api/v1/places/{missing}/reality` -> 404

## 2. Consumer E2E empty-state spec — 3/3 PASS

- home-empty：渲染 `当前还没有已发布的场所数据` + `探索地图` / `贡献线索` buttons。
- search-empty：渲染 `没有找到已收录场所`。
- place 404：渲染显式 ERROR 状态，非空白页。

## 3. 不变量 (Invariants)

- **No fake places**：实测基于空 TEST db（skip-seed）；demo seed 不进入 release 路径（TD-003 隔离，release 构建不含 seed 数据）。
- **UNKNOWN != ALLOWED**：文案层保持语义不变量——"未收录 ≠ 没有规则"、"暂无记录 ≠ 没有动物"、"≠ 未处理"、"设施 ≠ 入场政策"（见 PlaceView / RealityPanel 文案）。

## 4. 结论

**结论: EMPTY_STATE = PASS**
