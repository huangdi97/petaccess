# Blind-Model UI Skill Usage

> Goal v0.2.2 §15–§19。本文件记录 4 个已安装 Skill 在「无眼模式」下的实际使用方法，
> 以及它们的输出如何被转换为可测量约束后进入代码。任何模糊建议（"让层级更清楚"、
> "留白更多"、"更高级"）都不得直接进入实现；必须先变成数字或明确结构。

## 1. 实际读取的 Skill（本机安装路径）

| Skill | 路径 | 本轮职责 |
|---|---|---|
| Impeccable | `C:\Users\Kaiser\.agents\skills\impeccable\SKILL.md` | Design Intent → Numeric / Structural Constraints |
| frontend-design | `C:\Users\Kaiser\.agents\skills\frontend-design\SKILL.md` | Contract → Production Implementation Plan |
| UI UX Pro Max | `C:\Users\Kaiser\.agents\skills\ui-ux-pro-max\SKILL.md` | 针对性 pattern research → RULE / RATIONALE / IMPLEMENTABLE CONSTRAINT / ANTI-PATTERN |
| Playwright (CLI) | `C:\Users\Kaiser\.agents\skills\playwright-cli\SKILL.md` | 浏览器驱动、route 状态、DOM/bbox/computed probe、截图证据 |

Agent **没有**视觉。Screenshot 仅作为人类验收证据；Agent 的 UI 判断一律来自
DOM / accessibility tree / computed styles / bounding boxes / text content /
layout metrics / CSS variables / machine contract 对比结果。

## 2. Impeccable → 数值约束

针对每个页面 archetype（Search / Place / Home / Map / Reality / Evidence /
Contribution），将 Impeccable 的 craft 输出强制转换为 measurable constraints：

| Impeccable 语言 | 转换规则 |
|---|---|
| "层级要清楚" | 字号阶梯（identity 26–30 / decision 26–32 / section 17–19 / body 14–16 / metadata 12–13）+ 字重（600–700 / 500 / 400）+ 语义标记（左 accent 线 2px） |
| "增加留白" | 只允许 token 阶梯 4/8/12/16/20/24/32/40/48；section↔section 24–32px；禁止 >180px 空洞 |
| "更高级 / premium" | 名词禁止：gradient / glass / hero / 新配色 / 新字体；改用：surface 扁平 + divider + 单一 anchor |
| "不要像后台" | 结构约束：cells→行、cards→divider rows、label/value 表→judgment 块 |

转换产物：`docs/ui/contracts/*.md` + `json/*.json`（每个约束都有 min/max 或
结构断言，供 `tools/ui-oracle/compare.ts` 判定）。

## 3. frontend-design → 实现计划

用于把契约落成实现，输出格式：

| 问题 | 回答 |
|---|---|
| 哪个 layout 用 grid/flex | 桌面 split = flex（rail + pane + detail）；移动 = 单列 block flow |
| 哪些尺寸用 token/clamp | 所有 font-size / spacing / radius 引 design-tokens，禁止 invent 数值 |
| 哪些组件抽取 | Search/Place 共用 `DecisionInspector`、`QueryContextBar`、`StatusBadge` |
| sticky/scroll 边界 | Place inspector sticky top = context bar + 20–24px |
| desktop/mobile transform | `<1100px` 单列、`>=1100px` split；不是等比缩放 |
| 页面私有 CSS vs token | 只允许布局/定位私有样式；颜色、字号、间距、radius 必须走 token |

## 4. UI UX Pro Max → pattern research

只做针对性研究（list-detail / inspector / dossier / spatial workspace /
bottom sheet / timeline / provenance / dense information UI / accessible
status），每次一个具体问题，输出统一为：

```text
RULE:            （可执行的规则）
RATIONALE:       （为什么）
IMPLEMENTABLE CONSTRAINT: （直接可测量的约束）
ANTI-PATTERN:    （不要做什么）
```

示例（search 结果行）：
```text
RULE: Selected list item uses background tint + left indicator, not a floating card.
IMPLEMENTABLE CONSTRAINT: radius=0, background=--pa-color-accent-weak, left accent=2px
ANTI-PATTERN: rounded selected card on a flat list
```

不持久化新的 design system；不新增主题。

## 5. Playwright → 唯一测量与证据通道

- route state setup：`petaccess_visual` 确定性 seed + API :8011 + preview :5175；
- deterministic fixture：capture 时 animations 禁用、reduced-motion 模拟、固定 viewport；
- DOM / bbox / computed probe：`tools/ui-oracle/probe.ts`；
- text scan：`tools/ui-oracle/language-scan.ts`（UUID / snake_case / ALL_CAPS / invariants）；
- responsive metrics：contract viewport 矩阵 360/390/430/768/800/1280/1440；
- screenshots：`artifacts/blind-ui-recovery/screens/{stage}/`（证据产物）。

## 6. 本轮 Skill 产出一览

- `docs/ui/contracts/*.md`（12 份）——Impeccable + frontend-design 转换结果；
- `docs/ui/contracts/json/*.json`（10 份）——机器可读约束；
- `tools/ui-oracle/*`——Playwright + node 测量/对比实现；
- `artifacts/blind-ui-recovery/probes|reports|screens/`——证据。

## 7. 诚实边界

- Agent 不宣称"截图看起来正确"；
- 只报告 machine contract 判定（PASS/WARN/FAIL）与测量值；
- 人类视觉验收由用户在 `HUMAN_REVIEW/` 截图包上完成。