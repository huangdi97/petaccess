# V0207_PRODUCT_CRAFT_FINAL_REPORT

Round: **v0.2.7 — Final Product Craft / Spatial Map / Desktop Composition Closure**

## 1. Identity

- PROJECT = PetAccess (Place Animal Coexistence Intelligence; Rule Layer + Reality Layer + Evidence / Governance)
- BRANCH = `feat/ui-product-craft-v7`
- BASE_HEAD = `42ed4e34158a566b2574b7176d3d12ddf12a20e1`（轮开始时 fetch 后的 origin/master；与规格参考 SHA 一致）
- FINAL_HEAD = `c7f06df49e0f5241ca1e308e74c49928d9bf0b33`（本轮分支 HEAD）
- ORIGIN_MASTER = `42ed4e34158a566b2574b7176d3d12ddf12a20e1`（未动）
- V0_1_0_TAG_SHA = `c84b4cf61fda1b904027aa6899a00a443a1ee383`（未动）
- WORKTREE_STATUS = clean（提交后）

## 2. WHAT_CHANGED

受控 craft 实现（仅 CSS / template / oracle 契约 / 报告 / 状态文档）：

1. **Map Spatial Craft（P0-A）**
   - `MockMap.vue`：抽象城市空间画布 —— 道路层级（primary 5px / secondary 2px）、街区多边形、district edge、开放空间斑块、建筑体块提示、水系 ribbon；整体极浅冷中性低对比，地图不抢 overlay。
   - Marker 系统：UNKNOWN=neutral fill、CONDITIONAL=subtle amber ring、ALLOWED/RESTRICTED=语义 fill、SELECTED=scale(12→16px)+halo+elevation；无大彩 pin / emoji / 动物 icon 满图；cluster 聚合保留实心语义填充与选中 halo。
   - `MapView.vue`：map-canvas 移除「灰网格 + 数字」式 repeating-grid，退回极浅冷中性纯色，由 MockMap SVG 分层。
   - `MapSelectedSheet.vue`：mobile sheet 仅 craft handle/间距；**expanded 只新增真实信息**（结论 verdict + 证据与来源 issuer·更新日期，全部来自 snapshot，无伪造/占位）。
2. **Contribution Desktop Composition（P0-B）**
   - `ContributeView.vue`：desktop（≥1024）两栏 workspace —— main task column（680px）+ secondary context rail（280px，总宽 1008px ∈ 900–1040）；context 只放真实上下文（当前场所/区域、本次贡献类型、为什么需要这些信息、提交之后），无营销/统计/badge wall。
   - `ContributionStepShell.vue`：progress 退后（label sm+宽字距）、question 更强（title 26/650）。
   - `ContributeRealityForm.vue`：Step 2 结构化表单包 `data-ui="contribution-form"`；When/Where/What 三组 Field Group 组距 24px（20–28 节奏），消除「一项一巨大 gap」。
3. **Desktop Density / Reading Rhythm（P0-C / P1）**
   - `RealityEventLog.vue`：Observed Fact 主行（event 先、600/15px）、Location 次行（md/secondary）、staff 从属（sm/secondary）、review meta 第三层；待核验不抢事实。
   - `EvidenceView.vue`：record identity 22/650 成为页面首要事实；provenance 层级不变。
   - `DecisionInspector.vue`（search variant）：Reality + Evidence 归组为 secondary evidence grouping（顶部细分隔线），primary decision 保持唯一强焦点。
4. **Oracle Craft Gates（§40，用户确认为硬性 gate）**
   - 新增 10 个 gate：MAP_CANVAS_OCCUPANCY、MAP_SELECTED_HIERARCHY、MAP_MOBILE_SHEET_CONTENT_DENSITY、MAP_EXPANDED_NO_FAKE_FILLER（含新 page `map-mobile-expanded`）、CONTRIBUTION_DESKTOP_WORKSPACE_BALANCE、CONTRIBUTION_MAIN_COLUMN_BOUNDED、CONTRIBUTION_CONTEXT_VISIBLE、CONTRIBUTION_FIELD_GROUP_RHYTHM、PRIMARY_CONTENT_DOMINATES_METADATA（×4 契约）、STATUS_BADGE_NOT_PRIMARY（×2 契约）。
   - `tools/ui-oracle/compare.ts` 增加 `shadowed` computed-style 检查（selected marker 浮起判定）。
5. **Human Review Pack（§36）**
   - `tests/ui-oracle/human-review-v7.spec.ts` + `artifacts/ui-product-craft-v7/HUMAN_REVIEW/`：13 张截图（01_home_desktop … 13_contribution_mobile_step1），每张 O6 State Integrity VALID=true，配 metadata JSON + HUMAN_REVIEW_INDEX.html（含 before=RC 冻结 baseline / after=craft 对照）。

## 3. WHAT_DID_NOT_CHANGE

