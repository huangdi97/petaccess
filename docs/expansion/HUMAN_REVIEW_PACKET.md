# HUMAN_REVIEW_PACKET — 人工复核包（EXP-R1-W01-REVIEW-R1）

- expansion_run_id: `EXP-R1-W01-20260918`
- review_revision: `EXP-R1-W01-REVIEW-R1`
- generated_at: 2026-09-18T03:43:17.580156+00:00
- 生成方式：由 `scripts/expansion_w01_reports.py` 从生产库与运行清单派生，非手写

> **本文件不含任何人工决策。** 决策字段为空白，须由人工复核人填写。
> 机器只负责把材料摆到复核人面前，不负责替复核人做决定（§3, §42-§45）。

## 1. 复核范围

- 候选规则：31 条，全部 `REVIEW_PENDING`
- 复核版本：`EXP-R1-W01-REVIEW-R1`
- 决策登记表：`docs/expansion/review_decisions_expansion_r1_wave01.json`

## 2. 复核人须知

1. 每条候选必须给出 `final_decision`：APPROVED / HOLD / REJECTED 之一。
2. `final_decision` 与 `reviewer`、`decided_at` 必须同时填写；缺一即视为无效。
3. 不得批注「交由系统后续自动决定」。
4. 批准后仍走独立发布批次流程，不在本轮自动执行。

## 3. 逐条材料

### CHARLIE'S 粉红汉堡（马当路店）

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| 052d19cc | 犬只 | dog | dog | prohibited | LEGAL | exact |  |
| f25e4093 | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | legal_interpretation_required | lead-only 社媒/第三方平台内容（§12：social 仅作线索，不得单独成规则）。本条落库仅为待审线索，不得据以发布。 |

### omitofee 上海首店（浦江郊野公园滨江漫步区）

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| 7de2f5d7 | 犬只 | dog | dog | prohibited | LEGAL | exact | 与运营方「允许宠物随主人一同入内」直接冲突。法条为 LEGAL/mandatory，运营方声明为 OPERATOR_POLICY；如实并存，禁止自动让运营方覆盖法条（§20）。 |
| d37afb4d | 小型犬 / 全犬种 | dog | dog | conditional | OPERATOR_POLICY | legal_interpretation_required | 分区规则需拆分为两个 zone 才能准确表达；本轮先落一条候选并标注需人工细化。 |
| 16b7acc5 | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | exact | 来源为媒体报道（needs_verification=true），未取得门店官方页面原文；与 LEGAL 层冲突，交人工复核。 |

### 上海动物园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| 6f2bfd39 | 动物 | other | other | prohibited | OPERATOR_POLICY | exact | 来源用词为「动物」（全部动物），非「宠物」/「犬只」。按条例第五十九条动物园特定用途犬只另有国家规定；本条按场所管理方声明记录为 OPERATOR_POLICY，非 LEGAL 层（第二十三条清单不含动物园）。 |

### 上海博物馆东馆

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| fa5f33f1 | 犬只 | dog | dog | prohibited | LEGAL | exact | LEGAL 层禁入。适用性证据为场所类型与法条列举项的对应，需人工复核。 |
| 73de8e33 | 导盲犬 | guide_dog | service_dog | allowed | LEGAL | exact | 同层 LEGAL carve-out；来源用词为「导盲犬」，scope 不做向「全部服务犬」的泛化（ADR-025）。 |
| 4710a68f | 携带宠物者 | ordinary_pet | ordinary_pet | prohibited | OPERATOR_POLICY | exact | 场馆自行声明，与 LEGAL 层同向；不得被解读为覆盖 LEGAL。 |

### 上海新天地朗廷酒店

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| df1645fe | 犬只 | dog | dog | prohibited | LEGAL | exact | 与运营方 Pawcation 条款存在明显张力（法条禁止携带犬只进入宾馆）。两者如实并存，OPERATOR_POLICY 不得覆盖 LEGAL，交人工复核（§20）。 |
| 32a1e612 | 狗狗 | dog | dog | conditional | OPERATOR_POLICY | exact | 运营方官方条款，逐字可核；空间范围限于「宠物友好区」。与 LEGAL 层张力见 langham-legal-dog-prohibited。 |
| a3bc8efe | 宠物 | dog | dog | conditional | OPERATOR_POLICY | exact | 结构化条件来自原文「抱紧/装笼/推车」，不得简化为 amenity 备注（§21）。 |
| 3ef1f976 | 宠物 | dog | dog | conditional | OPERATOR_POLICY | exact | 宠物友好区含「凯旋餐厅的室外区域（Al Fresco）」；餐厅属第二十三条第一款列举的「餐饮场所」，室外部分是否落入需人工判定。 |

