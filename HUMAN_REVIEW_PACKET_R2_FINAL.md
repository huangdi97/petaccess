# HUMAN_REVIEW_PACKET_R2_FINAL.md

> GOV-01 最终签署包（R2-FINAL）· ADR-025 源忠实 scope / ADR-028 复合词拆分
> 取代 `HUMAN_REVIEW_PACKET_R2.md`（R2 与更早的 R1）
> 机器登记表：`docs/reality_audit/review_decisions_r2_final.json`（共 36 条）
> **本包直接从数据库生成**，与发布工具实际消费的数据同源，不存在登记表与库漂移。

## 0. 纪律（不可协商）

1. **AI 不做最终裁决**（ADR-005 / Master Goal §0.9）。本包只提供事实与建议。
2. `final_decision` / `reviewer` / `reviewed_at` **全部保持空白**，由具名人类评审员填写。
3. 未获签署，任何候选不得 APPROVED，更不得 Publish。
4. 弱证据（`search_snippet` / `social_lead`）不得 APPROVED（ADR-021）。
5. 来源写「导盲犬」只能是 `guide_dog`；写「军警犬」拆为 `police_dog` +
   `military_working_dog`，**不得**扩张到其他 working dog（ADR-028）。
6. 本包**不执行发布**。

## 1. 建议分布

| 建议 | 条数 |
|---|---|
| `RECOMMEND_REJECT` | **3** |
| `RECOMMEND_HOLD` | **0** |
| `RECOMMEND_APPROVE` | **33** |
| **合计** | **36** |

### 1.1 上海图书馆复合词拆分（ADR-028）

来源原文：`请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。`

| rule_id | source_scope_exact（原话） | normalized scope | normalization_type |
|---|---|---|---|
| `lib-sd-op-guide` | 导盲犬 | guide_dog | `exact` |
| `lib-sd-op-military` | 军警犬 | military_working_dog | `compound_term_split` |
| `lib-sd-op-police` | 军警犬 | police_dog | `compound_term_split` |

> 「军警犬」未在原文中区分军犬/警犬，故 `source_scope_exact`
> **原样保留「军警犬」**，
> 由两行分别承载 `police_dog` 与 `military_working_dog`；两行的并集恰为「军警犬」的
> 含义，且**不包含**任何其他 working dog（见 `animal_scope.COMPOUND_TERM_SPLIT_MEANINGS`）。

### 1.2 fp-sd-op：运营方原始来源

> 检索状态：**FOUND**

| 项 | 内容 |
|---|---|
| 已检索渠道 | 场所官网 / 品牌官网（fairmont.com 官方 guest-services 页，中英双语） |
| 已检索渠道 | 雅高/费尔蒙官方公众号与新闻稿 |
| 已检索渠道 | 管理方（锦江/费尔蒙联合管理方）公开规则页 |
| 已检索渠道 | 运营方公开答复（客服/社交平台官方账号） |
| 一手来源（中文页） | https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html |
| 一手来源（英文页） | https://www.fairmont.com/en/hotels/shanghai/fairmont-peace-hotel/guest-services.html |
| 原文引文（zh） | > 上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。 |
| 原文引文（en） | > Fairmont Peace Hotel does not allow pets. Seeing-eye dogs are always welcome and exempt of charges and restrictions. |
| content_hash | `38aba307ec8e953a0b1e8f2c8d3ff801fe96044a605f6a69b09a2f0155c5030d` （`sha256(captured_excerpt)`，**可重建**） |
| 首次接入 | 2026-09-13T06:17:24Z · scripts/evidence_repair_r2.py（该候选自 09-13 起即挂在一手来源上，非本轮新建） |
| 本轮复核 | 2026-09-15 实时重读该页面，逐字一致 |
| 处置 | **状态修正**：「fp-sd-op 只有 OTA 聚合页证据」这一前提已**不再成立**——该候选自 2026-09-13 起即由 `scripts/evidence_repair_r2.py` 挂到fairmont.com 运营方一手页面；本轮对该页做了实时复核，逐字一致且 `content_hash` 可重建（见下）。因此本轮**未新建证据链**，只新增了按来源原话正确建模的候选 `fp-sd-op-firstparty`（guide_dog / exact）。旧行 `fp-sd-op` 仍建议 REJECT，原因是它把同一句话建模为粗粒度 `service_dog`（源未证成的泛化），而非因为缺少一手来源。 |

