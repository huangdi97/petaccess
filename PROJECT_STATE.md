# PROJECT_STATE.md

## Current phase
PHASE 2 COMPLETE (Rule Spec & Evaluator) — entering Phase 3 (FastAPI full API)

## Last verified
2026-09-06

## Completed
- Phase 0: monorepo (uv Python workspace + Node 结构预留), git init, docker-compose
  (PostGIS 17-3.5 / Redis 7 / MinIO), root scripts, ruff+pytest+mypy 配置, uv.lock.
- Phase 1: 17 张领域表 SQLAlchemy 2 模型；Alembic 初始迁移（含 postgis/pg_trgm 扩展、
  GIST 空间索引、trgm 名称索引）；合成 demo seed（4 虚构场所/15 Zone/规则/来源/观察/
  异议/法规/认领/关注）；FastAPI 应用骨架 + /health + /health/ready。
- Phase 2: packages/rule-spec 5 个 JSON Schema（draft 2020-12）+ cafe fixture；
  app/rulespec 纯确定性 evaluator（无 DB/LLM），Zone 覆盖 Place 特异性解析、
  服务犬与普通宠物 scope 隔离、obligation/threshold/time-window 条件求值、
  UNKNOWN≠允许/禁止、冲突检测。

## Test evidence
- `alembic upgrade head` → 19 tables；`alembic downgrade base` → 2 tables；再 upgrade 成功。
- PostGIS 真查：ST_Distance nearby 返回 4 场所距离（355m/818m/1931m/2728m）；
  ST_Contains 点位命中"A 草坪"；pg_trgm 模糊搜索命中"星河咖啡·测试店"。
- seed 重复运行两次成功（确定性 UUID）。
- uvicorn 冒烟：/health 200, /health/ready 200 (postgres 17.5, postgis 3.5), /api/v1/ping 200。
- `ruff check` PASS；`ruff format --check` PASS；`mypy services/api/app` PASS (22 files)。
- pytest: evaluator 15 passed（GOAL #7 十条全含）+ contract 2 passed
  （JSON Schema 校验 + fixture 三场景期望状态），共 17 passed。

## Actual commands
- `bash scripts/dev.sh` / `docker compose up -d`
- `cd services/api && uv run alembic upgrade head`
- `uv run python -m app.db.seed --demo`
- `bash scripts/lint.sh` / `bash scripts/test.sh` / `uv run mypy services/api/app`

## Known environment notes
- 目录名为中文 → docker compose 必须固定 `name: petaccess`（已写入 compose 文件）。
- .env 中 DB host 使用 127.0.0.1（localhost 解析 ::1 时出现瞬时 No buffer space）。
- 端口 8000 被本机其他进程占用，冒烟测试用 8010；API 默认仍配置 8000。

## Current blockers
None confirmed.

## Next action
Phase 3: FastAPI 全量 API（auth/pets/places/nearby/zones/rules/evaluate/sources/observations/verifications/operators/regulations/disputes/watches/admin）+ RBAC/audit/rate-limit/idempotency + OpenAPI → TS client。