### 上海苏河湾万象天地

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| 8ba2b49b | 犬只 | dog | dog | prohibited | LEGAL | exact | LEGAL 层只作用于 indoor zone；不得外推到室外。 |
| e8727b00 | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | exact | 与 LEGAL 层潜在张力：若室外区域被认定为「商场」的一部分，则 OPERATOR_POLICY 不得放宽 LEGAL。此处如实并存，交人工复核（§20 禁止 OPERATOR 覆盖 LEGAL）。 |

### 上海蟠龙天地

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| 9787b070 | 毛孩子们 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | legal_interpretation_required | 「覆盖大部分区域」为模糊表述，且街区内含餐饮场所（第二十三条第一款独立列举）。本条不宣称全街区可携宠，交人工细化到 zone/店铺粒度。 |
| 21bb1b33 | 毛孩子们 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | legal_interpretation_required | 来源未给出可逐字引用的准入条件；「宠物友好覆盖大部分区域」不构成 ALLOWED 规则，仅作条件性候选。开放式街区/景区不在第二十三条第一款列举清单内，故为 OPERATOR_POLICY。 |

### 上海迪士尼乐园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| 3a04d4d1 | 动物（导盲犬除外） | other | other | prohibited | OPERATOR_POLICY | exact | 主题乐园不在第二十三条第一款列举清单内 → OPERATOR_POLICY。来源用词「动物」宽于宠物，逐字保留。 |
| 305fa08c | 导盲犬 | guide_dog | service_dog | conditional | OPERATOR_POLICY | exact | 同层 OPERATOR_POLICY carve-out。base scope 为「动物」含导盲犬 → 该 carve-out 可达（非 inert）。SEMANTIC_REMODEL_ISSUE 本轮不自动修复（§3）。 |

### 世纪公园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| a3b2d092 | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | exact | Zone-first：局部开放不得写成 Place 级 ALLOWED（§17）。来源为政府文旅平台转述园方口径，needs_verification=true。 |
| 4e217d58 | 宠物 | ordinary_pet | ordinary_pet | prohibited | OPERATOR_POLICY | exact | 公园不在《上海市养犬管理条例》第二十三条第一款列举清单内，管理者可自行决定（第二十三条第二款），故记为 OPERATOR_POLICY。 |

### 兴业太古汇

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| 1fb3d7f1 | 犬只 | dog | dog | prohibited | LEGAL | exact |  |
| 6482477d | 导盲犬 | guide_dog | service_dog | allowed | LEGAL | exact | 运营方口径为「导盲犬等工作犬」，宽于法条「导盲犬」。本条只按法条原文记录导盲犬；「等工作犬」未取得法条依据，不得写入（ADR-025）。 |
| b340f06c | 除导盲犬等工作犬以外的其他宠物 | ordinary_pet | ordinary_pet | prohibited | OPERATOR_POLICY | legal_interpretation_required | 来源为「工作犬以外其他宠物」，与存储 scope ordinary_pet 不完全等价，标记 legal_interpretation_required 交人工判定；且来源为媒体报道，needs_verification=true。 |

### 前滩太古里

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| d1aee781 | 犬只 | dog | dog | prohibited | LEGAL | exact |  |
| b6af608a | 毛孩子 | ordinary_pet | ordinary_pet | prohibited | OPERATOR_POLICY | legal_interpretation_required | 与存量官方《宠物友好》页口径（室内需物业同意）方向一致但更严；两者并存交人工裁决哪一版为 current。来源 needs_verification=true。 |
| 0763f68c | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | exact | 室外区域与存量官方页口径一致。LEGAL 层仅作用于 indoor zone。 |

### 港汇恒隆广场

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| e951785d | 犬只 | dog | dog | prohibited | LEGAL | exact |  |
| cf3fa538 | 除导盲犬等工作犬以外的其他宠物 | ordinary_pet | ordinary_pet | prohibited | OPERATOR_POLICY | legal_interpretation_required | 存量候选基于解放日报 2025 年报道；本条为 2026-03 更新口径，可能构成 supersede 关系，是否取代由人工判定。 |