## 2. 逐条

### FINAL-01 · `mn-outdoor-media` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`ed79071d-d052-46b4-a216-dc789aae4128`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`）· zone：`outdoor_seating`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文））
- **Source URL**：https://www.cbndata.com/information/255703
- **关键原文引文**：> Manner咖啡全国首家宠物友好店落地凯德虹口商业中心，设置宠物户外区域
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_REJECT**
- **recommendation reason**：REJECT_CURRENT_CLAIM
- **reject reason codes**：`PLACE_ATTRIBUTION_ERROR`, `INSUFFICIENT_PLACE_ZONE_EVIDENCE`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-02 · `fp-sd-op` — 和平饭店（费尔蒙）

- **candidate_id**：`7efddba6-7c42-4013-8918-bedbb996d702`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`whole_hotel`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：service_dog
- **subject_scope_normalized（精确 scope）**：`—`
- **normalization_type**：`legal_interpretation_required`（需法律解释（当前无法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.booking.com/hotel/cn/peace-hotel.html
- **关键原文引文**：> 上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_REJECT**
- **recommendation reason**：SUPERSEDED_BY_SOURCE_FAITHFUL_ROW
- **reject reason codes**：`SUPERSEDED_BY_SOURCE_FAITHFUL_ROW`, `SCOPE_NORMALIZATION_MISSING`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-03 · `gh-outdoor-keep` — 港汇恒隆广场

- **candidate_id**：`887f21ba-e548-457b-a3dd-30ea806d988e`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`outdoor`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文））
- **Source URL**：https://www.jfdaily.com/news/detail?id=1079860
- **关键原文引文**：> 港汇恒隆广场不再允许宠物进入商场室内区域，户外街区保留宠物通行
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_REJECT**
- **recommendation reason**：REJECT_CURRENT_CLAIM
- **reject reason codes**：`INSUFFICIENT_PLACE_ZONE_EVIDENCE`, `LEGAL_SCOPE_CONFLICT`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-04 · `mn-legal-dog` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`c2b179b9-77bf-433a-9219-5a406c42d5c7`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-05 · `mn-sd-legal` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`52936479-c385-4279-814e-aa7fe8ab0a42`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-06 · `lib-legal-dog` — 上海图书馆东馆

- **candidate_id**：`49f2894e-2eae-4f57-bc97-f5ab7e0e0ba3`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`whole_building`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-07 · `lib-pets-op` — 上海图书馆东馆

- **candidate_id**：`330abc76-b6e2-402f-91b1-47596bd95965`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`whole_building`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.library.sh.cn/guide/xuzhi
- **关键原文引文**：> 请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-08 · `lib-sd-legal` — 上海图书馆东馆

- **candidate_id**：`caa28a93-94e9-4643-b6c1-bbd5d77c3ecc`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-09 · `lib-sd-op-guide` — 上海图书馆东馆

- **candidate_id**：`76d0dfc3-64ae-4d2b-a152-18ff8ebed588`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`whole_building`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **carve_out_of（但书所属基础规则）**：lib-pets-op（读者须知：猫、狗禁入）+ lib-legal-dog（条例禁入）
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.library.sh.cn/guide/xuzhi
- **关键原文引文**：> 请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-10 · `lib-sd-op-military` — 上海图书馆东馆

- **candidate_id**：`21578527-5b09-4d53-b868-512c3603b83f`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`whole_building`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：军警犬
- **subject_scope_normalized（精确 scope）**：`military_working_dog`
- **normalization_type**：`compound_term_split`（复合词穷尽拆分（具备法律效力，成员集固定））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`any_handler`
- **carve_out_of（但书所属基础规则）**：lib-pets-op（读者须知：猫、狗禁入）
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.library.sh.cn/guide/xuzhi
- **关键原文引文**：> 请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-11 · `lib-sd-op-police` — 上海图书馆东馆

- **candidate_id**：`81168603-f74a-4130-8fd7-c09a645a4840`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`whole_building`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：军警犬
- **subject_scope_normalized（精确 scope）**：`police_dog`
- **normalization_type**：`compound_term_split`（复合词穷尽拆分（具备法律效力，成员集固定））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`any_handler`
- **carve_out_of（但书所属基础规则）**：lib-pets-op（读者须知：猫、狗禁入）
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.library.sh.cn/guide/xuzhi
- **关键原文引文**：> 请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-12 · `dl-legal-dog` — 上海迪士尼乐园

