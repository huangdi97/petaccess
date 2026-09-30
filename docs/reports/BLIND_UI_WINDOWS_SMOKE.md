# BLIND_UI_WINDOWS_SMOKE.md — Windows Smoke（真实 Tauri runtime / WebView2）

> 分支 `feat/visual-fidelity-recovery` · 复用本机 Rust/MSVC/WebView2/Tauri 工具链
> 证据：`artifacts/blind-ui-recovery/windows-smoke/`（6 张 CDP 页面截图 1250×950）

## 构建

| 项 | 事实 | 结果 |
|---|---|---|
| 前端 dist | `VITE_TAURI_API_BASE=http://127.0.0.1:8021/api/v1 pnpm exec tauri build --debug --no-bundle`（**在唯一工作区内构建成功**，MSVC link.exe 处理 CJK 路径无问题） | PASS（3m04s） |
| 产物 | `apps/client-h5/src-tauri/target/debug/petaccess.exe` | 存在 |
| 运行 API | `visual_db_reset.py` + `dev_api_server.py --role VISUAL --port 8021`（job） | health 200 |
| 启动 | `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9223 --force-renderer-accessibility` | 窗口「PetAccess 宠物共处」，CDP target 在线 |

## 运行验证（全部真实执行）

| 场景 | 结果 | 证据（CDP DOM + 截图） |
|---|---|---|
| launch | PASS | `PROC_RUNNING=True`、`WINDOW_TITLE=PetAccess 宠物共处`、`WINDOW_HANDLE=10754418`、CDP `/json` 有 target |
| Home | PASS | `url=#/ shell=true homeTitle=true placeName=去之前，先看看这里的规则和现场。`；`win-home.png` |
| Search | PASS | 输入「咖啡」→ **results=16**；`win-search.png` |
| Place | PASS | `#/place/5a9084d0-… placeName=云栖中心·测试商场 errorState=false`；`win-place.png` |
| Map | PASS | `mapShell=true`；`win-map.png` |
| navigation | PASS | hash 路由切换（Home→Search→Place→Map）每页 DOM 标记变化 |
| offline | PASS | `Network.emulateNetworkConditions offline` → `offlineBanner=true`；`win-offline.png` |
| recovery | PASS | 恢复在线 → `offlineBanner=false`；`win-recovery.png` |
| 短生命周期 | — | 桌面常驻进程不适用（已在 Android FAST 覆盖） |

## 截图真伪核验

6 张 1250×950 PNG：magic `89-50-4E-47`、non-zero bytes、hash 各异（win-home 与 win-recovery 同为首页确定态、像素一致属预期）。

## 结论

Windows Smoke 全场景 PASS：launch / Home / Search（16 结果）/ Place / Map / navigation / offline / recovery，真实 WebView2 runtime 上完成闭环。
