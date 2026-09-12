# ENGINEERING_QUALITY_BASELINE.md

> PART A（ENGINEERING-QUALITY-FREEZE）的基线定义与起点证据。
> 状态词汇：PASS = 实际执行成功；BLOCKED_EXTERNAL = 外部条件缺失；NOT_RUN = 没跑；PARTIAL = 有缺失。

## 起点（2026-09-13 接管快照，真实命令）

| 项 | 值 |
|---|---|
| HEAD | `2c9b547535c16bb7a0435584c3e306f7c7747044`（`zcode: takeover report baseline evidence filled`） |
| Branch | master（本地仓库，无 remote） |
| Working tree | 无 modified / staged；untracked：`.workbuddy-ai/`、resume 文档、旧补丁快照、`playwright-out/` |
| 保护补丁 | `quality_phase_pre_takeover.patch`（0B）、`quality_phase_pre_takeover_staged.patch`（0B） |
| 环境 | Windows 10.0.26200 x64 / Git Bash / Docker 29.2.1 / uv 0.9.18 / node 22.15.0 / pnpm 12.4.1 |
| Infra | petaccess-db-1（postgis/postgis:17-3.5，5432）up 28h healthy；petaccess-redis-1（6379）healthy；petaccess-minio-1（9000/9001）up |

## 前序会话声称的基线（本阶段必须以实测复核，不轻信）

pytest 184 passed · Playwright 7 passed · ruff lint/format PASS（103 files）·
mypy 72 files PASS · Admin/H5 build PASS · 7 revision 迁移 down/up 双循环 ·
demo seed 正常 · MinIO/Redis/Celery/PostGIS 集成 PASS · real_place_claims = 0。

## 已知基线缺口（接管时即识别，PART A 需处理）

| # | 缺口 | 影响 A 项 |
|---|---|---|
| G1 | 前端无 ESLint / Prettier 配置，从未运行 | A1 |
| G2 | 无 coverage 工具（pytest-cov 不在依赖中），从无 coverage 报告 | A5 |
| G3 | 无 pytest markers（unit/integration/contract 未注册） | A3 |
| G4 | `services/worker/` 只有 pyproject.toml 空壳（真实 worker 代码在 services/api/app/worker） | A15 |
| G5 | `packages/design-tokens/` 空目录；`apps/client/adapters/` 空目录 | A15 |
| G6 | `pnpm-workspace.yaml` 含字面占位符 `allowBuilds: esbuild: set this to true or false` | A15 |
| G7 | `tests/e2e/` 含游离 `__init__.py`（Python 包标记在 Playwright 目录） | A15 |
| G8 | 从无 TEST_COVERAGE / PERFORMANCE / SECURITY / PRIVACY / TECH_DEBT / REPRODUCIBILITY / BACKUP_EVIDENCE 报告文件 | A5/A8/A9/A11/A13/A15/A16 |
| G9 | E2E 链路 7（Entrance/AccessPath/Amensity 显示）覆盖情况待核查 | A3 |

## BASELINE 判定

- 代码基线：v0.5 本地 RC（见 `V05_FINAL_REPORT.md`），全部红线约束有测试锁定。
- 本文件不宣布任何 PASS；全部 PASS 判定见 `ENGINEERING_QUALITY_ACCEPTANCE.md`（只记实测）。
- PART A 开始时间：2026-09-13（见 git log 的本次接管提交）。
