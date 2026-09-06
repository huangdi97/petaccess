# GOAL.md
# 宠物准入信息平台 · ZCode 全程工程目标

> 本文件是 ZCode/AI Coding Agent 的最高执行目标之一。
> 必须先读 `AGENTS.md`、`docs/MASTER_DESIGN_v0.3_DEV.md`、`DECISIONS.md`，再执行本文件。
> 不允许只做脚手架、只写 TODO、只生成页面截图或只输出计划后停止。

---

# 0. 总目标

从当前仓库开始，把《宠物准入信息平台 v0.3 · DEV MASTER》实现成一个**真实可运行、可测试、可本地演示、可继续接真实地图/AI/登录/上架凭证的全栈 MVP/Release Candidate 工程**。

最终至少包含：

- 一个 uni-app x 客户端：
  - Web/H5 可运行；
  - 微信小程序工程可构建；
  - Android 工程具备构建配置；
  - iOS 工程具备构建配置；
  - HarmonyOS 工程具备构建配置；
- 一个 FastAPI API；
- PostgreSQL + PostGIS；
- Redis；
- Celery worker；
- S3-compatible object storage abstraction，本地 MinIO；
- Vue 3 Admin；
- OpenAPI 生成的 TS API client；
- 确定性 Rule Evaluator；
- Pet Profile；
- AI Provider abstraction + Mock；
- Place / Zone / Geometry；
- AccessRule / Condition；
- Source / Provenance；
- ObservationClaim；
- VerificationEvent；
- Operator Claim；
- JurisdictionRule；
- DisputeCase；
- AuditLog；
- WatchSubscription；
- synthetic demo data；
- unit / integration / contract / e2e tests；
- local docker development；
- CI 配置；
- release/check scripts；
- 完整文档和真实状态报告。

---

# 1. 执行纪律

你是执行 Agent，不是顾问。

收到启动指令后：

1. 读取全部控制文档；
2. 检查环境；
3. 初始化 git（如果还没有）；
4. 建立项目结构；
5. 写代码；
6. 安装依赖；
7. 启动基础设施；
8. 运行 migration；
9. 运行测试；
10. 修错；
11. 启动服务；
12. 做端到端验证；
13. 更新状态文档；
14. 继续下一个阶段；
15. 直到所有“不依赖外部人工凭证”的 Gate 都通过。

**不要在每个阶段问用户“要不要继续”。**

---

# 2. 允许的真实外部 Blocker

只有以下类型允许标记 `BLOCKED_EXTERNAL`：

- 地图 Key；
- 短信/微信/Apple/Huawei OAuth 凭证；
- iOS 证书、Apple Developer 账户或 macOS/Xcode；
- HarmonyOS 发布签名/开发者账户；
- Android 商店签名/账户；
- 微信小程序 AppID/类目/隐私接口审批；
- 付费/人工审批地图授权；
- 生产域名/备案/主体隐私政策信息；
- 真实 AI Provider key；
- 法律/合规专业确认；
- 真实场所管理方身份核验；
- 必须真人设备完成的最终 smoke test。

遇到 Blocker：

1. 不停止项目；
2. 建 Mock / Adapter / feature flag；
3. 完成其余所有工作；
4. 在 `BLOCKERS.md` 写：
   - 缺什么；
   - 为什么；
   - 用户要做什么；
   - 拿到后执行什么命令；
   - 影响哪个 Gate。

“没有地图 Key”不能成为不做地图模块的理由。

---

# 3. 冻结技术栈

## Client
- uni-app x
- Vue 3
- TypeScript
- 优先 Vapor/蒸汽模式
- platform adapter

## Map
- provider abstraction
- MVP Tencent
- 自有 Place UUID
- 外部 POI 只 ExternalPlaceRef

## Admin
- Vue 3
- TypeScript
- Vite

## Backend
- Python
- FastAPI
- Pydantic v2
- SQLAlchemy 2
- Alembic
- psycopg3

## Database
- PostgreSQL + PostGIS

## Cache / Jobs
- Redis
- Celery

## Object Storage
- S3-compatible
- local MinIO

## Contract
- OpenAPI 为 SSOT
- TS client 自动生成

---

# 4. 目标 Monorepo

```text
apps/
  client/
  admin/

services/
  api/
  worker/

packages/
  rule-spec/
  api-client/
  design-tokens/

infra/
  docker/
  migrations/

tests/
  contract/
  integration/
  e2e/

docs/
scripts/

AGENTS.md
GOAL.md
DECISIONS.md
IMPLEMENTATION_PLAN.md
ACCEPTANCE_MATRIX.md
PROJECT_STATE.md
BLOCKERS.md
README.md
```

---

# 5. Phase 0 — Repository Foundation

完成：
- git init；
- `.editorconfig`；
- `.gitignore`；
- `.env.example`；
- Docker compose；
- healthcheck；
- dependency lockfiles；
- lint / format / typecheck / test；
- root scripts；
- README。

必须做到：

```text
one documented command → infra up
one documented command → test
one documented command → lint
```

