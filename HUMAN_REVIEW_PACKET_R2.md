# HUMAN_REVIEW_PACKET_R2.md

> GOV-01 支撑材料 · **R2**（ADR-025 源忠实 scope）
> 取代：`HUMAN_REVIEW_PACKET_R1.md`（R1 的 AI 建议建立在已被撤回的
> `service_dog` 泛化之上，**未被继承**，全部重新计算）
> 机器登记表：`docs/reality_audit/review_decisions_r2.json`（共 33 条）

## 0. 纪律（不可协商）

1. **AI 不做最终裁决**（ADR-005 / Master Goal §0.9）。本包只提供事实与建议。
2. 所有 `final_decision` / `reviewer` / `reviewed_at` **保持空白**，由具名人类评审员填写。
3. 未获签署，任何候选不得 APPROVED，更不得 Publish。
4. 弱证据（`search_snippet` / `social_lead`）不得 APPROVED（ADR-021）。
5. **ADR-025**：来源写「导盲犬」就只能是 `guide_dog`；写成 `service_dog` 属
   本体推断，不具法律效力，已在本轮全部修正。
6. 本包**不执行发布**。

## 1. 摘要

| 建议 | 条数 |
|---|---|
| `RECOMMEND_REJECT` | **2** |
| `RECOMMEND_HOLD` | **2** |
| `RECOMMEND_APPROVE` | **29** |
| **合计** | **33** |

## 2. 逐条

### R2-01 · `mn-outdoor-media` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`ed79071d-d052-46b4-a216-dc789aae4128`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`）· zone：`outdoor_seating`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文））
- **Source URL**：https://www.cbndata.com/information/255703
- **conditions**：需牵引
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_REJECT`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_REJECT**
- **recommendation reason**：REJECT_CURRENT_CLAIM
- **reject reason codes**：`PLACE_ATTRIBUTION_ERROR`, `INSUFFICIENT_PLACE_ZONE_EVIDENCE`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-02 · `gh-outdoor-keep` — 港汇恒隆广场

- **candidate_id**：`887f21ba-e548-457b-a3dd-30ea806d988e`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`outdoor`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文））
- **Source URL**：https://www.jfdaily.com/news/detail?id=1079860
- **conditions**：需牵引
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_HOLD`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_REJECT**
- **recommendation reason**：REJECT_CURRENT_CLAIM
- **reject reason codes**：`INSUFFICIENT_PLACE_ZONE_EVIDENCE`, `LEGAL_SCOPE_CONFLICT`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-03 · `lib-sd-op` — 上海图书馆东馆

- **candidate_id**：`76d0dfc3-64ae-4d2b-a152-18ff8ebed588`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`whole_building`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬、军警犬例外
- **subject_scope_normalized（精确 scope）**：—
- **normalization_type**：`legal_interpretation_required`（需法律解释（当前无法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.library.sh.cn/guide/xuzhi
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_HOLD**
- **recommendation reason**：SCOPE_REVIEW_REQUIRED
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-04 · `fp-sd-op` — 和平饭店（费尔蒙）

- **candidate_id**：`7efddba6-7c42-4013-8918-bedbb996d702`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`whole_hotel`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：（来源未陈述）
- **subject_scope_normalized（精确 scope）**：—
- **normalization_type**：`legal_interpretation_required`（需法律解释（当前无法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.booking.com/hotel/cn/peace-hotel.html
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_HOLD**
- **recommendation reason**：SCOPE_REVIEW_REQUIRED
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-05 · `mn-legal-dog` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`c2b179b9-77bf-433a-9219-5a406c42d5c7`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-06 · `mn-sd-legal` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`52936479-c385-4279-814e-aa7fe8ab0a42`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：guide_dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE_WITH_NOTE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-07 · `lib-legal-dog` — 上海图书馆东馆

- **candidate_id**：`49f2894e-2eae-4f57-bc97-f5ab7e0e0ba3`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`whole_building`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-08 · `lib-pets-op` — 上海图书馆东馆

- **candidate_id**：`330abc76-b6e2-402f-91b1-47596bd95965`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`whole_building`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.library.sh.cn/guide/xuzhi
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-09 · `lib-sd-legal` — 上海图书馆东馆

- **candidate_id**：`caa28a93-94e9-4643-b6c1-bbd5d77c3ecc`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：guide_dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE_WITH_NOTE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-10 · `dl-legal-dog` — 上海迪士尼乐园

