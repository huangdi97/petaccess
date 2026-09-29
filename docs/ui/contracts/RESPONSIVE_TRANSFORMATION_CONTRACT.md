# Responsive Transformation Contract

> JSON：`docs/ui/contracts/json/responsive.json`（视图矩阵定义）。
> 目标 viewports：360 / 390 / 430 / 768 / 800 / 1280 / 1440。

## 1. 原则

- 真正的布局模式转换，不是等比缩放；
- machine contract 用 layout mode / ratio / min-max，不全部写死像素；
- 页面不得有横向溢出。

## 2. Search

```text
>= 1100:  list-detail（result pane + detail inspector）
768–1099: compact list-detail 或 reduced inspector
<  768:   单列表 / drill-down（inspector count = 0）
```

## 3. Place

```text
>= 1100:  dossier + sticky inspector
<  1100:  单列
```

## 4. Map

```text
desktop:  result pane + map canvas
mobile:   map + bottom sheet
```

## 5. Home

```text
desktop: 宽布局（location → query → search → recent/nearby → lens）
mobile:  单列同顺序
```

## 6. Reality / Evidence / Contribution

- Reality/Evidence：窄内容列（max-width token）；Control 不变形；
- Contribution：单列流程，表单 focused-step，无横向挤出。

## 7. 验证

于每个 target viewport 断言：
- layout mode 正确（DOM 结构/visibility 可测）；
- 无 horizontal overflow（`document.documentElement.scrollWidth <= clientWidth + 1`）；
- 无关键元素被切断（rail 可见 / tabbar 可见等）。