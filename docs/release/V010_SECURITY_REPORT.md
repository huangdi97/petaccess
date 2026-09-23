# V010 SECURITY REPORT — 2026-09-24

> 状态标记 (Status Legend): **CURRENT VERIFIED** 本会话(2026-09-24)实际执行并核验 | **HISTORICAL** 此前会话执行、本轮未重跑 | **NOT RERUN** 未重跑(原因已注明) | **BLOCKED** 无法执行(原因已注明)

## 状态总表 (Status Table)

| 项 | 结果 | 标记 |
|---|---|---|
| Secret scan（worktree + history） | 0 findings | CURRENT VERIFIED |
| Tauri capabilities | 仅 `core:default`（default.json） | CURRENT VERIFIED |
| CSP | strict（self + ipc + localhost/127.0.0.1） | CURRENT VERIFIED |
| Android 权限 | 仅 INTERNET | CURRENT VERIFIED |
| 签名 keystore 位置 | `~/.petaccess-keystore/`，不在 Git | CURRENT VERIFIED |
| DEPENDENCY_SCAN（pip-audit / pnpm audit） | 0 known vulnerabilities（pip-audit: No known vulnerabilities found；pnpm audit --prod: 0） | CURRENT VERIFIED |



## 1. 实测面（CURRENT VERIFIED）

- Secret scan：worktree + git history 0 findings。
- Tauri：capabilities `default.json` 仅 `core:default`（未授予 shell / fs / http 插件）。
- CSP：strict，connect-src 仅 self + ipc + localhost/127.0.0.1。
- Android：manifest 仅 `android.permission.INTERNET`，runtime permissions 0。
- 签名密钥：release keystore 位于用户目录 `~/.petaccess-keystore/`，不在 Git 仓库内。

## 2. Critical / High 立场
- **DEPENDENCY_SCAN（CURRENT VERIFIED）**：pip-audit 对 services/api + services/worker 依赖树 → "No known vulnerabilities found"（仅跳过本地未发布包 petaccess-api/worker）；pnpm audit --prod → "No known vulnerabilities found"。Critical=0 / High=0。
- 对上述实测面（含依赖扫描），未发现 Critical / High 级问题（Critical=0 / High=0，仅限本报告实测范围）。

## 3. 范围声明

- 本 PASS 结论适用于 v0.1.0 范围（secret 卫生 / capability 授予 / CSP / 权限最小化 / 密钥存放 / 依赖扫描）。

## 4. 结论

**结论: SECURITY = PASS（v0.1.0 scope）** — 含依赖扫描（pip-audit / pnpm audit 均为 0 known vulnerabilities）。
