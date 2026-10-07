## Current phase（2026-10-07 — direct-v8 Canonical Fidelity + Dispute Closure）

- 分支：`feat/ui-direct-craft-v8`；PR #1 保持 **draft**；base = `feat/ui-product-craft-v7-human-review-final`；master / tag / Release 不动。
- `UI_HUMAN_VISUAL_ACCEPTANCE = REJECTED_REOPENED / PENDING_REVIEW` 继续有效。机器 Gate、DOM contract、旧 screenshot 均不得替代用户对当前最终 runtime 的真人视觉验收。
- 本轮继续按 Canonical Master §61 / §65–§72 与 `UI_RECONSTRUCTION_DESIGN_FREEZE.md` 反查 source，而不是为了旧 Oracle 数字删设计。
- 已关闭的高价值语义缺口：Home 中性推荐标题恢复为“近期值得先看”；Published Reality dispute 在 Evidence / Event Log / Reality summary 中可见；StaffResponse / AnimalFacility 的 open dispute count 进入 Place Overview / Space / Map Facility Lens，异议不会删除事实、不会修改 Rule。
- Consumer 仍严格保持：Rule != Reality；Observation != Rule；StaffResponse != OperatorPolicy；Facility != EntryPolicy；No Observation != No Animal Presence；Access != Friendly。
- 当前唯一剩余 UI 停止线不是“再做一个版本”，而是：**对同一最终 HEAD 重新生成 authoritative Web HUMAN_REVIEW desktop+mobile，并由本地 Agent 对 Windows WebView2 / Android AVD 当前 HEAD 重新取证；配置真实地图 provider 时补 real-map 证据，否则明确 BLOCKED_EXTERNAL。**
- 在上述真人视觉验收完成前：禁止 baseline promotion、禁止 master 集成、禁止 tag / Release、禁止把 PR 转 ready。

## Current phase（2026-10-06 — direct-v8 Canonical Visual Recovery）

- 分支：`feat/ui-direct-craft-v8`；PR #1 保持 **draft**；`master` / tag / Release 不动。
- `UI_HUMAN_VISUAL_ACCEPTANCE = REJECTED_REOPENED` 继续有效：旧机器 Gate/旧 screenshot pack 不能替代真人视觉验收。
- **旧包已降级为历史证据**：`artifacts/ui-direct-craft-v8-local-acceptance/HUMAN_REVIEW/` 对应的是此前 UI/Reality/Map/Contribution 状态，已不能作为当前 direct-v8 的视觉验收依据。
- **新的唯一 Web 人审入口**：`tests/ui-oracle/human-review-direct-v8.spec.ts` → `artifacts/ui-direct-v8/HUMAN_REVIEW/{desktop,mobile}/`。每张 PNG 只有在对应 frozen archetype 的真实 DOM 状态/关键内容存在后才允许写出；manifest 明确标记 `humanVisualAcceptance=PENDING`。
- 新人审包强制覆盖：Home 四任务入口与 Coexistence Digest；Search List–Detail；Place Rule/Reality/Staff/Facility/Evidence；Map 四 Lens；v0.9 Reality event log；Evidence provenance；登录后的 Contribution 五入口/Rule lead/Place correction/Reality flow；Mine/Settings/Privacy/Notifications/Pets/Boundary/Why/About/Onboarding/404。
- 当前继续做的是 **canonical fidelity + semantic integrity**，不是新增 IA：Home/Search/Map/Place 的 Reality headline 已统一到完整 CoexistenceSnapshot（Presence + StaffResponse + Facility），Evidence 元数据也统一统计完整 Reality layer。
- 停止线不变：新 Web 人审包 + Windows WebView2 + Android AVD 对当前最终 HEAD 重新取证并由用户真人审图前，禁止 baseline promotion、禁止 master 集成、禁止 tag、禁止 Release、禁止把 PR 转 ready。


# PROJECT_STATE.md

## Current phase（2026-10-05 — Canonical Visual Recovery implementation complete / CI pending）

- 状态：`DIRECT_V8_CANONICAL_VISUAL_RECOVERY = CODE_COMPLETE` · `MACHINE_ACCEPTANCE = PENDING` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = REJECTED_REOPENED` · `PR #1 = DRAFT` ·
  `MASTER = UNCHANGED` · `PUBLIC_RELEASE = NOT_PERFORMED`。
- 权威恢复冻结：`docs/ui/DIRECT_V8_CANONICAL_VISUAL_RECOVERY_2026-10-05.md`。
  Canonical Master v0.10-R1 决定产品内容；Executable Blueprint 只负责可测几何，不再允许旧 Gate
  删除 Home recommendations/divergence、Map 四 Lens 或 Place Coexistence Passport 首屏事实。
- 本轮 GitHub 实施：Home 恢复四任务 Lens → 按关注推荐 → Rule/Reality 速览 → divergence → recent；
  Search 每行恢复 Rule + Reality + Evidence/Freshness；Map 恢复 Rule / Reality / Facility /
  Divergence 四 Lens 且全部投影同一 CoexistenceSnapshot；Place 首屏恢复 Rule + Reality +
  Staff Response + Animal Facility + Divergence，以及 Evidence / Why / Correction actions。
- 数据边界：`RowFacts` 仅保留服务端 `CoexistenceSnapshot` 作为 Consumer projection SSOT；
  UI 不新增第二 Rule/Reality resolver，不把 Reality / Facility tone 解释为 access verdict。
- 工程收口：已修复上一轮 CI 暴露的 RowFacts fallback type gap；Home digest 与 Map lens projection
  已拆分，避免新增 `vue>200` / `ts>300` quality-gate FAIL；Oracle JSON 已同步 Canonical。
- 停止线：等待本 HEAD 的 PR CI / UI Direct Validation / UI Direct Visual 真实结果。
  即使机器全绿，也只进入 `HUMAN_REVIEW_READY`；在真实 Web / Windows / Android 截图人工确认前，
  禁止 baseline promotion、禁止 master 集成、禁止 tag / Release。


## Current phase（2026-10-05 — direct-v8 Human Visual Reopen）

- 分支：`feat/ui-direct-craft-v8`；PR #1 保持 **draft**；`master` / tag / Release 不动。
- 人工视觉结论：`UI_HUMAN_VISUAL_ACCEPTANCE = REJECTED_REOPENED`。用户在真实本地运行软件中确认：整体产品观感与冻结设计存在明显偏差。
- 机器状态不等于视觉通过：`UI Direct Validation` / `UI Direct Visual` 与 Oracle 全绿仅证明已编码的结构、几何、语言和状态契约通过，**不得再据此写作 Human Visual PASS / UI COMPLETE**。
- 当前唯一 UI 主线：`DIRECT_V8_VISUAL_FIDELITY_RECOVERY = IN_PROGRESS`。依据顺序：Canonical Master → `UI_RECONSTRUCTION_DESIGN_FREEZE.md` → `UI_HUMAN_CLOSURE_V5.md` / 已批准参考 → 当前真实 runtime screenshot → 当前 source。
- 冻结不变量继续有效：Rule / Reality / Evidence-Governance 分离；Observation != Rule；StaffResponse != OperatorPolicy；Facility != EntryPolicy；No Observation != No Animal Presence；Access != Friendly。
- 冻结 archetype 不重做：Home=Task Launcher；Search=List–Detail；Place=Dossier；Map=Spatial Workspace；Reality=Event Log；Evidence=Provenance Record；Contribution=Structured Transaction Flow。
- 停止线：在新的真实 Web / Windows / Android 人工截图明确通过之前，**禁止 baseline promotion、禁止 master 集成、禁止 tag、禁止 Release、禁止把 PR 转 ready**。

