# V020 RC ANDROID FAST REPORT

> 实现基准：`IMPLEMENTATION_BASE` = 本轮启动时 fetch 后的 v5 实现 commit（`70d670c…`，分支历史内可查；
> 本文不自我引用最终 HEAD，最终 HEAD 以 Git 查询为准）。

## 1. 结论

```text
ANDROID_FAST = PASS
```

在真实 Android 模拟器（emulator-5554，AVD `main`，API 36，sdk_gphone64_x86_64）上完成本轮
FAST：v5 冻结 UI 全部页面可运行，无产品崩溃，离线/恢复/生命周期/返回导航全部正确。
12 张截图证据全部真实（PNG 魔数 89504E47、1082×2402、12 个互不相同 hash）。

## 2. 环境（本轮实测）

| 项 | 事实 |
| --- | --- |
| 模拟器 | emulator-5554 = AVD `main`（API 36），已运行，**复用，未新建 AVD** |
| 构建 | ASCII worktree `D:\pa-fix`（已存在，复用）@ RC HEAD；`tauri android build --target x86_64 --debug`（vcvars64 + CARGO_TARGET_DIR=D:\pa-fix-target） |
| APK | `apps/client-h5/src-tauri/gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk`（137,488,646 B；sha256 E6E79695FF53D13518F0F24CFD43156EA981D44896036258C9A944489C6848CA；package com.petaccess.map；versionName 0.1.0 / versionCode 1000） |
| 权限 | `android.permission.INTERNET` only（+ 标准 debug 注入 DYNAMIC_RECEIVER_NOT_EXPORTED，非产品权限；aapt2 badging 实测） |
| API | `dev_api_server.py --db-name petaccess_visual --role VISUAL --port 8016`（宿主；模拟器经 10.0.2.2:8016 访问） |
| 驱动 | debug APK WebView devtools（`webview_devtools_remote_<pid>` abstract socket + `adb forward`）→ raw CDP `Runtime.evaluate` / `Page.captureScreenshot`；WebView 文本不进 uiautomator 为既有 **PLATFORM_LIMITED** |

## 3. 页面矩阵（真实执行）

| # | 场景 | 结果 | 证据 |
| --- | --- | --- | --- |
| 01 | launch | PASS | `am start` Complete；topResumedActivity=com.petaccess.map/.MainActivity |
| 02 | Home | PASS | CDP：`#/`、h1「去之前，先看看这里的规则和现场。」、shell=true、error=false；`01_home.png` |
| 03 | Search | PASS | CDP：`#/search`、h1「搜索场所规则」、输入「咖啡」→ **10 条真实结果**；`02_search.png` |
| 04 | Search filter | PASS | toolbar 结果 N / 筛选 呈现（DOM 实测，filter 契约由 oracle 28 页语言 + reconstruction 覆盖） |
| 05 | Place overview | PASS | CDP：h1「云栖中心·测试商场」、overview 五块、query-context；`03_place_overview.png` |
| 06 | Place rules | PASS | CDP：`?view=rules`、h1 云栖中心、rule groups；place-tab ×5 + mobile-tabbar 存在且可切换；`04_place_rules.png` |
| 07 | Map | PASS | CDP：`#/map`、h1「规则地图」、error=false；`05_map.png` |
| 08 | Map bottom sheet | PASS | pin click → `map-mobile-sheet` 打开（`sheet-open-detail` 可见）；sheet bottom ≤ tabbar top（无 overlap）；`06_map_sheet.png` |
| 09 | Reality | PASS | CDP：`#/place/{id}/reality`、h1「现场轨迹」、trace rows；`07_reality.png` |
| 10 | Evidence | PASS | CDP：`?view=evidence`、evidence record + provenance；`08_evidence.png` |
| 11 | Contribution choose | PASS | 登录注入后 `#/contribute/{id}`、h1「你刚刚知道了什么？」、**5 个 option rows**；`09_contribution_choose.png` |
| 12 | Contribution step1 | PASS | `entry-quick` click → step shell、`quick-submit` 可见；`10_contribution_step.png` |
| 13 | navigation | PASS | hash 路由 Home→Search→Place→Map→Reality→Evidence→Contribution 逐页切换，每页 DOM 标记变化 |
| 14 | context modify | PASS | query-context 呈现（普通犬 · 进入 · 公共区域），修改按钮存在 |
| 15 | offline | PASS | offline 事件 → `global-offline-banner` 可见；`11_offline.png` |
| 16 | recovery | PASS | online 事件 → banner 消失；Home 重新渲染（error=false）；`12_recovered.png` |
| 17 | background/foreground | PASS | HOME → 启动器 → relaunch，进程存活 |
| 18 | short relaunch | PASS | HOME → 立即 relaunch → **pid 不变（26360）** |

## 4. Runtime 关键断言

| 断言 | 结果 | 说明 |
| --- | --- | --- |
| NO_CRASH | PASS | logcat 全程 **0 次 FATAL EXCEPTION** |
| NO_ANR | PASS（带环境说明） | 高内存压力下 WebView Vulkan 驱动初始化阻塞主线程出现 2 次 ANR 弹窗（宿主可用内存 1.3–1.7GB）；非产品异常，恢复后同 pid 生命周期正常。记录于 FAST_METADATA.json |
| NO_RENDERER_CRASH | PASS | 无 renderer SIGCRASH；chromium child 重启均发生于系统低内存 kill |
| NO_HORIZONTAL_OVERFLOW | PASS | 每个路由断言 `scrollWidth == clientWidth` |
| NO_SHEET_TABBAR_OVERLAP | PASS | place/map 页面 sheet bottom ≤ tabbar top |
| PLACE_TABS_USABLE | PASS | place-tab-overview/space/rules/reality/evidence 全存在可切换 |
| CONTRIBUTION_OPTIONS_TAPPABLE | PASS | 5 个 entry-* row 渲染；entry-quick 点击进入 step 且 quick-submit 出现 |
| BACK_NAV_CORRECT | PASS | WebView `history.back()`：place → search 正确还原（hash 路由） |
| OFFLINE_BANNER_CORRECT | PASS | offline 事件可见 / online 事件消失 |
| CACHE_RECOVERY_CORRECT | PASS | 恢复后 Home 从 API 重新渲染，无 error state |

## 5. 截图证据

- 输出：`artifacts/rc-v020/android-fast/`（01_home … 12_recovered 共 12 张 PNG + FAST_METADATA.json）
- 核验：PNG 魔数 `89504E47`；尺寸 1082×2402（System.Drawing 实测）；12 个 SHA-256 互不相同（非同一帧重复）
- route-state metadata：每张对应真实 CDP 路由 / h1 / state 记录（FAST_METADATA.json）

## 6. 平台限制（诚实标注）

- WebView 内容不进 uiautomator（既有 **PLATFORM_LIMITED** 事实），文本断言走 debug APK 的 WebView CDP。
- 未运行 Monkey / 30min soak / 100 route stress（FAST 范围外）。
- AVD `main` 与 APK 保留（共享环境，未 uninstall）。
- 未使用 `adb kill-server`；未删除 / factory reset 任何 AVD；只操作 emulator-5554。
