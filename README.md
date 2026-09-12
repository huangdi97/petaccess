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
| 全部测试 | `bash scripts/test.sh`（pytest 207：单测+契约+集成；E2E 见下） |
| lint | `bash scripts/lint.sh`（ruff check + format check） |
| typecheck | `bash scripts/typecheck.sh`（mypy） |
| E2E（需 API:8010 + H5:5175 运行中） | `pnpm exec playwright test` |
| worker | `cd services/api && uv run celery -A app.worker.celery_app:celery_app worker --pool=solo` |

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
