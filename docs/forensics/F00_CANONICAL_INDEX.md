# F00_CANONICAL_INDEX — 文档分级索引（canonical/historical/stale）

> 用途：防止旧状态污染当前判断。生成于 2026-09-26 取证会话，只读扫描（文件名 + 首 40 行要点 + git 系谱核验），未修改任何源文件。
> git 系谱实测：`v0.1.0` tag = `c84b4cf`（KNOWN_GOOD 发布基线；发布记录提交 `5b1dd05`）；HEAD = `5af2bdb`（v0.2.0 M8-D 完结）；`v0.5-quality-freeze` 与 v0.5/WorkBuddy/生产线（`53c4c03` 等）均为 `v0.1.0` 的祖先，即**更早历史线**，v0.1.0/v0.2.0 主线已在它们之上完成发行与开发。

## 判定标准

| 标记 | 含义 | 用法 |
|---|---|---|
| **CURRENT** | 描述当前 HEAD 行为 / 当前质量门禁 / canonical spec | 必须作为本 Goal（全局取证审计与系统恢复，.pi/goal 20260926）依据 |
| **HISTORICAL** | 过去里程碑记录；作为历史/基线证据有效，但非规范 | 可引用为证据（尤其 v0.1.0 = HISTORICAL-BASELINE-EVIDENCE），不得当作当前状态或门禁 |
| **HISTORICAL-BASELINE-EVIDENCE** | 是 HISTORICAL 的子类：v0.1.0 KNOWN_GOOD 发布/审计证据 | 本取证 Goal 的 A 矩阵（KNOWN_GOOD 对照）唯一证据源 |
| **STALE** | 已被取代 / 状态过期 / 废弃 / 一次性上下文 | 不得用于判断当前；理由见 E 节与逐行依据 |

约束：当前 HEAD 状态唯一权威 = `PROJECT_STATE.md`（v0.1.0 RELEASED + v0.2.0 M1..M8 基线，下一 M9）；当前工程门禁 = `scripts/check_engineering_quality.py`（§40 门禁，见 `docs/audit/V020_GLOBAL_CODE_AUDIT.md`）与 `.github/workflows/pr-ci.yml`。

---

# A. ROOT 规范与状态（85 项 *.md，覆盖 100%）

