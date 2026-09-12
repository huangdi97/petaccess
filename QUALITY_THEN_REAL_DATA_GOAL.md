# QUALITY_THEN_REAL_DATA_GOAL.md

> 本文件是当前阶段的最高执行目标，由用户指令（2026-09-13，手机远程）授权 Agent 自主创建并执行。
> 前置阅读：`AGENTS.md`、`docs/MASTER_DESIGN_v0.3_DEV.md`、`GOAL.md`、`DECISIONS.md`、
> `PROJECT_STATE_V05.md`、`V05_FINAL_REPORT.md`、`ACCEPTANCE_MATRIX_v0.5.md`、`BLOCKERS.md`。
>
> 执行纪律：不问用户是否继续；先 Quality 后真实数据；PART A Quality Gate 全 PASS 之前
> 禁止开始大规模抓取真实数据；状态只用 PASS / FAIL / BLOCKED_EXTERNAL / NOT_RUN / PARTIAL，
> PASS 必须有真实命令与真实输出。

---

## 仓库保护（已执行）

- 接管时禁止 `git reset --hard` / `git clean -fd` / `git checkout -- .`。
- 接管时快照：`git diff` → `quality_phase_pre_takeover.patch`（0 字节，无 tracked 修改），
  `git diff --cached` → `quality_phase_pre_takeover_staged.patch`（0 字节，无 staged）。
- 接管时状态（2026-09-13）：HEAD `2c9b547`，工作树仅 untracked 会话产物
  （`.workbuddy-ai/`、resume 文档、旧补丁快照、playwright-out/），无 modified/staged。

---

## PART A — ENGINEERING-QUALITY-FREEZE

本阶段禁止大规模抓取真实数据。目标：把当前代码打磨成可长期维护、可安全接入真实数据的高质量工程基线。

### A1 代码格式 / 风格

Python（必须实际运行）：Ruff format、Ruff lint、imports、unused imports、unreachable code、
broad exception、mutable defaults、async misuse、timezone-aware datetime、public interface typing。

TypeScript / Vue（必须实际运行）：Prettier、ESLint、strict TypeScript、no implicit any、
no unexplained unsafe cast、no duplicated API DTO、generated API client 与 OpenAPI 一致、
清理 dead code / unused export。

最终必须：format PASS / lint PASS / typecheck PASS / build PASS。不能只是新增配置文件。

### A2 类型质量

- 继续使用 mypy；重点覆盖 domain / services / repository / provider / rule resolver /
  candidate pipeline / evidence pipeline；避免 Any 穿透核心领域。
- TypeScript `strict = true`；Rule / Boundary / Provider 等核心枚举禁止散落 magic strings。

### A3 测试体系

原有测试全部保持 PASS。补充或核查以下覆盖：

- UNIT：RuleResolver、BoundaryMatcher、RuleCandidate、ObservationCandidate、EvidenceBundle、
  SourceMonitor、Freshness、DataLicense、PetAccessJSON、Answerability、media validation、
  provider error mapping。
- INTEGRATION：PostgreSQL、PostGIS、Redis、Celery、MinIO、API、RBAC、Audit、Migration、
  SourceMonitor、Media/OCR、Backup/Restore。
- CONTRACT：OpenAPI、generated TS client、PetAccessJSON、provider adapter、JSON Schema。
- E2E 至少真实覆盖 7 条链路：
  1. pet → place → rule result
  2. BoundaryProfile → explainable match
  3. signage upload → MinIO → OCR → EvidenceBundle → RuleCandidate → Admin Review → AccessRule → client
  4. verified operator → questionnaire/policy → resolver → client
  5. source changed → SourceMonitor → Evidence → Candidate → supersede old rule → watch notification
  6. external lead → EvidenceBundle → RuleCandidate/ObservationCandidate → Review，且不能直接 Publish
  7. Entrance / AccessPath / Amenity 显示

### A4 Property-based / 不变量测试（Hypothesis 或等价）