- 产品结构 / IA：Home、Search（Rail|Result Pane|Decision Detail Pane）、Place（Dossier with Views）、Map（Spatial Workspace）、Reality（Event Log）、Evidence（Provenance Record）、Contribution（Structured Transaction Flow）全部保持；无 dashboard、无 card wall、无黑名单/评分/排行语义。
- Rule != Reality、Observation != Rule、StaffResponse != OperatorPolicy、External != Official、No Observation != No Animal Presence 等语义分离保持；consumer copy 0 命中内部 code（§27 扫描通过）。
- Design System：未换字体、未重做 token；本轮未新增 design token（全部复用现有 tokens.css 语义色/spacing）。
- Admin UI：零改动（ADMIN_VISUAL_BASELINE_CHANGE = 0）。
- 未接入任何地图 provider / API key / billing；无大型 GIS 下载。
- TD-030（15 个 >200 行冻结 Consumer 组件）：保持 deferred（本轮未导致文件不可维护）。
- Release-like artifacts：RELEASE_LIKE_ARTIFACT_REBUILD = NOT_REQUIRED（本轮未重建 AAB/NSIS/manifest）。

## 4. MAP_CRAFT

- 判定：PASS。几何 gate（MAP_CANVAS_OCCUPANCY：desktop canvas ≥700px；MAP_SELECTED_HIERARCHY：selected ≥14px + shadowed=1；MAP_MOBILE_SHEET_CONTENT_DENSITY：sheet body gap 8–48；MAP_EXPANDED_NO_FAKE_FILLER：无 placeholder/filler + semanticBlockCount 3–6）全部通过；O6 expanded page VALID。
- 人工对照：04_map_desktop / 05_map_mobile_ready / 06_map_mobile_half / 07_map_mobile_expanded 已进人审包。

## 5. CONTRIBUTION_CRAFT

- 判定：PASS。CONTRIBUTION_DESKTOP_WORKSPACE_BALANCE（main/workspace 0.55–0.8，实测 0.65/0.64）、MAIN_COLUMN_BOUNDED（620–760，实测 680/664）、CONTEXT_VISIBLE（240–320，实测 280）、FIELD_GROUP_RHYTHM（16–40，实测 24）全通过；`PRIMARY_CONTENT_DOMINATES_METADATA`（question vs hint ≥1.4）通过。
- 人审包：10/11/12/13 contribution 截图。

## 6. DESKTOP_DENSITY / SEARCH_CRAFT / REALITY_CRAFT / EVIDENCE_CRAFT

- DESKTOP_DENSITY：Reading（Reality/Evidence 820）、Task（Contribution 1008 两栏）、Spatial（Search/Map/Place workspace）三类宽度落地；density 诊断 28 行 FAIL=0；ui-reconstruction 180/180（含 responsive 8 断点 + leakage + a11y）。
- SEARCH_CRAFT：detail secondary grouping + 保留 620–704 内容列；SEARCH_DETAIL_* 既有契约 0 FAIL。
- REALITY_CRAFT：event/location/staff/meta 四层阅读层级 gate（PRIMARY_CONTENT_DOMINATES_METADATA reality 契约 ≥1.1）通过；REALITY_* 既有契约 0 FAIL。
- EVIDENCE_CRAFT：record identity 22/650；provenance 5 步、marker x 一致、step gap 28–36 等契约 0 FAIL。

## 7. VISUAL_DIFF_CLASSIFICATION

- 视觉回归：59/59 PASS（compare 模式 + `--update-snapshots` 模式各一次）。
- 所有 craft diff 均低于 baseline 的 maxDiffPixelRatio 2% 容差 → 分类 **EXPECTED_CRAFT_DIFF（sub-threshold）**；`--update-snapshots` 实际产生 **0 个 snapshot 文件变更**（无 diff 超过容差即无需重写）。
- UNEXPECTED_REGRESSION = 0；**ADMIN_VISUAL_BASELINE_CHANGE = 0**（admin 14 张全部未变）。
- 说明：用户已授权「机器全过后即 promote」；本轮 promote 尝试后基线文件零变更，即基线在当前容差下已包含全部 craft 效果，无需重写。

## 8. HUMAN_REVIEW_PACK