| 文档路径 | 判定 | 依据 |
|---|---|---|
| AGENTS.md | CURRENT | 工程规则（阅读顺序/核心约束/质量词汇），本 Goal 必读，无版本过期 |
| PROJECT_STATE.md | CURRENT | 当前阶段唯一权威：v0.1.0 已发布 + v0.2.0 M2..M8 实测基线（938/2→944→946→…→E2E 与 visual 逐 M 更新），下一里程碑 V020_M9_ANDROID_FINAL |
| DECISIONS.md | CURRENT | Frozen ADR 累积清单（ADR-001..032 及 Status），最终决策源，跨版本有效 |
| README.md | CURRENT | 当前产品描述（当前版本 v0.1.0 Early Preview，Empty-First 产品定位） |
| CHANGELOG.md | CURRENT | 版本历史，v0.1.0 = 当前版本条目 |
| SECURITY.md | CURRENT | 安全政策（漏洞报告流程），非里程碑绑定 |
| CONTRIBUTING.md | CURRENT | 贡献指南，指向设计母版/AGENTS（指南本身现行） |
| CODE_OF_CONDUCT.md | CURRENT | 社区行为准则，版本无关 |
| COMPLIANCE_GATE.md | CURRENT | 合规矩阵（P7；LEGAL_REVIEW_REQUIRED 约束仍未过期，属约束而非状态快照） |
| COPY_GUIDE.md | CURRENT | 中性文案规范，机制仍被 `test_design_tokens.py::test_no_forbidden_copy_in_user_facing_sources` 在当前 HEAD 强制 |
| GOAL.md | HISTORICAL | v0.3 DEV 时代的最高目标（Phase 0-13 已完成），已被 v0.1.0/v0.2.0 主线取代；AGENTS.md 仍列阅读顺序，但作为历史基线目标引用 |
| RELEASE.md | HISTORICAL-BASELINE-EVIDENCE | v0.1.0 发布流程记录的权威文本；授权 `RELEASE_V0_1_0_AUTHORIZATION` 已于 2026-09-24 授予并完成发布（tag v0.1.0=c84b4cf） |
| IMPLEMENTATION_PLAN.md | HISTORICAL | v0.3 时代 Phase 计划，已由 M1..M8 里程碑交付取代 |
| BLOCKERS.md | HISTORICAL | v0.3 时代阻塞登记表（B-01 HBuilderX 等）；当下阻塞以各 V020_* 报告声明为准 |
| BLOCKERS_V05_TEMPLATE.md | HISTORICAL | v0.5 空模板（阻塞项格式 B-V05-XX），无实质内容，无判定影响 |
| FINAL_RELEASE_REPORT.md | HISTORICAL | v0.5 线本地 RC 报告（基线 95c357e），早于 v0.1.0 |
| FINAL_PRODUCTION_READINESS_REPORT.md | HISTORICAL | v0.5 生产线就绪终报（`READY_FOR_PUBLIC_BETA = NO` 等，见 E 节 #3）：已由 v0.1.0 Early Preview 发行演进，其「NO/未就绪」表述不得用作当前发布状态 |
| NEXT_GOAL_v0.5.md | HISTORICAL | v0.5 续跑目标（RC-HARDENING-01/V05-DOMAIN-01/PILOT-READINESS-01），已完成并被取代 |
| V05_FINAL_REPORT.md | HISTORICAL | v0.5 本地 RC 最终报告（V33 收口），v0.5 线终态证据 |
| BASELINE_FREEZE_V05.md | HISTORICAL | v0.5 基线冻结记录（95c357e/7eacfc3） |
| MIGRATION_V05.md | HISTORICAL | v0.5 迁移文档（7 revision 实测记录）；当前 schema 以 HEAD migrations 为准 |
| ACCEPTANCE_MATRIX.md | HISTORICAL | G00..G21 验收矩阵（v0.3 线），已被 v0.1.0/v0.2.0 门禁取代 |
| ACCEPTANCE_MATRIX_v0.5.md | HISTORICAL | v0.5 V-Gate 验收矩阵，v0.5 线证据 |
| QUALITY_THEN_REAL_DATA_GOAL.md | HISTORICAL | PART A/B 执行目标（2026-09-13 已完结）；其状态词纪律（PASS/BLOCKED_EXTERNAL…）仍是好实践但非规范 |
| ENGINEERING_QUALITY_BASELINE.md | HISTORICAL | PART A 起点基线（HEAD 2c9b547），数字已被 v0.1.0 938 基线取代 |
| ENGINEERING_QUALITY_ACCEPTANCE.md | HISTORICAL | PART A Q01..Q28 验收（2026-09-13 实测），被 v0.1.0/v0.2 gate 取代（门禁入口现为 docs/engineering/QUALITY_GATE.md） |
| ENGINEERING_QUALITY_FINAL_REPORT.md | HISTORICAL | PART A 终审（2026-09-13） |
| REAL_DATA_PILOT_STATE.md | HISTORICAL | PART B 实时状态（33 条 REVIEW_PENDING），v0.5 线 |
| REAL_DATA_PILOT_10_REPORT.md | HISTORICAL | 第一批 10 真实场所试点（R1） |
| REAL_DATA_PILOT_10_R2_REPORT.md | HISTORICAL | R2 收尾（SG-REAL-01 修复，evidence 93.9%） |
| REAL_DATA_FINAL_REPORT.md | HISTORICAL | PART B 最终报告（B16，0 条发布） |
| REAL_DATA_REVIEW_DECISIONS_R1.md | HISTORICAL | R1 审核工作稿（proposed_decision 非裁决） |
| REAL_DATA_PUBLISH_R1_REPORT.md | HISTORICAL | P0 发布准备执行报告（写库被外部条件阻塞；发布线此后在 09-17..21 真实执行，见 governance） |
| PUBLISHED_RULES_SNAPSHOT_R1.md | HISTORICAL | dry-run 快照（未写库） |
| RULE_REVIEW_SHEET_R1.md | STALE | R1 审核工作表（33 条），已被 R2/R2-FINAL（37 条）取代；文件自身被 `HUMAN_REVIEW_PACKET_R2_FINAL` 声明取代 |
| HUMAN_REVIEW_PACKET_R1.md | STALE | GOV-01 R1 签署包，文件自述「未被继承，全部重新计算」 |
| HUMAN_REVIEW_PACKET_R2.md | STALE | GOV-01 R2 签署包，被 R2-FINAL-R3 取代（文件自述） |
| HUMAN_REVIEW_QUICK_TABLE_R1.md | STALE | R1 速填表，被 R2_FINAL 取代 |
| HUMAN_REVIEW_QUICK_TABLE_R2.md | STALE | R2 速填表，被 R2_FINAL 取代 |
| HUMAN_REVIEW_PACKET_R2_FINAL.md | HISTORICAL | GOV-01 最终签署包（R2-FINAL-R3，37 条，签名基线） |
| HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md | HISTORICAL | 最终速填表（R2-FINAL-R3） |
| HUMAN_SIGNATURE_READINESS_AUDIT.md | HISTORICAL | 签名就绪审计（R2-FINAL-R3 同源） |
| PRODUCTION_STATE.md | STALE | 2026-09-14 生产状态（HEAD 53c4c03，v0.5 生产线的「写库就绪/ENV-01 解除」），其 HEAD/数据基线已被 Wave01/02 与 v0.1.0 主线取代，不得作为当前 HEAD 状态 |
| PRODUCTION_TAKEOVER_REPORT.md | HISTORICAL | P00 生产接管审计（PostGIS 阻塞结论已被 ENV01_RESOLUTION 解除） |
| PRODUCTION_ACCEPTANCE_MATRIX.md | HISTORICAL | 生产验收矩阵（2026-09-14，53c4c03） |
| P0_PUBLISH_CLOSURE_REPORT.md | HISTORICAL | P0 发布闭环（2026-09-14） |
| ENV01_RESOLUTION_REPORT.md | HISTORICAL | ENV-01 解除实录 |
| ANIMAL_SCOPE_REMODEL_FINAL_REPORT.md | HISTORICAL | Workstream A 收口（2026-09-15，53c4c03） |
| CONSUMER_UX_BASELINE_V1_IMPLEMENTATION_REPORT.md | HISTORICAL | Workstream C 实施报告（2026-09-15），UI 已被 v0.2.0 M2..M8 重构取代 |
| AI_PROVIDER_SELECTION.md | HISTORICAL | v0.5 决策记录（未选型）；当前 AI 事实以 HEAD 代码为准 |
| BACKUP_RESTORE_EVIDENCE.md | HISTORICAL | PART A A13 演练证据（2026-09-13） |
| REPRODUCIBILITY_REPORT.md | HISTORICAL | PART A A16 可复现性报告 |
| PRIVACY_DATA_INVENTORY.md | HISTORICAL | PART A A9 数据清单（v0.5 时点盘点；机制仍被 current 代码约束但数字为当时） |
| PERFORMANCE_BASELINE.md | HISTORICAL | PART A A11 本地性能基线（4 演示场所） |
| TEST_COVERAGE_REPORT.md | HISTORICAL | PART A A5 覆盖率报告（数字被 v0.1.0 基线取代） |
| TECH_DEBT_REGISTER.md | HISTORICAL | PART A A15 债务登记（当前 HEAD 债务以 V010_TECH_DEBT_REGISTER 后续为准） |
| SECURITY_AUDIT.md | HISTORICAL | PART A A8 安全审计（2026-09-13）；v0.1.0 安全证据见 docs/release/V010_SECURITY_REPORT.md |
| DB_INTEGRITY_REPORT.md | HISTORICAL | PART A A6 结构清单（v0.5 时点） |
| MIGRATION_AUDIT.md | HISTORICAL | PART A A7 迁移链核验（v0.5 时点） |
| UI_UX_IMPLEMENTATION_SPEC.md | HISTORICAL | v0.6 Beta UI/UX 生产化规范（生产线）；当前 UI 规范 = V020_*_SPEC（v0.2.0） |
| UI_UX_IMPLEMENTATION_REPORT.md | HISTORICAL | P3 实现报告（基准 716b163） |
| UI_STATE_MATRIX.md | HISTORICAL | 状态矩阵（53c4c03），UI 状态已收口于 V020_EMPTY_ERROR_OFFLINE_SPEC |
| UX_FLOW.md | HISTORICAL | 用户流程（716b163） |
| PRODUCT_IA.md | HISTORICAL | 信息架构（716b163） |
| DESIGN_SYSTEM.md | HISTORICAL | v0.6 设计系统说明；当前 SSOT = packages/design-tokens + V020_DESIGN_SYSTEM_SPEC |
| FRONTEND_ACCEPTANCE.md | HISTORICAL | 前端验收矩阵（716b163） |
| FRONTEND_QA_REPORT.md | HISTORICAL | 前端 QA（08ee60c） |
| UI_CORE_CLOSURE_REPORT.md | HISTORICAL | UI 核心收口（53c4c03），v0.2 重构已在此基础上演进 |
| LAUNCH_READINESS_CHECKLIST.md | STALE | 发布就绪清单（基准 a970a80，「当前 10 场所」数字已被 Wave01/02（30+）与 v0.1.0 发行取代） |
| UNFINISHED_TASK_MATRIX.md | HISTORICAL | 2026-09-15 未完成任务矩阵（53c4c03） |
| PROJECT_STATE_V05.md | STALE | v0.5 状态文档（V0.5 LOCAL RC COMPLETE），状态已被 PROJECT_STATE.md 取代 |
| README_V05_NEXT.md | STALE | v0.5 一次性升级包安装说明（任务已完成） |
| WORKBUDDY_TAKEOVER_REPORT.md | HISTORICAL | WorkBuddy 接管时仓库状态实录（2026-09-12，HEAD 0542827），历史证据 |
| WORKBUDDY_PRODUCTION_MASTER_GOAL.md | STALE | WorkBuddy 生产线执行目标（1455 行一次性治理文档），已被 v0.1.0 发行主线取代 |
| WORKBUDDY_PRODUCTION_START_PROMPT.md | STALE | 一次性接管提示词 |
| README_WORKBUDDY_PRODUCTION_PACK.md | STALE | 一次性 pack 使用说明 |
| ZCODE_START_PROMPT.md | STALE | 一次性开跑提示词（v0.3 时代） |
| ZCODE_CONTINUE_PROMPT_v0.5.md | STALE | 一次性续跑提示词（v0.5 时代） |
| ZCODE_RESUME_COMMAND.md | STALE | 一次性接管命令脚本 |
| ZCODE_RESUME_AFTER_WORKBUDDY_v0.5.md | STALE | 一次性续跑目标文档（953 行） |
| ZCODE_RESUME_TAKEOVER_REPORT.md | HISTORICAL | ZCode 接管审计实录（2026-09-13，HEAD 88b4c70），历史证据 |
| AGENT_MASTER_TAKEOVER_REPORT.md | HISTORICAL | 2026-09-15 接管基线实测记录（53c4c03） |
| AGENT_MASTER_CONTINUE_FINAL_REPORT.md | HISTORICAL | 2026-09-15 终报（A=PASS / B=BLOCKED_HUMAN / C=PASS） |
| AGENT_MASTER_CONTINUE_ALL_UNFINISHED_GOAL.md | STALE | 一次性总接管目标（1382 行），已被主线取代 |
| 宠物准入与公共空间共处规则平台_v0.9-R1_…统一全量母版_2026-09-20.md | HISTORICAL | v0.9-R1 线的 Canonical Master（4551 行，含 Reality/Staff/AnimalFacility ENGINEERING_OPEN 状态）；属 v0.9 生产数据线设计母版，非当前 HEAD 线；其 §81-84 ENGINEERING_OPEN 状态已由 v0.2.0 M5/M7 实现演进（见 E 节污染项） |

