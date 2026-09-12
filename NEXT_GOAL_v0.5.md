# NEXT_GOAL_v0.5.md
# 宠物准入与公共空间共处规则平台
# RC-HARDENING-01 + V05-DOMAIN-01 + PILOT-READINESS-01

> 基于现有仓库增量续跑，不从零重建。
> 当前历史可信基线来自 `FINAL_RELEASE_REPORT.md`：报告基线 `95c357e`；Phase 0–13 已完成；30 pytest、5 Playwright、Alembic/PostGIS/Redis/Celery/Admin/H5 均有实际验证。
> 本轮目标：保住现有 RC，全量补齐本地可完成的硬化工作，并实现最新 v0.5 域模型，达到真实小范围数据试点前的本地 RC。

---

## 0. 非谈判执行原则

1. 先读现有仓库，先重跑 baseline，再改核心代码。
2. 已通过能力不得因重构回归。
3. migration 优先 additive，旧 API 不得无迁移方案直接破坏。
4. v0.5 新能力未稳定前使用 feature flag/兼容层。
5. Observation 永不自动成为 AccessRule。
6. UNKNOWN 永不自动变 allowed/prohibited。
7. Service dog 与 ordinary pet 独立。
8. Place 使用自有 UUID；地图 POI 只 ExternalPlaceRef。
9. 平台保持中性：不做红黑榜、卫生评分、文明评分、评论区、遇宠率。
10. “共处边界”记录空间规则，不评价任何一类人。
11. 真实未核验商家不能作为负面 demo。
12. PASS 必须有真实命令/输出证据。
13. 外部 Key/证书只阻塞 live smoke，不能成为 adapter 代码/fixture/tests 没做的借口。

---

## 1. Baseline Freeze

### 1.1 必读
- `FINAL_RELEASE_REPORT.md`
- 原 `GOAL.md`
- `AGENTS.md`
- `DECISIONS.md`
- `PROJECT_STATE.md`
- `ACCEPTANCE_MATRIX.md`
- `BLOCKERS.md`
- `docs/PLATFORMS.md`
- 当前 migrations
- current evaluator/API/client/Admin/worker
- 本包所有 v0.5 文件

### 1.2 Git
执行：
```bash
git status
git log --oneline -10
git rev-parse HEAD
```
如果实际 HEAD 不是 `95c357e`，不得强行 reset；记录实际基线。

### 1.3 重跑基线
至少：
```bash
uv run pytest -q
pnpm exec playwright test
bash scripts/lint.sh
uv run mypy services/api/app
```
并按现有工程方式验证：
- Alembic up/down/up
- PostGIS
- Redis
- Celery
- Admin build
- H5 build

创建 `BASELINE_FREEZE_V05.md`。
基线红时先修基线，不在红色基线上做域模型升级。

---

# 2. Track A — RC-HARDENING-01

## A1. MinIO / S3 真实本地链路

现有报告只完成 S3 抽象，未串通“真实图片→对象存储→审核”。

必须完成：
```text
Client/Admin Upload
→ API validation
→ MinIO
→ media_object metadata
→ OCR/Mock task
→ review queue
→ TTL/delete
→ audit
```

建议 `media_object`：
- id UUID
- owner_type/owner_id
- purpose
- bucket/object_key
- mime_type/byte_size/sha256
- upload_status
- moderation_status
- privacy_class
- created_at/expires_at/deleted_at

上传安全：
- MIME allowlist
- extension/MIME 一致性
- size limit
- image decode verification
- randomized object key
- hash
- duplicate basic check
- no path traversal
- audit

Integration/E2E 必须真实打本地 MinIO：
上传规则牌 → 对象存在 → DB metadata → OCR task → review → delete/TTL → 对象删除 → audit。

## A2. TencentMapProvider 真 Adapter 代码

保留：
```text
MapProvider
├─ MockMapProvider
└─ TencentMapProvider
```

按当前产品真正使用的能力实现：
- text/place search
- nearby search（如业务需要）
- reverse geocode（如业务需要）
- map config
- navigation config/deep link
- provider error normalization

要求：
- 最新官方文档核对 request/response；
- timeout/retry；
- fixture/mock HTTP contract tests；
- success/empty/malformed/auth/quota/timeout/network tests；
- Key 不入库；
- 第三方 ID 不当自有主键；
- 未确认许可的数据不得批量持久化。

没有 Key 只允许 live smoke `BLOCKED_EXTERNAL`。

## A3. AI Provider 收口

稳定：
- VisionProvider
- OCRProvider
- NaturalLanguageQueryProvider

每个 provider：
- timeout
- retry
- normalized error
- telemetry
- secret redaction
- fixture contract tests

若已有明确 provider 和官方文档，实现至少一个 real adapter；无 Key 仍可用 mocked HTTP/fixtures 验证 contract。
若尚未选型，不得假装文本 provider 支持 vision/OCR；写 `AI_PROVIDER_SELECTION.md`。

