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

推荐不是评分，也不是“适合你”。只有用户真实选择过关注 Lens 后，标题才使用“按你的关注推荐”，且只改变信息排序/强调；没有已保存偏好时使用中性的“近期值得先看”。不得用内部加权分伪装成个性化推荐。

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

非 Rule Lens 不得复用“绿色 = 允许”的视觉语义：Reality 使用 Reality palette，Facility 使用 Facility palette，Divergence 使用差异/历史语义色。MarkerStatus 在非 Rule Lens 只可作为聚类/形状内部 carrier，用户可见文字必须来自当前 Lens 的事实标签。

Mock 阶段的地图缩放控件必须可真实操作，不能展示 disabled 的“道具按钮”；desktop 结果行点击先形成地图选中态与 Place Preview，再由 Preview 进入完整场所。

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

**Rule = UNKNOWN 只代表规范事实不足，绝不能把整个 Place Overview 替换成 Unknown 空页。** 即使规则未知，只要 Reality / Staff Response / Animal Facility / Evidence 中任一维度已有事实，就必须继续展示。

工作人员处理与动物设施是 Public Beta 一等信息：Overview 给摘要与独立入口；Reality view 展示完整 Staff Response 汇总，Space view 展示独立 Animal Facility 汇总。它们不得被压缩成“设施存在 = 可以进入”或“工作人员处理 = 正式政策”。

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
- Oracle contract 同步 canonical，而不是让旧契约逼迫新实现退化；
- Home 推荐改为真实 attention preference 驱动：选择 Lens 才持久化偏好，无偏好时使用中性近期信息排序；
- Search 默认恢复 Reality-first，同时保留 Rule semantic status / Rule conclusion / Evidence metadata；
- 修复 Place Rule UNKNOWN 吞掉 Reality/Staff/Facility/Evidence 的产品级错误；
- Place Reality 增加 Staff Response 一等详情，Place Space 增加 Animal Facility 一等详情；
- Map 非 Rule Lens 使用 Reality/Facility/Divergence 专属 palette，不再把现场/设施“借绿”成准入允许；
- Mock Map 的 +/− 缩放改为真实交互；desktop 列表点击保持在 Spatial selection flow，并显式高亮选中行；
- 新增/强化 Home、Search、Map、Place desktop/mobile contract，专门防止上述语义与视觉回归。

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

## 7.1 已核验外部参考（2026-10-05）

本轮只把外部产品当作交互机制证据，不把它们当作 PetAccess 产品定义：

- Wheelmap FAQ / mapping guide：unknown 是地图一等状态，marker 通过状态语义而不是隐藏 unknown；https://wheelmap.org/faq/
- Apple Human Interface Guidelines — Maps：地图通常应可交互，支持 zoom / pan；自定义 overlay 需要突出时应让底图降饱和；selected place 使用清晰选中态与 place card/sheet；https://developer.apple.com/design/human-interface-guidelines/maps
- Google Maps “Edit business information in Google Maps”：属性允许 Yes / No / Unsure，用户修改进入审核，照片可作为核验材料；https://support.google.com/maps/answer/7084895
- AccessNow：强调具体 accessibility feature、现场照片/评论与透明信息；PetAccess 只吸收“具体事实 + 透明未知 + 低负担贡献”机制，不采用场所评分；https://accessnow.com/

这些参考共同支持本轮恢复方向：**未知可见、事实维度分开、地图可交互、选中态明确、贡献待核验**。

---

## 8. 研究结论

真正需要恢复的不是更多装饰，而是 **产品语义的视觉可见性**：

- Wheelmap 证明 unknown/partial 等状态应成为地图一等信息；
- AccessNow 证明现实空间工具必须让贡献、筛选和透明事实进入主要体验；
- Google Maps 的 edit/review 流证明“不确定 + 待核验 + 证据材料”比伪确认更可信；
- Apple HIG 证明 Search / Maps / Place card 的空间关系应服务任务，不应为了统一模板牺牲平台直觉。

PetAccess 的差异化不在于“也有地图”，而在于 **Rule + Reality + Evidence/Governance + Divergence** 四者在一个现实场所模型里被严格分离又能同时阅读。


## 9. 2026-10-05 官方模式研究补强

本轮进一步只看官方设计系统与官方帮助文档，结论与 Canonical 一致：

1. **Apple HIG / Search fields**：搜索需要让范围清楚、结果尽量简化，并允许必要的 scope/filter；在 split-view 信息工具里，搜索与结果列表相邻、选择项持续可见于详情区域，是成熟桌面信息架构。PetAccess 因此继续维持 Search = Results Pane + Detail Inspector，不把桌面退化成移动卡片流。
   - https://developer.apple.com/design/human-interface-guidelines/search-fields
