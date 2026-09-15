# AGENT_MASTER_CONTINUE_ALL_UNFINISHED_GOAL.md
# 宠物准入与公共空间共处规则平台
# 新 Agent 总接管：补完前置任务 + Consumer UX v1 + P0 发布闭环
# 日期：2026-09-15
# 适用：ZCode / OpenCode / Codex / Claude Code / 其他代码 Agent

> 你接管的是一个已经由 ZCode / WorkBuddy 多轮开发的真实仓库。
> WorkBuddy 在额度耗尽前同时存在多个“尚未完全结束”的任务。
>
> 本 Goal 的第一原则：
>
> **不要从最后一个 Goal 误判整个项目当前阶段。**
>
> 你必须先恢复“所有未完成任务图”，确认每个前序 Goal 的真实完成度，
> 然后按依赖关系继续，而不是只做 Consumer UX。
>
> 当前已知至少有三条工作线：
>
> A. Animal Scope / Guide Dog / Service Dog 精确语义修复
> B. P0 Human Review / Publish Closure
> C. Consumer UX Baseline v1
>
> 依赖关系：
>
> A 自动完成
>   ↓
> 重新生成 Human Review Packet
>   ↓
> B 等待具名人类签署
>   ├─ 未签：不得 Publish / 不得扩 30–50，但可继续 C
>   └─ 已签：完成 Publish Closure → P0 Gate
>                    ↓
>             才允许 30–50 Place
>
> C Consumer UX 可以在 A 完成后继续；
> 不要求等 GOV-01 人工签署才做 UI，
> 但正式 Published Rule 的生产验证必须等 B 完成。

==================================================
0. 总原则
==================================================

1. 不重建项目。
2. 不 reset --hard。
3. 不 clean -fd。
4. 不覆盖 WorkBuddy 未提交成果。
5. 不以旧报告中的 HEAD / 测试数字冒充当前事实。
6. 不因为某个报告写“PASS”就跳过代码与测试核验。
7. 不替人类 Reviewer 签名。
8. 不自动批准 RuleCandidate。
9. 不把 Candidate 当正式 Rule。
10. 不把 UNKNOWN 当 ALLOWED。
11. 不把 ontology 父类关系当法律效力扩张。
12. 不在 P0 Publish Gate 通过前进入 30–50 Place 扩量。
13. Consumer UX 可与 GOV-01 人工阻塞并行，但不得伪造发布态。
14. 外部 Key / 证书 / 审批只阻塞对应 Gate，不阻塞其余可完成工作。

==================================================
1. 第一阶段：真实仓库接管
==================================================

立即执行：

```bash
git status
git diff --stat
git diff
git diff --cached
git log --oneline -40
git rev-parse HEAD
git branch --show-current
```

若存在未提交修改：

```bash
git diff > agent_master_takeover_unstaged.patch
git diff --cached > agent_master_takeover_staged.patch
```

不要删除。

创建：

`AGENT_MASTER_TAKEOVER_REPORT.md`

记录：

- current HEAD
- branch
- dirty files
- staged files
- untracked files
- 最近 40 commit
- 当前 Docker/Postgres/Redis/MinIO 状态
- 当前 backend/frontend test 状态
- 当前各任务线状态：
  - A Scope Remodel
  - B P0 Publish Closure
  - C Consumer UX v1
- BLOCKED_EXTERNAL
- 第一项实际继续任务

==================================================
2. 恢复所有未完成 Goal / ADR / 状态文件
==================================================

按存在即读取：

## 总母版 / UX

- `宠物准入与公共空间共处规则平台_v0.6-R1_统一全量设计母版.md`
- `WORKBUDDY_CONSUMER_UX_BASELINE_V1_GOAL.md`
- `AGENT_CONTINUE_FROM_WORKBUDDY_GOAL.md`
- `首页与三条用户路径设计_2026-09-15.md`
- `项目评审与深化建议_2026-09-15.md`

## P0 / Review / Publish

- `P0_PUBLISH_CLOSURE_REPORT.md`
- `RULE_REVIEW_SHEET_R1.md`
- `HUMAN_REVIEW_PACKET_R1.md`
- `HUMAN_REVIEW_QUICK_TABLE_R1.md`
- `HUMAN_REVIEW_DECISIONS_R1.json`
- `ROLLBACK_RUNBOOK.md`
- `ENV01_RESOLUTION_REPORT.md`

## Scope / Animal Ontology

