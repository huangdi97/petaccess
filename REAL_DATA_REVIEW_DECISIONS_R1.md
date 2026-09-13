# REAL_DATA_REVIEW_DECISIONS_R1.md

> P0 — PILOT-REVIEW-PUBLISH-01 / S1–S5：33 条 RuleCandidate 的审核工作稿。
> 生成时间：2026-09-13（GMT+8）· 基准：`REAL_DATA_PILOT_10_R2_REPORT.md`（commit `08ee60c`）
>
> **纪律（不可协商）**
> 1. 本文件是**审核工作稿**，不是裁决。`proposed_decision` 为建议；`final_decision` 必须由**具名人类评审员**填写并签署（ADR-005 / Master Goal §0.9：AI 不做最终规则裁决）。
> 2. 未获人类签署前，任何候选不得进入 APPROVED，更不得 Publish。
> 3. 3 条 ObservationCandidate 保持 lead-only，永不进入规则发布。
> 4. 引用 `search_snippet` / `social_lead` 证据的候选被 Pre-Publish Validation 硬拦截（ADR-021/022）。

---

## 0. 决策词表

| proposed_decision | 含义 | 可否进入发布批次 |
|---|---|---|
| `RECOMMEND_APPROVE` | 证据可追溯、归属正确、许可允许、语义与原文一致 | 可（过六检后） |
| `RECOMMEND_APPROVE_WITH_NOTE` | 可批准，但须评审员确认一条建模注记 | 可（须勾选注记） |
| `RECOMMEND_HOLD` | 证据未证实，或结论为推断/法律解释，须补证或裁定 | 否 |
| `RECOMMEND_REJECT` | 来源不支持该候选 | 否（终态 REJECTED） |

---

## 1. 汇总

| proposed_decision | 数量 | 候选 |
|---|---|---|
| RECOMMEND_APPROVE | **21** | 7 条法规「犬只禁入」+ 2 条政府公园试点 + 12 条运营方规则 |
| RECOMMEND_APPROVE_WITH_NOTE | **8** | 8 条法规「服务犬豁免」（scope 泛化注记，ADR-020） |
| RECOMMEND_HOLD | **3** | `f5a8d87f`（迪士尼法规解释）、`ffb804af`（公园其余区域推断禁止）、`887f21ba`（港汇户外未证实） |
| RECOMMEND_REJECT | **1** | `ed79071d`（Manner 凯德虹口，归因错误实锤） |
| 合计 | **33** | |

**第一批发布批次 R1-A（17 条）**：7 条法规「犬只禁入」+ 8 条法规「服务犬豁免」+ 2 条政府公园试点。选择依据：来源层级最高（法规/政府）、redistribution 允许、逐字引文可直接比对、无 unresolved conflict。

---

## 2. 逐条审核表

字段：`#` / 候选 ID / Place·Zone / 内容 / 证据 / 归属 / 许可 / 建议。

### 2.1 法规层 LEGAL（16 条，来源：《上海市养犬管理条例》第二十三条 · gaj.sh.gov.cn）

