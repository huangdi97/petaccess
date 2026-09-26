# F07 GENERATED STATE DRIFT

**结论：无实质漂移（reproducible）。**

## 1. 方法

- 对象 A/B 使用独立 worktree：D:\pa-v010（v0.1.0）与 D:\pa-head（HEAD）各 `pnpm exec tauri android init` 一次（fresh）。
- 对比 fresh-vs-fresh：文件集（881 个）、结构性差异项。
- 对比 existing（主 worktree `apps/client-h5/src-tauri/gen/android`，HEAD 时代已生成）vs fresh：compileSdk/目标特性一致。

## 2. 结果

| 维度 | v0.1.0 fresh gen | HEAD fresh gen | 主 worktree existing |
|---|---|---|---|
| 文件数 | 881 | 881 | 881（结构一致） |
| compileSdk / targetSdk / minSdk | 36 / 36 / 24 | 36 / 36 / 24 | 36 / 36 / 24 |
| 差异项 | `.gradle/kotlin/errors/*.log`（时间戳文件名） | 同（不同时间戳） | — |
| 包标识 | `com.petaccess.map` | `com.petaccess.map` | `com.petaccess.map` |

两棵 fresh 树仅 kotlin 编译错误日志的时间戳不同；无源码/配置级漂移。主 worktree existing 与 HEAD fresh 对齐。

## 3. 与 v0.1.0 CI 的差异（记录，不改生成代码）

- v0.1.0 Release CI（Ubuntu + 当时 CLI）安装 `platforms;android-35` 并生成 compileSdk 35；本机 `tauri android init`（CLI ^2.11.x）默认生成 compileSdk 36（平台已装 34/35/36）。**属工具链/平台演进，非手工污染**；B/C/修复构建均在本机同一生成参数下完成，三矩阵对照内部一致。
- 生成代码零手工修改（git 无 gen 提交；B/C 构建均从 fresh gen 产出）。

F07 = PASS（可复现；无 contamination）。