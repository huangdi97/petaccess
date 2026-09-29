# Search Mobile Contract

> 目标 viewport：390 / 430 × ~900+。JSON：`docs/ui/contracts/json/search.mobile.json`。

## 1. 结构（自上而下）

```text
Top context
Search
Recent / Filter
Result list
Bottom nav
```

- 不显示 detail pane（decision-inspector count = 0）。
- 点击结果 → 进入 Place（drill-down），不是横向压扁双栏。

## 2. Result row

- padding horizontal 16px；padding vertical 14–16px；height 104–132px；
- 最多 5 行可见文本行（视觉行组：名称+状态 / 类型·距离 / 大结论(+1 条件) / reality·evidence）；
- 决策高于 metadata；`result-rules` / `result-branch` 等桌面极轻元数据在移动隐藏。

## 3. Filter

- `筛选 N` 按钮 → **bottom sheet**：top radius 16px、drag handle、title、checkbox/select 列表、action 区；
- 不再是铺开的 chips wall；sheet 不是巨大空白表单。

## 4. 语言

- 同 CONSUMER_LANGUAGE_CONTRACT（无泄漏）。
- zone 事实经 mapper 转译。

## 5. 密度

- 首屏（932px viewport）：Top context + Search + 至少 2 条结果可见；
- 非空白空洞 ≤ 180px。