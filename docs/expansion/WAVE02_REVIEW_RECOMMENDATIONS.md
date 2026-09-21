# WAVE02_REVIEW_RECOMMENDATIONS — 20 条候选 AI 审核与签署建议（待 huangdi97 逐行决定）

- expansion_run_id: `EXP-R1-W02-20260919`
- review_revision: `EXP-R1-W02-REVIEW-R1`
- 生成：PI-Desktop（Agent）· 2026-09-21 · **只读审核**
- 对应包：`docs/expansion/WAVE02_HUMAN_REVIEW_PACKET.md` / `WAVE02_HUMAN_REVIEW_QUICK_TABLE.md` / `review_decisions_expansion_r1_wave02.json`
- 决策登记表：`docs/expansion/review_decisions_expansion_r1_wave02.json`（**本文件不修改登记表**）

> **声明（不代签）**：本文档只提供 AI 审核意见与推荐理由，供 `huangdi97` 逐行签署。
> `final_decision` 列全部保持 **EMPTY**；本文不写入登记表、不填 reviewer / decided_at、
> 不发布任何规则。决策只允许 APPROVED / HOLD / REJECTED 三选一（Packet §2）。

---

## 1. 审核判据（22 项，逐条过一遍）

| # | 判据 | 检查内容 |
|---|---|---|
| 1 | original source | 来源原文 vs 候选 scope 的一致性（source_scope_exact） |
| 2 | source type | official_operator_policy / government_service / external_web_reference |
| 3 | source scope exactness | 来源用词（动物 / 宠物 / 犬类 / 猫类 / 导盲犬）字面保真 |
| 4 | normalized subject | subject_scope_normalized（dog / cat / other / ordinary_pet / guide_dog）|
| 5 | dog / cat / other | 动物→拆分子集是否仅为「可表达子集」声明 |
| 6 | compound_term_split | normalization_type=compound_term_split 是否有声明拆分语义 |
| 7 | RuleLayer | OPERATOR_POLICY 是否与来源层级匹配 |
| 8 | MandatoryLevel | operator_discretion 是否与 layer 匹配 |
| 9 | effect | prohibited / conditional 与 normative_effect 一致 |
| 10 | Zone | zone 归属（全园 / 全馆 / 试点区域 / 后滩除外）精确性 |
| 11 | condition | time_windows / leash_required / other_structured_note 结构化 |
| 12 | exception | 导盲犬 / 后滩滨江 例外是否同层、可达、不泛化 |
| 13 | source freshness | 采集时间、贴纸更新、试点期限 |
| 14 | EvidenceBundle | evidence_bundle_id 存在、quote/hash 可溯 |
| 15 | license | storage/display/redistribution 是否与发布要求兼容 |
| 16 | place attribution | place_id 对应正确场所（含同名消歧） |
| 17 | source attribution | source_id 指向正确发行人 |
| 18 | ontology remainder | 「动物」未建模成员是否保持 UNKNOWN（不得变 ALLOWED） |
| 19 | guide dog / service dog 语义 | 导盲犬例外不得推广至所有服务犬（ADR-025/031） |
| 20 | holder_scope | 例外持有者范围（person_with_disability 等）不超出原文 |
| 21 | conflict / supersession | 与既有已发布规则 / 候选无冲突、无重复 |
| 22 | AI recommendation | 综合以上给出 APPROVED / HOLD / REJECTED 建议 + 理由 |

---

## 2. 逐场所审核

### 2.1 上海世博文化公园（3 条）

