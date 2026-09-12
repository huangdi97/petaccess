# REAL_DATA_PILOT_10_REPORT.md

> PART B（EVIDENCE-FIRST REAL DATA AUTOMOUS PILOT）第一批 10 个真实场所试点报告。
> 采集日期：2026-09-13。前置：PART A Quality Gate 全 PASS（commit 47fcb32，tag v0.5-quality-freeze）。
> **AI 在本试点中只做发现、转录与结构化，没有发布任何正式事实；全部 33 条 RuleCandidate 停在 REVIEW_PENDING（B13）。**

## 1. 结论（TL;DR）

- 10/10 真实场所完成 全链路入库：Source → SourceArtifact → EvidenceBundle → RuleCandidate/ObservationCandidate，全部证据可溯源（URL/引文/hash/place_match）。
- Reality Audit 实跑：**10/10 可表达**；1 个 schema-gap 候选 + 2 个引擎表达力发现（如实记录，不中途改裁决器）。
- B8 组成要求 **全部满足**（3 咖啡/餐饮、2 商场、2 公园、1 酒店、1 景区、1 其他；5 种 source_type；多 Zone；conditional/prohibited/unknown/Rule/Observation 全覆盖）。
- **B15 停止条件触发：Evidence incomplete 21.2% > 10% —— 30–50 扩量立即停止，先修系统**（详见 §7）。这本身是试点的正确产出：问题在采集能力（403/JS 页面），不在数据模型。
- 前滩太古里、上海迪士尼、上海图书馆、上海市养犬管理条例、黄浦区政府公告 五份 **Tier-1 官方全文** 已逐字抓取入库；解放日报/新华网/CBNData/OTA 等 Tier-2 来源按 **Needs Verification / lead-only** 处理。

## 2. 试点区域与选择依据（B2）

**试点区域：上海市**（第一轮以黄浦区/浦东新区/徐汇区为主）。

依据：
1. **法规公开且数字化程度高**：《上海市养犬管理条例》全文在上海公安网官方转载页可逐字引用（LEGAL 层可落地）。
2. **政府公告可核验**：2025-09 公园宠物试点有黄浦区政府官网公告（TEMPORARY_POLICY 场景稀缺样本）。
3. **官方运营方政策丰富**：太古里/迪士尼/上图/星巴克均有官网政策页（DIRECT 来源）。
4. **规则形态多样**：同一城市同时存在 conditional（太古里户外）、prohibited（迪士尼/上图/港汇室内）、zone 级试点（广场公园 H6）、UNKNOWN（烘焙工坊门店级）、来源变更（2026-02 商场宠物政策调整、2026-08 星巴克宠物专区调整）——恰好覆盖 Place→Zone→AccessRule 与 supersede 场景。
5. 遵守 Demo 默认虚构场所红线：本批是 **试点数据**，全部走证据链并留待人工审核，与 demo 数据严格分离（provenance manifest 标 real_place_claims=10）。

## 3. 方法与红线合规（B3–B7）

- **中性搜索**：查询词同时覆盖 允许/禁止/条件/未知（如“宠物 政策”“禁止 携带 宠物”“养犬管理条例 公园 试点”“宠物友好”），未只搜“宠物友好”。
- **Tier 优先**：优先官方来源（运营方官网、政府站点、法规原文）；新闻/社媒仅作 Lead Discovery。
- **Rule vs Observation 分流**：来源表达“店方规定/官方公告/法规” → RuleCandidate；表达“我看到/用户经历” → ObservationCandidate（Manner 社媒帖、西岸事件用户帖）。
- **不绕过访问控制**：未登录任何账号、未绕过验证码/权限；403 页面（WebFetch 被拒）未强行抓取，改用搜索结果中已展示的逐字片段并如实标注 `capture_method=search_snippet`。
- **许可与隐私**：官方政策页 redistribution=false（版权谨慎）；社媒内容 display=false、storage=false、lead-only；不长期存储位置轨迹（place_match 只记录地址/名称匹配证据）。
- **AI 不做最终裁判**：结构化转录标记 `extraction_method=agent_assisted_extraction_2026_09_13`，置信度为内部字段；发布权 100% 留给人工 Review Gate。

## 4. 十个真实场所

