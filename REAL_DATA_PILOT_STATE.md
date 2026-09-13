# REAL_DATA_PILOT_STATE.md

> PART B（EVIDENCE-FIRST REAL DATA AUTONOMOUS PILOT）实时状态。
> 前置条件：PART A Quality Gate 全 PASS（见 `ENGINEERING_QUALITY_ACCEPTANCE.md`，commit 47fcb32，tag v0.5-quality-freeze）。

## 状态

| 项 | 值 |
|---|---|
| PART A 状态 | **PASS**（2026-09-13，A01–A28 全 PASS） |
| PART B 状态 | **R2_GATE_PASS（有条件）— PILOT-REVIEW-AND-SCHEMA-FIX-01 完成；允许 30–50 扩量（前置见 R2 报告 §11）** |
| Pilot 区域 | 上海（黄浦/浦东/徐汇为主；选择依据见 REAL_DATA_PILOT_10_REPORT.md §2） |
| 已建真实 Place 数 | **10 / 10** |
| real_place_claims（provenance manifest） | **10**（docs/reality_audit/real_pilot_01/provenance_manifest.json） |
| 发布状态 | **0 条发布** —— 33 条 RuleCandidate 全部 REVIEW_PENDING（B13 第一轮全人工） |

## Pilot 组成要求（B8）—— 全部满足

3+ 餐饮/咖啡（星巴克烘焙工坊、Manner凯德虹口、星巴克西岸梦中心）· 2 商场（太古里、港汇）·
2 公园（广场公园黄浦段、大吉路）· 1 酒店（和平饭店）· 1 景区（迪士尼）· 1 其他（上图东馆）；
5 种 source_type · 多 Zone（≥2）· conditional ×8 · prohibited ×9 · unknown（烘焙工坊 cat 查询）·
RuleCandidate 33 · ObservationCandidate 3 · 全部候选有完整证据链（bundle→artifact→hash）。

## 候选台账（10 场所汇总；逐条引文见 real_pilot_evidence.json）

| # | Place | 类型 | Zone | 来源(Tier/type) | 通道 | 候选状态 | 证据完整度 |
|---|---|---|---|---|---|---|---|
| 1 | 前滩太古里 | mall | 户外开放区/室内 | T1/official_operator + 法规 | Rule ×5 | REVIEW_PENDING | direct |
| 2 | 上海迪士尼乐园 | scenic_area | 全园 | T1/official_operator + 法规 | Rule ×4 | REVIEW_PENDING | direct |
| 3 | 广场公园（黄浦段） | park | H6区/其余 | T1/government_service | Rule ×2 | REVIEW_PENDING | direct |
| 4 | 大吉路公园 | park | 全园 | T1/government_service | Rule ×1 | REVIEW_PENDING | direct |
| 5 | 港汇恒隆广场 | mall | 室内/户外街区 | T2/新闻(解放日报) + 法规 | Rule ×4 | REVIEW_PENDING | **snippet ×2（需核验）** |
| 6 | 上海图书馆东馆 | library | 全馆 | T1/official_operator + 法规 | Rule ×4 | REVIEW_PENDING | direct |
| 7 | 和平饭店（费尔蒙） | hotel | 全酒店 | T3/OTA聚合 + 法规 | Rule ×4 | REVIEW_PENDING | **snippet ×2（需核验）** |
| 8 | 星巴克臻选上海烘焙工坊 | cafe | 全店 | T1/品牌页 + 法规 | Rule ×2 + **Observation ×1（UNKNOWN 演示）** | REVIEW_PENDING | direct（品牌层） |
| 9 | Manner咖啡（凯德虹口店） | cafe | 户外宠物区/室内 | T2/新闻(CBNData) + 社媒lead + 法规 | Rule ×3 + Observation ×1 | REVIEW_PENDING | **snippet ×1（需核验）** |
| 10 | 星巴克（徐汇西岸梦中心店） | cafe | 室内/户外宠物区 | T2/新闻(待归档URL) + 社媒lead + 法规 | Rule ×4 + Observation ×1 | REVIEW_PENDING | **snippet ×2（需核验）** |

## KPI（B14，2026-09-13 实测）

| KPI | 值 |
|---|---|
| Places discovered | 10 |
| Answerable Place Rate | 96.3%（audit 探针 26/27 非 UNKNOWN） |
| RuleCandidate count | 33 |
| ObservationCandidate count | 3 |
| Evidence Completeness | **78.8%（26/33 direct）→ 低于 90%，B15 停扩** |
| Official/operator source ratio | 54.5%（6/11 Tier-1） |
| Candidate approval rate | 0%（无人工审核，第一轮全部留待 Review Gate） |
| Attribution error | 0/33 |
| Schema gap rate | 10%（1/10 样本；另 2 项引擎表达力发现记入提案） |
| Stale rate | 0% |
| Conflict rate | 0 POTENTIAL_CONFLICT（LEGAL 同层冲突不可见性 → SG-REAL-01 提案） |
| Source change latency | ~3 个月（港汇 2026-02 调整经新闻捕获；新闻通道固有滞后） |

## 停止条件（B15，任一触发立即停）

Schema Gap > 20% ✅(10%) · attribution error > 5% ✅(0%) · **evidence incomplete > 10% ❌(21.2% 触发)** ·
AI major extraction error > 5% ⏳(待人工复核) · unauthorized source usage ✅(0) · merge/duplicate instability ✅(0)。

**R2 修复结果（2026-09-13，详见 REAL_DATA_PILOT_10_R2_REPORT.md）**：
7 条 snippet 候选 → 5 修复（新华网/费尔蒙官网/潮新闻直抓）、1 归因错误（Manner，建议人工 REJECT）、
1 未证实（港汇户外）；**direct-or-strong 93.9%**（≥90% 解锁）；SG-REAL-01 已修复（RuleException，ADR-020），
服务犬解析 7/7 正确；Pre-Publish Validation 六检上线；REAL-WORLD-REGRESSION-FIXTURES 入 CI；
REALITY-AUDIT-10-R2：10/10 可表达、0 resolver 错误。全量测试 238/238。
**扩量前置**：人工 Review Gate 处置 33 条 + 2 条残留 snippet 核验。

## 关键红线执行情况

- AI 全程未发布任何正式事实；0 条 APPROVED/PUBLISHED。
- 无登录/验证码/权限绕过；403 页面未强行抓取（改用搜索展示片段并如实标注 capture_method）。
- 社媒内容 lead-only：display=false、storage=false。
- 《上海市养犬管理条例》第23条作为 LEGAL 层入库，与宠物友好运营政策并存的张力如实建模（烘焙工坊案例）。
- provenance manifest 从 synthetic 硬编码改为 `_manifest` 如实声明（引擎增强，+2 单测）。
