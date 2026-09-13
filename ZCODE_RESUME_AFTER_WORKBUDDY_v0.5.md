# ZCODE_RESUME_AFTER_WORKBUDDY_v0.5.md

你现在是在 WorkBuddy + DeepSeek-v4-flash 之后，继续接管同一个“宠物准入与公共空间共处规则平台”现有仓库。

这不是从零开始，也不是回到旧基线重做。你的唯一正确做法是：

> **读取当前真实仓库状态 → 保护 WorkBuddy 已有修改 → 重跑当前测试 → 找到第一个未完成/半完成 Gate → 从那里继续 → 直到所有本地可完成项 PASS。**

---

## 1. 接管前先做 Git 审计

立即执行：

```bash
git status
git diff --stat
git diff
git diff --cached
git log --oneline -20
git rev-parse HEAD
```

如果存在 modified / staged / untracked 文件：

- 不允许 `git reset --hard`
- 不允许 `git clean -fd`
- 不允许 `git checkout -- .`
- 不允许为了“恢复旧版本”覆盖 WorkBuddy 的工作

把这些改动视为 WorkBuddy 已做但可能尚未收口的内容。

先保存快照：

```bash
git diff > zcode_resume_pre_takeover.patch
git diff --cached > zcode_resume_pre_takeover_staged.patch
```

---

## 2. 必读文件

依次完整读取：

1. `FINAL_RELEASE_REPORT.md`
2. 原 `GOAL.md`
3. `AGENTS.md`
4. `DECISIONS.md`
5. `PROJECT_STATE.md`
6. `ACCEPTANCE_MATRIX.md`
7. `BLOCKERS.md`
8. `NEXT_GOAL_v0.5.md`
9. `ZCODE_CONTINUE_PROMPT_v0.5.md`
10. `WORKBUDDY_DEEPSEEK_V4_FLASH_CONTINUE.md`（如果存在）
11. `WORKBUDDY_TAKEOVER_REPORT.md`（如果存在）
12. `PROJECT_STATE_V05.md`
13. `ACCEPTANCE_MATRIX_v0.5.md`
14. `docs/V05_ARCHITECTURE_DELTA.md`
15. `docs/DATA_PIPELINE_SPEC.md`
16. `docs/RULE_RESOLVER_SPEC.md`
17. `docs/COEXISTENCE_BOUNDARY_SPEC.md`
18. `docs/PROVIDER_HARDENING_SPEC.md`
19. `docs/REALITY_AUDIT_PLAN.md`
20. `docs/MIGRATION_SPEC_v0.5.md`
21. `docs/TEST_PLAN_v0.5.md`
22. `docs/PLATFORMS.md`
23. WorkBuddy 新增的任何状态报告、ADR、迁移说明、测试报告。

若某个文件不存在：
- 记录缺失
- 不猜
- 继续读取其他真实存在的文件

---

## 3. 创建接管报告

新建：

`ZCODE_RESUME_TAKEOVER_REPORT.md`

至少记录：

```text
Actual HEAD:
Working tree status:

Recent commits:
- ...

WorkBuddy modified/untracked files:
- ...

Likely completed Gates:
- ...

Likely partial Gates:
- ...

Not started Gates:
- ...

Current failing tests:
- ...

External blockers:
- ...

First unfinished executable Gate:
- ...

Resume strategy:
- ...
```

必须基于真实代码、Git、测试和 migration 判断。

---

## 4. 先跑当前 baseline

在继续开发前，重新执行当前项目实际适用的验证：

```bash
uv run pytest -q
pnpm exec playwright test
bash scripts/lint.sh
uv run mypy services/api/app
```

并根据仓库已有脚本验证：

- Admin build
- H5 build
- Alembic current
- Alembic upgrade
- 如当前环境安全，测试 downgrade/up
- PostGIS smoke
- Redis health
- Celery smoke
- MinIO health

如果失败：

1. 判断是否是 WorkBuddy 尚未收口的半成品；
2. 不回滚全部 WorkBuddy 修改；
3. 修复当前失败；
4. baseline 回绿后继续。

---

## 5. 按 `ACCEPTANCE_MATRIX_v0.5.md` 继续

状态解释：

- `PASS`：不重做，除非回归失败
- `PARTIAL`：优先收口
- `FAIL`：修复
- `NOT_RUN`：按顺序执行
- `BLOCKED_EXTERNAL`：只阻塞 live smoke，不阻塞本地代码、fixture、contract test