查找所有：
- ADR-020
- ADR-023
- AnimalRole / AnimalScope ADR
- RuleException ADR
- guide dog / service dog / police dog / military dog
- source_scope_exact
- subject_scope_normalized
- normalization_type
- FACILITATION_REQUIRED
- LEGAL_ACCESS_PROTECTION

## Production

- `PRODUCTION_STATE.md`
- `PRODUCTION_ACCEPTANCE_MATRIX.md`
- `BLOCKERS.md`
- `DECISIONS.md`
- `TECH_DEBT_REGISTER.md`
- `FINAL_PRODUCTION_READINESS_REPORT.md`

若文件名不同：
按语义寻找。

==================================================
3. 重新验证真实工程状态
==================================================

必须实际跑：

### Python

```bash
ruff check .
ruff format --check .
```

mypy 使用当前仓库既有命令。

### Frontend

- ESLint
- Prettier
- Typecheck
- H5 build
- Admin build
- client build
- uni-app x 可用构建

### Tests

如果 Docker / DB 可用：

- full pytest
- 不允许 deselect DB tests 后叫 full PASS
- rollback integration
- publish integration
- supersession
- PostGIS
- Redis
- Celery
- MinIO
- Playwright / E2E

记录真实数字。

==================================================
4. 建立 Unfinished Task Matrix
==================================================

创建：

`UNFINISHED_TASK_MATRIX.md`

至少：

| Workstream | Item | Status | Evidence | Next |
|---|---|---|---|---|
| A Scope | Guide dog exact scope | ... | ... | ... |
| A Scope | national accessibility rule | ... | ... | ... |
| A Scope | gh-outdoor-keep | ... | ... | ... |
| B Review | 33 human decisions | ... | ... | ... |
| B Publish | dry-run | ... | ... | ... |
| B Publish | first batch | ... | ... | ... |
| C UX | AccessAnswer | ... | ... | ... |
| C UX | Decision Home | ... | ... | ... |
| C UX | Rule Trace | ... | ... | ... |
| C UX | E2E | ... | ... | ... |

Status：

```text
DONE
PARTIAL
NOT_DONE
BLOCKED_HUMAN
BLOCKED_EXTERNAL
REGRESSED
```

后续按这个矩阵执行。

==================================================
5. WORKSTREAM A — Animal Scope 精确修复
==================================================

这是所有 Human Review 之前的前置。

如果已真实完成：
- 验证 migration/API/Admin/PetAccessJSON/Resolver/tests 后标 DONE。

如果未完成：
继续完成。

--------------------------------------------------
5.1 禁止 Guide Dog → Generic Service Dog 法律泛化
--------------------------------------------------

原则：

```text
Ontology parent relation
!=
Legal scope expansion
```

即：

```text
GUIDE_DOG is-a SERVICE_DOG
```

只能用于：

- 搜索
- 分类
- UI grouping
- query inheritance

不能用于：

```text
Source only says GUIDE_DOG
→ rule effect applies to all SERVICE_DOG
```

新增 / 验证 invariant：

```text
ONTOLOGY_PARENT_RELATIONSHIP
MUST_NOT
IMPLY_LEGAL_SCOPE_EXPANSION
```

--------------------------------------------------
5.2 Animal Role Taxonomy
--------------------------------------------------

至少：

```text
DOG
├─ ORDINARY_DOG
├─ SERVICE_DOG
│  ├─ GUIDE_DOG
│  ├─ HEARING_DOG
│  ├─ ASSISTANCE_DOG
│  └─ OTHER_SERVICE_DOG
├─ POLICE_DOG
└─ MILITARY_WORKING_DOG
```

注意：

- POLICE_DOG 不等于 SERVICE_DOG
- MILITARY_WORKING_DOG 不等于 SERVICE_DOG

--------------------------------------------------
5.3 Source Scope Fields
--------------------------------------------------

Rule / RuleCandidate 或等价模型支持：

```text
source_scope_exact
subject_scope_normalized
normalization_type
```

normalization_type 至少：

```text
EXACT
PARENT_GROUP_FOR_QUERY_ONLY
LEGAL_INTERPRETATION_REQUIRED
```

Source 写：

```text
盲人携带导盲犬
```

必须忠实保存。

不能自动存成：

```text
ALL_SERVICE_DOG
```

--------------------------------------------------
5.4 上海地方条例
--------------------------------------------------

正确模型：

```text
Base Rule
DOG
ENTER
PROHIBITED
Mandatory

RuleException
GUIDE_DOG
EXEMPT_FROM_PROHIBITION
```

不要：

```text
SERVICE_DOG ALLOWED
```

