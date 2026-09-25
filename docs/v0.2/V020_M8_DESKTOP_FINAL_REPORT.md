# V020 M8 DESKTOP_FINAL — Report

Status: V020_M8_DESKTOP_FINAL — 本轮实测完成（M8 Contract 批准后执行；三拍板点：①Playwright 视口+deviceScaleFactor 模拟 9 组 DPI + 真实壳 release 构建/安装冒烟 ②重建 v0.2 桌面产物并留存 artifacts/v0.2 ③Android 模拟器冒烟并入 M8）
Last updated: 2026-09-25
基线：M7 已提交（HEAD `80bbc52`）；M8 全部改动在本轮真实实测后落盘。

## 1. 按验收项逐条状态（证据 = 本轮实际执行）

### A. Windows DPI 矩阵 QA（M2 §7 延期项收口）
- **A1 9 组 DPI 模拟矩阵 — PASS**：新增 `tests/e2e/desktop-dpi.spec.ts`，
  覆盖 M2 契约的三物理分辨率（1280×720 / 1440×900 / 1920×1080）× DPI
  100/125/150%，按 `physical / scale` 换算逻辑 CSS 视口并用
  `deviceScaleFactor = scale` 模拟缩放（1280@150%→853×480、1440@125%→1152×720、
  1920@125%→1536×864 等 9 组）。每 cell × 6 主页面（home/search/map/place/
  contribute/mine）共 **54 条**，断言：渲染非空、无横向溢出
  （scrollWidth ≤ innerWidth+1）、≥768px 逻辑宽度下 desktop-rail 可见且
  mobile-tabbar 不存在、`devicePixelRatio` 实际等于 cell.scale（防静默跑在
  1.0）。实测 **54 passed**。
- **A2 真实壳构建 — PASS**：`tauri build`（vcvars MSVC 环境 + pnpm exec）
  成功产出 `petaccess.exe`（release, 1m25s）+ NSIS 安装包
  `PetAccess_0.1.0_x64-setup.exe`；前端为 M2–M7 全量（dist 重建含贡献向导）。
