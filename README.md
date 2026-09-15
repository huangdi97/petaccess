# 宠物准入信息平台 / Place Animal Access Map

> 一句话：让每个人在到达一个地方之前，知道这里关于动物的规则。
> 设计母版：`docs/MASTER_DESIGN_v0.3_DEV.md`（冻结）。

## 快速开始（Windows / macOS / Linux）

前置：Docker Desktop、Python 3.11+（含 uv）、Node 20+（含 pnpm，`npm i -g pnpm`）。

```bash
# 1. 基础设施 + 迁移 + 演示数据（one command infra up）
bash scripts/dev.sh          # Windows PowerShell: 见 scripts/dev.ps1

# 2. 启动 API（默认 8000；被占用时用 8010）
cd services/api && uv run uvicorn app.main:app --reload --port 8000
#   API 文档: http://127.0.0.1:8000/docs

# 3. H5 客户端
cd apps/client-h5 && pnpm install && pnpm dev      # http://localhost:5174

# 4. 管理后台
cd apps/admin && pnpm install && pnpm dev          # http://localhost:5173
```

### One command 基准

| 目标 | 命令 |
|---|---|
| infra up（+迁移+seed） | `bash scripts/dev.sh` |
| 全部测试 | `bash scripts/test.sh`（pytest 209：单测+契约+集成；E2E 见下） |
| lint | `bash scripts/lint.sh`（ruff check + format check） |
| typecheck | `bash scripts/typecheck.sh`（mypy） |
| E2E（需 API:8010 + H5:5175 运行中） | `pnpm exec playwright test` |
| worker | `cd services/api && uv run celery -A app.worker.celery_app:celery_app worker --pool=solo` |

### E2E 前置（API :8010 + 真实数据）

E2E 断言的是真实数据，因此需要 API 与种子数据都在。H5 产物通过**绝对 API 基址**直连
:8010（API 的 CORS 已放行 `http://127.0.0.1:5175`）：

```bash
# 1. 基础设施 + 迁移
docker-compose up -d && cd services/api && uv run alembic upgrade head && cd ../..

# 2. API（E2E 约定 8010）+ worker（OCR/TTL 用例需要）
cd services/api && uv run uvicorn app.main:app --port 8010 &
cd services/api && uv run celery -A app.worker.celery_app:celery_app worker --pool=solo &

# 3. 以 E2E 基址构建 H5，然后运行
VITE_API_BASE=http://127.0.0.1:8010/api/v1 pnpm --filter @petaccess/client-h5 build
pnpm exec playwright test
```

`vite preview` 不会继承 `server.proxy`，因此 `vite.config.ts` 同时声明了 `preview.proxy`
（可用 `VITE_API_PROXY` 覆盖目标），避免相对基址的产物在预览时把 404 误判为应用缺陷。

## 演示账号（种子数据，全部虚构场所）

- 管理员：`admin@demo-petaccess.com` / `admin12345`
- 演示场所：星河咖啡·测试店 / 青岚公园·演示 / 云栖中心·测试商场 / 松风社区·演示
  （含 service dog 差异、规则冲突、废止规则、已认领场所、观察与规则并存）

## 结构

见 `docs/ARCHITECTURE.md`；跨端状态见 `docs/PLATFORMS.md`；
真实状态见 `PROJECT_STATE.md` / `ACCEPTANCE_MATRIX.md` / `BLOCKERS.md`。

## 非谈判原则（实现遵守）

Access 而非 Friendly；Place→Zone→AccessRule；自有 UUID（外部 POI 仅引用）；
Observation 永不变 Rule；服务犬独立；evaluator 确定性；UNKNOWN≠允许/禁止；
不做遇宠率/排行榜/评论区；小区只公共空间规则；不存连续轨迹；
高影响规则必有 Source；demo 全虚构。
