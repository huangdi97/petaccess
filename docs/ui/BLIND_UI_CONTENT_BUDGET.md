# Blind UI Content Budget（v0.2.3 O4）

> 内容预算 = 视口内真实渲染的文本行数 / 语义块数。所有计数基于真实 line-box
> （`getClientRects()`），跳过 `.visually-hidden` / `[aria-hidden='true']` / `.sr-only`，
> 同行内联 badge 通过 6px 顶部桶共享同一行——不会被当作额外行。

## 1. 预算指标（probe.ts measureBudget）

| 指标 | 含义 | 测量方式 |
|---|---|---|
| `rowTextLines` | 行内可见文本行数（max over rows） | `visibleLinesIn(row)`：遍历文本节点 line-box，6px 桶合并同行 |
| `firstViewportBlocks` | 首屏语义块数 | `section/article/h2/h3/[data-ui-block]` 且 top∈[0,vp) |
| `firstViewportTextLines` | 首屏可见文本行数 | TreeWalker + line-box，长块按行高估算折行 |

## 2. 本轮执行的预算契约（final 全 PASS）

| 契约 | 预算行 | 上限 | 实测 |
|---|---|---|---|
| Search Mobile row | `rowTextLines` | ≤5 | PASS（行=divider、radius 0；规则数量行已按 §21.5 移除） |
| Search Detail 首屏 | `firstViewportBlocks` | ≥5 | PASS |
| Place Mobile 首屏 | `firstViewportVisibleTextLines` | ≤26（warnAt 22） | 38 → **WARN**（既有容忍项，见 PLACE 报告） |
| Search Mobile 首屏 | `firstViewportTextLines` | 视契约 | PASS |

## 3. 为什么用 line-box 而不是 innerText

- innerText 会把「名称 + 同排状态 badge」数成两行；line-box 桶合并让它们算 1 行。
- 隐藏文本（SR-only / aria-hidden）不参与计数，避免预算被辅助标记虚高。
- 这是 §21.5 的「row ≤5 行」能对真实 DOM 成立的关键。

## 4. 本轮移除的内容负担（§21.5 / §39 / §40）

- Search row：移除 规则数量 / 人工核验数量 / 内部来源计数 / domain fact count 行
  （蓝图明文禁止）；e2e 断言同步为 decision-line 语义（`row-rule` 存在/缺席），
  不是删除测试。
- Reality 事件：time col 72px 只放时钟时间，日期进 date-group header——72px 列
  永不折行。
- Evidence 步：label + note 两行以内，marker col 固定 24px。
- Contribution：第一屏仅 5 个固定选项 + 一条提示行，choice-count 走隐藏计数。

## 5. 结果

- final budget 相关行全部 PASS；唯一 WARN（Place Mobile 首屏行数）为既有容忍项。
