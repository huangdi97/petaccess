# RELEASE — v0.1.0 发布流程

本文档定义 **v0.1.0（Early Preview）** 的发布流程。
发布状态受控：**`RELEASE_V0_1_0_AUTHORIZATION`（huangdi97）未授予前，不创建 tag、不发布 GitHub Release、不伪造任何发布动作。**

## 0. 发布定位（先对齐再动手）

- v0.1.0 = **EARLY PREVIEW / TECHNICAL PREVIEW**。**不是 Public Beta，不承诺数据覆盖。**
- 当前真实数据**可能为空**（Places / Rules / RealityClaims / StaffResponses / AnimalFacilities 均可能为 0）。
- 发布说明与所有对外文案必须诚实声明以上两点；**永不声称 Public Beta 数据覆盖**。

## 1. 前置条件（全部满足才进入发布）

| # | 条件 | 状态（2026-09-24 实测） |
|---|---|---|
| 1 | 全部质量门 PASS | pytest 916/2、E2E 21、visual 47、mypy 93 files 0 errors、ruff+format PASS、engineering gate 0 FAIL、secret scan 0 findings |
| 2 | 版本 SSOT | VERSION_DRIFT = 0（package.json / tauri.conf.json / Cargo.toml 全部 = 0.1.0） |
| 3 | RC 产物存在 | `artifacts/v0.1.0/`：Windows 安装包、签名 APK、`SHA256SUMS.txt`（另存 `docs/release/`） |
| 4 | 工作树干净 | 无未提交改动（含 release 文档本身提交后） |
| 5 | 发布授权 | `RELEASE_V0_1_0_AUTHORIZATION` 已由 huangdi97 授予 |

## 2. RC 冻结

- RC 版本号：**0.1.0-rc.1**。
- 评审面：`docs/release/` 下 V010 系列报告（CODE / ARCHITECTURE / UI_UX / ADMIN / EMPTY_STATE / WINDOWS / ANDROID / SECURITY / FULL_REGRESSION）全部记录为 PASS-with-blockers。
- RC 冻结的含义：产物哈希固定，后续只允许修复性改动，不允许再改功能。

## 3. 人类授权（硬门）

- **授权变量**：`RELEASE_V0_1_0_AUTHORIZATION`
- **授权人**：huangdi97
- **时机**：必须在 **打 tag 与创建 Release 之前**完成；无授权不继续。
- 授权应落成可审计记录（DECISIONS.md / 授权文档），与发布证据一并归档。

## 4. 发布步骤

1. **提交并干净工作树**：提交全部 release 文档与产物清单，确认 `git status` 干净。
2. **配置 remote**（当前仓库无 remote，CI 因此 BLOCKED）：
   `git remote add origin <repo-url>`。
3. **打 tag**：
   ```bash
   git tag -a v0.1.0 -m "v0.1.0 Early Preview (Phase AB)"
   git push origin master --tags
   ```
4. **Release CI**（`.github/workflows/release-ci.yml`，tag `v*` 触发）自动执行：
   版本校验（tag == 0.1.0、VERSION_DRIFT=0）→ 工程门 + 后端 → 前端构建 → Windows NSIS →
   Android 签名 APK（Secrets 注入 keystore）→ SHA256SUMS。
   > 该 workflow **只产产物、不创建 GitHub Release**——发布本身仍是人工授权步骤。
5. **创建 GitHub Release**（人工，需已获授权）：
   - Tag：`v0.1.0`；标题：**PetAccess v0.1.0 — Early Preview（技术预览）**。
   - 正文必须包含：Early Preview 声明、数据可能为空声明、安装说明、校验方式、已知限制。
   - **上传资产**：
     - `PetAccess_0.1.0_x64-setup.exe`（Windows 安装包）
     - `PetAccess_0.1.0-android-universal.apk`（签名 APK）
     - `SHA256SUMS.txt`（来自 `artifacts/v0.1.0/`）
     - SBOM（Release CI 产物）
6. **标记状态**：确认后更新 `PROJECT_STATE.md`：`V0_1_0_RELEASED = YES`（否则保持 NO）。

## 5. 发布后验证（必须执行）

1. **重新下载**：从 GitHub Release 下载全部资产，而不是用本地缓存文件。
2. **校验哈希**：
   ```bash
   sha256sum -c SHA256SUMS.txt     # 或 PowerShell: Get-FileHash
   ```
   与 `artifacts/v0.1.0/SHA256SUMS.txt` 及 `docs/release/` 记录逐项一致。
3. **安装冒烟**：
   - Windows：运行安装包完成安装，启动应用，确认首页空态文案「当前还没有已发布的场所数据」与「探索地图 / 贡献线索」按钮正常。
   - Android：安装 APK（允许「未知来源」），确认启动、搜索空态、场所 404 显式错误态；`aapt2 dump permissions` 仅见 `INTERNET`。
4. **确认发布定位**：Release 正文与产品内文案均为 Early Preview，无 Public Beta 数据覆盖表述。

## 6. 禁止事项

- 未经授权创建 tag / Release / 推送。
- 伪造签名（Windows 未签名是政策，不是疏漏）。
- 在 release 中包含 demo seed / 虚构数据。
- 声称 Public Beta、完整数据覆盖或「真实地图已接入」等不实表述。
