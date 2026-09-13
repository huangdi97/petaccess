# WORKBUDDY_PRODUCTION_MASTER_GOAL.md
# 宠物准入与公共空间共处规则平台
# Production Master Goal
# 从当前 R2 状态持续做到“可上线”

> 执行对象：WorkBuddy + DeepSeek-v4-flash
> 执行方式：在当前真实仓库继续，不从零重建。
> 当前真实起点：REAL_DATA_PILOT_10_R2 已完成。
>
> 当前已知状态：
> - Evidence completeness = 93.9%
> - 33 RuleCandidate 全部 REVIEW_PENDING
> - 3 ObservationCandidate lead-only
> - Published = 0
> - SG-REAL-01 已修复
> - service dog 7/7 正确
> - Reality Audit R2 = 10/10 可表达，0 resolver error
> - tests 238/238，ruff/mypy 全绿
> - R2 Gate = PASS（有条件）
>
> 本 Goal 的终局不是“代码基本完成”，而是：
>
> **完成一个可以在上海试点范围公开上线的、具有真实数据、真实审核、真实地图/证据链、完整 UI/UX、生产部署、监控、隐私与回滚能力的产品。**
>
> 第一公开版本建议定位：
> **上海中心城区试点 Beta**
> 不得把 30–50 Place 的数据包装成“全上海/全国完整覆盖”。

---

# 0. 总执行纪律

1. 不重建项目。
2. 不 reset/clean 覆盖现有 ZCode/WorkBuddy 修改。
3. 先读真实仓库、真实 Git、真实状态文件。
4. 任何 PASS 必须有真实验证。
5. 不因为 UI 改造破坏现有 Rule/Evidence/Data 逻辑。
6. 不因为追求上线速度降低 Evidence 门槛。
7. 不因为外部 Key/账号阻塞本地可完成工作。
8. 不自动 Publish 未审核 Rule。
9. AI 永远只做 extraction/candidate，不做最终规则裁决。
10. 任何涉及法律效力、隐私条款、平台资质的最终结论只能标注“需专业/平台最终确认”，不能伪造“已合法合规”。
11. 每完成一个阶段：
    - 更新状态文件
    - 跑相关测试
    - 小步 commit
    - 记录证据
12. 不反复问我“要不要继续”，除非确实缺少无法替代的外部账号/证书/人工审批。

---

# 1. 首先做 Production Takeover Audit

立即执行：

```bash
git status
git diff --stat
git diff
git diff --cached
git log --oneline -30
git rev-parse HEAD
```

读取当前所有存在的：

- FINAL_RELEASE_REPORT.md
- V05_FINAL_REPORT.md
- REAL_DATA_PILOT_10_REPORT.md
- REAL_DATA_PILOT_10_R2_REPORT.md
- REAL_DATA_FINAL_REPORT.md
- REAL_DATA_PILOT_STATE.md
- PROJECT_STATE.md
- PROJECT_STATE_V05.md
- ACCEPTANCE_MATRIX.md
- ACCEPTANCE_MATRIX_v0.5.md
- DECISIONS.md
- BLOCKERS.md
- REVIEW_WORKLIST_R1.md
- EVIDENCE_REPAIR_LOG_R1.md
- SCHEMA_GAPS.md
- 当前 migrations
- 当前 tests
- 当前 UI/client/admin
- provider adapters
- deployment/infra
- docs

创建：

`PRODUCTION_TAKEOVER_REPORT.md`

必须写：
- actual HEAD
- dirty files
- latest tests
- current published counts
- current real place counts
- current blockers
- first executable task

---

# 2. 总阶段

严格按顺序：

```text
P0  Review / Publish 10-Place R2
P1  30–50 Real Place Expansion
P2  Product UX Freeze
P3  UI / Frontend Production Redesign
P4  Admin / Data Ops Productionization
P5  Real Provider Integration
P6  Backend Production Hardening
P7  Security / Privacy / Compliance
P8  Performance / Reliability / Observability
P9  Cross-platform Build & Device QA
P10 Staging Deployment
P11 Launch Candidate / UAT
P12 Production Release
P13 Post-launch Safeguards
```

不得跳过 P0/P1 直接“上线”。

---

# P0 — PILOT-REVIEW-PUBLISH-01

