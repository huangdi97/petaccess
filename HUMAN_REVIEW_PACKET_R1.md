# HUMAN_REVIEW_PACKET_R1.md

> GOV-01 支撑材料 · 33 条真实 RuleCandidate 的**人工签署包**（按风险排序）
> 数据来源：`docs/reality_audit/review_decisions_r1.json`（机器登记表）+ 数据库证据包
> 配套：`HUMAN_REVIEW_DECISIONS_R1.json`（待填模板）、`HUMAN_REVIEW_QUICK_TABLE_R1.md`（速填表）

## 0. 纪律（不可协商）

1. **AI 不做最终裁决**（ADR-005 / Master Goal §0.9）。本包只提供事实与建议。
2. 所有 `final_decision` / `reviewer` / `reviewed_at` **保持空白**，由具名人类评审员填写。
3. 未获签署，任何候选不得 APPROVED，更不得 Publish（`publish_reviewed_r1.py` 硬门禁）。
4. 弱证据（`search_snippet` / `social_lead`）**不得 APPROVED**（ADR-021 + Pre-Publish Validation）。
5. LEGAL 候选的 `mandatory_level` 由 layer 确定性映射（ADR-023），可逐行覆盖；留空将被拒绝发布。
6. 本包**不执行发布**。

## 1. 摘要

| 风险分组 | 含义 | 条数 |
|---|---|---|
| **Group 1** | REJECT 推荐（错归因实锤） | **1** |
| **Group 2** | HOLD 推荐（证据未核验 / 需裁定） | **3** |
| **Group 3** | CONFLICT / APPROVE_WITH_NOTE（须额外确认） | **16** |
| **Group 4** | LOW-RISK APPROVE（无冲突、证据可追溯） | **13** |
| **合计** | | **33** |

## 2. 特别标记索引

| 标记 | 条数 | 候选（`rule_id`） |
|---|---|---|
| 🔴 **Manner 错归因 → REJECT 推荐** | 1 | `mn-outdoor-media` |
| 🟠 **弱 search-snippet** | 2 | `mn-outdoor-media`、`gh-outdoor-keep` |
| 🟠→🟢 其中按弱证据 → **HOLD 推荐** | 1 | `gh-outdoor-keep` |
| 🟠→🔴 其中同时是错归因 → **REJECT 优先** | 1 | `mn-outdoor-media` |
| ⚠️ **存在 conflict** | 12 | `gc-other-keep`、`gh-outdoor-keep`、`dl-sd-legal`、`dl-sd-op`、`qt-indoor-op`、`qt-outdoor-op`、`fp-sd-legal`、`fp-sd-op`、`gc-h6-pilot`、`xm-indoor-new`、`xm-outdoor-media`、`gh-indoor-new` |
| ⚖️ **LEGAL + Mandatory（法定强制，构成 resolver 下限）** | 16（其中 mandatory 16） | `dl-legal-dog`、`mn-sd-legal`、`lib-sd-legal`、`dl-sd-legal`、`qt-sd-legal`、`fp-sd-legal`、`xm-sd-legal`、`sb-sd-legal`、`gh-sd-legal`、`mn-legal-dog`、`lib-legal-dog`、`qt-indoor-legal`、`fp-legal-dog`、`xm-legal-dog`、`sb-legal-dog`、`gh-legal-dog` |
| 🦮 **service-dog / RuleException 相关** | 12 | `mn-sd-legal`、`lib-sd-legal`、`dl-sd-legal`、`dl-sd-op`、`qt-sd-legal`、`fp-sd-legal`、`fp-sd-op`、`xm-sd-legal`、`sb-sd-legal`、`gh-sd-legal`、`lib-sd-op`、`qt-sd-op` |

