# PROJECT_STATE.md

## Current phase（2026-09-29 本轮实测 — v0.2.2 Blind-Model UI 全量收口）
- 状态：`UI_MACHINE_CONTRACT_ACCEPTANCE = PASS` · `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING`（第一轮人工验收 = **REJECTED**：「太规整，缺生活气息」→ 按用户选定方向 B 完成视觉温度收口并重发，等待再次签字）· `UI_VISUAL_CLOSURE = PENDING_HUMAN`
- 分支：`feat/visual-fidelity-recovery`；HEAD = `12ad324`（push 后更新）；origin/master = `842c030` **未动**（不 merge、不 fast-forward、等人工视觉确认后另行请求）；v0.1.0 tag 未动。
- 方法：Blind-Model —— 不使用任何视觉模型/OCR/截图理解；以 `docs/ui/contracts/` 机器契约 + `tools/ui-oracle/` 自建 Oracle 测量（DOM/bbox/computed style/density/语言扫描）驱动收口。见 `docs/ui/BLIND_UI_COMPLETION_METHOD.md`。
- 机器 Gate（final）：10 契约 **TOTAL PASS=164 WARN=1 FAIL=0**（唯一 WARN = place.mobile 首屏 42 行，契约 warnAt=30，progressive disclosure 记录）；语言扫描 21 页 FAIL=0（UUID/enum/invariant 可见命中 0）。产物 `artifacts/blind-ui-recovery/reports/*`。
- **生活气息收口（2026-09-30，用户 REJECTED「太规整」后按方向 B 重发）**：暖纸 app 底色（#faf7f2）+ 暖 surface token（surface-warm/warm-strong/border-warm + radius-row 12px）；Search/Map/Home nearby 行从「radius 0 divider 表格」改为「12px 圆角 + 轻投影柔行」；DecisionInspector 与 Place 决策块从裸文字改为暖 surface；Place section 间距 24→32。语义色不变。契约锚点 SEARCH_ROW_RADIUS_ZERO → SEARCH_ROW_RADIUS_SOFT(8–16px)。重跑后 final gate 仍 PASS=164 WARN=1 FAIL=0。
- 回归（本轮实测）：client-h5 vue-tsc+build PASS；eslint 0；prettier PASS；Playwright e2e 189/189（串行；并行 2-worker 下 contribute-wizard 懒加载超时 flake 既有）；ui-reconstruction 180/180（phase1/3 + a11y + leakage all）；visual 59/59（consumer 基线按新 UI 重生成 38 张）；ui-audit 70/70；backend pytest 836 passed / 2 skipped / 4 环境性失败（celery/OCR/adb 路径，均与本轮无关；`-k reality` 30/30）。
- Android FAST（emulator-5554 复用，ASCII worktree 例外经用户确认后构建并已删除）：install/launch/Home/Search(16 结果)/Place/Map/nav/offline/recovery/lifecycle 全 PASS。见 `docs/reports/BLIND_UI_ANDROID_FAST.md`。
- Windows Smoke（真实 WebView2/Tauri，工作区内构建）：launch/Home/Search(16 结果)/Place/Map/nav/offline/recovery 全 PASS。见 `docs/reports/BLIND_UI_WINDOWS_SMOKE.md`。
- 人工验收证据：`artifacts/blind-ui-recovery/HUMAN_REVIEW/`（14 张命名截图 + HUMAN_REVIEW_INDEX.html，仅机器校验 PNG magic/dimensions/bytes/hash）。**等待用户人工视觉签字，Agent 不替代视觉 PASS。**
- 历史章节（下方 v0.2.1 / M3 / M8 / M2 等）均为 HISTORY / PRE-INTEGRATION，不再代表当前视觉状态。

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