## 2.1 33 RuleCandidate Review

对全部 33 条逐条 Review。

检查：
- EvidenceBundle
- SourceArtifact
- URL
- issuer
- quote
- hash
- place match
- zone match
- effective time
- evidence strength
- data license
- conflicts
- freshness
- schema support

每条写：
- reviewer
- reviewed_at
- decision
- reason
- evidence_summary
- place_match_summary
- license_summary

禁止无审查批量 APPROVE。

## 2.2 Manner 错归因

确认 R2 contradiction。
若一致：
- REJECT
- reason = PLACE_ATTRIBUTION_ERROR
- 保留审计历史

## 2.3 两条 search snippet

主动补证：
1. 官方/管理方
2. 政府
3. 原始新闻
4. 合法现场证据

找不到：
- 继续 pending
- 不 Publish

## 2.4 ObservationCandidate

当前 3 条：
- lead-only
- 不自动发布
- 不转 Rule

## 2.5 Pre-Publish Validation

至少六检：
- evidence
- place
- schema
- conflict
- freshness
- license

并额外：
- status=APPROVED
- no duplicate publish
- no self-supersede
- RuleException valid

## 2.6 第一轮小批量 Publish

先发布 10–20 条最干净 Rule：
优先：
- 法规
- 政府
- 官方场所
- 官方品牌/酒店

不发布：
- search snippet only
- social lead only
- unresolved conflict
- unresolved P0 gap

## 2.7 发布验证

逐条检查：
- AccessRule created
- candidate↔rule linkage
- source/evidence
- version
- audit
- resolver
- effective-rules
- client display
- rollback/withdraw
- supersession
- watch

## 2.8 P0 输出

生成：
- REAL_DATA_REVIEW_DECISIONS_R1.md
- REAL_DATA_PUBLISH_R1_REPORT.md
- PUBLISHED_RULES_SNAPSHOT_R1.md

Gate：

```text
PILOT_REVIEW_PUBLISH_GATE = PASS
```

不 PASS 不进入 P1。

---

# P1 — 30–50 REAL PLACE EXPANSION

目标约 40 Place，最少 30，最多 50。

按 10 Place 一批：

```text
+10
→ Reality Audit
→ Review
→ Publish Gate
→ Regression

+10
→ ...
```

## 3.1 场所结构

建议最终：

- 餐饮/咖啡：18–22
- 商场：5–7
- 公园/绿地：5–7
- 酒店：3–5
- 景区/公共设施/其他：3–5

## 3.2 中性采样

必须包含：
- allowed
- prohibited
- conditional
- unknown
- conflict
- stale
- superseded
- temporary/event

不要只搜“宠物友好”。

## 3.3 复杂规则覆盖

主动寻找：
- weight
- height
- count
- leash
- muzzle
- carrier
- stroller
- no-ground
- designated entrance
- designated elevator
- designated route
- time window
- event
- service dog exception
- hotel fee/deposit
- room restriction
- indoor/outdoor
- coexistence
- legal/operator conflict

## 3.4 Evidence First

每条正式 Rule：
- 100% Source
- 100% EvidenceBundle
- 100% place match evidence
- 100% audit
- 100% publish gate

## 3.5 扩量 Gate

最终要求：

- direct-or-strong evidence >= 90%
- Published Rule evidence = 100%
- Place attribution error <= 3%
- AI major extraction error <= 5%
- Unauthorized source usage = 0
- Critical resolver errors = 0
- Common rule expressibility >= 90%
- Answerable Place Rate >= 80%
- AI direct publish = 0
- unresolved P0 schema gap = 0

生成：

- REALITY_AUDIT_REAL_01.md
- REAL_DATA_30_50_FINAL_REPORT.md
- SCHEMA_GAPS_REAL_01.md
- SOURCE_LICENSE_REAL_01.md
- REAL_WORLD_REGRESSION_SUMMARY.md

Gate：

```text
REAL_DATA_30_50_GATE = PASS
```

---

# P2 — PRODUCT UX FREEZE

这一阶段不要先写代码。

先冻结用户产品结构。

产品定位：

> **中性的宠物准入与公共空间共处规则地图。**
> 去之前，把边界看清楚。

长期后台是 Pet Access Network；
C 端第一版保持简单。

## 4.1 一级用户任务

