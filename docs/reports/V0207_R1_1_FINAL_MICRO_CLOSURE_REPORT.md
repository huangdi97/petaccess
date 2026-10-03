# V0207_R1_1_FINAL_MICRO_CLOSURE_REPORT

Round: **v0.2.7-R1.1 — Final Micro Closure（Human Review Integrity / Rail Micro-Closure / Git Truth）**

## 1. Identity

- PROJECT = PetAccess（Place Animal Coexistence Intelligence）
- BRANCH = `feat/ui-product-craft-v7-runtime-final`（自 origin/feat/ui-product-craft-v7-runtime-closure 创建，无 merge/rebase/force）
- BASE_HEAD = `42ed4e34158a566b2574b7176d3d12ddf12a20e1`（重新 fetch 后 origin/master）
- V7_HEAD = `346abbd378e519b44f08a16557cd0b62216c9843`（origin/feat/ui-product-craft-v7）
- R1_IMPLEMENTATION_HEAD = `f8c1227d861ec271f73b02281a58cbc05ac661af`（v0.2.7-R1 代码实现提交，历史头，**不是**本轮最终 HEAD）
- FINAL_BRANCH_HEAD = `__FINAL_BRANCH_HEAD__`（本轮最终提交，提交后以 `git rev-parse HEAD` 实测回填）

## 2. HUMAN_REVIEW_INDEX_FIX（P0-1）

- 根因：生成器 `tests/ui-oracle/human-review-r1.spec.ts` 中 Windows row 的 name 已带 `.png`，
  HTML 模板又追加 `.png` → `.png.png`；且 `beforePairs` 查找此前永不命中（name 带 .png 而 pair name 不带），
  命中后才暴露 `path.join(SMOKE, <object>)` 潜在 TypeError。
- 修复（生成器，不只手改 HTML）：
  - row 统一为 `logicalName`（不带扩展名），文件写 `{logicalName}.png`；
  - `WINDOWS_COPY` 复制目标由 `path.join(OUT, to)` 改为 `path.join(OUT, `${to}.png`)`；
  - before/after 模板改为 `before?.before`（字符串路径）；
  - 输出目录改为 `artifacts/ui-product-craft-v7-runtime-final/HUMAN_REVIEW`。
- 新增 referential-integrity gate：解析生成 HTML 全部 `<img src>`，逐个 `existsSync` 校验，
  `expect(missingImages).toHaveLength(0)` + `expect(pngPngCount).toBe(0)`（该 gate 在本轮
  实际暴露了复制目标缺 `.png` 的问题并被修复——rev-string integrity gate 生效）。
- 结果：`HUMAN_REVIEW_INDEX_REFERENTIAL_INTEGRITY = PASS`（7/7 img src 全部 resolve，0 个 `.png.png`）。

## 3. RAIL_TOOLTIP_FIX（P0-2）

- 移除被 `overflow-x: hidden` 裁掉的自定义外置 tooltip：`.desktop-rail__tip` DOM span、
  `.desktop-rail__tip` CSS、`:hover/:focus-visible` 显示规则、`rail-tip-in` animation 全部删除（DesktopRail.vue 中 0 命中）。
- 6 个导航 RouterLink（首页/搜索/地图/贡献/我的/设置）均保留 `:aria-label` 并新增 `:title`（原生 tooltip）。
- 横向 overflow 硬 Gate 不回退：`.desktop-rail { overflow-x: hidden; }` 仍在；
  oracle `DESKTOP_RAIL_NO_HORIZONTAL_OVERFLOW` 逐页断言 7 路由通过（427/0/0 内含）。
- Windows 真实 runtime 逐页实测 `rail.scrollWidth 67 <= clientWidth 67`（9→7 路由 targeted，全部 PASS）。

## 4. RAIL_FOOTER_FIX（P0-3）

- 68px rail 底部可见文本改为 compact version only = **`v0.2`**（`compactVersion = version.split("-")[0].split(".").slice(0,2).join(".")`）。
- 移除可见两行工程 metadata（`PetAccess v0.2.0-dev` / `development|production`）；
  完整版本+环境信息保留于 accessible metadata：`:title="PetAccess v{version} · {env}"` +
  `data-version` + `data-env`。