> **优先级说明**：错归因（事实性缺陷）**优先于**弱证据。`mn-outdoor-media` 同时命中两项，
> 因此归入 Group 1（REJECT）而非 Group 2 —— 这就是「2 条弱证据」但 Group 2 中只有 1 条源自弱证据的原因。
> Group 2 共 3 条 = 弱证据 HOLD 1 条 + 结论为推断/法律解释 HOLD 2 条。
> **service-dog 说明**：法条原文为「盲人携带导盲犬」，平台按 ADR-020 泛化为 `service_dog`。
> 该泛化是平台级决策，须评审员逐条确认（Group 3 的 APPROVE_WITH_NOTE 即为此类）。
> 当前数据库内**无** `status=current` 的 RuleException 覆盖本批任何场所（现有 6 条例外均为测试产物、状态 `withdrawn`）。

---

## Group 1 — REJECT（建议拒绝）

### G1-01 · `mn-outdoor-media` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`ed79071d-d052-46b4-a216-dc789aae4128`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`） · zone：`outdoor_seating`
- **proposed subject/action/effect**：普通宠物 · enter · **有条件允许**
- **conditions**：需牵引
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文））
- **Source issuer**：CBNData（Manner 首家宠物友好店报道）
- **Source URL**：https://www.cbndata.com/information/255703
- **关键原文引文**：> Manner咖啡全国首家宠物友好店落地凯德虹口商业中心，设置宠物户外区域
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=Manner咖啡（凯德虹口商业中心店） · canonical_address=上海市虹口区西江湾路388号凯德虹口商业中心 · spatial_precision=precise
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**REJECT**
- **recommendation reason**：PLACE_ATTRIBUTION_ERROR —— 来源原文不支持该场所（错归因实锤）
- **final_decision**：`________`  ← 留空，由具名评审员填写

## Group 2 — HOLD（建议挂起）

### G2-01 · `dl-legal-dog` — 上海迪士尼乐园

- **candidate_id**：`f5a8d87f-2d2a-4c1a-a018-b319cc9e580f`
- **place**：上海迪士尼乐园（`dl-disneyland`） · zone：`whole_park`
- **proposed subject/action/effect**：犬（通用） · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=上海迪士尼乐园 · canonical_address=上海市浦东新区川沙新镇申迪北路753号 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**HOLD**
- **recommendation reason**：结论为推断/法律解释或证据未证实，须补证或裁定
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G2-02 · `gc-other-keep` — 广场公园（黄浦段）

- **candidate_id**：`ffb804af-c271-443f-a07a-0fb3b5db5a87`
- **place**：广场公园（黄浦段）（`gc-huangpu-sect`） · zone：`other_areas`
- **proposed subject/action/effect**：普通宠物 · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：黄浦区人民政府官网《9月1日起，上海这些公园试点宠物入园》（来源：新闻晨报）
- **Source URL**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **关键原文引文**：> 目前这3个地方都属于试点，我们在现场张贴了试点公告，待试点结束后，将根据实际情况形成正式的规定。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=广场公园（黄浦段） · canonical_address=上海市黄浦区（金陵中路、西藏南路、延安东路、普安路合围H6区域） · spatial_precision=approximate
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict `gc-h6-pilot`（TEMPORARY_POLICY · conditional · primary_direct） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**HOLD**
- **recommendation reason**：结论为推断/法律解释或证据未证实，须补证或裁定
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G2-03 · `gh-outdoor-keep` — 港汇恒隆广场

- **candidate_id**：`887f21ba-e548-457b-a3dd-30ea806d988e`
- **place**：港汇恒隆广场（`gh-grand-gateway`） · zone：`outdoor`
- **proposed subject/action/effect**：普通宠物 · enter · **有条件允许**
- **conditions**：需牵引
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文））
- **Source issuer**：解放日报（运营方室内宠物禁令报道）
- **Source URL**：https://www.jfdaily.com/news/detail?id=1079860
- **关键原文引文**：> 港汇恒隆广场不再允许宠物进入商场室内区域，户外街区保留宠物通行
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=港汇恒隆广场 · canonical_address=上海市徐汇区虹桥路1号 · spatial_precision=precise
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict `gh-indoor-new`（OPERATOR_POLICY · prohibited · secondary_reputable） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**HOLD**
- **recommendation reason**：EVIDENCE_NOT_VERIFIED —— 证据仍仅为搜索摘要，未核验原文；不强行通过
- **final_decision**：`________`  ← 留空，由具名评审员填写

