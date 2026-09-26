# F12 DOCUMENTATION DRIFT（本轮）

> 全量判定见 `F00_CANONICAL_INDEX.md`（CURRENT=39 / HISTORICAL=221 / STALE=21）。本节记录 docs/code 漂移要点。

## 1. 状态类漂移（防止旧状态污染判断）

- F00 STALE 清单 14 条：`PUBLISH_BATCHES.md` 的 `30_50_PLACE_EXPANSION = ALLOWED_NOT_STARTED`（实际已执行）；v0.9-R1 母版 `ENGINEERING_OPEN` 状态位（M5/M7 已实现）；`FINAL_PRODUCTION_READINESS_REPORT` 的 `READY_FOR_PUBLIC_BETA=NO`（v0.1.0 已 Early Preview 发行）；`OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL/STATUS=OPEN`（已闭环）；WorkBuddy/ZCODE 一次性接管文档；`PROJECT_STATE_V05`/`README_V05_NEXT` 旧线状态。
- 结论引用规则：判定当前状态只允许引用 CURRENT 组与 HISTORICAL-BASELINE-EVIDENCE 组（v0.1.0 发行事实）。

## 2. 代码/文档漂移（本轮发现）

| 项 | 代码现状 | 文档 | 处置 |
|---|---|---|---|
| HomeView 头部注释 | 引用 "Consumer UX Baseline v1（goal §9–§12 / §12.x §17 §30）" | 目标文档已是 v0.1.0/v0.2 线 | LOW 债务（FF-003），不改动行为 |
| `components/AppShell.vue` 等旧代组件仍被 HomeView 使用 | 26–98 行旧组件 | V020_APP_SHELL_SPEC 描述 ConsumerAppShell | LOW 债务（FF-003），记录 |
| 工程质量数字 | 本轮 945 passed/2 skipped；gate 0 FAIL/60 REVIEW/34 WARN | 旧基线 "938 passed"（PROJECT_STATE 3386924） | 数字已更新于 F02；PROJECT_STATE 待随修复后基线更新（本 Goal 文档集为准） |
| packaged API 配置 | `main.ts` 默认 `/api/v1`（已修 → 按 runtime 解析） | vite.config 注释仍只描述 H5 proxy | 修复 commit 已落地；F12 记录 |
| tauri.conf.json version | 0.1.0（HEAD 未 bump） | RELEASE.md 标 v0.1.0 | 版本语义一致（v0.2 开发未发布），非漂移 |
| README/CI | 与 pr-ci/release-ci 一致（release-ci 为 v0.1.0 快照） | 一致 | — |

## 3. 契约/规范文件一致性

- `docs/v0.2/V020_DESIGN_SYSTEM_SPEC / APP_SHELL_SPEC / EMPTY_ERROR_OFFLINE_SPEC`：与实现一致（tokens SSOT、ConsumerAppShell 职责、六类错误呈现）→ CURRENT。
- 安全相关：`docs/release/ANDROID_SIGNING.md` 描述（同一密码 keystore）与本机一致（apksigner 验证通过）。
- 本 Goal 关键文档（F00–F13 等）统一归档 `docs/forensics/`，与历史线隔离。

F12 = PASS_WITH_TRACKED_DEBT（FF-003 等已登记；无规范性冲突）。