# UI Reconstruction — Windows Smoke（真实 Tauri runtime）

> 分支：`feat/ui-reconstruction-spatial-dossier`
> 方式：Tauri v2 debug 构建 → 真实 WebView2 运行 → CDP（`--remote-debugging-port=9223`）+ Windows UI Automation 驱动与截图
> 截图：`artifacts/ui-reconstruction/windows/`（home / search / map / place / offline / recovery / window-frame）

## 构建

| 项 | 命令/事实 | 结果 |
|---|---|---|
| 前端 dist | `VITE_TAURI_API_BASE=http://127.0.0.1:8011/api/v1 pnpm exec tauri build --debug --no-bundle` | PASS（2m52s） |
| 产物 | `apps/client-h5/src-tauri/target/debug/petaccess.exe` | 存在 |
| 运行 API | `visual_db_reset.py` + `dev_api_server.py --role VISUAL --port 8011`（WMI 分离） | health 200，seed 就绪 |
| 启动 | `petaccess.exe`（WMI 分离，`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9223 --force-renderer-accessibility`） | 窗口 `PetAccess 宠物共处`，CDP target 在线 |

## 运行验证（全部真实执行）

| 场景 | 驱动方式 | 结果 | 证据 |
|---|---|---|---|
| launch | UIA 找到窗口 + CDP page | PASS | window-frame.png（OS 窗口 1268×994） |
| Home | 默认路由 | PASS | home.png；UIA 树含“去之前，先看看这里的规则和现场。”、“附近已核验”、divider 行、`◐有条件` 徽章（新 Spatial Dossier UI，非 stretched H5） |
| Search | CDP `location.hash=#/search` + 输入“咖啡” + 查询 | PASS | search.png；`result-*` 计数 7（真实 API 结果） |
| Map | CDP `#/map` | PASS | map.png（结果窗格 + 地图画布 + 浮动预览） |
| Place | CDP `#/place/5a9084d0-…` | PASS | place.png；h1 = 云栖中心·测试商场；decision inspector 渲染 |
| navigation | hash 路由切换（Home→Search→Map→Place） | PASS | 各截图 URL/title 变化 |
| offline | CDP `Network.emulateNetworkConditions offline:true` → `navigator.onLine=false` | PASS | offline.png；`global-offline-banner` 可见=true |
| recovery | 恢复在线 + 重进 Home | PASS | recovery.png；verified 行重新出现（云栖中心·测试商场 ◐有条件） |
| 短生命周期 | 不适用桌面常驻进程（跳过，已在 Android 覆盖） | — | — |

## 桌面 UI 判定
- 不再是 stretched H5：UIA 暴露桌面 Rail（主导航 Group：首页/搜索/地图/贡献 + 账户与说明：我的/设置），主区域为 List–Detail / Spatial Workspace 结构。
- Search workspace：结果行（身份/结论/现场）分栏；Map workspace：地图画布为主；Place dossier：h1 档案 + 粘性 inspector。
- CORS：打包 origin `http://tauri.localhost` 数据请求成功（API 已允许该 origin，回归测试 `test_tauri_webview_origin_is_cors_allowed` 通过）。
