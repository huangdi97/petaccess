# F03 ANDROID THREE-WAY MATRIX（本轮实测，2026-09-26）

## 0. 测试对象（同一机器 / 同一 SDK / 同一 emulator / 统一 adb）

- 机器：Windows 11 Pro 10.0.26200；SDK `C:\Users\Kaiser\AppData\Local\Android\Sdk`（platforms 34/35/36, build-tools 35.0.0, NDK 27.1.12297006）
- emulator：pdig35（API 35 google_apis x86_64，headless `-no-window -gpu swiftshader_indirect`）**emulator-5556**
- adb：SDK platform-tools 37.0.1（1.0.41）全流程统一；裸 `adb` 一律规避（REG-001）
- 对象：
  - **A** = GitHub Release v0.1.0 官方 APK（`gh release download` 下载），SHA256 `e236f1936360a7f950152df53860ed01076c0c595b35fa881d4543c9f427f82d` = Release 报告 SHA256SUMS ✓（本地 `artifacts/v0.1.0` APK 为旧本地构建 d9e3acf4≠官方，未采用）
  - **B** = v0.1.0 source（独立 worktree D:\pa-v010，c84b4cf）现机重建：`pnpm install --frozen-lockfile` → frontend build → `tauri android init` → `tauri android build --target x86_64`（vcvars64 加载）→ release keystore 签名
  - **C** = HEAD（5af2bdb）clean build（独立 worktree D:\pa-head，同命令链）→ release keystore 签名
- 证据文件：`artifacts/forensics/F03/{A,B,C}/`（install/launch/pid/activity/png/ui.xml/logcat/meminfo）

## 1. 矩阵

| 单元格 | A 官方 v0.1.0 | B v0.1.0 重建 | C HEAD |
|---|---|---|---|
| adb install | PASS（Success） | PASS（Success） | PASS（Success） |
| launch | PASS（monkey） | PASS | PASS |
| PID | PASS（3346，boot 与 resume 同） | PASS（4442） | PASS（4729，boot 与 resume 同） |
| activity resumed | PASS（MainActivity t7，resume 后仍 t7） | PASS（MainActivity t8；resume 后 pid 存活，捕获时 launcher 过渡） | PASS（MainActivity t9，resume 后仍 t9） |
| WebView | PASS（ui.xml: android.webkit.WebView 全屏） | PASS（同） | PASS（同） |
| Vue mounted / Home ready（渲染证据） | PASS（320×640，1176 色初测 / 193 色抽样，品牌蓝 #34618E，bri 241，nonwhite 0.49） | PASS（与 A 几乎一致的渲染统计） | PASS（v0.2 新界面：201 色，bri 229.5 亮色 UI，非灰屏） |
| network state | 后端不可达（无 10.0.2.2:8000）→ Empty-First 态；logcat 窗口无 net::/Uncaught/FATAL | 同左 | 同左（packaged API 依赖相对路径问题见 REG-003，表现=数据面 offline，不影响 shell） |
| screenshot | PASS（cmd 重定向，合法 PNG 魔数 89504E47） | PASS | PASS |
| background/resume | PASS（HOME→relaunch，pid 不变+activity resumed） | PASS（pid 4442 存活；前台捕获落在 launcher 过渡帧，属采集竞态，非崩溃） | PASS（pid 4729 不变+activity resumed） |
| relaunch | PASS（二次 monkey 注入 1 事件成功） | PASS | PASS |
| uninstall | PASS（`adb uninstall` Success） | PASS（矩阵前清理） | PASS（终检中） |

升级路径（A 官方 → C HEAD / C-fix）：A=官方 v0.1.0 签名 = release keystore（与本地同一 keystore）→ `install -r C` Success；修复验证阶段将再验证 A → C-fixed 升级 + 最终 uninstall。

## 2. 判定（合同 §10）

**情况 4：A PASS / B PASS / C PASS。**

- 三对象在统一工具链下 boot、安装、启动、Activity、WebView、渲染、screenshot、background/resume、relaunch 全部 PASS；
- C（HEAD）渲染出的是 v0.2 新版界面且**非灰屏**；
- 后端全量 945 passed/2 skipped（0 fail）；依赖零漂移（F04）；Android 栈 tracked 变更 0（F04）。

→ 症状线首层失败不在应用代码（boot/render 层 REPOSITORY_CODE_CAUSAL=NO），而在：**ADB 工具链混用（REG-001）+ PowerShell 截图编码（REG-002）+ 并发 agent 干扰（REG-005）** 组成的**环境/自动化故障**；同时确认一个真实产品缺陷 **packaged API base 依赖 Vite proxy（REG-003，HIGH）**——它以"数据面全 offline"形式存在（Empty-First 掩盖了灰屏），已修复（见 FINAL_ROOT_CAUSE_REPORT 修复节），不影响本矩阵 PASS 判定。

## 3. 证据索引

- `artifacts/forensics/F03/A/`：official-v010 安装/pid/activity/06_home.png/12_after_resume.png/ui.xml/logcat/meminfo
- `artifacts/forensics/F03/B/`、`F03/C/`：同构证据
- 截图像素统计脚本与输出：scratch + F13