- UNKNOWN 不能自动变 MATCH
- 未发布 RuleCandidate 不能进入 EffectiveRuleSet
- 未发布 ObservationCandidate 不能成为正式 ObservationClaim
- Observation 不能改变 normative RuleResolver
- expired temporary rule 不能 current
- superseded rule 不能 current
- service_dog 与 ordinary_pet scope 隔离
- external provider id 永远不能成为 Place 主键
- stale 不能等于 invalid
- mandatory legal constraint 不能被低层 operator policy 静默覆盖

### A5 Coverage

真实 coverage report。建议 backend domain/services line ≥ 85%、branch ≥ 75%；
RuleResolver / Candidate state machine / BoundaryMatcher / SourceMonitor / Evidence pipeline
尽量 line ≥ 90%。不为覆盖率造无价值测试。产出 `TEST_COVERAGE_REPORT.md`。

### A6 数据库

检查 FK / unique / check constraints / PostGIS indexes / bbox、nearby / candidate queue、
source monitor、audit 索引 / N+1 / query plan；执行 upgrade → downgrade → upgrade，
验证 fresh DB / seed DB / populated DB。产出 `DB_INTEGRITY_REPORT.md`。

### A7 Migration Audit

additive first、尽量 reversible、destructive 必须说明、backfill 幂等、禁止 silent data loss。
产出 `MIGRATION_AUDIT.md`。

### A8 Security

pip-audit、pnpm/npm audit、secret scan；.env 不入库、API Key 不入库。
API：RBAC、IDOR、rate limit、CORS、auth expiry、privilege escalation、idempotency。
Upload：MIME、extension mismatch、oversized、malformed image、decompression bomb（如适用）、
path traversal、filename injection。
SourceMonitor / External Fetcher：只允许 http/https、禁止 localhost/private network、
redirect 校验、timeout、max response bytes、content type、禁止 file://。重点 SSRF 防护。
产出 `SECURITY_AUDIT.md`。

### A9 Privacy

用户 raw GPS 不长期默认保存；media 默认 private；Evidence 不保存无必要 PII；
face / license plate redaction 能力或处理策略；evidence retention / deletion；
BoundaryProfile 最小化；小区不存住户养宠档案。产出 `PRIVACY_DATA_INVENTORY.md`。

### A10 Reliability

实际测试或合理模拟：Redis unavailable、DB transient failure、MinIO unavailable、Celery restart、
duplicate task、OCR failure、AI timeout、Map provider timeout、SourceMonitor duplicated fetch、
Notification retry。要求 bounded retry、idempotency、failure visible、no infinite retry、
no duplicate Rule publish。

### A11 Performance

建立 baseline：API p50/p95、nearby、bbox map query、resolver batch、answerability、
candidate queue、source monitor batch、admin pagination；必要位置 EXPLAIN ANALYZE。
产出 `PERFORMANCE_BASELINE.md`。

### A12 Concurrency

测试：两个 reviewer 同时处理一个 Candidate、两个 Operator 同时改 Policy、
SourceMonitor 同时触发、RuleVersion race、duplicate publish、duplicate watch notification。
通过 transaction / optimistic locking / unique guard / version check 等当前架构合适方法解决。

### A13 Backup / Restore

实际执行 backup → mutate/delete → restore clean DB → integrity compare；
MinIO bucket/metadata/restore-export 策略。产出 `BACKUP_RESTORE_EVIDENCE.md`。

### A14 Observability

request_id、task_id、structured logging、provider latency、DB/Redis/MinIO/worker health、
SourceMonitor metrics、Candidate counts、failed job visibility、Rule publish event。
不为本地 RC 引入过重基础设施。

### A15 Dead Code / Tech Debt

扫描 TODO / FIXME / HACK / pass / NotImplemented / mock-only production path / orphan file /
unused env / duplicate schema。能修就修；不能本轮修的统一写 `TECH_DEBT_REGISTER.md`。不能藏。

