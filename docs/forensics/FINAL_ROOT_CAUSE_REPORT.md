# FINAL ROOT CAUSE REPORT（2026-09-26 本轮实证）

## 结论速览

```
PETACCESS_GLOBAL_FORENSIC_AUDIT = PASS
ROOT_CAUSE_PROVEN = YES
REPOSITORY_CODE_CAUSAL = NO（针对原始症状线：安装/启动/渲染/截图/offline 抖动）
                          + YES（针对 packaged API 数据面缺陷 REG-003，已修复）
FIX_VERIFIED = YES
ANDROID_RUNTIME = PASS       WINDOWS_RUNTIME = PASS       H5_RUNTIME = PASS
GLOBAL_UI_AUDIT = PASS       GLOBAL_CODE_AUDIT = PASS     FULL_REGRESSION = PASS
CRITICAL = 0                 HIGH = 0（修复后；修复前 HIGH=1 项 FF-001 已闭环）
M3_RESUME_ALLOWED = YES
```

## 十个必答问题

### 1. 原始症状是什么？
emulator device→offline 抖动；`screencap` 失败；`/sdcard` 截图文件缺失；`exec-out`/Python 截图"仍异常"；App 进程曾存在；MainActivity/UI 曾出现全灰或异常；agent 不断重试截图；shell/自动化本身也异常。

### 2. 第一处真正失败在哪一层？
两个独立层，均有可复现证据：

- **(a) host 工具链层（症状主因）**：5037 adb server 被旧/新双版本客户端反复 kill 重建（REG-001）。任何一次 adb 调用版本不匹配 → `adb server is out of date. killing...` → 全部 device transport 断开 → 后续命令 `device offline`。实测 server 归属在 36924(SDK 1.0.41)→33336(C:\Android 1.0.32)→12340(SDK 1.0.41) 间切换。
- **(b) 自动化截图层**：PowerShell `>` 重定向把 `exec-out screencap` 的二进制按 UTF-16 文本写盘（REG-002）——文件存在但魔数为 `FFFEFDFF50004E00` 而非 PNG 魔数 `89504E47`，截图"异常"的根因。
- 附带环境约束：主工作区路径含非 ASCII → AGP 拒绝 Android 构建（REG-007）；并发另一 agent 会话周期性操作 adb/emulator（REG-005）放大 (a)。

### 3. 根因是什么？
`MULTIPLE_ROOT_CAUSES`（明确归因，非单一）：
1. **ADB_TOOLCHAIN_FAILURE（REG-001）**：PATH 首位 `C:\Android\adb.exe`(1.0.32, 2016) 与 SDK platform-tools(1.0.41) 并存；33x-41x 版本不匹配引发 server churn → device offline / transport 抖动（机制级实验复现）。
2. **AGENT_AUTOMATION_FAILURE（REG-002）**：PS `>` 写二进制损坏截图（三法对照复现）。
3. **EMULATOR/外部干扰（REG-005）**：并发会话 schtasks 分离启动 petaccess_360（5554）并周期性调用旧 adb；本 Goal 以统一 adb+轮询自愈脚本完成全部矩阵（此环境仍可运行）。
4. **RUNTIME_CONFIG_REGRESSION（REG-003，产品缺陷）**：packaged Tauri 无 Vite proxy，`main.ts` 默认相对 `/api/v1` → packaged 数据面不可达（Empty-First 掩盖为"正常渲染+数据空"，非灰屏）。此缺陷为 v0.1.0 时代遗留（当时只验证了 render），v0.2 未修复。
5. 非根因（REJECTED）：后端代码回归（945 passed/2 skipped，0 fail）、前端 boot/渲染回归（A/B/C 全 PASS）、依赖漂移（F04 零漂移）、生成状态污染（F07 可复现）。

### 4. 哪个 commit / file / environment 引入？
- REG-001/002/005/007：环境/自动化层——本机 PATH 与并发会话，无 commit。
- REG-003：无单一"坏 commit"，为 v0.1.0 既有设计遗留（`apps/client-h5/src/main.ts` 的 `?? "/api/v1"`）；v0.1.0 验证流程未覆盖 packaged 数据流（只验证 render）故未暴露。修复 commit：`1d93942`。

### 5. 为什么 v0.1.0 曾正常？
A（官方 Release APK）与 B（v0.1.0 重建）在本 Goal 统一工具链下实测全链 PASS：install/launch/PID/activity/WebView/渲染/relaunch/uninstall。当时正常的原因：彼时验证经正确工具链执行；且 v0.1.0 验证目标=render，未测 packaged API 数据流（该缺陷一直存在）。

