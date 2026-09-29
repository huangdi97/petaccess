# Map Contract

> JSON：`docs/ui/contracts/json/map.json`。
> Map = Canvas。不放 card。

## 1. Desktop（1440×900）

```text
Rail
Result pane 360–420px
Map fills remaining
```

- selected place → 唯一 floating preview（`.map-preview-float`，radius 10–12px + 轻阴影）——这是允许的唯一卡片；
- 其余 UI 都是 pane/overlay。

## 2. Mobile（430×932）

```text
Map full
Bottom sheet（collapsed / medium / full）
```

## 3. Filters

- 只显示 `筛选 N` 入口（panel/popover）；
- 删除永久一排 `允许/有条件/限制/未知/冲突` pill wall。
- 仅允许 view 切换（map/list）作为轻量 toggle。

## 4. Mock Map（无真实 provider）

必须表达空间感（DOM/SVG 可测，不依赖渲染像素判断）：
- road-like lines（≥3 条 path/line 元素）；
- block polygons（≥2 个 polygon/rect 形状）；
- 水系/绿地 subtle 区域（≥1 个 area 元素）；或以上有等价标记且数量达标；
- marker positions（≥4 个 marker）；
- selected marker（选中态与未选中可区分：data-selected / class / size）；
- scale/zoom affordance（≥1 个 ± 控件或 scale 元素）。

不允许：灰色网格 + 一个数字。
实现：轻量 SVG/CSS mock，在 repo 内，不引入新 map library。

## 5. 语言

- 无 UUID / snake_case / 状态枚举原文泄漏（marker 语义要经 mapper）。