### 为什么重开

direct-v8 在若干页面达到了机器契约，但出现了「结构正确、产品视觉不对」的问题：语义状态层级被削弱、Rule/Reality 共处信息没有在首屏形成足够强的产品识别、部分核心 surface 过度稀疏并呈现 prototype / functional-page 感。当前工作是恢复设计 fidelity，不是再发明 IA 或换 Design System。

## Current phase（2026-10-03 本轮实测 — v0.2.7-R1.1.1 Human Review Truth Closure）
- 状态：`V0207_R1_1_1_HUMAN_REVIEW_TRUTH_CLOSURE = MACHINE_PASS` · `HUMAN_REVIEW_PACK = COMPLETE` ·
  `HUMAN_REVIEW_CARDS = 7/7` · `HUMAN_REVIEW_PNGS = 7/7` · `HUMAN_REVIEW_IMG_REFS = 9/9` ·
  `HUMAN_REVIEW_INDEX_REFERENTIAL_INTEGRITY = PASS` · `HUMAN_REVIEW_INDEX_EXACT_SET = PASS` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` · `MASTER = UNCHANGED` · `PUBLIC_RELEASE = NOT_PERFORMED`
- 分支：`feat/ui-product-craft-v7-human-review-final`（基点 = origin/feat/ui-product-craft-v7-runtime-final `a83f64f`；
  已 push；BASE_HEAD `42ed4e3` / V7_HEAD `346abbd` / R1_IMPLEMENTATION_HEAD `f8c1227` /
  R1_1_CODE_HEAD `2010775` / R1_1_EVIDENCE_HEAD `647ecd5` / R1_1_DOCS_HEAD `a83f64f`；
  FINAL_BRANCH_HEAD 以最终验证时刻 `git rev-parse HEAD` / `git rev-parse origin/feat/ui-product-craft-v7-human-review-final`
  实测为准（避免自引用死锁）；origin/master 未动；v0.1.0 tag 未动；无 v0.2.0 tag / Release / store）。
- 内容：P0-3 单一最终 writer 修复——`tests/ui-oracle/human-review-r1.spec.ts` 非 oracle-desktop project
  在 pack 组装前 early return，只有 `oracle-desktop` 允许 assemble + 写最终 Index + 跑完结 gates
  （ONE FINAL WRITER，deterministic）；P0-1/P0-2 显式 `HUMAN_REVIEW_EXPECTED_CARD_SET`（固定顺序 7 个）+ exact-set /
  数量(7) / img-ref(9) / orphan / missing / `.png.png` 门禁全部 assert 化。
- 人审包：`artifacts/ui-product-craft-v7-runtime-final/HUMAN_REVIEW/`（目录不变，无 v8/v9 噪音）重新生成：
  **7 cards、7 PNG、9 `<img src>`、0 missing、0 orphan、0 `.png.png`**，Index 标题 `7 VALID / 7 total`；
  01–05 = windows-smoke 真实 WebView2 证据逐字节复制（SHA256 一致），06/07 = generator 自然重截
  （state integrity page/state/fixture/h1 全 PASS，`valid=true` 全部来自真实 DOM，零伪造）。
- 机器 Gate（本轮实测）：prettier --check（spec）exit 0；eslint（spec）0 issues；
  human-review-r1 spec（两个 project，`--workers=1`）**2 passed / 0 failed**
  （desktop：7 shots、7 VALID、0 INVALID；mobile：skip assembly 日志 + 不再写 Index）。
- 复用（未重跑，产品代码零改动，`apps/` 0 变更）：ui-oracle 427/0/0、ui-reconstruction 180/180、
  e2e 189/189、visual 59/59（均来自 R1.1）；`WINDOWS_RUNTIME_RERUN = NOT_REQUIRED`（R1.1 targeted 5/5），
  `ANDROID_RERUN = NOT_REQUIRED`，`FULL_PRODUCT_REGRESSION_RERUN = NOT_REQUIRED`，`BACKEND_CODE_CHANGED = NO`。
- 停止线：exact-set 全绿 + Git truth PASS + HUMAN_REVIEW READY，**等待用户人工视觉签字**
  （Agent 不代替 `UI_HUMAN_VISUAL_ACCEPTANCE = PASS`）；签字并授权后才执行 Stage B：
  force recapture 批准快照 → canonical baseline = 批准外观 → visual compare ×2 → docs truth →
  verify master ancestor → fast-forward master（仅 FF，无 force/merge/rebase）。

### 历史记录 — v0.2.7-R1.1 Final Micro Closure（2026-10-03，HISTORICAL）

## Current phase（2026-10-03 本轮实测 — v0.2.7-R1.1 Final Micro Closure）
- 状态：`V0207_R1_1_MICRO_CLOSURE = MACHINE_PASS` · `HUMAN_REVIEW = READY` ·
  `WINDOWS_RAIL_OVERFLOW = PASS` · `WINDOWS_RAIL_TOOLTIP = PASS` ·
  `WINDOWS_RAIL_FOOTER = PASS` · `HUMAN_REVIEW_INDEX = PASS` ·
  `WINDOWS_CONTRIBUTION_COMPOSITION = PASS` · `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` ·
  `MASTER = UNCHANGED` · `PUBLIC_RELEASE = NOT_PERFORMED`
- 分支：`feat/ui-product-craft-v7-runtime-final`（基点 = origin/feat/ui-product-craft-v7-runtime-closure `7d4772e`；
  BASE_HEAD `42ed4e3` / V7_HEAD `346abbd` / R1_IMPLEMENTATION_HEAD `f8c1227`；
  最终 HEAD 见 `docs/reports/V0207_R1_1_FINAL_MICRO_CLOSURE_REPORT.md` GIT_TRUTH，以 `git rev-parse HEAD` 实测为准；
  origin/master 未动；v0.1.0 tag 未动；无 v0.2.0 tag / Release / store）。
- 内容：P0-1 Human Review Index `.png.png` 修复（生成器 logicalName 模型 + beforePairs 修正 +
  referential-integrity gate：全部 `<img src>` 必须 resolve，`expect(missingImages).toHaveLength(0)`）；
  P0-2 DesktopRail 移除被 overflow-x:hidden 裁掉的自定义 tooltip（span/CSS/rail-tip-in 动画），
  6 个导航 RouterLink 改 `aria-label` + 原生 `:title`，rail 横向 overflow 硬 Gate 保持（scrollWidth ≤ clientWidth + 1）；
  P0-3 rail footer 可见文本改 compact version only = `v0.2`，完整版本/环境保留于 title/data-attribute；
  P0-4 Git/Docs truth：FINAL_BRANCH_HEAD 与 ahead/behind 全部按重新 fetch/rev-list 实测重写。
- 机器 Gate（本轮实测）：prettier PASS、eslint 0、client-h5 vue-tsc+build PASS、admin build PASS；
  ui-oracle **427/0/0**；ui-reconstruction **180/180**；e2e **189/189**；
  visual regression **59/59**（Stage A 不更新 snapshot）；backend `BACKEND_CODE_CHANGED = NO`
  （`git diff origin/feat/ui-product-craft-v7-runtime-closure...HEAD -- services/` 为空）→
  `BACKEND_FULL_RERUN = NOT_REQUIRED`；Android（未改 Contribution layout）`ANDROID_RERUN = NOT_REQUIRED`。
- 真实 Windows runtime（Tauri v2 + WebView2，CDP :9223，沿用 `D:\pa-fix-target-win\debug\petaccess.exe`，
  1120×760）：targeted 5/5 PASS（Map / Contribution choose / step1 / step2 / Rail closeup）——
  rail 67/67 无横向滚动条、Contribution 三页 layoutMode=wide + sameRow=true、
  footer 可见 `v0.2`、6 项 title+aria-label 原生 tooltip 齐备、document 无横向溢出。
- 人审包：`artifacts/ui-product-craft-v7-runtime-final/HUMAN_REVIEW/` 7 张
  （01–05 真实 WebView2 targeted refresh + 06 web 1440 WIDE + 07 web 1000 COMPACT）+ BEFORE/AFTER
  （Map / Contribution）+ HUMAN_REVIEW_INDEX.html；
  `HUMAN_REVIEW_INDEX_REFERENTIAL_INTEGRITY = PASS`（7/7、0 `.png.png`）。
- 停止线：机器 gate 全绿 + HUMAN_REVIEW READY，**等待用户人工视觉签字**
  （Agent 不代替 `UI_HUMAN_VISUAL_ACCEPTANCE = PASS`）；签字并授权后才执行
  canonical baseline promotion → fast-forward master（仅 FF，无 force/merge/rebase）。

### 历史记录 — v0.2.7-R1 Final Runtime Closure（2026-10-03，HISTORICAL）

## Current phase（2026-10-03 本轮实测 — v0.2.7-R1 Final Runtime Craft Closure）
- 状态：`V0207_R1_RUNTIME_CLOSURE = MACHINE_PASS` · `WINDOWS_RAIL_OVERFLOW = PASS` ·
  `WINDOWS_CONTRIBUTION_COMPOSITION = PASS` · `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` ·
  `PRODUCT_STRUCTURE = FROZEN` · `MASTER = UNCHANGED` · `PUBLIC_RELEASE = NOT_PERFORMED`
- 分支：`feat/ui-product-craft-v7-runtime-closure`（基点 = origin/feat/ui-product-craft-v7
  `346abbd`，R1_HEAD = `f8c1227`；origin/master 未动；v0.1.0 tag 未动；无 v0.2.0 tag / Release / store）。
- 内容：P0-1 DesktopRail 横向 scrollbar 修复（footer ellipsis + 隐藏 tooltip display:none +
  overflow-x hidden；rail.scrollWidth 104→67）；P0-2 Contribution 双栏 breakpoint 契约
  （COMPACT 768–1119 / WIDE ≥1120，默认窗口 width 1000→1120，默认 Windows runtime 真并排）；
  新增 DESKTOP_RAIL_NO_HORIZONTAL_OVERFLOW + nested contribution gates（oracle 427/0/0）。
- 机器 Gate（本轮实测）：vue-tsc / h5 build / admin build / eslint 0 / prettier PASS；
  ui-oracle **427/0/0**；ui-language 29 FAIL=0；ui-density 28 FAIL=0；
  ui-reconstruction **180/180**；e2e **189/189**；visual regression **59/59**（Stage A 不更新 snapshot）；
  backend `BACKEND_CODE_CHANGED = NO`（git diff 无 services 变更）→ `BACKEND_FULL_RERUN = NOT_REQUIRED`。
- 真实 Windows runtime（Tauri v2 + WebView2，CDP :9223）：9 路由 smoke 全 PASS
  （rail 67/68 无横向滚动条；contribution choose/step1/step2 layoutMode=wide；
  完整 metrics 见 `artifacts/ui-product-craft-v7-runtime-closure/windows-runtime-metrics.json`）。
- Android：贡献 targeted smoke（choose + step1，emulator-5554 / AVD main）PASS + 无 overflow；
  浏览器 responsive 360/390/430 无 Contribution regression（reconstruction/e2e 覆盖）。
- 人审包：`artifacts/ui-product-craft-v7-runtime-closure/HUMAN_REVIEW/` 7 张
  （01–05 真实 WebView2 + 06 web 1440 WIDE + 07 web compact）+ BEFORE/AFTER（Map / Contribution）
  + HUMAN_REVIEW_INDEX.html；metadata actual 全部来自真实 DOM。
- 停止线：机器 gate 全绿 + HUMAN_REVIEW READY，**等待用户人工视觉签字**
  （Agent 不代替 `UI_HUMAN_VISUAL_ACCEPTANCE = PASS`）；签字并授权后才做
  canonical baseline promotion → `git push origin HEAD:master`（仅 fast-forward）。

### 历史记录 — v0.2.7 Product Craft（2026-10-03，HISTORICAL）


## Current phase（2026-10-03 本轮实测 — v0.2.7 Final Product Craft / Spatial Map / Desktop Composition Closure）
- 状态：`V0207_PRODUCT_CRAFT = MACHINE_PASS` · `PRODUCT_STRUCTURE = FROZEN` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` · `V020_RC_READY = PRESERVED` ·
  `PUBLIC_RELEASE = NOT_PERFORMED`
