# BLIND_UI_ANDROID_FAST.md — Android FAST（真实模拟器执行）

> 分支 `feat/visual-fidelity-recovery` · 设备：复用运行中的 `emulator-5554`（不新建 AVD、不下载 system image）
> 证据：`artifacts/blind-ui-recovery/android-fast/`（FAST_SUMMARY.json + 4 张设备截图 1080×2400）

## 执行环境（真实）

| 项 | 事实 |
|---|---|
| 构建 | 唯一工作区 `E:/AI/宠物管理` 内构建**真实失败**于 lld 链接 CJK 路径（`cannot open E:\AI\宠物管理\.tmp\cargo-target\...rcgu.o: 在多字节的目标代码页中，没有此 Unicode 字符可以映射到该字符`）；MSVC/Java/SDK/Gradle 已排除（vcvars 修正后走到链接阶段）。按契约 ASCII Path Block 例外**经用户确认**，新建唯一 ASCII worktree `D:\pa-android-fast`（detached @ f6b940c，完成后已删除） |
| APK | `app-universal-debug.apk`（137,492,062 B，`com.petaccess.map` v0.1.0，`aapt2 dump badging`：launchable-activity=MainActivity、sdk 24+、target 36、compileSdk 36） |
| API | `visual_db_reset.py` + `dev_api_server.py --role VISUAL --port 8020`（host；模拟器经 NAT `10.0.2.2:8020` 访问，CSP 已含 `http://10.0.2.2:*`） |
| 工具链 | SDK `D:\Code\Android\SDK`（NDK 26.1/27.1/30.0）、JDK 21、Rust x86_64-linux-android target、gradle 8.14.3（wrapper 缓存此前被清，按需恢复 137MB 构建分发） |
| 恢复 | `gradle-8.14.3-bin.zip`（137,393,837 B）下载至 `~/.gradle/wrapper/dists`（构建声明依赖，<500MB） |

## 场景执行结果（全部真实，CDP DOM + 设备层截图证据）

| # | 场景 | 结果 | 证据 |
|---|---|---|---|
| 1 | install | PASS | `adb install -r` Success |
| 2 | launch | PASS | `am start -W`；pidof=832（后续实例 1474） |
| 3 | Home | PASS | CDP：`url=#/ title=首页 · PetAccess shell=true homeTitle=true errorState=false` |
| 4 | Search | PASS | 输入「咖啡」→ **results=16**（10.0.2.2:8020 真实 API）；`fast-search.png` |
| 5 | Place | PASS | `#/place/5a9084d0-…` shell=true 无 errorState；`fast-place.png` |
| 6 | Map | PASS | `#/map mapShell=true`；`NAV_MAP`/`NAV_HOME` hash 路由切换 DOM 变化 |
| 7 | navigation | PASS | Home→Search→Place→Map→Home 每页 DOM 标记变化 |
| 8 | offline | PASS | `offlineBanner=true`（dispatch offline）；`fast-offline.png` |
| 9 | recovery | PASS | 恢复在线后 `offlineBanner=false` |
| 10 | short lifecycle | PASS | 摘除 CDP forward 后：HOME 键 → 重新 `am start` → **pid 1474 不变**，无 ANR/crash |
| 11 | 设备截图 | PASS | 4 张 1080×2400 PNG（magic 89-50-4E-47、non-zero、hash 互异） |

## 平台限制（诚实标注）

- WebView 内容不进 uiautomator → 文本断言走 WebView CDP（debug APK 的 `webview_devtools_remote_<pid>` abstract socket + `adb forward`），记为 **PLATFORM_LIMITED**（既有事实）。
- debug APK 在 CDP 调试器附着时 HOME 背景化触发 WebView ANR（Java backtrace dump，无 native crash/tombstone），进程重启；**摘除 CDP 后生命周期 PASS** → 判定为调试器/Harness 产物，非应用缺陷。
- 未运行 Monkey 1000 / 30min soak / 100 route stress（FAST 范围外，契约 §E.24 不重跑）。
- ASCII worktree 已删除（`git worktree remove --force`），`D:\pa-android-cargo` 已清理。

## 结论

Android FAST 全场景 PASS：install / launch / Home / Search（16 结果）/ Place / Map / navigation / offline / recovery / short lifecycle，界面为新收口的 Consumer UI（时间线事件日志、provenance、无 pill wall 的地图）。