--------------------------------------------------
5.5 国家无障碍规则
--------------------------------------------------

如果当前模型支持，单独建模：

subjects：

```text
GUIDE_DOG
HEARING_DOG
ASSISTANCE_DOG
OTHER_SERVICE_DOG
```

holder scope：

```text
PERSON_WITH_DISABILITY
```

normative effect：

优先：

```text
FACILITATION_REQUIRED
```

或语义等价。

不要粗暴写成：

```text
UNCONDITIONAL_ALLOWED
```

如果当前 resolver 还没有 obligation 语义：
- 设计兼容扩展
- 不破坏当前 allow/prohibit API
- Consumer UI 通过 rights_information 暴露

--------------------------------------------------
5.6 Operator Policy 精确 Scope
--------------------------------------------------

逐条复核当前真实候选：

- Disney：
  原始来源若只写 guide dog，则精确为 GUIDE_DOG
  条件 leash_required 保留

- 前滩太古里：
  原始来源“除导盲犬外” → GUIDE_DOG

- 上海图书馆：
  若原文为导盲犬、军警犬例外：
  必须分别表达：
  GUIDE_DOG
  POLICE_DOG
  MILITARY_WORKING_DOG / 等价精确分类

- 和平饭店及其他：
  按 source exact wording 建模

--------------------------------------------------
5.7 gh-outdoor-keep
--------------------------------------------------

对候选：

```text
gh-outdoor-keep
```

不得批准。

如果当前证据仍只是 search snippet 且无法支持：

> 港汇恒隆 outdoor 普通宠物 conditional allowed

则：

```text
REJECT_CURRENT_CLAIM
```

或当前状态机等价：

```text
REJECTED
```

reason 至少包含：

```text
INSUFFICIENT_PLACE_ZONE_EVIDENCE
LEGAL_SCOPE_CONFLICT
```

保留：
- Source
- Evidence
- Audit
- Reject reason

未来若拿到运营方明确 Zone policy：
- 新建 Candidate
- 不恢复旧错误 Candidate

--------------------------------------------------
5.8 Scope Tests
--------------------------------------------------

至少：

1. ordinary dog + mall → prohibited
2. guide dog + applicable mall → local exception
3. hearing dog 不得继承 Shanghai guide-dog exception
4. assistance dog 不得继承 Shanghai guide-dog exception
5. national accessibility rule 对 guide/hearing/assistance 正确匹配
6. ontology parent 不扩大 legal effect
7. police dog != service dog
8. military working dog != service dog
9. Disney guide dog + leash
10. Shanghai Library precise scopes
11. gh-outdoor-keep cannot enter publish queue

必须跑：

- unit
- property
- integration
- migration
- API contract
- Admin
- PetAccessJSON

--------------------------------------------------
5.9 A Gate
--------------------------------------------------

只有：

```text
ANIMAL_SCOPE_REMODEL_GATE = PASS
```

才重新生成 Human Review Packet。

==================================================
6. 重新生成 Human Review Packet
==================================================

Scope 修复后：

重新生成：

- `RULE_REVIEW_SHEET_R2.md`
- `HUMAN_REVIEW_PACKET_R2.md`
- `HUMAN_REVIEW_QUICK_TABLE_R2.md`
- `HUMAN_REVIEW_DECISIONS_R2.json`

如果项目要求继续 R1 文件名：
可兼容保留，但必须明确 revision。

每条显示：

- candidate id
- place
- zone
- exact source scope
- normalized scope
- action/effect
- RuleLayer
- MandatoryLevel
- RuleException
- EvidenceStrength
- Source URL
- key quote
- place match
- license
- conflict
- AI recommendation
- recommendation reason
- human final decision blank
- reviewer blank
- reviewed_at blank

重要：

> 不得继承旧包中因 scope 泛化产生的 AI Recommendation 而不重新计算。

==================================================
7. WORKSTREAM B — P0 Human Review / Publish Closure
==================================================

--------------------------------------------------
7.1 判断 GOV-01 是否解除
--------------------------------------------------

检查：

`HUMAN_REVIEW_DECISIONS_R2.json`
或当前正式 review decisions 文件。

具名人类必须填写：

```text
reviewer
reviewed_at
final_decision
```

允许决策：

```text
APPROVED
APPROVED_WITH_NOTE
HOLD
REJECTED
```

如果为空：

```text
GOV-01 = BLOCKED_HUMAN
```

Agent 不得代签。