---

# B. docs/release 与 docs/audit（24 项 md + 1 校验和文件，覆盖 100%）

## B.0 git 系谱结论（本次实测）

- `git merge-base --is-ancestor v0.5-quality-freeze v0.1.0` → 0（是）；`53c4c03…` ∈ `git rev-list v0.1.0`（是）。
- 即：v0.5 线 / WorkBuddy / 生产基线全部早于 v0.1.0（KNOWN_GOOD，`c84b4cf`），HEAD `5af2bdb` 是 v0.1.0 之后的 v0.2.0 M1..M8 线。**任何 v0.5/生产线的"当前状态"表述都不能用于判断现在的 HEAD。**

## B.1 按目录（docs/release 开头的 V010 系列均为 v0.1.0 证据）

| 文档路径 | 判定 | 依据 |
|---|---|---|
| docs/release/V010_RELEASE_READINESS_REPORT.md | HISTORICAL-BASELINE-EVIDENCE | v0.1.0 发布就绪总表（CURRENT VERIFIED 标记，2026-09-24）；KNOWN_GOOD 门槛证据 |
| docs/release/V010_GITHUB_RELEASE_REPORT.md | HISTORICAL-BASELINE-EVIDENCE | tag v0.1.0 → c84b4cf、GitHub Release 已发布、Phase AH 校验记录 |
| docs/release/V010_TEST_REPORT.md | HISTORICAL-BASELINE-EVIDENCE | 发布前全量测试记录（938/2+E2E 21 等） |
| docs/release/V010_ARCHITECTURE_AUDIT.md | HISTORICAL-BASELINE-EVIDENCE | 架构审计（PASS） |
| docs/release/V010_GLOBAL_CODE_AUDIT.md | HISTORICAL-BASELINE-EVIDENCE | 代码门禁审计（PASS） |
| docs/release/V010_FRONTEND_UI_AUDIT.md | HISTORICAL-BASELINE-EVIDENCE | 前端 UI 审计 |
| docs/release/V010_ADMIN_AUDIT.md | HISTORICAL-BASELINE-EVIDENCE | Admin 审计 |
| docs/release/V010_EMPTY_STATE_REPORT.md | HISTORICAL-BASELINE-EVIDENCE | Empty-First 空态实测 |
| docs/release/V010_DESKTOP_REPORT.md | HISTORICAL-BASELINE-EVIDENCE | Windows 桌面实测 |
| docs/release/V010_ANDROID_REPORT.md | HISTORICAL-BASELINE-EVIDENCE | Android 实测 |
| docs/release/V010_SECURITY_REPORT.md | HISTORICAL-BASELINE-EVIDENCE | 安全/依赖审计（0/0） |
| docs/release/V010_VISUAL_QA_REPORT.md | HISTORICAL-BASELINE-EVIDENCE | 视觉 QA（真实渲染） |
| docs/release/ANDROID_SIGNING.md | HISTORICAL-BASELINE-EVIDENCE | v0.1.0 签名策略（release 签名，禁 debug 签名） |
| docs/release/ANDROID_PERMISSION_AUDIT.md | HISTORICAL-BASELINE-EVIDENCE | 权限清单（v0.1.0 不请求定位） |
| docs/release/SHA256SUMS-v010.txt | HISTORICAL-BASELINE-EVIDENCE | 产物哈希（A 矩阵校验物） |
| docs/release/V09_FINAL_REPORT.md | HISTORICAL | v0.9 线终态报告（HEAD 6a48135；tag v0.5-quality-freeze），早于 v0.1.0 |
| docs/release/PUBLIC_BETA_RC_REPORT.md | HISTORICAL | v0.9 Public Beta RC 判定（RC 冻结 6a48135） |
| docs/release/FINAL_RELEASE_CHECKLIST.md | HISTORICAL | v0.9 发布清单（READY_FOR_PUBLIC_BETA=NO 结论已被 v0.1.0 Early Preview 发行演进） |
| docs/release/FINAL_UAT_PREP.md | HISTORICAL | v0.9 UAT 准备材料（BLOCKED_HUMAN 是当时事实） |
| docs/release/STAGING_READINESS_REPORT.md | HISTORICAL | v0.9 staging 判定（BLOCKED_EXTERNAL 是当时事实） |
| docs/release/FINAL_PRODUCTION_READINESS_REPORT.md | HISTORICAL | v0.9 生产就绪终报（NOT_READY_FOR_PUBLIC_DEPLOY / READY_FOR_PUBLIC_BETA=NO）；该"不能发布"结论针对 v0.9 Public Beta 线，v0.1.0 后已按 Early Preview 发行，不得当作当前发布状态 |
| docs/audit/V010_REPOSITORY_BASELINE.md | HISTORICAL-BASELINE-EVIDENCE | v0.1.0 Phase A 仓库基线盘点（属 v0.1.0 证据；文件内中文乱码为坏编码，不影响其证据属性） |
| docs/audit/V010_TECH_DEBT_REGISTER.md | HISTORICAL-BASELINE-EVIDENCE | v0.1.0 债务登记（同乱码说明） |
| docs/audit/V010_A11Y_REPORT.md | HISTORICAL-BASELINE-EVIDENCE | v0.1.0 无障碍实测（CURRENT VERIFIED） |
| docs/audit/V020_GLOBAL_CODE_AUDIT.md | CURRENT | v0.2.0 M1 §40 全量机器门禁审计 = 当前工程门禁定义（check_engineering_quality.py），PROJECT_STATE 基线的门禁来源 |

---

# C. docs/v0.2（13 项，覆盖 100%）

| 文档路径 | 判定 | 依据 |
|---|---|---|
| docs/v0.2/V020_APP_SHELL_SPEC.md | CURRENT | M2 产物规范：ConsumerAppShell 壳层（chrome 归壳、页面管数据），描述当前 HEAD 结构 |
| docs/v0.2/V020_DESIGN_SYSTEM_SPEC.md | CURRENT | 当前设计系统 SSOT（packages/design-tokens + base/domain 组件），当前 UI 的规范源 |
| docs/v0.2/V020_EMPTY_ERROR_OFFLINE_SPEC.md | CURRENT | 空态/错误/离线/加载/Toast 统一规范（EMPTY_STATE_COPY SSOT），当前页面契约 |
| docs/v0.2/V020_M2_ENGINEERING_REPORT.md | HISTORICAL | M2 完结实测（2026-09-24） |
| docs/v0.2/V020_M2_SCREENSHOT_REVIEW.md | HISTORICAL | M2 逐图审阅记录 |
| docs/v0.2/V020_M3_CONSUMER_CORE_REPORT.md | HISTORICAL | M3 完结实测（route/query/PlacePreview） |
| docs/v0.2/V020_M4_MAP_AND_PASSPORT_REPORT.md | HISTORICAL | M4 完结实测（Map split-view / Passport，含 BLOCKED_EXTERNAL 腾讯地图无 Key 如实记录） |
| docs/v0.2/V020_M5_REALITY_TRACE_AND_EVIDENCE_REPORT.md | HISTORICAL | M5 完结实测（Reality Trace + Evidence） |
| docs/v0.2/V020_M7_CONTRIBUTION_UX_REPORT.md | HISTORICAL | M7 完结实测（贡献向导重建，ADR-029 三拍板） |
| docs/v0.2/V020_M8_DESKTOP_FINAL_REPORT.md | CURRENT-EVIDENCE | 最新完结里程碑实测（M8 DPI 矩阵 9 组/真实壳构建安装冒烟/Android 模拟器冒烟并入），PROJECT_STATE M8 基线的直接来源；当前门禁数字以本报告为最新 |
| docs/v0.2/V020_SEARCH_UX_REPORT.md | HISTORICAL | M2 Search 产品化记录（被 M3/M4 report 延续） |
| docs/v0.2/V020_HOME_UX_REPORT.md | HISTORICAL | M2 Home 产品化记录 |
| docs/v0.2/V020_REALITY_CONTRIBUTION_GAP_AUDIT.md | HISTORICAL | M2 后端缺口审计（只读结论，M7 已据此补齐贡献链） |