必须服务 3 类任务：

### A. 带宠查询
“我的宠物能不能去？”

### B. 空间边界查询
“这里普通宠物能到哪里、做到什么程度？”

### C. 直接看规则
“这个地方现在怎么规定？”

不要设计成“爱宠 vs 反宠”。

## 4.2 主导航

推荐 4 个 Tab：

1. 地图
2. 搜索/发现
3. 贡献
4. 我的

如果现有 IA 更好，可以保留，但必须给出 UX rationale。

## 4.3 首页 / 地图

必须包含：

- 搜索框
- 当前区域
- 当前 pet profile / boundary profile 状态
- 轻量模式切换：
  - 带宠查询
  - 空间边界
- 地图
- marker clustering
- bottom sheet
- filter chips
- 定位
- list/map toggle
- data coverage hint

禁止：
- 红黑榜
- “雷店”
- “文明/不文明”
- 遇宠率

## 4.4 Place Card

卡片优先显示：

```text
Place name
Place type

当前查询结果：
允许 / 有条件 / 限制 / 未知

最关键 1–2 个条件

来源 badge
最近核验时间
```

不要显示综合评分。

## 4.5 Place Detail

首屏只回答五个问题：

1. 能不能进入
2. 哪里能进入
3. 需要什么条件
4. 共处边界
5. 来源/更新时间

第二层展开：
- Zone
- Entrance / AccessPath
- Amenity
- Law / Operator policy
- Observation
- Version history
- Evidence summary
- Dispute/correction

## 4.6 Coexistence UX

餐饮首批展示：
- 室内堂食
- 户外
- 顾客座椅
- 桌面
- 食品取用区
- 自助区
- 顾客餐具
- 宠物专用餐具
- 独立区域
- 分隔方式

使用中性文案：
- 明确允许
- 明确限制
- 有条件
- 未说明
- 尚未核验

不要用：
- 脏
- 卫生差
- 不文明
- 恶心

## 4.7 Boundary Profile

用户可设置：
- 室内普通宠物：接受/不接受/不在意
- 户外
- 座椅
- 自助食品区
- 餐具
- 独立区域偏好

输出：
- MATCH
- CONFLICT
- UNKNOWN

禁止百分比分数。

## 4.8 Pet Profile

支持：
- dog/cat/other
- breed optional
- weight
- shoulder height
- count
- carrier/stroller
- service role separately

AI recognition:
- 只能建议
- 用户确认
- 不自动认 service dog

## 4.9 Contribution

用户贡献流程要短：

入口：
- 规则仍然有效
- 规则变了
- 我看到现场告示
- 我知道这个地方的规则
- 我有现场经历

优先结构化，不做自由评论区。

## 4.10 Empty / Unknown

必须清晰：

> 尚未核验
> 截至 YYYY-MM-DD，在已核验来源中暂未找到明确规则

不要把 Unknown 显示成“允许”。

## 4.11 UX 输出

生成：

- PRODUCT_IA.md
- UX_FLOW.md
- COPY_GUIDE.md
- UI_STATE_MATRIX.md
- FRONTEND_ACCEPTANCE.md

Gate：

```text
PRODUCT_UX_FREEZE = PASS
```

---

# P3 — UI / FRONTEND PRODUCTION REDESIGN

目标：
> 不只是“能用”，而是达到可以公开 Beta 上线的完整产品质量。

当前技术栈继续：
- uni-app x
- Vue 3
- TypeScript
- client-core
- H5
- 微信
- Android/iOS/HarmonyOS 共享核心逻辑

不要无必要重写框架。

## 5.1 Design System

建立：

```text
packages/design-tokens
或现有合理位置
```

至少定义：
- typography
- spacing
- radius
- elevation
- color tokens
- semantic status tokens
- icon size
- motion duration
- breakpoints

## 5.2 视觉方向

建议：
- 清洁、克制、城市地图工具感
- 中性，不“萌宠化”
- 不用大面积粉色/爪印/卡通
- 不把 prohibited 设计成“坏店警告”
- 强调信息层级和证据来源

## 5.3 状态颜色

允许用语义色，但必须：
- 有文字/图标辅助
- 不仅靠颜色
- contrast 合格
- 禁止价值化“红榜绿榜”