--------------------------------------------------
7.2 如果 GOV-01 仍 BLOCKED_HUMAN
--------------------------------------------------

则：

1. 不 Publish。
2. 不进入 30–50 Place。
3. 更新 `BLOCKERS.md`。
4. 生成/更新 Human Review materials。
5. 继续 Workstream C Consumer UX。
6. 继续其他不依赖正式 Publish 的测试/安全/文档/前端工作。

不要因为等人工签署而停止整个项目。

--------------------------------------------------
7.3 如果 GOV-01 已解除
--------------------------------------------------

先 dry-run：

```bash
python scripts/publish_reviewed_r1.py --dry-run
```

或当前正式脚本。

必须验证：

- signed=true
- reviewer 完整
- reviewed_at 完整
- 决策总数一致
- HOLD 不可发布
- REJECT 不可发布
- weak evidence 不可绕 Gate
- mandatory level 完整
- scope exact 完整
- Pre-Publish Validation 全执行
- no duplicate
- no self supersede

--------------------------------------------------
7.4 第一批 Publish
--------------------------------------------------

不要一口气发全部 Approved。

优先：

> 10–15 条最强证据 / 最清晰 Scope / 无冲突 Rule

顺序：

1. 政府 / 法规
2. 政府公告
3. Operator Official
4. Official brand / hotel / park
5. 无 search snippet-only
6. 无 unresolved P0 gap

--------------------------------------------------
7.5 Publish Drill
--------------------------------------------------

验证：

```text
Human Review
→ Candidate APPROVED
→ Pre-Publish Validation
→ Publish
→ AccessRule
→ RuleVersion
→ Evidence
→ Source
→ Resolver
→ API
→ H5/Client
→ Audit
```

至少做：

### Withdraw

```text
Published
→ Withdrawn
→ Evaluator = UNKNOWN
→ Evidence retained
→ Audit retained
```

### Supersession

```text
V1 Published
→ New Candidate
→ V2 Published
→ V1 Superseded
→ V2 Current
```

### Watch

规则变化：
- 产生正确 watch notification
- idempotent
- 不重复轰炸

--------------------------------------------------
7.6 B Gate
--------------------------------------------------

只有以下通过：

```text
PILOT_REVIEW_PUBLISH_GATE = PASS
```

要求：

- 全候选有人类最终状态
- wrong attribution rejected
- weak evidence held
- first real publish success
- Published Evidence = 100%
- Published Source = 100%
- Published source-policy/license coverage = 100%
- MandatoryLevel correct
- RuleException correct
- Animal scope exact
- rollback PASS
- supersession PASS
- watch PASS
- audit PASS
- resolver critical errors = 0
- full regression PASS

只有该 Gate PASS：
才允许未来进入 30–50 Place。

==================================================
8. WORKSTREAM C — Consumer UX Baseline v1
==================================================

A Scope Remodel 完成后即可继续 C。

不需要等 GOV-01 Human Signature。

但：
- Pending Candidate 不得冒充 Published Rule
- UI 使用 DEMO fixture 时必须标 DEMO/FICTIONAL
- 真实生产态只消费 Published Rule

==================================================
9. Consumer UX 产品方向冻结
==================================================

1. Search-first。
2. 首页不是 Map-first。
3. 首页是 Decision Home。
4. 地图是一级 Tab。
5. 三路径：
   A. 已知目的地 → 搜索 / 历史 / 分享
   B. 未知目的地 → 分类 / 附近 / 地图
   C. 现场 → 拍规则牌 / 核验
6. 小程序 = 20 秒查清。
7. App = 同一答案体系 + Watch / 消息 / 历史 / 完整档案。
8. Place Detail = 规则护照。
9. UNKNOWN != ALLOWED。
10. Zone 不压平成 Place 总状态。
11. Evidence 数量不代替 applicability。

==================================================
10. 统一 AccessAnswer
==================================================

首页、Search、Map Card、Place Detail、H5 Share、Watch：

必须消费统一答案模型。

最低：

```text
query_context
normative_result
condition_evaluation
scope_summary
evidence_state
conflict_state
rights_information
matched_rule_versions
explanation_items
next_actions
evaluated_at
valid_until
evaluation_version
```

禁止页面自行算 Rule。

==================================================
11. Decision Home
==================================================

冻结结构：

```text
上海 · 试点           覆盖范围

去之前，查清规则

[ 搜索场所名、分店或地址 ]

[ 看场所规则 | 携带动物 | 共处偏好 ]

最近查看（有才显示）

[ 公园 ][ 商场 ][ 餐饮 ][ 酒店 ][ 更多 ]

附近已核验           看地图 >

Place Card

规则待核实

Place Card

拍规则牌 / 现场核验

首页 | 地图 | 贡献 | 我的
```