| candidate_id | 7774a487… / f80c6071… / afe409b1… |
|---|---|
| 来源 | 官网《游园须知》`https://www.expoculturepark.cn/faq`，official_operator_policy，direct |
| scope | 动物 → dog / cat / other，compound_term_split（声明拆分子集）|
| effect | 禁止（prohibition）×3，OPERATOR_POLICY / operator_discretion |
| conditions | 无 |
| zone | whole_park = 「全园（后滩滨江区域除外）」——zone 已排除后滩滨江 |
| evidence | `expansion_r1_wave02_evidence.json` expo_official_rules，fragment `no_animals_except_houtan` |
| 22 项核对 | 拆分语义正确（未建模动物保持 UNKNOWN，不 ALLOWED）；同层；无冲突/无 supersede；ADR030/031 PASS（§29 gates 实测）|
| 风险 | ①「狗GO乐园」宠物乐园子区域未建模为独立 zone/例外（packet 明确「例外待人工核验」）；②zone 名称以「后滩滨江区域除外」方式表达例外，需在发布批次继续保留该语义 |
| **AI recommendation** | **APPROVED**（3 条成组）|
| recommended reason | 官方一手来源、字面保真、拆分语义规范、证据完备；zone 已排除后滩滨江。请 huangdi97 确认：狗GO乐园若为独立可携宠区域，应在发布批次前补录为 zone/例外（本期不新增，仅提示）；若认为该缺口不可接受，可将本条改 HOLD。 |

### 2.2 上海植物园（3 条）

| candidate_id | 97d564fa… / 4b4b4e07… / 630e1c0d… |
|---|---|
| 来源 | 市级共享来源《上海市公园文明游园守则（2018版）》+ 园方《游园守则》，government_service，direct |
| scope | 动物 → dog / cat / other，compound_term_split |
| effect | 禁止 ×3，OPERATOR_POLICY / operator_discretion |
| conditions | 无 |
| zone | whole_park = 全园 |
| evidence | shbg_official_rules / shared 市级游园守则 bundle |
| 22 项核对 | 拆分正确；layer/level 匹配；无冲突；gates PASS |
| 风险 | 2018 版市级守则的时效性（5.5 年旧），freshness gate PASS 但建议发布批次保留 SourceMonitor 轮巡 |
| **AI recommendation** | **APPROVED**（3 条成组）|
| recommended reason | 政府一手来源（市级文明游园守则适用于本市公园），字面拆分与 zone 精确；唯一风险为守则版本年限，已有 SourceMonitor 兜底。 |

### 2.3 上海自然博物馆（1 条）

| candidate_id | 700dcd4d… |
|---|---|
| 来源 | 官网《参观须知》`https://www.snhm.org.cn/cgfw/cgzx.htm`，official_operator_policy，direct |
| scope | 宠物 → ordinary_pet，**exact**（真等价）|
| effect | 禁止，OPERATOR_POLICY / operator_discretion |
| conditions | 无 |
| zone | whole_museum = 全馆（indoor）|
| evidence | snhm_official_rules，fragment `no_pets` |
| 22 项核对 | 原文「请勿携带…宠物等」→ ordinary_pet exact 保真；未发现导盲犬/服务犬例外原文，不臆造（ADR-030 proviso 仅在 legal provision 成立时适用）——**正确** |
| 风险 | 低（一手官方、exact、无例外缺口）|
| **AI recommendation** | **APPROVED** |
| recommended reason | 字面 exact、官方直源、zone 精确；未在无依据时泛化服务犬例外，语义严谨。 |

### 2.4 上海辰山植物园（1 条）

| candidate_id | 81eca767… |
|---|---|
| 来源 | 官网《游园指南》`https://www.csnbgsh.cn/…zhinan.ashx`，official_operator_policy，但 **directness=secondary**；「禁止携带宠物…入园」句为**外部收录的入园须知第九条表述**，`needs_verification=True` |
| scope | 宠物 → ordinary_pet，**exact** |
| effect | 禁止，OPERATOR_POLICY / operator_discretion |
| conditions | 无 |
| zone | whole_garden = 全园 |
| evidence | csn_official_guide，fragment `no_pets` |
| 22 项核对 | scope/拆分/layer 均规范；**唯一缺口：禁用句子来自外部收录而非官网原页逐字核验**（packet 明示「以官网原页逐字核验为准」）|
| 风险 | 若外部收录转述有偏差，会造成「禁止携带宠物」被误记；官网页面可达故可核验 |
| **AI recommendation** | **HOLD**（待官网原页逐字核验后再批准）|
| recommended reason | 本轮剩余工作极小：进入 `https://www.csnbgsh.cn/sites/chenshan2020/static/zhinan.ashx` 原页，逐字核对入园须知第九条后即可转 APPROVED；批准前不应发布一个 needs_verification=True 的禁止规则（§27 二级/未核验来源不静默升级）。 |