## Group 3 — CONFLICT / APPROVE_WITH_NOTE（须额外确认）

### G3-01 · `mn-sd-legal` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`52936479-c385-4279-814e-aa7fe8ab0a42`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`） · zone：`—`
- **proposed subject/action/effect**：服务犬 · enter · **允许**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=Manner咖啡（凯德虹口商业中心店） · canonical_address=上海市虹口区西江湾路388号凯德虹口商业中心 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **recommendation reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-02 · `lib-sd-legal` — 上海图书馆东馆

- **candidate_id**：`caa28a93-94e9-4643-b6c1-bbd5d77c3ecc`
- **place**：上海图书馆东馆（`lib-sh-library-east`） · zone：`—`
- **proposed subject/action/effect**：服务犬 · enter · **允许**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=上海图书馆东馆 · canonical_address=上海市浦东新区合欢路300号 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **recommendation reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-03 · `dl-sd-legal` — 上海迪士尼乐园

- **candidate_id**：`393c6b89-ea48-451f-aa93-9fba89ce215f`
- **place**：上海迪士尼乐园（`dl-disneyland`） · zone：`—`
- **proposed subject/action/effect**：服务犬 · enter · **允许**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=上海迪士尼乐园 · canonical_address=上海市浦东新区川沙新镇申迪北路753号 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict `dl-sd-op`（OPERATOR_POLICY · conditional · primary_direct） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **recommendation reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-04 · `dl-sd-op` — 上海迪士尼乐园

- **candidate_id**：`f799a74b-1f7e-49fb-bc4f-6281838877f0`
- **place**：上海迪士尼乐园（`dl-disneyland`） · zone：`whole_park`
- **proposed subject/action/effect**：服务犬 · enter · **有条件允许**
- **conditions**：需牵引
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海迪士尼度假区官网《上海迪士尼乐园游客须知》
- **Source URL**：https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/
- **关键原文引文**：> 动物（导盲犬除外）。导盲犬须时刻栓有系绳并在主人的看管下。部分游乐项目也可能不允许导盲犬进入。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=上海迪士尼乐园 · canonical_address=上海市浦东新区川沙新镇申迪北路753号 · spatial_precision=precise
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict `dl-sd-legal`（LEGAL · allowed · primary_direct） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-05 · `qt-indoor-op` — 前滩太古里

- **candidate_id**：`93fdbdf9-4855-45f8-8bd9-8af86715f748`
- **place**：前滩太古里（`qt-taikoo-li`） · zone：`indoor`
- **proposed subject/action/effect**：普通宠物 · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：前滩太古里（太古地产）官网《宠物友好》页
- **Source URL**：https://www.taikooliqiantan.com/detail/58.html
- **关键原文引文**：> 您的宠物仅能在前滩太古里户外开放区域，或商场或商场物业不时指定的室外特定范围区域内活动。未经商场或商场物业同意，您的宠物不得进入商场室内空间活动。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=前滩太古里 · canonical_address=上海市浦东新区东育路500弄 · spatial_precision=precise
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict `qt-outdoor-op`（OPERATOR_POLICY · conditional · primary_direct） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-06 · `qt-outdoor-op` — 前滩太古里

- **candidate_id**：`100d76af-c766-494d-8c25-2e29e2214b71`
- **place**：前滩太古里（`qt-taikoo-li`） · zone：`outdoor_open`
- **proposed subject/action/effect**：普通宠物 · enter · **有条件允许**
- **conditions**：需牵引、vaccination_required、max_count（1）
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：前滩太古里（太古地产）官网《宠物友好》页
- **Source URL**：https://www.taikooliqiantan.com/detail/58.html
- **关键原文引文**：> 您的宠物仅能在前滩太古里户外开放区域，或商场或商场物业不时指定的室外特定范围区域内活动。未经商场或商场物业同意，您的宠物不得进入商场室内空间活动。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=前滩太古里 · canonical_address=上海市浦东新区东育路500弄 · spatial_precision=precise
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict `qt-indoor-op`（OPERATOR_POLICY · prohibited · primary_direct） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-07 · `qt-sd-legal` — 前滩太古里

