# PetAccess direct-v8 Canonical Visual Recovery（2026-10-05）

> 状态：ACTIVE RECOVERY FREEZE  
> 适用分支：`feat/ui-direct-craft-v8`  
> 权威顺序：Canonical Master v0.10-R1 > 本恢复冻结 > UI Reconstruction Design Freeze > v0.2.3 数值蓝图 > 历史截图/历史实现。  
> 若后层文件与 Canonical Master 冲突，必须修改后层文件，不能用机器 Gate 反向否定 Canonical。

## 1. 为什么重开

本轮人工检查确认 direct-v8 出现了典型的 **machine-green / product-wrong**：

- 页面 archetype 大体正确，但产品第一眼识别被削弱；
- 为了消灭 card / pill / density，部分页面过度“摊平”，变成功能页或 QA 工具；
- Rule / Reality / Evidence 三层虽然数据存在，但没有持续形成主视觉层级；
- v0.10-R1 已明确新增的首页推荐、规则-现场差异、Map 四 Lens、Place Coexistence Passport 第一屏工作人员/设施事实，被后续收口过程部分压缩或遗漏；
- 某些 Oracle 数值已经与自己的 Executable Blueprint 漂移（例如 Search row 蓝图 112–132px，但旧 JSON 仍限制在更小高度）；
- “自动化可以测到的结构”被误当成“设计已经还原”。

因此本轮不是换主题、加装饰、做视觉皮肤，而是恢复 **产品语义 × 信息架构 × 视觉层级** 的一致性。

## 2. 外部模式研究：只吸收机制，不复制品牌

### 2.1 Wheelmap

Wheelmap 的强项不是“漂亮地图”，而是把 **未知状态也做成一等状态**，并让用户在地图上快速区分 fully / partially / not / unknown。对 PetAccess 的启发：

- Unknown 必须可见，不能默认隐藏；
- marker 需要形状/文字/颜色协同，而不是颜色单独表意；
- 地图的任务是快速建立空间态势，不是在 marker 上塞完整详情。

PetAccess 不复制其“单一总状态”模型，因为 PetAccess 同时拥有 Rule、Reality、Facility、Divergence 四个事实视角。

### 2.2 AccessNow

AccessNow 的地图、过滤、照片与众包贡献强调“到达前知道现场条件”和“社区补充真实世界信息”。可借鉴：

- 场所发现和现场事实需要并行；
- 贡献入口必须低负担；
- 透明展示“哪些信息已知 / 哪些仍需补充”比伪精确评分更重要。

PetAccess 不复制 review/rating 模型；平台继续坚持事实层与证据层，不做场所总分。

### 2.3 Google Maps place edits / attributes

Google Maps 的可编辑属性采用明确值、Unsure/不知道以及提交后 review 状态；照片可帮助验证。可借鉴：

- 用户前台只回答自然语言事实，不填写内部 provenance 枚举；
- 不确定是合法答案；
- 提交后必须明确“待核验”，不能让用户误以为已改变正式事实；
- 证据照片是核验材料，不是装饰图。

### 2.4 Apple HIG：Search / Maps / Place card

Apple 当前 HIG 强调：

- Search 重要时要处在主位置；
- recent / suggestion 能减少重复输入；
- 搜索结果应简化、排序并允许按必要属性过滤；
- 地图底图可以低饱和，让 overlay 成为主角；
- 地图控件必须可辨识；
- 地点卡承担选中地点的结构化信息，不应让所有信息永久压在地图上。

这与 PetAccess 的 Search-first Home、List–Detail Search、Spatial Map + Selected Preview、低饱和地图基底完全一致。

## 3. direct-v8 的最终视觉命题

PetAccess 不是“宠物友好 App”，也不是“规则数据库前端”。正确的第一眼应该是：

> **一个冷静、可信、空间化的现实公共空间动物共处信息工具。**

用户在任何核心页面都能快速理解三件事：

1. **规则怎么说？**
2. **现场发生过什么？**
3. **这些信息有什么依据、是否新鲜、是否存在冲突？**

只有 Place/Map 等场景确有必要时才进一步展开工作人员处理、动物设施、分区域、历史、纠错等信息。

## 4. 核心视觉纪律

继续禁止：

- 白卡墙、每字段一张卡；
- chip/pill 墙；
- 大圆角 + 大阴影泛滥；
- AI 紫蓝渐变、玻璃拟态；
- pet-friendly score / 避雷榜；
- 用绿色自动表示“好”，用红色自动表示“坏”；
- Desktop 只是移动页面拉宽；
- 为了让截图“更满”而添加伪造数据、placeholder filler 或旅游图片。

但“无卡片”不等于“无层级”。必须恢复：

- 强 identity；
- 强主事实；
- 明确 section rhythm；
- Rule / Reality 的并列对照；
- Evidence / freshness 的弱元数据层；
- 需要时的单一强 CTA；
- 地图/选中状态的空间焦点。

## 5. 页面终态冻结

### 5.1 Home = Task Launcher + Coexistence Digest

顺序严格回到 Canonical：

