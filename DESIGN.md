# DESIGN.md — PetAccess

> **DERIVED DOCUMENT**
> Derived from `宠物准入与公共空间共处规则平台_v0.10-R1_..._统一全量母版_2026-09-27.md`（Canonical Master）。
> **Canonical Master wins on conflict.**
> Direction: **Structured Utility**（V020_M3_UI_DIRECTION_DECISION.md，DESIGN FREEZE 生效）。

## 1. Design direction

PetAccess = **Modern Urban Information Tool**：

```text
Calm · Neutral · Urban · Evidence-first · Modern · Structured · Trustworthy · Lightweight
```

明确不是：

```text
Cute / Pet-commerce / Social feed / Government dashboard / Financial dashboard /
Cyberpunk / AI-gradient product / Gaming UI
```

用户第一反应应是「这是一个成熟的信息工具」，不是「这是 AI 自动生成的 App」。

## 2. Design principles

1. **Structure > Decoration**：先排版、留白、分隔线、分区层级、列表、语义图标、文本、元数据；后 Card/Badge/Shadow/Color。
2. **Rule 与 Reality 可区分但同源**：Rule = 结论徽标族（StatusBadge，Text+Icon+Structure+Color 共同表意）；Reality = 摘要段落族（RealityStatus/FreshnessStatus/EvidenceMeta）。绝不只靠颜色表意。
3. **Evidence 可见、Freshness 可理解**：行级带 Freshness/Evidence 元数据；无数据时显示诚实空态（「暂无现场记录 ≠ 没有动物」）。
4. **克制**：无渐变、无玻璃拟态、无发光按钮、无大圆角滥用、无重阴影滥用、无 hero 大标题模板、无 eyebrow/kicker、无 AI 紫蓝渐变。
5. **Card 是语义容器不是默认**：Card 只用于 interactive container / strong semantic grouping；优先 divider + whitespace + text。
6. **Badge 只用于重要语义状态与小分类元数据**：禁止每行 3–6 个 pill。
7. **Distill**：第一屏只保留帮助决策的信息；重复字段/重复徽标/低价值元数据一律删除。
8. **Desktop 是真 adaptive**：≥768 rail、≥1280 真实层级（宽容器 + 分区/Split），不是移动页面放大。
9. **Motion 只服务导航连续性 / 状态转换 / 交互确认**；respect `prefers-reduced-motion`。

## 3. Token SSOT（不变，全部来自 @petaccess/design-tokens）

- 颜色：`--pa-color-*`（bg #f4f6f8 / surface #fff / accent #34618e / status 语义族 / reality 语义族 / evidence 语义族）。
- 字体：`--pa-font-family`（PingFang SC / Microsoft YaHei / Segoe UI / system-ui）+ `--pa-font-size-*`（11–32px role scale）+ `--pa-font-weight-*`。
- 间距：`--pa-space-*`（4px 基数有限刻度：4 8 12 16 20 24 32 40 48）。
- 圆角：sm 6 / control 8 / md 10 / lg 12 / pill。
- 边框：1px / strong 2px；shadow 仅在需要深度时使用且带 offset+blur（当前默认不用）。
- 断点：sm/md/lg(768)/xl(1280)（`BREAKPOINTS`）；z-index、safe-area、layout（rail 宽、content max/narrow/gutter、tabbar 高、touch target）均有 token。

**页面不得私有定义** color/spacing/radius/font 值；所有值走 token。

## 4. Typography roles

| 角色 | token | 用途 |
|---|---|---|
| Page title | `--pa-font-size-2xl`(20) · medium · tight | Home 标题「去之前，先看看这里的规则和现场。」 |
| Place name | `--pa-font-size-xl`(18) · semibold · tight | PlacePreview 名称 / 结果行名称 |
| Section title | `--pa-font-size-lg`(16) · medium | 分区标题（附近已核验 / 规则待核实） |
| Primary conclusion | `--pa-font-size-base`(15) · medium | Rule 状态文本 / Reality 摘要首行 |
| Body | `--pa-font-size-base`(15) · regular | 正文 |
| Metadata | `--pa-font-size-md`(13) · muted | 地址 / 类型 / 条件 / 依据行 |
| Freshness/Evidence | `--pa-font-size-md`(13) · muted + badge | FreshnessStatus / EvidenceMeta |
| Helper | `--pa-font-size-sm`(12) · muted | 说明 / 语义注释 |

## 5. Layout system

- **AppShell 框架**（ConsumerAppShell）：mobile bottom tabbar（首页/地图/贡献/我的）<768；desktop rail（首页/搜索/地图/贡献 + 我的/设置/关于 + 版本）≥768；safe area 由 shell 消费。
- **DesktopContentContainer**：single-column（细节页）/ wide（Home、结果页）/ split（Search list+preview、Map+detail）。
- **Home 层级**：搜索主任务 → 视角（单组）→ 附近已核验（Rule 结论 + Reality 摘要行）→ 规则待核实 → 贡献 footer。
- **Search 层级**：搜索框 → 结果列表（行 = identity → Rule → Reality → Freshness/Evidence → 仅相关 divergence）→ 桌面右侧 PlacePreview。

## 6. State semantics（正式文案，沿用共享词汇）

- Home empty：「当前还没有已发布的场所数据」。
- Search empty：「没有找到已收录场所」+ 贡献 CTA + 清筛选。
- Rule 空：「暂无可靠规则结论」（UNKNOWN ≠ 允许/禁止）。
- Reality 空：「暂无足够现场记录」；「暂无现场记录 ≠ 没有动物」。
- Staff 空：「暂无经核验的工作人员处理记录」。
- Facility 空：「暂无经核验的动物设施记录」。
- Offline：「当前离线，部分内容可能不是最新状态」（GlobalOfflineBanner）。
- Error：回答「发生了什么 / 哪些数据仍可用 / 是否有缓存 / 用户能做什么 / Retry 在哪」。

## 7. Page states（本轮范围）

- AppShell：`M3-PARTIAL → FINAL`（移除旧 AppShell 双层包裹；上下文收敛单行）。
- Home：`M3-PARTIAL → FINAL`（首屏收敛、Reality/Freshness/Evidence 行级、桌面层级）。
- Search：`M3-PARTIAL → FINAL`（移动端 Reality 摘要、tags 减负、split 保留）。
- Map/Place/Trace/Evidence/Contribution：仅共享层自然影响（`FUTURE-M4/M5/M7`）。