- 分支：`feat/ui-product-craft-v7`（基点 = origin/master `42ed4e34`，已 push；
  origin/master 未动；v0.1.0 tag 未动；无 v0.2.0 tag / Release / store）。
- 内容：Map Spatial Craft（抽象城市画布 + marker 系统 + selected scale/halo）、
  Contribution Desktop 双栏 composition（main 680 + context 280）、
  Reality/Evidence/Search 阅读节奏收口、§40 十个 craft gates 全绿。
- 机器 Gate（本轮实测）：vue-tsc / h5 build / admin build / eslint 0 / prettier PASS；
  ui-oracle **423/0/0**（398 → +25，WHY_TEST_COUNT_CHANGED=新增 craft gates 与
  map-mobile-expanded 页）；language 29 FAIL=0；density 28 FAIL=0；
  ui-reconstruction **180/180**；e2e **189/189**；backend pytest
  **961 passed / 2 skipped / 0 failed**；visual regression **59/59**（craft diff 全部
  低于 2% 容差 → EXPECTED_CRAFT_DIFF sub-threshold，snapshot 零变更；admin 0）。
- 人审包：`artifacts/ui-product-craft-v7/HUMAN_REVIEW/` 13/13 VALID（O6 全部
  VALID=true）+ HUMAN_REVIEW_INDEX.html + before/after 对照。
- 跨运行时：Android targeted FAST 7/7（emulator-5554 / AVD main；NO_HORIZONTAL_
  OVERFLOW / NO_CRASH / NO_ANR / NO_RENDERER_CRASH 全 PASS）；Windows targeted
  Smoke 7/7（Tauri v2 + WebView2；rail / keyboard / overflow 全 PASS）。
- 环境注记：Docker Desktop 无法稳定启动，DB 栈改用会话级 Windows pg16+PostGIS、
  Windows Redis、moto S3（scratch 内 `pg_up.ps1`/`redis_up.ps1`），仓库代码零依赖。
- 停止线：机器全绿 + 人审包 READY，**等待用户人工视觉签字**（Agent 不代替
  `UI_HUMAN_VISUAL_ACCEPTANCE = PASS`）；未 merge master / 未 tag / 未发布。
