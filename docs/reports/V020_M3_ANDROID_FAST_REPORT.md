# V020 M3 ANDROID FAST REPORT

> M3 深化收口后的 Android 快速验收（契约 §89：只跑 FAST，不重跑 Full）。

## 环境（本轮实测）

- Owned AVD：`pdig5`（API 35 模拟器），own serial `emulator-5556`（与 runbook 独立端口策略一致；emulator-5554/5568 为其他会话，未触碰）。
- 启动方式：`emulator.exe -avd pdig5 -port 5556 -no-window -gpu swiftshader_indirect`（WMI 分离启动防进程回收）。
- APK：`D:\pa-m3` ASCII worktree（git worktree @ M3 HEAD 173bdcb）构建 `tauri android build --target x86_64 --debug`，前端含 M3 改动 + `VITE_TAURI_ANDROID_API_BASE=http://10.0.2.2:8010/api/v1`（10.0.2.2 = 模拟器到宿主别名；8010 为独立 PetAccess API 实例）。
- 后端：`dev_api_server.py --db-name petaccess_visual --role VISUAL --port 8010`（独立实例，非 8000 他人服务）。
- ADB churn：环境存在其他 agent 周期重启 adb server（runbook REG-001 已知），本轮工具链（scripts/android_acceptance/adb.py + m3_fast.py）带 self-healing 重试；全程 `adb -s emulator-5556` 专用，未 kill-server 他人设备、未操作其他 serial。

## 执行结果（真实 DOM 验证，debug APK CDP + 截图）

| 项 | 结果 | 证据 |
|---|---|---|
| Launch（冷启动/force-stop 后 relaunch） | PASS | `am start` 成功；PID 6258 → force-stop → relaunch PID 7154 运行 |
| Home | PASS | CDP：`shell=true, homeTitle=true, errorState=false`（数据加载成功）；截图 `home-m3-final.png`（223,595 B，PNG 头 89504E47） |
| Search | PASS | CDP：`#/search, searchInput=true, results=21`（搜索返回 21 条真实结果）；截图 `search-m3-final.png`（286,059 B） |
| Navigation（map → home） | PASS | CDP：`#/map`（shell=true, errorState=false）→ `#/`（homeTitle=true） |
| Offline | PASS | CDP 触发 offline 事件：`offlineBanner=true`（GlobalOfflineBanner 出现） |
| Recovery | PASS | CDP 触发 online 事件：`offlineBanner=false`（banner 消失，恢复） |
| Short lifecycle | PASS | force-stop → relaunch → 进程存活（PID 7154） |

## 截图

- `artifacts/ui-audit/android/home-launch.png`（首次安装启动 Home）
- `artifacts/ui-audit/android/home-m3-final.png`（M3 Home 最终）
- `artifacts/ui-audit/android/search-m3-final.png`（M3 Search 最终）

## 与上一轮 Full Acceptance 的关系

- M3 未改动 Tauri shell / Android lifecycle / WebView 配置 / release 配置 / native bridge（本轮仅 Vue 前端 + Consumer 层），按契约 §90 不扩大至 Full（100 route / 100 nav / Monkey / 30min soak / upgrade matrix 不重跑）。
- Android WebView `uiautomator` 文本可见性仍为 `PLATFORM_LIMITED`（既有记录），本轮改用 debug APK CDP 做真实 DOM 断言，规避该限制且不视为缺陷。

## 结论

`M3_ANDROID_FAST = PASS`（本轮实测：launch / Home / Search / navigation / offline / recovery / short lifecycle 全通过，截图真实归档）。