- **candidate_id**：`f5a8d87f-2d2a-4c1a-a018-b319cc9e580f`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`whole_park`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-13 · `dl-pet-ban` — 上海迪士尼乐园

- **candidate_id**：`cfe82cd4-4156-4daa-9ce2-3fdd5f5797fb`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`whole_park`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/
- **关键原文引文**：> 动物（导盲犬除外）。导盲犬须时刻栓有系绳并在主人的看管下。部分游乐项目也可能不允许导盲犬进入。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-14 · `dl-sd-legal` — 上海迪士尼乐园

- **candidate_id**：`393c6b89-ea48-451f-aa93-9fba89ce215f`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-15 · `dl-sd-op` — 上海迪士尼乐园

- **candidate_id**：`f799a74b-1f7e-49fb-bc4f-6281838877f0`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`whole_park`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/
- **关键原文引文**：> 动物（导盲犬除外）。导盲犬须时刻栓有系绳并在主人的看管下。部分游乐项目也可能不允许导盲犬进入。
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-16 · `qt-indoor-legal` — 前滩太古里

- **candidate_id**：`8151db71-3622-429d-81bc-0a0212f23290`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-17 · `qt-indoor-op` — 前滩太古里

- **candidate_id**：`93fdbdf9-4855-45f8-8bd9-8af86715f748`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.taikooliqiantan.com/detail/58.html
- **关键原文引文**：> 您的宠物仅能在前滩太古里户外开放区域，或商场或商场物业不时指定的室外特定范围区域内活动。未经商场或商场物业同意，您的宠物不得进入商场室内空间活动。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-18 · `qt-outdoor-op` — 前滩太古里

- **candidate_id**：`100d76af-c766-494d-8c25-2e29e2214b71`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`outdoor_open`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.taikooliqiantan.com/detail/58.html
- **关键原文引文**：> 您的宠物仅能在前滩太古里户外开放区域，或商场或商场物业不时指定的室外特定范围区域内活动。未经商场或商场物业同意，您的宠物不得进入商场室内空间活动。
- **conditions**：leash_required、vaccination_required、max_count
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-19 · `qt-sd-legal` — 前滩太古里

- **candidate_id**：`958d4d4c-6cd5-467e-9bc4-5eae2f67630e`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-20 · `qt-sd-op` — 前滩太古里

- **candidate_id**：`1249b621-1186-4366-a538-db04a6731fec`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：除导盲犬外
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.taikooliqiantan.com/detail/58.html
- **关键原文引文**：> 本须知适用于除导盲犬以外的所有宠物，导盲犬不受本须知的限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-21 · `fp-legal-dog` — 和平饭店（费尔蒙）

- **candidate_id**：`c8a3f92b-27eb-443e-bc0e-083458158582`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`whole_hotel`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-22 · `fp-pets-op` — 和平饭店（费尔蒙）

- **candidate_id**：`4c7aba30-a7e3-4ad7-88d7-61a0ba255f27`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`whole_hotel`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.booking.com/hotel/cn/peace-hotel.html
- **关键原文引文**：> 上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-23 · `fp-sd-legal` — 和平饭店（费尔蒙）

- **candidate_id**：`e94d2259-7f77-4bb5-a81c-c5ac5bc81239`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-24 · `fp-sd-op-firstparty` — 和平饭店（费尔蒙）

- **candidate_id**：`0de7771a-d461-4f86-8190-dac0604b9970`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`whole_hotel`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **carve_out_of（但书所属基础规则）**：该场所自身「禁止宠物」政策的但书（同一运营方一手来源）
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html
- **关键原文引文**：> 上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-25 · `dj-pilot` — 大吉路公园

