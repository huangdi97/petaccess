# Android Preview APK

PetAccess 当前 Android 产品实现是 **`apps/client-h5 + Tauri 2`**。为了让 Consumer/UI 变更不必先依赖本地构建，仓库提供独立的 Preview APK 工作流。

## 1. 不变量

- workflow：`.github/workflows/android-preview.yml`
- Preview app label：**PetAccess Preview**
- Preview package：**`com.petaccess.map.preview`**
- canonical release package：**`com.petaccess.map`**
- build：debug
- Preview 与正式 App 可并存安装
- Preview 不读取正式 release keystore
- Preview 不得作为 Release / 商店包
- `apps/client`（legacy uni-app x）不参与任何当前 Android Preview / Release

Preview 身份通过 `apps/client-h5/src-tauri/tauri.preview.conf.json` 合并到正式 Tauri 配置，是真实 Android application id 隔离，不只是 APK 文件名约定。

## 2. 每次自动生成两份 Preview

当前 UI 工作分支发生 Consumer/runtime 相关变更时，workflow 用 matrix 同时构建两个 artifact。

### 2.1 emulator · x86_64

API：

```text
http://10.0.2.2:8000/api/v1
```

用于 Android Emulator；`10.0.2.2` 指向宿主机。

### 2.2 usb-device · aarch64

API：

```text
http://127.0.0.1:8000/api/v1
```

用于主流 ARM64 Android 真机。手机通过 USB 连接电脑时，以 `adb reverse` 把手机回环端口映射到电脑本地 API：

```bash
adb -s <serial> reverse tcp:8000 tcp:8000
```

这样不需要为了临时预览放宽 Tauri CSP，也不需要把本地 API 暴露到公网。

## 3. 真机一键安装 + FAST

推荐直接使用仓库辅助脚本，而不是手工拼安装、reverse、包名和 FAST 环境变量：

```bash
python scripts/android_acceptance/preview_usb_smoke.py \
  --apk path/to/PetAccess-preview-usb-device-aarch64-<sha>-debug.apk \
  --serial <adb devices 中的目标 serial>
```

脚本会依次：

1. 用 `aapt dump badging` 在安装前确认 APK 的 application id **必须**是 `com.petaccess.map.preview`；
2. 对电脑 `127.0.0.1:8000` 做真实 PetAccess API 身份检查：`/health` 必须返回 `status=ok`，`/api/v1/ping` 必须返回 `pong=true`；
3. 等待指定 adb 设备；
4. 优先用 `adb install -r` 保留 Preview 数据覆盖安装；
5. 只有遇到 `INSTALL_FAILED_UPDATE_INCOMPATIBLE`（不同 CI runner 的 debug 签名变化）时，才卸载 **Preview package 本身**并重装；正式 `com.petaccess.map` 永远不碰；
6. 确认 Preview package 确实存在；
7. 建立并验证 `adb reverse tcp:8000 tcp:8000`；
8. 设置 `PETACCESS_ANDROID_PACKAGE=com.petaccess.map.preview` 与目标 serial；
9. 调用 `scripts/android_acceptance/m3_fast.py`。

如果 Preview 已安装，可加：

```bash
--skip-install
```

该脚本不卸载正式 PetAccess，也不把 Preview 当成正式升级对象。

## 4. 手动运行 Android FAST

Android acceptance 工具默认仍验证正式包。需要直接验 Preview 时：

```powershell
$env:PETACCESS_ANDROID_PACKAGE = "com.petaccess.map.preview"
$env:PETACCESS_ANDROID_SERIAL = "<adb serial>"
python scripts/android_acceptance/m3_fast.py
```

真机 USB 模式仍需保持：

```bash
adb -s <serial> reverse tcp:8000 tcp:8000
```

这两个环境变量只改变验收目标，不改变产品代码。未设置时继续使用正式 package / owned emulator 默认值。

## 5. 为什么不接受任意 API URL

当前仓库没有冻结的 Public Beta API 域名，而且 Tauri CSP 是显式 allowlist。允许 workflow 临时注入任意 URL 会制造两类假象：

1. APK 看起来支持任意公网后端，但 WebView 可能被 CSP 拦截；
2. 为了“让预览能连”而放宽 `connect-src`，反而削弱正式运行时边界。

因此目前只允许两条明确开发链：

- emulator：`10.0.2.2`
- USB device：`127.0.0.1 + adb reverse`

未来 Public Beta API 域名冻结后，应新增明确的 `public-beta` profile，并同时更新 CSP、endpoint tests 与 runtime acceptance；不要恢复自由字符串 URL。

## 6. Artifact 必须包含

每个 Preview artifact 必须包含：

- Preview APK；
- `SHA256SUMS.txt`；
- `PREVIEW_SIGNER_CERTS.txt`：debug Preview 实际 signer certificate 指纹；
- `PREVIEW_METADATA.txt`：commit、profile、API、ABI、package、签名/Release 边界。

workflow 还必须：

- 使用 `apksigner verify` 验证 APK 可安装签名，并保存 `--print-certs` 结果；
- 使用 `aapt dump badging` 验证实际 package 是 `com.petaccess.map.preview`，且 app label 是 `PetAccess Preview`；
- 在 APK 打包后检查 Vite Consumer bundle 内确实烘焙了 matrix profile 对应的 `VITE_TAURI_ANDROID_API_BASE`；
- 使用独立 Preview Tauri config；
- 不读取正式 release keystore。

## 7. Preview APK 不能替代什么

Preview APK 只证明“候选安装包已生成并经过 package/signature 检查”。它**不替代**：

- Android FAST semantic gate；
- 13-route CDP journey；
- Evidence → 系统 Back → Reality；
- 多尺寸 / 生命周期 / 网络矩阵；
- Human Visual Acceptance；
- 正式 signed Release / 商店审核。