AI 永远不得：
- 自动认服务犬
- 自动发布正式 Rule
- 视觉估重直接写 confirmed
- 最终法律判断

## A4. Backup/Restore 真演练

实际执行：
seed DB → backup → mutate/delete → restore 到干净库 → integrity check。

对象存储至少验证 test bucket/metadata 的恢复/导出策略。

生成 `docs/BACKUP_RESTORE_RUNBOOK.md`。

## A5. Reliability/Observability

补齐：
- request_id
- structured logs
- Celery task id
- retry policy
- failed job visibility
- health/readiness
- DB/Redis/MinIO/provider health
- metrics abstraction
- error capture abstraction

不要为此引入不必要的重型微服务。

---

# 3. Track B — V05-DOMAIN-01

## B1. RuleLayer

新增：
- LEGAL
- REGULATORY_GUIDANCE
- OPERATOR_POLICY
- TEMPORARY_POLICY

`OBSERVED_PRACTICE` 不进入 normative AccessRule；继续属于 Observation/Verification。

AccessRule 增加：
- rule_layer
- origin/authority metadata
- effective/review metadata

## B2. EffectiveRuleResolver

解析链：
```text
Legal constraints
→ Regulatory guidance
→ Organization PolicyTemplate
→ Place override
→ Zone override
→ Temporary/Event override
→ EffectiveRuleSet
```

不是简单 numeric priority，也不是 last-write-wins。

至少考虑：
- jurisdiction
- mandatory/advisory/operator discretion
- animal scope
- action
- place/zone scope
- effective time
- supersedes
- exception
- template inheritance
- temporary event
- service dog isolation

输出：
- applicable_rules[]
- suppressed_rules[]
- unresolved_conflicts[]
- explanation_steps[]
- compliance_state

`compliance_state`：
- CONSISTENT
- POTENTIAL_CONFLICT
- REVIEW_REQUIRED
- UNKNOWN

禁止自动公开写“违法商家”。

## B3. RuleCandidate

新增一等实体：
- id
- source_id
- place/zone candidate refs
- animal_scope
- action
- effect
- proposed_conditions
- extraction_method/provider
- internal_confidence nullable
- review_status
- reviewer
- notes
- published_rule_id
- timestamps

状态：
- DISCOVERED
- EXTRACTED
- MATCH_PENDING
- REVIEW_PENDING
- APPROVED
- REJECTED
- PUBLISHED
- SUPERSEDED

硬规则：
OCR / AI / URL monitor / 用户上传 / 外部线索 / 电话草稿都必须先进 Candidate。
未 APPROVED/PUBLISHED 的 Candidate 不得参与最终 evaluator。

## B4. DataSourceJob

类型：
- OFFICIAL_IMPORT
- OPERATOR_IMPORT
- PHONE_VERIFY
- ONSITE_VERIFY
- USER_SUBMISSION
- URL_MONITOR
- AI_EXTRACTION
- MAPPING_MISSION

记录：
- target scope
- state
- actor/provider
- started/completed
- result counts
- errors
- audit ref

## B5. SourceMonitor

新增：
- source_id
- monitor_type
- schedule
- last_checked_at
- last_changed_at
- content_hash
- etag/last_modified optional
- status
- failure_count
- next_check_at

工作流：
```text
check
→ unchanged
或
→ changed
→ diff artifact
→ RuleCandidate
→ review
→ new RuleVersion
→ Watch notification
```

MVP 只支持安全/授权明确来源，不做社交平台大规模爬虫。

必须做 SSRF 防护、协议/大小/超时限制。

## B6. FreshnessPolicy

统一：
- last_verified_at
- review_due_at
- freshness_policy_id

`review_due` ≠ invalid。
过期只显示“需要复核”，不自动反转规则。
Observation 保留历史，不按 Rule freshness 失效。

## B7. CoexistencePolicy

把“共食/共处边界”做成一等语义，但保持中性。

餐饮首批：
- ordinary pet in indoor dining
- outdoor dining
- animal on customer seat
- animal on table surface
- animal near food service area
- animal in self-service food area
- animal use customer tableware
- dedicated pet tableware available
- dedicated pet zone available
- zone separation type

必须写 ADR 决定它最终是：
- AccessRule action extension
还是
- AccessRule + CoexistenceAttribute
禁止复制第二套互相冲突的规则引擎。

三者永久分离：
1. Operator/Rule：店方规定
2. Observation：用户看到
3. BoundaryProfile：用户自己的接受边界

## B8. BoundaryProfile

新增：
- boundary_profile
- boundary_preference

首版只 animal domain。

示例：
- 普通宠物室内堂食：不接受
- 户外：可接受
- 上顾客座椅：不接受
- 进入食品自助区：不接受
- 独立携宠区：偏好
- 顾客餐具用于宠物：要求明确禁止