2. **Apple HIG / Split views**：主列表选择驱动相邻详情，本质上支持 PetAccess 的 Search List–Detail 与 Map Results–Canvas 结构。selection 必须可见，pane 之间用克制 divider，而不是把每一项包成浮卡。
   - https://developer.apple.com/design/human-interface-guidelines/split-views
3. **GOV.UK Summary list**：少量 key facts 应用清晰 row / key-value rhythm，而不是小卡片墙；这强化了 Place Evidence/Settings/Mine 的 divider-led 信息呈现。
   - https://design-system.service.gov.uk/components/summary-list/
4. **GOV.UK Tag**：tag 是状态，不应被伪装成链接/按钮。这支持 PetAccess 将 StatusBadge 仅留给 Rule semantic status，并把筛选/“为什么”/查看依据做成真实 action。
   - https://design-system.service.gov.uk/components/tag/
5. **Google Maps Edit place information**：用户可以补充、纠正或明确“不知道正确值但现值错误”，提交后由平台核验；照片可以帮助验证。这与 PetAccess 的“不确定是合法答案 + Contribution 待核验 + Evidence 不自动升级成 Rule”完全同向。
   - https://support.google.com/maps/answer/7084895

这些参考不改变产品定义，只进一步确认：**Task-first Search、持续 selection、少卡片的事实摘要、status/action 分离、不确定与待核验显式存在** 是正确方向。

## 10. Oracle 数值的解释纪律

机器 Oracle 只允许约束“可测的外形代理”，不得反向扭曲 Canonical：

- Search 仍限制为不超过 5 个**语义组**：Identity / Reality(or Rule lead) / Rule(or Reality secondary) / Key condition / Evidence-freshness；浏览器 rendered-line probe 可能把并排 StatusBadge 或窄屏换行单独计数，因此 desktop 机器上限 6、mobile 上限 7，不代表允许新增信息组。
- Place mobile 第一屏已经按照 Coexistence Passport 恢复 Identity actions + Rule + Reality + Space/Evidence summary；因此旧的 30 rendered-line 上限不再是权威。新上限只用于防止继续膨胀，不允许把 Staff/Facility/History 全量塞回第一屏。
- Map 的状态筛选只属于 Rule Lens；Reality / Facility / Divergence Lens 必须显示完整空间态势，不能为了让旧 filter gate 通过而套用 Rule status filter。



## 11. 2026-10-06：Human Review 证据模型重置

### 11.1 为什么旧 direct-v8 截图不再有效

`artifacts/ui-direct-craft-v8-local-acceptance/HUMAN_REVIEW/` 保留为历史 runtime 证据，但它拍摄的产品状态已被后续 canonical recovery 明确替代：

- Home 当时缺少完整四任务 lens / recommendation / Coexistence Digest；
- Map 当时没有以 Rule / Reality / Facility / Divergence 四 Lens 作为一等视图；
- Place 首屏尚未完整呈现 StaffResponse / AnimalFacility / divergence / 完整 Reality evidence；
- Reality 仍是旧 Observation-only 表达；
- Contribution 的代表图包含未登录门禁，而非真实五入口与 structured flow；
- Evidence 尚未与 v0.9 published Reality event stream 完整对齐。

因此，任何 `UI Direct Validation = green`、旧 Oracle PASS 或上述旧 PNG 都不得再写成
`UI_HUMAN_VISUAL_ACCEPTANCE = PASS`。

### 11.2 当前 authoritative Web 人审包

唯一 canonical capture 定义：

`tests/ui-oracle/human-review-direct-v8.spec.ts`

输出：

`artifacts/ui-direct-v8/HUMAN_REVIEW/{desktop,mobile}/`

规则：

1. 只有真实 DOM 已出现冻结 archetype 的关键状态/内容，才允许保存截图；
2. capture 本身只证明“拍到了正确产品状态”，不证明“视觉已经好看”；
3. manifest 固定标记 `machineValidatedOnly=true`、`humanVisualAcceptance=PENDING`；
4. 最终 PASS 仍由真人检查当前 HEAD 的 Web / Windows / Android 真实画面后给出。

### 11.3 当前必须一起出现的产品事实

人审不能再只看 Rule verdict。核心 surface 必须同时能检查：