### 2.5 上海野生动物园（1 条）

| candidate_id | 237512f7… |
|---|---|
| 来源 | 官网《游园指南》`https://www.swap-shendi.com/index.do?guide=`，official_operator_policy，direct |
| scope | 宠物 → ordinary_pet，**exact** |
| effect | 禁止，OPERATOR_POLICY / operator_discretion |
| conditions | 无 |
| zone | whole_park = 全园 |
| evidence | shwzoo_official_guide，fragment `no_pets` |
| 22 项核对 | 原文「二、不得携带宠物入园」；place 消歧已注明与上海动物园（长宁区虹桥路2381号）为不同法人/园区——正确 |
| 风险 | 与「上海动物园」同名混淆（已消歧）|
| **AI recommendation** | **APPROVED** |
| recommended reason | 官方一手、exact、place 归属带消歧说明，无缺口。 |

### 2.6 共青森林公园（3 条）

| candidate_id | c111a1a1… / ec883c91… / eba1843a… |
|---|---|
| 来源 | 官网《文明游园守则》`https://www.shgqsl.com/…`，official_operator_policy，direct |
| scope | 动物 → dog / cat / other，compound_term_split |
| effect | 禁止 ×3，OPERATOR_POLICY / operator_discretion |
| conditions | 无 |
| zone | whole_park = 全园 |
| evidence | gongqing_official_rules，fragment `no_animals` |
| 22 项核对 | 拆分正确；未建模动物保持 UNKNOWN；无冲突；gates PASS |
| 风险 | 低 |
| **AI recommendation** | **APPROVED**（3 条成组）|
| recommended reason | 官方直源、字面拆分规范，同 2.1/2.2 推理。 |

### 2.7 和平公园（2 条）

| candidate_id | 98d2b355…（dog）/ da0c270c…（cat）|
|---|---|
| 来源 | 虹口区绿化和市容管理局试点公告（2025-09-01 起）`https://www.shhk.gov.cn/…`，government_service，direct |
| scope | 犬类/猫类 → dog / cat，**exact** |
| effect | 有条件允许（conditional_permission），OPERATOR_POLICY / operator_discretion |
| conditions | dog：time_windows(8:00-20:00) + leash_required(True) + other_structured_note(刚性牵引绳≤1.5m、禁伸缩绳、肩高≥45cm 嘴套)；cat：time_windows + other_structured_note(按公园规定、禁便溺、避让老幼孕) |
| zone | pet_pilot_area = 携宠试点区域（部分区域）|
| evidence | hongkou_pilot_notice_shared，fragment `pilot_pet_rule` |
| 22 项核对 | 条件是结构化条件（condition_schema gate PASS）；试点区域 zone 化正确；「有条件允许」是 zone-first 精确表达，未写成全园 ALLOWED——正确 |
| 风险 | ①试点性质与期限（2025-09-01 起，是否为限时试点/后续延续）需人工确认；②试点区域为部分区域，zone 语义必须保持 |
| **AI recommendation** | **APPROVED**（2 条成组）|
| recommended reason | 政府一手公告、exact 字面、条件全部结构化且 zone 精确到试点区域，未夸大为全园允许。请 huangdi97 注意试点期限问题：若试点已结束或轮巡发现变更，应按 SourceMonitor 流程另行处理（不阻塞本期批准，但建议发布批次把试点期限写进 freshness 元数据）。 |

### 2.8 昆山公园（1 条）

| candidate_id | d5551907… |
|---|---|
| 来源 | 同虹口试点公告（共享 source），government_service，direct |
| scope | 犬类 → dog，**exact** |
| effect | 有条件允许，OPERATOR_POLICY / operator_discretion |
| conditions | time_windows + leash_required + other_structured_note（同和平 dog）|
| zone | pet_pilot_area = 携宠试点区域 |
| evidence | hongkou_pilot_notice_shared |
| 22 项核对 | 与和平 dog 同源同结构；地址按区级公开信息录入四川北路1933号，**门牌级人工核验状态=False** |
| 风险 | 地址为区级公开信息，未做门牌级核验（不影响规则语义，影响导航精度）|
| **AI recommendation** | **APPROVED**（附加地址核验待办）|
| recommended reason | 同一政府来源、同一条件结构、试点 zone 精确。地址门牌未人工核验一项请列入后续数据质量清单（不影响本规则批准）。 |