禁止综合评分。

## B9. BoundaryMatcher

输入：
`EffectiveRuleSet + PlaceAttributes + BoundaryProfile`

输出：
- matched_preferences[]
- conflicting_preferences[]
- unknown_preferences[]
- sources[]
- freshness flags

只返回：
- MATCH
- CONFLICT
- UNKNOWN

Unknown 不得当 Match。

## B10. Amenity

独立于 Rule：
- PET_WATER
- WASTE_BAG
- PET_TOILET
- PET_WASH
- STROLLER_RENTAL
- TIE_UP
- PET_HOLDING
- PET_ELEVATOR
- PET_ENTRANCE
- PET_ACTIVITY_AREA

字段：
- place/zone
- amenity_type
- status
- source
- verified_at
- review_due_at

## B11. Entrance

新增：
- id
- place_id
- zone_id optional
- name
- geometry
- entrance_type
- access_notes
- source_id

类型：
- GENERAL
- PET_DESIGNATED
- SERVICE
- PARKING_CONNECTION
- OTHER

## B12. AccessPath

新增：
- id
- place_id
- name
- from_node/to_node
- geometry optional
- animal_scope
- conditions
- time_window
- source_id
- status

首版无需复杂路径算法，但要能表达：
P2 → 南门宠物入口 → 2号宠物电梯 → 3F宠物区。

## B13. Organization + PolicyTemplate

实现：
- organization
- policy_template
- policy_template_rule
- place_policy_binding
- place override
- zone override

Resolver 必须支持：
集团模板 → 门店继承 → Place override → Zone override。

不允许“最后写入赢”。

## B14. Event / Temporary Policy

支持：
- effective_from/to
- time window
- event zone scope
- recurrence（如当前工程成本合理）

至少表达：
- 宠物市集某日临时开放
- 公园夜间时段开放
- 节假日临时限制

结束后自动不适用但保留历史。

## B15. DataLicense

Provenance 与许可分开：

- source_id
- display_allowed
- storage_allowed
- redistribution_allowed
- commercial_use_allowed
- attribution_required
- license_name/url
- expires_at
- notes

未明确许可 ≠ 自动可再分发。

## B16. PetAccessJSON v0.1

内部统一 JSON Schema，先用于 import/export/test fixtures，不急着公开 API。

至少包含：
- subject/animal
- place/zone scope
- action
- effect
- rule_layer
- conditions
- validity
- source/provenance
- version

schema version：
`petaccessjson_version = "0.1"`。

## B17. Answerability Matrix

内部计算，不给商家打分。

回答字段：
- ordinary dog entry
- indoor/outdoor
- leash
- stroller/carrier
- size
- service dog
- seat
- food area
- tableware
- source
- freshness

输出：
- answerable
- unknown
- stale

---

# 4. Admin v0.5

必须真实连接 API：

1. Rule Candidates
2. Source Monitors
3. Data Source Jobs
4. Rule Conflict Review
5. Freshness Queue
6. Coexistence Policy Editor
7. Boundary Debugger
8. Amenities
9. Entrances
10. Access Paths
11. Organizations
12. Policy Templates
13. Override Preview
14. Event Rules
15. Data License
16. Answerability Dashboard
17. Media/OCR Queue

不做静态假页。

---

# 5. Client/H5 v0.5

场所详情最上层只回答五件事：
1. 能不能进入
2. 哪里能进入
3. 条件
4. 共处边界
5. 来源/更新时间

法规/Observation/版本历史二级展开。

新增：
- Boundary Settings
- Explainable Match
- Amenity
- Entrance/AccessPath

Explainable Match：
- ✓ MATCH
- ✕ CONFLICT
- ? UNKNOWN
不做 89 分、95% 等总分。

---

# 6. Track C — PILOT-READINESS-01

## C1. 三条端到端数据生产链

### E2E-A 现场规则牌
upload → MinIO → OCR mock/fixture → RuleCandidate → Admin approve → AccessRule → client visible

### E2E-B 管理方
verified operator → questionnaire/template → operator policy → resolver → client visible

### E2E-C 来源监控
source hash change → candidate → review → supersede old rule → watch notification

## C2. Reality Audit 工具

实现：
- CSV/JSON import template
- audit CLI/API
- schema gap report

输出每个 Place：
- expressible yes/no
- unsupported conditions
- unknown fields
- source quality
- freshness
- resolver result
- boundary result
- schema gaps

真实 30–50 Place 若没有合法素材，不得伪造；先用 adversarial fixtures 完成工具。

## C3. Adversarial fixtures