- **candidate_id**：`958d4d4c-6cd5-467e-9bc4-5eae2f67630e`
- **place**：前滩太古里（`qt-taikoo-li`） · zone：`—`
- **proposed subject/action/effect**：服务犬 · enter · **允许**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=前滩太古里 · canonical_address=上海市浦东新区东育路500弄 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **recommendation reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-08 · `fp-sd-legal` — 和平饭店（费尔蒙）

- **candidate_id**：`e94d2259-7f77-4bb5-a81c-c5ac5bc81239`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`） · zone：`—`
- **proposed subject/action/effect**：服务犬 · enter · **允许**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=和平饭店（费尔蒙） · canonical_address=上海市黄浦区南京东路20号 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict `fp-sd-op`（OPERATOR_POLICY · conditional · primary_direct） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **recommendation reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-09 · `fp-sd-op` — 和平饭店（费尔蒙）

- **candidate_id**：`7efddba6-7c42-4013-8918-bedbb996d702`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`） · zone：`whole_hotel`
- **proposed subject/action/effect**：服务犬 · enter · **有条件允许**
- **conditions**：无
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：Booking/Hotels.com/Expedia 聚合展示的运营方宠物政策
- **Source URL**：https://www.booking.com/hotel/cn/peace-hotel.html
- **关键原文引文**：> 上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。
- **place match evidence**：matched_by=canonical_name_and_address · place_id=7f5093f3-1222-4049-af9d-cc5ca4386b54 · note=R2 修复：原文页直接抓取并核验
- **evidence completeness**：3/4（缺：许可元数据）
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict `fp-sd-legal`（LEGAL · allowed · primary_direct） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-10 · `gc-h6-pilot` — 广场公园（黄浦段）