- e2e `navigation.spec.ts` 断言同步为 compact 契约：`toContainText(/^v\d+\.\d+$/)`（189/189 全绿）。
- 实测：`footerVisibleText = "v0.2"`、`footerTitle = "PetAccess v0.2.0-dev · production"`、
  `data-version = "0.2.0-dev"`、`data-env = "production"`；
  visible 中 0 个 `PetAccess…` / `production` / `development`。

## 5. WINDOWS_TARGETED_RESULTS

环境（沿用上一轮）：真实 Tauri v2（debug --no-bundle）+ host WebView2（CDP :9223），
二进制 `D:\pa-fix-target-win\debug\petaccess.exe`（在 ASCII worktree `D:\pa-fix` 于本轮 commit 重建，
`VITE_TAURI_API_BASE=http://127.0.0.1:8016/api/v1`，`CARGO_TARGET_DIR=D:\pa-fix-target-win`）；
API = `scripts/dev_api_server.py --db-name petaccess_visual --role VISUAL --port 8016`（pg16+PostGIS @ 127.0.0.1:55432）。
驱动：`chromium.connectOverCDP("http://127.0.0.1:9223")`，逐页断言真实 DOM state（route/page/state/fixture/h1）。

| Shots | State integrity | rail client/scroll | rail overflow | Contribution layout |
|---|---|---|---|---|
| 04_map | PASS（map/ready/map-ready-v1/规则地图） | 67 / 67 | PASS | — |
| 07_contribution_choose | PASS（contribution/choose-type/…-choose-type-v1/你刚刚知道了什么？） | 67 / 67 | PASS | **wide**（mainX 98 / mainW 664 / contextX 810 / contextW 280 / sameRow=true） |
| 08_contribution_step1 | PASS（contribution/step-1/…-step-1-v1/现场贡献） | 67 / 67 | PASS | **wide**（sameRow=true） |
| 09_contribution_step2 | PASS（contribution/step-2/…-step-2-v1/现场贡献） | 67 / 67 | PASS | **wide**（mainX 92 / mainW 661 / contextX 801 / contextW 280 / sameRow=true） |
| 05_desktop_rail_closeup | PASS（home/ready/home-ready-v1） | 67 / 67 | PASS | — |

- Rail closeup 截图 95×950（DPR 1.25，clip 76×760 CSS）真实内容：DOM 校验 PA 品牌块 + 6 个 icon 链接 +
  compact `v0.2`；可见 0 个横向 scrollbar / `PetAccess…` / `production` / `development`。
- Tooltip 检查（真实 runtime）：hover 首页 icon 后验证 DOM `title="首页"` + `aria-label="首页"`；6 个导航项
  `navTitles`/`navAriaLabels` 全等（首页/搜索/地图/贡献/我的/设置）。原生 OS tooltip 无法被截图，
  以 DOM title/aria-label 存在为准（规格 §23 允许路径）。
- 窗口：innerWidth 1120 / innerHeight 760（默认窗口契约保持）；documentClientWidth == documentScrollWidth（无文档级横向溢出）。
- 产物：`artifacts/ui-product-craft-v7-runtime-final/windows-smoke/`（5 PNG + 5 JSON + SMOKE_METADATA.json + before 对照 2 张）。
- `WINDOWS_TARGETED_RESULTS = 5/5 PASS`。

## 6. HUMAN_REVIEW

`artifacts/ui-product-craft-v7-runtime-final/HUMAN_REVIEW/`（重新生成）：
01_windows_map / 02_windows_contribution_choose / 03_windows_contribution_step1 /
04_windows_contribution_step2 / 05_desktop_rail_closeup（真实 WebView2 targeted refresh）+
06_web_contribution_1440（WIDE）/ 07_web_contribution_compact（COMPACT，web）+ HUMAN_REVIEW_INDEX.html
（Windows Map / Contribution BEFORE/AFTER 对照：BEFORE 取自 v7 runtime 既有截图）。
每张 metadata 全部来自真实 DOM；`HUMAN_REVIEW_INDEX_REFERENTIAL_INTEGRITY = PASS`（7/7、0 `.png.png`）。

