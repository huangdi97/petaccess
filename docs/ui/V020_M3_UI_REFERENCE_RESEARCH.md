# V020 M3 UI REFERENCE RESEARCH

> UI UX Pro Max（ui-ux-pro-max）本机检索结果 + Impeccable/frontend-design 方法论约束综合。仅学习 hierarchy/density/rhythm/interaction，不复制品牌、不像素级抄袭。

## 方法

- 工具：`python C:/Users/Kaiser/.agents/skills/ui-ux-pro-max/scripts/search.py`，domain=ux。
- 执行查询：① `urban city information utility trust evidence-first neutral`（--design-system）② `search results list information hierarchy` ③ `status badge semantic not color alone` ④ `offline cached data stale indicator` ⑤ `desktop navigation rail adaptive layout`。
- 约束：UI UX Pro Max = 设计研究员，不直接决定最终风格；结果服务于 PetAccess（Calm/Neutral/Urban/Evidence-first）。

## 1. Design-system 参考（查询①结果）

- **Pattern**: Trust & Authority —— 可信感来自结构（badges/certs/stats 只是辅助），PetAccess 的"可信"来自 Rule/Reality/Evidence 分层，而非营销徽章。
- **Style**: Minimalism & Swiss Style —— grid-based、高对比、克制装饰、清晰排版。与 PetAccess 现有 token（中性灰、克制 accent #34618E）高度一致。
- **Palette 参考**（不复制，仅对比语义）：navy 主色 + 中性背景 #F8FAFC + 语义色分离。PetAccess 已用更柔的 accent（#34618E）+ status 语义色（allowed/conditional/restricted/unknown/conflict）。
- **Typography**: 单一无衬线族 + 固定角色 scale 适合 Operate 模式；PetAccess 现有 PingFang/YaHei/Segoe UI system 栈符合中文城市工具定位（不引 Google Fonts，避免离线/网络依赖）。
- **Avoid**: AI purple/pink gradients、playful 装饰、emoji 作图标。

## 2. Search 结果结构（查询②）

- **No results ≠ 死胡同**：显示建议 + 出路，不要裸 "0 results"。→ PetAccess 已有 EMPTY_STATE_COPY.SEARCH + 贡献 CTA + 清筛选；M3 保持并打磨。
- **Autocomplete** 可加速（当前无）：debounced fetch + dropdown。M3 不做即时补全（范围外，避免新依赖），记录为后续 Gap；当前"输入 + 查询"模型保留。
- **结果行 anatomy 目标**（综合多条）：identity → 主结论 → 关键摘要 → 元数据 → 证据/新鲜度；一行一个主操作，避免每行多个 pill。

## 3. Status 呈现（查询③）

- **Color only 是 High severity anti-pattern**：必须 Text + Icon + Structure + Color 共同表达。→ PetAccess StatusBadge 已含文字标签 + 语义色；M3 检查 badge 是否始终带 icon/文本（确认无纯色圆点）。
- **Live badge 更新**用一条 atomic status message，不要多个竞争 live region。
- **结论**：Rule 状态与 Reality 状态用不同视觉族（badge vs 段落摘要），但同一 token 体系，避免"两个产品"感。

## 4. Offline / Stale（查询④）

- 检索返回 focus states 等通用项；对 offline 的强指导来自仓库既有规范（V020_EMPTY_ERROR_OFFLINE_SPEC）：offline ≠ app unusable；有可信 cache 时展示 cached state + last fetched + stale indicator。
- M3 落地：GlobalOfflineBanner（已有）+ 缓存层（本轮新增 query/repository）+ 文案 "当前离线，部分内容可能不是最新状态"。

## 5. Desktop adaptation（查询⑤）

- Sticky nav 不得遮挡内容（padding 补偿）→ 已有：DesktopRail 固定 + main margin-left。
- 键盘导航 tab order 与视觉一致 → e2e/人工审计。
- **桌面 ≠ 移动拉伸**：M3 让 Home 在 ≥1280 有真正的信息层级（两列或内容宽度约束 + 层级分区），Search 已 split（保留并打磨）。

## 6. Impeccable / frontend-design 方法论约束（采用）

- 禁 eyebrow/kicker 于标题之上（craft-floor ban）。
- 禁 hero-metric 模板（大数字 + 小标签 + 统计 + accent）。
- 正文 measure 45–75ch；中文长文本处理（现有排版）。
- Motion 只服务状态/导航连续性；prefers-reduced-motion 尊重。
- Card 只用于 surface grouping / interactive container / strong semantic grouping；Badge 只用于重要语义状态与小分类元数据。

## 7. 研究→设计决策映射

| 研究点 | PetAccess M3 决策 |
|---|---|
| Trust 来自结构 | Home 以"搜索主任务 + Rule/Reality 双事实分区"为结构，不以徽章阵列装点 |
| Swiss 克制 | 维持现有 token（中性、细边框、1px、受限 radius），不引入渐变/玻璃拟态 |
| No results 有出路 | Search 空态：标题 + 解释 + 贡献 CTA + 清筛选 |
| 状态非色 alone | StatusBadge 文字 + 图标 + 语义色；Reality 用摘要段落（FreshnessStatus/EvidenceMeta） |
| Offline 用缓存 | 新增 client 缓存 + 离线 fallback + stale 标注 |
| Desktop 真 adaptive | Home ≥1280 层级化布局；Search split 保留 |