至少覆盖 30 类：
- 小型/大型犬差异
- 10kg
- 40cm
- 封闭包
- 推车/不落地
- 室内禁/户外允许
- 商场公共区/餐饮区
- 超市禁/3F允许
- 指定入口/电梯
- 周末/夜间/节假日
- 临时活动
- 服务犬例外
- 法律与管理方冲突
- 集团模板/门店/Zone override
- stale
- Observation 不改变 Rule
- 座椅/桌面/食品区/餐具
- unknown/conflict/superseded/expired event
- max pet count

---

# 7. 测试升级

原基线测试必须全绿。

新增：

## Unit
- resolver
- inheritance
- event/time
- candidate state machine
- freshness
- boundary matcher
- answerability
- PetAccessJSON

## Property-based
建议 Hypothesis。
不变量：
- UNKNOWN 不自动 MATCH
- Observation 不影响 normative resolver
- expired event 不 current
- superseded 不 current
- unpublished candidate 不 effective
- service dog 隔离
- Place UUID 不等于 external provider ID

## Integration
- real local MinIO
- DB migrations
- Redis/Celery
- SourceMonitor
- media/OCR
- template inheritance
- watch after rule version

## E2E
- BoundaryProfile
- explainable match
- upload sign
- candidate review
- operator template
- source change
- access path

不要追求测试数量，按场景 Gate 验收。

---

# 8. Migration

必须生成 `MIGRATION_V05.md` 并实际验证。

原则：
- additive first
- old data readable
- old API stable
- idempotent backfill
- upgrade/down/upgrade

新增实体预计：
- media_object（若无）
- rule_candidate
- data_source_job
- source_monitor
- freshness_policy
- boundary_profile
- boundary_preference
- amenity
- entrance
- access_path
- organization
- policy_template
- policy_template_rule
- place_policy_binding/override
- event/temporary policy
- data_license

旧 AccessRule：
- 可确定 source 的尽量 backfill rule_layer
- 无法确定 → REVIEW_REQUIRED/UNKNOWN
- 不猜

---

# 9. Security / Privacy

Media：
- protected object
- evidence 不默认公开
- signed/protected access
- TTL/audit

BoundaryProfile：
- 仅空间偏好；
- 永不扩展到按人的固有身份做排斥筛选。

SourceMonitor：
- SSRF protection
- only http/https
- private network protection where applicable
- size/time limit
- content type checks

AI：
- secrets 不进日志
- no unnecessary PII
- media retention policy

---

# 10. Cross-platform

域升级和硬化完成后，再做 HBuilderX 五端验证。

如果当前机器有 HBuilderX：
- 实际编译目标端并修错误。

没有：
- B-01 保持外部 blocker
- 不伪造 PASS
- 其余代码继续

---

# 11. 本轮明确不做

- 宠物社交
- 附近宠友
- 遛宠轨迹
- 商城
- 医疗健康
- 新闻
- Dog Density
- 卫生评分
- 文明评分
- 红黑榜
- 用户骂店评论
- AI 自动违法判断
- 鼻纹识别
- 完整 OTA
- 吸烟/噪音等其他 Domain 前台

可预留 domain 字段，但 v0.5 只实现 animal。

---

# 12. 最终交付

必须生成：
- `BASELINE_FREEZE_V05.md`
- `MIGRATION_V05.md`
- `V05_FINAL_REPORT.md`
- 更新 `PROJECT_STATE_V05.md`
- 更新 `ACCEPTANCE_MATRIX_v0.5.md`
- 更新 `BLOCKERS.md`
- ADR
- OpenAPI
- generated TS client
- schema docs
- test evidence

---

# 13. v0.5 本地 RC 完成标准

同时满足：
1. 旧 RC 全绿；
2. MinIO 上传/OCR/审核真实本地链路 PASS；
3. Tencent adapter 代码 + contract tests PASS；
4. AI adapters contract tests PASS；
5. RuleLayer + Resolver PASS；
6. RuleCandidate + DataSourceJob + SourceMonitor PASS；
7. CoexistencePolicy + BoundaryProfile + Matcher PASS；
8. Amenity + Entrance + AccessPath PASS；
9. Organization/PolicyTemplate/Override PASS；
10. Temporary/Event PASS；
11. DataLicense + PetAccessJSON + Answerability PASS；
12. Admin 真操作 PASS；
13. H5 v0.5 E2E PASS；
14. migrations up/down/up PASS；
15. 新 RuleVersion 能触发 Watch；
16. 高影响操作有审计；
17. 文档真实；
18. 仅 live Key/证书项允许 BLOCKED_EXTERNAL。

---

# 14. 最终执行要求

> 不要停在计划。立即从 Baseline Freeze 开始，然后依次完成 RC-HARDENING-01 → V05-DOMAIN-01 → PILOT-READINESS-01。遇到外部凭证只阻塞对应 live smoke，不阻塞本地代码和测试。持续修复，直到所有本地可完成 Gate PASS，并生成 `V05_FINAL_REPORT.md`。