如果 WorkBuddy 没更新 matrix，则用真实代码与测试重新判断并更新。

---

# 6. 永久不可破坏的产品规则

1. Place 使用平台自有 UUID。
2. 外部地图 POI ID 只能是 ExternalPlaceRef。
3. ObservationClaim 永远不能自动变 AccessRule。
4. ObservationCandidate 永远不能自动变 ObservationClaim。
5. RuleCandidate 未审核不得进入正式规则层。
6. UNKNOWN 不得自动变 allowed/prohibited。
7. service_dog 与 ordinary_pet 分离。
8. AI 只负责抽取、识别、标准化和候选，不做最终准入/法律裁决。
9. 不做遇宠率。
10. 不做红黑榜。
11. 不做卫生评分。
12. 不做文明评分。
13. 不做用户骂店评论区。
14. 小区只做公共空间规则，不做住户养宠数据库。
15. 不默认连续保存用户轨迹。
16. 高影响 Rule 必须有 Source / Evidence。
17. Demo 默认使用虚构地点。
18. 平台中性：描述空间规则和可观察事实，不评价任何一类人。

---

# 7. 如果 RC-HARDENING-01 尚未收口

继续完成：

## 7.1 MinIO 真链路

```text
upload
→ validation
→ MinIO
→ media_object
→ OCR task
→ review queue
→ TTL/delete
→ audit
```

至少有：
- MIME allowlist
- size limit
- image decode validation
- random object key
- sha256
- duplicate basic check
- no path traversal
- protected access
- integration test

## 7.2 TencentMapProvider

必须完成真 adapter 代码：

- text/place search
- nearby（如当前业务需要）
- reverse geocode（如需要）
- map config
- navigation config
- timeout/retry
- provider error mapping
- fixture contract tests

没有 Key 只允许 live smoke `BLOCKED_EXTERNAL`。

## 7.3 AI Providers

至少稳定：

- VisionProvider
- OCRProvider
- NLQueryProvider

要求：
- timeout
- retry
- normalized errors
- secret redaction
- fixture contract tests

## 7.4 Backup/Restore

真演练：

```text
seed
→ backup
→ mutate/delete
→ restore
→ integrity check
```

## 7.5 Observability

至少：
- request_id
- task_id
- structured logs
- retry
- failed job visibility
- health/readiness
- DB/Redis/MinIO/provider health

---

# 8. RuleLayer / EffectiveRuleResolver

正式支持：

```text
LEGAL
REGULATORY_GUIDANCE
OPERATOR_POLICY
TEMPORARY_POLICY
```

Observation 不进入 normative resolver。

解析链：

```text
Legal
→ Guidance
→ Organization PolicyTemplate
→ Place Override
→ Zone Override
→ Event/Temporary Override
→ EffectiveRuleSet
```

必须考虑：
- jurisdiction
- mandatory/advisory/operator discretion
- animal scope
- action
- place/zone
- effective time
- supersedes
- exception
- inheritance
- event
- service dog isolation

输出：
- applicable_rules
- suppressed_rules
- unresolved_conflicts
- explanation_steps
- compliance_state

`compliance_state`：
- CONSISTENT
- POTENTIAL_CONFLICT
- REVIEW_REQUIRED
- UNKNOWN

禁止自动公开写“违法商家”。

---

# 9. Evidence-First Multi-Source Acquisition

平台后续不能只等用户上传。

必须支持主动发现：

- 政府/官方渠道
- 品牌官网
- 商场/酒店/景区官网
- 公众号/官方账号
- 搜索发现
- 公开网页
- 外部内容平台
- 用户提交链接
- 现场核验
- 电话/人工核验

但是：

> **没有证据链，就不能成为正式事实。**

---

## 9.1 EvidenceBundle

新增或保留等价模型：

```text
EvidenceBundle
- id
- source_platform
- source_url
- source_content_id
- source_type
- publisher_type
- published_at
- captured_at
- quoted_fragment
- extracted_fragment
- screenshot_ref
- snapshot_ref
- content_hash
- place_match_evidence
- temporal_evidence
- extraction_method
- extraction_model_version
- reviewer
- review_log
- license/privacy metadata
```

原则：

> AI 输出属于 Derived Evidence，不是 Original Evidence。

---

## 9.2 Collector abstraction

统一：

