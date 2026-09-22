# PROJECT_STATE.md

## Current phase
v0.9-R1 Reality Layer 落地中（后端 P0 完成；本会话新增 Divergence /
CoexistenceSnapshot / 前端 Reality 消费面 / Admin Reality；DB 侧 BLOCKED_EXTERNAL）

## Reality Layer (v0.9-R1)
- M3 `4841d66`：枚举 + 4 表（reality_candidate / observed_presence /
  staff_response_observation / animal_facility，迁移 `2c7ea6ca8e30` additive）+ 纯
  确定性 freshness 引擎 + RealityAnswer 消费聚合 + admin 候选队列与人工裁决端点
  （MODERATOR 角色、reviewer/decided_at 落库、`reality.decision` 审计）
- `24b08ce`：create 候选审计链补全（flush → record_audit）+ ADR-028
- 红线（测试钉死）：AI 永不写 reality_decision；空记录 ≠ 没有动物；单观察 ≠ 频率；
  过期事实不呈现为近期；staff 身份只存 actor_role；Observation ≠ Rule
- **2026-09-22 会话（本会话）新增**：
  - AC8 RuleRealityDivergence（六状态，纯函数 + 37 测试）
  - AC9 CoexistenceSnapshot 统一聚合（service + `POST /places/{id}/coexistence`
    端点 + 10 测试）；Home/Search/Map/Place 一律消费同一快照
  - AC10 H5 消费面：Home 一级入口（你更想先看什么？）、Place 第一屏 RealityPanel、
    Search lens、Contribute Reality 三分支（我刚刚看到动物 / 工作人员怎么处理 /
    动物相关设施）→ `POST /places/{id}/reality/contributions`
  - AC11 Admin Reality：Dashboard / CandidateQueue / Claims 三页面 + 路由 + 导航
  - client-core 新增 RealityAnswer / CoexistenceSnapshot 类型与 4 个 API 方法
  - 非 DB 测试子集：**75 passed**（28 存量 + 47 新增）；ruff 全绿；
    mypy 96 files / 0 errors；H5/Admin vue-tsc + build 通过
- 待办：DB 环境就绪后 `alembic upgrade head` 真实验证（本轮 Docker daemon 不可达，
  为 BLOCKED_EXTERNAL，见 BLOCKERS.md LOCAL_DOCKER_DESKTOP_ENGINE_UNSTABLE）；
  Playwright / 全量 pytest / 30-Place Reality Audit 等 DB 依赖项


## Completed（全部 13 个 Phase 的本地可实现部分）
- Phase 0: monorepo（uv workspace + pnpm workspace）、docker compose（PostGIS/Redis/MinIO）、
  根脚本、ruff/mypy/pytest、uv.lock + pnpm-lock。
- Phase 1: 17 表 + Alembic up/down + PostGIS/trgm 索引 + 可重复 seed（4 虚构场所 + 全演示状态）。
- Phase 2: rule-spec 5 个 JSON Schema + 纯确定性 evaluator + 15 单测（GOAL #7 十条）+ 契约测试。
- Phase 3: FastAPI 全量 API（13 组路由 / OpenAPI 50 路径）+ RBAC/audit/rate-limit/idempotency
  + openapi-typescript TS client。
- Phase 4: Admin（Vue3+Vite+TS）：登录/质量看板/场所/规则/来源/法规/认领/异议/观察/
  AI 队列/冲突/审计/用户，全部真连 API；vue-tsc strict + build 通过。
- Phase 5: client-core（平台无关业务核心）+ client-h5（浏览器真跑闭环）+
  uni-app x 源码工程（7 页面 + adapter；HBuilderX 构建见 B-01）。
- Phase 6: Vision/OCR/Map/Notification Provider 抽象 + Mock（确定性、跨进程可验证）。
- Phase 7: 快速贡献/渐进披露/幂等/限流（30/h→429 实测）。
- Phase 8: 认领→批准→问卷→operator 规则版本化（取代所有现行规则）；观察保留不可删。
- Phase 9: 法规四态 review_status（NOT_REVIEWED 等严格区分）+ 审核流。
- Phase 10: Dispute 全流程（提交→临时措施→反声明→办结→审计）。
- Phase 11: Celery worker 真跑：规则变化通知 + mock sink 落 Redis + 幂等不重复。
- Phase 12: 跨端配置与说明（docs/PLATFORMS.md）。
- Phase 13: Playwright E2E 5/5；pip-audit/pnpm audit 0 漏洞；文档齐备。

## Test evidence（真实命令与结果）
- `uv run pytest -q` → **30 passed**（15 evaluator 单测 + 2 契约 + 13 集成）；Playwright E2E 另计 5 passed
- `pnpm exec playwright test` → **5 passed**
- `bash scripts/lint.sh` → All checks passed（ruff check + format）
- `uv run mypy services/api/app` → 54 files, no issues
- `pnpm --filter @petaccess/admin build` / `client-h5 build` → vue-tsc + vite build 通过
- alembic upgrade head / downgrade base / upgrade head → PASS
- PostGIS 真查：ST_DWithin nearby、ST_Contains 点在"A 草坪"、trgm 模糊搜索 → PASS
- Celery：notify_rule_changes → {'notified_watches': 1}，Redis 有通知，二次 0

## Known environment notes
- 本机 8000 端口被外部进程占用 → 文档统一用 8010 跑 API 示例（不影响交付配置）。
- Docker Desktop 在本机偶发退出（会话中重启过一次）；容器卷数据持久。
- .env 使用 127.0.0.1 避免 localhost→::1 的瞬时连接问题。

## Current blockers
见 BLOCKERS.md（B-01..B-07，全部为真实外部凭证/工具项）。

## Next action
用户侧：HBuilderX 安装（B-01）→ uni-app x 全端构建验证；真实 Key 到位后切 Provider。

## Truth rule
Never infer PASS.