### 历史记录 — v0.2.6 RC Integration（2026-10-02，HISTORICAL）
## Current phase（2026-10-02 本轮实测 — v0.2.6 RC Integration / Cross-Runtime Final Acceptance）
- 状态：`V020_RC_INTEGRATION = PASS` · `UI_HUMAN_VISUAL_ACCEPTANCE = PASS_FOR_RC` ·
  `UI_VISUAL_CLOSURE = FROZEN_FOR_RC` · `CANONICAL_VISUAL_BASELINE_PROMOTION = PASS` ·
  `VISUAL_REGRESSION = PASS` · `WEB_FULL_REGRESSION = PASS` · `ANDROID_FAST = PASS` ·
  `WINDOWS_SMOKE = PASS` · `MASTER_FF_INTEGRATION = PASS` · `V020_RC_READY = YES` ·
  `PUBLIC_RELEASE = NOT_PERFORMED` · `AWAITING_RELEASE_AUTHORIZATION = YES`
- 分支：`feat/v020-rc-integration-v6`（基点 = v5 head `70d670c`）；origin/master 以 Git
  查询为准（本轮 fast-forward 集成，仅 FF，无 force/merge/rebase）；`v0.1.0` tag 未动。
- 基线提升：G2 将人工冻结的 v5 Consumer UI 提升为 canonical visual baseline
  （`docs/reports/V020_RC_VISUAL_BASELINE_MANIFEST.md`，24 张 consumer PNG + 断言对齐
  冻结 v5 DOM；Admin 零改动；视觉确定性 59/59 ×2 PASS）。
- 跨运行时：Android FAST（复用 emulator-5554 / AVD main，API 36）12 张截图全 PASS；
  Windows Smoke（真实 Tauri v2 + WebView2 154）9 张截图全 PASS；release-like H5 /
  Windows NSIS / Android APK+AAB 产物记录于 `artifacts/rc-v020/RC_ARTIFACT_MANIFEST.json`
  与 `docs/reports/V020_RC_ARTIFACT_REPORT.md`（signing 受限如实记录，不假签）。
- 机器 Gate（本轮实测）：vue-tsc PASS；client-h5 build PASS；admin build PASS；
  eslint 0；prettier PASS；ui-oracle compare 398/0/0 + 捕获套件 PASS（serial 稳定）；
  语言扫描 28 页 FAIL=0；density 21 FAIL=0；ui-reconstruction 180/180；
  Playwright e2e **189/189**；visual regression **59/59**；backend pytest
  **961 passed / 2 skipped / 0 failed**（含 Celery worker，petaccess_test DB）；
  secret scan 0 findings；dependency audit 0 known vulnerabilities；
  engineering gate **PASS（0 FAIL）**——v5 遗留 15 个 vue>200 冻结 Consumer 组件
  按仓库机制登记 TD-030（RC 轮禁止重构冻结 UI，拆分排 release 后）。
- G4 收口：Consumer 复制终扫 15 路由 0 命中；修复 2 处用户可见工程痕迹
  （地图覆盖提示 `信息不足 ≠ 允许` → `不等于允许`；设置页 `with_pet` 裸 key →
  `带宠出行`），并回归重建受影响 baseline。
- 本轮不创建 tag / 不发布 Release / 不上商店（`CREATE_V020_TAG = NO`；
  最终状态 `V020_RC_READY = YES`，发布动作等待用户授权）。

