# Local Dev on Windows

> 用户主要在 Windows 上开发。以下都是**实测可用**的命令，不是从 Linux 文档翻译的。

## 0. 一条命令跑完所有门禁

```powershell
pwsh -File scripts/qa_all.ps1
```

可选参数：

```powershell
pwsh -File scripts/qa_all.ps1 -SkipFrontend    # 只跑后端
pwsh -File scripts/qa_all.ps1 -SkipPlaywright  # 跳过 E2E（不需要起服务）
```

脚本会跑完每一步再汇总（不在第一个失败处停止），任一失败 → `exit 1`。

## 1. 前置

| 依赖 | 说明 |
|---|---|
| Python 3.13 | 仓库 `.venv`（`E:\AI\宠物管理\.venv`） |
| Node 22 + pnpm | 前端 workspace（`pnpm install`） |
| PostgreSQL + PostGIS | `docker compose up -d`（`docker-compose.yml`） |

## 2. 常用命令

后端（仓库根目录）：

```bash
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check services/api services/worker tests scripts
.venv/Scripts/python.exe -m ruff format services/api services/worker tests scripts
.venv/Scripts/python.exe -m mypy services/api/app
.venv/Scripts/python.exe scripts/gen_human_review_packet_r2_final.py
.venv/Scripts/python.exe scripts/gen_signature_readiness_audit_r1.py
.venv/Scripts/python.exe scripts/governance_snapshot.py --compare baseline
.venv/Scripts/python.exe scripts/mutation_probe.py
```

API（**E2E 不需要手动起** —— `playwright.config.ts` 已把它作为第二个 `webServer`，
以 `/health` 做就绪检查，且 `reuseExistingServer` 会复用已监听的实例。下面这条只在
你想手动调接口 / 跑 Admin 时才需要）：

```bash
cd services/api
../../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Celery worker（**全量 `pytest` 需要**，否则 4 个用例会等到超时）：

```bash
cd services/api
../../.venv/Scripts/python.exe -m celery -A app.worker.celery_app:celery_app worker --pool=solo --loglevel=warning
```

前端：

```bash
pnpm lint:fe
pnpm format:check:fe
pnpm --filter @petaccess/client-h5 build
pnpm --filter @petaccess/admin build     # 内部先跑 vue-tsc --noEmit
pnpm exec playwright test
```

## 3. Windows 专属坑

| 坑 | 表现 | 处理 |
|---|---|---|
| Bash 工具 PATH 被 shim 破坏 | `dirname: command not found`、`cd: null directory` | 每个 bash 调用前置 `export PATH="/c/Program Files/Git/cmd:/c/Program Files/Git/mingw64/bin:/usr/bin:/bin:$PATH"` |
| 中文路径 | 脚本参数含中文（如仓库根 `E:\AI\宠物管理`）时部分工具乱码 | 一律用绝对路径 + 双引号；**不要**为批量文件操作生成 `.ps1`/`.bat` 脚本（编码会坏），直接执行命令 |
| CRLF/LF | 生成器产物被 Prettier 判为改动 | 生成器内部统一 `newline="\n"`；`.prettierignore` 已排除生成物 |
| 长路径 | `node_modules` 深层路径超过 260 字符 | pnpm 默认使用较短的 store 布局；如遇问题启用系统长路径支持 |
| venv 无 pip | `No module named pip`（uv 创建的环境） | `.venv/Scripts/python.exe -m ensurepip --default-pip` |
| 临时目录 | `%TEMP%` 含中文用户名 | 脚本内不手写临时路径，交给 `tempfile`/`tmp_path` |
| H5 构建带了 `VITE_API_BASE` | 打完包后 E2E 全红：bundle 里写死 API 地址，绕过 preview 代理 | **E2E 前用不带 `VITE_API_BASE` 的构建**（`apps/client-h5` 下 `vite build`），让它回落默认的相对 `/api/v1`，由 `playwright.config.ts` 的 `VITE_API_PROXY` 代理到 `:8010` |
| 全量 pytest 看着像卡死 | 停在 40%–50% 不动 | 缺 Celery worker 时 `test_media.py` / `test_v05_e2e.py` 会一直等到超时（fail-closed 设计）。先起 worker，且 `pyproject.toml` 已配 `timeout = 120` 兜底 |

## 4. 生成物的编辑规则

以下文件**由脚本生成，不要手改**（改动会在下次生成时丢失，且会让治理快照漂移）：

- `HUMAN_REVIEW_PACKET_R2_FINAL.md`
- `HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md`
- `HUMAN_REVIEW_DECISIONS_R2_FINAL.json`
- `docs/reality_audit/review_decisions_r2_final.json`
- `HUMAN_SIGNATURE_READINESS_AUDIT.md`

它们都在 `.prettierignore` 中，避免前端 formatter 与生成器互相打架。