| # | 场所 | 类型 | 核心规则（转录自来源） | 规则层 | 来源质量 |
|---|---|---|---|---|---|
| 1 | 前滩太古里 | mall | 户外开放区域 conditional（≥8周/疫苗/登记/牵引/限1只）；室内未经同意 prohibited | OPERATOR + LEGAL(商场) | Tier-1 官网全文（direct） |
| 2 | 上海迪士尼乐园 | scenic_area | 全园宠物 prohibited（导盲犬除外）；导盲犬须牵引、部分项目可能不允许 | OPERATOR + LEGAL | Tier-1 官网全文（direct） |
| 3 | 广场公园（黄浦段） | park | H6 试点区 conditional（2025-09-01 起，TEMPORARY_POLICY，试点期未定）；其余区域 prohibited | TEMPORARY/OPERATOR | Tier-1 政府公告（direct） |
| 4 | 大吉路公园 | park | 全园试点 conditional（同上公告） | TEMPORARY | Tier-1 政府公告（direct） |
| 5 | 港汇恒隆广场 | mall | 2026-02 起室内 prohibited、户外保留（运营方规定经媒体报道） | OPERATOR + LEGAL | Tier-2 新闻（snippet，**Needs Verification**） |
| 6 | 上海图书馆东馆 | library | “请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆” | OPERATOR + LEGAL(图书馆) | Tier-1 官网全文（direct） |
| 7 | 和平饭店（费尔蒙） | hotel | 普通宠物 prohibited、服务动物 conditional（OTA 聚合） | OPERATOR + LEGAL(宾馆) | Tier-3 OTA（snippet，**Needs Verification**） |
| 8 | 星巴克臻选上海烘焙工坊 | cafe | 门店级政策未公开 → **UNKNOWN ≠ 允许/禁止**；LEGAL 层禁犬（餐饮场所） | LEGAL（门店无规则） | Tier-1 品牌页（direct，仅品牌层） |
| 9 | Manner咖啡（凯德虹口店） | cafe | 户外宠物区 conditional（媒体报道“首家宠物友好店”） | OPERATOR（待核验） | Tier-2 新闻（snippet）+ 社媒 lead |
| 10 | 星巴克（徐汇西岸梦中心店） | cafe | 2026-08 调整后室内 prohibited、户外宠物区 conditional | OPERATOR（待核验） | Tier-2 新闻（snippet）+ 社媒 lead |

## 5. 证据链与来源台账

**入库计数（DB 实测）**：10 Places · 15 Zones · 11 unique Sources（19 条来源记录按场所上下文建档）· 19 SourceArtifacts · 27 EvidenceBundles · **33 RuleCandidates（全部 REVIEW_PENDING）** · 3 ObservationCandidates · **0 Published**。

**来源构成（11 个唯一来源）**：

| source_type | 数量 | 来源 |
|---|---|---|
| official_operator_policy | 4 | 太古里官网、迪士尼游客须知、上图读者须知、星巴克中国官网新闻 |
| government_service | 1 | 黄浦区政府官网公告 |
| statute_or_regulation | 1 | 《上海市养犬管理条例》第22/23/43/44条（上海公安网官方转载） |
| external_web_reference | 4 | 解放日报、OTA 聚合、CBNData、新闻媒体（西岸调整，URL 待归档） |
| ordinary_user | 1 | 社交平台用户帖（lead-only，不展示不存储） |

**Tier-1（官方/政府/法规）占比：6/11 ≈ 55%**。

**采集方式分布（19 条来源记录）**：
- `web_reader_fetch`（页面直接抓取，引文逐字）：12 条 —— 太古里、迪士尼、上图、条例×7 处复用、黄浦公告×2 处复用、星巴克品牌页。
- `search_snippet`（搜索结果逐字片段，页面未直接抓取）：7 条 —— 解放日报、OTA、CBNData、西岸报道、用户帖。

**内容指纹**：每个 artifact 记录 `content_hash = sha256(逐字引文)`；引文在 evidence register（`docs/reality_audit/real_pilot_evidence.json`）中逐字保存，报告与 DB 三方可对照。

## 6. Reality Audit 实跑结果（B9）

命令：`uv run python -m app.tools.reality_audit docs/reality_audit/real_pilot_samples.json --out docs/reality_audit/real_pilot_01/`

