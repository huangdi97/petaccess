# SECURITY — 安全政策

## 1. 报告漏洞

发现安全漏洞或隐私风险，请按以下方式报告：

- 当前仓库尚无公开远程，首选渠道：**GitHub Issue / Private Security Advisory**（远程建立后），
  或直接联系维护者 **huangdi97**。
- 敏感细节（POC、密钥、隐私数据）**不要**贴进公开 Issue——先私密沟通，或只给可复现的抽象描述。
- 请附上：受影响版本（如 v0.1.0）、平台（Windows / Android）、复现步骤、影响与建议。
- 我们会先确认、再修复，并在修复后披露；**请勿在修复前公开利用细节**。

## 2. 范围

当前安全承诺适用于 **v0.1.0 Early Preview** 的实测范围：

- Secret 卫生（worktree + git history 扫描）
- Tauri capabilities 授予（仅 `core:default`）
- CSP（strict：self + ipc + localhost/127.0.0.1）
- Android 权限最小化
- 签名密钥存放

## 3. 项目安全基线（v0.1.0，2026-09-24 实测）

| 项 | 状态 |
|---|---|
| Secret 扫描（worktree + history） | **0 findings** |
| Critical / High 漏洞（实测范围） | **Critical = 0 / High = 0** |
| Android 权限 | 仅 `android.permission.INTERNET`；运行时权限请求数 = 0 |
| Tauri capabilities | 仅 `core:default`（未授予 shell / fs / http 插件） |
| CSP | strict（connect-src 仅 self + ipc + localhost/127.0.0.1） |
| Android APK 签名 | release keystore 正式签名（apksigner，v2/v3 scheme 已验证） |
| Windows 安装包签名 | **未签名**（NSIS）；SmartScreen 可能警告——项目政策：**不伪造签名** |
| 签名 keystore | `~/.petaccess-keystore/`，**不在 Git 仓库内**；CI 通过 Secrets 注入 |
| 依赖扫描（pip-audit） | 已运行；结果待回填复核（不属于本次 PASS 断言范围） |

## 4. Secret 处理政策

- **绝不 commit**：API key、private key、production credentials。
- Release keystore 与密码只存在于 Git 之外（用户目录 / CI Secrets），并须离线备份
  （keystore 丢失 = 已发布 APK 无法更新）。
- PR CI 与 Release CI 强制运行 `scripts/scan_secrets.py`（worktree + git history）。
- 日志禁止记录：password、token、secret、完整隐私正文。

## 5. 已知限制（诚实声明）

- v0.1.0 为 **Early Preview**：真实数据可能为空；未收录 ≠ 没有规则，空数据不等于安全保证。
- 地图、AI/OCR、存储、通知等外部能力在开发环境为 mock/local 实现；生产接入需重新评审。
- 依赖漏洞扫描结果待回填复核（见上表）。