- **candidate_id**：`8f98fd01-9a1a-4d64-b354-01632d7bdbcd`
- **place**：广场公园（黄浦段）（`gc-huangpu-sect`） · zone：`h6_pet_area`
- **proposed subject/action/effect**：普通宠物 · enter · **有条件允许**
- **conditions**：需牵引
- **RuleLayer**：`TEMPORARY_POLICY`（临时/事件政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：黄浦区人民政府官网《9月1日起，上海这些公园试点宠物入园》（来源：新闻晨报）
- **Source URL**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **关键原文引文**：> 9月1日，市绿化和市容管理局《关于加强本市公园绿地开放管理的指导意见》施行。当天起，黄浦区新增大吉路公园、静谧花园、广场公园黄浦段H6区域作为宠物可入园试点区域
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=广场公园（黄浦段） · canonical_address=上海市黄浦区（金陵中路、西藏南路、延安东路、普安路合围H6区域） · spatial_precision=approximate
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict `gc-other-keep`（OPERATOR_POLICY · prohibited · primary_direct） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-11 · `xm-indoor-new` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`9c8b4b26-a2cb-4efd-b188-aeee3a194951`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`） · zone：`indoor`
- **proposed subject/action/effect**：普通宠物 · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`secondary_reputable`（可靠二手（权威媒体直抓））
- **Source issuer**：新闻媒体（2026-08 星巴克宠物专区调整报道）
- **Source URL**：None
- **关键原文引文**：> 为此我们已向顾客本人表达了诚挚的歉意，并着手进行了改进，不在该店内继续设置宠物区域。……携宠顾客需在店外宠物友好区落座。
- **place match evidence**：matched_by=canonical_name_and_address · place_id=91bdaeba-2841-4aa8-88fe-5aa55a2df8b9 · note=R2 修复：原文页直接抓取并核验
- **evidence completeness**：3/4（缺：许可元数据）
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict `xm-outdoor-media`（OPERATOR_POLICY · conditional · secondary_reputable） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-12 · `xm-outdoor-media` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`fb003b3a-3583-484b-b16f-7a6f3a1b71d0`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`） · zone：`outdoor_pet_area`
- **proposed subject/action/effect**：普通宠物 · enter · **有条件允许**
- **conditions**：需牵引
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`secondary_reputable`（可靠二手（权威媒体直抓））
- **Source issuer**：新闻媒体（2026-08 星巴克宠物专区调整报道）
- **Source URL**：None
- **关键原文引文**：> 为此我们已向顾客本人表达了诚挚的歉意，并着手进行了改进，不在该店内继续设置宠物区域。……携宠顾客需在店外宠物友好区落座。
- **place match evidence**：matched_by=canonical_name_and_address · place_id=91bdaeba-2841-4aa8-88fe-5aa55a2df8b9 · note=R2 修复：原文页直接抓取并核验
- **evidence completeness**：3/4（缺：许可元数据）
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict `xm-indoor-new`（OPERATOR_POLICY · prohibited · secondary_reputable） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-13 · `xm-sd-legal` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`6bf5128a-17ad-4a2f-83e5-eabecc7afb9f`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`） · zone：`—`
- **proposed subject/action/effect**：服务犬 · enter · **允许**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=星巴克咖啡（徐汇西岸梦中心店） · canonical_address=上海市徐汇区龙腾大道（西岸梦中心 GATE M） · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **recommendation reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-14 · `sb-sd-legal` — 星巴克臻选上海烘焙工坊

- **candidate_id**：`b8cffbee-855a-4754-ad84-b01db0351ea3`
- **place**：星巴克臻选上海烘焙工坊（`sb-roastery`） · zone：`—`
- **proposed subject/action/effect**：服务犬 · enter · **允许**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=星巴克臻选上海烘焙工坊 · canonical_address=上海市静安区南京西路789号（兴业太古汇） · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **recommendation reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-15 · `gh-indoor-new` — 港汇恒隆广场

- **candidate_id**：`73448553-cdfa-44db-8265-cb45dd325687`
- **place**：港汇恒隆广场（`gh-grand-gateway`） · zone：`indoor`
- **proposed subject/action/effect**：普通宠物 · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`secondary_reputable`（可靠二手（权威媒体直抓））
- **Source issuer**：解放日报（运营方室内宠物禁令报道）
- **Source URL**：https://www.jfdaily.com/news/detail?id=1079860
- **关键原文引文**：> 比如港汇恒隆广场、兴业太古汇自今年2月起正式实施全新宠物管理规定，明确禁止除导盲犬等工作犬以外的其他宠物进入商场室内公共区域，全面撤除“宠物友好”相关标识
- **place match evidence**：matched_by=canonical_name_and_address · place_id=ae797630-12dd-4f3b-8233-a3f3d0253a46 · note=R2 修复：原文页直接抓取并核验
- **evidence completeness**：3/4（缺：许可元数据）
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict `gh-outdoor-keep`（OPERATOR_POLICY · conditional · search_snippet） ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G3-16 · `gh-sd-legal` — 港汇恒隆广场

- **candidate_id**：`d91706de-9447-4b3d-8977-fbfe08760c7e`
- **place**：港汇恒隆广场（`gh-grand-gateway`） · zone：`—`
- **proposed subject/action/effect**：服务犬 · enter · **允许**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=港汇恒隆广场 · canonical_address=上海市徐汇区虹桥路1号 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **recommendation reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`  ← 留空，由具名评审员填写

## Group 4 — LOW-RISK APPROVE（低风险建议批准）

### G4-01 · `mn-legal-dog` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`c2b179b9-77bf-433a-9219-5a406c42d5c7`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`） · zone：`indoor`
- **proposed subject/action/effect**：犬（通用） · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=Manner咖啡（凯德虹口商业中心店） · canonical_address=上海市虹口区西江湾路388号凯德虹口商业中心 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-02 · `lib-legal-dog` — 上海图书馆东馆

