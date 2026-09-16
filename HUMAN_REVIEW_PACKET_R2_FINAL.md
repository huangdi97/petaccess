# HUMAN_REVIEW_PACKET_R2_FINAL.md

> GOV-01 最终签署包（**R2-FINAL-R3**）· ADR-025 源忠实 scope / ADR-028 复合词拆分
> 取代 `HUMAN_REVIEW_PACKET_R2.md`（R2 与更早的 R1）
> 机器登记表：`docs/reality_audit/review_decisions_r2_final.json`（共 37 条）
> **本包逐行直接从数据库证据链生成**，不再引用手工维护的登记表字段，
> 因此不会出现「引文出自 A 页而 URL 写着 B 页」这类自相矛盾。

## 0. 纪律（不可协商）

1. **AI 不做最终裁决**（ADR-005 / Master Goal §0.9）。本包只提供事实与建议。
2. `final_decision` / `reviewer` / `reviewed_at` **全部保持空白**，由具名人类评审员填写。
3. 未获签署，任何候选不得批准，更不得 Publish。
4. 弱证据（`search_snippet` / `social_lead`）不得批准（ADR-021）。
5. 来源写「导盲犬」只能是 `guide_dog`；写「军警犬」拆为 `police_dog` +
   `military_working_dog`，**不得**扩张到其他 working dog（ADR-028）。
6. 本包**不执行发布**。

### 0.1 决策词表（唯一来源：`scripts/human_decisions.py`）

| 值 | 含义 |
|---|---|
| `APPROVED` | 批准 |
| `APPROVED_WITH_NOTE` | 批准（附注意见） |
| `HOLD` | 挂起（证据不足） |
| `REJECTED` | 拒绝 |

> 速填表、登记表与发布工具共用同一词表，**不存在别名**。
> 请勿使用 APPROVE / REJECT 等写法。

## 1. 建议分布

| 建议 | 条数 |
|---|---|
| `RECOMMEND_REJECT` | **5** |
| `RECOMMEND_HOLD` | **9** |
| `RECOMMEND_APPROVE` | **23** |
| **合计** | **37** |

### 1.1 上海图书馆复合词拆分（ADR-028）

来源原文：`请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。`

| rule_id | source_scope_exact（原话） | normalized | normalization_type |
|---|---|---|---|
| `lib-sd-op-military` | 军警犬 | military_working_dog | `compound_term_split` |
| `lib-sd-op-police` | 军警犬 | police_dog | `compound_term_split` |
| `lib-sd-op-guide` | 导盲犬 | guide_dog | `exact` |

> 「军警犬」未在原文中区分军犬/警犬，故 `source_scope_exact` **原样保留「军警犬」**，
> 由两行分别承载 `police_dog` 与 `military_working_dog`；两行并集恰为「军警犬」，
> 且**不包含**任何其他 working dog。

### 1.2 和平饭店：一手来源到底挂在哪（修 §2 缺陷）

审计发现的自相矛盾及其根因：

- **逐条里的 `fp-sd-op` 显示 booking.com**：该行 `source.source_url` 确实仍指向
  OTA 聚合页（`directness=tertiary`、`issuer_verification=unverified`、
  `needs_verification=True`）。
- **前文却说已挂 fairmont.com**：一手来源自 2026-09-13 起就存在并被
  `fp-sd-op-firstparty` 正确引用；当时的生成器把 `source_url` 取手工登记表、
  把引文取数据库，两者拼在一行里就自相矛盾了。
- **`fp-pets-op` 声称 primary_direct**：它的确不配这个等级（源为 OTA），
  本轮的 EvidenceStrength 由**证据链推导**，不再采信登记表自述。

**本轮处置**：生成端一律从证据链读取；两个 OTA 行改为 REJECT
（源非运营方一手、且被同名一手行取代），旧证据**一条未删**。

| 项 | 内容 |
|---|---|
| 一手来源 URL（zh） | https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html |
| 一手 bundle | `d2359c42-da06-4647-92b4-5df0757a4c7c` · content_hash `38aba307ec8e953a…` |
| 共用行 | 基础规则 `fp-pets-op-firstparty`（禁止宠物）· 例外 `fp-sd-op-firstparty`（导盲犬） |
| 实读复核 | 2026-09-15 复核 zh+en 双语页，逐字一致 |
| 被取代的旧行 | `fp-sd-op` / `fp-pets-op`（证据保留，不再作为发布依据） |

> 禁止宠物基础规则与导盲犬例外**共用同一句原文**，因此不需要两条独立证据。

### 1.3 gc-other-keep：改判（修 §3 缺陷）

该行断言「广场公园（黄浦段）其余区域禁止宠物」，但其唯一引文是：

> 目前这3个地方都属于试点，我们在现场张贴了试点公告，待试点结束后，将根据实际情况形成正式的规定。

这句话只证明**试点存在**，不证明公园其余区域禁止宠物——把「未列入试点」
读成「明令禁止」是平台替来源做的推断。
因此由 APPROVE 改判 **RECOMMEND_REJECT**（`CLAIM_NOT_SUPPORTED_BY_QUOTE` + `INSUFFICIENT_PLACE_ZONE_EVIDENCE`）。
若运营方现场公告明确写了「宠物仅限 H6 区域」，请补充该一手取证后重开此行。

### 1.4 迪士尼 LEGAL 投影：适用性必须被证明（修 §4 缺陷）

《上海市养犬管理条例》第二十三条管辖的是**它自己枚举的类别**：

> 办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆

| rule_id | place_type | 对应法条类别 | 适用性状态 | 建议 |
|---|---|---|---|---|
| `dl-legal-dog` | `scenic_area` | — | **NOT_EVIDENCED** | RECOMMEND_HOLD |
| `dl-sd-legal` | `scenic_area` | — | **NOT_EVIDENCED** | RECOMMEND_HOLD |

> 上海迪士尼 `place_type=scenic_area`（景区），**不在上述枚举名单内**。
> 「景区属于文化娱乐场所」是一个法律解释，不是已取证的事实；
> 在缺证据前不得让它承担法定禁止力度。
> 若取得主管部门或司法口径明确将景区纳入「文化娱乐场所」，补充该证据后重开此两行。

同源的 OPERATOR_POLICY 行 `dl-pet-ban` / `dl-sd-op` 不受影响，独立处理。

### 1.5 临时 / 试点政策：必须有期限与复核（修 §5 缺陷）

| rule_id | effective_from | effective_to | open-ended 原因 | last_verified_at | 缺口 | 建议 |
|---|---|---|---|---|---|---|
| `dj-pilot` | 2025-09-01T00:00:00+00:00 | — | — | 2026-09-13 | 缺 effective_to 且未记录 open-ended 原因；缺 last_verified_at（捕获时间不能代替「当前是否仍有效」的复核） | RECOMMEND_HOLD |
| `gc-h6-pilot` | 2025-09-01T00:00:00+00:00 | — | — | 2026-09-13 | 缺 effective_to 且未记录 open-ended 原因；缺 last_verified_at（捕获时间不能代替「当前是否仍有效」的复核） | RECOMMEND_HOLD |

> 这两条来自 2025-09-02 的政府通稿，试点自 2025-09-01 起，
> **来源未标注终止日期**，且本轮未复核至今是否仍在施行。
> 「没写到期」不等于「仍然有效」，因此建议 **HOLD**，
> 待实地/官网复核当前状态后放行。

### 1.6 缺失溯源链的行（修 §6 缺陷）