注：M6 无报告文件（M1 无报告文件，M1 成果=工程门禁收口，见 docs/audit/V020_GLOBAL_CODE_AUDIT.md）。

---

# D. docs/expansion 与 docs/governance（68 项，覆盖 100%）

## D.0 定性

这些是 **v0.5 生产数据线（2026-09-16..21）的真实执行记录**：Wave01（Batch-01A/01B 真实发布）、R2-FINAL-R3 Batch-02（9 行）、Wave02（20 条候选，16 条真实发布/4 条 HOLD）、Scope-Remodel-R2（round3/4/5，BATCH-03 发布）等。它们对 **生产库 petaccess 的数据历史** 是权威证据，但对 **当前 HEAD 代码/质量门禁** 不是规范。`petaccess` 生产库为 v0.5 时代的遗留环境（TEST_DATABASE_ISOLATION 已把测试与 petaccess 隔离），当前产品线（v0.1.0/v0.2.0）以 Empty-First 空数据设计发行——**生产库里的 30+ 真实 Place 不等同于当前发行版包含的数据**。

| 文档路径 | 判定 | 依据 |
|---|---|---|
| docs/expansion/WAVE01_SCOPE.md | HISTORICAL | Wave01 范围声明（EXP-R1-W01） |
| docs/expansion/WAVE01_FINAL_REPORT.md | HISTORICAL | Wave01 最终报告（脚本从生产库派生） |
| docs/expansion/WAVE01_BATCH_01A_REAL_PUBLISH_EXECUTION_REPORT.md | HISTORICAL | Wave01 Batch-01A 真实发布执行记录（REAL_PUBLISH_EXECUTED=YES） |
| docs/expansion/WAVE01_PRE_REAL_PUBLISH_SEMANTIC_BRIDGE_REPORT.md | HISTORICAL | 发布前语义桥接 |
| docs/expansion/WAVE01_PREPUBLISH_FINAL_REPORT.md | HISTORICAL | Wave01 签名+预发布（dry-run，未写库） |
| docs/expansion/WAVE01_REGRESSION_REPORT.md | HISTORICAL | Wave01 回归校验（alembic c9d4e2a17b30） |
| docs/expansion/HUMAN_REVIEW_PACKET.md | HISTORICAL | Wave01 人工复核包（工作稿；签署结果见 WAVE01 执行/closure 报告） |
| docs/expansion/HUMAN_REVIEW_QUICK_TABLE.md | HISTORICAL | Wave01 速填表 |
| docs/expansion/DATA_QUALITY_REPORT.md | HISTORICAL | Wave01 数据质量清单 |
| docs/expansion/FRESHNESS_MATRIX.md | HISTORICAL | Wave01 新鲜度矩阵 |
| docs/expansion/SOURCE_MONITOR_MATRIX.md | HISTORICAL | Wave01 来源监控矩阵 |
| docs/expansion/EVIDENCE_COVERAGE.md | HISTORICAL | Wave01 证据链覆盖 |
| docs/expansion/SOURCE_COVERAGE.md | HISTORICAL | Wave01 来源覆盖 |
| docs/expansion/NEW_10_PLACE_REPORT.md | HISTORICAL | 10 新增场所逐场所结果 |
| docs/expansion/EXISTING_7_GAP_REPORT.md | HISTORICAL | 存量 7 场所补齐情况 |
| docs/expansion/PLACE_SELECTION.md | HISTORICAL | 场所选取理由 |
| docs/expansion/WATCH_READINESS.md | HISTORICAL | Watch 就绪度 |
| docs/expansion/WAVE02_DATA_PIPELINE_REPORT_R1.md | HISTORICAL | Wave02 数据管线（10 Place + 20 REVIEW_PENDING 候选入库；未发布规则） |
| docs/expansion/WAVE02_HUMAN_REVIEW_PACKET.md | HISTORICAL | Wave02 复核包（工作稿；签署结果见 PREPUBLISH/PUBLISHABILITY） |
| docs/expansion/WAVE02_HUMAN_REVIEW_QUICK_TABLE.md | HISTORICAL | Wave02 速填表 |
| docs/expansion/WAVE02_REVIEW_RECOMMENDATIONS.md | HISTORICAL | Wave02 20 条候选 AI 建议（只读） |
| docs/expansion/WAVE02_PREPUBLISH_REPORT.md | HISTORICAL | Wave02 签名+预发布（未执行真实发布） |
| docs/expansion/WAVE02_PUBLISHABILITY_DISPOSITION.md | HISTORICAL | 16 可发布/4 不可发布判定（已签） |
| docs/expansion/WAVE02_REAL_PUBLISH_AUTHORIZATION_PACKET.md | HISTORICAL | 授权检查点材料包 |
| docs/expansion/WAVE02_RULE_PUBLISH_EXECUTION_REPORT.md | HISTORICAL | Wave02 真实发布执行（REAL_PUBLISH_EXECUTED=YES, BATCH-01） |
| docs/expansion/WAVE02_RULE_POSTPUBLISH_VERIFY.md | HISTORICAL | 发布后验证（canonical resolver 直连 live DB 复核） |
| docs/expansion/WAVE02_RULE_CLOSURE_REPORT.md | HISTORICAL | Wave02 Rule Track 收口（WAVE02_RULE_TRACK=CLOSED，16/4） |
| docs/expansion/B2_SCOPE_REMODEL_R2_CANDIDATES_REPORT.md | HISTORICAL | Gate B2 候选生成（未写库） |
| docs/expansion/SCOPE_REMODEL_R2_HUMAN_REVIEW_PACKET.md | HISTORICAL | R2 六候选复核包（工作稿；处置见 round3/4/5 报告） |
| docs/expansion/SCOPE_REMODEL_R2_HUMAN_REVIEW_QUICK_TABLE.md | HISTORICAL | R2 速填表 |
| docs/expansion/SCOPE_REMODEL_R2_CARVEOUT_HUMAN_REVIEW_PACKET.md | HISTORICAL | 迪士尼导盲犬 carve-out 复核包（处置见 round4/5） |
| docs/expansion/SCOPE_REMODEL_REVISION_R2_HUMAN_REVIEW_PACKET.md | HISTORICAL | 过宽术语拆分新 revision 复核包 |
| docs/expansion/PHASE_B_SCOPE_REMODEL_AND_OPEN_ITEMS.md | HISTORICAL | Phase B 非人工决定部分 |
| docs/expansion/PHASE_B_JURISDICTION_PROVISO_MECHANISM.md | HISTORICAL | ADR-030 但书机制交付（数据零变更） |
| docs/expansion/PHASE_B_REMAINING_GATES_B4_B5.md | HISTORICAL | B4/B5 剩余闸门复核 |
| docs/expansion/ADR030_JPROV001_ACTIVATION_REPORT.md | HISTORICAL | JPROV-001 激活执行（staged=1/activated=1） |
| docs/expansion/BATCH_02_REHEARSAL_REPORT.md | HISTORICAL | Batch-02 演练（生产克隆库，未写生产） |
| docs/expansion/B5_GEO_BACKFILL_AND_BATCH02_PUBLISH_REPORT.md | HISTORICAL | 坐标补录 + Batch-02 生产发布 |
| docs/governance/WAVE01_FINAL_CLOSURE_REPORT.md | HISTORICAL | Wave01 收口（Century Park 真实发布 1 行，EXP-R1-W01） |
| docs/governance/WAVE02_TAKEOVER_STATE_AUDIT_R1.md | HISTORICAL | Wave01 复验 + Wave02 启动审计 |
| docs/governance/WAVE02_START_AND_R2FINALR3_BACKLOG_REPORT.md | HISTORICAL | Wave02 启动 + R2-FINAL-R3 backlog |
| docs/governance/R2_FINAL_R3_BATCH_02_EXECUTION_AND_BACKLOG_CLOSURE.md | HISTORICAL | Batch-02 执行（9 行：6 AccessRule + 3 RuleException）与 backlog 闭环 |
| docs/governance/MASTER_GOAL_REMAINING_CHECKPOINT_R1.md | HISTORICAL | 剩余闭环检查点 R1（4 待决项） |
| docs/governance/MASTER_GOAL_REMAINING_CHECKPOINT_R2.md | HISTORICAL | 检查点 R2（已取代 R1；四项已裁决） |
| docs/governance/ROUND6_DISPOSITION_AND_CENTURY_PARK_EXECUTION_REPORT.md | HISTORICAL | Round6 处置 + Century Park 放行（无生产写入，dry-run） |
| docs/governance/B5_PUBLIC_BETA_MAP_DATA_QUALITY_R1.md | HISTORICAL | B5 坐标质量归项（不再阻挡治理闭环） |
| docs/governance/ADR032_LEGAL_PROVISION_LINEAGE_R1.md | HISTORICAL | ADR-032 LegalProvision 血缘模型（engineering track） |
| docs/governance/ADR030_HOLDER_SCOPE_CLOSURE_R1.md | HISTORICAL | ADR-031 holder scope 收口（LEGAL 层，BATCH_02 前） |
| docs/governance/OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL.md | STALE | 自标 STATUS=OPEN（待选 OPTION 1/2/3），该语义问题已由 SCOPE_REMODEL_R2 round3-5 处置闭环，其「OPEN」状态不得代表当前 |
| docs/governance/DISNEY_SCOPE_EXCEPTION_SEMANTIC_ISSUE.md | STALE | 自标 STATUS=OPEN（不修复），已由 carve-out 审查 + round4/5 真实发布处置，家族级关闭条件后续已另立 |
| docs/governance/LEGACY_EXCEPTION_MIGRATION_PLAN.md | HISTORICAL | 迁移计划（PLAN ONLY，未执行=未迁移） |
| docs/governance/BATCH_02_PRE_AUTHORIZATION_AUDIT.md | HISTORICAL | Batch-02 预授权审计 |
| docs/governance/AUDIT_EVENT_CONTRACT.md | HISTORICAL | 审计事件契约（唯一权威=app/core/audit_events.py，机制仍存在于当前 HEAD） |
| docs/governance/PRODUCTION_ISOLATION_CLOSURE_R1_GATE.md | HISTORICAL | 生产隔离闸门（PASS_WITH_LIMITATIONS） |
| docs/governance/PRODUCTION_INTEGRITY_LIMITATION_FINAL_CLOSURE.md | HISTORICAL | 生产完整性遗留收口（L4） |
| docs/governance/FIRST_REAL_PUBLISH_READINESS_R3.md | HISTORICAL | 首批真实发布准备 R3（未执行发布） |
| docs/governance/FIRST_REAL_PUBLISH_BATCH_01A_CLOSURE.md | HISTORICAL | Batch-01A 闭环（REAL_PUBLISH_EXECUTED=NO，等授权） |
| docs/governance/FIRST_REAL_PUBLISH_BATCH_01B_EXECUTION.md | HISTORICAL | **本项目第一次真实生产发布**（5 AccessRule + 3 RuleException，huangdi97 授权） |
| docs/governance/FIRST_REAL_PUBLISH_BATCH_01B_CLOSURE.md | HISTORICAL | 第一次真实发布（Batch-01B）的最终闭环报告（R2-FINAL-R3；01B 为历史首个 REAL_PUBLISH_EXECUTED 批次） |
| docs/governance/SCOPE_REMODEL_R2_MATERIALIZATION_REPORT.md | HISTORICAL | R2 候选入生产（1c10bbe worktree，写入候选/证据，未发布规则） |
| docs/governance/SCOPE_REMODEL_R2_POST_SIGNATURE_GATE_REPORT.md | HISTORICAL | 签署后闸门（REAL_PUBLISH_EXECUTED=NO 为该时点事实；其后 round5 完成 BATCH-03 真实发布） |
| docs/governance/SCOPE_REMODEL_R2_ROUND3_EXECUTION_REPORT.md | HISTORICAL | round3 执行（真实发布 BATCH-02 4 条 + selected-but-blocked 拒绝） |
| docs/governance/SCOPE_REMODEL_R2_ROUND4_EXECUTION_REPORT.md | HISTORICAL | round4（carve-out 签署→投影→批次→演练） |
| docs/governance/SCOPE_REMODEL_R2_ROUND5_REAL_PUBLISH_REPORT.md | HISTORICAL | round5 BATCH-03 真实发布（CREATE_ACCESS_RULE=1/CREATE_RULE_EXCEPTION=1） |
| docs/governance/PUBLISH_PLAN_MODEL.md | HISTORICAL | 发布计划模型（publish_reviewed_r1.py 唯一入口） |
| docs/governance/RULE_EXCEPTION_PUBLISHING.md | HISTORICAL | RuleException 发布规则（P0-01） |
| docs/governance/POST_SIGNATURE_PUBLISHER_CLOSURE.md | HISTORICAL | 签名后发布器闭环（GATE=PASS，未执行真实发布） |
| docs/governance/PUBLISH_BATCHES.md | STALE | 其中 `30_50_PLACE_EXPANSION = ALLOWED_NOT_STARTED — not started`（:6）已过期：Wave01/02 已实际执行并发布；表格后续批次的"当前"状态需以各执行报告为准 |

