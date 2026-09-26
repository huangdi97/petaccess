# F04: v0.1.0 → HEAD 变更地图 (V010_TO_HEAD_CHANGE_MAP)

- 范围: `v0.1.0` = c84b4cf  ..  `HEAD` = 5af2bdb (branch master)
- M1 基线: fa328e0 (`v0.2.0 M1 §40`) — 用于 changed_since_M1 对比
- commit 数: 20；git diff --name-status v0.1.0..HEAD 文件数: 212
- 生成时间: 2026-09-26 12:14:30 +08:00

## 1. 逐 commit 表 (`git log --oneline --decorate v0.1.0..HEAD`)

| sha | subject | 文件数（分类明细） | risk |
|---|---|---|---|
| 5af2bdb | M8-D: V020_M8_DESKTOP_FINAL report + PROJECT_STATE M8 基线 ` (HEAD -> master)` | 2 (DOC_ONLY:2) | LOW |
| 0856dc5 | M8-A: Windows DPI matrix QA — desktop-dpi spec (54 cases) | 2 (BUILD_CONFIG:1 TEST_ONLY:1) | MEDIUM |
| 80bbc52 | M7-D: V020_M7_CONTRIBUTION_UX report + PROJECT_STATE M7 基线 | 2 (DOC_ONLY:2) | LOW |
| 3491cd3 | M7-A..C: contribution wizard rebuild + history endpoint + MineView block | 18 (FRONTEND_RUNTIME:13 TEST_ONLY:3 BUILD_CONFIG:1 BACKEND_RUNTIME:1) | MEDIUM |
| 4078520 | M5-D: V020_M5_REALITY_TRACE_AND_EVIDENCE report + PROJECT_STATE M5 基线 | 2 (DOC_ONLY:2) | LOW |
| f1a9de8 | M5-A..C: Reality Trace + Evidence surface — 独立路由/深链、fact·review 分离、观察时间线、统一证据呈现、a11y | 16 (TEST_ONLY:12 FRONTEND_RUNTIME:3 BOOT_CRITICAL:1) | **HIGH** |
| 624336d | M4-D: V020_M4_MAP_AND_PASSPORT report（含 BLOCKED_EXTERNAL 记录）+ PROJECT_STATE M4 基线 | 2 (DOC_ONLY:2) | LOW |
| 87689b9 | M4-A..C: Map 桌面 split-view + 深链/状态收口 + Place Passport 收口（阅读列/证据视觉语言/统一错误）+ a11y | 20 (TEST_ONLY:16 FRONTEND_RUNTIME:3 UI_ONLY:1) | MEDIUM |
| 21566c6 | M3-E: V020_M3_CONSUMER_CORE report (acceptance-by-acceptance evidence) + PROJECT_STATE M3 baseline | 2 (DOC_ONLY:2) | LOW |
| e7ecf08 | M3-A..D: consumer route/query foundation + PlacePreview + Search desktop split-view + unified CoexistenceSnapshot consumption + wiring/a11y closure | 22 (FRONTEND_RUNTIME:14 TEST_ONLY:6 BOOT_CRITICAL:2) | **HIGH** |
| 315a99a | M2-G: visual/a11y/regression closure — 8 deliverables, engineering gate 0 FAIL, format clean, backend regression re-run, visual families green | 93 (TEST_ONLY:49 FRONTEND_RUNTIME:19 DOC_ONLY:9 UI_ONLY:8 BACKEND_RUNTIME:4 BOOT_CRITICAL:3 BUILD_CONFIG:1) | **HIGH** |
| a83b2ea | M2-F: reality/contribution gap audit + DEV_FIXTURE_MODE fail-closed + contract fixes | 6 (BACKEND_RUNTIME:3 TEST_ONLY:1 FRONTEND_RUNTIME:1 DOC_ONLY:1) | MEDIUM |
| eba0ea7 | M2-D+E: Home / Search first-round productization + domain components | 15 (FRONTEND_RUNTIME:15) | MEDIUM |
| 5fb107e | M2-C: empty/loading/error/offline foundation (V020_EMPTY_ERROR_OFFLINE_SPEC) | 6 (FRONTEND_RUNTIME:5 DOC_ONLY:1) | MEDIUM |
| 6a01cbd | M2-B: ConsumerAppShell + navigation + desktop layout (V020_APP_SHELL_SPEC) | 18 (FRONTEND_RUNTIME:11 BOOT_CRITICAL:4 TEST_ONLY:2 DOC_ONLY:1) | **HIGH** |
| 4f813b1 | M2-A: design token SSOT + base UI component family (V020_DESIGN_SYSTEM_SPEC) | 37 (UI_ONLY:36 DOC_ONLY:1) | MEDIUM |
| 3386924 | docs: PROJECT_STATE 质量基线更新为 §40 全门禁后的实测值（938 passed / gate 0 FAIL） | 1 (DOC_ONLY:1) | LOW |
| fa328e0 | v0.2.0 M1 §40: 补齐 silent-catch/magic-status/dead-code/duplicate-config 四项机器 Gate 并修复违规 | 26 (BACKEND_RUNTIME:19 BUILD_CONFIG:4 DOC_ONLY:2 TEST_ONLY:1) | MEDIUM |
| dd6994d | feat(reality): wire RealityReport parent-flow contribution API + reopen contract | 8 (BACKEND_RUNTIME:4 FRONTEND_RUNTIME:3 TEST_ONLY:1) | **HIGH** |
| 5b1dd05 | docs(release): mark v0.1.0 RELEASED — GitHub Release published + Phase AH verified (M12) ` (origin/master, origin/HEAD)` | 3 (DOC_ONLY:3) | LOW |

