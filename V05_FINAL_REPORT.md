# V05_FINAL_REPORT.md

# 宠物准入与公共空间共处规则平台 — v0.5 本地 RC 最终报告

日期：2026-09-13
性质声明：本报告只记录**实际执行过**的验证；未真实验证的项单独列出，绝不写成通过。

---

## 1. Takeover 与工作划分

| 项 | 值 |
|---|---|
| 接管时 HEAD | `88b4c700c4a131513f2297cafbbe37f981c9c8af`（WorkBuddy/前序 ZCode 会话产物） |
| 接管时工作树 | 1 个已修改文件 + 3 个未跟踪文件；补丁快照已存 `zcode_resume_pre_takeover*.patch` |
| 最终 HEAD | 见 `git log`（本报告随 V33 提交产生） |

### WorkBuddy / 前序会话已完成（本会话未重做，只做基线复跑确认）

- **Track A（RC-HARDENING-01）**：真实 MinIO 媒体链（A1）、TencentMapProvider 适配器
  + 13 contract tests（A2）、AI provider 硬化（A3）、backup/restore 真演练 + runbook（A4）、
  observability（A5）。
- **Track B（V05-DOMAIN-01）**：v0.5 域模型 + v05 API 路由 + rule_layer 回填迁移 + demo seed；
  Admin v0.5 真 API 页面（commit `8cede60`）；H5 边界设置 + 可解释匹配（commit `88b4c70`）。
- **Track C（PILOT-READINESS-01）**：E2E-A/B/C 修复并 PASS；evidence-first 链
  （source_artifact / evidence_bundle / observation_candidate，commit `0b7eabc`、`c329c56`）；
  collector 抽象与许可闸门（服务级）。
- 接管前两个未提交修改（`db.flush()` 审计修复、`trust_env=False` SSRF 加固）经复核**正确并保留**。

### ZCode 本会话新完成（4 个 Gate + 最终收口）

| Gate | 内容 | 提交 |
|---|---|---|
| V36 | `MIGRATION_V05.md` + 迁移 down→up→down→up 双循环真实验证（6 revision/向）+ revision 7 单循环 | `ac7c541` |
| V34 | **E2E-D 外部公开 lead 全链**：修复真实缺口 —— `candidate_service.publish()` 此前未接线 lead-only 发布闸门（守卫只存在于服务级单测）。新增迁移 `c81e02ba6d45`（`rule_candidate.evidence_bundle_id`，RESTRICT FK），rule 候选现在引用其 EvidenceBundle；发布边界强制 `assert_publishable`（lead-only 无再分发许可 → `lead_only_source_not_publishable`；规则证据必须可追溯）。观察通道 PUBLISHED 迁移接线同一闸门。E2E-D 测试证明：lead → artifact → bundle → 分类双通道 → 复核 → 拒绝发布 → 驳回收口；同一链路补齐许可后**可以**发布（闸门按许可判定，不按平台一刀切） | `35a3e3a` |
| V35 | 对抗性 fixtures：`tests/unit/test_v05_adversarial.py`，**40 个场景类**（代码内注册表可审计）：体型阈值/缺失输入不猜测/封闭包/推车/限只数、分区语义（室内户外/商场/超市楼层/裸规则不治理）、时间窗（周末/夜间/跨夜/未来/过期）、服务犬三向隔离、法定地板/覆盖链/冲突/遗留 NULL、状态机终态与跳转拒绝、边界 UNKNOWN 不当 MATCH 且无评分、Observation 结构性隔离、PetAccessJSON 拒绝坏数据、freshness=复核非失效 | `4d4dcab` |
| V29 | Reality Audit 工具：纯函数引擎 `app/tools/reality_audit.py`（CLI 与 admin API 同代码路径）；CSV/JSON import template；对 6 个合成样本实跑产出 `docs/reality_audit/` 报告三件套（REALITY_AUDIT_REPORT.md / SCHEMA_GAPS.md / provenance_manifest.json）；12 测试 | `2d7e7cb` |
| V33 | 本报告 + 状态文档收口 + 最终全量验证 | （本次提交） |

### 未提交改动的处置

- 接管时的 `ACCEPTANCE_MATRIX_v0.5.md` 修改（V21/V22 → PASS）：复核属实，随 V36 提交入库。
- 本会话每 Gate 小步提交（`zcode: ...`），无巨型 commit。
- 未跟踪的会话文件（`.workbuddy-ai/`、resume 指令、接管报告、补丁快照、playwright-out）
  保留未删除；补丁快照与接管报告是审计记录，建议保留或按需归档。

---