### 2.9 豫园（2 条）

| candidate_id | 5f22e9a1…（base）/ 91970069…（导盲犬例外）|
|---|---|
| 来源 | 官网《游园须知》`https://www.yugarden.com.cn/Page/ArticleView/notice.html`，official_operator_policy，direct |
| scope | base：宠物 → ordinary_pet exact；例外：导盲犬 → guide_dog exact（source 原文「宠物（符合规定的导盲犬除外）」）|
| effect | base：禁止；例外：exempt_from_prohibition（conditional）|
| conditions | 例外：other_structured_note(符合规定：持有效导盲犬身份证明及在役使用) |
| zone | whole_garden = 全园 |
| evidence | yuyuan_official_notice，fragment `no_pets_except_guide_dog` |
| 22 项核对 | base 与例外同层（OPERATOR_POLICY）同源——**例外为同层 carve-out，非跨层放宽**（§29 EXCEPTION_REACHABILITY PASS）；导盲犬例外**未**泛化为所有服务犬（ADR-025/031 保真）；holder_scope=person_with_disability 与原文「符合规定的导盲犬」关系需人工确认；condition 结构化为「符合规定：持有效导盲犬身份证明及在役使用」 |
| 风险 | holder_scope=person_with_disability：导盲犬天然由视障人士使用，person_with_disability 是平台 holder 语义的既有类别，但不排除收紧到更窄类别；base 禁止与例外并发发布时顺序需由发布批次保证（先 base 后例外或原子写入）|
| **AI recommendation** | base **APPROVED**；导盲犬例外 **APPROVED**（附 holder_scope 复核提示）|
| recommended reason | 来源原文同时给出 base 禁 + 导盲犬例外，语义闭环，字面 exact，未泛化服务犬。请 huangdi97 通过或在批注中确认 holder_scope：a) 维持 person_with_disability（推荐，平台既有类别，已带「持有效导盲犬身份证明及在役使用」条件约束）；b) 若认为必须逐字对应「盲人携带」可改批注校准。二者都不影响「不得泛化至 hearing/assistance/other service dog」的红线。 |

### 2.10 顾村公园（3 条）

| candidate_id | 36f6382f… / c6c5b74d… / b6abed36… |
|---|---|
| 来源 | 本地宝（bendibao）2025-03-11 转述顾村公园游园须知，**external_web_reference，directness=secondary**，`needs_verification=True` |
| scope | 动物 → dog / cat / other，compound_term_split |
| effect | 禁止 ×3，OPERATOR_POLICY / operator_discretion |
| conditions | 无 |
| zone | whole_park = 全园 |
| evidence | gucun_secondary_rules，fragment `no_animals` |
| 22 项核对 | 拆分正确；但**来源为二级转述**（本地宝标题即「宠物入园政策」，正文「未经许可，不得携带各种动物入园」）；packet 与 evidence 均标 needs_verification=True，「二级来源仅作 lead，不得静默升级（§27）」 |
| 风险 | 未核实到圃方一手《游园须知》原文；若转述失真，全园禁止会误导 |
| **AI recommendation** | **HOLD**（3 条成组：待圃方一手来源核实后批准）|
| recommended reason | 严格遵循 §27：二级来源（本地宝转述）只能作为 lead，不能静默升级为已核验规则。处置路径：a) 进入顾村公园官网/官方公众号核实「未经许可不得携带各种动物入园」原文；b) 核实后更新 source（directness→direct / needs_verification=False）并转 APPROVED；c) 若无法核实，保持 HOLD 并让 place 呈现「规则未知」。 |

---

## 3. 签署表（可直接逐行签署；final_decision 全部 EMPTY）