---

# E. 历史污染标记清单（STALE 状态字符串/文档，不得用于判断当前）

| # | 污染源（路径:行） | 污染字符串/表述 | 为什么不得用于判断当前 |
|---|---|---|---|
| 1 | docs/governance/PUBLISH_BATCHES.md:6 | `30_50_PLACE_EXPANSION = ALLOWED_NOT_STARTED — not started` | Wave01（Batch-01A/01B）与 Wave02（20 候选/16 发布）之后已实际执行；「NOT STARTED」状态过期 |
| 2 | 宠物准入…统一全量母版_2026-09-20.md:81-84、:3655 | Reality 各 Layer = `DESIGN_FROZEN / ENGINEERING_OPEN`（Observed Presence / Staff Response / Animal Facility / Reality Consumer UX） | 该 ENGINEERING_OPEN 是 v0.9-R1 时点状态；v0.2.0 M5（Reality Trace+Evidence）与 M7（Contribution UX）已实现在当前 HEAD，不能再按「未实现/PASS 未达成」解读 |
| 3 | FINAL_PRODUCTION_READINESS_REPORT.md:12（及 :303） | `READY_FOR_PUBLIC_BETA = NO` / `NOT_READY_FOR_PUBLIC_DEPLOY` | v0.5 生产线的就绪=NO 结论；其后 v0.1.0 已以 Early Preview 正式发行（tag c84b4cf）。该「NO」只对 v0.9 Public Beta 线成立，PubBeta判定须按当前 Goal 重新评估 |
| 4 | docs/release/FINAL_PRODUCTION_READINESS_REPORT.md:8、docs/release/PUBLIC_BETA_RC_REPORT.md（同结论） | `FINAL_PRODUCTION_READINESS = NOT_READY… / PUBLIC_BETA_RELEASED = NO` | 同上，v0.9 线报告；已发行 Early Preview 的事实覆盖了「未发布」表述 |
| 5 | docs/governance/OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL.md:3 | `STATUS = OPEN`（「不决定 OPTION 1/2/3」）+ `SIGNED_REVISION = R2-FINAL-R3` | 该 OPEN 语义问题已由 SCOPE_REMODEL_R2 round3-5 处置（含迪士尼 carve-out 真实发布）闭环；不得按「仍有未定语义缺口」使用 |
| 6 | docs/governance/DISNEY_SCOPE_EXCEPTION_SEMANTIC_ISSUE.md:3 | `STATUS = OPEN`（「本轮不修复」） | 该缺陷族已通过新 revision + carve-out 审查（round4）与真实发布（round5）处置关闭 |
| 7 | WORKBUDDY_PRODUCTION_MASTER_GOAL.md / WORKBUDDY_PRODUCTION_START_PROMPT.md / README_WORKBUDDY_PRODUCTION_PACK.md | 生产 Master Goal 全文（起点：`REAL_DATA_PILOT_10_R2 已完成 / Published = 0`） | 一次性接管线治理文档；其「当前状态」锚点（Published=0 等）已被 Wave01/02 真实发布推翻，且整条线已在 v0.1.0 发行前结束 |
| 8 | ZCODE_START_PROMPT.md / ZCODE_CONTINUE_PROMPT_v0.5.md / ZCODE_RESUME_COMMAND.md / ZCODE_RESUME_AFTER_WORKBUDDY_v0.5.md | 一次性 resume/prompt 指令（锚点：95c357e / 88b4c70 等旧 HEAD） | 提示词只对当时的会话有效；其引用的 HEAD/基线早于 v0.1.0，不得作为当前任务起点 |
| 9 | PROJECT_STATE_V05.md（V0.5 LOCAL RC COMPLETE）、README_V05_NEXT.md | v0.5「当前阶段」与升级包说明 | 状态过期：当前阶段以 PROJECT_STATE.md（v0.1.0+M8）为准；README_V05_NEXT 是已完成的一次性 overlay 安装说明 |
| 10 | PRODUCTION_STATE.md（2026-09-14，HEAD 53c4c03） | 生产状态「写库能力已就绪/仅剩 GOV-01 签署」 | 其 HEAD 与数据基线属 v0.5 生产数据线；之后有 Wave01/02 真实发布且主流已改道 v0.1.0 Empty-First 发行——该文件描述的状态不再是当前状态 |
| 11 | HUMAN_REVIEW_PACKET_R1/R2.md、HUMAN_REVIEW_QUICK_TABLE_R1/R2.md、RULE_REVIEW_SHEET_R1.md | GOV-01 签署包旧 revision（33 条；R1 建议基于已被撤回的 service_dog 泛化） | 文件自身声明被 R2_FINAL 取代（R2-FINAL-R3 共 37 条）；使用 R1/R2 内容会得到被撤销的审核建议 |
| 12 | docs/status/V09_FINAL_CURRENT_STATE_AUDIT.md 首行 | `> SUPERSEDED — 见 V09_FINAL_CURRENT_STATE_AUDIT_20260923.md` | 自标被 09-23 版取代；无需引用旧版做当前判断 |
| 13 | tag `v0.5-quality-freeze`、docs/release/V09_FINAL_REPORT.md（V09 终态） | v0.9 线的「终态」「冻结」叙事 | 该 tag/终态只是历史线上的一站（HEAD 6a48135），v0.1.0 班子在其后发行；不得把它当「项目最终状态」 |
| 14 | LAUNCH_READINESS_CHECKLIST.md（基准 a970a80） | `30–50 real Places —— 当前 10` | 数字时间点过期（Wave01/02 后生产库 30+ Place）；且生产库数据 ≠ 当前发行版数据 |