```text
SourceCollector
→ SourceArtifact
→ EvidenceBundle
→ Claim Extraction
→ Candidate
```

至少预留：

```text
OfficialWebCollector
OperatorSiteCollector
SearchDiscoveryCollector
SocialLeadCollector
UserLinkCollector
ManualVerificationCollector
OnsiteEvidenceCollector
```

小红书、抖音、微博、点评等第一阶段只作为：

> lead discovery

不能抓到内容就直接成为正式 Rule。

没有明确 API/许可时：
- 不无条件批量保存全文/视频
- 不无条件再分发
- 只保存最小必要证据、链接、hash、必要引用片段和审核记录

---

# 10. RuleCandidate / ObservationCandidate 必须分开

如果内容表达：

> 店方规定 / 官方公告 / 工作人员明确政策

进入：

```text
RuleCandidate
```

如果内容表达：

> 某人看到宠物位于座椅、桌面、自助区

进入：

```text
ObservationCandidate
```

ObservationCandidate 建议状态：

```text
DISCOVERED
EXTRACTED
PLACE_MATCH_PENDING
REVIEW_PENDING
APPROVED
REJECTED
PUBLISHED
```

只有 Published 才生成 ObservationClaim。

---

# 11. Original / Derived Evidence 分离

Original：

- URL
- screenshot
- official notice
- onsite signage
- uploaded image
- video keyframe

Derived：

- OCR text
- AI extraction
- place matching
- normalized rule
- summary

后台必须能追溯：

> 每条正式结构化事实到底来自哪个原始证据。

---

# 12. DataLicense / SourcePolicy

与 Provenance 分离记录：

```text
storage_allowed
display_allowed
redistribution_allowed
commercial_use_allowed
attribution_required
raw_media_retention_allowed
expires_at
```

原则：

> 公开可见 ≠ 自动允许批量抓取、长期保存和商业再分发。

---

# 13. DataSourceJob / SourceMonitor / Freshness

实现或继续收口：

```text
DataSourceJob
SourceMonitor
FreshnessPolicy
```

SourceMonitor：

```text
source_url
content_hash
etag
last_modified
last_checked
last_changed
status
failure_count
next_check
```

变化流程：

```text
source changed
→ diff
→ EvidenceBundle
→ RuleCandidate
→ review
→ new RuleVersion
→ Watch notification
```

`review_due` 不等于规则失效。

---

# 14. CoexistencePolicy

保持中性记录：

- 普通宠物是否进入室内堂食
- 是否进入户外堂食
- 是否允许上顾客座椅
- 是否允许上桌面
- 是否靠近食品操作/取用区
- 是否进入自助食品区
- 是否使用顾客餐具
- 是否有宠物专用餐具
- 是否有独立宠物区域
- 是否有物理分隔

永久分离：

```text
Rule
Observation
BoundaryPreference
```

平台不写：
- 恶心
- 不文明
- 卫生差

---

# 15. BoundaryProfile / BoundaryMatcher

用户设置自己的空间边界。

只返回：

```text
MATCH
CONFLICT
UNKNOWN
```

逐项解释。

禁止：
- 综合分
- 89 分
- 95% 匹配
- 商户好坏排行

---

# 16. 空间模型

最终支持：

```text
Place
├─ Zone
├─ Entrance
├─ AccessPath
└─ Amenity
```

Amenity 首批：

- pet water
- waste bag
- pet toilet
- pet wash
- stroller
- tie-up
- holding
- pet elevator
- pet entrance
- pet activity area

AccessPath 至少能表达：

```text
P2
→ 南门宠物入口
→ 2号宠物电梯
→ 3F宠物区
```

第一版不必做复杂最短路。

---

# 17. Organization / PolicyTemplate / Override

支持：

```text
Organization
→ PolicyTemplate
→ Place Binding
→ Place Override
→ Zone Override
```

用于连锁品牌、酒店集团、商场集团。

Resolver 必须有 inheritance/override tests。

---

# 18. Event / TemporaryPolicy

至少支持：

- 周末开放
- 夜间开放
- 节假日限制
- 临时宠物活动日

过期后不 current，但历史保留。

---

# 19. PetAccessJSON / Answerability

PetAccessJSON v0.1：

- subject
- scope
- action
- effect
- rule_layer
- conditions
- validity
- provenance
- version

Answerability 内部矩阵：

- entry
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

它是数据质量工具，不是商家评分。

---

# 20. Admin

