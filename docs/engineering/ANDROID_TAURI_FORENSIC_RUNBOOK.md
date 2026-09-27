# PetAccess 本地工程运行手册（2026-09-26 取证审计后固化）

> 来源：GLOBAL FORENSIC AUDIT（docs/forensics/F00–F13，REG-001/002/004/005/007 全部实证）。
> 用途：本机（Windows 11，工作区 `E:\AI\宠物管理`）Android/Tauri 构建与验证的**约束与操作规范**；恢复 M3 开发前必读。

## 1. adb / emulator 工具链（REG-001/005 教训）

- **禁止裸 `adb`**：PATH 首位是 `C:\Android\adb.exe`（1.0.32），与 SDK platform-tools（1.0.41）并存。任何 adb 调用版本与当前 5037 server 不匹配 → server 被 kill/重启 → device offline 抖动、截图/shell 间歇失败。一律使用全路径：
  `C:\Users\Kaiser\AppData\Local\Android\Sdk\platform-tools\adb.exe`
- churn 信号：`adb server version (32) doesn't match this client (41); killing...`、`daemon not running; starting now`。处理：重新 start-server，设备 5–30 秒内回连。
- 模拟器统一：`C:\Users\Kaiser\AppData\Local\Android\Sdk\emulator\emulator.exe -avd pdig35 -no-window -gpu swiftshader_indirect`；端口避开 5554（其他 agent 会话占用），本 Goal 用 5556。
- 并发 agent 会话（scratch `b3868a2a-…`）会经 schtasks 分离启动 headless 模拟器并周期性调用旧版 adb：回归/取证时把其视为外部干扰，勿与它并发裸抢 adb；脚本必须自愈（见 §5）。

## 2. 截图（REG-002 教训）

- 二进制输出**禁止** PowerShell `>` / `Out-File`（会把 exec-out 二进制写成 UTF-16 → PNG 损坏，魔数 `FFFEFDFF`）。
- 正确姿势（二选一）：
  - `cmd /c "adb -s <SERIAL> exec-out screencap -p > out.png 2>nul"`
  - `adb shell screencap -p /sdcard/s.png && adb pull /sdcard/s.png out.png`
- 验收：PNG 文件头魔数必须为 `89504E47`。

## 3. Android 构建（REG-004/007 教训）

- **主工作区路径含 CJK（`E:\AI\宠物管理`）→ AGP 拒绝构建**（`Failed to apply plugin 'com.android.internal.application' > Your project path contains non-ASCII characters...`，b.android.com/95744）。本地 Android 构建一律使用 ASCII worktree：
  `git worktree add D:\pa-<label> <commit>`
- Windows host 构建 Rust/android 需要 MSVC：在 cmd 内 `call "D:\Code\Visual Studio\Visual Studio\VC\Auxiliary\Build\vcvars64.bat" >nul`。注意：vcvars 输出重定向到**文件**会导致其退出（异常中断），必须 `>nul 2>&1`。
- 构建链（与 CI 等价）：
  ```
  pnpm install --frozen-lockfile
  pnpm --filter @petaccess/client-h5 build
  pnpm --filter @petaccess/client-h5 exec tauri android init
  pnpm --filter @petaccess/client-h5 exec tauri android build --target x86_64        # release（签名见下）
  pnpm --filter @petaccess/client-h5 exec tauri android build --target x86_64 --debug # 调试：WebView console → logcat
  ```
- 签名（release keystore，与 CI 同一身份，文档见 docs/release/ANDROID_SIGNING.md）：
  `apksigner sign --ks ~/.petaccess-keystore/petaccess-release.keystore --ks-key-alias petaccess --ks-pass pass:<storePass> --out signed.apk unsigned.apk`
  密钥密码 = 存储密码（同一文件），**不可传 --key-pass**（会解密失败）。
- `CARGO_TARGET_DIR=D:\…` 可避免占用 E: 磁盘。

## 4. 运行验证（F03/F06 流程）

- Boot 可观测性：`VITE_BOOT_TRACE=1` 构建 → debug APK → `adb logcat -d -s Tauri/Console` 应见
  `PETACCESS_BOOT=INDEX_LOADED / VUE_CREATED / APP_SHELL_MOUNTED / ROUTER_READY / HOME_READY`。
- 终态门禁清单：install → launch → `pidof` → `dumpsys activity` ResumedActivity → `uiautomator dump` 见 WebView → 截图像素非灰（色数≥100、非纯色）→ HOME 键 → relaunch → pid 不变 → uninstall → `pm list packages` 无残留。
- 升级路径：先 `install` 官方 v0.1.0 APK，再 `install -r <同 keystore 新构建>` → Success 即升级兼容（已实证）。
- Windows：NSIS `/S` 静默安装 → 启动 → 主窗口标题 → relaunch → `%LOCALAPPDATA%\PetAccess\uninstall.exe /S` → 校验目录与注册表清除。