### 西岸梦中心（Gate M）

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 说明 |
|---|---|---|---|---|---|---|---|
| e3d39839 | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | exact | 管理方明确「没有统一要求和规定」。此场所-分区应落在 PARTIALLY_ANSWERABLE / UNKNOWN 而非强制结论，候选仅作待审线索（§27）。 |
| e9322630 | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | exact | 户外开放空间不在第二十三条第一款列举清单内（非商场室内），管理者可自行决定；来源为客服口头回应（needs_verification=true）。 |

## 4. 全部候选一览

| # | 场所 | 来源用词 | 归一化主体 | scope | effect | layer | source_type | 抽取说明（截断） |
|---|---|---|---|---|---|---|---|---|
| 1 | CHARLIE'S 粉红汉堡（马当路店） | 犬只 | dog | dog | prohibited | LEGAL | statute_or_regulation |  |
| 2 | CHARLIE'S 粉红汉堡（马当路店） | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | external_web_reference | lead-only 社媒/第三方平台内容（§12：social 仅作线索，不得单独成规则）。本条落库仅为待审线索，不得据 |
| 3 | omitofee 上海首店（浦江郊野公园滨江漫步区） | 犬只 | dog | dog | prohibited | LEGAL | statute_or_regulation | 与运营方「允许宠物随主人一同入内」直接冲突。法条为 LEGAL/mandatory，运营方声明为 OPERATOR_PO |
| 4 | omitofee 上海首店（浦江郊野公园滨江漫步区） | 小型犬 / 全犬种 | dog | dog | conditional | OPERATOR_POLICY | external_web_reference | 分区规则需拆分为两个 zone 才能准确表达；本轮先落一条候选并标注需人工细化。 |
| 5 | omitofee 上海首店（浦江郊野公园滨江漫步区） | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | external_web_reference | 来源为媒体报道（needs_verification=true），未取得门店官方页面原文；与 LEGAL 层冲突，交人工 |
| 6 | 上海动物园 | 动物 | other | other | prohibited | OPERATOR_POLICY | official_operator_policy | 来源用词为「动物」（全部动物），非「宠物」/「犬只」。按条例第五十九条动物园特定用途犬只另有国家规定；本条按场所管理方声 |
| 7 | 上海博物馆东馆 | 犬只 | dog | dog | prohibited | LEGAL | statute_or_regulation | LEGAL 层禁入。适用性证据为场所类型与法条列举项的对应，需人工复核。 |
| 8 | 上海博物馆东馆 | 导盲犬 | guide_dog | service_dog | allowed | LEGAL | statute_or_regulation | 同层 LEGAL carve-out；来源用词为「导盲犬」，scope 不做向「全部服务犬」的泛化（ADR-025）。 |
| 9 | 上海博物馆东馆 | 携带宠物者 | ordinary_pet | ordinary_pet | prohibited | OPERATOR_POLICY | official_operator_policy | 场馆自行声明，与 LEGAL 层同向；不得被解读为覆盖 LEGAL。 |
| 10 | 上海新天地朗廷酒店 | 犬只 | dog | dog | prohibited | LEGAL | statute_or_regulation | 与运营方 Pawcation 条款存在明显张力（法条禁止携带犬只进入宾馆）。两者如实并存，OPERATOR_POLICY |
| 11 | 上海新天地朗廷酒店 | 狗狗 | dog | dog | conditional | OPERATOR_POLICY | official_operator_policy | 运营方官方条款，逐字可核；空间范围限于「宠物友好区」。与 LEGAL 层张力见 langham-legal-dog-pr |
| 12 | 上海新天地朗廷酒店 | 宠物 | dog | dog | conditional | OPERATOR_POLICY | official_operator_policy | 结构化条件来自原文「抱紧/装笼/推车」，不得简化为 amenity 备注（§21）。 |
| 13 | 上海新天地朗廷酒店 | 宠物 | dog | dog | conditional | OPERATOR_POLICY | official_operator_policy | 宠物友好区含「凯旋餐厅的室外区域（Al Fresco）」；餐厅属第二十三条第一款列举的「餐饮场所」，室外部分是否落入需人 |
| 14 | 上海苏河湾万象天地 | 犬只 | dog | dog | prohibited | LEGAL | statute_or_regulation | LEGAL 层只作用于 indoor zone；不得外推到室外。 |
| 15 | 上海苏河湾万象天地 | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | external_web_reference | 与 LEGAL 层潜在张力：若室外区域被认定为「商场」的一部分，则 OPERATOR_POLICY 不得放宽 LEGAL |
| 16 | 上海蟠龙天地 | 毛孩子们 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | official_operator_policy | 「覆盖大部分区域」为模糊表述，且街区内含餐饮场所（第二十三条第一款独立列举）。本条不宣称全街区可携宠，交人工细化到 zo |
| 17 | 上海蟠龙天地 | 毛孩子们 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | official_operator_policy | 来源未给出可逐字引用的准入条件；「宠物友好覆盖大部分区域」不构成 ALLOWED 规则，仅作条件性候选。开放式街区/景区 |
| 18 | 上海迪士尼乐园 | 动物（导盲犬除外） | other | other | prohibited | OPERATOR_POLICY | official_operator_policy | 主题乐园不在第二十三条第一款列举清单内 → OPERATOR_POLICY。来源用词「动物」宽于宠物，逐字保留。 |
| 19 | 上海迪士尼乐园 | 导盲犬 | guide_dog | service_dog | conditional | OPERATOR_POLICY | official_operator_policy | 同层 OPERATOR_POLICY carve-out。base scope 为「动物」含导盲犬 → 该 carve- |
| 20 | 世纪公园 | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | government_service | Zone-first：局部开放不得写成 Place 级 ALLOWED（§17）。来源为政府文旅平台转述园方口径，nee |
| 21 | 世纪公园 | 宠物 | ordinary_pet | ordinary_pet | prohibited | OPERATOR_POLICY | government_service | 公园不在《上海市养犬管理条例》第二十三条第一款列举清单内，管理者可自行决定（第二十三条第二款），故记为 OPERATOR |
| 22 | 兴业太古汇 | 犬只 | dog | dog | prohibited | LEGAL | statute_or_regulation |  |
| 23 | 兴业太古汇 | 导盲犬 | guide_dog | service_dog | allowed | LEGAL | statute_or_regulation | 运营方口径为「导盲犬等工作犬」，宽于法条「导盲犬」。本条只按法条原文记录导盲犬；「等工作犬」未取得法条依据，不得写入（A |
| 24 | 兴业太古汇 | 除导盲犬等工作犬以外的其他宠物 | ordinary_pet | ordinary_pet | prohibited | OPERATOR_POLICY | external_web_reference | 来源为「工作犬以外其他宠物」，与存储 scope ordinary_pet 不完全等价，标记 legal_interpr |
| 25 | 前滩太古里 | 犬只 | dog | dog | prohibited | LEGAL | statute_or_regulation |  |
| 26 | 前滩太古里 | 毛孩子 | ordinary_pet | ordinary_pet | prohibited | OPERATOR_POLICY | external_web_reference | 与存量官方《宠物友好》页口径（室内需物业同意）方向一致但更严；两者并存交人工裁决哪一版为 current。来源 need |
| 27 | 前滩太古里 | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | external_web_reference | 室外区域与存量官方页口径一致。LEGAL 层仅作用于 indoor zone。 |
| 28 | 港汇恒隆广场 | 犬只 | dog | dog | prohibited | LEGAL | statute_or_regulation |  |
| 29 | 港汇恒隆广场 | 除导盲犬等工作犬以外的其他宠物 | ordinary_pet | ordinary_pet | prohibited | OPERATOR_POLICY | external_web_reference | 存量候选基于解放日报 2025 年报道；本条为 2026-03 更新口径，可能构成 supersede 关系，是否取代由 |
| 30 | 西岸梦中心（Gate M） | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | external_web_reference | 管理方明确「没有统一要求和规定」。此场所-分区应落在 PARTIALLY_ANSWERABLE / UNKNOWN 而非 |
| 31 | 西岸梦中心（Gate M） | 宠物 | ordinary_pet | ordinary_pet | conditional | OPERATOR_POLICY | external_web_reference | 户外开放空间不在第二十三条第一款列举清单内（非商场室内），管理者可自行决定；来源为客服口头回应（needs_verifi |
