# Changelog

版本语义：`v0.x.y`；里程碑（M0-M12）标注见提交记录与 `DECISIONS.md`。
本文件中的数字全部为**实测**，不编造。

## [0.1.0] — 2026-09-24 — Early Preview（当前版本）

v0.1.0 为 **Early Preview / 技术预览**，不是 Public Beta，不承诺数据覆盖。

### 新增

- **Tauri 2 壳**：Windows x64 NSIS 安装包（`PetAccess_0.1.0_x64-setup.exe`，未签名）+ Android 通用 APK（`PetAccess_0.1.0-android-universal.apk`，release keystore 正式签名，v2/v3 scheme）。
- **Empty-First 空态与文案**：无数据时页面完整可用——首页「当前还没有已发布的场所数据」、搜索「没有找到已收录场所」、场所 404 显式 ERROR 状态；「未收录 ≠ 没有规则」语义保持。
- **工程门与 secret 扫描**：`scripts/check_engineering_quality.py`（工程质量门）+ `scripts/scan_secrets.py`（worktree + git history 扫描）。
- **PR / Release CI**：`.github/workflows/pr-ci.yml`（工程门 → 后端 mypy+pytest → 前端 typecheck+build → E2E shell 子集）；`.github/workflows/release-ci.yml`（tag `v*` 触发：版本校验 → 质量门 → H5 构建 → Windows NSIS → Android 签名 APK → SHA256SUMS，仅产产物、不建 Release）。
- **版本 SSOT**：`scripts/check_version_drift.py`，VERSION_DRIFT = 0（全部 package.json + `tauri.conf.json` + `Cargo.toml` = 0.1.0）。

### 说明

- 当前**真实数据可能为空**（`Places` / `Rules` / `RealityClaims` / `StaffResponses` / `AnimalFacilities` 均可能为 0）——设计使然：不造数，release 不含 demo seed，不含任何虚构数据。

### 质量基线（本会话实测）

- pytest **916 passed / 2 skipped**；Playwright E2E **21 passed**（18 常规 + 3 空态）；视觉回归 **47 passed**。
- mypy **93 files / 0 errors**；ruff + format **PASS**；engineering gate **0 FAIL**；secret scan **0 findings**。

---

## [v0.9-R1] — 2026-09-20 ~ 2026-09-23 — Reality 深化（上一阶段）

- **Reality 层落地**：`RealityReport` 父模型 + 7 状态枚举 + `ObservationEffort` / `Confirmation` / `ExternalContentReference`；Reality DB final closure（8 表 / 29 FK，Alembic 无 drift）。
- **reality_contribution 服务**：防滥用（rate limit / 去重 / 旧视频拒绝 / place mismatch）；R-01 FK 确定性命名闭环。
- **前端 Reality 面**：RealityPanel / Contribute / Home / Admin Dashboard/Queue/Claims，design-token 合规。
- **安全修复**：媒体 EXIF/XMP/PNG-text 元数据剥离（ingest 时）。
- **统一 AccessAnswer**：消费者各面迁移到统一准入答复模型。
- **真实数据发布治理**（Wave01 / Wave02，huangdi97 人工审阅）：30 个真实场所 / 42 条已发布规则落入生产库；Reality 各表 0 行（**未造数**）。
- 实测基线（2026-09-23）：pytest 889 passed / 2 skipped；Playwright 18 passed；Visual 17 PASS；mypy 97 files / 0 errors；Security CRITICAL=0 / HIGH=0。

## [v0.5] — 质量冻结

- 质量基线冻结（tag `v0.5-quality-freeze`）：设计令牌统一、前端 QA、性能与覆盖率基线、演示数据全虚构隔离。

## [Unreleased] — 下一阶段

- 真实数据采集（**禁造数**）、数据许可回填、真实地图 Key、Staging / UAT / 生产部署——均需人类授权。
