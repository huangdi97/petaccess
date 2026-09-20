# WAVE02_HUMAN_REVIEW_PACKET — 人工复核包（EXP-R1-W02-REVIEW-R1）

- expansion_run_id: `EXP-R1-W02-20260919`
- review_revision: `EXP-R1-W02-REVIEW-R1`
- generated_at: 2026-09-20T05:42:34.102699+00:00
- 生成方式：由 `scripts/wave02_review_packet.py` 从生产库与证据文件派生，非手写

> **本文件不含任何人工决策。** 决策字段为空白，须由人工复核人填写。
> 机器只负责把材料摆到复核人面前，不负责替复核人做决定（§3, §42-§45）。

## 1. 复核范围

- 候选规则：20 条，全部 `REVIEW_PENDING`
- 复核版本：`EXP-R1-W02-REVIEW-R1`
- 决策登记表：`docs/expansion/review_decisions_expansion_r1_wave02.json`

## 2. 复核人须知

1. 每条候选必须给出 `final_decision`：APPROVED / HOLD / REJECTED 之一。
2. `final_decision` 与 `reviewer`、`decided_at` 必须同时填写；缺一即视为无效。
3. 不得批注「交由系统后续自动决定」。
4. 批准后仍走独立发布批次流程，不在本轮自动执行。
5. `动物` 拆分行（dog/cat/other）是同一个来源术语的声明拆分，应成组审阅。

## 3. 逐条材料（按场所分组）

### 上海世博文化公园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 条件 | 说明 |
|---|---|---|---|---|---|---|---|---|
| 7774a487 | 动物 | dog | dog | 禁止 | 运营层 | 声明拆分 | - | 同上述；本条仅 dog 子集。后滩滨江区域与狗GO乐园的例外待人工核验。 |
| afe409b1 | 动物 | other | other | 禁止 | 运营层 | 声明拆分 | - | 来源原文「动物」；本条为已声明拆分（compound_term_split）的 other 成员，未建模动物保持 UNKNOWN（不得自动 ALLOWED）。 |
| f80c6071 | 动物 | cat | cat | 禁止 | 运营层 | 声明拆分 | - | 来源原文「动物」；本条为已声明拆分（compound_term_split）的 cat 成员，未建模动物保持 UNKNOWN（不得自动 ALLOWED）。 |

### 上海植物园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 条件 | 说明 |
|---|---|---|---|---|---|---|---|---|
| 4b4b4e07 | 动物 | cat | cat | 禁止 | 运营层 | 声明拆分 | - | 来源原文「动物」；本条为已声明拆分（compound_term_split）的 cat 成员，未建模动物保持 UNKNOWN（不得自动 ALLOWED）。 |
| 630e1c0d | 动物 | other | other | 禁止 | 运营层 | 声明拆分 | - | 来源原文「动物」；本条为已声明拆分（compound_term_split）的 other 成员，未建模动物保持 UNKNOWN（不得自动 ALLOWED）。 |
| 97d564fa | 动物 | dog | dog | 禁止 | 运营层 | 声明拆分 | - | 来源原文覆盖「动物」全域；本条仅表意 ontology 可表达子集 dog（compound_term_split）。 |

### 上海自然博物馆

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 条件 | 说明 |
|---|---|---|---|---|---|---|---|---|
| 700dcd4d | 宠物 | ordinary_pet | ordinary_pet | 禁止 | 运营层 | exact | - | 官网参观须知原文「请勿携带…宠物等」。来源保真：宠物=ordinary_pet exact；导盲犬/服务犬例外未见原文，不臆造（ADR-030 proviso 仅在 legal provision 成立时适用）。 |

### 上海辰山植物园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 条件 | 说明 |
|---|---|---|---|---|---|---|---|---|
| 81eca767 | 宠物 | ordinary_pet | ordinary_pet | 禁止 | 运营层 | exact | - | 官网《游园指南》页面存在且可达；「禁止携带宠物…入园」句为外部收录的入园须知第九条表述，注明 needs_verification=True（以官网原页逐字核验为准）；本条按普通宠物 exact 表述，不做「动物」全域声 |

### 上海野生动物园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 条件 | 说明 |
|---|---|---|---|---|---|---|---|---|
| 237512f7 | 宠物 | ordinary_pet | ordinary_pet | 禁止 | 运营层 | exact | - | 官网游园指南原文「二、不得携带宠物入园」。与上海动物园（长宁区虹桥路2381号）为不同法人/不同园区的另一场所；本条仅指浦东新区南六公路178号上海野生动物园。 |

