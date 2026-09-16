# Responsive Matrix

> 基于源码与真实构建产物，说明各断点下的实际行为（不是目标态）。

## 1. 断点定义

`packages/design-tokens/src/index.ts`：

```
sm: 0    md: 480    lg: 768    xl: 1024
```

`breakpointFor(width)` 是唯一解析函数。

## 2. H5（Consumer）

| 宽度 | 实际行为 | 判定 |
|---|---|---|
| 360×800 | 单列，`#app` `max-width: 480px` 内自适应，`.page` padding `16px 16px 88px`（底部 nav 留白） | PASS |
| 375×812 | 同上 | PASS |
| 390×844 | 同上（E2E 之外的宽度，未做机器验证） | PASS（同源规则） |
| 393×852 / 430×932 | 同上 | PASS（同源规则） |
| 768 / 1024 / 1280 | **居中 480px 单列**，两侧留白；无断点重排 | PASS_WITH_LIMITATIONS |

- `index.html` 有 `viewport-fit=cover`，配合底部留白处理安全区。
- H5 `styles.css` 中**没有**任何 `@media (max-width/…)` 宽度断点——只有
  `@media (prefers-reduced-motion: reduce)`。也就是说 H5 是「弹性单列 + 最大宽度约束」，
  而不是多栏响应式。对城市工具类移动端产品这是可接受取舍，但不是规范 §60 描述的完整断点体系。

## 3. Admin

| 宽度 | 实际行为 | 判定 |
|---|---|---|
| ≥900 | 多栏表格 + 工具栏 | PASS |
| <900 | 一处 `@media (max-width: 900px)` 做降级 | PASS_WITH_LIMITATIONS |
| 1280 / 1440 / 1920 | 正常；未做超大屏栅格利用 | PASS |

## 4. 长文本 / 溢出

| 场景 | 现状 |
|---|---|
| 长中文场所名 | 单行省略/换行依赖各 view；无统一 `text-overflow` token |
| 长来源名 / 长法条标题 | `SourceBadge` 用固定文案（官方法规 / 政府来源…），原始长标题不直接进徽章 |
| 长 reason 文本 | PlaceView 第 7 段按块级展示 |
| 表格长字段 | **Admin 表格无列宽/换行控制**（见 `ADMIN_UI_AUDIT.md` 未达标 2） |

## 5. 机器验证覆盖（已补齐）

- 功能 E2E（`playwright.config.ts`）仍在默认视口运行——它断言的是**行为**，视口无关。
- **视觉回归（`playwright.visual.config.ts`）已按 5 个视口实测**，逐页出图并可复现：

| project | 引擎 | 视口 | 消费者页 | Admin 页 |
|---|---|---|---|---|
| `h5-390` | Chromium（Pixel 5） | 393×851 @2.75 | 11 | — |
| `h5-768` | Chromium（tablet） | 768×1024 @2 | 11 | — |
| `h5-1440` | Chromium | 1440×900 | 11 | — |
| `admin-1440` | Chromium | 1440×900 | — | 7 |
| `admin-768` | Chromium（tablet） | 768×1024 @2 | — | 7 |

合计 47 张基线，比对模式 **47 passed**，详见 `VISUAL_REGRESSION_BASELINE.md`。

### 实测补充的两条事实

1. **平板档不用 WebKit**。`devices["iPad (gen 7)"]` 解析为 WebKit，而本环境下 WebKit
   加载不了应用（模块请求 404 + cancelled），只会截出空白页并报 PASS。
   经实测改为 Chromium 768 宽（保留 iPad UA 与 `hasTouch`），理由与证据见 `VISUAL_REGRESSION_BASELINE.md` §3.2。
2. **触控目标是真实量出来的**。390 宽下 `a.btn-inline` 实测 75×29、`input` 实测 328×42，
   均低于 44px 指引；已在 `styles.css` 统一到 `--pa-layout-touch-target`，a11y 审计归零。
   「设了 padding 应该够了」这种推法算不出 42 vs 44。

## 6. 结论

| 项 | 判定 |
|---|---|
| RESPONSIVE_MOBILE（360–430） | PASS |
| RESPONSIVE_TABLET（768） | PASS_WITH_LIMITATIONS（H5 为居中窄栏，非真正重排） |
| RESPONSIVE_DESKTOP（1024–1920） | PASS_WITH_LIMITATIONS（同上；Admin 正常，超大屏未优化） |

局限不影响「小屏是否拥挤、是否溢出」这一核心问题；缺的是更宽的断点利用与机器验证。