| rule_id | Source URL | artifact | content_hash | 快照 locator | 建议 |
|---|---|---|---|---|---|
| `fp-pets-op` | https://www.booking.com/hotel/cn/peace-hotel.html | 有 | 有 | — | RECOMMEND_REJECT |
| `fp-sd-op` | https://www.booking.com/hotel/cn/peace-hotel.html | 有 | 有 | — | RECOMMEND_REJECT |
| `gh-indoor-new` | https://www.jfdaily.com/news/detail?id=1079860 | 有 | 有 | — | RECOMMEND_HOLD |
| `xm-indoor-new` | https://tidenews.com.cn/news.html?id=3542194 | 有 | 有 | — | RECOMMEND_HOLD |
| `xm-outdoor-media` | https://tidenews.com.cn/news.html?id=3542194 | 有 | 有 | — | RECOMMEND_HOLD |

**逐行缺口明细**

- `fp-pets-op`：`bundle.license_metadata 为空`
- `fp-sd-op`：`bundle.license_metadata 为空`
- `gh-indoor-new`：`bundle.license_metadata 为空`
- `xm-indoor-new`：`bundle.license_metadata 为空`
- `xm-outdoor-media`：`bundle.license_metadata 为空`

> 这些行过去靠 `EVIDENCE_TRACEABLE` 四个字通过；现在必须真的能指出
> 取证位置、content_hash、快照与 license 三态。补全之前建议 **HOLD**。

### 1.7 RuleException 发布计划（层内绑定 · RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE）

例外**不是**再发一条普通 AccessRule：同一个 zone 里同时存在「禁止」与「允许」两条普通规则，会让求解器面对两条互相冲突的同层规则。
凡本表列为 carve-out 的行，必须在**基础规则发布之后**以 `rule_exception` 形式绑定到已发布的 `access_rule`（`rule_exception.rule_id` 外键）。

**硬原则（下表由同一算法生成，违反即拒绝生成）**

- A. LEGAL 例外只能作用于与其法律依据对应的 **LEGAL** base rule。
- B. OPERATOR_POLICY carve-out **不得**直接 override 更高层的 LEGAL 规则。
- C. 运营方政策写「允许」**不构成**法律禁令的例外。
- D. Resolver precedence 始终保持 **LEGAL > OPERATOR_POLICY**（例外只在自身层内替换 base）。
- E. 每条 RuleException 保留 source / layer / mandatory_level / source_scope_exact / subject_scope_normalized / normalization_type。

| 例外行 | 层 | effect | 精确 scope | 归一化 | 强制级 | 绑定基础规则（层） | base 裁决 | 可执行 | 说明 |
|---|---|---|---|---|---|---|---|---|---|
| `dl-sd-legal` | LEGAL | allowed | `guide_dog` | `exact` | `mandatory` | `dl-legal-dog`（LEGAL） | RECOMMEND_HOLD | ❌ | **本批不发布**：例外自身为 RECOMMEND_HOLD，本批不发布；dl-legal-dog：基础规则 RECOMMEND_HOLD，不可作为已发布例外的基础 |
| `lib-sd-op-military` | OPERATOR_POLICY | allowed | `military_working_dog` | `compound_term_split` | `operator_discretion` | `lib-pets-op`（OPERATOR_POLICY） | RECOMMEND_APPROVE | ❌ | **本批不发布**：例外自身为 RECOMMEND_HOLD，本批不发布 |
| `lib-sd-op-police` | OPERATOR_POLICY | allowed | `police_dog` | `compound_term_split` | `operator_discretion` | `lib-pets-op`（OPERATOR_POLICY） | RECOMMEND_APPROVE | ❌ | **本批不发布**：例外自身为 RECOMMEND_HOLD，本批不发布 |
| `dl-sd-op` | OPERATOR_POLICY | conditional | `guide_dog` | `exact` | `operator_discretion` | `dl-pet-ban`（OPERATOR_POLICY） | RECOMMEND_APPROVE | ✅ | 作为 `rule_exception` 发布 |
| `fp-sd-legal` | LEGAL | allowed | `guide_dog` | `exact` | `mandatory` | `fp-legal-dog`（LEGAL） | RECOMMEND_APPROVE | ✅ | 作为 `rule_exception` 发布 |
| `fp-sd-op-firstparty` | OPERATOR_POLICY | allowed | `guide_dog` | `exact` | `operator_discretion` | `fp-pets-op-firstparty`（OPERATOR_POLICY） | RECOMMEND_APPROVE | ✅ | 作为 `rule_exception` 发布 |
| `gh-sd-legal` | LEGAL | allowed | `guide_dog` | `exact` | `mandatory` | `gh-legal-dog`（LEGAL） | RECOMMEND_APPROVE | ✅ | 作为 `rule_exception` 发布 |
| `lib-sd-legal` | LEGAL | allowed | `guide_dog` | `exact` | `mandatory` | `lib-legal-dog`（LEGAL） | RECOMMEND_APPROVE | ✅ | 作为 `rule_exception` 发布 |
| `lib-sd-op-guide` | OPERATOR_POLICY | allowed | `guide_dog` | `exact` | `operator_discretion` | `lib-pets-op`（OPERATOR_POLICY） | RECOMMEND_APPROVE | ✅ | 作为 `rule_exception` 发布 |
| `mn-sd-legal` | LEGAL | allowed | `guide_dog` | `exact` | `mandatory` | `mn-legal-dog`（LEGAL） | RECOMMEND_APPROVE | ✅ | 作为 `rule_exception` 发布 |
| `qt-sd-legal` | LEGAL | allowed | `guide_dog` | `exact` | `mandatory` | `qt-indoor-legal`（LEGAL） | RECOMMEND_APPROVE | ✅ | 作为 `rule_exception` 发布 |
| `qt-sd-op` | OPERATOR_POLICY | allowed | `guide_dog` | `exact` | `operator_discretion` | `qt-indoor-op`（OPERATOR_POLICY） | RECOMMEND_APPROVE | ✅ | 作为 `rule_exception` 发布 |
| `sb-sd-legal` | LEGAL | allowed | `guide_dog` | `exact` | `mandatory` | `sb-legal-dog`（LEGAL） | RECOMMEND_APPROVE | ✅ | 作为 `rule_exception` 发布 |
| `xm-sd-legal` | LEGAL | allowed | `guide_dog` | `exact` | `mandatory` | `xm-legal-dog`（LEGAL） | RECOMMEND_APPROVE | ✅ | 作为 `rule_exception` 发布 |

**层间隔离核对**

| 检查项 | 结果 |
|---|---|
| 跨层绑定（cross-layer override，实际绑定表内） | **0** |
| HOLD 基础规则收到「可执行例外」 | **0** |
| Legal / Operator 例外分离 | **PASS** |
| 旧算法遗留的跨层绑定（已丢弃，仅记录） | **6**（`lib-sd-op-military`、`lib-sd-op-police`、`dl-sd-op`、`fp-sd-op-firstparty`、`lib-sd-op-guide`、`qt-sd-op`） |
| 例外行分布 | LEGAL 8 条 · OPERATOR_POLICY 6 条 |

> 层内判定口径：LEGAL 例外只绑定**同场所的 LEGAL 禁令**（`dog` 覆盖 `guide_dog`）；OPERATOR_POLICY 豁免只绑定**同一份运营方文件**里的禁令（禁令与豁免出自同一 `source_id`，如「禁止宠物入内。导盲犬可随时进入酒店。」）。跨层绑定一律丢弃并在此计数。

**发布顺序（不可颠倒）**：

1. 先发布基础禁止规则，取得 `access_rule.id`；
2. 再按上表逐条创建 `rule_exception`，把 scope / normalization /
   normative_effect / holder_scope 一并写入
   （否则又是一次 ADR-025 字段在写入时丢失）；