| candidate_id | place | rule summary | zone | source | evidence | risk | AI recommendation | recommended reason | final_decision |
|---|---|---|---|---|---|---|---|---|---|
| 7774a487-dbe4-462a-9c36-433803a3563e | 上海世博文化公园 | 动物(→dog) 全园禁止进入 | 全园（后滩滨江除外） | 官网《游园须知》(official, direct) | bundle 6a54fd30 / frag no_animals_except_houtan | 狗GO乐园子区域例外未建模；poster 批次前以 zone 保持例外 | APPROVED | 官方一手、拆分保真、zone 已排除后滩；例外缺口提示发布批次处理 | |
| f80c6071-28f0-4fe7-837d-41d6752ed0a4 | 上海世博文化公园 | 动物(→cat) 全园禁止进入 | 全园（后滩滨江除外） | 同上 | 同上 | 同上 | APPROVED | 同上（成组） | |
| afe409b1-3a21-41a5-bd3c-aa0996477c44 | 上海世博文化公园 | 动物(→other) 全园禁止进入 | 全园（后滩滨江除外） | 同上 | 同上 | 未建模动物保持 UNKNOWN（不 ALLOWED）| APPROVED | 同上（成组） | |
| 97d564fa-4de4-418a-bc40-ddcca0c1e8ea | 上海植物园 | 动物(→dog) 全园禁止进入 | 全园 | 市级文明游园守则+园方守则 (gov, direct) | bundle 487b18dc | 2018 版守则年限，SourceMonitor 兜底 | APPROVED | 政府一手、拆分保真、freshness 由 monitor 保障 | |
| 4b4b4e07-73e9-4a47-8728-cff6b3e1488a | 上海植物园 | 动物(→cat) 全园禁止进入 | 全园 | 同上 | 同上 | 同上 | APPROVED | 同上（成组） | |
| 630e1c0d-c9b6-4a15-ad8d-d31e3268b126 | 上海植物园 | 动物(→other) 全园禁止进入 | 全园 | 同上 | 同上 | 未建模动物保持 UNKNOWN | APPROVED | 同上（成组） | |
| 700dcd4d-6e15-4d87-bf13-5b77cab049cb | 上海自然博物馆 | 宠物(ordinary_pet) 全馆禁止进入 | 全馆(indoor) | 官网《参观须知》(official, direct) | bundle e2a1cc19 / frag no_pets | 低；未臆造导盲犬例外（正确）| APPROVED | 官方 exact、无例外缺口、语义严谨 | |
| 81eca767-c5dc-4c60-b165-a38e5db0aecd | 上海辰山植物园 | 宠物(ordinary_pet) 全园禁止进入 | 全园 | 官网《游园指南》(official, **secondary**, needs_verification) | bundle 1fab6943 | 禁止句子为外部收录，未逐字核验官网原页 | **HOLD** | needs_verification=True 的禁止不可先行发布；官网原页逐字核验后转 APPROVED（§27）| |
| 237512f7-6ce0-43cb-a207-4481dd6e9056 | 上海野生动物园 | 宠物(ordinary_pet) 全园禁止进入 | 全园 | 官网《游园指南》(official, direct) | bundle ae53ab55 | 与上海动物园同名混淆（已消歧）| APPROVED | 官方 exact、place 消歧完整 | |
| c111a1a1-6660-43fe-a663-dd19e0c1d6eb | 共青森林公园 | 动物(→dog) 全园禁止进入 | 全园 | 官网《文明游园守则》(official, direct) | bundle 7869b9cf | 低 | APPROVED | 官方直源、拆分保真 | |
| ec883c91-5c80-4754-8309-f6791ec9e565 | 共青森林公园 | 动物(→cat) 全园禁止进入 | 全园 | 同上 | 同上 | 低 | APPROVED | 同上（成组）| |
| eba1843a-46d2-4aab-9553-9efcbf74a5c5 | 共青森林公园 | 动物(→other) 全园禁止进入 | 全园 | 同上 | 同上 | 未建模动物保持 UNKNOWN | APPROVED | 同上（成组）| |
| 98d2b355-4fc1-4c15-ac7a-6b44188636ea | 和平公园 | 犬类(dog) 试点区限时8:00-20:00有条件允许 | pet_pilot_area | 虹口区试点公告(gov, direct) | bundle fa85fc03 | 试点期限未人工确认；zone 必须保持试点区域 | APPROVED | 政府一手、条件结构化、zone-first 精确、未夸大全园 | |
| da0c270c-71b1-4163-bb4a-095ba6bfe8d7 | 和平公园 | 猫类(cat) 试点区限时8:00-20:00有条件允许 | pet_pilot_area | 同上 | 同上 | 同上 | APPROVED | 同上（成组）| |
| d5551907-08dc-4d66-a6b7-50631c81581e | 昆山公园 | 犬类(dog) 试点区限时8:00-20:00有条件允许 | pet_pilot_area | 虹口区试点公告(共享 source) | bundle d672304b | 地址门牌级未人工核验（导航精度问题，非规则语义）| APPROVED | 同源同条件结构；地址核验列数据质量待办 | |
| 5f22e9a1-fd74-44a2-a0d4-312d98939ba2 | 豫园 | 宠物(ordinary_pet) 全园禁止进入 | 全园 | 官网《游园须知》(official, direct) | bundle 0f2c647a | 与导盲犬例外并发发布需批次顺序保证 | APPROVED | 官方原文 base 禁，exact | |
| 91970069-b691-4c3f-bd48-c4fca505e349 | 豫园 | 导盲犬(guide_dog) 持证+在役使用时有条件允许（例外）| 全园 | 官网《游园须知》(同源) | bundle 0f2c647a | holder_scope=person_with_disability 建议确认；不得泛化服务犬 | APPROVED | 原文明示例外、同层 carve-out、条件结构化、未泛化（ADR-025/031）| |
| 36f6382f-ecd9-4b89-8109-db341f3876fa | 顾村公园 | 动物(→dog) 全园禁止进入 | 全园 | 本地宝转述(external, **secondary**, needs_verification) | bundle e713bb40 | 二级来源未核实圃方一手原文 | **HOLD** | §27 二级来源仅作 lead，核实一手后转 APPROVED | |
| c6c5b74d-86ec-45e8-b412-2db94e934969 | 顾村公园 | 动物(→cat) 全园禁止进入 | 全园 | 同上 | 同上 | 同上 | **HOLD** | 同上（成组）| |
| b6abed36-993c-4861-981b-b392f917a07d | 顾村公园 | 动物(→other) 全园禁止进入 | 全园 | 同上 | 同上 | 未建模动物保持 UNKNOWN + 二级来源 | **HOLD** | 同上（成组）| |

