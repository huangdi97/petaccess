# UI Human Closure V5 — Human Visual Closure / Interaction & Brand Polish（规格与方法）

> 实现基准：`IMPLEMENTATION_BASE` = v5 代码与测试完成后的实现 commit（分支历史内可查，见
> `feat/ui-human-closure-v5`；本文不自我引用最终 HEAD，最终 HEAD 以 Git 查询为准）。
> 分支基点 = v4 head `e5a9949`；`origin/master` = `842c030` 未动。

## 1. 目标与边界

本轮（v0.2.5）把 v0.2.4 已经「结构正确、产品化基本成立」的 UI 推进到
**视觉一致、交互完整、没有明显工程痕迹、可进入最终 Human Visual Acceptance 的候选版本**。

- 全程不运行视觉模型 / OCR / 截图理解；Agent 不判断「好不好看」；
  所有视觉判断只来自规格中已文字化的人工审阅结论（§1–61）。
- 继承 v0.2.3/v0.2.4 成果：不重做信息架构、不重写 Oracle、不扩产品范围、禁止先做新功能。
- 冻结项不重做（除非真实 bug）：IA、Rule/Reality/Evidence 分离、CoexistenceSnapshot SSOT、
  Query Context、68px rail、mobile bottom nav、Search List–Detail、Place Dossier with Views、
  Map List+Spatial、Reality Event Log、Evidence Provenance、Contribution structured flow、
  O1–O6、Capture State Integrity、Consumer Language Scanner。

## 2. 优先级与交付内容

### P0 — Place 最后收口（§8–16）
- Overview 无孤立 `>`；consumer copy 无工程不变量（`≠`/UNKNOWN/ALLOWED/PROHIBITED/CONDITIONAL/
  source_id/rule_id/zone_type 用户可见 DOM 全部清零）。
- Unknown Overview 最小化：只含 Identity/Tabs/Current Query/Information Insufficient/Known
  Facts/Contribute Actions；自然语言 copy「目前没有足够可靠信息，无法确认是否允许进入」。
- Rules View 从重复行重组为 **Rule Groups**（contextLabel + subjectAction + status +
  condition/exception/source 至少一项；组间 divider + 20–24 gap；非 card wall；grouping 由真实
  domain data 决定，不伪造 zone/context；冲突 inline「△ 来源不一致 · 查看差异 →」）。
- Mobile Overview 补 Space/Evidence summary row（56–64px，不展开），解决「Decision+Reality
  后大片空白」。
- Inspector v5：300–320 宽、全左对齐、无卡片；顶部不再重复 Place Name/地址；search CTA
  「查看完整场所 →」；右侧 onboarding 去重复 CTA。

### P0 — Map Mobile Bottom Sheet（§22–26）
- 真实 overlay：`position: fixed` overlay 内 absolute sheet，bottom = tabbar + safe area
  （不与 tabbar 重叠）；白色 surface、top radius 16、drag handle、elevation、touch scroll。
- 三态：closed peek（56–64px）/ half（~280–340px，top < 700）/ expanded（max 70–78vh）。
- Half 内容 = handle + Place name + Status + Type·distance + Key condition + 最近现场 +
  查看场所 →；无全宽 outline status 条、无「返回地图」button、close 右上 icon。
- 地图填满 tabbar 上方视口；地图|列表 compact segmented control；selected marker 1.3x + halo；
  MockMap 抽象城市纹理，不伪造真实街道/坐标/第三方图层名。

### P0 — Contribution Step Flow（§28–34）
- ContributionStepShell：place context + 3-segment progress + title + description + question
  body + footer（back=1 / primary=1）+ privacy link；max 640 / min-height 440–520。
- Step-1 选项 = radio/checkbox **option rows**（非 pill），行高 min 52–60px，每行说明。
- Step-2 reality 按真实字段 cluster（什么时候/在哪里/你看到了什么/工作人员/证据），无 admin form。
- Done =「已提交待核验 · 感谢提供事实记录…查看我的贡献 →/返回场所 →」，不误写为规则已变更。
- privacy copy 恢复「提交内容会进入人工核验」（v5 shell 曾丢失，属真实 bug 修复）。

### P1 — Search / Home / Reality / Evidence 打磨（§17–21、§35–36）
- Search：selected tint 轻（`surface-warm`→`accent-weak`）、status 不抢 Place Name；Empty 仅左侧
  一个 primary「提交场所线索」；mobile toolbar「结果 N | 筛选」非独立大按钮；row ≤4 semantic lines。
- Home：`附近已核验`→`附近已有依据`、`规则待核实`→`附近待补充`；nearby row 不重复「已核验：
  普通犬 · 场所整体」。
