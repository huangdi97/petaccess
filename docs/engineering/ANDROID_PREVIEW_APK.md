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

## 6. API URL 边界：开发 Preview 与独立手机 Preview 分开

Tauri CSP 使用显式 allowlist，因此不能为了“让某个临时地址能连”而把
`connect-src` 全局放宽。当前仓库允许三条明确链路：

- emulator：固定 `10.0.2.2:8000`，用于 CI / 本机 Android Emulator；
- USB device：固定 `127.0.0.1:8000 + adb reverse`，用于本机真机调试；
- Phone Preview：接受一个**绝对 HTTPS API URL**，并只把该 URL 的 origin 加入本次
  Preview 的 CSP。手动 `workflow_dispatch` 可以通过 `api_base` 显式覆盖；如果仓库变量
  `PETACCESS_PHONE_PREVIEW_API_BASE` 已配置，则 `feat/ui-direct-craft-v8` 上的 Consumer /
  Tauri 相关改动会自动生成 ARM64 standalone Phone Preview。自动 freshness trigger 不只覆盖
  `apps/client-h5/**`，还必须覆盖 `packages/client-core/**`、`packages/api-client/**`、
  `packages/design-tokens/**`、根 `package.json`、`pnpm-lock.yaml` 与
  `pnpm-workspace.yaml`；否则 API client 或 workspace 构建边界变化后，GitHub 上仍可能留下
  一个 SHA 更新但运行契约已陈旧的手机 Preview。未配置该变量时，workflow 仍会
  运行 `Android Phone Preview · readiness`，并明确输出
  `BLOCKED_BY_API_BASE`；standalone ARM64 build 只在 readiness=READY 后启动。
  这样“没有独立手机包”是可观测的外部依赖状态，不会表现成整个 workflow 静默 skipped，
  也不会把 localhost / emulator API 冒充成可独立使用的手机 Preview。

Phone Preview 会拒绝：

- 非 `http(s)` scheme；
- 明文 `http://`；
- URL 中嵌入用户名/密码；
- query string；
- fragment；
- 不是以 `/api/v1` 结尾的 API base；
- 能访问但 `/health` / `/api/v1/ping` 不是 PetAccess 响应的地址。

手动运行 workflow 时还可以启用 `require_real_map=true`。自动分支构建固定为
`require_real_map=false`，避免把腾讯地图外部网络/配额变成每次 UI 提交的强制依赖。
真实地图验收包在打包前额外要求：

1. `/api/v1/ai/map/config` 返回 `real_enabled=true`、`provider=tencent` 且存在浏览器 client key；
2. `/api/v1/ai/map/translate` 能把一组 WGS84 坐标真实转换为 Tencent `GCJ-02`；
3. 任一条件不满足，workflow 直接失败，不生成“看起来像真实地图、其实仍是 fallback”的 Phone Preview。

常规 API35/API36 deterministic runtime smoke **不依赖腾讯外部网络或配额**，因此允许并明确记录 `fallback`；真实地图验收使用上述显式模式，而不是把第三方网络波动变成每个 PR 的必过依赖。

这样“任意 HTTPS 地址”只作用于一次隔离的 Debug Preview 构建，不会改变正式 Tauri 配置，
也不会把 localhost / emulator 特权一并带到独立手机包中。

未来 Public Beta API 域名冻结后，应新增明确的 `public-beta` profile，并同时更新 CSP、
endpoint tests 与 runtime acceptance；不要把 Phone Preview（无论手动还是自动）当成正式
发行通道。Phone Preview 始终保持 debug / Preview package / 非正式签名。

### 6.1 从公网 Preview 到 Phone Preview 的自动 handoff

当有真实 VPS / 域名后，不需要手工把 API URL 在多条 workflow 之间搬运。默认分支可执行：

```text
Public Preview Deploy
.github/workflows/public-preview-deploy.yml
```

它会：

1. 检查 domain / SSH / Preview secrets；
2. 把当前 commit 部署到远端不可变 release 目录；
3. 启动并迁移 Preview compose；
4. 对公网 HTTPS 运行 `verify_public_api.cjs`；
5. preflight PASS 后，用 GitHub `workflow_dispatch` 自动触发
   `Android Phone Preview APK`，并把本次 `https://<domain>/api/v1`
   作为明确输入。

