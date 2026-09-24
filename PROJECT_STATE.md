# PROJECT_STATE.md

## Current phase
v0.1.0 Early Preview — 已发布（2026-09-24, GitHub Release v0.1.0）｜进行中：v0.2.0 M2 已完结（M2-A..M2-G，Product Experience Foundation，见 docs/v0.2/）；下一 milestone：V020_M3_CONSUMER_CORE

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