| # | 候选 ID | Place · Zone | 内容 | evidence_summary | place_match_summary | license_summary | proposed |
|---|---|---|---|---|---|---|---|
| L1 | `8151db71-3622-429d-81bc-0a0212f23290` | 前滩太古里 · 商场室内空间 | dog / enter / prohibited | primary_direct；逐字：「禁止携带犬只进入…商场…」；hash 在案 | 条例 venue 词表命中「商场」→ 场所类型 mall；bundle 带 place_match_evidence | 政府公告 redistribution=true，可发布 | **APPROVE** |
| L2 | `958d4d4c-6cd5-467e-9bc4-5eae2f67630e` | 前滩太古里 · 场所级 | service_dog / enter / allowed | primary_direct；逐字：「盲人携带导盲犬的，不受本条规定的限制」 | 同源同位（bundle 级） | 同上 | **APPROVE_WITH_NOTE** |
| L3 | `f5a8d87f-2d2a-4c1a-a018-b319cc9e580f` | 上海迪士尼乐园 · 全园 | dog / enter / prohibited | primary_direct 引文为真，但**结论是解释**：条例「文化娱乐场所」是否覆盖主题乐园 | 场所类型 scenic_area 与条例词表**无直接对应** | 可发布，但语义存疑 | **HOLD** |
| L4 | `393c6b89-ea48-451f-aa93-9fba89ce215f` | 上海迪士尼乐园 · 场所级 | service_dog / enter / allowed | primary_direct；但书逐字 | 同源同位 | 同上 | **APPROVE_WITH_NOTE** |
| L5 | `49f2894e-2eae-4f57-bc97-f5ab7e0e0ba3` | 上海图书馆东馆 · 全馆 | dog / enter / prohibited | primary_direct；条例「图书馆」逐字命中 | 场所类型 library ↔ 「图书馆」直接对应 | 同上 | **APPROVE** |
| L6 | `caa28a93-94e9-4643-b6c1-bbd5d77c3ecc` | 上海图书馆东馆 · 场所级 | service_dog / enter / allowed | primary_direct；但书逐字 | 同源同位 | 同上 | **APPROVE_WITH_NOTE** |
| L7 | `70d10467-a771-4331-bc3e-444eac424df2` | 港汇恒隆广场 · 室内商业空间 | dog / enter / prohibited | primary_direct；「商场」逐字命中 | mall ↔ 商场 | 同上 | **APPROVE** |
| L8 | `d91706de-9447-4b3d-8977-fbfe08760c7e` | 港汇恒隆广场 · 场所级 | service_dog / enter / allowed | primary_direct；但书逐字 | 同源同位 | 同上 | **APPROVE_WITH_NOTE** |
| L9 | `c8a3f92b-27eb-443e-bc0e-083458158582` | 和平饭店 · 全酒店 | dog / enter / prohibited | primary_direct；「宾馆」逐字命中 | hotel ↔ 宾馆 | 同上 | **APPROVE** |
| L10 | `e94d2259-7f77-4bb5-a81c-c5ac5bc81239` | 和平饭店 · 场所级 | service_dog / enter / allowed | primary_direct；但书逐字 | 同源同位 | 同上 | **APPROVE_WITH_NOTE** |
| L11 | `1a97f24e-3cd0-445c-804d-741be34a0dad` | 星巴克烘焙工坊 · 全店 | dog / enter / prohibited | primary_direct；「餐饮场所」逐字命中 | cafe ↔ 餐饮场所 | 同上 | **APPROVE** |
| L12 | `b8cffbee-855a-4754-ad84-b01db0351ea3` | 星巴克烘焙工坊 · 场所级 | service_dog / enter / allowed | primary_direct；但书逐字 | 同源同位 | 同上 | **APPROVE_WITH_NOTE** |
| L13 | `c2b179b9-77bf-433a-9219-5a406c42d5c7` | Manner 凯德虹口店 · 室内 | dog / enter / prohibited | primary_direct（法规侧独立成立，不依赖被证伪的 CBNData 来源） | cafe ↔ 餐饮场所；place 归属成立 | 同上 | **APPROVE** |
| L14 | `52936479-c385-4279-814e-aa7fe8ab0a42` | Manner 凯德虹口店 · 场所级 | service_dog / enter / allowed | primary_direct；但书逐字 | 同源同位 | 同上 | **APPROVE_WITH_NOTE** |
| L15 | `6fc38502-85c7-4d7e-8a24-56fd5cc68e8a` | 西岸梦中心店 · 室内 | dog / enter / prohibited | primary_direct；「餐饮场所」逐字命中 | cafe ↔ 餐饮场所 | 同上 | **APPROVE** |
| L16 | `6bf5128a-17ad-4a2f-83e5-eabecc7afb9f` | 西岸梦中心店 · 场所级 | service_dog / enter / allowed | primary_direct；但书逐字 | 同源同位 | 同上 | **APPROVE_WITH_NOTE** |

> **APPROVE_WITH_NOTE 的注记（L2/L4/L6/L8/L10/L12/L14/L16，8 条）**
> 法条原文豁免对象是「**盲人携带导盲犬**」，候选建模为 `animal_scope=service_dog`（广义工作犬）。该泛化是 ADR-020 的平台级决定（guide dog = service_dog + service_role=working）。评审员须确认：**接受平台级泛化**，或在 `proposed_conditions` 增加 `service_role` 约束后再批准。**不建议**在无评审确认的情况下按现状批准。

### 2.2 政府层（3 条，来源：黄浦区人民政府官网公告 · shhuangpu.gov.cn）

