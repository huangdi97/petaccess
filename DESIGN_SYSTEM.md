# DESIGN_SYSTEM.md

> v0.6 Beta 设计系统 · 对应 `UI_UX_IMPLEMENTATION_SPEC.md` §1/§3/§9/§10
> 实现位置：`packages/design-tokens`（单一事实来源）→ `apps/client-h5/src/styles.css` 消费

---

## 1. 视觉定位

中性、清晰、城市工具、信息可信、证据可追溯、克制。

**不做**：大面积粉色、爪印/卡通堆叠、「雷店」/红黑榜/文明评分/卫生评分、过度社交化。

判断准则：当一处设计无法同时表达「来源」与「时效」时，它就不属于本产品。

---

## 2. 令牌清单（`packages/design-tokens/src/tokens.css`）

| 组 | 令牌 | 值 |
|---|---|---|
| 表面 | `--pa-color-bg-app` / `-surface` / `-sunken` / `-overlay` | `#f4f6f8` / `#fff` / `#eef1f4` / `rgba(20,28,36,.44)` |
| 文字 | `--pa-color-text-primary` / `-secondary` / `-muted` / `-inverse` | `#1d2733` / `#4a5560` / `#69747f` / `#fff` |
| 描边 | `--pa-color-border` / `-strong` / `--pa-color-focus` | `#e4e8ec` / `#c8d0d8` / `#34618e` |
| 品牌 | `--pa-color-accent` / `-weak` | `#34618e` / `#e7eef5` |
| 状态 | `--pa-color-status-{allowed,conditional,restricted,unknown,conflict,stale}` + `-bg` | 见 §3 |
| 间距 | `--pa-space-1..7` | 4 / 8 / 12 / 16 / 24 / 32 / 48 px |
| 圆角 | `--pa-radius-sm/md/lg/pill` | 6 / 10 / 12 / 999 px |
| 字体 | `--pa-font-family`、`--pa-font-size-xs..2xl`（11→20）、`--pa-font-weight-*`、`--pa-line-height-*` | PingFang SC / Microsoft YaHei / Segoe UI |
| 高度 | `--pa-elevation-0..3` | 无 → `0 6px 18px rgba(0,0,0,.14)` |
| 动效 | `--pa-motion-fast/base/slow` = 120/200/320ms，`--pa-motion-ease` | `prefers-reduced-motion` 下全部归零 |
| 布局 | `--pa-layout-max-width` 480、`--pa-layout-touch-target` 44、`--pa-layout-tabbar-height` 56 | |

**断点**（CSS 变量不能用于 `@media`，故在 TS 中定义并在 `tokens.css` 注释同步）：
`sm 0` · `md 480` · `lg 768` · `xl 1024`，`breakpointFor(width)` 提供运行时判定。

---

## 3. 状态语义（§3：绝不仅靠颜色）

`STATUS_SEMANTICS` 强制每条状态同时具备 `label` + `icon` + `colorVar` + `bgVar` + `ariaLabel`。

| key | 中文 | icon | 前景色 | 底色 |
|---|---|---|---|---|
| `ALLOWED` | 明确允许 | ✓ | `#2e7d52` | `#e8f3ec` |
| `CONDITIONAL` | 有条件 | ◐ | `#8a5f18` | `#faf1df` |
| `RESTRICTED` | 明确限制 | ✕ | `#8f4a3a` | `#f7e9e5` |
| `UNKNOWN` | 尚未核验 | ? | `#5c6873` | `#eceff2` |
| `CONFLICT` | 来源存在不一致 | ⚠ | `#6f5a9e` | `#eeeafa` |
| `STALE` | 需要复核 | ⟳ | `#8a5f18` | `#faf1df` |

**词汇归一**：后端 resolver 使用 `MATCH/CONDITIONAL/RESTRICTED/UNKNOWN/CONFLICT`，存储层使用 `allowed/conditional/prohibited`。两者通过 `ANSWER_STATUS_TO_SEMANTIC` / `EFFECT_TO_SEMANTIC` 映射到同一展示词汇，客户端无需理解两套命名。

**渲染约束**：`apps/client-h5/src/components/StatusBadge.vue` 是唯一的状态渲染入口；它总是输出 icon 元素、文字与 `visually-hidden` 的完整 aria 描述。`tests/unit/test_design_tokens.py` 断言这一点，任何绕过它的写法都会在测试中失败。

---

## 4. 来源徽标（§4）

`SOURCE_BADGES`：`官方法规 §` / `政府来源 ⌂` / `管理方确认 ◉` / `现场核验 ◎` / `用户现场报告 ☰` / `需要复核 ⟳` / `来源不一致 ⚠`。
`badgeForSourceType()` 将后端 `source_type` 映射为上述前台标签；后台保留更细的 `evidence_strength`。

---

## 5. 可访问性（§10）

| 要求 | 实现 |
|---|---|
| 对比度 | 状态前景/底色对均为深色文字浅色底，正文 `#1d2733` on `#fff` |
| 键盘 | `:focus-visible` 统一 2px `--pa-color-focus` 外描边 |
| 触控 | `button` / `.pill` / `.tabbar a` 强制 `min-height: 44px` |
| 非颜色唯一 | StatusBadge 强制 icon + 文本 + `aria-label` |
| 屏幕阅读器 | `.visually-hidden` 提供完整语义描述 |
| 减少动效 | `prefers-reduced-motion` 将全部 motion 令牌归零 |
| 字号缩放 | 全部字号为令牌，未使用固定 px 内联于关键文案 |

---

## 6. 消费方式

```css
/* apps/client-h5/src/styles.css */
@import "@petaccess/design-tokens/tokens.css";
```

已验证：构建产物 `dist/assets/index-*.css` 内含全部 `--pa-*` 令牌（见 `FRONTEND_QA_REPORT.md` §2）。

---

## 7. 已知缺口（诚实记录）

1. **暗色主题未实现**：令牌已按可覆盖方式组织（覆盖 `:root` 即可），但未提供 dark 变量集，`UI_UX_IMPLEMENTATION_SPEC` §11 的「dark/light 一致」未验证。
2. **视觉回归截图未采集**：Playwright 截图基线（§11 所列 9 个页面）尚未建立——需要可运行的 API 与数据层（当前 ENV-01 阻塞）。
3. **设计令牌未接入 admin**：`apps/admin` 仍使用自有 `styles.css`；接入属 P4（Admin/Data Ops）范围。
4. **uni-app x 端未接入**：`apps/client` 的 `.uvue` 页面尚未引用令牌；该端构建依赖 HBuilderX（B-01）。
