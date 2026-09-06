# ZCODE_START_PROMPT.md
# 复制以下整段给 ZCode / GLM-5.3 Flash

你现在接手一个从空目录开始的正式全栈工程：**宠物准入信息平台 / Place Animal Access Map**。

不要先问我“想做哪个模块”，不要只给建议，也不要停在脚手架。当前仓库中的设计和控制文件就是你的工程任务合同。你的工作方式必须是：

> **完整读取 → 检查真实环境 → 直接写代码 → 实际运行 → 测试 → 修复 → 更新状态 → 继续下一阶段。**

## 1. 先完整读取

按顺序：

1. `docs/MASTER_DESIGN_v0.3_DEV.md`
2. `AGENTS.md`
3. `GOAL.md`
4. `DECISIONS.md`
5. `IMPLEMENTATION_PLAN.md`
6. `ACCEPTANCE_MATRIX.md`
7. `PROJECT_STATE.md`
8. `BLOCKERS.md`
9. `.env.example`
10. `docker-compose.yml`

不要只读摘要。

读完检查：
- 当前目录；
- git；
- Docker；
- Node；
- Python；
- HBuilderX/uni-app x 条件；
- DevEco/HarmonyOS；
- 当前可实际运行哪些构建。

缺环境就记录，不要因此停掉所有研发。

## 2. 必须正确理解产品

这不是“宠物友好地图”，也不是“避雷平台”。

它是：

> **一个以具体动物/用户需求为查询上下文、以现实空间地图为载体、以结构化准入规则为核心，同时支持携宠、普通宠物限制和服务犬通行，并融合官方规则、管理方声明、现场核验和用户观察的动物准入信息系统。**

最终用户要得到：

> “豆豆可以去这里，但只能进入户外区域，需要牵引；规则来自管理方，最近核验于某日期。”

四种模式必须支持：
- 带宠出行；
- 普通宠物限制；
- 服务犬通行；
- 规则地图。

核心模型：

```text
PetProfile
    ↓
Place
    ↓
Zone
    ↓
AccessRule
    ↓
Deterministic Rule Evaluator
    ↓
ApplicabilityResult
```

并行事实：
- Rule
- Observation
- Source
- Verification
- Jurisdiction
- Operator
- Dispute

绝对不要简化成 `pet_friendly=true/false`。

## 3. 非谈判原则

1. Place 使用平台 UUID。
2. 地图 POI ID 只 ExternalPlaceRef。
3. Observation 永不自动变 Rule。
4. “没人阻止”不能解释成“允许”。
5. Service dog 与 ordinary pet 分开。
6. AI 不做最终准入/法律判断。
7. Rule Evaluator 为确定性代码。
8. UNKNOWN 不能当 allowed/prohibited。
9. 不做遇宠率。
10. 不做排行榜、红黑榜、评论区。
11. 小区只公共空间规则，不住户数据库。
12. 不默认保存连续定位轨迹。
13. 管理方不能直接删除用户 Observation。
14. 高影响 Rule 必须 Source。
15. Demo 默认虚构地点。

技术栈如果真有客观不可行性，必须先给证据并写 ADR，才能调整。

## 4. 冻结技术栈

Client：
- uni-app x
- Vue 3
- TypeScript
- Vapor 优先
- Web/H5、微信、Android、iOS、HarmonyOS

Admin：
- Vue 3 + TypeScript + Vite

API：
- Python + FastAPI
- Pydantic v2
- SQLAlchemy 2
- Alembic
- psycopg3

Data：
- PostgreSQL + PostGIS

Jobs：
- Redis + Celery

Storage：
- S3 abstraction + MinIO

Map：
- MapProvider abstraction
- Tencent first
- 无 Key 时 Mock

AI：
- Provider abstraction
- Mock first
- real key only env

Contract：
- OpenAPI SSOT
- generated TS client

## 5. 立即开始 Phase 0

不要给我重复设计说明。

建立真实 monorepo：
- git
- package manager
- Python env
- Docker
- PostGIS
- Redis
- MinIO
- lint
- format
- typecheck
- test
- root scripts
- healthcheck
- lockfiles

实际运行并修错。

做到：
- one command infra up
- one command test
- one command lint

## 6. Phase 1

数据库实体至少：

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

必须有：
- migrations
- rollback
- spatial indexes
- synthetic seed

## 7. Phase 2

实现 rule-spec 与 evaluator：

Animal / Action / Effect / Conditions。

返回：
- MATCH
- CONDITIONAL
- RESTRICTED
- UNKNOWN
- CONFLICT

并返回：
- applied rules
- unmet conditions
- unknown inputs
- source refs
- reason codes

写并运行充分单测。

## 8. Phase 3

