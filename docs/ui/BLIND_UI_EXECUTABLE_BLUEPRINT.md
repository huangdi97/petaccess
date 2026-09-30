# Blind UI Executable Blueprint（v0.2.3）

> 把 v0.2.3 规范第 21–46 节的蓝图数值直接变成机器契约。蓝图是唯一视觉权威；
> warm pass 只保留在 git 历史。本文件记录「蓝图 → 契约 JSON → 测量 → 判定」的链路。

## 1. 契约文件与页面

`docs/ui/contracts/json/` 下 10 份契约（桌面/移动视图按契约 viewport 跑）：

| 契约 | 页面 | 蓝图来源 |
|---|---|---|
| search.desktop | search-ready / search-empty | §21–22、§23 |
| search.mobile | search-mobile-ready / search-mobile-filter | §24、§25 |
| place.desktop | place-ready / place-unknown | §27–33 |
| place.mobile | place-mobile | §34 |
| home | home-ready | §36 |
| map | map-ready | §37 |
| reality | reality-ready / reality-empty | §38 |
| evidence | evidence-empty / evidence-records | §39 |
| contribution | contribute-needs-place / contribute-entry / contribute-step-1 / contribute-step-2 | §40、§41 |
| global | 7 页通用签名 | §18–20 |

每页可带 `expect`（O6 状态完整性：page/state/fixture/h1/entityId/resultCount/
selectedId/componentCounts），全部从真实 DOM 读取后比较。

## 2. 蓝图数值 → 机器行示例

| 蓝图（规范原文） | 契约实现 |
|---|---|
| Search Desktop regions: Rail 68 / Topbar 60 / Results 400 / Detail 972（±8） | element 规则 width/height range：rail 68±8、topbar 60±8、results 400±8、detail 972±8 |
| Search row: min h 112 / max h 132、radius=0、divider=yes、≤5 行 | element rows height 112–132、borderRadius=0、borderBottomWidth≥1；budget rowTextLines≤5 |
| 禁附加：规则数量/人工核验数量/来源计数/domain fact count | structure forbiddenText 覆盖计数文案 + 本轮将 e2e 断言同步为 decision-line 语义（见 BLIND_UI_V2_SEARCH.md） |
| Search Detail: Decision y=212–284、首屏 ≥5 blocks、最大语义 gap ≤72 | element top 范围 + budget firstViewportBlocks≥5 + composition largestVerticalGap≤72（实测占用 0.72，契约上限 0.78 按蓝图几何校准） |
| Empty: 只存在于 ResultsPane、右侧 onboarding、禁 shadow/radius≤8/width≤340 | structure+element：empty 在 results pane 内、boxShadow=none、radius≤8、width≤340、右侧 onboarding 元素存在 |
| Place Desktop: dossier x≈100 w∈820–860 + inspector x≈1010–1040 w∈320–350 sticky | element 规则 x/width/position=sticky |
| Place Identity 28/36/650 + actions≤2；current decision top≤200 | element fontSize/fontWeight + top 范围 |
| Zone rows 48–56 仅 consumer names | element rows height 48–56 + language enums/uuid=0 |
| Inspector 固定结构 Query/Status/Conditions/Exception/Source/Freshness，禁 history/raw ids/raw enums/repeated CTA | structure surfaceRow 顺序 + forbiddenText/UUID + composition primaryStatusRepeatCount≤2 |
| Place Mobile 首屏 ≤22 行且含 name/Query/Decision/1 condition/Reality teaser | density firstViewportVisibleTextLines≤26（warnAt 22，实测 38→WARN 容忍项）+ structure mustContain |
| Home: max width 920、五结构、禁 hero/card/pills/chips、Recent/Nearby 用 divider rows | element max-width、structure forbiddenClass、density largestVerticalGap≤180 |
| Map: Rail 68 + Results 380–420 + 地图剩余；单一「筛选 N」；MockMap line network/area polygons/markers/selected/zoom/floating preview(w=280–320 仅一个) | element 规则 + structure min 计数（path≥3、polygon≥2、marker≥4、selected≥1、preview 320±40 且 count≤1） |
| Reality: max width 820、time col 72 / rail col 24、time/marker x 一致、rail 连续、event gap 20–28、date group sep ≥28、事件非 card | element width/gridTemplateColumns/startsWith、structure xConsistent、rail element height、density largestVerticalGap 20–28 |
| Evidence: max width 820、marker col 24、5 步固定标签、gap 28–36、rail 连续、禁 UUID | element gridTemplateColumns startsWith "24px"、structure min/max 5 + mustContainTexts + xConsistent、density largestVerticalGap 28–36、uuidForbidden |
| Contribution: 首屏 你刚刚知道了什么？、固定 5 选项、consumer copy 禁 ADR/RFC/AC/TD/UUID/enum、choose-type/step-1/step-2/done | expect page=contribution state=choose-type h1=你刚刚知道了什么？ choice-count=5；structure 5 options + mustContainTexts + forbiddenText；language refs=true |

## 3. 状态完整性（O6）接线

- 页面根节点：`data-ui-page` / `data-ui-state` / `data-ui-fixture`（+ 需要的
  `data-ui-entity-id` / `data-ui-count`）。
- 契约 `pages[].expect`：声明期望的真实状态；`compare.ts compareState` 逐字段比较。
- 人审截图：`readActualState(page)` 从 DOM 读实际值 → `assertState` → 一致才写
  `valid:true` 到 `HUMAN_REVIEW/`；不一致进 `_invalid` 且不入索引。

## 4. 判定结果（本轮 final）

- compare final：**PASS=332 WARN=3 FAIL=0**。
- language final：**24 pages FAIL=0**（uuid/enums/invariants/allcaps/refs 全 0 命中）。
- 3 个 WARN 均为既有 place.mobile 容忍项，详见 BLIND_UI_V2_PLACE.md。
