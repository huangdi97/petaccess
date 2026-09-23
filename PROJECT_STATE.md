# PROJECT_STATE.md

## Current phase
v0.1.0 Early Preview — RC 冻结（2026-09-24）

## v0.1.0 状态
- **V0_1_0_RELEASED = NO**
- **HUMAN_ACTION_REQUIRED = RELEASE_V0_1_0_AUTHORIZATION**（huangdi97）
- GitHub 阶段 BLOCKED：无 git remote；未创建 tag；未发布 Release（边界遵守，未授权不伪造）
- 发布就绪门槛全部实测 PASS（见 docs/release/V010_RELEASE_READINESS_REPORT.md）

## 质量基线（2026-09-24 全实测, CURRENT VERIFIED）
- pytest 916 passed / 2 skipped（TEST DB + Celery worker）
- ruff / format PASS；mypy services/api/app 93 files / 0 errors
- Engineering gate：0 FAIL / 58 REVIEW / 24 WARN（豁免均引用 TD-00x）
- Secret scan（worktree + history）：0 findings
- VERSION_DRIFT = 0（scripts/check_version_drift.py，含 design-tokens 0.6.0-beta.1→0.1.0 修正）
- H5 + Admin vue-tsc + build PASS；Playwright E2E 21 passed（18 + 3 empty-state）
- Visual 47 PASS（17 基线家族 × viewports；Empty-First 文案改动后基线重生成一次，compare 全绿）
- A11y：0 issues（consumer + admin 全页, 键盘焦点走查 0 invisible）
- 依赖扫描：pip-audit / pnpm audit 均 0 known vulnerabilities（Critical=0 / High=0）

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
- **RELEASE_V0_1_0_AUTHORIZATION**（唯一人类关卡）
- 授权后：加 remote → 推 master → 打 v0.1.0 tag → release-ci 跑 → 建 GitHub Release
  → 从 Release 页重下产物并校验 SHA256/签名/安装（Phase AH）
- 远期（非 v0.1.0）：真实地图 key / AI key / 数据扩充 / 商店上架

## Truth rule
Never infer PASS。