### A16 Reproducibility

干净环境验证 repo → env → dependencies → Docker infra → migration → seed → backend →
Admin → H5 → tests；README 命令实际验证。产出 `REPRODUCIBILITY_REPORT.md`。

### A17 Quality Gate

产出 `ENGINEERING_QUALITY_FINAL_REPORT.md`。以下全部满足才能进入 PART B：
format / lint / typecheck / backend tests / frontend tests / E2E / property tests PASS；
coverage 达标或有合理解释；migration PASS；security audit；dependency audit；
privacy inventory；backup/restore PASS；performance baseline；critical concurrency PASS；
无 unexplained TODO；docs reproducible。

通过后：本地 commit `release: engineering-quality-freeze`，可打本地 tag `v0.5-quality-freeze`；
不自动 push（无 remote，且未获授权）。

---

## PART B — EVIDENCE-FIRST REAL DATA AUTONOMOUS PILOT

只有 PART A Quality Gate PASS 后才能开始。核心原则：自动发现 ≠ 自动认定。
所有真实数据必须走 Source → SourceArtifact → EvidenceBundle →
RuleCandidate / ObservationCandidate → Review → Publish。AI 永远不能直接发布正式事实。

### B1 第一轮只做 10 个真实 Place

禁止直接抓 500/5000。通过后才允许扩 30–50。优先中国城市公开来源、高密度城区/商圈；
无法确认用户意向城市时不停止——选择官方公开数据丰富、便于证据核验的演示区域，
并在 `REAL_DATA_PILOT_10_REPORT.md` 写明选择依据。

### B2 来源优先级

Tier 1：政府/政府公开服务/场所官网/品牌官网/商场官网/酒店官网/景区官网/公园官网/
官方公众号公开页面/官方公告/官方宠物地图。
Tier 2：新闻/攻略/搜索结果/小红书/抖音/微博/点评社区 —— 默认只作 Lead Discovery，
不能直接形成正式 Rule。

### B3 搜索必须中性

对每个 Place 同时查询：`"<场所名>" 宠物`、`宠物友好`、`禁止`、`狗`、`携宠`、`入内`、
`推车`、`电梯`、`室内`、`户外` 等变体。数据必须覆盖 allowed / prohibited / conditional / unknown。

### B4 证据要求

每条 Candidate 尽量保存：source_platform、source_url、source_content_id、publisher/issuer、
published_at、captured_at、quoted/extracted fragment、content hash、screenshot ref（仅在许可允许时）、
place_match_evidence、temporal_evidence、AI extraction（model/version）、reviewer、
DataLicense/SourcePolicy。证据不足不得 Publish，保持 Lead / Candidate / Needs Verification。

### B5 Rule 与 Observation 分离

"店方规定/官方公告/工作人员正式说明" → RuleCandidate；"我看到/现场有人/用户经历" →
ObservationCandidate。不能混。

### B6 Original vs Derived Evidence

Original：URL、官方页面、公告、现场告示、截图、上传照片、视频关键帧。
Derived：OCR、AI extraction、Place match、normalized rule、summary。AI 不是原始证据。

### B7 外部平台合规

主动采集前检查 robots、official API、platform terms、copyright、storage/display/redistribution/
commercial rights、attribution、privacy。禁止绕登录、绕验证码、绕访问控制、规避反爬、
批量获取私密内容、收集无必要个人信息、无授权复制完整第三方作品公开展示。
社交平台优先：搜索发现 → 保存 URL/最小必要证据 → 找官方/管理方更强来源 → 再核验。

### B8 第一批 10 Place 构成

至少 3 餐饮/咖啡、2 商场、2 公园、1 酒店、1 景区/公共空间、1 其他；尽量满足：
≥3 种 source_type、≥2 个 Zone、≥2 个 conditional、≥1 个 prohibited、≥1 个 unknown、
≥1 个 RuleCandidate、≥1 个 ObservationCandidate、全部 Candidate 有证据链。

