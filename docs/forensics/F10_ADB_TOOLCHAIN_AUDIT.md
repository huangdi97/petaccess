# F10 ADB 工具链审计（初稿，证据采集于 2026-09-26 11:07–11:55）

> 本轮实测，证据文件位于 `artifacts/forensics/`。

## 1. 多版本 adb 并存（实证）

| adb 来源 | 版本 | 位置 | PATH 顺序 |
|---|---|---|---|
| ADB1（PATH 首位命中） | 1.0.32（2016 年 platform-tools 旧版） | `C:\Android\adb.exe` | 1（最先） |
| ADB2 | 1.0.41（platform-tools 37.0.0） | `D:\Code\Android\SDK\platform-tools\adb.exe` | 2 |
| ADB3（本 Goal 统一 canonical） | 1.0.41（platform-tools 37.0.1） | `C:\Users\Kaiser\AppData\Local\Android\Sdk\platform-tools\adb.exe` | — |

`Get-Command adb -All` 实证返回 ADB1、ADB2；ANDROID_HOME / ANDROID_SDK_ROOT 未设置。

## 2. ADB Server 进程树切换（churn）复现实验

实验（2026-09-26）：统一使用 canonical adb（1.0.41）启动 server → 得到 5037 server（PID 36924，路径 SDK platform-tools）；随后执行 PATH 首位旧版 `C:\Android\adb.exe devices` → 输出：

```
adb server is out of date.  killing...
* daemon started successfully *
```

5037 server 被替换为 PID 33336（路径 `C:\Android\adb.exe`，1.0.32）；再次调用 canonical adb → 又将 server 顶回 1.0.41（PID 12340）。

**结论（机制级实证）：任何一次 `adb` 调用使用了与当前 server 不同版本的 adb 客户端，都会 kill 并重启 5037 server。每次重启都会断开全部 device transport，已注册模拟器短暂变为 `offline`，导致下一跳 `exec-out screencap` / `adb pull` / `adb shell` 报 `device offline` / `error: closed`。**

观察间隔内 5037 反复出现"daemon not running; starting now"（>=4 次），与上一轮开发会话中"emulator → offline / screencap 失败 / 截图文件不存在 / agent 无限重试"的症状序列一致。

## 3. 外部进程干扰（另一 agent 会话）

2026-09-26 11:07:45–46，另一 PI-desktop 会话（scratch 目录 `C:\Users\Kaiser\.pi-desktop\scratch\b3868a2a-…`）通过 Task Scheduler（`svchost` → `cmd.exe /c …launch_360.cmd`）分离启动了 headless 模拟器：

```
emulator.exe -avd petaccess_360 -port 5554 -no-snapshot-load -no-boot-anim -no-window -gpu swiftshader_indirect -no-audio -no-skin -no-metrics
```

该 AVD 位于 `F:\AndroidAvd`（其脚本 set ANDROID_AVD_HOME=F:\AndroidAvd）。该会话仍在活动（powershell PID 13520，11:40:20），会不定期调用 adb（含旧版），与本 Goal 的矩阵验证并存时造成 server churn。→ 证据：`artifacts/forensics/F10_adb_churn_evidence.txt`、进程 cmdline 记录。

## 4. 本 Goal 统一工具链（确定性处置）

- ADB = `C:\Users\Kaiser\AppData\Local\Android\Sdk\platform-tools\adb.exe`（1.0.41，与所用 SDK 同源）
- EMULATOR = `C:\Users\Kaiser\AppData\Local\Android\Sdk\emulator\emulator.exe`（37.1.11.0）
- ANDROID_HOME = ANDROID_SDK_ROOT = `C:\Users\Kaiser\AppData\Local\Android\Sdk`
- 所有长生命周期进程经 WMI `Win32_Process.Create` 分离（能跨工具调用存活；Task Scheduler 分离通道曾由他人使用）
- 规避：不调用裸 `adb`（避免命中 C:\Android 旧版）；截图统一走 cmd 重定向或 `adb pull`（见 REG-002）

## 5. ADB 边界结论

`adb version` 本身不失败（1.0.41 正常），但 PATH 命中旧版 1.0.32 客户端 + 多会话并发使用 adb ⇒ 5037 server 反复重启 ⇒ device offline / screencap / pull 间歇失败。**该症状线为环境/自动化归因；产品代码因果待三矩阵验证（REPOSITORY_CODE_CAUSAL 待定）。**