**用法红线：** 上述 14 项及其背后的 v0.9-R1 母版 ENGINEERING_OPEN 状态、v0.5 生产发布状态、WorkBuddy 接管文档、ZCODE 简历文档，在本次取证 Goal 中一律只作历史系谱参考（用于解释「为什么仓库里有这些文件」），**不参与**对当前 HEAD 任何门禁/状态/数据的判定。

---

# F. 其他 docs 组、CI、.pi/goal（补充表）

## F.1 docs/engineering（16 项）

| 文档路径 | 判定 | 依据 |
|---|---|---|
| docs/engineering/QUALITY_GATE.md | CURRENT | 质量闸门入口（命令/失败语义/当前状态）；权威清单链：ENGINEERING_QUALITY_ACCEPTANCE → QUALITY_GATE → §40 gate |
| docs/engineering/ERROR_MODEL.md | CURRENT | 统一错误模型（规范 §20），当前代码对外错误唯一路径 |
| docs/engineering/CODE_STYLE.md | CURRENT | 代码风格规则（工具强制），与当前 pyproject/eslint 一致 |
| docs/engineering/TESTING.md | CURRENT | 测试方针入口（什么断言算数），当前生效 |
| docs/engineering/TEST_MATRIX.md | CURRENT | 测试矩阵（规范 §8-§31 落点），当前回归结构 |
| docs/engineering/LOCAL_DEV_WINDOWS.md | CURRENT | Windows 本地开发实测命令，当前可用 |
| docs/engineering/DATABASE_ENVIRONMENT_MODEL.md | CURRENT | 数据库环境模型（每个库干什么），当前库隔离依据 |
| docs/engineering/TEST_DATABASE_ISOLATION.md | CURRENT | 测试库隔离原则（任何测试负载不可能写 petaccess），当前安全机制 |
| docs/engineering/PRODUCTION_DB_RUNBOOK.md | CURRENT | petaccess 运维手册（DatabaseSafetyGuard 唯一权威），当前生产库操作依据 |
| docs/engineering/PRODUCTION_DATA_INTEGRITY.md | CURRENT | 生产完整性检查（23 项只读检查脚本），当前工具 |
| docs/engineering/VERIFICATION_RUN_2026-09-15.md | HISTORICAL | 当日门禁重跑记录（53c4c03 时代），被 v0.1.0 基线取代 |
| docs/engineering/SECURITY_AUDIT.md | HISTORICAL | v0.5 线安全审计报告（v0.1.0 安全证据见 docs/release/V010_SECURITY_REPORT.md） |
| docs/engineering/REPOSITORY_HYGIENE_REPORT.md | HISTORICAL | 仓库卫生扫描记录（当时） |
| docs/engineering/PRODUCTION_CLEANUP_REPORT.md | HISTORICAL | 生产夹具清理执行记录（两批，2026-09-17） |
| docs/engineering/PRODUCTION_CONTAMINATION_AUDIT.md | HISTORICAL | 生产污染只读审计（当时结论） |
| docs/engineering/PRODUCTION_DUPLICATE_CURRENT_AUDIT.md | HISTORICAL | duplicate-current 审计（当时结论） |

## F.2 docs 根级（15 项）

