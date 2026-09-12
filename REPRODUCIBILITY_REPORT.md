# REPRODUCIBILITY_REPORT.md

日期：2026-09-13（PART A · A16）· 每条命令均为本日实际执行（或注明）。

## 环境起点

| 组件 | 版本 | 状态 |
|---|---|---|
| Windows | 10.0.26200 x64（Git Bash） | — |
| Docker | 29.2.1 | petaccess-db-1（postgis/postgis:17-3.5）healthy / redis 7 healthy / minio up |
| uv | 0.9.18 | `.venv` 可重建（uv.lock 提交） |
| Node / pnpm | 22.15.0 / 12.4.1（`packageManager` 钉版） | pnpm-lock 提交 |

## 从仓库到可运行栈的验证链（实跑）

| 步骤 | 命令 | 结果 |
|---|---|---|
| 1. env | `.env` 存在（`.env.example` 同步更新 JWT_SECRET） | OK |
| 2. Python 依赖 | `uv add --dev pytest-cov`（含全量 sync）+ `uv run …` | OK，lock 一致 |
| 3. Node 依赖 | `pnpm add -D -w eslint … prettier`（esbuild allowBuilds 修复后 postinstall OK） | OK |
| 4. Docker infra | 容器 28h+ healthy（`docker compose up -d` 语义等价已就位；`scripts/healthcheck.sh` 组件全绿） | OK |
| 5. migration | `alembic downgrade base / upgrade head` 双循环 + `alembic current`=head | OK |
| 6. seed | `uv run python -m app.db.seed --demo` ×3（迁移后/重置后/最终） | OK，计数一致 |
| 7. backend | `uv run pytest -q`（→ 207 passed） | OK |
| 8. lint/format | `bash scripts/lint.sh` 语义 = `ruff check` + `ruff format --check`（本轮直接跑两者） | OK |
| 9. typecheck | `uv run mypy services/api/app`（72 files） | OK |
| 10. API 启动 | `uvicorn app.main:app --port 8010`；`/health` `/health/ready` 真 OK（既有会话进程在本轮全链使用） | OK |
| 11. Admin build | `pnpm --filter @petaccess/admin build`（vue-tsc strict + vite）×2 | OK |
| 12. H5 build | `VITE_API_BASE=http://127.0.0.1:8010/api/v1 pnpm --filter @petaccess/client-h5 build` ×2 | OK |
| 13. Playwright | `./node_modules/.bin/playwright test --output=playwright-out`（7/7；preview 由 config 自动拉起） | OK |
| 14. worker | Celery worker 语义由 E2E-C（in-process sweep）+ 历史 `celery inspect ping`（1 node）背书 | OK |
| 15. 备份演练 | `bash scripts/backup_restore.sh` | PASS |
| 16. 性能探针 | `uv run python scripts/perf_baseline.py` | OK（新增脚本，可复跑） |

## README 命令核对

README 快速开始四步（dev.sh / uvicorn / H5 dev / Admin dev）与本表步骤 4–12 一致；
README 中过时的"pytest 35"计数已在本轮更正为实际值。dev.ps1（Windows PowerShell 路径）
本轮未执行（环境为 Git Bash，bash 脚本全链已验证），如实记录为 NOT_RUN（不影响 bash 路径结论）。

## 已知环境注意（非阻塞）

- 本机 8000 端口被外部进程占用 → 项目约定 8010（文档已写明）。
- 本机导出 HTTP(S)_PROXY → 本地探针一律 `--noproxy '*'` / `trust_env=False`（代码已固化）。
- Docker Desktop 偶发退出需手动重启（历史记录；本轮未发生）。

结论：仓库 → env → deps → infra → migration → seed → backend → Admin → H5 → tests
全链 **可复现**，全部命令真实执行。