### 共青森林公园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 条件 | 说明 |
|---|---|---|---|---|---|---|---|---|
| c111a1a1 | 动物 | dog | dog | 禁止 | 运营层 | 声明拆分 | - | 来源覆盖「动物」全域；本条仅表意 dog 子集。 |
| eba1843a | 动物 | other | other | 禁止 | 运营层 | 声明拆分 | - | 来源原文「动物」；本条为已声明拆分（compound_term_split）的 other 成员，未建模动物保持 UNKNOWN（不得自动 ALLOWED）。 |
| ec883c91 | 动物 | cat | cat | 禁止 | 运营层 | 声明拆分 | - | 来源原文「动物」；本条为已声明拆分（compound_term_split）的 cat 成员，未建模动物保持 UNKNOWN（不得自动 ALLOWED）。 |

### 和平公园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 条件 | 说明 |
|---|---|---|---|---|---|---|---|---|
| 98d2b355 | 犬类 | dog | dog | 有条件允许 | 运营层 | exact | time_windows(每日8:00-20:00); leash_required(True); other_structured_note(刚性牵引绳长度≤1.5m，禁止伸缩绳；肩高≥45cm需佩戴嘴套) | 政府试点公告（2025-09-01 起）原文：限时8:00-20:00、仅犬类/猫类、全程牵引、≤1.5m 刚性牵引绳、禁伸缩绳、大型犬（肩高≥45cm）戴嘴套、禁随地便溺。试点区域为部分区域（pet_area zone |
| da0c270c | 猫类 | cat | cat | 有条件允许 | 运营层 | exact | time_windows(每日8:00-20:00); other_structured_note(牵引用具按公园规定；禁随地便溺；应避让老幼孕及怕宠人群) | 同政府试点公告；猫类允许入园限试点区域与时段。 |

### 昆山公园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 条件 | 说明 |
|---|---|---|---|---|---|---|---|---|
| d5551907 | 犬类 | dog | dog | 有条件允许 | 运营层 | exact | time_windows(每日8:00-20:00); leash_required(True); other_structured_note(刚性牵引绳≤1.5m；肩高≥45cm需嘴套) | 同 2025-09-01 虹口区政府试点公告；昆山公园为试点公园之一。地址按区级公开信息录入四川北路1933号，门牌级人工核验状态=False。 |

### 豫园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 条件 | 说明 |
|---|---|---|---|---|---|---|---|---|
| 5f22e9a1 | 宠物 | ordinary_pet | ordinary_pet | 禁止 | 运营层 | exact | - | 官网游园须知原文「宠物（符合规定的导盲犬除外）」。base 禁止普通宠物入园；导盲犬为明示同层例外（见 yy-guide-dog 候选），不得泛化为所有服务犬（ADR-025/031）。 |
| 91970069 | 导盲犬 | guide_dog | service_dog | 有条件允许 | 运营层 | exact | other_structured_note(符合规定：持有效导盲犬身份证明及在役使用) | 明示例外仅限「符合规定的导盲犬」。guide_dog 例外不得推广至 hearing/assistance/other service dog（ADR-025 来源保真）；holder_scope=person_with |

### 顾村公园

| candidate | 来源用词 | 归一化主体 | scope | effect | layer | normalization | 条件 | 说明 |
|---|---|---|---|---|---|---|---|---|
| 36f6382f | 动物 | dog | dog | 禁止 | 运营层 | 声明拆分 | - | 来源（本地宝 2025-03-11 转述顾村公园游园须知）原文「未经许可，不得携带各种动物入园」；本条为已声明拆分（compound_term_split）的 dog 成员，未建模动物保持 UNKNOWN。二级来源仅作  |
| b6abed36 | 动物 | other | other | 禁止 | 运营层 | 声明拆分 | - | 来源（本地宝 2025-03-11 转述顾村公园游园须知）原文「未经许可，不得携带各种动物入园」；本条为已声明拆分（compound_term_split）的 other 成员，未建模动物保持 UNKNOWN。二级来源仅 |
| c6c5b74d | 动物 | cat | cat | 禁止 | 运营层 | 声明拆分 | - | 来源（本地宝 2025-03-11 转述顾村公园游园须知）原文「未经许可，不得携带各种动物入园」；本条为已声明拆分（compound_term_split）的 cat 成员，未建模动物保持 UNKNOWN。二级来源仅作  |