---

## 4. 汇总

- 建议 **APPROVED：16 条**（世博×3、植物园×3、自然博物馆×1、野生动物园×1、共青×3、和平×2、昆山×1、豫园×2）
- 建议 **HOLD：4 条**（辰山×1、顾村×3）
- 建议 **REJECTED：0 条**
- HOLD 全部为「来源核验缺口」类（官网逐字核验 / 二级转述核实一手），**无 schema / 语义 / 数据缺陷**；无需 deterministic regeneration。
- Approval 建议中的注意项（不阻塞签暑）：世博狗GO乐园例外缺口、虹口试点期限、昆山地址门牌核验、豫园 holder_scope 复核。

> 若 huangdi97 对任何 APPROVED 有异议，可改 HOLD / REJECTED；对 HOLD 逐字核实完成后可改 APPROVED。
> 所有判定仅由人决定；本文档不改变 `review_decisions_expansion_r1_wave02.json` 的任何字段。

---

## 5. 终止态

```
HUMAN_ACTION_REQUIRED = WAVE02_FINAL_DECISIONS
```

等待 `huangdi97` 在 `docs/expansion/review_decisions_expansion_r1_wave02.json`
（或本表）中逐行填写 final_decision（APPROVED / HOLD / REJECTED）与 reviewer / decided_at。
批准项将进入独立发布批次流程（届时另跑 pre-publish gate + dry-run，本 Goal 不自动执行）。