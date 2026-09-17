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

后端（仓库根目录）。**先固定 PATH 与隔离库环境变量**——现在 pytest 只认 `petaccess_test`，
指向 `petaccess` 会在第一条用例之前就 exit 4：

```bash
export PATH="/c/Program Files/Git/cmd:/c/Program Files/Git/mingw64/bin:/usr/bin:/bin:$PATH"
export PYTHONPATH=
export DATABASE_URL="postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess_test"
export CELERY_TASK_QUEUE=petaccess_test REDIS_URL="redis://127.0.0.1:6379/1" DB_ROLE=TEST
export HYPOTHESIS_STORAGE_DIRECTORY="$TEMP/hyp_storage"

.venv/Scripts/python.exe scripts/isolated_db.py --role TEST --reset   # 需要干净库时
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
以 `/health` 做就绪检查）。手动起时**必须声明角色**：

```bash
cd services/api
PYTHONPATH= ../../.venv/Scripts/python.exe ../../scripts/dev_api_server.py \
  --db-name petaccess_test --role TEST --port 8010

# 指向生产库需要显式授权，否则被拒
PYTHONPATH= ../../.venv/Scripts/python.exe ../../scripts/dev_api_server.py \
  --db-name petaccess --role PRODUCTION --production-confirm --port 8012
```

起完确认它连的是谁：`curl -s http://127.0.0.1:<port>/health/database`。
**指向 `petaccess` 的 dev 服务收工必须杀掉**——本轮就发现一个上轮遗留的
无闸门实例一直连着生产库。角色表见 `docs/engineering/DATABASE_ENVIRONMENT_MODEL.md`。

Celery worker（**全量 `pytest` 需要**，否则 4 个用例会等到超时）：

```bash
cd services/api
DATABASE_URL="postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess_test" \
CELERY_TASK_QUEUE=petaccess_test REDIS_URL="redis://127.0.0.1:6379/1" \
../../.venv/Scripts/python.exe -m celery -A app.worker.celery_app worker \
  --pool=solo --concurrency=1 -Q petaccess_test
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
| 把 SQLAlchemy URL 喂给 psycopg | `dev_api_server.py` 启动即报无法解析 URL | `postgresql+psycopg://` 是 SQLAlchemy 方言前缀，psycopg 不认。探测角色前要走 `psycopg_url_for()` 转成 `postgresql://` |
| 后台服务"启动失败"但其实是好的 | 用 `timeout N` 包一层，N 秒后被杀，退出码 124 | 那是超时杀掉了健康进程，不是崩溃。要长跑就直接用后台任务，不要套 `timeout` |
| 端口被上轮遗留进程占着 | E2E 起不来 / 连到了错误的库 | `netstat -ano \| grep LISTENING \| grep -E ":(8010\|8011\|8012)\b"` 找到 PID，`MSYS_NO_PATHCONV=1 taskkill /PID <pid> /F` |

## 4. 生成物的编辑规则

以下文件**由脚本生成，不要手改**（改动会在下次生成时丢失，且会让治理快照漂移）：

- `HUMAN_REVIEW_PACKET_R2_FINAL.md`
- `HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md`
- `HUMAN_REVIEW_DECISIONS_R2_FINAL.json`
- `docs/reality_audit/review_decisions_r2_final.json`
- `HUMAN_SIGNATURE_READINESS_AUDIT.md`

它们都在 `.prettierignore` 中，避免前端 formatter 与生成器互相打架。