3. 最后校验 resolver：`guide_dog` 命中例外得 allowed，其余命中基础规则得 prohibited，且 LEGAL 禁令不因任何运营方豁免而放宽。

> 本包只给出计划与绑定关系，**不执行**上述任何一步。

## 3. 逐条

### FINAL-01 · `fp-pets-op` — 和平饭店（费尔蒙）

- **candidate_id**：`4c7aba30-a7e3-4ad7-88d7-61a0ba255f27`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`，place_type=`hotel`） · zone：全酒店 · unknown
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文）） · chain directness：`tertiary`（三手（聚合）） · ⚠️ 登记表声称 `primary_direct` 与证据链推导不一致
- **Source issuer**：Booking/Hotels.com/Expedia 聚合展示的运营方宠物政策 · 核验：`unverified`（未核验）
- **Source URL（source.source_url）**：https://www.booking.com/hotel/cn/peace-hotel.html
- **capture locator（bundle.source_url）**：https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html  ⚠️ 与 source 不一致
- **artifact**：id=`1bf60fef-68cd-4c66-85d9-f28562ee37cb` · type=`web_page_text` · content_hash=`38aba307ec8e953a0b1e8f2c8d3ff801fe96044a605f6a69b09a2f0155c5030d`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "place_id": "7f5093f3-1222-4049-af9d-cc5ca4386b54", "note": "R2 修复：原文页直接抓取并核验"}`
- **DataLicense / SourcePolicy**：artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13T06:17:12.884288+00:00` · 缺口：—
- **strength note**：source.directness=tertiary / issuer_verification=unverified / needs_verification=True —— 不代表运营方一手来源
- **provenance 缺口**：`bundle.license_metadata 为空`
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_REJECT**
- **recommendation reason**：SUPERSEDED_BY_FIRST_PARTY_SOURCE
- **reason codes**：`SUPERSEDED_BY_FIRST_PARTY_SOURCE`, `SOURCE_NOT_OPERATOR_OF_RECORD`, `替代行：fp-pets-op-firstparty`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-02 · `fp-sd-op` — 和平饭店（费尔蒙）

- **candidate_id**：`7efddba6-7c42-4013-8918-bedbb996d702`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`，place_type=`hotel`） · zone：全酒店 · unknown
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：service_dog
- **subject_scope_normalized（精确 scope）**：`—`
- **normalization_type**：`legal_interpretation_required`（需法律解释（当前无法律效力））
- **normative_effect**：`—` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文）） · chain directness：`tertiary`（三手（聚合）） · ⚠️ 登记表声称 `primary_direct` 与证据链推导不一致
- **Source issuer**：Booking/Hotels.com/Expedia 聚合展示的运营方宠物政策 · 核验：`unverified`（未核验）
- **Source URL（source.source_url）**：https://www.booking.com/hotel/cn/peace-hotel.html
- **capture locator（bundle.source_url）**：https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html  ⚠️ 与 source 不一致
- **artifact**：id=`1bf60fef-68cd-4c66-85d9-f28562ee37cb` · type=`web_page_text` · content_hash=`38aba307ec8e953a0b1e8f2c8d3ff801fe96044a605f6a69b09a2f0155c5030d`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "place_id": "7f5093f3-1222-4049-af9d-cc5ca4386b54", "note": "R2 修复：原文页直接抓取并核验"}`
- **DataLicense / SourcePolicy**：artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：`fp-pets-op`、`fp-pets-op-firstparty`
- **exception**：需绑定为 `rule_exception` → fp-pets-op；fp-pets-op-firstparty（同层 OPERATOR_POLICY）——不得作为普通 AccessRule 独立发布
- **跨层绑定已丢弃**：`fp-legal-dog` —— 旧算法曾把它指向更高层规则；按原则 B/C/D 丢弃，运营方豁免不得覆盖法规禁令
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13T06:17:12.884288+00:00` · 缺口：—
- **strength note**：source.directness=tertiary / issuer_verification=unverified / needs_verification=True —— 不代表运营方一手来源
- **provenance 缺口**：`bundle.license_metadata 为空`
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_REJECT**
- **recommendation reason**：SUPERSEDED_BY_FIRST_PARTY_SOURCE
- **reason codes**：`SUPERSEDED_BY_FIRST_PARTY_SOURCE`, `SOURCE_NOT_OPERATOR_OF_RECORD`, `替代行：fp-sd-op-firstparty`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-03 · `gc-other-keep` — 广场公园（黄浦段）

- **candidate_id**：`ffb804af-c271-443f-a07a-0fb3b5db5a87`
- **place**：广场公园（黄浦段）（`gc-huangpu-sect`，place_type=`park`） · zone：公园其余区域 · outdoor
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：黄浦区人民政府官网《9月1日起，上海这些公园试点宠物入园》（来源：新闻晨报） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **artifact**：id=`7de10702-8e48-472d-844e-3c71427332cd` · type=`web_page_text` · content_hash=`fb5ef988c3083421edb1914318cad382e33ebfe067beeccd939afa5d4c8878a2`
- **snapshot_ref**：— · availability：`available_online` · spatial：`approximate`
- **关键原文引文**：> 目前这3个地方都属于试点，我们在现场张贴了试点公告，待试点结束后，将根据实际情况形成正式的规定。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "广场公园（黄浦段）", "canonical_address": "上海市黄浦区（金陵中路、西藏南路、延安东路、普安路合围H6区域）", "spatial_precision": "approximate"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：2025-09-01T00:00:00+00:00 → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_REJECT**
- **recommendation reason**：REJECT_CURRENT_CLAIM
- **reason codes**：`CLAIM_NOT_SUPPORTED_BY_QUOTE`, `INSUFFICIENT_PLACE_ZONE_EVIDENCE`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-04 · `gh-outdoor-keep` — 港汇恒隆广场

