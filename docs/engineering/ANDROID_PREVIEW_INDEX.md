# Android Preview Index

> 这是 **PetAccess 当前 Android 候选的下载/验收导航页**。
>
> 它不保存“永远最新”的固定 SHA。下载前先在 GitHub Actions 中打开当前
> `feat/ui-direct-craft-v8` 的最新成功运行，并确认 artifact commit 与当前 runtime input
> 等价。

## 1. 先选对包

| 你要做什么 | 选哪个 artifact | 能否脱离电脑 | API | 额外步骤 |
|---|---|---:|---|---|
| Android Emulator 看最新 UI | `petaccess-android-preview-emulator-<sha>` | 否 | `10.0.2.2:8000/api/v1` | 电脑启动本地 API |
| USB 真机看最新 UI | `petaccess-android-preview-usb-device-<sha>` | 否 | `127.0.0.1:8000/api/v1` | `adb reverse tcp:8000 tcp:8000` |
| 手机直接安装、离开电脑使用 | `petaccess-phone-preview-<short-sha>` | **是** | 手机可达 HTTPS `/api/v1` | Phone Preview readiness 必须 = `READY` |
| 正式发布 / 商店安装 | **以上都不是** | - | Production HTTPS API | 走 signed Release workflow |

## 2. Android Preview APK

GitHub Actions workflow：

```text
Android Preview APK
.github/workflows/android-preview.yml
```

每个相关代码提交自动生成：

- x86_64 emulator Preview；
- ARM64 USB-device Preview；
- API 35 packaged runtime acceptance；
- API 36 packaged runtime acceptance；
- Android runtime evidence / review board。

Preview 身份固定为：

```text
app label: PetAccess Preview
package:   com.petaccess.map.preview
build:     debug
release:   false
store:     false
```

它可以与正式 `com.petaccess.map` 并存。

## 3. USB 真机 Preview

下载：

```text
petaccess-android-preview-usb-device-<sha>
```

artifact 内至少应有：

```text
PetAccess-preview-usb-device-aarch64-<short-sha>-debug.apk
PREVIEW_MANIFEST.json
PREVIEW_METADATA.txt
PREVIEW_BADGING.txt
PREVIEW_SIGNER_CERTS.txt
SHA256SUMS.txt
INSTALL_PREVIEW.md
```

安装前先核验：

```bash
sha256sum -c SHA256SUMS.txt
```

连接手机后：

```bash
adb reverse tcp:8000 tcp:8000
adb install -r PetAccess-preview-usb-device-aarch64-<short-sha>-debug.apk
```

或使用仓库脚本：

```bash
python scripts/android_acceptance/preview_usb_smoke.py \
  --apk <apk-path> \
  --serial <adb-serial>
```

**不要**把 USB Preview 直接发到手机后离开电脑使用。它烘焙的是
`http://127.0.0.1:8000/api/v1`，依赖 adb reverse。

## 4. Standalone Phone Preview

GitHub Actions workflow：

```text
Android Phone Preview APK
.github/workflows/android-phone-preview.yml
```

它的 readiness 是事实源：

### READY

代表存在一个可从手机访问的 PetAccess HTTPS API：

```text
https://.../api/v1
```

之后才允许生成 ARM64 standalone Debug Preview。

### BLOCKED_BY_API_BASE

代表尚未提供：

```text
PETACCESS_PHONE_PREVIEW_API_BASE
```

或者手动 dispatch 的 `api_base`。

这不是 CI 故障，也不能用 localhost、`10.0.2.2`、假 URL 或静态 demo 数据绕过。

Phone Preview 仍然：

- package = `com.petaccess.map.preview`
- debug signer
- not store artifact
- not signed Release

## 5. Runtime evidence 怎么看

成功的 API35 / API36 runtime job 会上传对应 evidence artifact。

重点先打开：

```text
ANDROID_RUNTIME_REVIEW_BOARD.html
coverage_matrix.json
runtime/m3_fast.json
runtime/cdp_journey_playwright.json
runtime/ime_gate.json
runtime/width_matrix.json
```

机器 gate 当前覆盖：

- 19 个 Router page identity；
- Place overview / rules / space；
- 7 个 authenticated packaged-WebView 场景；
- governed scene media；
- Search / Pet New 真实 Android IME 输入；
- phone-m / ~360dp / ~430dp / tablet；
- horizontal overflow；
- safe-area overlap；
- Evidence → Android Back → Reality；
- fresh Home → Android Back → Activity 退出前台；
- offline → recovery；
- Home / Activity resume；
- API 35 / API 36。

Runtime Review Board 是**人工审图入口**，不是自动 Human Visual PASS。

## 6. 地图事实

如果没有腾讯地图 Key，runtime 可以使用 provider-neutral fallback，但必须如实标记。

只有在真实配置：

```text
TENCENT_MAP_KEY_CLIENT
TENCENT_MAP_KEY_SERVER
MAP_PROVIDER=tencent
FEATURE_REAL_MAP=true
```

并通过：

```text
require_real_map=true
```

的 Phone Preview/runtime 验证后，才能声明“真实腾讯底图已接入”。

## 7. Release 边界

不要把任何 Preview APK 上传为正式 Release。

正式 Android 包必须：

- package = `com.petaccess.map`
- production HTTPS API
- release keystore
- release CI
- apksigner verify
- final release authorization

当前发布事实和下一次发布门禁见：

```text
RELEASE.md
PRODUCTION_STATE.md
BLOCKERS.md
```

## 8. Truth Rule

```text
APK exists != runtime PASS
runtime PASS != Human Visual Acceptance
Preview != Release
USB Preview != standalone phone app
fallback map != real Tencent map
```