推荐语义：
- allowed
- conditional
- restricted
- unknown
- source verified
- stale
- conflict

## 5.4 必须完成页面

### Consumer
- Splash / boot
- onboarding
- location permission
- map home
- search
- filters
- list view
- place card
- place detail
- zone detail
- route/path
- pet profile
- boundary profile
- contribution
- photo evidence upload
- contribution status
- watch/favorites
- notifications
- settings
- privacy/data controls
- about/data methodology
- correction/dispute
- empty/loading/error/offline

### Operator
若 B 端单独 Web：
- claim status
- basic policy
- zone policy
- temporary policy
- amenities
- entrances
- access paths
- preview
- publish/version
- disputes

### Admin
- Candidate review
- Evidence viewer
- source monitor
- data jobs
- rule conflict
- freshness
- organizations
- templates
- publish
- rollback
- data quality

## 5.5 UI 状态完整性

每个核心页面必须有：
- loading
- skeleton
- empty
- success
- partial data
- stale
- conflict
- error
- offline
- permission denied

## 5.6 Responsive

至少：
- mobile portrait
- mobile landscape basic
- tablet reasonable
- desktop H5
- Admin desktop

## 5.7 Accessibility

至少：
- keyboard for H5/Admin
- focus states
- aria where supported
- text contrast
- touch target
- font scaling
- not color-only
- reduced motion where practical

## 5.8 Visual Regression

如果当前工具链适合：
- Playwright screenshots
- key page snapshots

至少：
- map shell
- list
- detail
- boundary
- contribution
- admin review

## 5.9 Frontend Performance

- lazy load
- map marker rendering
- virtual list if needed
- image compression
- avoid duplicate API
- cache strategy
- loading states

目标：
- H5 主要页面不卡顿
- map pan/zoom 可接受
- low-end Android 基本流畅

## 5.10 输出

生成：
- UI_UX_IMPLEMENTATION_REPORT.md
- DESIGN_SYSTEM.md
- FRONTEND_QA_REPORT.md

Gate：

```text
UI_FRONTEND_PRODUCTION_GATE = PASS
```

---

# P4 — ADMIN / DATA OPS PRODUCTIONIZATION

Admin 不是 demo。

必须真实可用：

- dashboard
- candidate queue
- evidence side-by-side
- review decision
- source/license
- place match
- rule diff
- rule exception
- publish gate
- rollback
- supersession
- observation queue
- source monitor
- freshness queue
- organization
- policy template
- amenity
- entrance
- path
- event
- audit log
- user/operator roles
- data quality metrics

关键页面必须支持：
- pagination
- filtering
- sorting
- error handling
- optimistic conflict
- permission
- audit

Gate：

```text
ADMIN_DATA_OPS_GATE = PASS
```

---

# P5 — REAL PROVIDER INTEGRATION

## Map

完成真实：
- TencentMapProvider
- key/env
- live smoke
- search
- nearby
- reverse geocode as needed
- map rendering
- navigation

必须遵守 provider 数据条款。
External ID 仍不当自有 PK。

## AI

真实接入：
- OCR
- Vision
- NL query if needed

如果当前用户已明确只使用某低成本 provider，则优先该 provider；
没有明确配置时保持可插拔。

真实测试：
- signage OCR
- rule extraction candidate
- no direct publish

## Notification

至少一个真实可用通知通道：
- in-app
- email / push / WeChat template depending target

Gate：

```text
REAL_PROVIDER_GATE = PASS
```

如缺 Key/账号：
- BLOCKED_EXTERNAL
- 其余全部完成
- 精确写用户需要做什么

---

# P6 — BACKEND PRODUCTION HARDENING

必须完成：

- env separation
- config validation
- migrations
- DB pool
- Redis
- Celery
- MinIO/S3
- task retry
- idempotency
- rate limiting
- pagination
- caching
- audit
- feature flags
- admin RBAC
- operator RBAC
- public API boundaries
- error model
- request id
- health/readiness

清理：
- debug endpoint
- test-only auth
- unsafe demo route
- mock-only prod path

Gate：

```text
BACKEND_PRODUCTION_GATE = PASS
```

---

# P7 — SECURITY / PRIVACY / COMPLIANCE

## Security

