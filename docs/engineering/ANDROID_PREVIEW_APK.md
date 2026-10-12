# Android Preview APK

PetAccess 的当前 Android 产品实现是 **`apps/client-h5 + Tauri 2`**。为了让 UI 变更不必先依赖本地构建，仓库提供独立 Preview APK 工作流：

- workflow：`.github/workflows/android-preview.yml`
- app label：**PetAccess Preview**
- package：**`com.petaccess.map.preview`**
- build：debug
- ABI：aarch64 + x86_64
- 与正式 `com.petaccess.map` 并存
- 不使用正式 release keystore
- 不得作为 Release / 商店包

Tauri CLI 的 `--config` 会把 `src-tauri/tauri.preview.conf.json` 合并到正式配置中，所以 Preview 身份不是“文件名约定”，而是实际 Android application id 隔离。

## 自动包：emulator

当前 UI 工作分支发生 Consumer/runtime 相关变更时，workflow 自动构建 Preview artifact。

API：

```text
http://10.0.2.2:8000/api/v1
```

用于 Android Emulator；`10.0.2.2` 指向宿主机。

## 真机 USB 包：usb-device

在 GitHub Actions 手动运行 **Android Preview APK**，将 `api_profile` 选择为：

```text
usb-device
```

该包使用：

```text
http://127.0.0.1:8000/api/v1
```

手机通过 USB 连接电脑后执行：

```bash
adb reverse tcp:8000 tcp:8000
```

然后启动 **PetAccess Preview**。这样实体 Android 设备可以访问电脑本地运行的 PetAccess API，又不需要为了临时预览放宽 Tauri CSP。

### 用同一套 Android FAST 验证 Preview

Android acceptance 工具默认仍验证正式包；Preview 只需要覆盖包名与设备 serial：

```powershell
$env:PETACCESS_ANDROID_PACKAGE = "com.petaccess.map.preview"
$env:PETACCESS_ANDROID_SERIAL = "<adb devices 中的目标 serial>"
python scripts/android_acceptance/m3_fast.py
```

真机 USB 模式同时保持：

```bash
adb -s <serial> reverse tcp:8000 tcp:8000
```

`PETACCESS_ANDROID_PACKAGE` 和 `PETACCESS_ANDROID_SERIAL` 只改变验收目标，不改变产品代码；未设置时仍按正式包 / 既有 owned emulator 默认值执行。

## 为什么不接受任意 API URL

当前仓库没有冻结的 Public Beta API 域名，而且 Tauri CSP 是显式 allowlist。允许 workflow 临时注入任意 URL 会造成两种假象：

1. APK 看起来支持任意公网后端，但 WebView 实际可能被 CSP 拦截；
2. 为了“让预览能连”而放宽 `connect-src`，反而降低正式运行时边界。

未来 Public Beta API 固定后，应新增明确的 `public-beta` profile，同时把该域名写入 CSP 与 runtime tests；不要恢复自由字符串 URL。

## Artifact 必须包含

- Preview APK；
- `SHA256SUMS.txt`；
- `PREVIEW_METADATA.txt`：commit、profile、API、package、签名/Release 边界。

workflow 使用 `aapt dump badging` 验证 APK 的实际 package 必须是 `com.petaccess.map.preview`，使用 `apksigner verify` 验证 debug APK 本身可安装。

Preview APK 只证明“候选安装包已生成”。它**不替代**：

- Android FAST semantic gate；
- 13-route CDP journey；
- Evidence → 系统 Back → Reality；
- 多尺寸 / 生命周期 / 网络矩阵；
- Human Visual Acceptance。
