# REAL_DATA_FINAL_REPORT.md

> PART B 最终报告（B16）。试点：上海，2026-09-13。
> 数据性质：**真实场所试点数据**（provenance: real_place_claims=10，见 docs/reality_audit/real_pilot_01/provenance_manifest.json）。
> 铁律执行：**AI 未发布任何正式事实** —— 0 条 APPROVED / 0 条 PUBLISHED；33 条 RuleCandidate 全部停在 REVIEW_PENDING 等待人工 Review Gate（B13）。

## 1. Pilot area

上海（第一轮：黄浦区、浦东新区、徐汇区、虹口区、静安区的 10 个场所）。选择依据：法规全文官方可得、政府公告可核验、官方运营方政策丰富、规则形态覆盖 conditional/prohibited/zone 试点/UNKNOWN/来源变更五种形态（详见 REAL_DATA_PILOT_10_REPORT.md §2）。

## 2. Places / Sources / Evidence stats

| 项 | 数值 |
|---|---|
| Places | 10（+15 Zones） |
| Sources（唯一） | 11：official_operator_policy ×4、government_service ×1、statute_or_regulation ×1、external_web_reference ×4、ordinary_user ×1 |
| SourceArtifacts | 19（每条来源记录含 content_hash=sha256(逐字引文)、采集方式、许可标志） |
| EvidenceBundles | 27（original 类；含 place_match_evidence 与 temporal_evidence） |
| 采集方式 | web_reader_fetch ×12（Tier-1 官方页逐字抓取）；search_snippet ×7（逐字片段，页面未直接核验，全部标 Needs Verification） |
| Tier-1 占比 | 55%（6/11） |

证据登记册（逐字引文级）：`docs/reality_audit/real_pilot_evidence.json`；入库台账：`docs/reality_audit/real_pilot_ingest_manifest.json`。

## 3. Rules / Observations / Candidates

| 通道 | 数量 | 终态 |
|---|---|---|
| RuleCandidate | 33（LEGAL 14 + OPERATOR 15 + TEMPORARY 3 + REGULATORY_GUIDANCE 1） | **全部 REVIEW_PENDING**（B13） |
| ObservationCandidate | 3（Manner 社媒 lead、西岸用户经历、烘焙工坊 UNKNOWN-state） | 待人工甄别；永不进入规则发布 |

效果分布：prohibited ×9、conditional ×8（含 zone 级/试点/时间窗）、allowed（服务犬豁免）×9、补充/兜底 ×7。
两个 supersede/时间线样本：港汇恒隆（2026-01-31 effective_to → 2026-02-01 起室内禁止）、星巴克西岸店（2026-08 调整）。

## 4. Approved / Rejected Candidates

**0 / 0。** 第一轮按 B13 全部留人工审核：26 条 Tier-1 direct 候选可直接进入人工比对；7 条引用 snippet 采集来源的候选须先按修复清单核验原文（REAL_DATA_PILOT_10_REPORT.md §7、§9）。

## 5. Schema gaps（引擎实跑发现）

1. **SG-REAL-01**：法定服务动物豁免无法结构化表达 —— `animal_scope=dog` 的 LEGAL 禁令捕获工作犬，LEGAL 层内 service_dog-allowed 不能抑制同层禁止，且同层 allowed-vs-prohibited 不标记 POTENTIAL_CONFLICT。运营方有服务犬条款的场所（太古里/迪士尼/上图）结果正确；无条款场所（烘焙工坊/港汇/西岸）导盲犬被解析为 prohibited，与条例23条但书意图相悖。提案：`Rule.exempt_animal_scopes` 显式豁免字段（方案 A，可审计不猜测）。
2. **SG-REAL-02**：`pet_stroller_rental` 等共处属性无结构化归属（引擎已记 schema-gap 候选）。提案：coexistence 枚举化或并入 amenities。
3. **Artifact 去重**：同一法规页按场所上下文产生 7 条 artifact —— 提案按 content_hash+source 归一。
4. 已顺带实施：provenance `_manifest` 显式声明、规则 `note` 字段入合法键集（+2 单测，全量 209 通过）。

