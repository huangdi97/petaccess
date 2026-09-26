# ROOT CAUSE CANDIDATES REGISTER（2026-09-26）

> 状态：CONFIRMED = 有直接可复现证据；REJECTED = 有反证；OPEN = 待实验。证据文件在 `artifacts/forensics/`。

## REG-001 ADB 工具链混用导致 server churn / device offline
- **Symptom**：device 在 online/offline 间抖动；`exec-out screencap`、`adb pull`、`adb shell` 间歇 `device offline`；5037 反复 "daemon not running / killing..."
- **Subsystem**：host toolchain（PATH: `C:\Android\adb.exe` 1.0.32 vs SDK platform-tools 1.0.41）
- **First seen**：本 Goal 首次 adb 探测即现
- **Evidence for**：实验复现——1.0.41 server(PID 36924) → 执行 1.0.32 `adb devices` → 输出 "adb server is out of date. killing..." → server 变为 1.0.32(PID 33336) → 再被 1.0.41 顶替(PID 12340)。矩阵运行中 6+ 次出现 "adb server version (32) doesn't match this client (41); killing..."
- **Evidence against**：无
- **Experiment**：F10 实验（5037 归属逐次记录）
- **Result**：机制级确认
- **Status**：**CONFIRMED**（环境层根因；见 F03 判定——矩阵在此环境下仍全部可完成，故非唯一根因）

## REG-002 PowerShell `>` 重定向破坏 exec-out 二进制截图
- **Symptom**："exec-out / Python bytes 截图仍异常"；截图文件存在但不可用/损坏
- **Subsystem**：agent 自动化（PowerShell 管道）
- **Evidence for**：三法对照——PS `>` 产出的 `shotA.png`（391,680B）魔数 `FFFEFDFF50004E00`（UTF-16LE BOM + "P N G" 文本）；cmd 重定向 `shotB.png`（205,392B）魔数 `89504E470D0A1A0A`（合法 PNG）
- **Evidence against**：无
- **Result**：复现并定位
- **Status**：**CONFIRMED**（AGENT_AUTOMATION 层）

## REG-003 packaged runtime API base = 相对 `/api/v1`（依赖 Vite proxy）
- **Symptom**：packaged（Windows/Android Tauri）应用无法访问后端 API；数据面全失败
- **Subsystem**：frontend runtime config（`apps/client-h5/src/main.ts`）
- **Evidence for**：代码实证——`configureApi(import.meta.env.VITE_API_BASE ?? "/api/v1")`；vite.config 注释自述 H5 依赖 proxy；Tauri packaged 无 Vite server
- **Evidence against**：Empty-First 状态机使 API 失败不致灰屏（A/B 实机渲染正常）
- **Experiment**：矩阵 C 运行中，将实测 packaged API 行为（logcat/console）
- **Status**：**CONFIRMED（代码层）**——修复依赖包范围（见 FINAL_ROOT_CAUSE_REPORT 修复节）

## REG-004 detached build 缺 MSVC cl.exe → android cargo build 失败
- **Symptom**：`tauri android build` 失败：vswhom-sys build script 找不到 cl.exe（exit 101）
- **Subsystem**：Windows host 构建环境（VS 工具链 PATH）
- **Evidence for**：B 首次构建失败日志 `failed to run custom build command for vswhom-sys ... "cl.exe" ... exit code 2`；加载 `vcvars64.bat` 后重跑成功
- **Result**：复现并修复（加载 VS 环境）
- **Status**：**CONFIRMED**（环境层；对 B/C 构建均适用）

## REG-005 并发 agent 会话干扰 adb/emulator
- **Symptom**：两个模拟器（5554 另一会话、5556 本 Goal）交替 offline；adb server 被外部 kill
- **Subsystem**：外部进程（另一 PI-desktop 会话 b3868a2a）
- **Evidence for**：进程父链（schtasks → cmd → emulator petaccess_360 -port 5554）；周期性出现 version-32 churn 消息
- **Status**：**CONFIRMED**（外部干扰因素；矩阵脚本以轮询+自愈 server 处理并完成）

## REG-006 后端/前端代码回归（用户初始假设）
- **Evidence against**：后端全量 945 passed/2 skipped = 0 fail；前端 HEAD clean build 成功；A/B 实机渲染一致；依赖零漂移（F04）
- **Status**：**REJECTED**（对 boot/render 症状线不成立；REG-003 属配置缺陷而非回归）

## REG-007 主工作区路径含非 ASCII（"宠物管理"）→ Windows AGP 拒绝构建 Android
- **Symptom**：在主工作树 `E:\AI\宠物管理` 直接 `tauri android build` 失败：`Failed to apply plugin 'com.android.internal.application' > Your project path contains non-ASCII characters...`（b.android.com/95744），gradle 报 `Io(BeforeSpawn...)`。
- **Subsystem**：Windows 构建环境约束（AGP/路径编码）
- **Evidence for**：固定复现——同一代码在主树（非 ASCII 路径）构建失败；同一代码在 ASCII worktree（D:\pa-v010 / D:\pa-head / D:\pa-fix）构建成功（B/C/FIX 产物均在 ASCII worktree 产出）。历史 v0.1.0/v0.2 本地 Android 构建同样只能在 ASCII 路径完成。
- **Status**：**CONFIRMED**（环境约束；非产品代码缺陷）
- **操作含义**：本机 Android 构建必须使用 ASCII worktree（本 Goal 已采用）；不得在主树直接构建。已记录于 F03/F11 及本寄存器。

> 剩余 OPEN：无（所有候选已闭合或已由矩阵判定覆盖）。