- **candidate_id**：`887f21ba-e548-457b-a3dd-30ea806d988e`
- **place**：港汇恒隆广场（`gh-grand-gateway`，place_type=`mall`） · zone：户外街区 · outdoor
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文）） · chain directness：`secondary`（二手）
- **Source issuer**：解放日报（运营方室内宠物禁令报道） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.jfdaily.com/news/detail?id=1079860
- **artifact**：id=`a0d16337-bfb6-4612-9a20-a9daf19f82f1` · type=`news_article` · content_hash=`01d26dd79b89a81893b08a0232ebd8c027bec3cb1e4258872a2f9824ca123a00`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 港汇恒隆广场不再允许宠物进入商场室内区域，户外街区保留宠物通行
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "港汇恒隆广场", "canonical_address": "上海市徐汇区虹桥路1号", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=False；artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：2026-02-01T00:00:00+00:00 → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **strength note**：source.directness=secondary / issuer_verification=verified / needs_verification=True —— 不代表运营方一手来源
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_REJECT**
- **recommendation reason**：REJECT_CURRENT_CLAIM
- **reason codes**：`INSUFFICIENT_PLACE_ZONE_EVIDENCE`, `LEGAL_SCOPE_CONFLICT`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-05 · `mn-outdoor-media` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`ed79071d-d052-46b4-a216-dc789aae4128`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`，place_type=`cafe`） · zone：户外宠物区 · outdoor
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文）） · chain directness：`secondary`（二手）
- **Source issuer**：CBNData（Manner 首家宠物友好店报道） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.cbndata.com/information/255703
- **artifact**：id=`ea46a977-1a5e-4dfc-b72f-39d3e65fafd8` · type=`news_article` · content_hash=`45126bafa4f4f0de3f5656cdafae261e426bd2cf84829a416c3d37ba13163fdb`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> Manner咖啡全国首家宠物友好店落地凯德虹口商业中心，设置宠物户外区域
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "Manner咖啡（凯德虹口商业中心店）", "canonical_address": "上海市虹口区西江湾路388号凯德虹口商业中心", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=False；artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **strength note**：source.directness=secondary / issuer_verification=verified / needs_verification=True —— 不代表运营方一手来源
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_REJECT**
- **recommendation reason**：REJECT_CURRENT_CLAIM
- **reason codes**：`PLACE_ATTRIBUTION_ERROR`, `INSUFFICIENT_PLACE_ZONE_EVIDENCE`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-06 · `dj-pilot` — 大吉路公园

- **candidate_id**：`70cc7579-1764-4177-82b5-fd2d5b255b37`
- **place**：大吉路公园（`dj-daji-park`，place_type=`park`） · zone：全园 · outdoor
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission` · **holder_scope**：`—`
- **RuleLayer**：`TEMPORARY_POLICY`（临时/事件政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：黄浦区人民政府官网《9月1日起，上海这些公园试点宠物入园》（来源：新闻晨报） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **artifact**：id=`758b7bce-b4d9-4820-be57-f2aa8ccdfced` · type=`web_page_text` · content_hash=`f4a561edbae92788b2b3aadd9ca3cef9a0ad204a49f1081829bfff31b1c6d2b7`
- **snapshot_ref**：— · availability：`available_online` · spatial：`approximate`
- **关键原文引文**：> 当天起，黄浦区新增大吉路公园、静谧花园、广场公园黄浦段H6区域作为宠物可入园试点区域
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "大吉路公园", "canonical_address": "上海市黄浦区大吉路", "spatial_precision": "approximate"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：2025-09-01T00:00:00+00:00 → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：缺 effective_to 且未记录 open-ended 原因；缺 last_verified_at（捕获时间不能代替「当前是否仍有效」的复核）
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_HOLD**
- **recommendation reason**：TEMPORARY_STATUS_NOT_REVERIFIED
- **reason codes**：`FRESHNESS_INCOMPLETE`, `未复核该临时/试点政策当前是否仍有效`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-07 · `dl-legal-dog` — 上海迪士尼乐园

- **candidate_id**：`f5a8d87f-2d2a-4c1a-a018-b319cc9e580f`
- **place**：上海迪士尼乐园（`dl-disneyland`，place_type=`scenic_area`） · zone：全园 · unknown
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`e656f871-720d-469f-acd0-891434286aff` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "上海迪士尼乐园", "canonical_address": "上海市浦东新区川沙新镇申迪北路753号", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`scenic_area` → 法条类别 — · 状态 `NOT_EVIDENCED` — 场所类型 place_type=scenic_area 不属于第二十三条枚举的任一类别（办公楼/学校/医院/体育场馆/博物馆/图书馆/文化娱乐场所/候车（机、船）室/餐饮场所/商场/宾馆）；将其纳入该法条适用范围属法律解释，需显式证据支撑。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_HOLD**
- **recommendation reason**：STATUTORY_APPLICABILITY_NOT_EVIDENCED
- **reason codes**：`APPLICABILITY_EVIDENCE_MISSING`, `场所类型 place_type=scenic_area 不属于第二十三条枚举的任一类别（办公楼/学校/医院/体育场馆/博物馆/图书馆/文化娱乐场所/候车（机、船）室/餐饮场所/商场/宾馆）；将其纳入该法条适用范围属法律解释，需显式证据支撑。`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-08 · `dl-sd-legal` — 上海迪士尼乐园

- **candidate_id**：`393c6b89-ea48-451f-aa93-9fba89ce215f`
- **place**：上海迪士尼乐园（`dl-disneyland`，place_type=`scenic_area`） · zone：— · —
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`e656f871-720d-469f-acd0-891434286aff` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "上海迪士尼乐园", "canonical_address": "上海市浦东新区川沙新镇申迪北路753号", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：`dl-legal-dog`
- **exception**：需绑定为 `rule_exception` → dl-legal-dog（同层 LEGAL）——不得作为普通 AccessRule 独立发布
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`scenic_area` → 法条类别 — · 状态 `NOT_EVIDENCED` — 场所类型 place_type=scenic_area 不属于第二十三条枚举的任一类别（办公楼/学校/医院/体育场馆/博物馆/图书馆/文化娱乐场所/候车（机、船）室/餐饮场所/商场/宾馆）；将其纳入该法条适用范围属法律解释，需显式证据支撑。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_HOLD**
- **recommendation reason**：STATUTORY_APPLICABILITY_NOT_EVIDENCED
- **reason codes**：`APPLICABILITY_EVIDENCE_MISSING`, `场所类型 place_type=scenic_area 不属于第二十三条枚举的任一类别（办公楼/学校/医院/体育场馆/博物馆/图书馆/文化娱乐场所/候车（机、船）室/餐饮场所/商场/宾馆）；将其纳入该法条适用范围属法律解释，需显式证据支撑。`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-09 · `gc-h6-pilot` — 广场公园（黄浦段）