## 2. Migrations

7 个 revision，全 additive（新表/可空列），无破坏性操作：

```
864ffcfc7ccb  initial schema（v0.3 域 + PostGIS/trgm 索引）
2e0155d834eb  media_object（Track A）
4930732f4783  v0.5 域 16 表 + access_rule 增量 6 列
b2a1c7d9e001  rule_layer 回填（确定性映射，幂等，其余 NULL→REVIEW_REQUIRED 不猜）
5cb24fc8e838  evidence-first 三表
4565819baf78  source_monitor.last_excerpt（trgm 索引显式保留）
c81e02ba6d45  rule_candidate.evidence_bundle_id（V34）
```

证据：`alembic downgrade base → upgrade head` 双循环各 6 步干净通过；
revision 7 单独 up→down→up 通过；`alembic current` = head；down/up 后 demo seed 复跑正常。
详见 `MIGRATION_V05.md`。

## 3. EffectiveRuleResolver

解析链 LEGAL → REGULATORY_GUIDANCE → template → place/zone override → event →
EffectiveRuleSet；强制法定地板（mandatory 禁令不可被下层放宽）、特异性遮蔽
（zone > place > template，非 last-write-wins）、event 遮蔽 operator、
allowed-vs-prohibited 同层冲突 → POTENTIAL_CONFLICT（禁止暂时治理）、
遗留 NULL layer → REVIEW_REQUIRED、五层全空 → UNKNOWN。
输出 applicable/suppressed/conflicts/explanation_steps/compliance_state/obligations。
Observation 数据在结构上不进入 resolver（签名无观察参数，测试锁定）。

## 4. Evidence-first acquisition

- `SourceCollector` ×7（官方网页/品牌官网/搜索发现/社交线索/用户链接/电话核验/现场证据），
  其中 4 个 v0.5 可无凭证运行；COLLECTORS 注册表 + contract 测试。
- `SourceArtifact → EvidenceBundle → classify → Candidate`：派生证据强制引用
  `derived_from_bundle_id`；规则类证据发布须有原文片段或哈希。
- RuleCandidate / ObservationCandidate 独立表 + 独立状态机；观察候选走完发布全流程后
  effective-rules 逐字节不变、AccessRule 计数为 0（API 级测试）。
- **发布闸门（本会话接线到 API）**：lead-only 平台（社交/搜索/用户链接）无再分发许可时，
  规则候选发布与观察候选 PUBLISHED 均返回 400 `lead_only_source_not_publishable`；
  许可补齐后同链路可发布（E2E-D 对照组）。

## 5. MinIO / 媒体管线

upload → MIME/扩展名/大小/图片解码校验 → 随机 object key → MinIO → media_object 元数据
（sha256/去重/隐私级/TTL）→ OCR 任务（mock）→ 审核队列 → 删除/TTL → 审计。
真实 MinIO 集成测试持续 PASS（V01）。

## 6. SourceMonitor / Freshness

- monitor check → unchanged / changed（→ artifact + bundle + RuleCandidate + 审计，
  previous_hash≠observed_hash）/ failed；SSRF 防护（协议/私网/大小/超时）；
  E2E-C 全链含 watch 通知（Redis mock sink，in-process sweep，幂等）。
- FreshnessPolicy：`review_due ≠ invalid`，过期只提示需要复核；answerability stale
  状态不反转规则结论（对抗 fixture H39 锁定）。

## 7. Coexistence / Boundary

- CoexistencePolicy 十项首批属性一等语义（place/zone/attribute/value + source）；
  Rule / Observation / BoundaryPreference 三者永久分离。
- BoundaryMatcher 只输出 MATCH / CONFLICT / UNKNOWN + 逐项理由；无综合分/百分比
  （属性级测试锁定）；UNKNOWN 永不当 MATCH。
- H5：Boundary Settings + Explainable Match（派生步骤展示）+ 2 条 Playwright 旅程。

## 8. Admin / H5

- Admin v0.5：8 新视图绑定真端点 + 9 个分页读端点（candidates / monitors / evidence /
  observation-candidates / organizations / templates / bindings / amenities / entrances /
  access-paths / event-policies / data-licenses / coexistence 等）；build 绿。
- H5 v0.5：场所详情五问 + 边界设置 + 可解释匹配；build 绿；Playwright 7/7。
- 本会话补充：候选序列化输出 `evidence_bundle_id`（Admin 可见证据链引用）；
  Reality Audit 端点（审计员可在后台直接跑审计）。

## 9. PetAccessJSON / Answerability