1. 上海 · 试点 / 当前查询；
2. “去之前，先看看这里的规则和现场。”
3. 主搜索；
4. “你更想先看什么？”四个任务 Lens；
5. **按你的关注推荐**；
6. **规则与现场速览**；
7. **规则与现场不一致**（有数据才显示）；
8. 最近查看；
9. 贡献 / 方法说明。

推荐不是评分，也不是“适合你”；只根据已有事实把更相关的信息上浮。

### 5.2 Search = List–Detail Workspace

每条结果必须同时保留：

- Place identity；
- 类型 / 距离；
- Rule semantic status；
- **Reality headline**；
- Rule conclusion + 最关键条件；
- Evidence / freshness metadata。

默认不应只让 Rule 成为唯一主角。进入 `rules` Lens 时再强化 Rule；presence/indoor/dining Lens 强化 Reality。

Desktop 继续 List + Detail；Mobile 继续单列结果 → Place。

### 5.3 Map = Spatial Workspace with 4 Lenses

Map 必须正式恢复 Canonical 四 Lens：

- Rule；
- Reality；
- Facility；
- Divergence。

四个 Lens 只改变 **同一 CoexistenceSnapshot 的投影**，绝不改变领域事实。

规则筛选只在 Rule Lens 出现；Reality / Facility / Divergence Lens 默认显示全部场所，避免把其它事实误装成“准入状态过滤器”。

Mock provider 仍必须像空间，不得退回数字网格；未来替换真实 provider 时不改变 Consumer 业务逻辑。

### 5.4 Place = Coexistence Passport

第一屏同时回答：

- 当前 Rule；
- 最近 Reality；
- 工作人员处理；
- 动物设施；
- Rule-Reality Divergence；
- Evidence/freshness。

第一屏明确提供：

- 查看证据；
- 为什么；
- 纠错 / 补充。

完整详情继续用 Overview / Space / Rules / Reality / Evidence 视图分层，不恢复无限长 dossier。

### 5.5 Reality = Temporal Event Log

继续 timeline-first：

TIME → EVENT → LOCATION → STAFF RESPONSE → REVIEW/EVIDENCE。

无记录只能说“暂无近期现场记录”，不得写“没有动物”。

### 5.6 Evidence = Provenance Record

继续突出：

- Record identity；
- provenance chain；
- Observed / Submitted / Reviewed 三个时间；
- evidence item；
- source；
- rule evidence 与 reality evidence 分维计数。

证据图片只在真实存在且具证据价值时出现。

### 5.7 Contribution = Structured Transaction Flow

第一问保持“你刚刚知道了什么？”；用户只回答消费者语言。

规则、动物出现、工作人员处理、设施、场所纠错均进入待核验流程。所有内部 PlaceMatchState / FactEvidenceState / RealityDecision 均不前台泄漏。

## 6. 本轮代码恢复项

本轮直接在 GitHub 完成：

- RowFacts 保留完整 CoexistenceSnapshot，消除 UI 为了展示 staff/facility/divergence 再造第二解释器；
- Home 恢复推荐 / 双事实速览 / divergence / recent 的 canonical 次序；
- Search 恢复 Rule + Reality + Evidence 同屏，并把 row geometry 恢复到 112–132px 蓝图；
- Search / Map 规则状态过滤 key 从错误的 MATCH 修正到 UI semantic key ALLOWED；
- Map 恢复四 Lens，marker / list row 同步投影；
- Place Overview 恢复 Rule + Reality 并排，并把 Staff / Facility / Divergence 拉回第一屏；
- Place 恢复 查看证据 / 为什么 / 纠错 三个核心动作；
- Oracle contract 同步 canonical，而不是让旧契约逼迫新实现退化。

## 7. Human Visual Acceptance 停止线

以下全部完成也只能写：

`MACHINE_PASS / HUMAN_REVIEW_READY`

不能写：

`UI_HUMAN_VISUAL_ACCEPTANCE = PASS`

直到真实 Web / Windows / Android 运行截图由用户人工确认。

人工复核至少看：

- Home desktop + 430；
- Search desktop selected + 430；
- Map 四 Lens desktop + mobile selected sheet；
- Place overview desktop + 430；
- Reality ready；
- Evidence ready；
- Contribution choose + one complete path；
- Mine / Settings / Pets 至少各一张，确认整体产品语言没有重新退化为“后台表单”。

## 8. 研究结论

真正需要恢复的不是更多装饰，而是 **产品语义的视觉可见性**：

- Wheelmap 证明 unknown/partial 等状态应成为地图一等信息；
- AccessNow 证明现实空间工具必须让贡献、筛选和透明事实进入主要体验；
- Google Maps 的 edit/review 流证明“不确定 + 待核验 + 证据材料”比伪确认更可信；
- Apple HIG 证明 Search / Maps / Place card 的空间关系应服务任务，不应为了统一模板牺牲平台直觉。

PetAccess 的差异化不在于“也有地图”，而在于 **Rule + Reality + Evidence/Governance + Divergence** 四者在一个现实场所模型里被严格分离又能同时阅读。