- **candidate_id**：`f5a8d87f-2d2a-4c1a-a018-b319cc9e580f`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`whole_park`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_HOLD`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-11 · `dl-pet-ban` — 上海迪士尼乐园

- **candidate_id**：`cfe82cd4-4156-4daa-9ce2-3fdd5f5797fb`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`whole_park`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-12 · `dl-sd-legal` — 上海迪士尼乐园

- **candidate_id**：`393c6b89-ea48-451f-aa93-9fba89ce215f`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：guide_dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE_WITH_NOTE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-13 · `dl-sd-op` — 上海迪士尼乐园

- **candidate_id**：`f799a74b-1f7e-49fb-bc4f-6281838877f0`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`whole_park`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：guide_dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/
- **conditions**：需牵引
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-14 · `qt-indoor-legal` — 前滩太古里

- **candidate_id**：`8151db71-3622-429d-81bc-0a0212f23290`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-15 · `qt-indoor-op` — 前滩太古里

- **candidate_id**：`93fdbdf9-4855-45f8-8bd9-8af86715f748`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.taikooliqiantan.com/detail/58.html
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-16 · `qt-outdoor-op` — 前滩太古里

- **candidate_id**：`100d76af-c766-494d-8c25-2e29e2214b71`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`outdoor_open`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.taikooliqiantan.com/detail/58.html
- **conditions**：需牵引、需免疫证明、数量上限（1）
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-17 · `qt-sd-legal` — 前滩太古里

- **candidate_id**：`958d4d4c-6cd5-467e-9bc4-5eae2f67630e`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：guide_dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE_WITH_NOTE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-18 · `qt-sd-op` — 前滩太古里

- **candidate_id**：`1249b621-1186-4366-a538-db04a6731fec`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：除导盲犬外
- **subject_scope_normalized（精确 scope）**：guide_dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.taikooliqiantan.com/detail/58.html
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-19 · `fp-legal-dog` — 和平饭店（费尔蒙）

- **candidate_id**：`c8a3f92b-27eb-443e-bc0e-083458158582`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`whole_hotel`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-20 · `fp-pets-op` — 和平饭店（费尔蒙）

- **candidate_id**：`4c7aba30-a7e3-4ad7-88d7-61a0ba255f27`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`whole_hotel`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.booking.com/hotel/cn/peace-hotel.html
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-21 · `fp-sd-legal` — 和平饭店（费尔蒙）

- **candidate_id**：`e94d2259-7f77-4bb5-a81c-c5ac5bc81239`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：guide_dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE_WITH_NOTE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-22 · `dj-pilot` — 大吉路公园

- **candidate_id**：`70cc7579-1764-4177-82b5-fd2d5b255b37`
- **place**：大吉路公园（`dj-daji-park`）· zone：`whole_park`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`TEMPORARY_POLICY`（临时/事件政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **conditions**：需牵引
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-23 · `gc-h6-pilot` — 广场公园（黄浦段）

- **candidate_id**：`8f98fd01-9a1a-4d64-b354-01632d7bdbcd`
- **place**：广场公园（黄浦段）（`gc-huangpu-sect`）· zone：`h6_pet_area`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`TEMPORARY_POLICY`（临时/事件政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **conditions**：需牵引
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-24 · `gc-other-keep` — 广场公园（黄浦段）

- **candidate_id**：`ffb804af-c271-443f-a07a-0fb3b5db5a87`
- **place**：广场公园（黄浦段）（`gc-huangpu-sect`）· zone：`other_areas`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_HOLD`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-25 · `xm-indoor-new` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`9c8b4b26-a2cb-4efd-b188-aeee3a194951`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`secondary_reputable`（可靠二手（权威媒体直抓））
- **Source URL**：None
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-26 · `xm-legal-dog` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`6fc38502-85c7-4d7e-8a24-56fd5cc68e8a`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-27 · `xm-outdoor-media` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`fb003b3a-3583-484b-b16f-7a6f3a1b71d0`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`outdoor_pet_area`
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`secondary_reputable`（可靠二手（权威媒体直抓））
- **Source URL**：None
- **conditions**：需牵引
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-28 · `xm-sd-legal` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`6bf5128a-17ad-4a2f-83e5-eabecc7afb9f`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：guide_dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE_WITH_NOTE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-29 · `sb-legal-dog` — 星巴克臻选上海烘焙工坊

- **candidate_id**：`1a97f24e-3cd0-445c-804d-741be34a0dad`
- **place**：星巴克臻选上海烘焙工坊（`sb-roastery`）· zone：`whole_store`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-30 · `sb-sd-legal` — 星巴克臻选上海烘焙工坊

- **candidate_id**：`b8cffbee-855a-4754-ad84-b01db0351ea3`
- **place**：星巴克臻选上海烘焙工坊（`sb-roastery`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：guide_dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE_WITH_NOTE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-31 · `gh-indoor-new` — 港汇恒隆广场

- **candidate_id**：`73448553-cdfa-44db-8265-cb45dd325687`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：ordinary_pet
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策）
- **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`secondary_reputable`（可靠二手（权威媒体直抓））
- **Source URL**：https://www.jfdaily.com/news/detail?id=1079860
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-32 · `gh-legal-dog` — 港汇恒隆广场

- **candidate_id**：`70d10467-a771-4331-bc3e-444eac424df2`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`indoor`
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—`
- **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### R2-33 · `gh-sd-legal` — 港汇恒隆广场

- **candidate_id**：`d91706de-9447-4b3d-8977-fbfe08760c7e`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`—`
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：guide_dog
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition`
- **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规）
- **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字））
- **Source URL**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **conditions**：无
- **R1 建议（仅供参考，已被取代）**：`RECOMMEND_APPROVE_WITH_NOTE`
- **AI recommendation（R2，重新计算）**：**RECOMMEND_APPROVE**
- **recommendation reason**：SOURCE_SCOPE_EXACT
- **final_decision**：`________`  ← 留空，由具名评审员填写

---

## 3. 签署

1. 在 `HUMAN_REVIEW_DECISIONS_R2.json` 填 `reviewer` / `reviewed_at` 与逐条
   `final_decision`（`APPROVED` / `APPROVED_WITH_NOTE` / `HOLD` / `REJECTED`）。
2. 回填机器登记表 `docs/reality_audit/review_decisions_r2.json`。
3. 校验：`python scripts/publish_reviewed_r1.py --dry-run`（自动读取 R2 登记表）
   应返回 `signed=true` 且「登记表 ↔ 库」一致性校验通过。