## 6. DataLicense

- redistribution_allowed=false：太古里、迪士尼、星巴克、解放日报、OTA、CBNData、西岸报道（版权谨慎，仅内部核验用）。
- display/storage=false（lead-only）：社交平台用户帖 —— 仅存发现线索引用，不存原文、不展示、不发布。
- redistribution_allowed=true：政府公告、法规原文（公务传播）、上图读者须知。
- 无任何来源绕过 robots/条款/登录/验证码；403 页面未强行抓取。

## 7. Resolver correctness

Reality Audit 27 探针查询：26 个返回明确的 allowed/prohibited/conditional 且与来源转录一致（人工比对通过）；1 个按设计返回 UNKNOWN（烘焙工坊 cat，applicable=[]，不猜测）✅。
已知偏差：SG-REAL-01 场景下导盲犬在 LEGAL-only 场所解析为 prohibited（引擎如实执行现行 schema，缺陷在 schema 表达力，已提案修复；未中途改代码"迎合"预期结果）。

## 8. Boundary matching / SourceMonitor

- 本批未录入 BoundaryProfile（边界几何需要现场测绘级数据，试点以 POINT + Zone 语义表达）；boundary-match 端点已在 PART A 建立 perf 基线，待扩量阶段启用。
- SourceMonitor：SSRF 防护（含私网拦截、重定向复验、2MB 上限）在 PART A 已测；本批未配置周期 monitor（下一步为 7 条待核验来源配置 monitor，实现政策变更的自动发现）。

## 9. Failures（如实记录）

1. WebFetch 抓取 taikooliqiantan.com 403、迪士尼页面 JS 渲染抓不全 → 换 web_reader 成功（太古里/迪士尼/上图/条例/黄浦公告均拿到逐字全文）。
2. 西岸梦中心调整的原始报道 URL 未能定位 → source_url 置空并标注"待归档"（不编造 URL）。
3. 费尔蒙官网政策页未直接核验 → OTA 聚合来源保持 Needs Verification。
4. Manner 官方渠道无公开宠物政策 → 门店级条款只能停在媒体转述 + 社媒 lead。
5. 7/33 候选证据直接核验占比不足 → **B15 触发，扩量停止**（这是本试点最重要的系统性发现：瓶颈在采集核验能力，不在数据模型）。

## 10. Proposed schema changes

见 §5（exempt_animal_scopes / coexistence 枚举化 / artifact 去重）。均未实施 —— 按"AI 不做最终规则裁判"，schema 变更留给人工评审决策。

## 11. 是否可扩 100–500 Place？

**结论：现在不能；修复后可分阶段扩。**
- 数据模型与证据链设计已被 10 个真实场所验证：10/10 可表达、0 attribution 错误、全链路可审计 → **架构层面支持规模化**。
- 阻塞在**采集核验产能**：Tier-2 来源直接核验率 78.8% < 90%。扩到 100–500 场所前必须：
  1. 落实人工 Review Gate 第一轮（26 条 Tier-1 候选先行）；
  2. 完成 §9.1 的 5 项来源核验，Evidence Completeness ≥90%；
  3. 评审并实施 SG-REAL-01 schema 修复（规模化后服务犬错判会被放大）；
  4. 为 Tier-1 来源配置 SourceMonitor（政策变更自动发现，替代新闻滞后通道）。
- 建议路径：30–50 场所（修复后，产出 REALITY_AUDIT_REAL_01.md）→ 复核 KPI → 100–500。

## 12. 产物索引

REAL_DATA_PILOT_10_REPORT.md（试点主报告）· REAL_DATA_PILOT_STATE.md（状态台账）·
docs/reality_audit/real_pilot_{evidence,samples}.json · docs/reality_audit/real_pilot_01/（引擎三件套）·
docs/reality_audit/real_pilot_ingest_manifest.json · scripts/real_pilot_ingest.py ·
ENGINEERING_QUALITY_FINAL_REPORT.md（PART A 门禁，PART B 前置）。