- PetAccessJSON v0.1 dump/load：非法 rule_layer/effect 拒绝出口（对抗 fixture H38）。
- Answerability 内部矩阵（entry/indoor/leash/…/source/freshness），三态
  answerable/unknown/stale，是数据质量工具不是商家评分。

## 10. 测试证据（最终全量，2026-09-13，真实命令）

| 命令 | 结果 |
|---|---|
| `uv run pytest -q`（仓库根，全量） | **184 passed**（含 evaluator、resolver、evidence、boundary、track_b、properties、E2E-A/B/C/D、reality audit、媒体/MinIO、Tencent/AI contract、API/权限/审计） |
| `./node_modules/.bin/playwright test` | **7 passed**（5 v0.3 旅程 + 2 v0.5 边界/可解释匹配） |
| `bash scripts/lint.sh` | All checks passed，103 files formatted |
| `uv run mypy services/api/app` | Success，72 source files |
| `pnpm --filter @petaccess/admin build` | ✓ built |
| `VITE_API_BASE=… pnpm --filter @petaccess/client-h5 build` | ✓ built |
| `alembic downgrade base / upgrade head ×2` | 6 revision/向 ×2 干净 + revision 7 单循环 |
| PostGIS / Redis / Celery / MinIO | 3.5 · PONG · 1 node online · 媒体链集成测试 PASS |
| `python -m app.db.seed --demo` | 4 places / 15 zones / 8 sources（FK 安全重置清单含证据表） |

## 11. Live provider status（外部凭证，BLOCKED_EXTERNAL）

| 项 | 状态 | Blocker |
|---|---|---|
| 腾讯地图 live smoke | 适配器 + 13 contract tests PASS；真实底图未验证 | B-04 |
| 真实 AI vision/OCR live smoke | Mock + 契约测试 PASS；真实模型未验证 | B-05 |
| uni-app x 五端编译 | 源码工程就绪；H5 行为已由 client-h5 真跑覆盖 | B-01 |
| 微信/移动端上架 | 需 AppID/签名/账号 | B-02/B-03 |
| OAuth/短信、生产部署 | 未实现/未部署 | B-06/B-07 |

以上**只阻塞对应 live smoke**，不阻塞本地代码、fixture、contract test（均已真实完成）。

## 12. Pilot readiness

| 链路 | 状态 |
|---|---|
| E2E-A 现场规则牌（upload→MinIO→OCR→candidate→approve→rule→client） | **PASS** |
| E2E-B 管理方（verified operator→template→binding/override→resolver→client） | **PASS** |
| E2E-C 来源监控（hash change→evidence→candidate→supersede→watch） | **PASS** |
| E2E-D 外部公开 lead（artifact→bundle→分类→复核→**不得直接发布**；许可后可发布） | **PASS** |

试点前剩余（非 Gate、非本地可完成）：
1. 真实 30–50 Place 样本采集（20 餐饮/5 商场/5 公园/5 其他 + 属地法规）——需合法素材与
   现场核验人力，Reality Audit 工具与 import template 已就绪，导入即出报告；
   **无合法素材不得伪造**（provenance manifest 强制 `real_place_claims: 0` 直至有真实来源）。
2. SCHEMA_GAPS 已记录的真实候选缺口：`use_pet_elevator` 等条件类型仅 note-only
   （路径语义在 Entrance/AccessPath 实体）；`pet_swimming_pool` 类共处属性无结构化归宿；
   真实样本导入后按同一流程继续扩表。

## 13. 状态文档收口

- `ACCEPTANCE_MATRIX_v0.5.md`：V29/V33/V34/V35/V36 → PASS；V30–V32 → BLOCKED_EXTERNAL。
- `PROJECT_STATE_V05.md`：已更新至本报告结论。
- `BLOCKERS.md`：B-01…B-07 无变化（全部为真实外部项）。
- `DECISIONS.md`：无架构级变更，无需新 ADR（本会话的发布闸门接线是既有
  ADR-004/006 与 brief §5/§10 的实现收口，不是新决策）。

## 14. 结论

v0.5 本地 RC 的全部本地可完成 Gate（V00–V29、V33–V44 中除三项外部阻塞外的全部）均已
**以真实命令与输出验证为 PASS**。平台在数据生产四链路（现场/管理方/监控/外部线索）上
具备试点就绪能力，产品红线（Observation≠Rule、UNKNOWN 不猜测、服务犬隔离、自有 UUID、
许可闸门、无评分/榜单/评论区、demo 全虚构）在单元、属性、集成、E2E 四层测试中持续锁定。
剩余工作全部依赖外部凭证或合法真实素材（§11/§12）。
