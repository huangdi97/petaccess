# Capture State Integrity（v0.2.3 §14–§15）

> 截图不再是“看截图”；每张人审截图在保存前必须从真实 DOM 证明它确实是它所声称的
> 页面状态。本文件记录实现、实测结果与修复的历史事实（含 Contribution 漂移修复）。

## 1. 页面状态属性约定（§14 命名）

目标页面根节点暴露：

```html
<div data-ui-page="search|place|home|map|reality|evidence|contribution"
     data-ui-state="ready|empty|choose-type|step-1|step-2|done|…"
     data-ui-fixture="search-ready-v1|place-unknown-v1|…"
     [data-ui-entity-id="<place uuid>"]
     [data-ui-count="choice-count|result-rows"]>
```

状态值来自真实派生（`computed`），不是写死的：例如 Contribution 的 `choose-type`
只在 step=entry 且已登录且带 placeId 时成立；Reality 的 `ready`/`empty` 由
observations 数量决定；Search 桌面自动选中首行 → `ready-selected`。

## 2. 契约侧 expect（O6）

契约 `pages[].expect` 声明期望的真实状态（compare.ts `compareState` 逐字段比较）：

```json
{ "page": "contribution", "state": "choose-type",
  "fixture": "contribution-choose-type-v1",
  "h1": "你刚刚知道了什么？",
  "componentCounts": [{ "selector": "choice-count", "min": 5 }] }
```

## 3. 人审截图流程（human-review.spec.ts）

1. 每张 shot：固定 viewport + clock frozen → `goto(route)` → `reload()`（避免上张
   残留 route/selection 泄漏）→ freeze motion → settle（无 skeleton）。
2. 可选 interactions（mobile filter 打开 / contribution entry 选项点击）在 **probe
   之前**执行——测量 DOM 必须等于截图 DOM。
3. `readActualState(page)` 从 DOM 读取：route/page/state/fixture/h1/entityId/
   selectedId/count/counts（全部真实值）。
4. `assertState(actual, expect)`：任一字段不一致 → `valid:false`。
5. 仅 `valid:true` 写入 `HUMAN_REVIEW/<phase>/<name>.png + .json`（metadata 含
   expected vs actual）；`valid:false` 进 `_invalid/`（不入索引，便于排查）。
6. 测试末尾断言 invalid 数量为 0——人审包要么可信、要么可见地不完整。

## 4. 实测结果

- 16 张截图全部 VALID：phase-a-search 4、phase-b-place 3、phase-c-home-map 2、
  phase-d-rest 7（reality ready/empty、evidence records/empty、contribution
  desktop choose-type / step-2、contribution mobile choose-type）。
- 全部 metadata 的 actual 来自真实 DOM；`_invalid/` 不存在。
- 每张截图的 h1/state/fixture 与契约 `expect` 一致（例如 contribution choose-type：
  page=contribution、state=choose-type、h1=你刚刚知道了什么？、choice-count=5）。

## 5. 历史事实：Contribution 截图/元数据漂移修复（§0/§15/§41）

- **旧问题**：Contribution 截图与 metadata 曾出现状态漂移（截图时 DOM 状态与
  metadata 声称的状态不一致）。
- **本轮修复**：
  - ContributeView 根节点增加 `data-ui-page="contribution"` + `uiState`/`uiFixture`
    computed（needs-place / sign-in-required / choose-type / step-1 / step-2 / done），
    状态完全由真实 wizard step + placeId + signedIn 派生；
  - h1 在 choose-type 时等于 `你刚刚知道了什么？`（§41 断言目标），其余为 `现场贡献`；
  - 隐藏 `data-ui-count="choice-count"` 输出真实选项数（5）；
  - 修复消费者文案：位置信息 copy 由含 `ADR-012` 的错误版改为规范正确版
    「位置信息仅用于核验场所，不保存连续位置轨迹。」；
  - human-review 对 choose-type 断言 `counts: { "choice-count": 5 }`，实测通过。
- **修复证据**：`contribution_desktop_choose-type.json` 与
  `contribution_mobile_choose-type.json` 的 `valid:true` 且 actual.counts.choice-count=5。

## 6. 另一处诚实修复：Reality 截图同像素问题

- 现象：reality ready 与 empty 两张 PNG 一度字节相同（时间线 section 起点 y≈907，
  在 900px 视口折线之下，视口截图看不到差异内容）。
- 修复：为 reality shot 增加 `scrollToTestid: "trace-observations"`——在断言状态
  **之后**、截图之前把区分性内容滚入视口；两张图现已不同（hash 各异）且状态断言
  仍先于滚动发生，O6 诚实性不受影响。
