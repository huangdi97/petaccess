# REVIEW_WORKLIST_R1.md

> PILOT-REVIEW-AND-SCHEMA-FIX-01 / S2：33 条 RuleCandidate 的人工审核工作清单。
> 基准：REAL-DATA-PILOT-10-R1（commit e299fab），候选 extraction_method=`agent_assisted_extraction_2026_09_13`。
>
> **纪律（B13 / 不强行 APPROVE）**：
> - AI/Agent 不做 APPROVED/REJECTED 决策；本清单供人工 Review Gate 使用。
> - 任何候选的 APPROVE 前提：证据核验通过 +（S8 实施后）Pre-Publish Validation 全绿。
> - 3 条 ObservationCandidate 保持 lead-only，永不进入规则发布。
> - 引用 search snippet 的 7 条必须先完成 Evidence Repair Task（B 组），不得为凑门槛直接放行。

## A 组：Evidence Review（26 条，Tier-1 直接抓取的官方/政府/法规原文，逐字引文可比对）

核验动作（每条相同）：打开来源 URL → 比对 bundle `quoted_fragment` 与页面原文逐字一致 → 比对结构化字段（scope/action/effect/conditions/zone）与原文语义一致 → 通过则 APPROVED（S8 六项检查自动前置），不一致则 REJECTED 并写明差异。

| # | Place | Zone | 候选内容 | 候选 ID | 来源（核验 URL） |
|---|---|---|---|---|---|
| A1 | 前滩太古里 | 商场室内空间 | dog 禁入（条例23『商场』） | `8151db71-3622-429d-81bc-0a0212f23290` | gaj.sh.gov.cn 条例第23条 |
| A2 | 前滩太古里 | 商场室内空间 | ordinary_pet 禁入（未经同意不得入内） | `93fdbdf9-4855-45f8-8bd9-8af86715f748` | taikooliqiantan.com/detail/58.html |
| A3 | 前滩太古里 | 户外开放区域 | conditional（牵引/疫苗/限1只；另有 8周/登记/监护人条款） | `100d76af-c766-494d-8c25-2e29e2214b71` | 同上 |
| A4 | 前滩太古里 | 场所级 | service_dog allowed（导盲犬不受须知限制） | `1249b621-1186-4366-a538-db04a6731fec` | 同上 |
| A5 | 前滩太古里 | 场所级 | service_dog allowed（条例23但书） | `958d4d4c-6cd5-467e-9bc4-5eae2f67630e` | gaj.sh.gov.cn 条例第23条但书 |
| A6 | 上海迪士尼乐园 | 全园 | ordinary_pet 禁入（动物（导盲犬除外）） | `cfe82cd4-4156-4daa-9ce2-3fdd5f5797fb` | shanghaidisneyresort.com/zh-cn/legal/park-rules/ |
| A7 | 上海迪士尼乐园 | 全园 | service_dog conditional（全程牵引；部分项目可能不允许） | `f799a74b-1f7e-49fb-bc4f-6281838877f0` | 同上 |
| A8 | 上海迪士尼乐园 | 全园 | dog 禁入（条例23『文化娱乐场所』解释，置信 0.7） | `f5a8d87f-2d2a-4c1a-a018-b319cc9e580f` | gaj.sh.gov.cn（**解释性条款，审核时须裁定适用性**） |
| A9 | 上海迪士尼乐园 | 场所级 | service_dog allowed（条例23但书） | `393c6b89-ea48-451f-aa93-9fba89ce215f` | 同上 |
| A10 | 上海图书馆东馆 | 全馆 | ordinary_pet 禁入（请勿携带活禽以及猫、狗…） | `330abc76-b6e2-402f-91b1-47596bd95965` | library.sh.cn/guide/xuzhi 第7条 |
| A11 | 上海图书馆东馆 | 全馆 | service_dog allowed（括注除外条款） | `76d0dfc3-64ae-4d2b-a152-18ff8ebed588` | 同上 |
| A12 | 上海图书馆东馆 | 全馆 | dog 禁入（条例23『图书馆』） | `49f2894e-2eae-4f57-bc97-f5ab7e0e0ba3` | gaj.sh.gov.cn |
| A13 | 上海图书馆东馆 | 场所级 | service_dog allowed（条例23但书） | `caa28a93-94e9-4643-b6c1-bbd5d77c3ecc` | 同上 |
| A14 | 广场公园（黄浦段） | H6宠物试点区域 | conditional（2025-09-01 起试点；牵引） | `8f98fd01-9a1a-4d64-b354-01632d7bdbcd` | shhuangpu.gov.cn 公告 |
| A15 | 广场公园（黄浦段） | 公园其余区域 | prohibited（未列入试点维持原规定，推断条款，置信 0.75） | `ffb804af-c271-443f-a07a-0fb3b5db5a87` | 同上（**推断性表述，须裁定**） |
| A16 | 大吉路公园 | 全园 | conditional（试点允许；牵引） | `70cc7579-1764-4177-82b5-fd2d5b255b37` | 同上 |
| A17 | 港汇恒隆广场 | 室内商业空间 | dog 禁入（条例23『商场』） | `70d10467-a771-4331-bc3e-444eac424df2` | gaj.sh.gov.cn |
| A18 | 港汇恒隆广场 | 场所级 | service_dog allowed（条例23但书） | `d91706de-9447-4b3d-8977-fbfe08760c7e` | 同上 |
| A19 | 和平饭店 | 全酒店 | dog 禁入（条例23『宾馆』） | `c8a3f92b-27eb-443e-bc0e-083458158582` | gaj.sh.gov.cn |
| A20 | 和平饭店 | 场所级 | service_dog allowed（条例23但书） | `e94d2259-7f77-4bb5-a81c-c5ac5bc81239` | 同上 |
| A21 | 星巴克烘焙工坊 | 全店 | dog 禁入（条例23『餐饮场所』） | `1a97f24e-3cd0-445c-804d-741be34a0dad` | gaj.sh.gov.cn（**与品牌宠物友好计划的适用范围冲突，见 R1 报告 §6 SG-REAL-01**） |
| A22 | 星巴克烘焙工坊 | 场所级 | service_dog allowed（条例23但书） | `b8cffbee-855a-4754-ad84-b01db0351ea3` | 同上 |
| A23 | 西岸梦中心店 | 室内 | dog 禁入（条例23『餐饮场所』） | `6fc38502-85c7-4d7e-8a24-56fd5cc68e8a` | gaj.sh.gov.cn |
| A24 | 西岸梦中心店 | 场所级 | service_dog allowed（条例23但书） | `6bf5128a-17ad-4a2f-83e5-eabecc7afb9f` | 同上 |
| A25 | Manner 凯德虹口店 | 室内 | dog 禁入（条例23『餐饮场所』） | `c2b179b9-77bf-433a-9219-5a406c42d5c7` | gaj.sh.gov.cn |
| A26 | Manner 凯德虹口店 | 场所级 | service_dog allowed（条例23但书） | `52936479-c385-4279-814e-aa7fe8ab0a42` | 同上 |