如果 WorkBuddy 尚未做完，继续：

- Rule Candidates
- Observation Candidates
- Evidence Review
- Source Monitors
- DataSource Jobs
- Rule Conflict Review
- Freshness Queue
- Coexistence Editor
- Boundary Debugger
- Amenities
- Entrances
- Access Paths
- Organizations
- Policy Templates
- Overrides
- Event Rules
- Data License
- Answerability Dashboard
- Media/OCR Queue

必须真实连 API。

---

# 21. H5 / Client

场所详情第一层只回答：

1. 能不能进入
2. 哪里能进入
3. 条件是什么
4. 共处边界
5. 来源和更新时间

法规 / Observation / 历史版本二级展开。

新增：

- Boundary Settings
- Explainable Match
- Amenity
- Entrance/AccessPath
- Evidence/Source summary

---

# 22. PILOT-READINESS

最终必须至少跑通 4 条：

## E2E-A

```text
upload signage
→ MinIO
→ OCR
→ EvidenceBundle
→ RuleCandidate
→ Admin approve
→ Rule
→ client
```

## E2E-B

```text
verified operator
→ questionnaire/template
→ policy
→ resolver
→ client
```

## E2E-C

```text
source changed
→ evidence/diff
→ candidate
→ review
→ supersede
→ watch
```

## E2E-D

```text
external public lead fixture
→ SourceArtifact
→ EvidenceBundle
→ classify RuleCandidate/ObservationCandidate
→ review
→ no direct publish
```

---

# 23. Reality Audit

实现或收口：

- CSV/JSON import template
- audit CLI/API
- schema gap report

后续真实样本建议：

- 20 餐饮/咖啡
- 5 商场
- 5 公园
- 5 酒店/景区/其他
- 属地法规

没有合法真实素材时不得伪造。

---

# 24. 测试

旧 baseline 必须持续 PASS。

新增至少覆盖：

- resolver
- RuleCandidate state machine
- ObservationCandidate
- evidence chain
- source monitor
- inheritance
- event
- freshness
- boundary
- answerability
- PetAccessJSON
- real local MinIO
- E2E-A/B/C/D

Property-based 不变量：

- UNKNOWN 不强转 MATCH
- Observation 不改变 normative resolver
- expired event 不 current
- superseded 不 current
- unpublished candidate 不 effective
- service dog scope 隔离
- external provider ID 永不成为 Place PK

---

# 25. Migration

必须：

- additive first
- old data readable
- old API 尽量稳定
- backfill idempotent
- upgrade/down/upgrade

无法确定的旧数据：

```text
REVIEW_REQUIRED
UNKNOWN
```

不要猜。

---

# 26. 状态纪律

每完成一个 Gate 更新：

- `PROJECT_STATE_V05.md`
- `ACCEPTANCE_MATRIX_v0.5.md`
- `BLOCKERS.md`
- `DECISIONS.md`

建议小步本地 commit：

```text
zcode: finish evidence pipeline
zcode: finish effective rule resolver
zcode: finish source monitor
...
```

不要一个巨大 commit。

---

# 27. 真正允许的外部 Blocker

只有：

- 腾讯地图 Key
- AI Key
- HBuilderX/特定 SDK
- 微信/Apple/Huawei/Android 开发者账号与签名
- 生产域名/备案
- 法律专业确认
- 真实管理方身份
- 必须真人设备操作

这些之外，不要轻易说“需要用户”。

---

# 28. 最终报告

所有本地可完成项结束后生成：

`V05_FINAL_REPORT.md`

必须包含：

- takeover HEAD
- WorkBuddy 已完成什么
- ZCode 新完成什么
- 未提交改动如何处理
- migrations
- RuleResolver
- Evidence-first acquisition
- RuleCandidate / ObservationCandidate
- MinIO/media pipeline
- SourceMonitor
- Coexistence/Boundary
- Admin/H5
- tests
- live provider status
- blockers
- pilot readiness
- remaining work

---

# 29. 现在开始

不要回复我大段计划。

立即执行：

1. `git status / diff / log`
2. 创建 `ZCODE_RESUME_TAKEOVER_REPORT.md`
3. 读取最新状态文件
4. 跑当前 baseline
5. 找到第一个 `PARTIAL / FAIL / NOT_RUN` Gate
6. 从那里继续实际写代码
7. 持续推进直到所有本地可完成项 PASS

**不要问我是否继续。**