## 5. 长生命周期进程与脚本编码（自动化层教训）

- 本环境的工具调用结束会回收其进程树：下载、构建、模拟器、worker 必须用分离通道：WMI `([wmiclass]'Win32_Process').Create(...)`（或 schtasks，见并发会话先例）。
- **cmd 文件保持纯 ASCII**：含中文的 `cd /d E:\AI\宠物管理` 会在 cmd 的 ANSI/UTF-8 混码下静默失败（pnpm 落到 System32 报 workspace walk error）。方案：环境变量注入 `%PA_REPO%`（WMI 不继承调用者 env，需在子进程内自设）、powershell 用 `[char]` 码点拼路径、或 `-EncodedCommand`（base64）。
- WMI 分离进程**不继承调用者临时环境变量**；所有 env 在脚本内显式设置。

## 6. 回归基准（修复后基线，2026-09-26 实测）

| 项 | 命令 | 期望 |
|---|---|---|
| Backend | `uv sync --dev --all-packages --frozen` → `isolated_db.py --role TEST --reset` → celery(`-A app.worker.celery_app worker --pool=solo -Q petaccess_test`) → `uv run pytest -q` | 945 passed / 2 skipped |
| 工程门禁 | `ruff check` / `ruff format --check` / `mypy services/api/app` / `check_engineering_quality.py` / `scan_secrets.py` | 全 PASS；0 FAIL / 0 findings |
| 前端 | `pnpm lint:fe` / `pnpm format:check:fe` / `pnpm --filter @petaccess/client-h5 build` / `pnpm --filter @petaccess/admin build` | 全 PASS |
| E2E | `pnpm exec playwright test` | 149 passed |
| 迁移 | `alembic heads` / `alembic current` / downgrade→upgrade 链 | 单头 e9f2c1d4a5b6，链通过 |

## 7. 已知环境事实（勿再当 bug 修）

- `C:\Android\adb.exe` 1.0.32 与 SDK 并存 → 只用 SDK 的。
- 主工作区不可直接 Android 构建 → 用 ASCII worktree。
- 后端回归需要 PostgreSQL/Redis/MinIO（docker compose up -d db redis minio）与 celery worker。
- tauri.conf.json version 仍为 0.1.0（v0.2 未发布）——非漂移。

## 8. 2026-09-26 Android 全光谱验收新增已验证约束（追加，不改旧节）

- **Android WebView 的 CORS**：打包 App 的前端 origin 是 `http://tauri.localhost`（/ `https://…`）。API 的 `CORSMiddleware.allow_origins` 必须包含这两个 origin，否则 WebView 的每次数据请求被浏览器按 CORS 拦截（表现为 Home “未能取得附近场所”），且修复必须带回归测试（`test_tauri_webview_origin_is_cors_allowed`）。已有本地开发端口（5173–5175 等）不覆盖打包 origin。
- **SVG 尺寸必须走 style**：`ICON_SIZES` 是 CSS 变量（`--pa-size-icon-*`）；`<svg width="var(...)">` 属性形式被浏览器拒绝（“attribute width: Expected length”），必须用 `:style`。回归规格：`tests/e2e/pa-icon-size.spec.ts`。
- **debug 包 WebView 远程调试（取证可用）**：debug APK 启用了 WebView devtools（`/proc/net/unix` 可见 `webview_devtools_remote_<pid>` 抽象 socket）。`adb forward tcp:<port> localabstract:webview_devtools_remote_<pid>` 后可用 CDP 读取 DOM/console；release 包无该 socket（非缺陷）。
- **celery worker 必须显式指向测试库**：WMI/分离启动 celery 时若不设 `DATABASE_URL`，会从 `.env` 解析到生产库 `petaccess` 而 pytest 的 `.delay()` 消息排队到 `petaccess_test` 找不到任务（表现为 3 条 media/ocr 超时）。启动 worker 前必须 `DATABASE_URL=…petaccess_test` 与 `CELERY_TASK_QUEUE=petaccess_test` 同环境设置。
- **并发 churn 自愈**：外部 agent 周期性调用旧 adb（1.0.32）会重启 5037 server；本机工具对每次设备命令做有限退避重试（≥8 次），并避免依赖单次 `am start -W` 退出码（以 boot-trace/截图为准）。
- **grid 子项必须 `min-width: 0`**：`.place-preview__row`（`5rem 1fr`）在 ≥768dp 分栏布局里，长文本会让 `1fr` 轨道把页面撑出横向滚动条（800dp 下 document 805>800）。grid 子项需显式 `min-width: 0`（`PlacePreview.vue`）。回归规格：`tests/e2e/place-preview-overflow.spec.ts`。
- **响应式宽度用 wm size 覆盖**：360dp=990×2200px@440、430dp=1183×2563px@440、800dp（tablet）=2200×3520px@440；每次切换后必须重启 App 再取证据（`width_matrix.json`）。