- **candidate_id**：`70cc7579-1764-4177-82b5-fd2d5b255b37`
- **place**：大吉路公园（`dj-daji-park`）· zone：`whole_park`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission`
- **holder_scope**：`—`
- **RuleLayer**：`TEMPORARY_POLICY`（临时/事件政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **关键原文引文**：> 当天起，黄浦区新增大吉路公园、静谧花园、广场公园黄浦段H6区域作为宠物可入园试点区域
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-26 · `gc-h6-pilot` — 广场公园（黄浦段）

- **candidate_id**：`8f98fd01-9a1a-4d64-b354-01632d7bdbcd`
- **place**：广场公园（黄浦段）（`gc-huangpu-sect`）· zone：`h6_pet_area`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission`
- **holder_scope**：`—`
- **RuleLayer**：`TEMPORARY_POLICY`（临时/事件政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **关键原文引文**：> 9月1日，市绿化和市容管理局《关于加强本市公园绿地开放管理的指导意见》施行。当天起，黄浦区新增大吉路公园、静谧花园、广场公园黄浦段H6区域作为宠物可入园试点区域
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-27 · `gc-other-keep` — 广场公园（黄浦段）

- **candidate_id**：`ffb804af-c271-443f-a07a-0fb3b5db5a87`
- **place**：广场公园（黄浦段）（`gc-huangpu-sect`）· zone：`other_areas`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **关键原文引文**：> 目前这3个地方都属于试点，我们在现场张贴了试点公告，待试点结束后，将根据实际情况形成正式的规定。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-28 · `xm-indoor-new` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`9c8b4b26-a2cb-4efd-b188-aeee3a194951`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`secondary_reputable`（可靠二手（权威媒体直抓））
- **Source URL**：None
- **关键原文引文**：> 为此我们已向顾客本人表达了诚挚的歉意，并着手进行了改进，不在该店内继续设置宠物区域。……携宠顾客需在店外宠物友好区落座。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-29 · `xm-legal-dog` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`6fc38502-85c7-4d7e-8a24-56fd5cc68e8a`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-30 · `xm-outdoor-media` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`fb003b3a-3583-484b-b16f-7a6f3a1b71d0`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`outdoor_pet_area`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`secondary_reputable`（可靠二手（权威媒体直抓））
- **Source URL**：None
- **关键原文引文**：> 为此我们已向顾客本人表达了诚挚的歉意，并着手进行了改进，不在该店内继续设置宠物区域。……携宠顾客需在店外宠物友好区落座。
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-31 · `xm-sd-legal` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`6bf5128a-17ad-4a2f-83e5-eabecc7afb9f`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-32 · `sb-legal-dog` — 星巴克臻选上海烘焙工坊

- **candidate_id**：`1a97f24e-3cd0-445c-804d-741be34a0dad`
- **place**：星巴克臻选上海烘焙工坊（`sb-roastery`）· zone：`whole_store`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-33 · `sb-sd-legal` — 星巴克臻选上海烘焙工坊

- **candidate_id**：`b8cffbee-855a-4754-ad84-b01db0351ea3`
- **place**：星巴克臻选上海烘焙工坊（`sb-roastery`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-34 · `gh-indoor-new` — 港汇恒隆广场

- **candidate_id**：`73448553-cdfa-44db-8265-cb45dd325687`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`secondary_reputable`（可靠二手（权威媒体直抓））
- **Source URL**：https://www.jfdaily.com/news/detail?id=1079860
- **关键原文引文**：> 比如港汇恒隆广场、兴业太古汇自今年2月起正式实施全新宠物管理规定，明确禁止除导盲犬等工作犬以外的其他宠物进入商场室内公共区域，全面撤除“宠物友好”相关标识
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-35 · `gh-legal-dog` — 港汇恒隆广场

- **candidate_id**：`70d10467-a771-4331-bc3e-444eac424df2`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-36 · `gh-sd-legal` — 港汇恒隆广场

- **candidate_id**：`d91706de-9447-4b3d-8977-fbfe08760c7e`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation（本包重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

---

## 3. 签署与后续

1. 在 `HUMAN_REVIEW_DECISIONS_R2_FINAL.json` 填 `reviewer`（具名）、
   `reviewed_at`（ISO 8601）与逐条 `final_decision`。
2. 回填机器登记表 `docs/reality_audit/review_decisions_r2_final.json`。
3. 校验：`python scripts/publish_reviewed_r1.py --dry-run`（自动读取最终登记表）应返回 `signed=true`。
4. **发布后**：图书馆的但书（carve-out）需要以 `rule_exception` 形式挂到已发布的基础规则上
   （`rule_exception.rule_id` 外键指向 `access_rule`，故必须在基础规则发布之后创建）。
   本包不执行该步骤，仅提示顺序。

