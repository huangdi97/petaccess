# AGENTS.md
# AI Coding Agent 工程规则

## 阅读顺序
1. `docs/MASTER_DESIGN_v0.3_DEV.md`
2. `GOAL.md`
3. `DECISIONS.md`
4. `IMPLEMENTATION_PLAN.md`
5. `ACCEPTANCE_MATRIX.md`
6. `PROJECT_STATE.md`
7. `BLOCKERS.md`

然后检查代码和 git 状态。

## 核心约束
- Access，不是 Friendly。
- Place → Zone → AccessRule。
- 自有 Place UUID。
- Observation != Rule。
- Service dog != ordinary pet。
- AI != final rule judge。
- UNKNOWN != allowed/prohibited。
- 小区不记录住户。
- 不做遇宠率。
- 不长期默认保存位置轨迹。
- 高影响 Rule 必须有 Source。
- 管理方声明与用户观察并存。
- Demo 默认虚构场所。

## Python
- type hints
- Ruff
- pytest
- SQLAlchemy 2
- Pydantic v2
- domain logic 与 HTTP 分离
- evaluator 尽量 pure

## TypeScript
- strict
- Composition API
- business logic 抽离页面
- generated API client
- platform adapter

## Database
- migration first
- FK / indexes
- PostGIS index
- audit timestamps

## Provider
必须 interface + adapter：
- Map
- AI/Vision/OCR
- Storage
- Notification
- Auth

开发环境默认 mock/local。

## Secrets
绝不 commit：
- API key
- private key
- production credentials

## 测试
每完成可验证单元就运行。
Phase 完成跑全量适用测试。
FAIL 必须修复或真实记录 blocker。

## 状态
PASS = 实际执行成功。
BLOCKED_EXTERNAL = 外部条件缺失。
NOT_RUN = 没跑。
PARTIAL = 有缺失。

## Git
无 git 就 init。
阶段性可本地 commit。
无 remote 不阻塞。
无授权不伪造 push。

## ADR
不要删除设计母版。
架构变化写 DECISIONS.md。
不要“简化”掉 source/audit/dispute/zone/evaluator。