- **可表达性：10/10 expressible** —— 真实规则（分层/分区/条件/时间窗/例外）全部能用现有 schema 表达。
- **Resolver 结果**（27 个探针查询）：
  - 太古里：室内狗 prohibited（LEGAL+OPERATOR 同向）/ 户外 conditional / 导盲犬 allowed ✓
  - 迪士尼：宠物 prohibited / 导盲犬 conditional（牵引）✓
  - 广场公园：H6 conditional（TEMPORARY_POLICY 生效中）/ 其余 prohibited / 猫 conditional ✓
  - 港汇：室内 prohibited（时间线：旧 conditional 规则 effective_to 2026-01-31，新 prohibited 自 2026-02-01）✓ supersede 建模可用
  - 上图：猫狗 prohibited / 导盲犬 allowed ✓
  - **烘焙工坊 cat 查询 → UNKNOWN（applicable=[]，不猜测）** ✓ —— B12“UNKNOWN≠允许/禁止”的真实样本
- **真实数据暴露的引擎发现（如实记录，未中途改代码裁决）**：
  1. **SG-REAL-01（表达力缺口）**：`animal_scope=dog` 的 LEGAL 禁令会捕获工作犬，而 LEGAL 层内 service_dog-allowed 规则**不能抑制**同层 dog-prohibited（v05_resolver 的同层冲突只在“下层 vs 法定”时标记）。结果：在**运营方未单独声明服务犬政策**的场所（烘焙工坊/港汇/西岸），导盲犬查询被解析为 prohibited —— 与条例23条但书（“盲人携带导盲犬的，不受本条规定的限制”）意图相悖，且该冲突未标记 POTENTIAL_CONFLICT。已在太古里/迪士尼/上图通过补充 OPERATOR 层服务犬规则绕开（这正是现行 schema 的正确用法），但**法定豁免本身需要 schema 支持**。→ 提案见 §8。
  2. **SG-REAL-02（字段缺口）**：`pet_stroller_rental`（太古里宠物推车服务）等共处属性无结构化归属 → 引擎已记为 schema-gap 候选。
  3. 引擎增强（本次实跑中完成并测试）：`_RULE_KEYS` 补 `note` 字段；`_manifest` 显式声明真实数据性质（provenance manifest 从硬编码 synthetic 改为可如实标注 real_place_claims=10）；+2 单测，全量 209 测试通过。

## 7. B15 停止条件评估 —— **扩量停止**

| 阈值 | 实测 | 判定 |
|---|---|---|
| Schema Gap > 20% | 1/10 样本存在 gap 候选 = 10% | ✅ 未触发（另 2 项引擎发现记入提案） |
| Place attribution error > 5% | 0/33（全部按名称+地址匹配，无错配） | ✅ 未触发 |
| **Evidence incomplete > 10%** | **7/33 = 21.2%**（引用 `search_snippet` 采集来源的规则候选：gh×2、fp×2、mn×1、xm×2） | ❌ **触发 → 停止扩量** |
| AI major extraction error > 5% | 人工复核前无法自证清零；引文逐字、置信度标注诚实 | ⏳ 留待 Review Gate |
| unauthorized source usage | 0（无登录绕过/robots 违规/半私密内容抓取） | ✅ 未触发 |
| Place merge/duplicate instability | 0（自有 UUID，外部 POI 仅 ExternalRef，未使用） | ✅ 未触发 |

**21.2% 的构成与修复路径**（先修系统，再扩量）：
1. 解放日报/新华网（港汇）：官网页本会话抓取失败（反爬）→ 修复=人工浏览器核验或补抓原文页，升级 `capture_method`。
2. OTA（和平饭店）：费尔蒙官网政策页未定位 → 修复=直接核验 fairmont.com。
3. CBNData（Manner）：Manner 官方无公开宠物政策 → 修复=门店现场/客服核验，核验前保持 Needs Verification。
4. 西岸调整报道：**报道 URL 待归档**（当前 source_url 为空）→ 修复=定位原报道并补 hash。
5. 用户帖（社媒）：**按设计保持 lead-only**，不计入可发布证据，核验路径=现场观察（Observation 通道）。