## 4. 全部候选一览

| # | 场所 | 来源用词 | 归一化主体 | scope | effect | layer | source_type |
|---|---|---|---|---|---|---|---|
| 1 | 上海世博文化公园 | 动物 | dog | dog | 禁止 | 运营层 | official_operator_policy |
| 2 | 上海世博文化公园 | 动物 | other | other | 禁止 | 运营层 | official_operator_policy |
| 3 | 上海世博文化公园 | 动物 | cat | cat | 禁止 | 运营层 | official_operator_policy |
| 4 | 上海植物园 | 动物 | cat | cat | 禁止 | 运营层 | government_service |
| 5 | 上海植物园 | 动物 | other | other | 禁止 | 运营层 | government_service |
| 6 | 上海植物园 | 动物 | dog | dog | 禁止 | 运营层 | government_service |
| 7 | 上海自然博物馆 | 宠物 | ordinary_pet | ordinary_pet | 禁止 | 运营层 | official_operator_policy |
| 8 | 上海辰山植物园 | 宠物 | ordinary_pet | ordinary_pet | 禁止 | 运营层 | official_operator_policy |
| 9 | 上海野生动物园 | 宠物 | ordinary_pet | ordinary_pet | 禁止 | 运营层 | official_operator_policy |
| 10 | 共青森林公园 | 动物 | dog | dog | 禁止 | 运营层 | official_operator_policy |
| 11 | 共青森林公园 | 动物 | other | other | 禁止 | 运营层 | official_operator_policy |
| 12 | 共青森林公园 | 动物 | cat | cat | 禁止 | 运营层 | official_operator_policy |
| 13 | 和平公园 | 犬类 | dog | dog | 有条件允许 | 运营层 | government_service |
| 14 | 和平公园 | 猫类 | cat | cat | 有条件允许 | 运营层 | government_service |
| 15 | 昆山公园 | 犬类 | dog | dog | 有条件允许 | 运营层 | government_service |
| 16 | 豫园 | 宠物 | ordinary_pet | ordinary_pet | 禁止 | 运营层 | official_operator_policy |
| 17 | 豫园 | 导盲犬 | guide_dog | service_dog | 有条件允许 | 运营层 | official_operator_policy |
| 18 | 顾村公园 | 动物 | dog | dog | 禁止 | 运营层 | external_web_reference |
| 19 | 顾村公园 | 动物 | other | other | 禁止 | 运营层 | external_web_reference |
| 20 | 顾村公园 | 动物 | cat | cat | 禁止 | 运营层 | external_web_reference |

## 5. 监控与新鲜度

| issuer | source_type | url | last_http_status | failure_count | 已哈希 |
|---|---|---|---|---|---|
| 上海世博文化公园官网《游园须知》 | official_operator_policy | https://www.expoculturepark.cn/faq | - | 0 | 未比对 |
| 上海市绿化和市容管理局《上海市公园文明游园守则》（2018版） | government_service | https://www.shanghai.gov.cn/nw12344/20200813/0001-12344_54837.html | - | 0 | 未比对 |
| 上海市虹口区绿化和市容管理局《搭帐篷、带宠物…虹口的公园9月1日起试点》 | government_service | https://www.shhk.gov.cn/xwzx/002014/20250901/e660ce0a-30ac-443c-b8d3-f342a909b4b3.html | - | 0 | 未比对 |
| 上海植物园官网《游园守则》 | official_operator_policy | https://www.shbg.org/sites/zhiwuyuan/InfoContent.aspx?ctgId=2645a2aa-f97c-4e83-ae58-411aad0b1983 | - | 0 | 未比对 |
| 上海自然博物馆官网《参观须知》 | official_operator_policy | https://www.snhm.org.cn/cgfw/cgzx.htm | - | 0 | 未比对 |
| 上海辰山植物园官网《游园指南》 | official_operator_policy | https://www.csnbgsh.cn/sites/chenshan2020/static/zhinan.ashx | - | 0 | 未比对 |
| 上海野生动物园官网《游园指南》 | official_operator_policy | https://www.swap-shendi.com/index.do?guide= | - | 0 | 未比对 |
| 共青森林公园官网《文明游园守则》 | official_operator_policy | https://www.shgqsl.com/sites/gongqingsl/index.ashx | - | 0 | 未比对 |
| 豫园官网《游园须知》 | official_operator_policy | https://www.yugarden.com.cn/Page/ArticleView/notice.html | - | 0 | 未比对 |