FastAPI 完整 API：
- auth/session
- pets
- places
- nearby
- zones
- geometry
- rules/evaluate
- sources
- observations
- verifications
- operators/claims
- regulations
- disputes
- watches
- admin

统一 error、RBAC、rate limit、audit、idempotency。
生成 TS API client。

## 9. Phase 4

Admin 必须真实连接 API：

- Place
- Zone/Geometry
- Rule
- Source
- Regulation
- Contribution
- Operator Claim
- Dispute
- Conflict
- AI Queue
- Audit
- Quality dashboard

不做静态假页面。

## 10. Phase 5

uni-app x 核心闭环：

- Onboarding
- Pet
- AI确认
- Map
- Mode Switch
- Search
- Filters
- Place Card
- Place Detail
- Zone Map
- Mall Floor/Zone
- Source
- Observation
- Quick Confirm
- Full Contribution
- Upload Signage
- Watch
- My
- Operator Claim
- Dispute

H5 先端到端真跑。

没有地图 Key：
- Mock provider；
- synthetic geometry；
- 地图交互和业务逻辑照做；
- 不允许空 TODO。

## 11. Phase 6 AI

- VisionProvider
- OCRProvider
- Query Parser
- Mock
- real adapter interface

宠物图片：
- species suggestion
- breed suggestion
- 用户确认

禁止：
- 自动 service dog
- 图像估重直接 confirmed

## 12. Phase 7 Contribution

- Progressive Disclosure
- Proximity verify
- Raw location minimization
- Upload
- OCR
- Moderation
- Withdrawal
- Anti-abuse

## 13. Phase 8 Operator

- Claim
- Verify
- Structured questionnaire
- Operator rule versioning
- Observation 独立保留
- E2E

## 14. Phase 9 Jurisdiction

严格区分：
- NOT_REVIEWED
- NO_EXPLICIT_RULE_FOUND
- EXPLICIT_OPERATOR_DISCRETION

法规的时间/空间/作用域必须结构化。

## 15. Phase 10 Dispute

真实流程：
- notice
- evidence
- temporary action
- forwarding
- counter statement
- review
- resolution
- audit

做 E2E。

## 16. Phase 11 Watch

- subscribe
- rule version event
- worker
- mock notification
- unsubscribe

## 17. Phase 12 Cross-platform

- H5
- 微信
- Android
- iOS
- HarmonyOS

平台差异集中到 adapter/provider。

无法真实构建某端时：
- 代码配置继续完成；
- blocker 精确记录；
- 不伪造 PASS。

## 18. Demo 场景

用虚构数据：

### 星河咖啡·测试店
- 室内 dog prohibited
- 户外 allowed
- leash

### 青岚公园·演示
- A草坪 leash allowed
- 儿童区 prohibited
- 宠物区 allowed
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
- 无住户信息

另外：
- service dog 规则差异
- conflict
- stale
- claimed
- dispute
- Observation 与 Rule 不一致但并存

## 19. UI 目标

不要把前端做成数据库表格。

优先给用户一句答案：

```text
对于：豆豆 · 柴犬 · 9.5kg

有条件进入

室内：普通犬限制
户外：可进入 · 需牵引

来源：管理方
最近核验：...
```

公园：
- polygon zone

商场：
- floor/zone
- pet entrance
- pet elevator

限制模式：
- 只表达规则明确限制普通宠物
- 不承诺现场绝对无动物

## 20. 质量纪律

每 Gate：
- 实际命令
- 实际输出
- 实际状态

持续更新：
- PROJECT_STATE.md
- ACCEPTANCE_MATRIX.md
- BLOCKERS.md
- DECISIONS.md

不要核心 TODO。
不要伪完成。

## 21. 只有这些事情允许需要我

- 地图真实 Key
- OAuth
- Apple/Huawei/微信开发者账号
- 签名
- 生产域名/备案
- 真实 AI key
- 法律审批
- 真实管理方认证
- 必须真人设备操作

即使遇到：
- Mock
- interface
- tests
- docs
- 继续其他 Phase

## 22. 最终验收

只有以下真实完成后才能写 RC：

- API 真跑
- DB 真跑
- migration 真跑
- PostGIS 真查
- H5 E2E 真跑
- Admin 真操作
- evaluator 真测试
- worker 真执行
- dispute 真闭环
- operator 真闭环
- security 基础完成
- 平台 build 或真实 blocker
- 文档完整

最后生成 `FINAL_RELEASE_REPORT.md`，写清：
- 完成
- 测试证据
- 未真实验证
- blocker
- 用户仅剩人工步骤
- 凭证拿到后的命令

## 23. 现在开始

**现在立即检查仓库并执行 Phase 0。持续做、实际运行、修复错误并推进下一 Gate。除非遇到真正的外部 Blocker，不要问我是否继续。**