- **A3 安装冒烟 — PASS**：静默安装 exit 0 → `%LOCALAPPDATA%\PetAccess\`
  出现 petaccess.exe + uninstall.exe → launch 存活（pid 3000，工作集 24.2MB）
  → 进程树确认 **msedgewebview2.exe 直接子进程（渲染确认，非空壳）** →
  relaunch 存活（pid 44908 + WebView2 子进程 44852）→ uninstall exit 0，
  目录移除、无残留进程。
- **A4 局限如实记录 — PASS**：headless 下未切换真实显示器 DPI（Win32 title
  lookup 不可靠，V010_DESKTOP_REPORT 已记录）；9 组矩阵为 Playwright 模拟 +
  真实壳构建/安装冒烟的组合，不以「真机 DPI 切换」声明。

### B. 桌面产物归档
- **B1 artifacts/v0.2 留存 — PASS**：`PetAccess_v0.2-desktop_x64-setup.exe`
  （1,970,372 B，SHA256 `be1e8c6a…`）+ `SHA256SUMS.txt`（双产物逐项）；
  Android 产物见 C。
- **B2 产物与版本 — PASS**：安装包 version 沿用 0.1.0（tauri.conf 未改；
  v0.2.0 正式发布轮再升版本号），文件名以 v0.2 前缀区分里程碑。

### C. Android 模拟器冒烟（并入 M8）
- **C1 APK 构建 — PASS**：worktree `C:\petaccess-worktree` reset 至 master
  （80bbc52），`tauri android build --apk --target x86_64` 产出
  `app-universal-release-unsigned.apk`（11.03 MB）；`sdkmanager` 补装
  `platforms;android-36` + `build-tools;36.0.0`（compileSdk 36 所需）。
- **C2 签名 — PASS**：apksigner（build-tools 36.0.0）用 release keystore
  （`~/.petaccess-keystore`，密码读自 keystore-password.txt）签名，
  verify 证书 DN=CN=PetAccess、SHA-256 `e5f7761c…`。
- **C3 模拟器冒烟 — PASS**（Android 15 API 35, emulator petaccess_api35，
  headless swiftshader）：install Success → launch COLD Status ok、pid 存活 →
  截屏 1080×2340 **2743 色 / 品牌蓝 #34617E + 文本色，真实渲染** →
  force-stop 后 pid 0 → relaunch Status ok、截屏 2753 色（渲染一致）→
  uninstall Success、包移除。产物 `PetAccess_v0.2-android-universal.apk`
  （SHA256 `c1600cc9…`）入 artifacts/v0.2。
- **C4 边界 — PASS**：仅模拟器冒烟（install/launch/渲染/relaunch/uninstall），
  未做 360/390/430 真机矩阵（属 M9，本轮不跨）。

### D. Engineering Gates（全绿，实测）
- **D1**：`check_engineering_quality.py` **0 FAIL**（60 REVIEW / 34 WARN）；
  ruff check PASS；ruff format（含 docs）PASS；mypy 96 files / 0 errors。
- **D2**：backend 全量回归重跑：DISCOVERED 947 = **945 passed / 2 skipped /
  0 failed**（50.5s；TEST DB + Celery worker 同命令存活）。
- **D3**：`pnpm lint:fe` PASS（desktop-dpi.spec.ts 入 typescript-eslint
  default project，匹配数 21 > 旧硬上限 20 → 上限调至 25，非豁免/忽略）；
  `pnpm format:check:fe` PASS；client-h5 build PASS；admin 未触及。
- **D4**：Playwright visual **59 passed**（compare 全绿，M8 无视觉基线变更）；
  Playwright e2e 全量 **144 passed / 0 failed**（90 存量 + 54 新增 DPI 矩阵）。
- **D5**：零新增 ignore / exemption / ts-ignore；`eslint.config.js` 仅放宽
  projectService 文件匹配上限（20→25，注释说明为新增测试文件的必要容量）。

### E. 交付
- **E1 本报告落盘**（此文件）。
- **E2**：PROJECT_STATE.md 更新为 M7 完结 + M8 完结；Android 真机矩阵仍属
  M9；无新架构决策。
- **E3 产物**：artifacts/v0.2/ 三件（desktop exe + android apk + SHA256SUMS.txt）。

## 2. 本轮新增/变更文件

- 新增：`tests/e2e/desktop-dpi.spec.ts`（9 组 DPI × 6 页面 = 54 条）、
  `artifacts/v0.2/PetAccess_v0.2-desktop_x64-setup.exe`、
  `artifacts/v0.2/PetAccess_v0.2-android-universal.apk`、
  `artifacts/v0.2/SHA256SUMS.txt`（构建产物，不 commit 二进制）。
- 修改：`eslint.config.js`（projectService 上限 20→25）。
- 壳配置审计：`tauri.conf.json`（窗口 1000×760 / min 640×480、CSP
  deny-by-default、capabilities 仅 core:default）复核无需变更。

## 3. 契约状态表（artifact / QA / gates / docs）

| 能力 | 结果 | 证据 |
|---|---|---|
| DPI 矩阵（3 分辨率 × 3 DPI） | IMPLEMENTED | desktop-dpi 54 passed（模拟+DSF 断言） |
| 桌面壳 release 构建 | IMPLEMENTED | tauri build 1m25s PASS |
| 安装冒烟（install/launch/relaunch/uninstall） | IMPLEMENTED | 进程树 + WebView2 子进程确认 |
| v0.2 桌面产物归档 | IMPLEMENTED | artifacts/v0.2 + SHA256SUMS |
| Android 模拟器冒烟（并入） | IMPLEMENTED | install/launch/渲染/relaunch/uninstall PASS |
| 门禁全量 | IMPLEMENTED | D1–D5 全绿（945 pytest / 144 e2e / 59 visual） |

状态词仅允许 IMPLEMENTED / PARTIAL / MISSING / NOT_WIRED / NOT_TESTED。

## 4. 边界遵守

- 桌面 QA 为 Playwright 视口+DSF 模拟 + 真实壳构建/安装冒烟组合（用户拍板点
  ①）；未伪造真机 DPI 切换。
- Android 仅并入模拟器冒烟（用户拍板点 ③）；360/390/430 真机矩阵属 M9。
- 未改 tauri.conf 版本号（v0.2.0 正式发布轮再升）；未扩 scanner；未重做
  M2–M5/M7；M6 空缺。
- `eslint.config.js` 上限调整非豁免/忽略——21 个 default-project 文件仍全部
  被 lint（上限放宽后 `npx eslint .` 0 error）。
- 构建产物（exe/apk）不入 Git，仅留 checksum；分片提交：M8-A（spec+config）
  + M8-D（报告与状态）。

**Overall: V020_M8_DESKTOP_FINAL = PASS**（A1–A4 / B1–B2 / C1–C4 / D1–D5 /
E1–E3 全部实测通过）。
