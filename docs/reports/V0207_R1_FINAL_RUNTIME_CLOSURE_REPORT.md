# V0207_R1_FINAL_RUNTIME_CLOSURE_REPORT

Round: **v0.2.7-R1 — Final Runtime Craft Closure（MINIMAL_RUNTIME_VISUAL_FIX）**

## 1. Identity

- PROJECT = PetAccess（Place Animal Coexistence Intelligence）
- BRANCH = `feat/ui-product-craft-v7-runtime-closure`
- BASE_HEAD = `42ed4e34158a566b2574b7176d3d12ddf12a20e1`（轮开始时 fetch 后的 origin/master）
- V7_HEAD = `346abbd378e519b44f08a16557cd0b62216c9843`（origin/feat/ui-product-craft-v7；比规格参考 SHA `c7f06df4…` 多 1 个 docs 提交，仍为 v7 线）
- R1_HEAD = `f8c1227d861ec271f73b02281a58cbc05ac661af`（本轮代码/证据提交）
- WORKTREE_STATUS = clean（报告提交后）

## 2. WINDOWS_RUNTIME_METRICS

真实 Tauri v2（debug --no-bundle）+ host WebView2（CDP :9223），二进制 `D:\pa-fix-target-win\debug\petaccess.exe`，
API = petaccess_visual @ 127.0.0.1:8016。测量先于任何 breakpoint 假设（不猜）。

| 指标 | BEFORE（v7 UI，1000 默认窗） | AFTER（R1，1120 默认窗） |
|---|---|---|
| window.innerWidth / innerHeight | 1000 / 760 | **1120 / 760** |
| devicePixelRatio | 1.25 | 1.25 |
| visualViewport.width | 984.8 | ~1105 |
| screen（CSS） | 2048×1152 | 2048×1152 |
| document clientWidth / scrollWidth | 985 / 985 | ~1105 / ~1105 |
| rail clientWidth / scrollWidth | 68 / **104**（overflow=1，全路由） | 68 / **67**（overflow=0，全路由） |
| contribution layoutMode | **compact**（choose/step1/step2） | **wide**（choose/step1/step2） |

完整逐路由数据：`artifacts/ui-product-craft-v7-runtime-closure/windows-runtime-metrics.json`（perRouteAfter 9 条）。

## 3. RAIL_ROOT_CAUSE / RAIL_FIX / RAIL_GATE

**Root cause（实测）**：`.desktop-rail` 为 68px icon rail 且 `overflow-y: auto`（x 轴按 CSS 规则计算为 auto）。
两个内容源撑出横向 scrollable overflow：
1. footer `PetAccess v0.2.0-dev` / `development` 文本（约 104px > 68px）；
2. **隐藏的 hover tooltip**（`position: absolute; left: 100% + 8px`，opacity:0 但仍计入 rail 的
   scrollable overflow region，实测 group.scrollWidth=104）。
两者叠加使 rail 底部出现横向 scrollbar（left arrow / thumb / right arrow）。

**Fix（最小实现）**：
- `overflow-x: hidden`（视觉 clamp）；
- footer span：`max-width:100% + overflow:hidden + text-overflow:ellipsis + white-space:nowrap`，
  content 不再撑宽 rail（scrollWidth 67 == clientWidth 67）；版本信息保留 DOM + `:title` 可访问；
- hover tooltip 默认 `display: none`（实测为唯一能让 scrollable overflow 归零的可靠手段），
  hover/focus 时 `display: block` + `rail-tip-in` 淡入动画；
- rail 仍为 68px icon rail：无扩宽、无常驻标签、不移位、版本不从 DOM 移除。

**Gate**：
- `DESKTOP_RAIL_NO_HORIZONTAL_OVERFLOW`：`rail.scrollWidth <= rail.clientWidth + 1`，global 契约
  7 页全查（`docs/ui/contracts/json/global.json`），oracle 引擎新增 `hOverflow` prop + probe
  scrollWidth/clientWidth 采集（probe.ts / oracle.spec.ts / compare.ts / contracts.ts）；
