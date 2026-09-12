# ZCODE_CONTINUE_PROMPT_v0.5.md

你现在接手的是一个**已经完成本地 RC 的现有仓库**，不是从零开始。

当前历史可信状态来自 `FINAL_RELEASE_REPORT.md`：
- Phase 0–13 已完成；
- 30 pytest PASS；
- 5 Playwright PASS；
- Alembic up/down/up 已执行；
- PostGIS、Redis、Celery、Admin、H5 已真实验证；
- 报告基线 commit 是 `95c357e`；
- 未真实完成项包括 uni-app x 五端编译、真实腾讯地图、真实 AI、OAuth/短信、生产部署、MinIO 图片上传完整链路。

你的任务是**增量完成下一阶段**，不要推倒重做。

## 1. 必读
依次完整读取：
1. `FINAL_RELEASE_REPORT.md`
2. 原 `GOAL.md`
3. `AGENTS.md`
4. `DECISIONS.md`
5. `PROJECT_STATE.md`
6. `ACCEPTANCE_MATRIX.md`
7. `BLOCKERS.md`
8. `docs/PLATFORMS.md`
9. `NEXT_GOAL_v0.5.md`
10. `docs/V05_ARCHITECTURE_DELTA.md`
11. `docs/DATA_PIPELINE_SPEC.md`
12. `docs/RULE_RESOLVER_SPEC.md`
13. `docs/COEXISTENCE_BOUNDARY_SPEC.md`
14. `docs/PROVIDER_HARDENING_SPEC.md`
15. `docs/REALITY_AUDIT_PLAN.md`
16. `docs/MIGRATION_SPEC_v0.5.md`
17. `docs/TEST_PLAN_v0.5.md`
18. `ACCEPTANCE_MATRIX_v0.5.md`

## 2. 先 Baseline Freeze
修改核心代码前先重跑：
- pytest
- Playwright
- lint
- mypy
- Admin build
- H5 build
- migration
- PostGIS
- Redis/Celery

创建 `BASELINE_FREEZE_V05.md`。
基线失败先修，不在红色基线上做域模型升级。

## 3. 按顺序执行
### Track A — RC-HARDENING-01
- MinIO 真实上传→对象元数据→OCR/审核→TTL 删除
- TencentMapProvider 真 adapter 代码与 fixture contract tests
- AI provider adapters contract tests
- backup/restore 真演练
- observability/retry/failed job visibility

没有 Key 只允许 live smoke Blocked，不能成为 adapter 代码没写的借口。

### Track B — V05-DOMAIN-01
实现：
- RuleLayer
- EffectiveRuleResolver
- RuleCandidate
- DataSourceJob
- SourceMonitor
- FreshnessPolicy
- CoexistencePolicy
- BoundaryProfile
- BoundaryMatcher
- Amenity
- Entrance
- AccessPath
- Organization
- PolicyTemplate
- Place/Zone Override
- Event/Temporary Rule
- DataLicense
- PetAccessJSON
- Answerability

全部落到：
- migration
- ORM/domain
- API
- Admin
- H5/client-core
- tests
- docs

### Track C — PILOT-READINESS-01
- 三条数据生产 E2E
- Reality Audit CLI/API
- import template
- schema gap report
- adversarial fixtures
- data quality dashboard

## 4. 永久原则
- Observation 永不自动变 Rule
- UNKNOWN 不自动 allowed/prohibited
- Service dog 独立
- Place 自有 UUID
- 不做遇宠率
- 不做排行榜/评论区
- 不做卫生/文明评分
- 小区不存住户
- 不连续追踪位置
- 高影响 Rule 有 Source
- Demo 默认虚构

## 5. 共处边界必须中性
可以记录：
- 是否允许普通宠物进入室内堂食
- 是否允许上顾客座椅
- 是否允许上桌
- 是否进入自助取餐区
- 是否使用顾客餐具

不能写平台结论：
- 恶心
- 不文明
- 卫生差

## 6. RuleCandidate 是硬边界
任何 OCR / AI / URL monitor / 用户上传 / 外部线索提取：
必须先 RuleCandidate → Review → Publish。
AI 不得直接写正式 Rule。

## 7. BoundaryProfile 不做总分
只能逐条：
- MATCH
- CONFLICT
- UNKNOWN
并解释原因。

## 8. 迁移
优先 additive。
保留旧 API。
backfill 幂等。
up/down/up。
无法确定的旧数据映射为 REVIEW_REQUIRED/UNKNOWN，不猜。

## 9. 每个 Gate 真实执行
持续更新：
- `PROJECT_STATE_V05.md`
- `ACCEPTANCE_MATRIX_v0.5.md`
- `BLOCKERS.md`
- `DECISIONS.md`

PASS 必须有实际命令证据。

## 10. 只有这些允许外部 Blocker
- 地图 Key
- AI Key
- HBuilderX/特定 SDK
- 微信/Apple/Huawei/Android 账号和签名
- 生产域名/备案
- 法律专业确认
- 真实管理方身份
- 必须真人设备操作

遇到后：记录、Mock/fixture、继续其他工作。

## 11. 最终
所有本地可完成 Gate PASS 后生成：
`V05_FINAL_REPORT.md`

报告必须写：
- baseline
- migrations
- 新实体
- resolver
- candidate pipeline
- media E2E
- source monitor
- coexistence/boundary
- admin
- H5
- tests
- real provider status
- blockers
- pilot readiness

现在开始。不要重新解释方案。立即读取仓库、跑 baseline、创建 `BASELINE_FREEZE_V05.md`，然后持续执行。
