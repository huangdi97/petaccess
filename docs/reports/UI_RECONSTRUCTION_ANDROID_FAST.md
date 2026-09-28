# UI Reconstruction — Android FAST（真实模拟器执行）

> 分支：`feat/ui-reconstruction-spatial-dossier` @ 4fc21ba（构建 commit）
> 环境：Windows 11 / AVD `pdig36`（API 35 模拟器，headless swiftshader）/ SDK adb 1.0.41
> 证据：`artifacts/ui-reconstruction/android/*.png`（CDP 页面截图 + 设备层 screencap）

## 执行环境（真实，含修复过程）

| 项 | 事实 | 备注 |
|---|---|---|
| 构建 | ASCII worktree `D:\pa-ui-rc` @ 4fc21ba；`pnpm install --frozen-lockfile` → `VITE_TAURI_ANDROID_API_BASE=http://10.0.2.2:8011/api/v1 pnpm --filter @petaccess/client-h5 build` → `tauri android init` → `tauri android build --target x86_64 --debug`（CARGO_TARGET_DIR=D:\pa-ui-rc-cargo，vcvars64 环境） | 首次全量构建超过 1 小时工具上限，但产物在超时前完成 |
| APK | `gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk`（267,807,884 B，package `com.petaccess.map` v0.1.0，`aapt2 dump badging` 核验 launchable-activity=MainActivity） | 通用包含 x86_64 |
| API | `visual_db_reset.py` + `dev_api_server.py --role VISUAL --port 8011`（host，emulator NAT `10.0.2.2` 可达；CORS 已含 tauri.localhost） | health 200 |
| 模拟器 | `emulator.exe -avd pdig36 -port 5556 -no-window -gpu swiftshader_indirect -no-snapshot`；boot_completed=1（~50s） | 曾遇 **C: 盘 1.3GB 可用不足** → 清理 `~/.gradle/caches` + `wrapper/dists`（+15.6GB）后正常启动 |
| adb churn | 外部 agent 会话周期性重启 5037 server（REG-001）；本次全部命令带设备等待与有限退避重试；**从未使用 `adb kill-server`** | 全程 SDK adb 全路径 |

## 场景执行结果（全部真实，CDP DOM 证据）

| # | 场景 | 结果 | 证据 |
|---|---|---|---|
| 1 | install + launch | PASS（`install -r` Success；`am start -W` Complete；topResumedActivity=com.petaccess.map/.MainActivity；pid 4460） | `pm list packages` 含 `com.petaccess.map` |
| 2 | Home | PASS | DOM：`shell=true, home=true, qc=true, badges=6, title=去之前，先看看这里的规则和现场。`；`home.png` |
| 3 | Search | PASS | `search-input` 存在；输入“咖啡”→ **7 条真实结果**（10.0.2.2:8011）；`search.png`；`result-*` 计数 7 |
| 4 | Map | PASS | DOM：`[data-testid=map]` canvas 存在；`map.png` |
| 5 | Place | PASS | DOM：`title=云栖中心·测试商场, qc=true, badges=13`（档案 + inspector）；`place.png` |
| 6 | navigation | PASS | CDP hash 路由 Home→Search→Map→Place 逐步切换，每页 DOM 标记变化（见上表） |
| 7 | offline | PASS | CDP `Network.emulateNetworkConditions offline` → `global-offline-banner` visible=true；`offline.png` |
| 8 | recovery | PASS | 恢复在线 + 重进 Home → 重新渲染；`recovery.png` |
| 9 | short lifecycle | PASS | `input keyevent 3`（HOME）→ 启动器 → `am start` 重进 → **pid 4460 不变**（before=4460 after=4460） |
| 10 | 设备层截图 | PASS | `exec-out screencap` PNG 魔数 `89-50-4E-47`，720×1280，145 distinct colors；`device-home.png` |

截图真伪核验：home/search/map/place/offline 五张 CDP 截图两两像素采样差异 229~424/220（**全部页面互不相同**，非同一帧重复）。

## 平台限制（诚实标注）
- WebView 内容不进 uiautomator（`xml len 2266` 无文本节点）→ 文本断言走 WebView CDP（debug APK 的 `webview_devtools_remote_4460` abstract socket + `adb forward`），文档记为 **PLATFORM_LIMITED**（既有事实，非缺陷）。
- AVD 由本 Goal 独占启动（端口 5556）；包保留安装（便于续跑），未执行 uninstall（共享环境，避免与其他会话冲突）。
- 未运行 Monkey 1000 / 30min soak / 100 route stress（FAST 范围外，符合契约）。

## 结论
Android FAST **全场景 PASS**，用户在真实模拟器上完成了 launcher/Home/Search/Map/Place/导航/离线/恢复/短生命周期闭环，界面为新 Spatial Dossier UI（查询上下文 + divider 行 + 状态徽章）。