- **candidate_id**：`49f2894e-2eae-4f57-bc97-f5ab7e0e0ba3`
- **place**：上海图书馆东馆（`lib-sh-library-east`） · zone：`whole_building`
- **proposed subject/action/effect**：犬（通用） · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=上海图书馆东馆 · canonical_address=上海市浦东新区合欢路300号 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-03 · `lib-pets-op` — 上海图书馆东馆

- **candidate_id**：`330abc76-b6e2-402f-91b1-47596bd95965`
- **place**：上海图书馆东馆（`lib-sh-library-east`） · zone：`whole_building`
- **proposed subject/action/effect**：普通宠物 · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海图书馆官网《读者须知》
- **Source URL**：https://www.library.sh.cn/guide/xuzhi
- **关键原文引文**：> 请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=上海图书馆东馆 · canonical_address=上海市浦东新区合欢路300号 · spatial_precision=precise
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-04 · `lib-sd-op` — 上海图书馆东馆

- **candidate_id**：`76d0dfc3-64ae-4d2b-a152-18ff8ebed588`
- **place**：上海图书馆东馆（`lib-sh-library-east`） · zone：`whole_building`
- **proposed subject/action/effect**：服务犬 · enter · **允许**
- **conditions**：无
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海图书馆官网《读者须知》
- **Source URL**：https://www.library.sh.cn/guide/xuzhi
- **关键原文引文**：> 请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=上海图书馆东馆 · canonical_address=上海市浦东新区合欢路300号 · spatial_precision=precise
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-05 · `dl-pet-ban` — 上海迪士尼乐园

- **candidate_id**：`cfe82cd4-4156-4daa-9ce2-3fdd5f5797fb`
- **place**：上海迪士尼乐园（`dl-disneyland`） · zone：`whole_park`
- **proposed subject/action/effect**：普通宠物 · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海迪士尼度假区官网《上海迪士尼乐园游客须知》
- **Source URL**：https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/
- **关键原文引文**：> 动物（导盲犬除外）。导盲犬须时刻栓有系绳并在主人的看管下。部分游乐项目也可能不允许导盲犬进入。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=上海迪士尼乐园 · canonical_address=上海市浦东新区川沙新镇申迪北路753号 · spatial_precision=precise
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-06 · `qt-indoor-legal` — 前滩太古里

- **candidate_id**：`8151db71-3622-429d-81bc-0a0212f23290`
- **place**：前滩太古里（`qt-taikoo-li`） · zone：`indoor`
- **proposed subject/action/effect**：犬（通用） · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=前滩太古里 · canonical_address=上海市浦东新区东育路500弄 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-07 · `qt-sd-op` — 前滩太古里

- **candidate_id**：`1249b621-1186-4366-a538-db04a6731fec`
- **place**：前滩太古里（`qt-taikoo-li`） · zone：`—`
- **proposed subject/action/effect**：服务犬 · enter · **允许**
- **conditions**：无
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：前滩太古里（太古地产）官网《宠物友好》页
- **Source URL**：https://www.taikooliqiantan.com/detail/58.html
- **关键原文引文**：> 本须知适用于除导盲犬以外的所有宠物，导盲犬不受本须知的限制。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=前滩太古里 · canonical_address=上海市浦东新区东育路500弄 · spatial_precision=precise
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-08 · `fp-legal-dog` — 和平饭店（费尔蒙）

- **candidate_id**：`c8a3f92b-27eb-443e-bc0e-083458158582`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`） · zone：`whole_hotel`
- **proposed subject/action/effect**：犬（通用） · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=和平饭店（费尔蒙） · canonical_address=上海市黄浦区南京东路20号 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-09 · `fp-pets-op` — 和平饭店（费尔蒙）

- **candidate_id**：`4c7aba30-a7e3-4ad7-88d7-61a0ba255f27`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`） · zone：`whole_hotel`
- **proposed subject/action/effect**：普通宠物 · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：Booking/Hotels.com/Expedia 聚合展示的运营方宠物政策
- **Source URL**：https://www.booking.com/hotel/cn/peace-hotel.html
- **关键原文引文**：> 上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。
- **place match evidence**：matched_by=canonical_name_and_address · place_id=7f5093f3-1222-4049-af9d-cc5ca4386b54 · note=R2 修复：原文页直接抓取并核验
- **evidence completeness**：3/4（缺：许可元数据）
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✗
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-10 · `dj-pilot` — 大吉路公园