| # | 候选 ID | Place · Zone | 内容 | evidence_summary | place_match_summary | license_summary | proposed |
|---|---|---|---|---|---|---|---|
| G1 | `8f98fd01-9a1a-4d64-b354-01632d7bdbcd` | 广场公园（黄浦段）· H6宠物试点区域 | ordinary_pet / enter / conditional（牵引） | primary_direct；逐字列出 H6 为试点区域 | 公告逐字点名「广场公园黄浦段H6区域」→ 精确归属 | 政府公告 redistribution=true | **APPROVE** |
| G2 | `70cc7579-1764-4177-82b5-fd2d5b255b37` | 大吉路公园 · 全园 | ordinary_pet / enter / conditional（牵引） | primary_direct；公告逐字点名「大吉路公园」 | 精确归属 | 同上 | **APPROVE** |
| G3 | `ffb804af-c271-443f-a07a-0fb3b5db5a87` | 广场公园（黄浦段）· 公园其余区域 | ordinary_pet / enter / prohibited | primary_direct 引文为真，但**原文未出现「禁止」**；结论由「未列入试点名单」**推断**（confidence 0.75） | 归属成立 | 可发布，但结论非原文陈述 | **HOLD** |

### 2.3 运营方 / 品牌层（14 条）

| # | 候选 ID | Place · Zone | 内容 | evidence_summary | place_match_summary | license_summary | proposed |
|---|---|---|---|---|---|---|---|
| O1 | `93fdbdf9-4855-45f8-8bd9-8af86715f748` | 前滩太古里 · 商场室内空间 | ordinary_pet / enter / prohibited | primary_direct；官网逐字「未经商场或商场物业同意…不得进入商场室内空间」 | 官网页面即该场所官网 | operator 页 redistribution=false / storage=true → 规则可发布（非 redistributable 的是页面文本，非规则陈述） | **APPROVE** |
| O2 | `100d76af-c766-494d-8c25-2e29e2214b71` | 前滩太古里 · 户外开放区域 | ordinary_pet / enter / conditional（牵引/疫苗/限1只） | primary_direct；三条件均有逐字片段（leash/vaccine/max_count） | 同上 | 同上 | **APPROVE** |
| O3 | `1249b621-1186-4366-a538-db04a6731fec` | 前滩太古里 · 场所级 | service_dog / enter / allowed | primary_direct；逐字「本须知适用于除导盲犬以外的所有宠物，导盲犬不受本须知的限制」 | 同上 | 同上 | **APPROVE** |
| O4 | `cfe82cd4-4156-4daa-9ce2-3fdd5f5797fb` | 上海迪士尼乐园 · 全园 | ordinary_pet / enter / prohibited | primary_direct；逐字「动物（导盲犬除外）」 | 官网游客须知即该场所 | 同上 | **APPROVE** |
| O5 | `f799a74b-1f7e-49fb-bc4f-6281838877f0` | 上海迪士尼乐园 · 全园 | service_dog / enter / conditional（牵引） | primary_direct；逐字「须时刻栓有系绳…部分游乐项目也可能不允许」 | 同上 | 同上 | **APPROVE** |
| O6 | `330abc76-b6e2-402f-91b1-47596bd95965` | 上海图书馆东馆 · 全馆 | ordinary_pet / enter / prohibited | primary_direct；《读者须知》第7条逐字 | 官网读者须知即该馆 | library 页 redistribution=true | **APPROVE** |
| O7 | `76d0dfc3-64ae-4d2b-a152-18ff8ebed588` | 上海图书馆东馆 · 全馆 | service_dog / enter / allowed | primary_direct；括注「（导盲犬、军警犬除外）」 | 同上 | 同上 | **APPROVE** |
| O8 | `73448553-cdfa-44db-8265-cb45dd325687` | 港汇恒隆广场 · 室内商业空间 | ordinary_pet / enter / prohibited（2026-02 起） | **R2 修复**：SEARCH_SNIPPET → SECONDARY_REPUTABLE（新华网 2026-05-29 直抓逐字「明确禁止除导盲犬等工作犬以外的其他宠物进入商场室内公共区域」） | 新华网原文逐字点名「港汇恒隆广场」 | 新闻 redistribution=false / storage=true；证据强度达 SECONDARY_REPUTABLE，非 lead-only | **APPROVE** |
| O9 | `4c7aba30-a7e3-4ad7-88d7-61a0ba255f27` | 和平饭店 · 全酒店 | ordinary_pet / enter / prohibited | **R2 修复**：SEARCH_SNIPPET → **PRIMARY_DIRECT**（费尔蒙官网 guest-services 逐字「禁止宠物入内」） | 官网即该酒店 | 官网 storage=true | **APPROVE** |
| O10 | `7efddba6-7c42-4013-8918-bedbb996d702` | 和平饭店 · 全酒店 | service_dog / enter / **allowed**（R2 效果修正：原 conditional） | **R2 修复**：PRIMARY_DIRECT（官网逐字「导盲犬可随时进入酒店，且无需支付额外费用或受任何限制」） | 同上 | 同上 | **APPROVE** |
| O11 | `9c8b4b26-a2cb-4efd-b188-aeee3a194951` | 西岸梦中心店 · 室内 | ordinary_pet / enter / prohibited（2026-08 调整） | **R2 修复**：SEARCH_SNIPPET → SECONDARY_REPUTABLE（潮新闻 2026-08-27 官方回应逐字「不在该店内继续设置宠物区域」） | 潮新闻原文点名西岸梦中心星巴克店 | 新闻 redistribution=false / storage=true | **APPROVE** |
| O12 | `fb003b3a-3583-484b-b16f-7a6f3a1b71d0` | 西岸梦中心店 · 户外宠物友好区 | ordinary_pet / enter / conditional（牵引） | **R2 修复**：SECONDARY_REPUTABLE（潮新闻「携宠顾客需在店外宠物友好区落座」+ 澎湃客服回应） | 同上 | 同上 | **APPROVE** |
| O13 | `887f21ba-e548-457b-a3dd-30ea806d988e` | 港汇恒隆广场 · 户外街区 | ordinary_pet / enter / conditional（牵引） | **未证实**：新华网原文只覆盖「室内公共区域」，未提户外；且 `leash_required` 为**审慎默认值**而非来源陈述 | 归属成立，但内容无来源支撑 | 可发布但内容不成立 | **HOLD** |
| O14 | `ed79071d-d052-46b4-a216-dc789aae4128` | Manner 凯德虹口店 · 户外宠物区 | ordinary_pet / enter / conditional（牵引） | **归因错误实锤**：CBNData 原文《Manner、KFC都入局》未报道凯德虹口宠物友好店（文中「凯德虹口」实指宠物用品店「狗道」）；Manner 案例实为徐汇滨江店 | **来源不支持该场所** | — | **REJECT** |

