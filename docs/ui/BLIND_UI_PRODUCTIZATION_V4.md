# Blind UI Productization v4 — 产品化收口方法与结果

> 文档定位：v0.2.4 Human Visual Recovery / Productization Closure 的方法与实施记录。
> 实现基准：`IMPLEMENTATION_BASE = e1c5ca7`（完成代码与测试后的实现 commit）。
> 分支最终 HEAD 以 Git 查询为准（feature branch pushed；不在此文档内自引用“本文档 commit 为最终 HEAD”）。

## 1. 目标

把 7 个消费者页面（Search / Place / Home / Map / Reality / Evidence / Contribution）从“工程正确”
推进到“产品完成”，产出可提交给真实人眼评审的证据包，并停在 `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING`。

本轮全程不运行任何视觉模型 / 图片理解 API；Agent 不评价截图；只依据规格文档中的文字化人工反馈
（§1–64）与可执行 UI contract 改代码。

## 2. 执行方式

- 分支：`feat/blind-ui-productization-v4`，基点 `feat/blind-ui-compiler-v2 @ 90d57e6`（先行 28 / 落后 0）。
- 只在本工作区 `E:\AI\宠物管理` 内改动；未 merge / 未 fast-forward master；未动 `v0.1.0` tag；
  无 force push、无历史改写；未更新 `tests/visual/**-snapshots/*.png`。
- Oracle 仅做最小修正：阈值修正、新增当前反馈所需少量 contract、删除 false-positive tolerance；
  O1–O6 六层保留，未做大范围 Oracle 重写。

## 3. 页面实施摘要

### Search（§11–14）
- 删除顶部 duplicate status badge；右侧结构严格按 §12：Place Identity → Current Query →
  Primary Decision(status + key condition) → Reality(one-line) → Evidence/Source → CTA。
- content width 620–680（不 >704）；首屏内容高 420–560px。
- Result pane = Search input + button + toolbar(结果 N | 筛选)；行高 desktop 92–108px / mobile 88–104px，
  最多 4 条 semantic lines。
- lens projection 修正：rules → decision 为标题行；presence → reality 为标题行（修复 WIP 阶段
  presence lens 把 decision 放进 `row-lens-headline` 的问题），indoor/dining 不再把 zone facts
  铺在行上；reality 行在 presence/indoor/dining lens 下不重复渲染。

### Place Dossier（§15–28）
- 不再一次渲染 3000px+ 长文档：Dossier 顶部本地 section 导航（概览/空间/规则/现场/证据，
  text tab + underline；mobile 横滑），每个 view 只渲染自己的 pane。
- 支持 `?view=overview|space|rules|reality|evidence` deep link / back-forward / refresh。
- Overview 五块：Identity / Current Decision / Recent Reality / Space Summary / Evidence·Source
  Summary；其余进各自 view。Rules/Evidence view progressive disclosure（历史版本折叠）。
- 长度门：desktop 全页 `<=1500`、mobile `<=2000`（实测 desktop 1181.25px / mobile 465.25px，PASS）。
- mobile 首屏 `firstViewportVisibleTextLines <= 22`（>24 FAIL，不再 WARN；实测 22，PASS）。
- section gap 24–36 target / 绝对 max 40（实测 24，PASS）。
- 去重：同一 screen Primary decision 完整表达 <=2 处；移除“普通宠物（基线）”第二结论块；
  Place Unknown 只渲染有数据的部分。
- 模式切换修复：PlaceView 恢复 `watch([session.mode, session.activePet]) → evaluate()`，
  普通携带 ↔ 服务犬通行切换后结论重新求值（e2e mode-switch 回归通过）。

### Home（§29–31）
- desktop main max 960px；结构 = location+map link / headline / search / 最近附近 divider rows /
  待核实 divider rows / quick lenses(4 links)；无大白 card、无 pending card rows、无“为什么？” pill。

### Map（§32–33）
- desktop 无“地图/列表”顶部 pill（恒为 List+Map）；mobile 保留 compact toggle。
- results 为 divider rows（非 rounded card）；selected preview 只显示 5 项内容
  （Place / Type·distance / Primary status+key condition / 最近现场 / 查看场所 →）。
- selected marker 放大 1.2–1.4x + halo。

### Reality（§34–36）
- Timeline-First：页顶只允许 title + 一句说明 + 筛选行；summary 收为一行 metadata
  （N 条记录 · 最近 DATE · M 条待核验）。
- 复用共享 RealityEventLog 组件；空态 inline（暂无近期现场记录 + 不代表现场没有动物）。

### Evidence（§37–40）
- 解析 Place name / Zone / Observed time（fetch `client.place` + `client.zones`），无“场所信息暂不可用”。
- record identity 头 + 每维度计数；EvidenceProvenance 5 步 rail（filled/pending）；
  记录存在时标题不显示“0 条依据”。

### Contribution（§41–43）
- ContributeEntry 5 个 choice row（icon+title+one-line description+chevron，64–72px）；
  §42 隐私文案降权为“隐私与审核说明 →”；步骤指示器修正为真实 3 步
  （legacy 表单 = 步骤 1 / 3，reality 父流程 = 步骤 2 / 3；修复 WIP 阶段现实
  步骤显示 5 / 3 的问题）。

### Global Visual Language v4（§9/§45）
- app bg 中性暖白/浅灰（`#F8F8F7` 系），surface 白；语义色占比 <=10%；
  全局 surface 收口：普通 section/row/divider，card 仅限 §10 允许清单。

## 4. 结果

- ui-oracle compare（final）：**TOTAL PASS=368 WARN=0 FAIL=0**（10 契约，原 3 个 WARN 升级项
  PLACE_HISTORY_COLLAPSED_MOBILE / PLACE_SECTION_GAP / PLACE_MOBILE_FIRST_VIEWPORT_LINES 按新阈值执行）。
- language scan（final）：26 页 FAIL=0。
- Human Review Pack v4：24 张 curated 截图全部 VALID（见 HUMAN_REVIEW_MANIFEST）。
- 完整机器套件全 PASS（vue-tsc / client-h5 build / admin build / eslint 0 / prettier /
  ui-oracle / language / state integrity(O6) / responsive 1440×900+430×932 / a11y /
  完整 e2e 189 / 完整 backend pytest 961 passed / 2 skipped）。

## 5. 下一步（人工视觉收口）

`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING`：请人工打开
`artifacts/blind-ui-productization-v4/HUMAN_REVIEW/HUMAN_REVIEW_INDEX.html` 目视评审；
人审 PASS 后才允许视觉 baseline 提升与 master 集成。