执行：
- dependency audit
- secret scan
- auth/RBAC
- IDOR
- SSRF
- upload abuse
- rate limit
- brute force
- CSRF where applicable
- CORS
- injection
- file validation
- admin privilege

P0/P1 vulnerability = 0。

## Privacy

必须：
- privacy inventory
- data minimization
- raw location policy
- media retention
- evidence retention
- delete flow
- account deletion/export where applicable
- consent UI
- privacy settings

## Legal / Content

准备草案：
- User Agreement
- Privacy Policy
- Data/Evidence Methodology
- Correction/Appeal Policy
- Operator Claim Terms
- Disclaimer

注意：
WorkBuddy 只能生成草案。
最终法律文本必须标注：
> `LEGAL_REVIEW_REQUIRED`

不要伪造法律审查已经完成。

## China map / platform compliance

对：
- 地图 SDK
- 小程序类目/资质
- UGC
- location
- evidence
- public map overlay
形成：

`COMPLIANCE_GATE.md`

标注：
- VERIFIED
- NEEDS_PROVIDER_CONFIRMATION
- LEGAL_REVIEW_REQUIRED
- PLATFORM_REVIEW_REQUIRED

Gate：

```text
SECURITY_PRIVACY_GATE = PASS_WITH_EXTERNAL_LEGAL_REVIEW
```

---

# P8 — PERFORMANCE / RELIABILITY / OBSERVABILITY

## Performance

至少测：
- p50/p95
- map bbox
- nearby
- place detail
- resolver
- candidate queue
- evidence upload
- admin list

设定合理 SLO。

## Reliability

测试：
- DB restart
- Redis unavailable
- MinIO unavailable
- worker restart
- duplicate task
- provider timeout
- source monitor repeat
- notification duplicate

## Observability

必须：
- structured logs
- request id
- task id
- error tracking
- health
- metrics
- provider latency
- queue depth
- failed task
- publish events
- source monitor events

## Backup / Restore

实际演练：
- DB backup
- restore
- object metadata
- audit consistency

输出：
- PERFORMANCE_FINAL.md
- RELIABILITY_FINAL.md
- BACKUP_RESTORE_FINAL.md
- OBSERVABILITY_FINAL.md

Gate：

```text
OPS_READINESS_GATE = PASS
```

---

# P9 — CROSS-PLATFORM BUILD & DEVICE QA

目标：
- H5
- 微信小程序
- Android
- HarmonyOS
- iOS

优先真实验证顺序：

1. H5
2. 微信小程序
3. Android
4. HarmonyOS
5. iOS

如果缺 HBuilderX / Apple signing / Huawei signing：
- 不伪造 PASS
- 其余继续
- BLOCKED_EXTERNAL

## Device QA

至少：
- Chrome desktop
- Edge
- Android Chrome
- 微信开发者工具
- 一台 Android 真机 if available
- Harmony/iOS as credentials/hardware allow

检查：
- location
- map
- upload
- camera
- permission
- navigation
- safe area
- keyboard
- back
- deep link
- network retry

输出：
`DEVICE_COMPATIBILITY_REPORT.md`

Gate：

```text
CROSS_PLATFORM_GATE = PASS_OR_EXTERNAL_BLOCKED
```

---

# P10 — STAGING

建立真正 Staging：

- production-like env
- isolated DB
- isolated Redis
- object storage
- HTTPS
- domain/subdomain
- migrations
- seed limited
- admin
- H5
- provider test keys
- logs
- backup

部署脚本必须可重复。

输出：
`STAGING_DEPLOYMENT_REPORT.md`

Gate：

```text
STAGING_GATE = PASS
```

---

# P11 — UAT / LAUNCH CANDIDATE

做一次完整用户验收。

## UAT 场景

### Consumer
- 首次进入
- 定位
- 搜索
- map
- place detail
- pet profile
- boundary profile
- contribution
- upload
- watch
- correction
- privacy

### Operator
- claim
- edit policy
- preview
- publish
- version

### Admin
- candidate
- evidence
- review
- publish
- rollback
- monitor

## Launch Candidate Data

至少：
- 30–50 reviewed Places
- 真实已发布 Rule
- 真实来源
- 有 unknown/stale/conflict 场景

不要只用 demo。

## Bug Gate

上线前：
- P0 = 0
- P1 = 0
- P2 有明确 waivers
- P3 可后续