> risk 启发式：触碰 `src-tauri/*`、`Cargo*`、`tauri.conf`、`vite.config`、`package.json` 依赖、`router`、`AppShell`、`main.*`、全局 css 的 commit → HIGH；只动 `tests/`、`docs/`、`*.md` → LOW；其余 MEDIUM。

## 2. 变更文件分类表 (`git diff --name-status v0.1.0..HEAD`)

| 分类 | 文件数 | 代表文件 |
|---|---|---|
| BOOT_CRITICAL | 5 | M apps/client-h5/src/App.vue<br>A apps/client-h5/src/components/shell/ConsumerAppShell.vue<br>M apps/client-h5/src/main.ts<br>M apps/client-h5/src/router.ts<br>… |
| ANDROID_CRITICAL | 0 | _（无命中）_ |
| FRONTEND_RUNTIME | 57 | M apps/client-h5/src/components/RealityPanel.vue<br>A apps/client-h5/src/components/contribute/ContributeDone.vue<br>A apps/client-h5/src/components/contribute/ContributeEntry.vue<br>A apps/client-h5/src/components/contribute/ContributeObservationForm.vue<br>… |
| BACKEND_RUNTIME | 24 | M services/api/app/api/v1/auth.py<br>M services/api/app/api/v1/observations.py<br>M services/api/app/api/v1/places.py<br>M services/api/app/api/v1/reality.py<br>… |
| BUILD_CONFIG | 5 | M eslint.config.js<br>M scripts/check_engineering_quality.py<br>A scripts/engineering_quality_scan2.py<br>A scripts/engineering_quality_scan3.py<br>… |
| UI_ONLY | 36 | A apps/client-h5/src/components/ui/PaBadge.vue<br>A apps/client-h5/src/components/ui/PaBanner.vue<br>A apps/client-h5/src/components/ui/PaBottomSheet.vue<br>A apps/client-h5/src/components/ui/PaButton.vue<br>… |
| TEST_ONLY | 63 | A tests/e2e/consumer-routes.spec.ts<br>A tests/e2e/contribute-wizard.spec.ts<br>A tests/e2e/desktop-dpi.spec.ts<br>M tests/e2e/h5-shell.spec.ts<br>… |
| DOC_ONLY | 22 | M DECISIONS.md<br>M PROJECT_STATE.md<br>M docs/audit/V010_TECH_DEBT_REGISTER.md<br>A docs/audit/V020_GLOBAL_CODE_AUDIT.md<br>… |

- ANDROID_CRITICAL = 0 的说明：本区间 git 跟踪的文件没有 `src-tauri/gen` 变更（桌面/Android 栈在 v0.1.0 已就绪且此后未改）；`apps/client-h5/src-tauri/gen/android` 整目录 untracked（被自身 .gitignore 忽略），见 ALL_FILES.csv（category=android-generated，56 文件）。
- BUILD_CONFIG 说明：包含 `scripts/**`（工程门禁/质量扫描工具）与 `eslint.config.js`。

## 3. 依赖漂移 (v0.1.0 vs HEAD)

### 3.1 直接依赖版本对比

| 依赖 | 来源 manifest | v0.1.0 | HEAD | 状态 |
|---|---|---|---|---|
| vue | apps/client-h5/package.json | `^3.5.13` | `^3.5.13` | unchanged |
| vue-router | apps/client-h5/package.json | `^4.5.0` | `^4.5.0` | unchanged |
| vite | apps/client-h5/package.json | `^6.0.0` | `^6.0.0` | unchanged |
| @tauri-apps/cli | apps/client-h5/package.json | `^2.11.5` | `^2.11.5` | unchanged |
| @tauri-apps/api | apps/client-h5/package.json | `ABSENT` | `ABSENT` | unchanged |
| tauri | apps/client-h5/src-tauri/Cargo.toml | `2.11.6` | `2.11.6` | unchanged |
| tauri-build | apps/client-h5/src-tauri/Cargo.toml | `2.6.3` | `2.6.3` | unchanged |
| serde | apps/client-h5/src-tauri/Cargo.toml | `1.0` | `1.0` | unchanged |
| serde_json | apps/client-h5/src-tauri/Cargo.toml | `1.0` | `1.0` | unchanged |
| axum | apps/client-h5/src-tauri/Cargo.toml | `ABSENT` | `ABSENT` | unchanged |
| fastapi | services/api/pyproject.toml | `fastapi>=0.115` | `fastapi>=0.115` | unchanged |
| pydantic | services/api/pyproject.toml | `pydantic>=2.9` | `pydantic>=2.9` | unchanged |
| pydantic | pyproject.toml (root) | `pydantic[email]>=2.13.5` | `pydantic[email]>=2.13.5` | unchanged |

### 3.2 manifest 整体差异

- package.json (root): **unchanged**（逐字节相同）
- apps/client-h5/package.json: **unchanged**（逐字节相同）
- apps/client-h5/src-tauri/Cargo.toml: **unchanged**（逐字节相同）
- services/api/pyproject.toml: **unchanged**（逐字节相同）
- pyproject.toml (root): **unchanged**（逐字节相同）

### 3.3 锁文件

| 锁文件 | 状态 (`git diff --stat v0.1.0..HEAD`) |
|---|---|
| pnpm-lock.yaml | unchanged（无任何差异行） |
| apps/client-h5/src-tauri/Cargo.lock | unchanged（无任何差异行） |
| uv.lock | unchanged（无任何差异行） |

- 结论：v0.1.0 → HEAD 期间 **没有任何直接依赖版本变化**，三个锁文件全部 unchanged；业务改动均为源码/配置/文档层面。