App 可增加消息 Tab。

==================================================
12. 首页六个修正
==================================================

### 12.1 Verified 范围精确

不要：

```text
示例公园 A 已核验
```

而是：

```text
已核验：普通犬 · 南侧草坪
```

### 12.2 “待核实场所”改“规则待核实”

### 12.3 状态卡中性

不要大面积绿色。

### 12.4 条件明确为“进入前需满足”

### 12.5 加“为什么？”

### 12.6 Contribution 降低视觉优先级

==================================================
13. 三个查询视角
==================================================

Consumer 文案：

```text
看场所规则
携带动物
共处偏好
```

默认：

```text
看场所规则
```

==================================================
14. 携带动物
==================================================

渐进询问：

```text
动物类型
→ 体重
→ 肩高
→ 数量
→ 推车/包
```

只问真正影响 Rule 的字段。

Guide / service-dog 使用 Workstream A 的精确 Scope。

==================================================
15. 共处偏好
==================================================

首版：

- 室内堂食
- 独立区域
- 顾客座椅
- 餐具
- 食品自助区

输出：

```text
符合
不符合
未知
```

无评分。

==================================================
16. Search
==================================================

支持：

- 名称
- 分店
- 地址
- 别名
- 旧名

同名必须消歧。

明确搜索的 Place 即使不符合偏好：
仍然显示，并说明为什么。

错误区分：

```text
未识别
有 Place 无 Rule
超出覆盖
Provider/网络失败
```

==================================================
17. Recent History
==================================================

- 2–3 条
- 重新求值
- 不复用旧答案
- 规则变化显示有更新
- 未登录可用
- 可清空

==================================================
18. Place Detail / Rule Passport
==================================================

第一屏：

1. Place
2. Query Context
3. Main Answer
4. Scope
5. Conditions
6. Unknown
7. Source / verified time
8. Next Action
9. 为什么

后续保持：

1. 当前答案
2. Zone
3. Conditions
4. Coexistence
5. Entrance / AccessPath
6. Amenity
7. Source / Evidence
8. Observation
9. Version History
10. Correction / Operator Claim

==================================================
19. Rule Trace
==================================================

真实消费 Resolver explanation。

例如：

```text
有条件进入

南侧草坪开放
└ 管理方公告

需全程牵引
└ 管理方公告

室内展馆
└ 尚无足够依据
```

==================================================
20. Map Tab
==================================================

一级 Tab：

```text
Area
→ Lens
→ Filter
→ Marker / Cluster
→ Bottom Sheet
→ Detail
```

地图失败：
- list fallback

定位拒绝：
- manual area

==================================================
21. Contribution
==================================================

统一：

```text
选择类型
→ Place/Branch/Zone
→ Photo/URL
→ OCR/Extract
→ User Confirm
→ Candidate
→ Receipt
```

现场经历：

```text
ObservationCandidate
```

AI UI 文案：

```text
AI 建议
```

不得写：

```text
AI 已确认
```

==================================================
22. Mini Program
==================================================

导航：

```text
首页
地图
贡献
我的
```

目标：

> 20 秒查清。

==================================================
23. App
==================================================

导航：

```text
首页
地图
贡献
消息
我的
```

增加：

- Complete PetProfile
- BoundaryProfile
- Watch
- Rule updates
- Version History
- Evidence
- Offline favorites

核心答案与小程序一致。

==================================================
24. H5 Share
==================================================

分享直达 Detail。

不强制：
- 登录
- App
- 首页

不泄露：
- 体重
- Boundary
- 健康信息
- 私密 PetProfile

==================================================
25. UI States
==================================================

必须：

- loading
- skeleton
- empty
- partial
- stale
- conflict
- error
- offline
- permission denied
- provider failure
- out-of-coverage

==================================================
26. Accessibility
==================================================

至少：

- 44px touch
- H5 keyboard
- focus
- semantic labels
- font scaling
- no color-only
- reduced motion
- 200% zoom

==================================================
27. Consumer UX Tests
==================================================

至少：

1. anonymous search → answer
2. history rule changed → recompute
3. branch disambiguation
4. zone allowed + another zone unknown
5. exact search doesn't hide mismatch
6. map failure → list
7. location denied → manual area
8. contribution → Candidate
9. share → direct Detail
10. withdrawn rule disappears
11. guide/service scope exact