Windows/macOS/Linux 分别有可执行说明。

---

# 6. Phase 1 — Database

实现：
- User
- PetProfile
- Place
- Zone
- PlaceGeometry
- ExternalPlaceRef
- Operator
- OperatorClaim
- AccessRule
- RuleCondition
- Source
- ObservationClaim
- VerificationEvent
- JurisdictionRule
- DisputeCase
- AuditLog
- WatchSubscription

要求：
- UUID；
- timestamps；
- lifecycle；
- FK；
- indexes；
- PostGIS spatial indexes；
- migration；
- rollback；
- repeatable synthetic seed。

禁止：
- 第三方 POI ID 当主键；
- 无 Source 的高影响 Rule；
- Observation 当 Rule。

---

# 7. Phase 2 — Rule Spec & Evaluator

`packages/rule-spec` 定义稳定 Schema。

Animal：
- dog
- cat
- ordinary_pet
- service_dog
- other

Action：
- enter
- pass_through
- stay
- walk
- off_leash
- ground_contact
- ride_elevator
- ride_transport
- use_facility
- dine
- stay_overnight

Effect：
- allowed
- prohibited
- conditional

Condition：
- leash
- muzzle
- carrier
- stroller
- no_ground
- registration
- vaccination
- max_weight
- max_height
- max_count
- reservation
- advance_notice
- designated entrance/elevator/route
- time/date window
- fee
- room restriction

Evaluator 返回：
- MATCH
- CONDITIONAL
- RESTRICTED
- UNKNOWN
- CONFLICT

并包含：
- applied rule IDs；
- unmet conditions；
- unknown inputs；
- source refs；
- reason codes。

单测至少覆盖：
1. 室内禁止/户外允许；
2. 10kg 上限；
3. 未知体重；
4. 时段；
5. 服务犬；
6. Zone 覆盖 Place；
7. superseded；
8. 冲突；
9. 无规则；
10. Observation 与 Rule 共存但不改变 evaluator。

---

# 8. Phase 3 — API

实现：
- auth/session；
- pets CRUD；
- places search/list/detail；
- nearby；
- zone/geometry；
- rules/evaluate；
- source；
- observation；
- verification；
- operator claim；
- regulation；
- dispute；
- watch；
- admin moderation；
- audit。

要求：
- OpenAPI；
- 统一错误格式；
- pagination/filter；
- RBAC；
- rate limit；
- audit；
- 高风险写操作 idempotency；
- 生成 TS client。

---

# 9. Phase 4 — Admin

Admin 必须真实可用：

- 登录；
- Place CRUD；
- Zone；
- Geometry/GeoJSON；
- Rule Editor；
- Source；
- Regulation；
- Contribution Queue；
- Operator Claim Queue；
- Dispute Queue；
- AI Queue；
- Conflict Review；
- Roles；
- Audit；
- Data Quality。

全部连接真实 API，不做静态假后台。

---

# 10. Phase 5 — Client Vertical Slice

H5/Web 先跑通：

Onboarding
→ Create Pet
→ Map/List
→ Search
→ Place
→ Rule Result
→ Zone
→ Contribution
→ Watch

真实地图 Key 缺失时：
- MapProvider Mock；
- synthetic place/geometry；
- 业务逻辑必须真实；
- 一拿到 Key 只切 provider。

不能留空地图 TODO。

---

# 11. Phase 6 — Pet AI

Provider abstraction：

```text
VisionProvider
  classify_pet()
```

Mock 可测试。
真实 provider 环境变量启用。

输出：
- species suggestion；
- breed suggestion；
- user confirmation required。

体重/肩高不能由图像直接写 confirmed。
Service dog 永不由照片自动确定。

---

# 12. Phase 7 — Contribution & Verification

完成：
- Quick Confirm；
- Progressive Disclosure；
- proximity adapter；
- image upload；
- OCR interface；
- moderation；
- duplicate protection；
- withdraw；
- VerificationEvent；
- anti-abuse。

位置：
- 不建立 raw continuous history；
- 保存 bucketed verification result。

---

# 13. Phase 8 — Operator Claim

完成：
- claim request；
- verification status；
- manual review；
- structured questionnaire；
- operator-declared rules；
- versioning；
- operator cannot delete observations；
- dispute entry。

完整演示：

```text
社区创建场所
→ 管理方认领
→ Admin 通过
→ 管理方填规则
→ Place 显示管理方来源
→ 用户仍可提交 Observation
```

---

# 14. Phase 9 — Jurisdiction

完成：
- regulation CRUD；
- jurisdiction scope；
- effective time；
- rule resolution；
- source refs；
- stale review。

严格区分：
- NOT_REVIEWED
- NO_EXPLICIT_RULE_FOUND
- EXPLICIT_OPERATOR_DISCRETION

---

# 15. Phase 10 — Dispute

完成：
- notice；
- evidence；
- temporary action；
- forward abstraction；
- counter statement；
- reviewer；
- resolution；
- restore/correct/archive/delete；
- audit。