## 7. WEB_GATES（本轮实测）

| Gate | Result |
|---|---|
| prettier --check | PASS（exit 0） |
| eslint . | 0 issues（exit 0） |
| client-h5 vue-tsc + build | PASS（exit 0） |
| admin build（vue-tsc + build） | PASS（exit 0） |
| ui-oracle probe（--workers=1） | 19 passed / 0 failed / 11 skipped |
| ui-oracle compare | **427 PASS / 0 WARN / 0 FAIL** |
| ui-reconstruction | **180/180** |
| Playwright e2e | **189/189** |
| visual regression（compare，Stage A，不更新 snapshot） | **59/59**（rail footer strip 差异低于 2% 容差；admin 0 变更） |

## 8. BACKEND_IMPACT

- `git diff origin/feat/ui-product-craft-v7-runtime-closure...HEAD -- services/` = 空
  → `BACKEND_CODE_CHANGED = NO`、`BACKEND_FULL_RERUN = NOT_REQUIRED`。

## 9. ANDROID_IMPACT

- 本轮只改 DesktopRail / Human Review 生成器 / navigation e2e 断言 / docs / artifacts，
  未触碰 Contribution layout（`ContributeView.vue` 无改动）
  → `ANDROID_RERUN = NOT_REQUIRED`，保留上一轮 targeted evidence。

## 10. GIT_TRUTH

- 工作前重新 `git fetch origin` 核验：
  - origin/master = `42ed4e34…`、origin/feat/ui-product-craft-v7 = `346abbd3…`、
    origin/feat/ui-product-craft-v7-runtime-closure = `7d4772e7…`（与规格参考一致）。
- 创建分支 `feat/ui-product-craft-v7-runtime-final`（基点 origin/feat/ui-product-craft-v7-runtime-closure）。
- `git rev-list --left-right --count origin/master...HEAD` = **0 / 9**（after docs commit 后为 0 / 10）。
- `git rev-list --left-right --count origin/feat/ui-product-craft-v7...HEAD` = **0 / 5**（after docs commit 0 / 6）。
- 全程无 force push / merge commit / shared rebase（仅本地提交，未 push）。
- WORKTREE 状态：主仓库 + `D:\pa-fix`（构建 worktree）均 clean于各自 commit；
  `D:\pa-fix` 保留 stash `r1-worktree-leftovers-r111-session`（v7/R1 遗留本地改动的只读保留，不恢复）。

## 11. BASELINE_STATUS

- **NOT_PROMOTED**：canonical visual baseline 未更新（Stage A——human sign-off 前不 promotion）。
- visual regression 59/59 通过（体积占比低于 2% 的 sub-threshold 差异：rail footer strip）。
- 人工 PASS 后将：force recapture 受影响 consumer snapshots → canonical baseline = R1.1 批准外观 →
  visual compare ×2 → docs truth final → FF master。

## 12. RELEASE_STATUS

- `V0207_R1_1_MICRO_CLOSURE = MACHINE_PASS` · `HUMAN_REVIEW = READY` ·
  `WINDOWS_RAIL_OVERFLOW / TOOLTIP / FOOTER = PASS` · `HUMAN_REVIEW_INDEX = PASS` ·
  `WINDOWS_CONTRIBUTION_COMPOSITION = PASS` · `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` ·
  `MASTER = UNCHANGED`（42ed4e34 未动）· `v0.1.0` tag 未动 · 无 `v0.2.0` tag / Release / store upload。
- 停止线已到达：机器 gate 全绿 + HUMAN_REVIEW READY，**等待用户人工视觉签字**；
  Agent 不代替 `UI_HUMAN_VISUAL_ACCEPTANCE = PASS`。签字后才执行 baseline promotion + fast-forward master。