---

## 3. 观察候选（3 条，lead-only，永不发布）

| # | Place | 内容 | 处置 |
|---|---|---|---|
| C1 | 星巴克烘焙工坊 | 门店级政策未公开（UNKNOWN-state 记录） | 保持 lead-only；`display_allowed`/`storage_allowed` 受限 |
| C2 | Manner 凯德虹口店 | 社媒帖：户外宠物区经历（ordinary_user，display=false/storage=false） | 保持 lead-only |
| C3 | 西岸梦中心店 | 用户经历：室内占座争执（ordinary_user，display=false/storage=false） | 保持 lead-only |

---

## 4. 审核期发现的发布路径缺陷（P0 级）

| ID | 严重度 | 缺陷 | 状态 |
|---|---|---|---|
| **BLK-LAYER-01** | P0 | `RuleCandidate` 无 `rule_layer` 字段，入库静默丢弃；`publish()` 硬编码 `rule_layer="OPERATOR_POLICY"` → 16 条 LEGAL 规则与 2 条 TEMPORARY_POLICY 规则会被降级，改变 resolver 分层路由与遮蔽语义 | **已修复**：模型 + 迁移 `d1a4f7c93b28` + `publish()` 透传 + publish gate 校验 + 入库脚本携带 + 5 项回归测试 |
| **BLK-LAYER-02** | P0 | `AccessRule` **无 `mandatory_level` 列**，故 DB 来源的 LEGAL 规则永远进不了 resolver 的 `legal_mandatory` 分支（`v05_resolver.py:274`），且被排除在 `governing` 之外（`:409`）。后果：运营方「允许」规则可**覆盖**《养犬管理条例》第23条法定禁止。现有 13 项回归夹具同样不带 `mandatory_level`，因此测试无法暴露该缺口 | **未修复**（需人类裁定：schema + ADR）。见 `REAL_DATA_PUBLISH_R1_REPORT.md` §4 |

---

## 5. 人类签署区（必填）

> 未填写本节，任何候选不得进入 APPROVED / PUBLISHED。

| 字段 | 值 |
|---|---|
| reviewer（具名） | **（待填写）** |
| reviewer_role | **（待填写）** |
| reviewed_at | **（待填写）** |
| 已接受 APPROVE_WITH_NOTE 的 scope 泛化（ADR-020） | ☐ 是 ☐ 否 |
| BLK-LAYER-02 处置决定 | ☐ 按现状发布 ☐ 先补 `mandatory_level` 再发布 ☐ 其他：____ |
| 批次 R1-A 批准条数 | **（待填写）** |
| 签名 | **（待填写）** |

---

## 6. 状态

| 项 | 值 |
|---|---|
| RuleCandidate 总数 | 33 |
| 已具名人类审核 | **0** |
| APPROVED | **0** |
| REJECTED | **0** |
| PUBLISHED | **0** |
| 工作稿状态 | **COMPLETE（待人类签署）** |