### 历史记录 — v0.2.5 Human Visual Closure（2026-10-01，HISTORICAL）
## Current phase（2026-10-01 本轮实测 — v0.2.5 Human Visual Closure / Interaction & Brand Polish 全量机器管道）
- 状态：`UI_HUMAN_CLOSURE_V5 = MACHINE_PASS` · 七页 `*_CANDIDATE = READY_FOR_HUMAN` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING` · `UI_VISUAL_CLOSURE = PENDING_HUMAN` ·
  `VISUAL_BASELINE_PROMOTED = NO` · `MASTER_MERGED = NO`
  （不得写作 `UI_HUMAN_VISUAL_ACCEPTANCE = PASS` / `UI_VISUAL_CLOSURE = PASS`）
- 分支：`feat/ui-human-closure-v5`（基点 = v4 head `e5a9949`）；feature branch pushed；
  最终分支 HEAD 以 Git 查询为准（文档不自我引用 HEAD）。
  origin/master = `842c030` **未动**（不 merge、不 fast-forward master，等人审 PASS 后另行请求）；
  `v0.1.0` tag 未动；无 force push / 无历史改写 / 未更新 `tests/visual/**-snapshots/*.png`
  （`git diff <v4-base>..HEAD --stat tests/visual/` 为空）。
- 方法：Human Visual Closure v5 —— 不使用任何视觉模型/OCR/截图理解；依据 v0.2.5 规格
  （§1–61 文字化人工反馈）做交互与品牌打磨；Oracle 只新增 §46 的 8 个 FAIL 级 gate
  （PLACE_NO_STRAY_GLYPH / PLACE_NO_ENGINEERING_INVARIANT_COPY / PLACE_RULE_GROUP_HAS_CONTEXT /
  PLACE_MOBILE_OVERVIEW_SUMMARY_PRESENT / MAP_MOBILE_SHEET_OVERLAY / MAP_MOBILE_SHEET_ABOVE_TABBAR /
  CONTRIBUTION_STEP_CONTEXT_PRESENT / CONTRIBUTION_OPTION_ROWS_NOT_PILLS），O1–O6 保留。
- 机器 Gate（final）：11 契约 **TOTAL PASS=398 WARN=0 FAIL=0**（含新增 map.mobile 契约 +
  8 个新 gate；v4 的 3 个 WARN 项本轮已清零）；语言扫描 28 页 FAIL=0（含 §48 禁词
  ≠/UNKNOWN/ALLOWED/PROHIBITED/CONDITIONAL/source_id/rule_id/zone_type 用户可见 DOM 0 命中）；
  density 诊断 21 行 FAIL=0（与 compare gate 对齐）。
- 页面实施：Place P0 收口（Rule Groups 带回文章节、Unknown Overview 最小化、mobile
  Space/Evidence summary row、Inspector 去重）/ Map Mobile overlay bottom sheet（half/
  expanded/peek 三态、segmented 地图|列表）/ Contribution Step Shell（place context +
  3-segment progress + radio option rows + reality cluster 表单 + Done copy）/ Search/Home/
  Reality/Evidence 打磨 / 全局一致性（Top Context Bar h60、rail blue-tint、reduced-motion）。
- 人审包：`artifacts/ui-human-closure-v5/HUMAN_REVIEW/`（§42 清单 **27 张全部 VALID** +
  HUMAN_REVIEW_INDEX.html；metadata actual 全部来自真实 DOM，O6 延续；metadata 只证明
  真实状态，不宣称视觉通过）。**等待用户人工视觉签字，Agent 不替代视觉 PASS。**
- 回归（本轮实测）：vue-tsc PASS；client-h5 build PASS；admin build PASS；eslint 0；
  prettier check PASS；ui-oracle probe + human-review v4/v5 全绿（final）；
  ui-reconstruction 180/180（responsive 8 断点 360/390/430/768/1024/1280/1440/1920 +
  a11y + phase gates + leakage）；Playwright e2e **189/189 ×2 全绿**（含 v5 §15 断言对齐、
  wizard 确定性 token boot、UUID 幂等键修复并行 409、reality 提交错误显式化）；
  backend pytest **961 passed / 2 skipped / 0 failed**（含 Celery worker，petaccess_test DB）。
- 本轮不产生 Android FAST / Windows Smoke 报告（人审门通过后的后续轮次；
  ANDROID_FAST = NOT_REQUIRED · WINDOWS_SMOKE = NOT_REQUIRED）。

### 历史记录 — v0.2.4 Blind UI Productization（2026-10-01，HISTORICAL）
## Current phase（2026-10-01 本轮实测 — v0.2.4 Blind UI Productization 全量机器管道）
- 状态：`BLIND_UI_PRODUCTIZATION_V4 = PASS` · `UI_MACHINE_PRODUCTIZATION = PASS` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING` · `UI_VISUAL_CLOSURE = PENDING_HUMAN`
  （不得写作 `UI_VISUAL_CLOSURE = PASS`）
- 分支：`feat/blind-ui-productization-v4`（基点 `feat/blind-ui-compiler-v2 @ 90d57e6`，
  先行 28 / 落后 0）；实现基准 `IMPLEMENTATION_BASE = e1c5ca7`（代码与测试完成后的实现 commit）；
  feature branch pushed；最终分支 HEAD 以 Git 查询为准。
  origin/master = `842c030` **未动**（不 merge、不 fast-forward master，等人审 PASS 后另行请求）；
  `v0.1.0` tag 未动；无 force push / 无历史改写 / 未更新 `tests/visual/**-snapshots/*.png`。
- 方法：Blind UI Productization v4 —— 不使用任何视觉模型/OCR/截图理解；依据 v0.2.4 规格
  （§1–64 文字化人工反馈 + 可执行 UI contract）改代码；Oracle 仅最小修正
  （阈值/作用域修正 + 当前反馈所需少量 contract + minVisibleInViewport 探针；O1–O6 保留）。
- 机器 Gate（final）：10 契约 **TOTAL PASS=368 WARN=0 FAIL=0**（原 3 个 WARN 升级项
  PLACE_HISTORY_COLLAPSED_MOBILE / PLACE_SECTION_GAP / PLACE_MOBILE_FIRST_VIEWPORT_LINES
  按新阈值执行，违反一律 FAIL）；语言扫描 26 页 FAIL=0。
- 页面实施：Search / Place / Home / Map / Reality / Evidence / Contribution 七页按
  v0.2.4 产品化规格落地（Place = Dossier with Views：`?view=` 本地导航、Overview 五块、
  长度门 desktop<=1500/mobile<=2000、mobile 首屏<=22 行、section gap<=40、去重、Unknown 收口）。
- 人审包：`artifacts/blind-ui-productization-v4/HUMAN_REVIEW/`（phase-a-search 4 /
  phase-b-place 5 / phase-c-home-map 5 / phase-d-rest 10 = **24 张全部 VALID** +
  HUMAN_REVIEW_INDEX.html；metadata actual 全部来自真实 DOM，O6 延续）。
  **等待用户人工视觉签字，Agent 不替代视觉 PASS。**
- 回归（本轮实测）：vue-tsc PASS；client-h5 build PASS；admin build PASS；eslint 0；
  prettier check PASS；ui-oracle probe + human-review 全绿（final）；
  ui-reconstruction 180/180（responsive 1440×900 / 430×932 + a11y + phase gates + leakage）；
  Playwright e2e **189/189**（含修复 mode-switch 重算、lens headline、并行 hash goto 加固）；
  backend pytest **961 passed / 2 skipped / 0 failed**（含 Celery worker，petaccess_test DB）。
- 本轮修复（WIP 阶段发现）：presence lens `row-lens-headline` 应为 reality 行（非 decision）；
  PlaceView 恢复 session mode watch（模式切换重算）；Contribution 步骤指示 5/3 → 2/3。
- 本轮不产生 Android FAST / Windows Smoke 报告（人审门通过后的后续轮次）。

### 历史记录 — v0.2.3 Blind UI Compiler v2（2026-10-01，HISTORICAL）
# PROJECT_STATE.md

## Current phase（2026-10-01 本轮实测 — v0.2.3 Blind UI Compiler v2 全量机器管道）
- 状态：`BLIND_UI_COMPILER_V2 = PASS` · `UI_MACHINE_CONTRACT_ACCEPTANCE = PASS` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING` · `UI_VISUAL_CLOSURE = PENDING_HUMAN`
- 分支：`feat/blind-ui-compiler-v2`；HEAD = `03ec482`（自 `e724f1c`，16 commits，已 push）；
  origin/master = `842c030` **未动**（不 merge、不 fast-forward，等人工视觉确认后另行请求）；
  v0.1.0 tag 未动；无 force push / 无历史改写 / 未删除既有 worktree。
- 方法：Blind UI Compiler v2 —— 不使用任何视觉模型/OCR/截图理解；六层 Oracle
  （O1 语义 / O2 几何 / O3 相对层级 / O4 内容预算 / O5 构图 / O6 状态完整性）+ Capture
  State Integrity + Executable Blueprint。见 `docs/ui/BLIND_UI_COMPILER_V2_METHOD.md`。
- 机器 Gate（final）：10 契约 **TOTAL PASS=332 WARN=3 FAIL=0**（3 WARN 均为既有
  place.mobile 容忍项：PLACE_HISTORY_COLLAPSED_MOBILE / PLACE_SECTION_GAP /
  PLACE_MOBILE_FIRST_VIEWPORT_LINES）；语言扫描 24 页 FAIL=0（uuid/enums/invariants/
  allcaps/refs 可见命中 0）。产物 `artifacts/blind-ui-compiler-v2/reports/*`。
- 页面实施：Search / Place / Home / Map / Reality / Evidence / Contribution 七页按
  v0.2.3 蓝图实施并全过机器门禁（phase A–D）。
- 人审包：`artifacts/blind-ui-compiler-v2/HUMAN_REVIEW/`（phase-a-search 4 /
  phase-b-place 3 / phase-c-home-map 2 / phase-d-rest 7 = **16 张全部 VALID** +
  HUMAN_REVIEW_INDEX.html，metadata actual 全部来自真实 DOM）。**等待用户人工视觉
  签字，Agent 不替代视觉 PASS。**
- 回归（本轮实测）：client-h5 vue-tsc+build PASS；eslint 0；prettier 3.9.6 PASS
  （repo-wide LF + format pass，独立 style commit，无语义变化）；Playwright e2e 串行
  189/189（并行 contribute-wizard TEST-001 懒加载 flake 既有，单跑绿）；ui-oracle
  probe+human-review 12+2 passed；ui-audit 70/70；visual 59/59（consumer 基线按蓝图
  重生成 24 张，admin 未动）；ui-reconstruction 串行 180/180；backend pytest
  **961 passed / 2 skipped / 0 failed**（含 Celery worker；adb.py 修复 ANDROID_HOME
  解析，Android 工具链 15/15）。
- 本轮不产生 Android FAST / Windows Smoke 报告（人审门通过后的后续轮次）。

### 历史记录 — v0.2.1 Visual Fidelity Recovery，Phase A（2026-09-28，HISTORICAL）

## Current phase（2026-09-28 当前会话实测 — v0.2.1 Visual Fidelity Recovery，Phase A: Search + Place）
# 状态重置（Goal §2）：UI_VISUAL_FIDELITY = FAIL · UI_CONSUMER_LANGUAGE = FAIL（Phase A 页面已清零，Reality/Evidence 属 Phase C）· UI_HUMAN_VISUAL_ACCEPTANCE = FAIL · UI_VISUAL_CLOSURE = REOPENED
# Phase A（Search/Place 桌面+移动）已完成实现与自动化门禁，真实截图见 artifacts/visual-fidelity-recovery/phase-a/ 与 VISUAL_FIDELITY_REVIEW.html；HUMAN_VISUAL_GATE_A = PENDING，见 docs/reports/VISUAL_FIDELITY_PHASE_A_REPORT.md
# 历史「UI_RECONSTRUCTION 全矩阵闭环」为 PRE-INTEGRATION / HISTORICAL 记录，不再作为当前视觉状态。
# 上游：v0.1.0 Early Preview — 已发布（2026-09-24）｜v0.2.0 M1–M8 已完成（HISTORICAL）

## UI Reconstruction 收口（2026-09-28 全实测, HISTORICAL / PRE-INTEGRATION — 当前视觉状态以顶部 v0.2.2 章节为准）
- 定位：M3.1 Consumer Contract 关闭（G1 五项全 PASS）+ Home/Search/Map/Place/Reality/Evidence/Contribution 七页按 v0.10-R1 Canonical Master + Approved Reference 重构为 Spatial Dossier（空间档案式）成熟工具。
- Canonical master 与 Approved Reference PNG 已随分支提交（commit 5af0020），非 untracked。
- G1（M3.1）消费契约 5 项 PASS（COEXISTENCE_SNAPSHOT_SSOT / TRANSPORT_ERROR_CACHE / SNAPSHOT_CACHE_KEY / OFFLINE_STALE_WIRING / LENS_SEMANTICS），回归测试 tests/e2e/consumer-contract-closure.spec.ts 全绿。
- 工程门禁（本轮实测）：backend pytest **961 passed / 2 skipped**；vue-tsc / client-h5 build / admin build / eslint / prettier 全 PASS；Playwright e2e **189 passed**（响应式矩阵扩至 8 页 × 9 viewport）；ui-reconstruction capture（final stage）**90/90**；phase1+phase3 gate 45/45；a11y gate **30/30**；responsive 72/72。
- 文件体积遗留已处理：HomeView 199 行 / MapView 203 行 / EvidenceView 263 行（composable + 子组件拆分，prettier 幂等）。
- Android FAST（真实模拟器 pdig36，端口 5556）：Install/launch/Home/Search(7 条真实结果)/Map/Place/navigation/offline/recovery/short-lifecycle **全 PASS**（WebView CDP DOM + 设备层截图证据；修复了 C: 盘 1.3GB 可用不足；从未 adb kill-server）。见 docs/reports/UI_RECONSTRUCTION_ANDROID_FAST.md。
- Windows smoke（真实 Tauri WebView2 runtime）：build 2m52s → petaccess.exe；launch/Home/Search/Map/Place/navigation/offline/recovery 全 PASS（CDP + UI Automation 证据）；不再是 stretched H5。见 docs/reports/UI_RECONSTRUCTION_WINDOWS_SMOKE.md。
- 视觉审计：结构断言 + 像素级证据全过；90 张 final 截图 + UI_RECONSTRUCTION_BEFORE_AFTER_GALLERY.html（90 格）可直接打开。当时 `UI_VISUAL_CLOSURE = PASS（自动化证据）` 已按本轮 v0.2.2 契约修正为 **HISTORICAL**；人工目视复核见本轮 `artifacts/blind-ui-recovery/HUMAN_REVIEW/`（等待用户签字，`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING`）。
- 遗留（tracked）：TEST-001 contribution-wizard 并行 flake（既有冻结语义，单跑/重跑均 PASS）；Android WebView uiautomator 文本可见性 PLATFORM_LIMITED（既有，非缺陷）；artifacts/ 目录 gitignored（工作区证据）。
- LOCAL git：分支 `feat/ui-reconstruction-spatial-dossier`（commit：5af0020→567e42e→8b7e245→fa2b368→ec8af2c→2fcf241→4fc21ba→af25ee6→7404155）；origin/master `434efd3` 未变（0 divergence，纯 fast-forward descendant，按 AC-G1 四条件 FF 集成并 push）。v0.1.0 tag 未动。

## M3 深化收口基线（历史记录 — 2026-09-27，保留作 provenance）

## M3 深化收口基线（2026-09-27 全实测, CURRENT VERIFIED — 见 docs/reports/V020_M3_FINAL_REPORT.md）
- 定位（用户确认）：M3 深化收口——基于现有实现做 UI/UX 全量设计收口，不吞并 M4/M5/M7；Canonical Master = v0.10-R1（2026-09-27）。
- 方向 FREEZE：Structured Utility（Calm/Neutral/Urban/Evidence-first）；DESIGN.md + docs/ui/V020_M3_UI_DIRECTION_DECISION.md；候选 A/C 归档 artifacts/ui-audit/concepts/。
- Consumer 架构：新增 consumer/{cache,repository,rowView}.ts — bounded concurrency（Search 原 N×无界 Promise.all → 4 worker）+ ConsumerCache（TTL/stale/offline/coalesce）+ request epoch（race 保护）+ transport error ≠ domain fact（answerError/realityError 显式）。
- CoexistenceSnapshot SSOT：Search/Home 行级 Reality+Freshness+Evidence（PlaceResultRow）；无页面级第二套 Rule/Reality truth。
- Home/Search/AppShell：移除旧 AppShell 双层 chrome（Home/Search 直接 ConsumerAppShell 框架）；行级信息 = identity→Rule→Reality→Freshness/Evidence；桌面 wide/split 分层。
- 测试（本轮实测）：backend pytest **961 passed / 2 skipped**；vue-tsc/build/eslint/prettier 全 PASS；Playwright e2e **157/158**（1 = 既有 TEST-001 flake，stash 到基线 HEAD 复现同样失败、单独跑 3/3 绿，与 M3 无关）；visual **59/59**（12 张 consumer 基线按 M3 视觉重生成）；新增 m3-consumer-core.spec（5 tests）全绿。
- 截图取证：current（BEFORE）70 张 + m3-final（AFTER）70 张 + UI_CURRENT_STATE_GALLERY / UI_M3_FINAL_GALLERY / UI_M3_BEFORE_AFTER_GALLERY（140 图 0 broken）；根目录 artifacts/ui-audit/。
- Android FAST：PASS（launch/home/search 21 results/nav/offline/recovery/short lifecycle，debug APK CDP DOM 证据；见 docs/reports/V020_M3_ANDROID_FAST_REPORT.md）。
- Windows smoke：PASS（NSIS install/launch/home/search/split-preview/navigation/offline/recovery，截图 + accessibility 树；见 docs/reports/V020_M3_WINDOWS_SMOKE_REPORT.md）。
- 遗留（tracked）：TEST-001 contribution wizard 并行 flake（既有冻结；基线复现）；Home/Search 文件体积 >300 行（既有大型页面，数据逻辑已抽 repository，M4 可继续拆）；Android WebView uiautomator 文本可见性 PLATFORM_LIMITED（既有）。
- LOCAL git：baseline 049fc39；M3 分支 feat/v020-m3-consumer-core（8 commits）；origin/master 5b1dd05 未变（纯 fast-forward descendant，待最终 FF 集成与 push）。

## Current phase（历史记录 — 2026-09-25 M8 基线，保留作 provenance）

## 取证审计基线（2026-09-26 全实测, CURRENT VERIFIED — 见 docs/forensics/）
- 结论：PETACCESS_GLOBAL_FORENSIC_AUDIT = PASS（FINAL_ROOT_CAUSE_REPORT.md / GLOBAL_CODE_AUDIT_FINAL_REPORT.md；F00–F13 全量落盘）
- 三矩阵（F03）：A=GitHub Release v0.1.0（SHA256 e236f193…）／B=v0.1.0 重建／C=HEAD，同机同 SDK 同 emulator 统一 adb 全链 PASS；情况 4 判定（A/B/C 全 PASS）→ 原始异常归因为环境/自动化（ADB churn REG-001、PS 截图编码 REG-002、并发会话 REG-005、ASCII 路径 REG-007），非 boot/渲染代码回归
- 产品缺陷修复（REG-003，commit 1d93942）：packaged API base 按运行形态解析（endpoints.ts），不再依赖 Vite proxy；CSP 最小 +10.0.2.2（Android 模拟器 dev）
- Backend pytest：**945 passed / 2 skipped / 0 failed**（修复后重跑与传统基线 938/944 均为历史值）
- Engineering gate：0 FAIL / 60 REVIEW / 34 WARN；ruff / format PASS（299 文件）；mypy 96 files / 0 errors；secret scan 0 findings；alembic 单头 e9f2c1d4a5b6（downgrade→upgrade 链实测通过）
- H5+Admin build PASS；Playwright e2e **149 passed**（全量重跑确认；contribute-wizard B2 并行抖动已加固）
- Windows 运行时 PASS（NSIS install/launch/窗口/relaunch/uninstall 全清）；Android 终态门禁 PASS（A→修复版同签名升级、PETACCESS_BOOT 5 阶段链 logcat 实证、uninstall 后设备干净）
- 遗留（tracked）：FF-003/FF-004/FF-006/FF-007（维护性债务，见 FORENSIC_FINDINGS_REGISTER.md）；M3_RESUME_ALLOWED = YES（恢复条件已满足，恢复动作由用户决定）

## v0.1.0 状态
- **V0_1_0_RELEASED = YES（2026-09-24 已发布 https://github.com/huangdi97/petaccess/releases/tag/v0.1.0）**
- **HUMAN_ACTION_REQUIRED = 无**（RELEASE_V0_1_0_AUTHORIZATION 已由 huangdi97 于 2026-09-24 授权并完成发布）
- GitHub 阶段 DONE：remote=origin（huangdi97/petaccess）；tag v0.1.0；GitHub Release 已发布（Early Preview，非 Public Beta）；双产物已重下载并通过 SHA256/签名/安装校验（Phase AH）
- 发布就绪门槛全部实测 PASS（见 docs/release/V010_RELEASE_READINESS_REPORT.md）
## 质量基线（2026-09-24 全实测, CURRENT VERIFIED）
- pytest 938 passed / 2 skipped（TEST DB + Celery worker）
- ruff / format PASS；mypy services/api/app 93 files / 0 errors
- Engineering gate：0 FAIL / 60 REVIEW / 26 WARN；§40 四新项（silent-catch / magic-status / dead-code / duplicate-config）已接入 collect()，修复后 RESULT: PASS
- Secret scan（worktree + history）：0 findings
- VERSION_DRIFT = 0（scripts/check_version_drift.py，含 design-tokens 0.6.0-beta.1→0.1.0 修正）
- H5 + Admin vue-tsc + build PASS；Playwright E2E 21 passed（18 + 3 empty-state）
- Visual 47 PASS（17 基线家族 × viewports；Empty-First 文案改动后基线重生成一次，compare 全绿）
- A11y：0 issues（consumer + admin 全页, 键盘焦点走查 0 invisible）
- 依赖扫描：pip-audit / pnpm audit 均 0 known vulnerabilities（Critical=0 / High=0）


## v0.2.0 M3 质量基线（2026-09-24 全实测, CURRENT VERIFIED）
- Route/query foundation：404 catch-all + NotFoundView、route meta.title（afterEach）、scrollBehavior；Search 深链 ?q=/?lens= 回填、back/forward 同步（e2e A1/A3/B1/B2 全绿）
- CoexistenceSnapshot 统一消费兑现（ADR-029）：Search 桌面 split-view（PlacePreview 第一轮，client.coexistenceSnapshot），行级 rule 摘要收敛为共享 ruleSummaryLabel；PlacePreview 纯 props 呈现、无第二套模型
- 统一错误呈现收口：新增 presentDescription（errors.ts）；Home/MatchExplain/Mine 接线 StateMessage；e2e E2 断言页面不泄漏 SQLAlchemy/FastAPI/psycopg2 等内部字样
- E1 视图状态守卫扩展：REQUIRED_PER_VIEW 覆盖全部数据驱动视图 + DECLARED_STATIC（@ui-static/@ui-form 显式声明），断言每个路由视图必须落入其一（unit 8 passed）
- A11y：M3 新增/变更面 axe 0 critical / 0 serious（顺带修复桌面 rail 版本标签对比度）；移动端 6 家族复扫 0/0
- 门禁全绿：eng gate 0 FAIL / 60 REVIEW / 29 WARN；ruff / format PASS；mypy 96·0；backend 回归 DISCOVERED 946 = 944 passed / 2 skipped / 0 failed；e2e 75 passed；visual 42 passed；eslint / prettier PASS；H5 + Admin build PASS
- 后端零改动；性能无退化（SearchView 10.0 kB，+0.1 kB split 逻辑）

## v0.2.0 M4 质量基线（2026-09-24 全实测, CURRENT VERIFIED）
- Map 桌面 split-view（DesktopContentContainer split：地图 + PlacePreview 详情面板）+ `/map?place=` 深链与 back/forward 同步（e2e A1/A4 全绿；visual map-split 家族）
- Map 状态收口：empty（EMPTY_STATE_COPY.MAP + 返回首页）、error 走 presentError（修复原始泄漏）、offline 由 shell GlobalOfflineBanner 单一承担（移除本地 banner）
- Place Passport 收口（10 段骨架未重建）：桌面阅读列（single-column）、Section 7 证据视觉语言（EvidenceStatus/EvidenceMeta/FreshnessStatus，无原始枚举上屏）、统一错误呈现（4 处 quickMsg + 主错误）；e2e B1/B2/B3/B5 全绿
- A11y：map / place 表面 axe 0 critical / 0 serious（顺带修复 ALLOWED 徽章对比度 #2e7d52→#277348，tint 上 4.38→5.06:1）；移动端 6 家族复扫 0/0
- 门禁全绿：eng gate 0 FAIL / 60 REVIEW / 29 WARN；ruff / format PASS；mypy 96·0；backend 回归重跑 944 passed / 2 skipped / 0 failed；e2e 82 passed；visual 42 passed；eslint / prettier PASS
- 后端零改动；真实腾讯地图无 Key → 如实记录 BLOCKED_EXTERNAL（MockMap 交付，不假接线）

## v0.2.0 M5 质量基线（2026-09-24 全实测, CURRENT VERIFIED）
- Reality Trace 独立路由 `/#/place/:id/reality`（meta.title「现场轨迹」+ 深链 + Passport RealityPanel「查看现场轨迹」CTA）；fact/review 分区渲染（sunken 表面区分，非仅颜色），note 保留
- 观察时间线（client.observations：时效/动物范围/动作/工作人员/note/争议）+ 空态 REALITY copy；状态完备（SkeletonList/StateMessage/presentError/shell offline）
- 统一 Evidence 呈现：EvidenceStatus（dispute 映射 verified/pending/disputed/historical）+ EvidenceMeta + freshness，无原始枚举上屏（顺带修复 RealityPanel 原 verification 枚举泄漏）；规则 provenance 留 Passport §7 未复制
- A11y：trace 页（桌面+移动）axe 0 critical / 0 serious
- 门禁全绿：eng gate 0 FAIL / 60 REVIEW / 30 WARN；ruff / format（470 文件）PASS；mypy 96·0；backend 回归重跑 944 passed / 2 skipped / 0 failed；e2e 87 passed；visual 45 passed；eslint / prettier PASS
- 后端零改动；无新架构决策
## v0.2.0 M7 质量基线（2026-09-25 全实测, CURRENT VERIFIED）
- 贡献向导重建（769 行旧单体 → 171 行编排器 + 8 个步骤组件，全部 vue ≤200）：entry/quick/signage/rule/experience/reality/done 7 步状态机；placeId+signedIn 门禁（未选场所/未登录双 CTA）；TD-015 豁免关闭
- 现实贡献走父流 createRealityReport（candidates + effort + privacy private，ADR-029）；规则/拍照/快速确认保持旧端点不迁移
- 贡献历史：新端点 GET /api/v1/me/reality-contributions（仅本人数据 50 上限，匿名 401，复用 RealityReport/RealityCandidate 无新模型）+ MineView「我的贡献」区块（CANDIDATE_TYPE_LABELS/CONTRIBUTION_STATUS_LABELS 字典，无原始枚举上屏）
- A11y：contribute 全态（signed-out/entry/reality-form 桌面+移动）+ mine axe 0 critical / 0 serious（顺带修复全部表单 label/select 程序化关联）
- 门禁全绿：eng gate 0 FAIL / 60 REVIEW / 34 WARN；ruff / format PASS；mypy 96·0；backend 回归重跑 945 passed / 2 skipped / 0 failed（+1 贡献历史集成测试）；e2e 90 passed（+3 contribute-wizard）；visual 59 passed（contribute-h5-390 重生成）；eslint / prettier PASS；client-h5 build PASS
- 后端改动仅 1 新端点（UI 所需 contract gap）+ 集成测试；死代码豁免新增仅 TD-028 decorator-registered 类别
## v0.2.0 M8 质量基线（2026-09-25 全实测, CURRENT VERIFIED）
- Windows DPI 矩阵收口（M2 §7 延期项）：新增 tests/e2e/desktop-dpi.spec.ts，3 物理分辨率 × DPI 100/125/150% = 9 组（逻辑 CSS 视口 = physical/scale + deviceScaleFactor 模拟），×6 主页面 54 条：渲染非空/无横向溢出/desktop-rail 可见/DSF 实际生效
- 真实壳冒烟：tauri build（vcvars+MSVC）1m25s → petaccess.exe + NSIS 安装包；install/launch（WebView2 子进程渲染确认）/relaunch/uninstall 全 PASS；产物 artifacts/v0.2/PetAccess_v0.2-desktop_x64-setup.exe（SHA256 be1e8c6a…）
- Android 模拟器冒烟并入 M8（用户拍板）：worktree reset 至 master → tauri android build（补装 platform-36/build-tools-36）→ apksigner release 签名 → emulator API35 install/launch（截屏 2743 色真实渲染）/force-stop/relaunch（2753 色）/uninstall 全 PASS；PetAccess_v0.2-android-universal.apk（SHA256 c1600cc9…）
- 门禁全绿：eng gate 0 FAIL / 60 REVIEW / 34 WARN；ruff / format PASS；mypy 96·0；backend 回归重跑 945 passed / 2 skipped / 0 failed；e2e 144 passed（+54 DPI 矩阵）；visual 59 passed；eslint / prettier PASS（eslint.config.js projectService 上限 20→25，非豁免）
- 壳配置审计无变更（窗口 1000×760 / min 640×480 / CSP deny-by-default / capabilities 仅 core:default）；tauri.conf 版本号沿用 0.1.0，v0.2.0 发布轮再升
## v0.2.0 M2 质量基线（2026-09-24 全实测, CURRENT VERIFIED）
- Engineering gate：0 FAIL / 60 REVIEW / 28 WARN（PASS）；ruff / format PASS；mypy 96 files / 0 errors
- Backend pytest 全量重跑：DISCOVERED 946 = PASSED 944 / SKIPPED 2 / FAILED 0（TEST DB + Celery + MinIO）
- H5 + Admin vue-tsc + build PASS；ESLint / Prettier PASS（29 个 M2 文件补 prettier，见工程报告 §6）
- Playwright e2e 70 passed；Visual 42 passed（14 基线家族 × 390/768/1440，a11y 修复后重生成）
- A11y（axe-core 4.10 六家族机器扫描）：0 critical / 0 serious
- 性能基线（§50）：main 134.39 kB（gzip 51.94）；HomeView 10.19 kB；SearchView 9.99 kB；记录于 V020_M2_ENGINEERING_REPORT.md
- Windows Tauri / Android 真机 DPI QA：PARTIAL（推迟 M8/M9），见工程报告 §7
- 8 份 §56 交付文档齐备（docs/v0.2/）；DECISIONS.md 记录 ADR-031（DEV_FIXTURE_MODE fail-closed）

## v0.1.0 产品（Early Preview, Empty-First）
- 允许数据为空：Places/Rules/RealityClaims/StaffResponses/AnimalFacilities = 0 也完整可用
- Home「当前还没有已发布的场所数据」+ 探索地图/贡献线索；Search「没有找到已收录场所」
- 不变量：UNKNOWN ≠ ALLOWED；Observation ≠ Rule；AI ≠ final judge；无 fake 数据入 release

## 平台产物（实测构建并冒烟）
- Windows：`artifacts/v0.1.0/PetAccess_0.1.0_x64-setup.exe`（NSIS, 未签名→SmartScreen 提示）
  install→launch→relaunch→uninstall 冒烟 PASS（WebView2 渲染确认）
- Android：`artifacts/v0.1.0/PetAccess_0.1.0-android-universal.apk`（release keystore 签名 v2/v3,
  com.petaccess.map, versionName 0.1.0, versionCode 1000, minSdk 24, 仅 INTERNET）
  模拟器 API 35 冒烟 PASS（install→launch 实拍渲染→relaunch→uninstall）
- SHA256SUMS.txt 双产物逐项校验一致

## 架构
- UI（Vue3+H5/Admin, design-tokens）→ App（client-core）→ Domain（FastAPI app/）→ Ports
- Infrastructure implements Ports；dependency cycles = 0（gate 检测）
- Tauri 2 壳（src-tauri, additive）：仅 window/lifecycle/IPC/security；Domain 不写入 Rust
- Provider 全部 interface + adapter（map/ai/ocr/storage/notification, 默认 mock）

## CI
- .github/workflows/pr-ci.yml（M1, committed）+ release-ci.yml（M9/M10, committed）
- 远程 CI 未执行：BLOCKED（无 remote, 发布未授权）— 不得伪造 PASS

## 环境备注
- Docker Desktop 29.2.1（WMI 持久启动）；postgis 17 + redis + minio healthy
- Celery worker（Redis db 1, queue petaccess_test）供 test_media/test_v05_e2e 消费
- Rust 1.97.1 + 便携 VS2022 MSVC（D:）经 vcvars 环境构建
- Android 构建需 ASCII 路径：仓库路径含 CJK 触发 AGP 拒绝 → 使用 git worktree
  C:\petaccess-worktree（记录于 V010_ANDROID_REPORT.md）

## Blocker / 下一步
- **v0.1.0 已发布（2026-09-24）**；RELEASE_V0_1_0_AUTHORIZATION 已授权并完成：remote + tag + Release CI 全绿 + GitHub Release + 重下载 SHA256/签名/安装校验全 PASS
- 远期（非 v0.1.0）：真实地图 key / AI key / 数据扩充 / 商店上架 / Public Beta 数据版

## Truth rule
Never infer PASS。
