# 架构说明（Architecture）

> 唯一设计母版：`docs/MASTER_DESIGN_v0.3_DEV.md`。本文只描述工程落地结构。

## 总览

```text
┌─ apps/client (uni-app x 源码, HBuilderX→5端)
│   └─ 共享 ↓
├─ packages/client-core (平台无关业务核心)
├─ apps/client-h5 (Vite H5 验证应用, Playwright E2E)
├─ apps/admin (Vue3+Vite 管理后台, 真连 API)
├─ packages/api-client (OpenAPI SSOT 生成的 TS 类型 + 轻封装)
├─ services/api (FastAPI + SQLAlchemy 2 + Alembic + PostGIS)
│    └─ app/
│        ├─ rulespec/        纯确定性规则引擎（无 DB/LLM）
│        ├─ models/          17 张领域表
│        ├─ api/v1/          13 组路由
│        ├─ core/            auth/RBAC、audit、ratelimit、idempotency、errors
│        ├─ providers/       Map/Vision/OCR/Notification 抽象 + Mock
│        └─ worker/          Celery：关注变化通知、图片 TTL
├─ packages/rule-spec (JSON Schema 契约 + fixtures)
└─ infra/docker (initdb 扩展)
```

## 核心链路

```text
PetProfile/QueryContext → Place → Zone → AccessRule(conditions)
    → rulespec.evaluator (确定性) → ApplicabilityResult
    → 前端一句答案 + 分区域明细 + Source/最近核验
```

- **判定只发生在 `app/rulespec/evaluator.py`**：纯函数，输入 QueryContext+Rule 列表，
  输出 MATCH/CONDITIONAL/RESTRICTED/UNKNOWN/CONFLICT + applied rules +
  unmet conditions + unknown inputs + source refs + reason codes。
- **特异性规则**：zone 级规则按 (animal_scope, action) 遮蔽 place 级规则；
  服务犬 scope 与普通宠物隔离（ADR-005/019）。
- **并行事实**：ObservationClaim/VerificationEvent 与 Rule 并存，永不参与 evaluator；
  管理方不能删观察，只能走 Dispute 流程。
- ** UNKNOWN ≠ 允许/禁止**：缺输入（如体重）返回 unknown_inputs，由前端提示补充。

## 数据模型（17 表）

User, PetProfile, Place, Zone, PlaceGeometry(PostGIS), ExternalPlaceRef,
Operator, OperatorClaim, AccessRule, RuleCondition, Source,
ObservationClaim, VerificationEvent, JurisdictionRule, DisputeCase,
AuditLog, WatchSubscription。迁移：`services/api/migrations/`（up/down 已验证）。

## 横切关注

- 统一错误：`{"error": {code, message, request_id, details}}`（core/errors.py）
- RBAC：user < operator < trusted_verifier < moderator < admin（core/security.py）
- 审计：高影响操作写 audit_log（before/after 状态）
- 限流：Redis 滑窗（observations 30/h, verifications 20/h）
- 幂等：Idempotency-Key → Redis 24h（observations/verifications）
- 隐私：位置仅一次性使用，存分桶结果（distance_bucket/accuracy_bucket），
  无连续轨迹；小区无住户数据；服务犬仅用户声明。

## Provider 抽象（Mock first）

`app/providers/factory.py` 按 .env 选择；真实 Key 到位只改 factory/adapter
（Map: 腾讯优先 B-04；Vision/OCR: B-05；Notification: mock sink 写 Redis）。

## 合同

FastAPI OpenAPI = SSOT → `packages/api-client`（openapi-typescript 生成 50 路径）。
再生成：启动 API 后 `pnpm --filter @petaccess/api-client generate`。