这条链依旧不写 Production、不读取 Android release keystore，也不会自动在 push 上部署公网服务器。

## 7. Artifact 必须包含

每个 Preview artifact 必须包含一份**机器可读 manifest**和一份**人可读安装说明**，让下载者不依赖文件名猜测运行边界：

- 普通 emulator / USB Preview：`PREVIEW_MANIFEST.json` + `INSTALL_PREVIEW.md`；
- standalone Phone Preview：`PHONE_PREVIEW_MANIFEST.json` + `PHONE_PREVIEW_INSTALL.md`。

manifest 至少固定：commit、branch、package、app label、build type、ABI、API base、是否需要 adb reverse、是否 standalone phone、是否要求真实地图，以及 `releaseArtifact=false` / `storeArtifact=false`。这些字段同时由工程质量门禁锁定。

每个 Preview artifact 还必须包含：

- Preview APK；
- `SHA256SUMS.txt`；
- `PREVIEW_SIGNER_CERTS.txt`：debug Preview 实际 signer certificate 指纹；
- `PREVIEW_BADGING.txt`：AAPT 实际 package / version / minSdk / targetSdk / native ABI；
- `PREVIEW_METADATA.txt`：commit、profile、API、ABI、package、签名/Release 边界。

workflow 还必须：

- 使用 `apksigner verify` 验证 APK 可安装签名，并保存 `--print-certs` 结果；
- 使用 `aapt dump badging` 验证实际 package 是 `com.petaccess.map.preview`、app label 是 `PetAccess Preview`，并硬校验 matrix 期望的 native ABI；
- 每个 matrix profile 必须只产生 **1 个**非 `androidTest` debug APK；若出现 0 个或多个候选，workflow fail-closed 并列出全部 APK，禁止用 `head -1` 任取一个文件冒充确定产物；
- 在 APK 打包后检查 Vite Consumer bundle 内确实烘焙了 matrix profile 对应的 `VITE_TAURI_ANDROID_API_BASE`；
- 使用独立 Preview Tauri config；
- 不读取正式 release keystore。

## 8. Android Runtime Review Board

API 35 / API 36 emulator runtime smoke 成功后，CI 会在各自 runtime evidence artifact 根目录生成；当前门禁同时要求公开态与登录态 packaged-WebView 证据：

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
- 19/19 Router 页面 + Place rules/space 两个额外公开视图（21 public/default cases）的 WebView page-level CDP journey；
- CI 真实注册账号后的 7-case authenticated packaged-WebView sweep：具体场所贡献入口 / 我的 / 隐私 / 宠物档案 / 通知 / 共处边界 / 新建宠物；
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

### 9.1 终态等待与进程死亡契约（2026-10-17）

- 每条 route 的截图与判定必须在该 route 的 `data-ui-state` 进入终态后进行；`loading`
  永远不是 PASS。Search 额外要求出现真实结果集（结果行 / 显式空态 / 错误）后才算终态，
  因为它在请求发出前的首帧也会是 `ready`。
- 进程死亡场景先 `am kill`；若 pid 仍存活则回退 `am force-stop`。只有观察到 pid 真正改变，
  才允许把“进程死亡后恢复”记为 PASS。`force-stop` 保留应用数据（不是 `pm clear`），
  证据同时记录 `killMethod` 与 `pidAfterKill`。
- 新装或冷启动后首次 Home 若因宿主网络瞬断进入可恢复的“附近不可用”状态，允许一次有界
  reload；最终仍必须是 `home/ready`，且第一次失败原文写入证据，不能静默吞掉。
- CI 在 API 启动后先预热 `/api/v1/places` 与 `/api/v1/places/nearby`，避免打包 WebView
  的首个数据请求撞上冷连接池。
- 验收脚本在 Windows 本地运行时显式以 UTF-8 解码 CDP/Node 输出并显式 UTF-8 打印汇总；
  否则默认 GBK 会让含中文的成功结果在最后一步被误判为失败。

