# V020 Android 运行时性能报告（模拟器）

> 目标 §123 · 设备：`emulator-5562`（API 35）· APK：debug `current-debug.apk`（137 MB）与 release-like `current-release-signed.apk`（11.6 MB）
> 目的：找明显 regression / hang / 泄漏；不制造虚假 KPI。

## 冷启动 / 热启动

| 项 | 实测 | 证据 |
|---|---|---|
| Cold launch 10 次平均 | ~6.08s（5.75–7.36s）到 HOME_READY（boot trace 全链每次完整） | `runtime/cold_launch.json` |
| Warm launch 20 次 | 20/20 无 crash/ANR/blank | `runtime/warm_launch.json` |
| Release-like 启动 | Home 渲染（非灰截图），ResumedActivity 正常 | `phoneM__home__release__RELEASE01.png` |

## 内存基线（dumpsys meminfo，TOTAL PSS）

| 采样点 | TOTAL PSS (KB) | Java Heap | Native Heap |
|---|---|---|---|
| cold Home | 70,225 | 4,624 | 18,541 |
| after bottom-nav 100 | 73,969 | 5,056 | 18,694 |
| after route stress 100 | 110,675 | 11,724 | 19,674 |
| after scroll 50 | 110,730 | 11,608 | 19,674 |
| soak start | 109,909 | 10,904 | 19,854 |
| soak end（30min） | 109,637 | 11,296 | 20,078 |

- 结论：路由切换累计增长有限（70→110 MB 主要在 WebView 缓存/页面堆），scroll 与 30 分钟 soak **无不可恢复增长**（soak 结束反而回落 272 KB）→ 无明确泄漏信号。

## CPU

- idle Home `top` 采样已存 `performance/cpu_idle_home.txt`；soak 期间周期性 logcat 监控未见持续异常占用。

## 体积

- debug APK 137,469,246 B（含多 ABI debug 符号）；release-like universal 11,642,245 B → 正式体积合理（无回归）。

## 判断

- 无 hang、无明显 regression、无泄漏信号 → **PERFORMANCE = PASS**（不制造 KPI；数字为真实执行值）。
