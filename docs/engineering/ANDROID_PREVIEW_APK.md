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

## 2. 构建工具链

Preview 与正式 Release 使用同一 Android SDK 主版本，不依赖 GitHub runner 的隐式预装：

- Android SDK Platform：`android-36`
- Android SDK Build Tools：`36.0.0`
- NDK：`27.1.12297006`
- Java：17
- Tauri Android：当前 `@tauri-apps/cli` 2.x

APK artifact 内的 `PREVIEW_BADGING.txt` 继续记录实际 compileSdk / minSdk / targetSdk / native ABI，防止“workflow 参数写 36，但最终 APK 不是 36”的假一致。

### 2.1 哪些变化必须重跑 Preview

Preview 不是“前端截图工作流”。只要会改变打包 Consumer 或其真实 API 契约，当前工作分支都必须重新跑 Android Preview：

- `apps/client-h5/**`、`packages/client-core/**`、`packages/api-client/**`、`packages/design-tokens/**`；
- `services/api/**`；
- `scripts/isolated_db.py` 与 `scripts/dev_api_server.py`；
- `pyproject.toml`、`uv.lock` 以及前端 workspace/lock 文件；
- Android acceptance 脚本和 Preview workflow 自身。

这组 path trigger 由工程质量门禁锁定，避免以后出现“Web/Backend 已变，但 packaged Android runtime 没有重跑”的假新鲜证据。当前 runtime smoke 没有启动 Celery，因此 `services/worker/**` 不被写成已验证边界；涉及 worker 的贡献异步链仍需独立验收。

## 3. 每次自动生成两份 Preview

当前 UI 工作分支发生 Consumer/runtime 相关变更时，workflow 用 matrix 同时构建两个 artifact。

### 3.1 emulator · x86_64

API：

```text
http://10.0.2.2:8000/api/v1
```

用于 Android Emulator；`10.0.2.2` 指向宿主机。

### 3.2 usb-device · aarch64

API：

```text
http://127.0.0.1:8000/api/v1
```

用于主流 ARM64 Android 真机。手机通过 USB 连接电脑时，以 `adb reverse` 把手机回环端口映射到电脑本地 API：

```bash
adb -s <serial> reverse tcp:8000 tcp:8000
```

这样不需要为了临时预览放宽 Tauri CSP，也不需要把本地 API 暴露到公网。

## 4. 真机一键安装 + FAST

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

## 5. 手动运行 Android FAST

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

## 6. 为什么不接受任意 API URL

当前仓库没有冻结的 Public Beta API 域名，而且 Tauri CSP 是显式 allowlist。允许 workflow 临时注入任意 URL 会制造两类假象：

1. APK 看起来支持任意公网后端，但 WebView 可能被 CSP 拦截；
2. 为了“让预览能连”而放宽 `connect-src`，反而削弱正式运行时边界。

因此目前只允许两条明确开发链：

- emulator：`10.0.2.2`
- USB device：`127.0.0.1 + adb reverse`

未来 Public Beta API 域名冻结后，应新增明确的 `public-beta` profile，并同时更新 CSP、endpoint tests 与 runtime acceptance；不要恢复自由字符串 URL。

## 7. Artifact 必须包含

每个 Preview artifact 必须包含：

- Preview APK；
- `SHA256SUMS.txt`；
- `PREVIEW_SIGNER_CERTS.txt`：debug Preview 实际 signer certificate 指纹；
- `PREVIEW_BADGING.txt`：AAPT 实际 package / version / minSdk / targetSdk / native ABI；
- `PREVIEW_METADATA.txt`：commit、profile、API、ABI、package、签名/Release 边界。

workflow 还必须：

- 使用 `apksigner verify` 验证 APK 可安装签名，并保存 `--print-certs` 结果；
- 使用 `aapt dump badging` 验证实际 package 是 `com.petaccess.map.preview`、app label 是 `PetAccess Preview`，并硬校验 matrix 期望的 native ABI；
- 在 APK 打包后检查 Vite Consumer bundle 内确实烘焙了 matrix profile 对应的 `VITE_TAURI_ANDROID_API_BASE`；
- 使用独立 Preview Tauri config；
- 不读取正式 release keystore。

## 8. Android Runtime Review Board

API 35 / API 36 emulator runtime smoke 成功后，CI 会在各自 runtime evidence artifact 根目录生成：

`ANDROID_RUNTIME_REVIEW_BOARD.html`

下载并解压 `petaccess-android-preview-runtime-<sha>` 后，直接打开该 HTML 即可一次查看打包 Android WebView 的全部 route screenshot，并看到每页的：

- `data-ui-page` / `data-ui-state` / fixture；
- viewport 与 document 尺寸；
- horizontal overflow；
- safe-area top 与 content top；
- 当前 runtime PASS / FAIL。

Review Board 明确保持 `HUMAN_VISUAL_ACCEPTANCE = PENDING`。机器截图与几何通过不能自动变成人工视觉通过。

## 9. Preview APK 不能替代什么

Preview APK 只证明“候选安装包已生成并经过 package/signature 检查”。它**不替代**：

- Android FAST semantic gate；
- 19/19 Router 页面 + Place rules/space 两个额外视图（21-case）的 WebView page-level CDP journey；
- Evidence → 系统 Back → Reality；
- fresh Home → 系统 Back → MainActivity 退出前台；
- packaged WebView 离线提示 → 恢复；
- Activity Home/Resume 后 Consumer shell 与横向 overflow gate；
- 多尺寸矩阵；
- Human Visual Acceptance；
- 正式 signed Release / 商店审核。

当前 CI 的 Android CDP 旅程直接连接 Android System WebView 暴露的 page target，
而不是把该 target 当成完整桌面 Chromium browser context。这样既保留真实 DOM / route /
screenshot 证据，也避免 Playwright `connectOverCDP()` 在 WebView 上发送仅浏览器上下文支持的
Browser-domain 命令导致假失败。
