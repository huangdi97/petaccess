# V010 DESKTOP REPORT (Windows) — 2026-09-24

> 状态标记 (Status Legend): **CURRENT VERIFIED** 本会话(2026-09-24)实际执行并核验 | **HISTORICAL** 此前会话执行、本轮未重跑 | **NOT RERUN** 未重跑(原因已注明) | **BLOCKED** 无法执行(原因已注明)

## 状态总表 (Status Table)

| 项 | 结果 | 标记 |
|---|---|---|
| cargo build --release | PASS -> petaccess.exe | CURRENT VERIFIED |
| tauri build | PASS -> PetAccess_0.1.0_x64-setup.exe | CURRENT VERIFIED |
| Installer smoke（install/launch/relaunch/uninstall） | PASS | CURRENT VERIFIED |
| WebView2 renderer 确认 | 进程树 + bundled copy 确认 | CURRENT VERIFIED |
| 窗口直接截图 | 未捕获（headless Win32 title lookup 不可靠） | NOT RERUN（局限，如实记录） |

## 1. 构建

- Tauri 2.11.6 scaffold 为 additive 引入（仅 `apps/client-h5/src-tauri`，无前端拷贝）。
- identifier `com.petaccess.map`；productName `PetAccess`；version `0.1.0`；min window 640x480；NSIS currentUser zh/en。
- cargo build --release PASS -> petaccess.exe；tauri build PASS -> 安装包。

## 2. Artifact

- `artifacts/v0.1.0/PetAccess_0.1.0_x64-setup.exe`（1.9 MB）。
- SHA256：`a0a2f61b62c3eefd44acbefe5d42b35f2f68fb9c96a848af5f1de086da4f7501`（Get-FileHash 复核）。

## 3. Installer smoke

- install exit 0 -> launch alive（观察到 WebView2 renderer 子进程）-> exit -> relaunch alive -> uninstall exit 0，安装目录与开始菜单项已移除。

## 4. 渲染确认与局限（如实记录）

- 渲染确认：WebView2 进程树存在 + bundled copy 存在 + 同一 bundle 在 Playwright 下正确渲染。
- 局限：headless 环境下直接窗口截图未捕获（Win32 title lookup 不可靠），不以截图声明渲染。

## 5. Security Posture

- CSP：deny-by-default；connect-src 仅 self + ipc + localhost/127.0.0.1（loopback）。
- Capabilities：default.json 仅 `core:default`（未授予 shell / fs / http 插件权限）。

## 6. 签名状态

- Windows 未签名（无代码签名证书）；安装时 SmartScreen 将出现"未知发布者"警告——属预期行为；正式分发前应补齐证书签名。

## 7. 结论

**结论: WINDOWS_BUILD = PASS; WINDOWS_INSTALL = PASS**