**判定：Pilot Gate = NOT PASS（不满足扩量条件）**。第一批 10 场所的数据本身合格（组成、链路、可表达性全达标），阻塞点集中在 Tier-2 来源的**直接核验能力**，属采集流程问题，按 B15“先修系统”。

## 8. Schema 变更提案（供评审，未实施）

1. **法定服务动物豁免的结构化表达**（SG-REAL-01）：候选方案 A：`Rule.exempt_animal_scopes`（禁令规则声明豁免范围）；B：引入 `AnimalScope.WORKING_DOG` 并允许 LEGAL 规则以“非服务犬”为范围；C：LEGAL 层内 service_dog-allowed 自动抑制同层 dog-prohibited（改 resolver 语义，影响面最大）。建议 A——显式、可审计、不猜。
2. **共处属性结构化**（SG-REAL-02）：`coexistence_policies` 增加 `pet_stroller_rental`/`pet_amenity` 等枚举，或将自由属性迁入 `amenities`。
3. **来源去重/归一**：同一 statute 页按场所建档产生 7 条 artifact 副本 —— 提案：artifact 按 content_hash+source 去重，候选通过 bundle 引用共享。
4. **`_manifest`/`note` 引擎增强**：已实施并通过测试（本次试点顺带落地，见 §6.3）。

## 9. 人工审核队列（Review Gate 待办）

33 条 REVIEW_PENDING 候选按核验优先级：
1. **可直接 APPROVED**（Tier-1 direct 全文，人工比对引文即可）：26 条。
2. **须先核验来源原文**：7 条（§7 清单）——核验通过后升级 capture_method 并附官方页 hash，再进 APPROVED。
3. **须补充 URL 归档**：西岸调整报道（1 条来源记录）。
4. 3 条 ObservationCandidate：仅作现场核验线索，**永不进入规则发布**。

## 10. KPI（B14）

| KPI | 值 |
|---|---|
| Places discovered | 10（上海） |
| Answerable Place Rate（audit 探针非 UNKNOWN） | 26/27 = 96.3% |
| RuleCandidate count | 33 |
| ObservationCandidate count | 3 |
| Evidence Completeness（直接抓取占比） | 26/33 = 78.8%（**低于 90% 门槛 → B15 停扩**） |
| Official/operator source ratio | 6/11 = 54.5%（Tier-1） |
| Candidate approval rate | 0%（B13：第一轮全部人工） |
| Attribution error | 0/33 |
| Schema gap rate | 1/10 样本 = 10%（+2 引擎提案） |
| Stale rate | 0（全部当日核验；STALE_DAYS=180） |
| Conflict rate | 0 POTENTIAL_CONFLICT（LEGAL 同层冲突不可见性已记 SG-REAL-01） |
| Source change latency | 港汇 2026-02 调整经 5 月报道捕获 —— 延迟约 3 个月（新闻通道固有滞后，记入经验） |

## 11. 产物清单

| 文件 | 内容 |
|---|---|
| `docs/reality_audit/real_pilot_evidence.json` | 证据登记册：逐字引文、URL、采集方式、许可标志、置信度 |
| `docs/reality_audit/real_pilot_samples.json` | Reality Audit 输入（10 样本/36 规则/27 查询，`_manifest` 如实声明） |
| `docs/reality_audit/real_pilot_01/` | 引擎输出三件套（报告/SCHEMA_GAPS/provenance manifest，real_place_claims=10） |
| `docs/reality_audit/real_pilot_ingest_manifest.json` | 入库 ID 台账（幂等重放用） |
| `scripts/real_pilot_ingest.py` | 全链路入库脚本（不发布；REVIEW_PENDING 止步） |
| DB | 10 Place / 15 Zone / 33 候选待人工审核（audit_log 全程留痕） |

## 12. 下一步

1. **先修系统（B15）**：完成 §7 五项来源核验，把 Evidence Completeness 提到 ≥90%。
2. 人工 Review Gate 跑第一批 26 条 Tier-1 候选，产出 APPROVED/REJECTED 决策与修订记录。
3. 评审 §8 schema 提案（尤其 SG-REAL-01）。
4. 以上完成后再扩量 30–50 场所，产出 `REALITY_AUDIT_REAL_01.md`；扩量结论见 `REAL_DATA_FINAL_REPORT.md`。