输出：
`UAT_REPORT.md`
`LAUNCH_CANDIDATE_REPORT.md`

Gate：

```text
LAUNCH_CANDIDATE = PASS
```

---

# P12 — PRODUCTION RELEASE

上线目标：

> 上海中心城区试点 Beta

不得宣称全国覆盖。

## Production

要求：
- HTTPS
- env secrets
- DB backup
- Redis
- object storage
- migration
- health
- monitoring
- alerting
- log retention
- admin restricted
- rate limit
- privacy pages
- terms
- source methodology page

## Release

建议：
- release commit
- tag
- version
- changelog
- rollback point

例如：
```text
v0.6.0-beta.1
```

## 上线后验证

Smoke：
- public home
- search
- map
- place
- API
- evidence
- login
- contribution
- admin
- worker
- source monitor

输出：
`PRODUCTION_RELEASE_REPORT.md`

Gate：

```text
PRODUCTION_LAUNCH = PASS
```

若外部商店/小程序审核未完成：
- H5 可先上线 Beta
- 其他端保持 SUBMISSION_PENDING
- 不伪造已上架

---

# P13 — POST-LAUNCH

上线不是结束。

实现：

- error monitoring
- source monitor
- freshness
- review SLA
- dispute SLA
- backup schedule
- security patch process
- data incident runbook
- rollback runbook
- release checklist
- weekly data quality report

第一周监控：
- crash/error
- API p95
- failed tasks
- evidence upload
- duplicate place
- review queue
- rule publish
- attribution error
- user correction

输出：
`POST_LAUNCH_WEEK1_PLAN.md`

---

# 14. 产品上线完成定义

只有同时满足：

## Data
- 30–50 real Places
- reviewed
- evidence-first
- publish gate
- attribution target
- unresolved P0 schema gap = 0

## UX
- complete flows
- loading/empty/error
- neutral copy
- no score/ranking
- accessibility baseline

## Engineering
- tests
- lint/type
- migrations
- security
- backup
- monitoring
- rollback

## Providers
- real map or explicit external block
- real OCR or explicit external block

## Deployment
- staging PASS
- production PASS
- smoke PASS

## Legal/Product
- privacy/terms draft
- legal review status honest
- platform review status honest

才可以写：

```text
READY_FOR_PUBLIC_BETA = YES
```

---

# 15. 状态文件

持续维护：

- PRODUCTION_STATE.md
- PRODUCTION_ACCEPTANCE_MATRIX.md
- BLOCKERS.md
- DECISIONS.md
- TECH_DEBT_REGISTER.md

每个阶段：
- NOT_RUN
- IN_PROGRESS
- PASS
- PARTIAL
- FAIL
- BLOCKED_EXTERNAL

---

# 16. Commit Discipline

建议：

```text
data: finish reviewed pilot publish
data: add real batch 02
ui: implement production map shell
ui: finish place detail and boundary flows
admin: finish evidence review console
ops: add staging deployment
release: production beta candidate
```

不要一个超级大 commit。

---

# 17. 最终报告

最终必须生成：

`FINAL_PRODUCTION_READINESS_REPORT.md`

内容：

- current version
- git/tag
- data coverage
- published rules
- source/evidence quality
- UX complete
- admin complete
- providers
- security
- privacy
- performance
- reliability
- device QA
- staging
- production
- blockers
- legal review
- store/submission status
- rollback
- unresolved tech debt

最后只能三种结论：

```text
READY_FOR_PUBLIC_BETA = YES
```

或

```text
READY_FOR_PUBLIC_BETA = YES_WITH_EXTERNAL_SUBMISSION_PENDING
```

或

```text
READY_FOR_PUBLIC_BETA = NO
```

不得模糊。

---

# 18. 执行要求

现在直接执行。

不要只给我“计划”。

从当前 R2 仓库开始：

P0 Review/Publish
→ P1 30–50 Real Data
→ P2 UX Freeze
→ P3 UI/Frontend
→ P4 Admin
→ P5 Real Providers
→ P6–P9 Production Hardening
→ P10 Staging
→ P11 UAT
→ P12 Production
→ P13 Post-launch

遇到外部账号/证书：
- 写清准确 blocker
- 给出用户要做的最小动作
- 继续所有不受影响工作

不要问我是否继续。