注：条例第23条但书（service_dog allowed）与第23条正文（dog prohibited）来自同一法定条文；S3 已实现 `RuleException` 机制后，人工审核可选择"批准 base 规则 + 挂同源 exception"的建模（推荐），或将但书作为独立 allowed 规则（现状建模）。两种表达的 resolver 结果必须等价（S5 不变量测试覆盖）。

## B 组：Evidence Repair Task（7 条，仅 search snippet，须先补强证据）

| # | Place / Zone | 候选内容 | 候选 ID | 现状 | Repair 路径（优先级序） |
|---|---|---|---|---|---|
| B1 | 港汇恒隆广场 / 室内商业空间 | ordinary_pet 禁入（2026-02 起运营方规定） | `73448553-cdfa-44db-8265-cb45dd325687` | 解放日报搜索摘要 | ① 运营方（恒隆）官方公告页 ② 解放日报/新华网原文页直接抓取 ③ 现场/客服核验 |
| B2 | 港汇恒隆广场 / 户外街区 | conditional（户外保留） | `887f21ba-e548-457b-a3dd-30ea806d988e` | 同上摘要 | 同 B1 |
| B3 | 和平饭店 / 全酒店 | ordinary_pet 禁入（OTA 聚合） | `4c7aba30-a7e3-4ad7-88d7-61a0ba255f27` | Booking 等聚合摘要 | ① 费尔蒙官网政策页 ② 酒店官方客服/邮件确认 ③ OTA 页直接抓取（降级为 SECONDARY） |
| B4 | 和平饭店 / 全酒店 | service_dog conditional | `7efddba6-7c42-4013-8918-bedbb996d702` | 同上 | 同 B3 |
| B5 | Manner 凯德虹口店 / 户外宠物区 | conditional（首家宠物友好店） | `ed79071d-d052-46b4-a216-dc789aae4128` | CBNData 摘要 | ① Manner 官方渠道（小程序/公告）② CBNData 原文页 ③ 门店现场核验 |
| B6 | 西岸梦中心店 / 室内 | ordinary_pet 禁入（2026-08 调整） | `9c8b4b26-a2cb-4efd-b188-aeee3a194951` | 新闻摘要（**URL 待归档**） | ① 定位原始报道并归档 URL+hash ② 星巴克官方回应原文 ③ 门店现场核验 |
| B7 | 西岸梦中心店 / 户外宠物友好区 | conditional（户外引导） | `fb003b3a-3583-484b-b16f-7a6f3a1b71d0` | 同上 | 同 B6 |

Repair 结果记录：见 `docs/reality_audit/EVIDENCE_REPAIR_LOG_R1.md`（每次尝试一条，含目标 URL、方式、结果、升级/降级判定）。

## C 组：ObservationCandidate（3 条，lead-only）

| # | Place | 内容 | ID | 处置 |
|---|---|---|---|---|
| C1 | 星巴克烘焙工坊 | 门店级政策未公开（UNKNOWN-state 记录） | 见 ingest manifest | 仅线索；永不发布 |
| C2 | Manner 凯德虹口店 | 社媒帖：户外宠物区经历 | 同上 | 仅线索；永不发布 |
| C3 | 西岸梦中心店 | 用户经历：室内占座争执 | 同上 | 仅线索；永不发布 |

## 状态汇总

| 状态 | 数量 |
|---|---|
| Evidence Review 待人工（A 组） | 26 |
| Evidence Repair 待补强（B 组） | 7 |
| Observation lead-only（C 组） | 3 |
| APPROVED / REJECTED（本轮） | **0 / 0（不强行审批）** |
| PUBLISHED | **0** |