### B9 Reality Audit

每个真实 Place 必须跑：expressible?、unsupported condition、unknown fields、source quality、
evidence completeness、freshness、resolver result、boundary result、schema gaps。
表达不了的必须记 Schema Gap；禁止"塞到 note 里假装支持"。

### B10 Schema Gap

统计 gap type / frequency / severity / workaround / core impact。只有高频、高价值、
影响正确性的 Gap 才进入 Schema。

### B11 10 Place 报告

`REAL_DATA_PILOT_10_REPORT.md`：所有 Place、来源、EvidenceBundle 状态、RuleCandidate、
ObservationCandidate、approved/rejected、Schema Gap、license 状态、resolver 结果、
BoundaryMatcher 结果、数据错误、是否允许扩至 30–50 Place。

### B12 扩到 30–50

仅当第一批通过：约 20 餐饮/咖啡、5 商场、5 公园、5 酒店/景区/公共空间 + 对应法规。
目标：≥90% 常见规则可结构化、100% 正式发布 Rule 有 EvidenceBundle、0 条 AI 直接发布、
0 条无来源、0 条无 Place Match Evidence 的外部平台数据直接发布。
产出 `REALITY_AUDIT_REAL_01.md`。

### B13 首阶段不允许全自动 Publish

Agent 可自动发现/采集/OCR/抽取/匹配/提候选/去重/发现变化；正式 Publish 必须过 Review Gate。
第一轮真实数据建议全部人工审核。不为自动化牺牲准确性。

### B14 Data KPI

记录 Places discovered、Answerable Place Rate、RuleCandidate count、ObservationCandidate count、
Evidence Completeness、Official/operator source ratio、Candidate approval rate、
Attribution error、Schema gap rate、Stale rate、Conflict rate、Source change latency。
抓取网页数量不是 KPI。

### B15 自动停止条件

Schema Gap > 20%、Place attribution error > 5%、Evidence incomplete > 10%、
AI major extraction error > 5%、unauthorized source usage、Place merge instability、
duplicate instability —— 任一出现立即停止扩量，先修系统。

### B16 最终报告

`REAL_DATA_FINAL_REPORT.md`：Pilot area、Places、Sources、Evidence stats、Rules、Observations、
Approved/rejected Candidates、Schema gaps、DataLicense、Resolver correctness、Boundary matching、
SourceMonitor、Failures、Proposed schema changes、是否可扩 100–500 Place。

---

## 执行原则（最终）

1. 先 Quality，后真实数据。2. Quality Gate 没 PASS 不抓大规模数据。3. 可主动搜索公开信息。
4. 真实数据 Evidence-First。5. AI 只生成 Candidate。6. 社交平台默认 Lead Discovery。
7. 遵守 robots / 平台条款 / 版权 / 隐私 / 数据许可。8. 不绕登录、验证码、权限控制。
9. 真实数据先 10 个再 30–50。10. Reality Audit 决定是否扩 Schema。
11. 不为 Place 数量降低证据要求。12. 不问用户是否继续。

## 交付物清单

PART A：`TEST_COVERAGE_REPORT.md`、`DB_INTEGRITY_REPORT.md`、`MIGRATION_AUDIT.md`、
`SECURITY_AUDIT.md`、`PRIVACY_DATA_INVENTORY.md`、`PERFORMANCE_BASELINE.md`、
`BACKUP_RESTORE_EVIDENCE.md`、`TECH_DEBT_REGISTER.md`、`REPRODUCIBILITY_REPORT.md`、
`ENGINEERING_QUALITY_FINAL_REPORT.md`（+ 本目录的 BASELINE/ACCEPTANCE 两文件填充）。
PART B：`REAL_DATA_PILOT_10_REPORT.md`、（若扩量）`REALITY_AUDIT_REAL_01.md`、
`REAL_DATA_FINAL_REPORT.md`。