- 通用 nested check：`CONTRIBUTION_WORKSPACE/MAIN/CONTEXT_NO_HORIZONTAL_OVERFLOW`
  （`docs/ui/contracts/json/contribution.json`）；
- Windows 真实 runtime 9 路由逐条 `railNoHorizontalOverflow = PASS`。

## 4. CONTRIBUTION_BREAKPOINT_ROOT_CAUSE / FINAL_BREAKPOINT_MODEL

**Root cause（实测）**：默认窗口 CSS viewport = 1000（< 1024），`@media (min-width:1024px)` 永不命中；
而 nav desktop 自 768 起（useBreakpoint lg）。分层不一致 + 默认窗口偏窄 → 双栏退化纵向。
可用内容宽 = viewport − rail(68) − page padding(≈40) − 滚动条(≈15) ≈ viewport − 123；
设计 workspace（main 680 + gap 48 + context 280 = 1008）需要内容 ≥ 1008 → viewport ≥ ~1131；
main ≥ 620（oracle 下限）需 viewport ≥ ~1056。

**FINAL_BREAKPOINT_MODEL（测量驱动，写入代码注释与 tauri.conf）**：
- **COMPACT_DESKTOP = 768 ≤ CSS viewport < 1120**：rail + 单栏 task（context rail 不并排，不硬塞两栏）。
- **WIDE_DESKTOP = CSS viewport ≥ 1120**：rail + main|context 双栏（main 620–680 / gap 48 / context 280）。
- 默认窗口小幅上调 `tauri.conf.json width 1000 → 1120`（+12%，非最大化/非超宽；screen 2048 余量充足），
  使真实默认 Windows 窗口落在 WIDE 且完整呈现已批准的 v7 构图（实测 main≈664/context 280）。

## 5. CONTRIBUTION_RUNTIME_COMPOSITION_MODE

- 判定条件（wide）：`main.right < context.left` **且** 垂直重叠 > 0（两盒共享水平条带 = 真并排；
  规格中的 “>50%” 启发式在 step-2 的自然几何下不成立——表单主列很高（1046px）、context rail 较短（322px），
  重叠比 0.31 但真实并排；compact（context.top >= main.bottom）仍被显式捕获并记录，绝不静默）。
- 实测（默认 Windows 窗口，真实 runtime）：choose / step1 / step2 全部 wide；
  mainX≈98–92、mainWidth 661–664、contextX 801–810、contextWidth 280、sameRow=true、重叠 0.31–0.74。
- Windows smoke `CONTRIBUTION_RUNTIME_COMPOSITION_MODE = PASS`。

## 6. WINDOWS_RUNTIME_RESULTS

`artifacts/ui-product-craft-v7-runtime-closure/windows-smoke/`（9 路由 PNG + per-page JSON +
`SMOKE_METADATA.json` 升级字段：innerWidth/innerHeight/devicePixelRatio/visualViewportWidth/
documentClientWidth/documentScrollWidth/railClientWidth/railScrollWidth/layoutMode；
contribution 页另含 mainX/mainWidth/contextX/contextWidth/sameRow/verticalOverlapRatio）：

- WINDOW_CHROME = PASS；DESKTOP_RAIL_PRESENT = PASS；
- **DESKTOP_RAIL_NO_HORIZONTAL_OVERFLOW = PASS**（9/9，rail 67/68）；
- **CONTRIBUTION_RUNTIME_COMPOSITION_MODE = PASS**（3/3 wide）；
- STATE_INTEGRITY = PASS（9/9 真实 DOM state）；NO_DOCUMENT_HORIZONTAL_OVERFLOW = PASS。

BEFORE/AFTER：`04_map_before.png` / `07_contribution_choose_before.png`（v7 UI，rail scrollbar + compact 可见）
与 `04_map.png` / `07_contribution_choose.png` 并排入人审包。

## 7. ANDROID_IMPACT