- Rule：当前查询、结论、条件、真实 Rule verification freshness；
- Reality：animal presence / staff response / animal facility 三类经核验事实；
- Evidence：Rule 与 Reality 来源/证据并列，Observed / Submitted / Reviewed 时间不混写；
- Map：四 Lens 共用同一批 Place + CoexistenceSnapshot；
- Contribution：Rule lead / Place correction / Reality fact 分不同治理通道，Observation 永不自动成为 Rule；
- Facility：用途确认度、运行状态、使用方式与可用安全属性；Facility 永不推导 EntryPolicy。


## 12. 2026-10-06：Source Fidelity Closure Checkpoint

这一轮不再以“旧截图是否像”作为代码判断依据，而是从 Canonical 不变量反查运行链路。当前 source 已明确做到：

- **Home**：任务入口 → 个性化关注推荐 → Rule / Reality 共处速览；有 Reality 依据但 Rule UNKNOWN 的场所不会被错误藏进“待补充”。
- **Search**：desktop 持续 List–Detail；默认 Reality-first，同时保留 Rule 语义状态、关键条件、Evidence / Freshness；筛选只改变显示。
- **Place**：以 `CoexistenceSnapshot` 为 Rule / Reality 同屏 SSOT；Rule UNKNOWN 不会吞掉 StaffResponse / Facility / Evidence；规则核验日期使用真实 `last_verified_at`，不拿 snapshot 生成时间冒充。
- **Map**：Rule / Reality / Facility / Divergence 四 Lens 共用同一 Place + Snapshot；真实坐标从 PostGIS 投影到 Consumer；生产环境缺坐标时不伪造 marker；配置可用时走 TencentMap，provider 不可用才明确降级到简化空间底图。
- **Reality**：Consumer timeline 读取经人工核验的 v0.9 published events（presence / staff response / facility）；Staff role 可展示、个人身份不采集；staff statement 仍只是具体事件事实，不能升级成 OperatorPolicy。
- **Facility**：用途确认度、运行状态、使用方式、容量与可核验的遮雨 / 遮阳 / 通风 / 饮水 / 看护 / 安全属性进入 Space dossier；任何设施属性都不得推导 EntryPolicy 或安全保证。
- **Evidence**：Rule evidence 与完整 Reality layer provenance 并列；Observed / Submitted / Reviewed 时间保持不同字段，外部内容只有发布时间时不得伪装成现场发生时间。
- **Contribution**：Rule confirmation / changed-rule lead / new-rule lead / signage evidence、Reality facts、Place correction 各走自己的治理通道；Rule lead 不写 Observation；“不知道正确值”是合法纠错输入；所有结果先进入 review。
- **Secondary surfaces**：Mine / Notifications 将 Rule watch 与 Reality watch 分开；Privacy 对尚未实现的服务端账号删除/导出流程明确写不可用，不用本地按钮伪装已提交。
- **Dispute / correction**：Published Reality fact 的异议不删除事实、不修改 Rule；Evidence 与 timeline 显示“异议处理中”，presence 异议会把 Reality summary 降级为 DISPUTED，StaffResponse / Facility 的 open dispute count 继续投影到 Place Overview / Space / Map Facility Lens，避免把有争议事实伪装成干净摘要。

### 12.1 Human-review runner 纪律

`tests/ui-oracle/human-review-direct-v8.spec.ts` 的每一个 shot 都必须从新 Document 启动。原因不是视觉偏好，而是同一个 Contribution hash route 会承载多个独立状态；若只做 hash 导航，前一 shot 的 step state 会污染后一 shot。Capture URL 的 outer query 只用于强制重新 bootstrap，真实 hash route 不变。

`UI Direct Autofmt` 现在同时格式化 `packages/client-core/src/api/client.ts`。Shared client 是 Consumer UI 的实际类型/调用边界，不能再出现“app 目录已经 prettier，但共享 client 让全仓 format gate 失败”的假红。

### 12.2 当前停止线

Source / contract / capture runner 完成不等于 Human Visual PASS。最终仍必须对**同一最终 HEAD**重新取得：

1. Web authoritative HUMAN_REVIEW desktop + mobile；
2. Windows Tauri / WebView2 当前 HEAD；
3. Android AVD 当前 HEAD；
4. 配置真实地图 provider 时，至少一张 real-map runtime 证据；若环境没有 provider key，必须把“简化空间底图”明确记录为外部配置 blocker，而不是假装真实地图已验收。

在上述证据由真人看过以前，`UI_HUMAN_VISUAL_ACCEPTANCE` 保持 `REJECTED_REOPENED / PENDING_REVIEW`，PR #1 保持 draft，master / tag / Release 不动。