- Reality：Date=metadata、Time=strong（tabular-nums）、Zone=subsection、Fact=body strong、
  Review state=小号 muted（待核验用 small muted + clock icon，不用强 badge）。
- Evidence：record identity 更强；`2 条现场记录 · 8 个来源 · 3 个待核验` 层级明确（compact
  inline stats）；provenance pending 用 empty-circle + muted label（不用 warning 黄）。

### P2 — 全局一致性与 bad-weather（§7、§37–41、§52）
- bg 中性浅色不偏黄；amber 仅 conditional、red 仅 restriction、blue = nav/links/primary；
  radius = controls 8 / sheet·modal 14–16 / map preview 12 / decision surface 10–12 / list row 0；
  shadow 仅 sheet、map preview、dialog、floating overlay。
- Top Context Bar h60 + ellipsis；Desktop rail 68px active 为 subtle blue tint；Mobile bottom nav
  safe area / z-index 不重叠。
- Motion：hover/focus 120–160ms、sheet 180–240ms、selected marker 120ms、route 无动画；
  `prefers-reduced-motion` 全部降级（styles.css 全局）。
- Bad-weather states inline、保留 context/navigation、retry 清楚（既有实现保持）。

## 3. Oracle 变更（§46，最多 8 个 FAIL 级 gate）

| Gate | 作用 |
| --- | --- |
| PLACE_NO_STRAY_GLYPH | 禁止只含 `>`/`<`/`:::`/`——` 的异常可见文本 |
| PLACE_NO_ENGINEERING_INVARIANT_COPY | 禁止 `≠`/UNKNOWN/ALLOWED/PROHIBITED/CONDITIONAL/source_id/rule_id/zone_type |
| PLACE_RULE_GROUP_HAS_CONTEXT | Rules View 至少 1 个带回文章节的 rule group |
| PLACE_MOBILE_OVERVIEW_SUMMARY_PRESENT | mobile overview 首屏含 Space/Evidence summary row（≥2） |
| MAP_MOBILE_SHEET_OVERLAY | sheet 为真实 overlay（position absolute 于 fixed overlay、radius 14–18） |
| MAP_MOBILE_SHEET_ABOVE_TABBAR | half 态 top 300–700 / height 180–360（不与 tabbar 重叠） |
| CONTRIBUTION_STEP_CONTEXT_PRESENT | step-1 含 place context + progress + primary + back（≥4） |
| CONTRIBUTION_OPTION_ROWS_NOT_PILLS | quick-options ≥3 个 option-row，禁 pill class |

- 新增契约 `docs/ui/contracts/json/map.mobile.json`（430×932，map-mobile-ready /
  map-mobile-selected-half `?place=8412b521…`）。
- 既有契约仅做与已批准 §15/§10/§11 一致的作用域/阈值对齐（decision/density/section-gap 规则
  只在有相应内容块的真实页面执行；inspector x、mobile first-viewport budget 按新布局重校准），
  不弱化任何断言；WARN 不放过。
- O1–O6 / Capture State Integrity / Consumer Language Scanner 全部保留。

## 4. 本轮修复的真实 bug（非视觉）

- Contribution 隐私 copy「提交内容会进入人工核验」在 shell 化时丢失 → 恢复（shell + entry）。
- Reality 提交错误只写 `error` 不渲染（silent failure）→ 恢复 `reality-error` alert（v4 有）。
- 客户端幂等键 `Date.now()`+模块计数 → 多标签同毫秒冲突触发服务端 409 → 改 `crypto.randomUUID()`。
- e2e/reconstruction 并行下 hash goto 被 SPA boot 覆盖 → 测试改为确定性 token 注入
  （addInitScript + 单次 full-page goto）。

## 5. 文档与状态

- 文档：本文（`docs/ui/UI_HUMAN_CLOSURE_V5.md`）+ 报告/清单
  （`docs/reports/UI_HUMAN_CLOSURE_V5_REPORT.md`、`docs/reports/UI_HUMAN_CLOSURE_V5_MANIFEST.md`）。
- PROJECT_STATE 顶层：`UI_HUMAN_CLOSURE_V5 = MACHINE_PASS`、七页 `*_CANDIDATE =
  READY_FOR_HUMAN`、`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING`、`UI_VISUAL_CLOSURE =
  PENDING_HUMAN`、`VISUAL_BASELINE_PROMOTED = NO`、`MASTER_MERGED = NO`。
- 人审包：`artifacts/ui-human-closure-v5/HUMAN_REVIEW/`（27 张 + INDEX + metadata）。