E2E 覆盖完整 dispute。

---

# 16. Phase 11 — Watch

- Watch Place；
- Rule new version；
- notification job；
- Mock notification sink；
- real adapter；
- unsubscribe；
- audit。

---

# 17. Phase 12 — Cross-platform

目标：
- Web/H5；
- 微信小程序；
- Android；
- iOS；
- HarmonyOS。

平台差异集中：

```text
platform/
providers/
adapters/
```

不得把平台 if/else 散落在业务页面。

每端完成：
- permission；
- privacy copy；
- map config；
- media config；
- build notes。

无法真实构建：
- 配置/代码/脚本继续完成；
- 精确写 blocker；
- 不伪造 PASS。

---

# 18. Demo Seed

必须有：

### 星河咖啡·测试店
- indoor dog prohibited
- outdoor dog allowed
- leash required

### 青岚公园·演示
- A草坪 leash allowed
- 儿童区 prohibited
- 宠物活动区 allowed
- 夜间 time window

### 云栖中心·测试商场
- 1–4F stroller/carrier
- B1 prohibited
- 3F pet zone
- pet elevator

### 松风社区·演示
- public road leash
- children zone prohibited
- pet activity area
- 无住户数据

另外：
- service dog 与 ordinary pet 规则不同；
- rule conflict；
- stale rule；
- claimed place；
- dispute；
- Observation 与 Rule 不一致但并存。

---

# 19. 测试 Gate

必须实际运行：

Backend：
- pytest unit；
- integration；
- migration；
- API contract。

Frontend：
- lint；
- typecheck；
- unit；
- Web E2E Playwright。

Worker：
- task；
- retry/idempotency。

Security：
- secret scan；
- dependency audit（工具可用时）。

DB：
- migration up/down；
- spatial query；
- repeatable seed。

---

# 20. 性能

MVP：
- nearby spatial index；
- pagination；
- 避免 N+1；
- evaluator 可批量；
- map bbox query；
- marker clustering；
- geometry LOD；
- lazy load source；
- thumbnails。

不提前拆微服务。

---

# 21. Observability

完成：
- structured logs；
- request id；
- health；
- readiness；
- metrics abstraction；
- error capture abstraction；
- worker health；
- DB/Redis health。

---

# 22. 状态文档

每阶段更新：

`PROJECT_STATE.md`
- 当前阶段；
- 已完成；
- 测试结果；
- 实际命令；
- 未完成；
- 外部 blocker；
- 下一阶段。

`BLOCKERS.md`
- 只记录真实外部 blocker。

`DECISIONS.md`
- 架构变化 ADR。

`CHANGELOG.md`
- 结构/用户可见变化。

---

# 23. Definition of Done

## Code
- 无核心 TODO/placeholder；
- 无秘密；
- mock 有明确开关；
- migrations 完整；
- seed 可重建。

## Functional
- H5 核心闭环；
- Admin 审核闭环；
- evaluator 真实；
- PostGIS 真实；
- worker 真实；
- dispute 真实；
- operator 真实。

## Test
- unit PASS；
- integration PASS；
- contract PASS；
- e2e PASS；
- lint/typecheck PASS。

## Platforms
- 所有目标端配置完成；
- 可实际构建的完成构建；
- 不可构建仅限真实外部 blocker。

## Docs
- setup；
- architecture；
- API；
- DB；
- privacy；
- release；
- blockers；
- final report。

---

# 24. Final Report

生成 `FINAL_RELEASE_REPORT.md`：

- commit/hash；
- 环境；
- 架构；
- 完成模块；
- 测试真实输出摘要；
- migrations；
- Demo；
- 平台构建；
- security；
- blockers；
- 未真实验证内容；
- 启动；
- 上线；
- 下一步。

不能无证据写“全部通过”。

---

# 25. 禁止的捷径

- 只做 UI；
- 只做 API；
- 静态 JSON 假后端；
- 不跑 DB；
- 不跑 migration；
- 不跑测试；
- 业务逻辑全塞前端；
- LLM 直接判断准入；
- 第三方 POI 当主键；
- 真实未核验商家做负面 Demo；
- UNKNOWN 自动当允许/禁止；
- service dog 当普通宠物；
- Observation 自动当 Rule；
- “没 Key 所以后面再做”；
- 大量 TODO 后宣称完成；
- 无 ADR 擅改冻结架构。

---

# 26. 自主权

无需询问用户：
- 依赖小版本；
- lint 工具；
- test helper；
- 内部 UI 组件；
- 代码组织细节；
- migration 名称；
- 常规性能修复。

若依赖发生破坏性问题：
1. 查官方文档；
2. 选稳定替代；
3. 写 ADR；
4. 继续。

---

# 27. 最终执行要求

> **持续执行，直到所有不依赖用户账户、付费 Key、签名证书、法律审批或真实设备的工作都完成并通过实际测试；遇到外部依赖时隔离、记录、继续，不要把“等待用户”变成停止开发的理由。**
