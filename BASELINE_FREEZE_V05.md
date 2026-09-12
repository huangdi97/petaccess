# BASELINE_FREEZE_V05.md

日期：2026-09-12
结论：**基线全绿，v0.5 域模型升级可以开始。**

## 1. Git 基线

- 期望基线（报告）：`95c357e`
- 实际 HEAD：`7eacfc314df8d12087e1999063968915977cd16f`
- 差异说明：`95c357e` 之后有两个非域模型提交：
  1. `9fe71d9` chore: gitignore test-results, fix report baseline hash（文档/工具修正）
  2. `7eacfc3` v0.5 pack: control documents（本轮控制文档入库）
- 处置：按 NEXT_GOAL_v0.5 §1.2 不强行 reset，以 `7eacfc3` 为 v0.5 工作基线。
  域代码与 `95c357e` 时完全一致（两次提交均未触碰 services/packages/apps 源码）。

## 2. 基线重跑证据（实际命令 → 实际输出）

| 检查 | 命令 | 结果 |
|---|---|---|
| 后端测试 | `uv run pytest -q` | **30 passed** (7.77s) |
| E2E | `pnpm exec playwright test` | **5 passed** (4.6s) |
| Lint | `bash scripts/lint.sh` | All checks passed! / 64 files already formatted |
| 类型 | `uv run mypy services/api/app` | Success: no issues found in 54 source files |
| Admin 构建 | `pnpm --filter @petaccess/admin build` | ✓ built in 2.31s |
| H5 构建 | `pnpm --filter @petaccess/client-h5 build`（VITE_API_BASE=:8010） | ✓ built in 1.49s |
| 迁移 | `alembic downgrade base` + `alembic upgrade head` | 864ffcfc7ccb down→up 成功 |
| 种子 | `uv run python -m app.db.seed --demo` | 4 places / 15 zones / 8 sources / 全演示状态 |
| PostGIS | `SELECT PostGIS_Version()` | 3.5 USE_GEOS=1 USE_PROJ=1 |
| Redis | docker compose ps | petaccess-redis-1 Up 11 hours (healthy) |
| Postgres | docker compose ps | petaccess-db-1 Up 11 hours (healthy) |
| MinIO | docker compose ps | petaccess-minio-1 Up 11 hours |
| Celery | `celery inspect ping` | 1 node online |
| API 冒烟 | `curl :8010/api/v1/ping` | {"pong":true} |
| H5 冒烟 | `curl :5175/` | 宠物准入地图 |

## 3. 冻结声明

以上基线在 v0.5 任何域模型改动前冻结。基线测试集
（`uv run pytest -q` + `pnpm exec playwright test` + lint + mypy）
在 v0.5 每个 Track 的 Gate 点必须保持全绿（V27 Gate）。

## 4. 已知环境注意事项（沿用 PROJECT_STATE.md）

- 本机 8000 端口被外部进程占用：文档示例用 8010。
- Docker Desktop 历史上偶发退出；本轮开始时已连续运行 11 小时。