Visual regression：

- Home
- Home no history
- Search
- Detail conditional
- Detail unknown
- Detail conflict
- Rule Trace
- Map
- Contribution
- H5 share

==================================================
28. C Gate
==================================================

只有真实通过：

```text
CONSUMER_UX_BASELINE_V1_GATE = PASS
```

包括：

- Search-first
- verified scope
- rule pending semantics
- Detail
- Zone
- Rule Trace
- Map Tab
- Contribution
- Mini Program / App / H5 consistency
- Guide/service precise
- accessibility
- E2E
- visual regression
- build
- lint
- typecheck
- backend regression

==================================================
29. A/B/C 的并行与阻塞规则
==================================================

正确执行：

```text
先完成 A（Scope）
       ↓
更新 Human Review Packet
       ↓
如果 GOV-01 未签：
    B = BLOCKED_HUMAN
    继续 C
       ↓
C PASS 后继续其他不依赖 B 的 production work
```

如果用户已经签：

```text
A PASS
↓
B Publish Closure PASS
↓
C 可继续/已继续
↓
才允许 30–50 Place
```

绝对不能：

```text
GOV-01 未签
→ Agent 自己填 final_decision
```

==================================================
30. 后续 30–50 Place 条件
==================================================

只有同时：

```text
ANIMAL_SCOPE_REMODEL_GATE = PASS
PILOT_REVIEW_PUBLISH_GATE = PASS
```

才允许启动已有：

`WORKBUDDY_REALITY_AUDIT_30_50_GOAL.md`

或等价 Goal。

Consumer UX PASS 单独不赋予扩量资格。

==================================================
31. 持续维护的状态文件
==================================================

更新：

- `PRODUCTION_STATE.md`
- `PRODUCTION_ACCEPTANCE_MATRIX.md`
- `BLOCKERS.md`
- `DECISIONS.md`
- `TECH_DEBT_REGISTER.md`
- `UNFINISHED_TASK_MATRIX.md`

新增：

- `ANIMAL_SCOPE_REMODEL_FINAL_REPORT.md`
- `HUMAN_REVIEW_PACKET_R2.md`
- `P0_PUBLISH_CLOSURE_R2_REPORT.md`（若 GOV-01 已解除）
- `CONSUMER_UX_BASELINE_V1_IMPLEMENTATION_REPORT.md`
- `AGENT_MASTER_CONTINUE_FINAL_REPORT.md`

==================================================
32. Commit Discipline
==================================================

建议小步：

```text
fix: preserve exact animal legal scope
fix: reject unsupported gh outdoor claim
test: enforce ontology legal scope invariant
docs: regenerate human review packet r2

ui: finish decision home baseline
ui: unify access answer rendering
ui: add rule trace and scoped verification
test: close consumer ux e2e
docs: close consumer ux baseline

data: publish first human-reviewed rules
test: validate publish rollback supersession
```

不要大爆炸 commit。

==================================================
33. 最终退出条件
==================================================

本次新 Agent 至少持续到：

```text
ANIMAL_SCOPE_REMODEL_GATE = PASS
```

以及：

```text
CONSUMER_UX_BASELINE_V1_GATE = PASS
```

如果 GOV-01 已由用户解除：
还必须做到：

```text
PILOT_REVIEW_PUBLISH_GATE = PASS
```

如果 GOV-01 尚未解除：

输出：

```text
PILOT_REVIEW_PUBLISH_GATE = BLOCKED_HUMAN
```

并精确说明：
用户只需完成什么签署。

最终生成：

`AGENT_MASTER_CONTINUE_FINAL_REPORT.md`

只允许诚实写：

```text
A Scope = PASS / FAIL
B Publish = PASS / BLOCKED_HUMAN / FAIL
C Consumer UX = PASS / FAIL
30–50 Expansion = ALLOWED / NOT_ALLOWED
```

==================================================
34. 立即开始
==================================================

现在直接：

1. 接管 Git。
2. 建立 UNFINISHED_TASK_MATRIX。
3. 先检查 Workstream A 是否真的做完。
4. 未完成就补完。
5. Scope PASS 后重新生成 Human Review Packet。
6. GOV-01 未签则标 BLOCKED_HUMAN，但继续 Consumer UX。
7. 完成 Consumer UX Baseline v1。
8. 若 GOV-01 已签，再完成首批 Publish Closure。
9. 不自动进入 30–50，除非 P0 Gate 真正 PASS。
10. 不问我是否继续。

不要只写计划，直接执行。
