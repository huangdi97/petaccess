# A11Y Audit — 真实页面的机器可判定无障碍检查

> 工具：`scripts/a11y_audit.mjs`（Playwright + 注入式 DOM 检查，**无 axe-core 依赖**）。
> 复跑：`node scripts/a11y_audit.mjs --json artifacts/a11y/final.json`

## 1. 覆盖范围（先把话说清楚）

「a11y PASS」不带范围等于没说话。本审计只覆盖**机器能判定**的部分：

| 覆盖 | 判定方式 |
|---|---|
| 文档语言 | `<html lang>` 存在且合法 |
| 标题结构 | 可见 `<h1>` 数量、层级不得跳级 |
| 可访问名 | `aria-label` / `aria-labelledby` / `label[for]` / 包裹 label / `title` / 文本 |
| 表单标签关联 | 每个控件必须有可计算的名字（placeholder 单独计为 minor） |
| 触控目标 | 真实 `getBoundingClientRect()`，对照 44px 指引 |
| 焦点可见性 | 键盘逐格走查，统计不可见焦点 |
| 焦点顺序 | 是否存在正 `tabindex` |
| 色彩不单独承载信息 | 状态必须同时有图标与文字 |
| 动效 | `prefers-reduced-motion` 下 motion 归零 |

**不覆盖**：文案对读屏用户是否讲得通、认知负荷、顺序在语义上是否合理、屏幕阅读器实测。
这些需要人，不假装机器能做。

## 2. 最终实测结果

命令：`node scripts/a11y_audit.mjs`

```
=== consumer ===   12 页     全部 ok
=== admin ===      10 页     全部 ok
=== keyboard focus walkthrough ===
  ok   consumer:home                tabStops=23 invisibleFocus=0
  ok   consumer:place               tabStops=9  invisibleFocus=0
  ok   admin:rule-candidates        tabStops=26 invisibleFocus=0

TOTAL issues: 0  (serious=0 moderate=0 minor=0)
```

| | 本轮起始 | 最终 |
|---|---|---|
| 问题总数 | 53 | **0** |
| serious | 36 | **0** |
| moderate | 0 | **0** |
| minor | 17 | **0** |
| 覆盖页面 | 22（12 消费者 + 10 Admin） | 22 |
| 键盘走查不可见焦点 | — | 0 |

## 3. 修了什么

### 3.1 无可见 `<h1>`（serious，主要来源）

多个消费者页面（搜索、贡献、我的）没有页面级标题，或标题被写成了 `div`。
修法：补 `visually-hidden` 的 `<h1>`（视觉不变、结构正确），并删掉重复标题。
`ContributeView` 原本同时存在一个可见标题和一个重复的隐藏标题，一并收敛成一个。

### 3.2 控件无可访问名（serious）

搜索框、Admin 表单控件大量只有视觉相邻的文字，没有 `label[for]`/`id` 关联。
修法：批量补关联——

- Consumer：`search-input` 等补 `aria-label`。
- Admin：脚本化关联 **47 组** label/控件（`for` 与 `id` 由同一 `v-model` 派生，避免手抄错位），分布于 13 个 view。

### 3.3 `<RouterLink>` 里套 `<button>`（serious，全站 8 处）

嵌套交互元素：Tab 停两次、读屏播两遍、外层目标只有行内文本高度（约 20px，低于 24px 底线、不到 44px 指引的一半）。
修法：链接本身穿上按钮样式（`a.btn` / `a.btn.primary` / `a.btn-inline` / `a.pill`），一处控件、一个名字、一个目标。

### 3.4 触控目标小于 44px（minor，最后一轮清零）

审计最后剩下的 6 项全部是尺寸，且都能一次修干净：

| 元素 | 实测 | 原因 |
|---|---|---|
| `a.btn-inline` ×3（「看地图 >」「前往设置」） | 75×29 / 74×29 | 覆盖了 padding（`4px 8px`），且未被 `min-height` 分组覆盖 |
| `input` ×3（`#home-q` 等） | 328×42 | 10px padding + 15px 文本，真实盒模型 42px |

修法：把 `a.btn-inline` 并入 `min-height: var(--pa-layout-touch-target)` 分组；给 `input, select, textarea` 统一加同一 `min-height`。

> 注：42 与 44 差 2px 这种问题，只有**实测**才会发现。用「我设了 padding，应该够了」去推，永远推不出来。

## 4. 方法论教训

### 4.1 审计脚本自己会造缺陷

第一版 `a11y_audit.mjs` 有三处假阳性，报告全是噪声：

| bug | 后果 |
|---|---|
| `waitUntil: networkidle` + 固定 450ms 等待 | 场所详情页第二波请求未回，审的是骨架屏 → 报出**不存在**的「没有 h1」 |
| 用 `button[type="submit"]` 选登录按钮 | 该按钮没有 `type`，30s 超时后被 `catch(() => {})` 吞掉 → **Admin 七个页面审的全是登录页**（控件数完全相同：24），报告看不出来 |
| 用 `#/review`、`#/publish` 等**不存在**的 hash 路由 | 路由回落登录页 → 同上 |

三处都改成"等骨架屏消失 / 用真实选择器 / 用真实路由"，并且**登录失败要显式失败**：

```js
expect(page.url()).not.toContain("/login");
```

**一个会凭空造缺陷的报告，比没有报告更糟——它训练读者忽略它。**

### 4.2 数字必须当场跑出来

本轮 a11y 从 36 项 serious 降到 0，中间还纠正了自己上一版的 3 类假阳性。
「上次报告写 PASS」不是现在 PASS 的证据。所有数字都来自本次实跑，命令写在上面，任何人可复现。

## 5. 判定

**A11Y = PASS（范围见 §1）。**

serious / moderate / minor 全为 0，22 页覆盖，键盘走查无不可见焦点。
未被覆盖的是需要人判断的部分（文案、认知负荷、屏幕阅读器实测），此处不冒充为通过。