- 修改了 ContributeView CSS media query（1024 → 1120）→ 按规格补跑 **Android Contribution targeted
  smoke（仅 choose + step1）**：真实 emulator-5554 / AVD main（x86_64 debug APK，含 R1 UI），
  CDP 驱动（`artifacts/ui-product-craft-v7-runtime-closure/android-contribution-smoke/`）：
  choose-type / step-1 均 PASS，document overflow = 0（inner=412 CSS，dpr=2.625）。Map 未重跑、未做全量 FAST。
- 浏览器 responsive gates：ui-reconstruction ui-360 + ui-430 contribution tests PASS、e2e responsive
  （390/430 等 8 断点）PASS → 430/390/360 无 Contribution regression。

## 8. WEB_GATES（本轮实测）

| Gate | Result |
|---|---|
| vue-tsc（client-h5 build） | PASS |
| client-h5 build | PASS |
| admin build（vue-tsc + build） | PASS |
| eslint | 0 issues |
| prettier --check | PASS |
| ui-oracle（compare） | **427 PASS / 0 WARN / 0 FAIL**（≥ 423；+4 = 新增 rail/nested gates） |
| ui-language | 29 pages FAIL=0 |
| ui-density | 28 rows FAIL=0 |
| ui-reconstruction | **180/180** |
| Playwright e2e | **189/189** |
| visual regression（compare，Stage A 不更新 snapshot） | **59/59**（rail strip diff 远低于 2% 容差；admin 0 变更） |
| backend pytest | BACKEND_CODE_CHANGED = NO（`git diff origin/feat/ui-product-craft-v7...HEAD -- services/` 为空）→ **BACKEND_FULL_RERUN = NOT_REQUIRED** |

## 9. HUMAN_REVIEW

`artifacts/ui-product-craft-v7-runtime-closure/HUMAN_REVIEW/`：
01_windows_map / 02_windows_contribution_choose / 03_windows_contribution_step1 /
04_windows_contribution_step2 / 05_desktop_rail_closeup（真实 WebView2 runtime）+ 
06_web_contribution_1440（WIDE）/ 07_web_contribution_compact（COMPACT，web）+
HUMAN_REVIEW_INDEX.html（Windows Map / Contribution BEFORE/AFTER 对照）。
每张 metadata actual 来自真实 DOM（route/page/state/fixture/h1；windows 页另含 rail/composition 实测）。
状态：`V0207_R1_RUNTIME_CLOSURE = MACHINE_PASS`、`HUMAN_REVIEW = READY`；
`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`（Agent 不代替签字）。

## 10. BASELINE_STATUS

- canonical visual snapshot：**未更新**（Stage A 规则——先 runtime closure → 人工视觉 PASS → 再真正 promotion）。
- visual regression 59/59 通过（2% 容差内 sub-threshold 差异：rail 底条 ~68×40px 变化，远低于阈值）。
- 人工 PASS 后将强制重新 capture 受影响的 consumer snapshots（Map / Contribution / rail 可见的 desktop 页），
  Admin 0 changes，视觉 compare ×2 59/59。

## 11. GIT_STATUS

- 分支 `feat/ui-product-craft-v7-runtime-closure`，基点 origin/feat/ui-product-craft-v7（346abbd），
  ahead=4 / behind=0 关系保持；R1 提交 `f8c1227`（代码 + 证据）。
- origin/master = `42ed4e34` **UNCHANGED**；v0.1.0 tag 未动；无 v0.2.0 tag / Release / store。
- 无 force push / 无 merge commit / 无 rebase。

## 12. RELEASE_STATUS

- `V0207_R1_RUNTIME_CLOSURE = MACHINE_PASS` · `WINDOWS_RAIL_OVERFLOW = PASS` ·
  `WINDOWS_CONTRIBUTION_COMPOSITION = PASS` · `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` ·
  `MASTER = UNCHANGED` · `PUBLIC_RELEASE = NOT_PERFORMED` · `AWAITING_RELEASE_AUTHORIZATION = YES`。
- 停止线已到达：机器 gate 全绿 + HUMAN_REVIEW READY，等待用户人工视觉签字。
  签字并授权后（Stage B）：canonical baseline promotion → `git push origin HEAD:master`（仅 fast-forward）。