- **candidate_id**：`70cc7579-1764-4177-82b5-fd2d5b255b37`
- **place**：大吉路公园（`dj-daji-park`） · zone：`whole_park`
- **proposed subject/action/effect**：普通宠物 · enter · **有条件允许**
- **conditions**：需牵引
- **RuleLayer**：`TEMPORARY_POLICY`（临时/事件政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：黄浦区人民政府官网《9月1日起，上海这些公园试点宠物入园》（来源：新闻晨报）
- **Source URL**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **关键原文引文**：> 当天起，黄浦区新增大吉路公园、静谧花园、广场公园黄浦段H6区域作为宠物可入园试点区域
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=大吉路公园 · canonical_address=上海市黄浦区大吉路 · spatial_precision=approximate
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-11 · `xm-legal-dog` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`6fc38502-85c7-4d7e-8a24-56fd5cc68e8a`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`） · zone：`indoor`
- **proposed subject/action/effect**：犬（通用） · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=星巴克咖啡（徐汇西岸梦中心店） · canonical_address=上海市徐汇区龙腾大道（西岸梦中心 GATE M） · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-12 · `sb-legal-dog` — 星巴克臻选上海烘焙工坊

- **candidate_id**：`1a97f24e-3cd0-445c-804d-741be34a0dad`
- **place**：星巴克臻选上海烘焙工坊（`sb-roastery`） · zone：`whole_store`
- **proposed subject/action/effect**：犬（通用） · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=星巴克臻选上海烘焙工坊 · canonical_address=上海市静安区南京西路789号（兴业太古汇） · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

### G4-13 · `gh-legal-dog` — 港汇恒隆广场

- **candidate_id**：`70d10467-a771-4331-bc3e-444eac424df2`
- **place**：港汇恒隆广场（`gh-grand-gateway`） · zone：`indoor`
- **proposed subject/action/effect**：犬（通用） · enter · **禁止**
- **conditions**：无
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方/一手直抓（逐字））
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place match evidence**：matched_by=canonical_name_and_address · canonical_name=港汇恒隆广场 · canonical_address=上海市徐汇区虹桥路1号 · spatial_precision=unknown
- **evidence completeness**：4/4
- **DataLicense status**：展示 ✓ · 存储 ✓ · 再分发 ✓
- **conflict / exception**：conflict 无 ｜ exception 无（本场所无 active RuleException）
- **AI recommendation**：**APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`  ← 留空，由具名评审员填写

---

## 3. 填写与提交方式

1. 在 `HUMAN_REVIEW_DECISIONS_R1.json` 中填写：
   - 顶层 `reviewer`（具名）与 `reviewed_at`（ISO 8601）；
   - 每条 `decisions[]` 的 `final_decision` 与 `review_note`。
   - `final_decision` 取值：`APPROVED` / `APPROVED_WITH_NOTE` / `HOLD` / `REJECTED`（须与发布脚本的 `EXECUTABLE` 口径一致）。
2. 或直接在 `HUMAN_REVIEW_QUICK_TABLE_R1.md` 的「我的决定」列勾填。
3. 随后把结果回填到机器登记表 `docs/reality_audit/review_decisions_r1.json` 的
   `final_decision` / `reviewer` / `reviewed_at` 三列（发布脚本读的是该文件）。
4. 校验：`python scripts/publish_reviewed_r1.py --dry-run` 应返回 `signed=true`，
   且「登记表 ↔ 库」一致性校验通过（ADR-024）。
5. 首批建议条数 ≤ `--max-approve`（默认 20），禁止盲批。

> **本包不执行任何发布。** `--execute` 必须由人类评审员在签署后手动触发。

