# UI Design System

> 反映真实实现，不是目标态。`packages/design-tokens` 是唯一 token 源；本文档说明它现在有什么、
> 缺什么、以及各 app 的遵守情况。

## 1. 位置与消费方式

| 项 | 真实值 |
|---|---|
| Token 源 | `packages/design-tokens/src/tokens.css`（CSS 变量）+ `src/index.ts`（TS 常量与语义映射） |
| H5 消费 | `apps/client-h5/src/styles.css` 顶部 `@import "@petaccess/design-tokens/tokens.css"`，并在 `:root` 里做短别名（`--bg` `--panel` `--line` `--text` `--muted` `--accent` …） |
| Admin 消费 | `apps/admin/src/styles.css` 同样 import |
| 本地重声明 | 无硬编码 hex（`apps/*/src` 内 `#rrggbb` 命中数为 0，仅 `dist/` 构建产物里有） |
| 机器校验 | `tests/unit/test_design_tokens.py`（token 单一来源、状态必须图标+文字、禁用文案词表） |

## 2. 已有 token

### 颜色（语义化）

`--pa-color-bg-app` / `bg-surface` / `text-primary` / `text-muted` / `text-inverse` / `border` /
`accent` / `skeleton-sheen`，以及状态色 `--pa-color-status-{allowed,conditional,restricted,unknown,conflict,stale}`
与其 `-bg` 底色变量。

### 状态语义（§35 的「颜色 + 图标 + 文字」硬要求）

`STATUS_SEMANTICS` 对 6 个状态各给出 `label / icon / ariaLabel / colorVar / bgVar`：

| 状态 | 文案 | 图标 | aria |
|---|---|---|---|
| ALLOWED | 明确允许 | ✓ | 明确允许：已核验来源明确允许 |
| CONDITIONAL | 有条件 | ◐ | 有条件：满足所附条件后方可进入 |
| RESTRICTED | 明确限制 | ✕ | 明确限制：已核验来源明确限制 |
| UNKNOWN | 尚未核验 | ? | 尚未核验：在已核验来源中暂未找到明确规则，**不代表允许** |
| CONFLICT | 来源存在不一致 | ⚠ | 已收录来源之间结论冲突，待人工复核 |
| STALE | 需要复核 | ⟳ | 证据超出核验时效，结论可能已变化 |

映射函数：`semanticForAnswerStatus()`（resolver 的 MATCH/CONDITIONAL/RESTRICTED/UNKNOWN/CONFLICT）
与 `semanticForEffect()`（allowed/conditional/prohibited）。resolver 保留自己的命名，只有展示层归一化。

### 来源徽章

`SOURCE_BADGES`：官方法规 § / 政府来源 ⌂ / 管理方确认 ◉ / 现场核验 ◎ / 用户现场报告 ☰ /
需要复核 ⟳ / 来源不一致 ⚠；`badgeForSourceType()` 做 `source_type → badge` 映射。

### 页面状态（与访问状态是两套词汇）

`PAGE_STATES`：LOADING / EMPTY / ERROR / OFFLINE / PARTIAL / STALE / CONFLICT / PERMISSION_DENIED，
每个都有图标 + 标题 + 一句中性说明（例如 EMPTY：「本平台只展示已核验收录的信息；未收录不代表该场所没有规则。」）。

### Spacing / Radius / Typography / Elevation / Motion

- spacing：`--pa-space-1..7` = 4 / 8 / 12 / 16 / 24 / 32 / 48 px（4px 基准）
- radius：`--pa-radius-sm 6` / `--pa-radius-control 8` / `--pa-radius-md 10` / `--pa-radius-lg 12` / `--pa-radius-pill 999`
  （`--pa-radius-control` 为本轮新增，用于收敛 Admin/H5 里散落的裸 `8px`）
- typography：`--pa-font-size-{xs 11, sm 12, md 13, base 15, lg 16, xl 18, 2xl 20}`，
  `--pa-font-weight-{regular 400, medium 500, bold 700}`，`--pa-line-height-{tight 1.25, base 1.5}`
- elevation：`--pa-elevation-0..3`（none → `0 6px 18px rgba(0,0,0,.14)`），共 4 层
- motion：`--pa-motion-{fast 120ms, base 200ms, slow 320ms}` + `ease`；
  `@media (prefers-reduced-motion: reduce)` 下全部归零
- 触控目标：`TOUCH_TARGET_PX = 44`

### 文案约束

`REQUIRED_COPY` 固定中性表述；`FORBIDDEN_COPY` 含「雷店/雷区/黑榜/红榜/星级/文明指数/遇宠率/爱宠人士…」，
由 `test_design_tokens.py` 在源码层拦截。

## 3. 缺口（本轮实测，未修）

| # | 缺口 | 影响 | 处置 |
|---|---|---|---|
| 1 | spacing 阶梯缺 `20` / `40` 两档（规范 §37 列出 4-8-12-16-20-24-32-40-48） | 需要这两档时会退回裸 px | 记录为 P2；未新增档位以免引入未经评审的视觉变化 |
| 2 | H5/Admin 的 `styles.css` 仍有约 20+ 处裸 px（`14px` `10px` `6px` `18px` 等）不在任何档位上 | 设计漂移；改 token 不会带动这些值 | 记录为 P2。本轮只收敛了圆角（3 处 `8px` → `--pa-radius-control`） |
| 3 | 无 Icon 组件层的统一封装（图标是字符 + 徽章字符串） | 图标风格靠约定维持 | P2；现有字符图标一致，未发现混用 |
| 4 | 没有 `--pa-space` 之外的组件尺寸 token（控件高度、表格行高） | 组件尺寸靠各文件 px 维持 | P2 |

## 4. 结论

**DESIGN_SYSTEM = PASS**（有单一 token 源、状态三要素齐全、禁用文案有机器校验、reduced-motion 支持、无硬编码色值）。
上表 4 项为 P2 缺口，不影响语义正确性。