- **candidate_id**：`8f98fd01-9a1a-4d64-b354-01632d7bdbcd`
- **place**：广场公园（黄浦段）（`gc-huangpu-sect`，place_type=`park`） · zone：H6宠物试点区域 · outdoor
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission` · **holder_scope**：`—`
- **RuleLayer**：`TEMPORARY_POLICY`（临时/事件政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：黄浦区人民政府官网《9月1日起，上海这些公园试点宠物入园》（来源：新闻晨报） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
- **artifact**：id=`7de10702-8e48-472d-844e-3c71427332cd` · type=`web_page_text` · content_hash=`fb5ef988c3083421edb1914318cad382e33ebfe067beeccd939afa5d4c8878a2`
- **snapshot_ref**：— · availability：`available_online` · spatial：`approximate`
- **关键原文引文**：> 9月1日，市绿化和市容管理局《关于加强本市公园绿地开放管理的指导意见》施行。当天起，黄浦区新增大吉路公园、静谧花园、广场公园黄浦段H6区域作为宠物可入园试点区域
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "广场公园（黄浦段）", "canonical_address": "上海市黄浦区（金陵中路、西藏南路、延安东路、普安路合围H6区域）", "spatial_precision": "approximate"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：2025-09-01T00:00:00+00:00 → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：缺 effective_to 且未记录 open-ended 原因；缺 last_verified_at（捕获时间不能代替「当前是否仍有效」的复核）
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_HOLD**
- **recommendation reason**：TEMPORARY_STATUS_NOT_REVERIFIED
- **reason codes**：`FRESHNESS_INCOMPLETE`, `未复核该临时/试点政策当前是否仍有效`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-10 · `gh-indoor-new` — 港汇恒隆广场

- **candidate_id**：`73448553-cdfa-44db-8265-cb45dd325687`
- **place**：港汇恒隆广场（`gh-grand-gateway`，place_type=`mall`） · zone：室内商业空间 · indoor
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文）） · chain directness：`secondary`（二手） · ⚠️ 登记表声称 `secondary_reputable` 与证据链推导不一致
- **Source issuer**：解放日报（运营方室内宠物禁令报道） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.jfdaily.com/news/detail?id=1079860
- **capture locator（bundle.source_url）**：http://www.xinhuanet.com/food/20260529/7317dcff712642e9a63813374aab5b3b/c.html  ⚠️ 与 source 不一致
- **artifact**：id=`381510bb-85d2-4299-ab00-77fc925c5a0b` · type=`web_page_text` · content_hash=`a3ec99e0efaf8f7b1666d7190c567284ca4cd5a731b57a8827e6329684e889af`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 比如港汇恒隆广场、兴业太古汇自今年2月起正式实施全新宠物管理规定，明确禁止除导盲犬等工作犬以外的其他宠物进入商场室内公共区域，全面撤除“宠物友好”相关标识
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "place_id": "ae797630-12dd-4f3b-8233-a3f3d0253a46", "note": "R2 修复：原文页直接抓取并核验"}`
- **DataLicense / SourcePolicy**：artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13T06:17:12.884288+00:00` · 缺口：—
- **strength note**：source.directness=secondary / issuer_verification=verified / needs_verification=True —— 不代表运营方一手来源
- **provenance 缺口**：`bundle.license_metadata 为空`
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_HOLD**
- **recommendation reason**：EVIDENCE_CHAIN_INCOMPLETE
- **reason codes**：`证据强度 search_snippet 未达一手标准（ADR-021）`, `source.directness=secondary / issuer_verification=verified / needs_verification=True —— 不代表运营方一手来源`, `bundle.license_metadata 为空`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-11 · `lib-sd-op-military` — 上海图书馆东馆

- **candidate_id**：`21578527-5b09-4d53-b868-512c3603b83f`
- **place**：上海图书馆东馆（`lib-sh-library-east`，place_type=`library`） · zone：全馆 · indoor
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：军警犬
- **subject_scope_normalized（精确 scope）**：`military_working_dog`
- **normalization_type**：`compound_term_split`（复合词穷尽拆分（具备法律效力，成员集固定））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`any_handler`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海图书馆官网《读者须知》 · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.library.sh.cn/guide/xuzhi
- **artifact**：id=`3f2136b8-6cc0-4902-b0eb-783577959ca7` · type=`web_page_text` · content_hash=`667497d4a82d2444728c3eea65d4f41a1bdd7e15e430982a99dd987e6727cfc6`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "上海图书馆东馆", "canonical_address": "上海市浦东新区合欢路300号", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：`lib-pets-op`
- **exception**：需绑定为 `rule_exception` → lib-pets-op（同层 OPERATOR_POLICY）——不得作为普通 AccessRule 独立发布
- **跨层绑定已丢弃**：`lib-legal-dog` —— 旧算法曾把它指向更高层规则；按原则 B/C/D 丢弃，运营方豁免不得覆盖法规禁令
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_HOLD**
- **recommendation reason**：LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED
- **reason codes**：`LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED`, `该运营方豁免会放宽已生效的法规禁令 `lib-legal-dog`，但尚无针对 `military_working_dog` 的法律/行政依据；运营方政策不得作为法律禁令的例外（原则 B/C）。`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-12 · `lib-sd-op-police` — 上海图书馆东馆

- **candidate_id**：`81168603-f74a-4130-8fd7-c09a645a4840`
- **place**：上海图书馆东馆（`lib-sh-library-east`，place_type=`library`） · zone：全馆 · indoor
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：军警犬
- **subject_scope_normalized（精确 scope）**：`police_dog`
- **normalization_type**：`compound_term_split`（复合词穷尽拆分（具备法律效力，成员集固定））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`any_handler`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海图书馆官网《读者须知》 · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.library.sh.cn/guide/xuzhi
- **artifact**：id=`3f2136b8-6cc0-4902-b0eb-783577959ca7` · type=`web_page_text` · content_hash=`667497d4a82d2444728c3eea65d4f41a1bdd7e15e430982a99dd987e6727cfc6`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "上海图书馆东馆", "canonical_address": "上海市浦东新区合欢路300号", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：`lib-pets-op`
- **exception**：需绑定为 `rule_exception` → lib-pets-op（同层 OPERATOR_POLICY）——不得作为普通 AccessRule 独立发布
- **跨层绑定已丢弃**：`lib-legal-dog` —— 旧算法曾把它指向更高层规则；按原则 B/C/D 丢弃，运营方豁免不得覆盖法规禁令
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_HOLD**
- **recommendation reason**：LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED
- **reason codes**：`LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED`, `该运营方豁免会放宽已生效的法规禁令 `lib-legal-dog`，但尚无针对 `police_dog` 的法律/行政依据；运营方政策不得作为法律禁令的例外（原则 B/C）。`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-13 · `xm-indoor-new` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`9c8b4b26-a2cb-4efd-b188-aeee3a194951`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`，place_type=`cafe`） · zone：室内 · indoor
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文）） · chain directness：`secondary`（二手） · ⚠️ 登记表声称 `secondary_reputable` 与证据链推导不一致
- **Source issuer**：新闻媒体（2026-08 星巴克宠物专区调整报道） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://tidenews.com.cn/news.html?id=3542194
- **artifact**：id=`8a07249d-d273-40f7-a6ea-5743a33ce091` · type=`web_page_text` · content_hash=`d4ddaf075bdfa3e1573766e3f44242ff41dc0ff0695022983c73249f6166c468`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 为此我们已向顾客本人表达了诚挚的歉意，并着手进行了改进，不在该店内继续设置宠物区域。……携宠顾客需在店外宠物友好区落座。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "place_id": "91bdaeba-2841-4aa8-88fe-5aa55a2df8b9", "note": "R2 修复：原文页直接抓取并核验"}`
- **DataLicense / SourcePolicy**：artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13T06:17:12.884288+00:00` · 缺口：—
- **strength note**：source.directness=secondary / issuer_verification=verified / needs_verification=True —— 不代表运营方一手来源
- **provenance 缺口**：`bundle.license_metadata 为空`
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_HOLD**
- **recommendation reason**：EVIDENCE_CHAIN_INCOMPLETE
- **reason codes**：`证据强度 search_snippet 未达一手标准（ADR-021）`, `source.directness=secondary / issuer_verification=verified / needs_verification=True —— 不代表运营方一手来源`, `bundle.license_metadata 为空`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-14 · `xm-outdoor-media` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`fb003b3a-3583-484b-b16f-7a6f3a1b71d0`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`，place_type=`cafe`） · zone：户外宠物友好区 · outdoor
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`search_snippet`（搜索摘要（未核验原文）） · chain directness：`secondary`（二手） · ⚠️ 登记表声称 `secondary_reputable` 与证据链推导不一致
- **Source issuer**：新闻媒体（2026-08 星巴克宠物专区调整报道） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://tidenews.com.cn/news.html?id=3542194
- **artifact**：id=`8a07249d-d273-40f7-a6ea-5743a33ce091` · type=`web_page_text` · content_hash=`d4ddaf075bdfa3e1573766e3f44242ff41dc0ff0695022983c73249f6166c468`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 为此我们已向顾客本人表达了诚挚的歉意，并着手进行了改进，不在该店内继续设置宠物区域。……携宠顾客需在店外宠物友好区落座。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "place_id": "91bdaeba-2841-4aa8-88fe-5aa55a2df8b9", "note": "R2 修复：原文页直接抓取并核验"}`
- **DataLicense / SourcePolicy**：artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13T06:17:12.884288+00:00` · 缺口：—
- **strength note**：source.directness=secondary / issuer_verification=verified / needs_verification=True —— 不代表运营方一手来源
- **provenance 缺口**：`bundle.license_metadata 为空`
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_HOLD**
- **recommendation reason**：EVIDENCE_CHAIN_INCOMPLETE
- **reason codes**：`证据强度 search_snippet 未达一手标准（ADR-021）`, `source.directness=secondary / issuer_verification=verified / needs_verification=True —— 不代表运营方一手来源`, `bundle.license_metadata 为空`
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-15 · `dl-pet-ban` — 上海迪士尼乐园

- **candidate_id**：`cfe82cd4-4156-4daa-9ce2-3fdd5f5797fb`
- **place**：上海迪士尼乐园（`dl-disneyland`，place_type=`scenic_area`） · zone：全园 · unknown
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海迪士尼度假区官网《上海迪士尼乐园游客须知》 · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/
- **artifact**：id=`1dd693b9-0246-4591-8209-7a8439b1ea12` · type=`web_page_text` · content_hash=`98f50c64465fad74d1f8fefe273f1f8a2968300d23e4b8b7b1deed73e1c8e9ec`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 动物（导盲犬除外）。导盲犬须时刻栓有系绳并在主人的看管下。部分游乐项目也可能不允许导盲犬进入。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "上海迪士尼乐园", "canonical_address": "上海市浦东新区川沙新镇申迪北路753号", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=False；artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-16 · `dl-sd-op` — 上海迪士尼乐园

- **candidate_id**：`f799a74b-1f7e-49fb-bc4f-6281838877f0`
- **place**：上海迪士尼乐园（`dl-disneyland`，place_type=`scenic_area`） · zone：全园 · unknown
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海迪士尼度假区官网《上海迪士尼乐园游客须知》 · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/
- **artifact**：id=`1dd693b9-0246-4591-8209-7a8439b1ea12` · type=`web_page_text` · content_hash=`98f50c64465fad74d1f8fefe273f1f8a2968300d23e4b8b7b1deed73e1c8e9ec`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 动物（导盲犬除外）。导盲犬须时刻栓有系绳并在主人的看管下。部分游乐项目也可能不允许导盲犬进入。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "上海迪士尼乐园", "canonical_address": "上海市浦东新区川沙新镇申迪北路753号", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=False；artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：`dl-pet-ban`
- **exception**：需绑定为 `rule_exception` → dl-pet-ban（同层 OPERATOR_POLICY）——不得作为普通 AccessRule 独立发布
- **跨层绑定已丢弃**：`dl-legal-dog` —— 旧算法曾把它指向更高层规则；按原则 B/C/D 丢弃，运营方豁免不得覆盖法规禁令
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **conditions**：leash_required
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-17 · `fp-legal-dog` — 和平饭店（费尔蒙）

- **candidate_id**：`c8a3f92b-27eb-443e-bc0e-083458158582`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`，place_type=`hotel`） · zone：全酒店 · unknown
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`fbf660c4-ee00-4f1f-8cfc-c1d783d169c1` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "和平饭店（费尔蒙）", "canonical_address": "上海市黄浦区南京东路20号", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`hotel` → 法条类别 宾馆 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-18 · `fp-pets-op-firstparty` — 和平饭店（费尔蒙）