- 路径：`artifacts/ui-product-craft-v7/HUMAN_REVIEW/`
- 13/13 VALID（9 desktop + 4 mobile），0 INVALID；每张 PNG 先过 O6 State Integrity 再保存；metadata JSON 的 actual 全部来自真实 DOM（route/page/state/fixture/h1/entity/count）。
- `HUMAN_REVIEW_INDEX.html`：13 张卡片 + before（tests/visual 已冻结 RC baseline）/after 并排对照（存在映射处），声明 `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。

## 9. WEB_GATES（本轮实测）

| Gate | Result |
|---|---|
| vue-tsc / client-h5 build | PASS |
| admin build（vue-tsc + build） | PASS |
| eslint | 0 issues |
| prettier --check | PASS |
| ui-oracle（final） | **423 PASS / 0 WARN / 0 FAIL**（基线 398 → +25：10 新 craft gates + expanded page 行；WHY_TEST_COUNT_CHANGED = 新增 §40 gates 与 map-mobile-expanded 页） |
| ui-language | 29 pages FAIL=0 |
| ui-density | 28 rows FAIL=0 |
| ui-reconstruction | **180/180** |
| Playwright e2e | **189/189** |
| visual regression | **59/59**（baseline 零变更；admin 0） |
| backend pytest | **961 passed / 2 skipped / 0 failed**（含 Celery worker；moto S3 替代 MinIO 用于 media 用例） |

## 10. ANDROID_TARGETED_FAST

- 环境：复用 emulator-5554 / AVD `main`（未新建 AVD）；APK = `D:\pa-fix\apps\client-h5\src-tauri\gen\android\app\build\outputs\apk\universal\debug\app-universal-debug.apk`（debug，x86_64，VITE_TAURI_ANDROID_API_BASE=http://10.0.2.2:8016/api/v1，含 v7 UI）；API = petaccess_visual :8016。
- 7/7 截图：01_home / 02_search / 03_place_overview / 04_map / 05_map_half / 06_map_expanded / 07_contribution（`artifacts/ui-product-craft-v7/android-fast/`）。
- 检查：NO_HORIZONTAL_OVERFLOW（每路由 scrollWidth==clientWidth）PASS；NO_CRASH（0 FATAL EXCEPTION）PASS；NO_ANR PASS；NO_RENDERER_CRASH PASS；APP_ALIVE PASS；CDP 截图 PNG magic 校验（同 RC 流程）。
- 未执行：adb kill-server / factory reset / 删 AVD / 全局 Gradle cache clear。

## 11. WINDOWS_TARGETED_SMOKE

- 环境：真实 Tauri v2 + WebView2（host 安装，远程调试 :9223）；binary = `D:\pa-fix-target-win\debug\petaccess.exe`（debug --no-bundle，VITE_TAURI_API_BASE=http://127.0.0.1:8016/api/v1，含 v7 UI）。
- 7/7 截图：01_home / 02_search / 03_place / 04_map / 05_reality / 06_evidence / 07_contribution（`artifacts/ui-product-craft-v7/windows-smoke/`）。
- 检查：DESKTOP_RAIL（`app-rail` 每路由 present）PASS；KEYBOARD/FOCUS（search input fill 实测回读 OK）PASS；NO_HORIZONTAL_OVERFLOW（每路由 0）PASS；WINDOW_CHROME（正常启动/关闭自有进程）PASS。

## 12. KNOWN_LIMITATIONS

- 环境依赖（本轮实测发现并解决）：本机 Docker Desktop 引擎无法稳定启动、原 Docker Postgres/Redis/MinIO 均不可用。已用现有 Windows pg16 二进制 + PostGIS 3.6.2 便携包（118MB 下载）+ Windows Redis 5.0.14 便携（12.6MB）+ moto S3 mock 替代；`pg_up.ps1`/`redis_up.ps1` 为会话级辅助脚本（scratch），不在仓库内。WSL 后备路径因 localhost 转发不稳定弃用。
- Visual 基线容差：craft diff 均在 2% 像素容差内，未触发快照重写；未来如提升严格度可再 promote。
- e2e 单测 h5-journey quick-confirm 依赖 Redis（Celery 队列/结果后端）；Redis 缺失时该路径响应 >5s 导致 5s expect 超时（基线代码同样复现），Redis 就绪后 189/189。
- Android/Windows 二进制在专用 ASCII worktree `D:\pa-fix` 构建（detached HEAD at 分支 SHA）；未提交 build 产物。
- td-030 / signing / Authenticode：维持原状（signing 仍 BLOCKED_SECRET / NotSigned，本轮不处理、不假签）。

## 13. TECH_DEBT

- `--pa-font-weight-regular` 等未定义 token 的引用（既有，非本轮引入；本轮未新增使用）。
- `tools/ui-oracle/compare.ts` 的 `shadowed` prop 为最小引擎扩展（DOM/computed-style 判定，非主观）。
- 会话内 moto/pg/redis 替代栈：若恢复 Docker/MinIO/Redis 可还原原配置；不影响仓库代码。
- td-030 继续 deferred。

## 14. RELEASE_STATUS

- V0207_PRODUCT_CRAFT = MACHINE_PASS
- PRODUCT_STRUCTURE = FROZEN
- UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW（Agent 不代替签字）
- V020_RC_READY = PRESERVED
- PUBLIC_RELEASE = NOT_PERFORMED
- 未创建 tag（v0.1.0 未动、无 v0.2.0）；无 GitHub Release；无商店上传；无 master merge / FF。
- 停止线已到达：机器 gate 全绿 + HUMAN_REVIEW_PACK READY，等待用户人工视觉签字。