| 文档路径 | 判定 | 依据 |
|---|---|---|
| docs/MASTER_DESIGN_v0.3_DEV.md | CURRENT | Canonical Design Master（自标「开发唯一设计母版」），README/AGENTS 仍指向它；当前产品核心不变量来源 |
| docs/ARCHITECTURE.md | CURRENT | 当前工程落地结构（uni-app x 源码 + client-core + H5 + FastAPI…） |
| docs/PLATFORMS.md | CURRENT | 跨端构建与平台差异（@petaccess/client-core 结构仍为当前） |
| docs/ROLLBACK_RUNBOOK.md | CURRENT | 回滚/回退手册（生产演练状态自我标注 NOT_RUN，手册本身现行） |
| docs/INCIDENT_RUNBOOK.md | CURRENT | 数据/运行事故手册（现行） |
| docs/BACKUP_RESTORE_RUNBOOK.md | CURRENT | 备份/恢复手册（现行；演练记录见 docs/backup） |
| docs/COEXISTENCE_BOUNDARY_SPEC.md | HISTORICAL | 早期规格小文（30 行），已并入母版与产品实现 |
| docs/RULE_RESOLVER_SPEC.md | HISTORICAL | 早期 resolver 规格（输入/输出骨架），v0.5 后已演进（v05_resolver 为准） |
| docs/DATA_PIPELINE_SPEC.md | HISTORICAL | 早期数据管线规格（来源分类），实现已超越 |
| docs/MIGRATION_SPEC_v0.5.md | HISTORICAL | v0.5 迁移原则规格（被 MIGRATION_V05.md 落实） |
| docs/TEST_PLAN_v0.5.md | HISTORICAL | v0.5 测试计划（被 TESTING/TEST_MATRIX 取代） |
| docs/PROVIDER_HARDENING_SPEC.md | HISTORICAL | v0.5 供应商硬化规格（Tencent 适配器已实现并 contract-tested） |
| docs/V05_ARCHITECTURE_DELTA.md | HISTORICAL | v0.5 架构增量（Legal→PolicyTemplate 链），已并入现行架构 |
| docs/REALITY_AUDIT_PLAN.md | HISTORICAL | reality audit 计划（两阶段），已执行完成（docs/reality_audit 产物） |
| docs/SOURCES_AND_RESEARCH.md | HISTORICAL | 设计参考链接（2026-09-06 时点） |

## F.3 docs 其余子目录（state/reality/audit/frontend/adr/legal/ops/security/backup/forensics）

