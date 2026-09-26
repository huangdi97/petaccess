# F01 REPOSITORY CURRENT STATE（本轮实测，2026-09-26）

## 1. Git 事实（本地实测输出）

| 项 | 值 | 命令 |
|---|---|---|
| LOCAL_HEAD | `5af2bdb6b1da43af30f34c15ef08d05fa5ceb21d` | `git rev-parse HEAD` |
| BRANCH | `master` | `git branch --show-current` |
| DESCRIBE | `v0.1.0-20-g5af2bdb` | `git describe --tags --always` |
| V010_TAG_SHA | `c84b4cf61fda1b904027aa6899a00a443a1ee383` | `git rev-parse v0.1.0` |
| V010_RELEASE_DOC | `5b1dd05d75d38a55bf471ae746b927f76f22b79f` | `git rev-parse 5b1dd05`（"mark v0.1.0 RELEASED"） |
| ORIGIN_MASTER | `5b1dd05d75d38a55bf471ae746b927f76f22b79f` | `git rev-parse origin/master` |
| AHEAD_OF_ORIGIN | 19 commits | `git status -sb`: `## master...origin/master [ahead 19]` |
| WORKTREE_STATE | 干净（无 tracked 改动） | `git status --short` 空 |

`git fetch --all --tags` 已执行；`origin/master` 停留在 `5b1dd05`（v0.1.0 发布记录），即 GitHub public master 落后本地 19 个 commit——本地 Code 的存在性判断**不得**以 GitHub 可见性为准。

## 2. v0.1.0 后的 commit 序列（20 个：c84b4cf..HEAD）

`5af2bdb M8-D 报告/PROJECT_STATE M8 基线`、`0856dc5 M8-A Windows DPI 矩阵 QA`、`80bbc52 M7-D 报告`、`3491cd3 M7-A..C contribution wizard`、`4078520 M5-D 报告`、`f1a9de8 M5-A..C Reality Trace+Evidence`、`624336d M4-D 报告`、`87689b9 M4-A..C Map/Passport`、`21566c6 M3-E 报告`、`e7ecf08 M3-A..D Consumer route/query+PlacePreview+Search split`、`315a99a M2-G closure`、`a83b2ea M2-F gap audit+DEV_FIXTURE_MODE`、`eba0ea7 M2-D+E Home/Search productization`、`5fb107e M2-C empty/loading/error/offline`、`6a01cbd M2-B ConsumerAppShell`、`4f813b1 M2-A design tokens`、`3386924 docs 质量基线 938`、`fa328e0 v0.2 M1 四项 gate`、`dd6994d reality contribution 路由`、`5b1dd05 mark v0.1.0 RELEASED`。

## 3. 工具链状态（详 F11/F10）

- Node 22.15.0 / pnpm 12.4.1 / Python 3.13.14 / uv 0.9.18 / Rust 1.97.1 / JDK 21.0.12.1（CI 用 17——版本漂移，见 F11）/ Gradle 8.14.3（gen/android）
- Android SDK `C:\Users\Kaiser\AppData\Local\Android\Sdk`：platforms 34/35/36、build-tools 34/35/36、NDK 26.1/27.1.12297006、emulator 37.1.11、system-image android-35 google_apis x86_64
- PATH 上 adb 双版本并存：`C:\Android\adb.exe`（1.0.32）在 `D:\Code\Android\SDK\platform-tools`（1.0.41）之前；本 Goal 统一使用 SDK platform-tools（1.0.41, platform-tools 37.0.1）
- 已存在 AVD：pdig35/pdig36/pdig_api34/petaccess_360/390/430 等 15 个（部分为其他 agent 会话所建）

## 4. 并发外部进程（另一 agent 会话）

- 2026-09-26 11:07 另一 PI-desktop 会话（scratch `b3868a2a-…`）经 Task Scheduler 分离启动 headless `petaccess_360`（port 5554, AVD 在 `F:\AndroidAvd`）
- 该会话仍活动（powershell PID 7368/13520 等），周期性调用 adb（命中 PATH 首位 1.0.32）→ 5037 server 反复被 kill/重建 → 本 Goal 矩阵运行中多次出现 `adb server version (32) doesn't match this client (41); killing...` 与 device offline/flapping
- 证据：`artifacts/forensics/F10_adb_churn_evidence.txt`、进程父链 cmdline 记录（emulator 20988 ← cmd 10008 ← svchost 2268；F10 报告）

## 5. 判定

REPOSITORY_STATE = CAPTURED（可复核）。