- **candidate_id**：`02454820-f30c-47de-851d-894496c36914`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`，place_type=`hotel`） · zone：全酒店 · unknown
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：宠物
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：费尔蒙上海和平饭店官网《宾客信息·宠物政策》 · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html
- **artifact**：id=`1bf60fef-68cd-4c66-85d9-f28562ee37cb` · type=`web_page_text` · content_hash=`38aba307ec8e953a0b1e8f2c8d3ff801fe96044a605f6a69b09a2f0155c5030d`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。
- **place_match_evidence**：`{"note": "场所为单位：酒店经营范围即 sd 宠物政策适用范围，无进一步房间级细分（来源未作区域限定）。", "place_id": "7f5093f3-1222-4049-af9d-cc5ca4386b54", "zone_name": "全酒店", "matched_by": "canonical_name_and_address", "canonical_name": "和平饭店（费尔蒙）", "canonical_address": "上海市黄浦区南京东路20号", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=False；《运营方官网内容，版权归费尔蒙/雅高集团所有；仅限事实性摘录引用》；无第三方快照；可复现性依赖 canonical URL + sha256(captured_excerpt)。最近复核 2026-09-15，中英双语页逐字一致。；artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：运营方常态化政策，来源未标注终止日期
- **freshness**：last_verified_at=`2026-09-15` · 缺口：—
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-19 · `fp-sd-legal` — 和平饭店（费尔蒙）

- **candidate_id**：`e94d2259-7f77-4bb5-a81c-c5ac5bc81239`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`，place_type=`hotel`） · zone：— · —
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`fbf660c4-ee00-4f1f-8cfc-c1d783d169c1` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "和平饭店（费尔蒙）", "canonical_address": "上海市黄浦区南京东路20号", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：`fp-legal-dog`
- **exception**：需绑定为 `rule_exception` → fp-legal-dog（同层 LEGAL）——不得作为普通 AccessRule 独立发布
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`hotel` → 法条类别 宾馆 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-20 · `fp-sd-op-firstparty` — 和平饭店（费尔蒙）

- **candidate_id**：`0de7771a-d461-4f86-8190-dac0604b9970`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`，place_type=`hotel`） · zone：全酒店 · unknown
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`person_with_disability`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：费尔蒙上海和平饭店官网《宾客信息·宠物政策》 · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html
- **artifact**：id=`1bf60fef-68cd-4c66-85d9-f28562ee37cb` · type=`web_page_text` · content_hash=`38aba307ec8e953a0b1e8f2c8d3ff801fe96044a605f6a69b09a2f0155c5030d`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。
- **place_match_evidence**：`{"note": "场所为单位：酒店经营范围即 sd 宠物政策适用范围，无进一步房间级细分（来源未作区域限定）。", "place_id": "7f5093f3-1222-4049-af9d-cc5ca4386b54", "zone_name": "全酒店", "matched_by": "canonical_name_and_address", "canonical_name": "和平饭店（费尔蒙）", "canonical_address": "上海市黄浦区南京东路20号", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=False；《运营方官网内容，版权归费尔蒙/雅高集团所有；仅限事实性摘录引用》；无第三方快照；可复现性依赖 canonical URL + sha256(captured_excerpt)。最近复核 2026-09-15，中英双语页逐字一致。；artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：`fp-pets-op-firstparty`
- **exception**：需绑定为 `rule_exception` → fp-pets-op-firstparty（同层 OPERATOR_POLICY）——不得作为普通 AccessRule 独立发布
- **跨层绑定已丢弃**：`fp-legal-dog` —— 旧算法曾把它指向更高层规则；按原则 B/C/D 丢弃，运营方豁免不得覆盖法规禁令
- **effective_from / to**：— → — · open-ended：运营方常态化政策，来源未标注终止日期
- **freshness**：last_verified_at=`2026-09-15` · 缺口：—
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-21 · `gh-legal-dog` — 港汇恒隆广场

- **candidate_id**：`70d10467-a771-4331-bc3e-444eac424df2`
- **place**：港汇恒隆广场（`gh-grand-gateway`，place_type=`mall`） · zone：室内商业空间 · indoor
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`f6b129e4-e9c3-4c9b-a42b-d46d6401df1b` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "港汇恒隆广场", "canonical_address": "上海市徐汇区虹桥路1号", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`mall` → 法条类别 商场 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-22 · `gh-sd-legal` — 港汇恒隆广场

- **candidate_id**：`d91706de-9447-4b3d-8977-fbfe08760c7e`
- **place**：港汇恒隆广场（`gh-grand-gateway`，place_type=`mall`） · zone：— · —
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`f6b129e4-e9c3-4c9b-a42b-d46d6401df1b` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "港汇恒隆广场", "canonical_address": "上海市徐汇区虹桥路1号", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：`gh-legal-dog`
- **exception**：需绑定为 `rule_exception` → gh-legal-dog（同层 LEGAL）——不得作为普通 AccessRule 独立发布
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`mall` → 法条类别 商场 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-23 · `lib-legal-dog` — 上海图书馆东馆

- **candidate_id**：`49f2894e-2eae-4f57-bc97-f5ab7e0e0ba3`
- **place**：上海图书馆东馆（`lib-sh-library-east`，place_type=`library`） · zone：全馆 · indoor
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`f85b97d7-9da3-4e1e-acb6-1e97070ce52c` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "上海图书馆东馆", "canonical_address": "上海市浦东新区合欢路300号", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`library` → 法条类别 图书馆 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-24 · `lib-pets-op` — 上海图书馆东馆

- **candidate_id**：`330abc76-b6e2-402f-91b1-47596bd95965`
- **place**：上海图书馆东馆（`lib-sh-library-east`，place_type=`library`） · zone：全馆 · indoor
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海图书馆官网《读者须知》 · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.library.sh.cn/guide/xuzhi
- **artifact**：id=`3f2136b8-6cc0-4902-b0eb-783577959ca7` · type=`web_page_text` · content_hash=`667497d4a82d2444728c3eea65d4f41a1bdd7e15e430982a99dd987e6727cfc6`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "上海图书馆东馆", "canonical_address": "上海市浦东新区合欢路300号", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-25 · `lib-sd-legal` — 上海图书馆东馆

- **candidate_id**：`caa28a93-94e9-4643-b6c1-bbd5d77c3ecc`
- **place**：上海图书馆东馆（`lib-sh-library-east`，place_type=`library`） · zone：— · —
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`f85b97d7-9da3-4e1e-acb6-1e97070ce52c` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "上海图书馆东馆", "canonical_address": "上海市浦东新区合欢路300号", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：`lib-legal-dog`
- **exception**：需绑定为 `rule_exception` → lib-legal-dog（同层 LEGAL）——不得作为普通 AccessRule 独立发布
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`library` → 法条类别 图书馆 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-26 · `lib-sd-op-guide` — 上海图书馆东馆

- **candidate_id**：`76d0dfc3-64ae-4d2b-a152-18ff8ebed588`
- **place**：上海图书馆东馆（`lib-sh-library-east`，place_type=`library`） · zone：全馆 · indoor
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`person_with_disability`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海图书馆官网《读者须知》 · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.library.sh.cn/guide/xuzhi
- **artifact**：id=`3f2136b8-6cc0-4902-b0eb-783577959ca7` · type=`web_page_text` · content_hash=`667497d4a82d2444728c3eea65d4f41a1bdd7e15e430982a99dd987e6727cfc6`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "上海图书馆东馆", "canonical_address": "上海市浦东新区合欢路300号", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：`lib-pets-op`
- **exception**：需绑定为 `rule_exception` → lib-pets-op（同层 OPERATOR_POLICY）——不得作为普通 AccessRule 独立发布
- **跨层绑定已丢弃**：`lib-legal-dog` —— 旧算法曾把它指向更高层规则；按原则 B/C/D 丢弃，运营方豁免不得覆盖法规禁令
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-27 · `mn-legal-dog` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`c2b179b9-77bf-433a-9219-5a406c42d5c7`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`，place_type=`cafe`） · zone：室内 · indoor
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`99408199-2d62-43a2-a2c6-b96722d39890` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "Manner咖啡（凯德虹口商业中心店）", "canonical_address": "上海市虹口区西江湾路388号凯德虹口商业中心", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`cafe` → 法条类别 餐饮场所 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-28 · `mn-sd-legal` — Manner咖啡（凯德虹口商业中心店）

- **candidate_id**：`52936479-c385-4279-814e-aa7fe8ab0a42`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`，place_type=`cafe`） · zone：— · —
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`99408199-2d62-43a2-a2c6-b96722d39890` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "Manner咖啡（凯德虹口商业中心店）", "canonical_address": "上海市虹口区西江湾路388号凯德虹口商业中心", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：`mn-legal-dog`
- **exception**：需绑定为 `rule_exception` → mn-legal-dog（同层 LEGAL）——不得作为普通 AccessRule 独立发布
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`cafe` → 法条类别 餐饮场所 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-29 · `qt-indoor-legal` — 前滩太古里

- **candidate_id**：`8151db71-3622-429d-81bc-0a0212f23290`
- **place**：前滩太古里（`qt-taikoo-li`，place_type=`mall`） · zone：商场室内空间 · indoor
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`71fd2fb6-2c8e-489f-b4db-0e80f2f96955` · type=`statute_text` · content_hash=`c39379e1b55f4444474790ba6adbbddeeefff55895413c7c9c0661880f199e6d`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "前滩太古里", "canonical_address": "上海市浦东新区东育路500弄", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`mall` → 法条类别 商场 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-30 · `qt-indoor-op` — 前滩太古里

- **candidate_id**：`93fdbdf9-4855-45f8-8bd9-8af86715f748`
- **place**：前滩太古里（`qt-taikoo-li`，place_type=`mall`） · zone：商场室内空间 · indoor
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：前滩太古里（太古地产）官网《宠物友好》页 · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.taikooliqiantan.com/detail/58.html
- **artifact**：id=`d80d641f-c6f7-4c6a-8d7c-dd86f0a6fdce` · type=`web_page_text` · content_hash=`8dae2c7a9e4365e1baa19238d358f1faa9a531bafb28cc76e595bcdcda410254`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 您的宠物仅能在前滩太古里户外开放区域，或商场或商场物业不时指定的室外特定范围区域内活动。未经商场或商场物业同意，您的宠物不得进入商场室内空间活动。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "前滩太古里", "canonical_address": "上海市浦东新区东育路500弄", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=False；artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-31 · `qt-outdoor-op` — 前滩太古里

- **candidate_id**：`100d76af-c766-494d-8c25-2e29e2214b71`
- **place**：前滩太古里（`qt-taikoo-li`，place_type=`mall`） · zone：户外开放区域 · outdoor
- **action / effect**：enter · **有条件允许**
- **coarse animal_scope**：`ordinary_pet`（普通宠物）
- **source_scope_exact（来源原话）**：ordinary_pet
- **subject_scope_normalized（精确 scope）**：`ordinary_pet`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`conditional_permission` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：前滩太古里（太古地产）官网《宠物友好》页 · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.taikooliqiantan.com/detail/58.html
- **artifact**：id=`d80d641f-c6f7-4c6a-8d7c-dd86f0a6fdce` · type=`web_page_text` · content_hash=`8dae2c7a9e4365e1baa19238d358f1faa9a531bafb28cc76e595bcdcda410254`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 您的宠物仅能在前滩太古里户外开放区域，或商场或商场物业不时指定的室外特定范围区域内活动。未经商场或商场物业同意，您的宠物不得进入商场室内空间活动。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "前滩太古里", "canonical_address": "上海市浦东新区东育路500弄", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=False；artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **conditions**：leash_required、vaccination_required、max_count
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-32 · `qt-sd-legal` — 前滩太古里

- **candidate_id**：`958d4d4c-6cd5-467e-9bc4-5eae2f67630e`
- **place**：前滩太古里（`qt-taikoo-li`，place_type=`mall`） · zone：— · —
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`71fd2fb6-2c8e-489f-b4db-0e80f2f96955` · type=`statute_text` · content_hash=`c39379e1b55f4444474790ba6adbbddeeefff55895413c7c9c0661880f199e6d`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "前滩太古里", "canonical_address": "上海市浦东新区东育路500弄", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：`qt-indoor-legal`
- **exception**：需绑定为 `rule_exception` → qt-indoor-legal（同层 LEGAL）——不得作为普通 AccessRule 独立发布
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`mall` → 法条类别 商场 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-33 · `qt-sd-op` — 前滩太古里

- **candidate_id**：`1249b621-1186-4366-a538-db04a6731fec`
- **place**：前滩太古里（`qt-taikoo-li`，place_type=`mall`） · zone：— · —
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：除导盲犬外
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`—` · **holder_scope**：`—`
- **RuleLayer**：`OPERATOR_POLICY`（运营方政策） · **MandatoryLevel**：`operator_discretion`（运营方裁量）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：前滩太古里（太古地产）官网《宠物友好》页 · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://www.taikooliqiantan.com/detail/58.html
- **artifact**：id=`d80d641f-c6f7-4c6a-8d7c-dd86f0a6fdce` · type=`web_page_text` · content_hash=`8dae2c7a9e4365e1baa19238d358f1faa9a531bafb28cc76e595bcdcda410254`
- **snapshot_ref**：— · availability：`available_online` · spatial：`precise`
- **关键原文引文**：> 本须知适用于除导盲犬以外的所有宠物，导盲犬不受本须知的限制。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "前滩太古里", "canonical_address": "上海市浦东新区东育路500弄", "spatial_precision": "precise"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=False；artifact: storage=True / display=True / redistrib=False
- **conflict（同场所同层反向规则）**：`qt-indoor-op`
- **exception**：需绑定为 `rule_exception` → qt-indoor-op（同层 OPERATOR_POLICY）——不得作为普通 AccessRule 独立发布
- **跨层绑定已丢弃**：`qt-indoor-legal` —— 旧算法曾把它指向更高层规则；按原则 B/C/D 丢弃，运营方豁免不得覆盖法规禁令
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-34 · `sb-legal-dog` — 星巴克臻选上海烘焙工坊

- **candidate_id**：`1a97f24e-3cd0-445c-804d-741be34a0dad`
- **place**：星巴克臻选上海烘焙工坊（`sb-roastery`，place_type=`cafe`） · zone：全店 · indoor
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`0cea33d4-4cfe-49aa-b5d3-d2e23f1c5d82` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "星巴克臻选上海烘焙工坊", "canonical_address": "上海市静安区南京西路789号（兴业太古汇）", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`cafe` → 法条类别 餐饮场所 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-35 · `sb-sd-legal` — 星巴克臻选上海烘焙工坊

- **candidate_id**：`b8cffbee-855a-4754-ad84-b01db0351ea3`
- **place**：星巴克臻选上海烘焙工坊（`sb-roastery`，place_type=`cafe`） · zone：— · —
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`0cea33d4-4cfe-49aa-b5d3-d2e23f1c5d82` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "星巴克臻选上海烘焙工坊", "canonical_address": "上海市静安区南京西路789号（兴业太古汇）", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：`sb-legal-dog`
- **exception**：需绑定为 `rule_exception` → sb-legal-dog（同层 LEGAL）——不得作为普通 AccessRule 独立发布
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`cafe` → 法条类别 餐饮场所 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-36 · `xm-legal-dog` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`6fc38502-85c7-4d7e-8a24-56fd5cc68e8a`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`，place_type=`cafe`） · zone：室内 · indoor
- **action / effect**：enter · **禁止**
- **coarse animal_scope**：`dog`（犬（通用））
- **source_scope_exact（来源原话）**：dog
- **subject_scope_normalized（精确 scope）**：`dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`prohibition` · **holder_scope**：`—`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`3db425b5-68a2-4d2d-8bd9-0f3e53c49b5e` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 禁止携带犬只进入办公楼、学校、医院、体育场馆、博物馆、图书馆、文化娱乐场所、候车（机、船）室、餐饮场所、商场、宾馆等场所或者乘坐公共汽车、电车、轨道交通等公共交通工具。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "星巴克咖啡（徐汇西岸梦中心店）", "canonical_address": "上海市徐汇区龙腾大道（西岸梦中心 GATE M）", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：无
- **exception**：不适用（本身即基础规则 / 无同层冲突）
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`cafe` → 法条类别 餐饮场所 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

### FINAL-37 · `xm-sd-legal` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate_id**：`6bf5128a-17ad-4a2f-83e5-eabecc7afb9f`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`，place_type=`cafe`） · zone：— · —
- **action / effect**：enter · **允许**
- **coarse animal_scope**：`service_dog`（服务犬（粗粒度 API scope））
- **source_scope_exact（来源原话）**：导盲犬
- **subject_scope_normalized（精确 scope）**：`guide_dog`
- **normalization_type**：`exact`（精确（来源即此 scope，具备法律效力））
- **normative_effect**：`exempt_from_prohibition` · **holder_scope**：`person_with_disability`
- **RuleLayer**：`LEGAL`（法规） · **MandatoryLevel**：`mandatory`（强制）
- **EvidenceStrength**：`primary_direct`（官方一手直抓（逐字）） · chain directness：`direct`（直接）
- **Source issuer**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） · 核验：`verified`（已核验）
- **Source URL（source.source_url）**：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
- **artifact**：id=`3db425b5-68a2-4d2d-8bd9-0f3e53c49b5e` · type=`statute_text` · content_hash=`1cd32532f6232d91507083de57965a28383aa46dc823fd083c3349778d83cf3a`
- **snapshot_ref**：— · availability：`available_online` · spatial：`unknown`
- **关键原文引文**：> 盲人携带导盲犬的，不受本条规定的限制。
- **place_match_evidence**：`{"matched_by": "canonical_name_and_address", "canonical_name": "星巴克咖啡（徐汇西岸梦中心店）", "canonical_address": "上海市徐汇区龙腾大道（西岸梦中心 GATE M）", "spatial_precision": "unknown"}`
- **DataLicense / SourcePolicy**：bundle: storage=True / display=True / redistrib=True；artifact: storage=True / display=True / redistrib=True
- **conflict（同场所同层反向规则）**：`xm-legal-dog`
- **exception**：需绑定为 `rule_exception` → xm-legal-dog（同层 LEGAL）——不得作为普通 AccessRule 独立发布
- **effective_from / to**：— → — · open-ended：—
- **freshness**：last_verified_at=`2026-09-13` · 缺口：—
- **applicability**：place_type=`cafe` → 法条类别 餐饮场所 · 状态 `ENUMERATED_IN_STATUTE` — 场所类型与法条枚举类别直接对应，适用性可自证。
- **conditions**：无
- **review_status**：`REVIEW_PENDING`
- **AI recommendation**：**RECOMMEND_APPROVE**
- **recommendation reason**：EVIDENCE_TRACEABLE
- **final_decision**：`________`  ← 留空，由具名评审员填写

---

## 4. 签署与后续

1. 在 `HUMAN_REVIEW_DECISIONS_R2_FINAL.json` 填写 `reviewer`（具名）、
   `reviewed_at`（ISO 8601）与逐条 `final_decision`。
   `final_decision` 只能取：`APPROVED` / `APPROVED_WITH_NOTE` / `HOLD` / `REJECTED`。
2. 回填机器登记表 `docs/reality_audit/review_decisions_r2_final.json`。
3. 校验：`python scripts/publish_reviewed_r1.py --dry-run`
   （自动读取**最新**登记表）应返回 `signed=true`。
4. **发布后**按 §1.7 的顺序创建 `rule_exception`；
   先行的基础规则必须已 published。本包不执行该步骤，仅规定顺序。