### 6. 为什么当前异常？
不是"当前代码变坏"，而是**运行环境的工具链/自动化叠加**：旧 adb 在 PATH 首位 + 多会话并发 → server churn → device offline 与截图失败。历史会话在无并发、工具链一致的时机可以成功；在并发/chaotic 时机就落入 (a)+(b)+(c) 抖动循环。

### 7. 为什么之前 screenshot workaround 无效？
- PS `>` 重定向损坏二进制（REG-002）→ 换更复杂的 exec-out/Python 字节仍落入同一 UTF-16 陷阱或 churn 窗口；
- 截图失败后重试→重试本身调用 adb→版本不匹配再 kill server→更 offline（正反馈循环）；
- 截图被当成 readiness 判定（合同 §88），在传输层不稳定时必然无限重试。
实证：同样命令，cmd 重定向即得合法 PNG；server 稳定后截图即刻成功。

### 8. 修复是什么？
- (a) 修复 REG-003（产品代码，commit `1d93942`）：`config/endpoints.ts` 按运行形态解析 API base——WEB=`VITE_API_BASE??/api/v1`、TAURI_DESKTOP=`VITE_TAURI_API_BASE??http://127.0.0.1:8000/api/v1`、TAURI_ANDROID=`VITE_TAURI_ANDROID_API_BASE??http://10.0.2.2:8000/api/v1`（10.0.2.2 仅 Android dev 默认）；main.ts 接线；CSP connect-src 最小增加 `http://10.0.2.2:* ws://10.0.2.2:*`。
- (b) 可观测性：`config/bootTrace.ts`（VITE_BOOT_TRACE=1 门控）输出 PETACCESS_BOOT 阶段链；Android debug 构建 logcat 验证 5 阶段齐全。
- (c) 测试网：`endpoint-resolution.spec`（fail-before=模块缺失 → pass-after 4/4）+ `backend-down-home.spec`（Empty-First P0：backend 不可达仍呈现 AppShell+Home、0 unhandled）。
- (d) 环境处置（非产品代码）：统一 SDK platform-tools adb、规避裸 adb、ASCII worktree 构建（REG-007）、WMI 分离长进程与轮询自愈脚本、cmd 重定向截图。

### 9. 为什么这个修复正确？
- REG-003 修复方向由确定性证据定锚：vite.config 自述 H5 依赖 proxy + packaged 无 proxy + Empty-First 掩盖数据面失败；修复使 packaged 按运行形态解析显式端点，并以单测覆盖三种运行形态与 10.0.2.2 不泄漏到 WEB/desktop（断言）。
- 升级路径补证（13:40 实测）：官方 v0.1.0 Windows setup（SHA256=adb8e984… 校验通过）安装 → 当前修复构建覆盖升级 exit=0 → launch/relaunch PASS → 卸载清理 PASS；连同 Android 同签名升级（终态门禁 03 步），§90 双端升级路径均实证。（此前"Windows 旧→新演练未跑"的备注由此更新为已跑。）
- fail-before→pass-after 已演示（模块缺失→5/5 通过）；Android 实机 5 阶段 boot 标记、升级/重启/卸载全 PASS（最终门禁）。
- CSP 最小放行（仅 10.0.2.2 connect），未关闭任何安全机制；bootTrace 编译期门控，生产不泄漏。
- 环境类根因的处置（统一 adb/ASCII worktree/截图编码）使整套验证可在同一会话内稳定复现（F03/F10/F13）。

### 10. 是否还有相关风险？
- `M3_RESUME_ALLOWED=YES`，但恢复开发前建议：①把 Android 构建固化进 ASCII worktree 流程（REG-007）或迁库到 ASCII 路径；②CI 保持（CI 路径 ASCII，无此问题）；③将 endpoint resolution 纳入前端单测门禁（本次已加）；④截图自动化统一 cmd 重定向/pull（REG-002 教训）；⑤并发会话会造成 adb churn，多 agent 并存时以本 Goal 的轮询自愈脚本为模板。
- 遗留债务（PASS_WITH_TRACKED_DEBT）：FF-003（HomeView 旧代组件）、FF-004/006/007（规模/复杂度 warn）——不影响 correctness/runtime/security，有 tracking ID。

## 归因判定（合同 §94 禁止措辞校验）

本报告结论章节对 `可能|大概|像是` 进行 grep 校验 = 0 命中；`应该` 未用于因果断言；每个因果链路均有实验编号（F03/F05/F09/F10/F11/F13 与 REG-xxx）。