| 文档路径 | 判定 | 依据 |
|---|---|---|
| docs/status/V09_FINAL_CURRENT_STATE_AUDIT.md | STALE | 首行自标 `SUPERSEDED`（被 20260923 版取代） |
| docs/status/V09_FINAL_CURRENT_STATE_AUDIT_20260923.md | HISTORICAL | v0.9 线终态实测审计（09-23 版） |
| docs/status/V09_CURRENT_REALITY_AUDIT.md | HISTORICAL | Wave02 复核点只读审计（09-21） |
| docs/reality/REALITY_DB_MIGRATION_VERIFICATION.md | HISTORICAL | Reality 迁移核验（09-22，v0.9 线） |
| docs/reality/30_PLACE_REALITY_AUDIT.md | HISTORICAL | 30 场所 reality 审计（09-23，生产库实测） |
| docs/reality/30_PLACE_DATA_QUALITY_REPORT.md | HISTORICAL | 30 场所数据质量（09-23） |
| docs/reality/30_PLACE_CONSUMER_ANSWERABILITY_REPORT.md | HISTORICAL | 30 场所消费者可答复性（09-23） |
| docs/reality/TEST_TREE_INVENTORY.md | HISTORICAL | 测试树盘点（09-22） |
| docs/reality_audit/REALITY_AUDIT_REPORT.md (+SCHEMA_GAPS.md) | HISTORICAL | v0.5 reality audit 工具首批合成样本产物（09-12） |
| docs/reality_audit/real_pilot_01/*、real_pilot_02/* | HISTORICAL | 真实试点 10 场所 audit 产物（09-12/13） |
| docs/reality_audit/EVIDENCE_REPAIR_LOG_R1.md | HISTORICAL | 证据补强记录（S6，09-13） |
| docs/reality_audit/REVIEW_WORKLIST_R1.md | HISTORICAL | 33 条候选审核工作清单（S2） |
| docs/frontend/A11Y_AUDIT.md | CURRENT | 无障碍检查工具文档（scripts/a11y_audit.mjs），V010 与 M2..M8 共用机制 |
| docs/frontend/UI_DESIGN_SYSTEM.md | CURRENT | 反映真实实现的 design-tokens 现状（唯一 token 源） |
| docs/frontend/VISUAL_REGRESSION_BASELINE.md | CURRENT | 截图基线机制与复跑命令（具体张数以当前 V020 报告为准） |
| docs/frontend/SEARCH_DISAMBIGUATION.md | CURRENT | `GET /api/v1/places?q=` 真实行为（同名/分店/排序），当前 API 契约 |
| docs/frontend/ADMIN_UI_AUDIT.md | HISTORICAL | 治理工作台审计（v0.1.0 前；Admin 后续仍有变动） |
| docs/frontend/CONSUMER_UI_AUDIT.md | HISTORICAL | Consumer UI 审计（被 v0.2.0 M2..M8 重构追赶） |
| docs/frontend/UI_REALITY_POLISH_REPORT.md | HISTORICAL | UI 走查修复记录（09-16） |
| docs/frontend/RESPONSIVE_MATRIX.md | HISTORICAL | 断点行为矩阵（v0.2 重构前）；v0.2 响应式以 M8 报告为准 |
| docs/frontend/MAP_AREA_LENS.md | HISTORICAL | 记录 MAP_AREA_LENS=FAIL（未实现）；结论需在 v0.2 面上重新验证 |
| docs/frontend/VISUAL_REGRESSION_MATRIX.md | HISTORICAL | 自标「旧结论已被取代」，仅历史缺口记录 |
| docs/adr/ADR-030-jurisdiction-level-statutory-proviso.md | HISTORICAL | v0.9 生产数据线的 ADR 文档（机制已实现；激活记录见 expansion/JPROV001） |
| docs/adr/ADR-031-holder-scope-and-service-role-semantics.md | HISTORICAL | ADR-031（Status: accepted）——决策并入 DECISIONS.md 体系，语义仍约束当前 domain，但文档属 v0.9 线 |
| docs/legal/README.md + 6 份 DRAFT（OPERATOR_CLAIM_TERMS / DATA_METHODOLOGY / CORRECTION_APPEAL_POLICY / USER_AGREEMENT / PRIVACY_POLICY / DISCLAIMER） | HISTORICAL | 工程侧法律草案（LEGAL_REVIEW_REQUIRED 未过期，未经律师审阅不得发布）；仍为当前唯一草案，但源自 v0.5 生产目标，非本 Goal 依据 |
| docs/ops/OBSERVABILITY_REPORT.md | HISTORICAL | 观测实测报告（09-23）；观测栈仍在 HEAD，数据需重跑验证 |
| docs/security/SECURITY_FINAL_REPORT.md | HISTORICAL | v0.9 线安全终报（09-23，0/0）；v0.1.0 安全证据见 V010_SECURITY_REPORT |
| docs/backup/BACKUP_RESTORE_DRILL_REPORT.md | HISTORICAL | 备份/恢复演练实测记录（09-23） |
| docs/forensics/F10_ADB_TOOLCHAIN_AUDIT.md | CURRENT | 本取证会话既有产物（多版本 adb 实证），继续有效 |

## F.4 .github/workflows（2 项）

| 文档路径 | 判定 | 依据 |
|---|---|---|
| .github/workflows/pr-ci.yml | CURRENT | 现役 PR/推送工程门禁（engineering-gate + secret scan + 测试 + 构建），当前质量门禁的一部分 |
| .github/workflows/release-ci.yml | CURRENT | 现役发布管线（tag v* 触发；verify→tests→H5→NSIS→APK→SHA256→SBOM），版本 SSOT 校验脚本=当前 |

## F.5 .pi/goal/ 契约（17 项，仅标题/首段判定）

| 契约文件（按日期排序） | 判定 | 依据 |
|---|---|---|
| first-real-publish-batch-preparation-r1-…-20260916-2329 | HISTORICAL | v0.5 生产数据线首批真实发布准备（已执行完毕） |
| 宠物准入平台-wave01-收口复验-wave02-数据管线-…-20260919-1949 | HISTORICAL | Wave02 契约（Wave01 收口复验 + data pipeline，已完结） |
| wave02-人类复核前-只读审计-…-20260921-0927 | HISTORICAL | Wave02 复核准备（已完结） |
| 波浪02-复核检查点推进-…-20260921-1622 | HISTORICAL | Wave02 复核推进（20 条审核建议，已签署并发布/挂起） |
| v0-9-r1-reality-layer-六阶段推进至-public-beta-判定-20260922-1243 | HISTORICAL | v0.9-R1 Reality 深化六阶段（已完结） |
| v0-9-r1-reality-深化至-public-beta-rc-生产发布另立契约-20260922-2318 | HISTORICAL | v0.9-R1 深化至 Public Beta RC（已终结于 09-23） |
| 宠物准入与公共空间共处规则平台-v0-9-完整马拉松至-public-beta-rc-冻结与诚实终态报告-20260923-1229 | HISTORICAL | v0.9 马拉松终态契约（冻结于 6a48135） |
| 宠物共处平台-v0-1-0-early-preview-工程收口-windows-android-tauri2-集成-ci-rc-20260923-1926 | HISTORICAL | v0.1.0 工程收口开端（HEAD 6079847） |
| 宠物共处平台-v0-1-0-early-preview-全量收口-工程-gate-empty-first-tauri2-wind-20260923-2006 | HISTORICAL | v0.1.0 全量收口（HEAD bf7b64c） |
| v0-1-0-early-preview-全量收口-a-ai-止步-release-v0-1-0-authorization-20260923-2341 | HISTORICAL | v0.1.0 收口至人类授权点（RELEASE_V0_1_0_AUTHORIZATION） |
| v0-1-0-early-preview-全仓治理-empty-first-tauri-windows-android-rc-冻-20260924-0017 | HISTORICAL | v0.1.0 RC 冻结契约（交付至 RC 冻结） |
| petaccess-v0-2-0-完整产品体验版-止步于-human-release-checkpoint-20260924-1254 | HISTORICAL | v0.2.0 主目标前置版（M0-M13 至 Human Checkpoint） |
| petaccess-v0-2-0-完整产品体验预览版-止步于-human-release-checkpoint-产出-v0-2-20260924-1310 | HISTORICAL | v0.2.0 主目标版（基准 c84b4cf/5b1dd05） |
| petaccess-v0-2-0-m2-product-experience-foundation-design-system-20260924-1802 | HISTORICAL | M2 契约（Design System 基础，已完结） |
| v020-m3-consumer-core-home-search-最终集成-…-20260924-2319 | HISTORICAL | M3 契约（已完结） |
| v020-m4-map-and-passport-map-桌面-split-view-…-20260925-1111 | HISTORICAL | M4 契约（已完结） |
| petaccess-全局取证审计与系统恢复-known-good-三矩阵根因证明-最小修复-全量回归与三端真实运行验证-20260926-1129 | **CURRENT** | **本 Goal 契约**：以 v0.1.0（tag v0.1.0=c84b4cf，KNOWN_GOOD）为对照做三矩阵取证；冻结 v0.2.0 新增功能 |

---


---

# 结论

## 分表计数（生成脚本按各表标签统计；文件级）

| 组 | CURRENT | HISTORICAL | 其中 HISTORICAL-BASELINE-EVIDENCE | STALE | 文件数 |
|---|---|---|---|---|---|
| A. ROOT（*.md） | 10 | 58 | 1（RELEASE.md） | 17 | 85 |
| B. docs/release + docs/audit（含 SHA256SUMS-v010.txt） | 1 | 24 | 18 | 0 | 25 |
| C. docs/v0.2（M8 计 CURRENT-EVIDENCE） | 4 | 9 | 0 | 0 | 13 |
| D. docs/expansion + docs/governance | 0 | 65 | 0 | 3 | 68 |
| F1. docs/engineering | 10 | 6 | 0 | 0 | 16 |
| F2. docs 根级（MASTER_DESIGN/ARCHITECTURE/runbook 等） | 6 | 9 | 0 | 0 | 15 |
| F3. docs 其余子目录（status/reality/reality_audit/frontend/adr/legal/ops/security/backup/forensics） | 5 | 34 | 0 | 1 | 40 |
| F4. .github/workflows | 2 | 0 | 0 | 0 | 2 |
| F5. .pi/goal 契约（本 Goal 1 项 CURRENT） | 1 | 16 | 0 | 0 | 17 |
| **合计** | **39** | **221** | **19** | **21** | **281** |

> 说明：分类按「文件（路径）级」计数；F3 中 docs/reality_audit（9 文件）与 docs/legal（7 文件）在正文以组合行覆盖，计数仍按文件数。HISTORICAL-BASELINE-EVIDENCE 共 19 项 = docs/release/V010 系列 14 项 + docs/audit/V010 系列 3 项 + docs/release/SHA256SUMS-v010.txt + RELEASE.md（v0.1.0 发布流程记录）。STALE 21 项 = A 组 17 + D 组 3（OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL / DISNEY_SCOPE_EXCEPTION_SEMANTIC_ISSUE / PUBLISH_BATCHES）+ V09_FINAL_CURRENT_STATE_AUDIT（自标 SUPERSEDED）。

## 本 Goal 的可信依据链（CURRENT 主线）

1. 契约：`.pi/goal/petaccess-全局取证审计与系统恢复-…-20260926-1129.md`（KNOWN_GOOD 三矩阵 A/B/C + F00-F13 交付物）
2. 状态：`PROJECT_STATE.md`（v0.1.0 RELEASED + M1..M8 实测基线，下一 V020_M9_ANDROID_FINAL）
3. 基线证据：tag `v0.1.0` = `c84b4cf`（KNOWN_GOOD，发布记录 commit `5b1dd05`）；`docs/release/V010_*` 与 `docs/audit/V010_*`（A 矩阵对照）
4. 门禁：`.github/workflows/pr-ci.yml` + `release-ci.yml`、`docs/audit/V020_GLOBAL_CODE_AUDIT.md`（§40 gate）、`docs/engineering/QUALITY_GATE.md`
5. 规格：`docs/MASTER_DESIGN_v0.3_DEV.md`（设计母版）、`docs/v0.2/V020_APP_SHELL_SPEC.md` / `V020_DESIGN_SYSTEM_SPEC.md` / `V020_EMPTY_ERROR_OFFLINE_SPEC.md`（当前 UX 规范）、`DECISIONS.md`（ADR 累积）、`docs/ARCHITECTURE.md` / `docs/PLATFORMS.md`
6. 运行契约：`docs/engineering/ERROR_MODEL.md`、`TEST_DATABASE_ISOLATION.md`、`DATABASE_ENVIRONMENT_MODEL.md`、`PRODUCTION_DB_RUNBOOK.md`、`PRODUCTION_DATA_INTEGRITY.md`、`docs/BACKUP_RESTORE_RUNBOOK.md` 等 runbook

## 判定红线

- **不得**把以下内容当作当前状态：v0.5/生产数据线（root 与 docs/release、docs/expansion、docs/governance、docs/status 的 09-16..23 报告）、Wave01/Wave02「NOT STARTED/OPEN」表述、v0.9-R1 母版 `ENGINEERING_OPEN`、WorkBuddy/ZCODE/AGENT_MASTER 一次性接管文档、GOV-01 R1/R2 签署包。
- v0.1.0 系的 19 项 BASELINE-EVIDENCE 是**历史基线证据**（KNOWN_GOOD），不是「当前门禁」——当前门禁以 PROJECT_STATE.md 与 V020_* 报告数字为准。
- 本文件由只读扫描生成；判定依据仅为文件名、首 40 行要点、git 系谱（`git merge-base --is-ancestor v0.5-quality-freeze v0.1.0` = 是；`53c4c03…` ∈ v0.1.0 rev-list = 是；HEAD = `5af2bdb`）。未经逐文件全文核对的地方以「文件自标状态」如实引用。
