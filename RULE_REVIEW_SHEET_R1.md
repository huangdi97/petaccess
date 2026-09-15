# RULE_REVIEW_SHEET_R1.md

> P0-PUBLISH-CLOSURE · 33 条真实 RuleCandidate 的可签署人工审核工作表。
> 生成来源：`docs/reality_audit/review_decisions_r1.json`（机器登记表）。
> 候选总数：**33**。

## 纪律（不可协商）

1. **AI 不做最终裁决**（ADR-005 / Master Goal §0.9）。`AI 建议` 与 `理由` 仅为建议；
   `final_decision` / `reviewer` / `reviewed_at` 三列由**具名人类评审员**填写。
2. 未获签署，任何候选不得进入 APPROVED，更不得 Publish（`publish_reviewed_r1.py` 硬门禁）。
3. 弱证据（`search_snippet` / `social_lead`）不得 APPROVED（ADR-021 + Pre-Publish Validation）。
4. 3 条 ObservationCandidate 保持 lead-only，永不进入规则发布（不在本表内）。
5. LEGAL 候选的 `mandatory_level` 由 layer 确定性映射（ADR-023），评审员可逐行覆盖；留空将导致发布被拒。

## 建议汇总

| AI 建议 | 数量 |
|---|---|
| APPROVE | 21 |
| APPROVE_WITH_NOTE | 8 |
| HOLD（pending） | 3 |
| REJECT | 1 |
| **合计** | **33** |

> `HOLD（pending）` 含两类：结论为推断/法律解释，或证据仍仅为搜索摘要。**均不强行通过。**

---

## 逐条审核表

### 1. `dj-pilot` — 大吉路公园

- **candidate**：`70cc7579-1764-4177-82b5-fd2d5b255b37`
- **place**：大吉路公园（`dj-daji-park`）· zone：`whole_park`
- **proposed rule**：ordinary_pet · enter · 有条件允许（leash_required） · layer：`TEMPORARY_POLICY`（临时/事件政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：黄浦区人民政府官网《9月1日起，上海这些公园试点宠物入园》（来源：新闻晨报）
  - URL：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 2. `dl-legal-dog` — 上海迪士尼乐园

- **candidate**：`f5a8d87f-2d2a-4c1a-a018-b319cc9e580f`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`whole_park`
- **proposed rule**：dog · enter · 禁止 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**HOLD（pending）**
- **reason**：结论为推断/法律解释或证据未证实，须补证或裁定
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 3. `dl-pet-ban` — 上海迪士尼乐园

- **candidate**：`cfe82cd4-4156-4daa-9ce2-3fdd5f5797fb`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`whole_park`
- **proposed rule**：ordinary_pet · enter · 禁止 · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海迪士尼度假区官网《上海迪士尼乐园游客须知》
  - URL：https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 4. `dl-sd-legal` — 上海迪士尼乐园

- **candidate**：`393c6b89-ea48-451f-aa93-9fba89ce215f`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`None`
- **proposed rule**：service_dog · enter · 允许 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：`dl-sd-op`（OPERATOR_POLICY · conditional · primary_direct）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 5. `dl-sd-op` — 上海迪士尼乐园

- **candidate**：`f799a74b-1f7e-49fb-bc4f-6281838877f0`
- **place**：上海迪士尼乐园（`dl-disneyland`）· zone：`whole_park`
- **proposed rule**：service_dog · enter · 有条件允许（leash_required） · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海迪士尼度假区官网《上海迪士尼乐园游客须知》
  - URL：https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：`dl-sd-legal`（LEGAL · allowed · primary_direct）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 6. `fp-legal-dog` — 和平饭店（费尔蒙）

- **candidate**：`c8a3f92b-27eb-443e-bc0e-083458158582`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`whole_hotel`
- **proposed rule**：dog · enter · 禁止 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 7. `fp-pets-op` — 和平饭店（费尔蒙）

- **candidate**：`4c7aba30-a7e3-4ad7-88d7-61a0ba255f27`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`whole_hotel`
- **proposed rule**：ordinary_pet · enter · 禁止 · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：Booking/Hotels.com/Expedia 聚合展示的运营方宠物政策
  - URL：https://www.booking.com/hotel/cn/peace-hotel.html
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 8. `fp-sd-legal` — 和平饭店（费尔蒙）

- **candidate**：`e94d2259-7f77-4bb5-a81c-c5ac5bc81239`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`None`
- **proposed rule**：service_dog · enter · 允许 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：`fp-sd-op`（OPERATOR_POLICY · conditional · primary_direct）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 9. `fp-sd-op` — 和平饭店（费尔蒙）

- **candidate**：`7efddba6-7c42-4013-8918-bedbb996d702`
- **place**：和平饭店（费尔蒙）（`fp-peace-hotel`）· zone：`whole_hotel`
- **proposed rule**：service_dog · enter · 有条件允许 · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：Booking/Hotels.com/Expedia 聚合展示的运营方宠物政策
  - URL：https://www.booking.com/hotel/cn/peace-hotel.html
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：`fp-sd-legal`（LEGAL · allowed · primary_direct）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 10. `gc-h6-pilot` — 广场公园（黄浦段）

- **candidate**：`8f98fd01-9a1a-4d64-b354-01632d7bdbcd`
- **place**：广场公园（黄浦段）（`gc-huangpu-sect`）· zone：`h6_pet_area`
- **proposed rule**：ordinary_pet · enter · 有条件允许（leash_required） · layer：`TEMPORARY_POLICY`（临时/事件政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：黄浦区人民政府官网《9月1日起，上海这些公园试点宠物入园》（来源：新闻晨报）
  - URL：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：`gc-other-keep`（OPERATOR_POLICY · prohibited · primary_direct）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 11. `gc-other-keep` — 广场公园（黄浦段）

- **candidate**：`ffb804af-c271-443f-a07a-0fb3b5db5a87`
- **place**：广场公园（黄浦段）（`gc-huangpu-sect`）· zone：`other_areas`
- **proposed rule**：ordinary_pet · enter · 禁止 · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：黄浦区人民政府官网《9月1日起，上海这些公园试点宠物入园》（来源：新闻晨报）
  - URL：https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f4-4591-a25b-4d591628f514.html
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：`gc-h6-pilot`（TEMPORARY_POLICY · conditional · primary_direct）
- **AI recommendation**：**HOLD（pending）**
- **reason**：结论为推断/法律解释或证据未证实，须补证或裁定
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 12. `gh-indoor-new` — 港汇恒隆广场

- **candidate**：`73448553-cdfa-44db-8265-cb45dd325687`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`indoor`
- **proposed rule**：ordinary_pet · enter · 禁止 · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：可靠二手（权威媒体直抓）
- **source**：解放日报（运营方室内宠物禁令报道）
  - URL：https://www.jfdaily.com/news/detail?id=1079860
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`secondary_reputable`
- **conflicts**：`gh-outdoor-keep`（OPERATOR_POLICY · conditional · search_snippet）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 13. `gh-legal-dog` — 港汇恒隆广场

- **candidate**：`70d10467-a771-4331-bc3e-444eac424df2`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`indoor`
- **proposed rule**：dog · enter · 禁止 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 14. `gh-outdoor-keep` — 港汇恒隆广场

- **candidate**：`887f21ba-e548-457b-a3dd-30ea806d988e`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`outdoor`
- **proposed rule**：ordinary_pet · enter · 有条件允许（leash_required） · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：搜索摘要（未核验原文）
- **source**：解放日报（运营方室内宠物禁令报道）
  - URL：https://www.jfdaily.com/news/detail?id=1079860
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`search_snippet`
- **conflicts**：`gh-indoor-new`（OPERATOR_POLICY · prohibited · secondary_reputable）
- **AI recommendation**：**HOLD（pending）**
- **reason**：EVIDENCE_NOT_VERIFIED —— 证据仍仅为搜索摘要，未核验原文；不强行通过
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 15. `gh-sd-legal` — 港汇恒隆广场

- **candidate**：`d91706de-9447-4b3d-8977-fbfe08760c7e`
- **place**：港汇恒隆广场（`gh-grand-gateway`）· zone：`None`
- **proposed rule**：service_dog · enter · 允许 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 16. `lib-legal-dog` — 上海图书馆东馆

- **candidate**：`49f2894e-2eae-4f57-bc97-f5ab7e0e0ba3`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`whole_building`
- **proposed rule**：dog · enter · 禁止 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 17. `lib-pets-op` — 上海图书馆东馆

- **candidate**：`330abc76-b6e2-402f-91b1-47596bd95965`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`whole_building`
- **proposed rule**：ordinary_pet · enter · 禁止 · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海图书馆官网《读者须知》
  - URL：https://www.library.sh.cn/guide/xuzhi
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 18. `lib-sd-legal` — 上海图书馆东馆

- **candidate**：`caa28a93-94e9-4643-b6c1-bbd5d77c3ecc`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`None`
- **proposed rule**：service_dog · enter · 允许 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 19. `lib-sd-op` — 上海图书馆东馆

- **candidate**：`76d0dfc3-64ae-4d2b-a152-18ff8ebed588`
- **place**：上海图书馆东馆（`lib-sh-library-east`）· zone：`whole_building`
- **proposed rule**：service_dog · enter · 允许 · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海图书馆官网《读者须知》
  - URL：https://www.library.sh.cn/guide/xuzhi
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 20. `mn-legal-dog` — Manner咖啡（凯德虹口商业中心店）

- **candidate**：`c2b179b9-77bf-433a-9219-5a406c42d5c7`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`）· zone：`indoor`
- **proposed rule**：dog · enter · 禁止 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 21. `mn-outdoor-media` — Manner咖啡（凯德虹口商业中心店）

- **candidate**：`ed79071d-d052-46b4-a216-dc789aae4128`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`）· zone：`outdoor_seating`
- **proposed rule**：ordinary_pet · enter · 有条件允许（leash_required） · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：搜索摘要（未核验原文）
- **source**：CBNData（Manner 首家宠物友好店报道）
  - URL：https://www.cbndata.com/information/255703
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`search_snippet`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**REJECT**
- **reason**：PLACE_ATTRIBUTION_ERROR —— 来源原文不支持该场所（错归因实锤）
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 22. `mn-sd-legal` — Manner咖啡（凯德虹口商业中心店）

- **candidate**：`52936479-c385-4279-814e-aa7fe8ab0a42`
- **place**：Manner咖啡（凯德虹口商业中心店）（`mn-kaidi-hongkou`）· zone：`None`
- **proposed rule**：service_dog · enter · 允许 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 23. `qt-indoor-legal` — 前滩太古里

- **candidate**：`8151db71-3622-429d-81bc-0a0212f23290`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`indoor`
- **proposed rule**：dog · enter · 禁止 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 24. `qt-indoor-op` — 前滩太古里

- **candidate**：`93fdbdf9-4855-45f8-8bd9-8af86715f748`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`indoor`
- **proposed rule**：ordinary_pet · enter · 禁止 · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：前滩太古里（太古地产）官网《宠物友好》页
  - URL：https://www.taikooliqiantan.com/detail/58.html
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：`qt-outdoor-op`（OPERATOR_POLICY · conditional · primary_direct）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 25. `qt-outdoor-op` — 前滩太古里

- **candidate**：`100d76af-c766-494d-8c25-2e29e2214b71`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`outdoor_open`
- **proposed rule**：ordinary_pet · enter · 有条件允许（leash_required、vaccination_required、max_count） · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：前滩太古里（太古地产）官网《宠物友好》页
  - URL：https://www.taikooliqiantan.com/detail/58.html
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：`qt-indoor-op`（OPERATOR_POLICY · prohibited · primary_direct）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 26. `qt-sd-legal` — 前滩太古里

- **candidate**：`958d4d4c-6cd5-467e-9bc4-5eae2f67630e`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`None`
- **proposed rule**：service_dog · enter · 允许 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 27. `qt-sd-op` — 前滩太古里

- **candidate**：`1249b621-1186-4366-a538-db04a6731fec`
- **place**：前滩太古里（`qt-taikoo-li`）· zone：`None`
- **proposed rule**：service_dog · enter · 允许 · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：官方/一手直抓（逐字）
- **source**：前滩太古里（太古地产）官网《宠物友好》页
  - URL：https://www.taikooliqiantan.com/detail/58.html
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 28. `sb-legal-dog` — 星巴克臻选上海烘焙工坊

- **candidate**：`1a97f24e-3cd0-445c-804d-741be34a0dad`
- **place**：星巴克臻选上海烘焙工坊（`sb-roastery`）· zone：`whole_store`
- **proposed rule**：dog · enter · 禁止 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 29. `sb-sd-legal` — 星巴克臻选上海烘焙工坊

- **candidate**：`b8cffbee-855a-4754-ad84-b01db0351ea3`
- **place**：星巴克臻选上海烘焙工坊（`sb-roastery`）· zone：`None`
- **proposed rule**：service_dog · enter · 允许 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 30. `xm-indoor-new` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate**：`9c8b4b26-a2cb-4efd-b188-aeee3a194951`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`indoor`
- **proposed rule**：ordinary_pet · enter · 禁止 · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：可靠二手（权威媒体直抓）
- **source**：新闻媒体（2026-08 星巴克宠物专区调整报道）
  - URL：None
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`secondary_reputable`
- **conflicts**：`xm-outdoor-media`（OPERATOR_POLICY · conditional · secondary_reputable）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 31. `xm-legal-dog` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate**：`6fc38502-85c7-4d7e-8a24-56fd5cc68e8a`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`indoor`
- **proposed rule**：dog · enter · 禁止 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 32. `xm-outdoor-media` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate**：`fb003b3a-3583-484b-b16f-7a6f3a1b71d0`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`outdoor_pet_area`
- **proposed rule**：ordinary_pet · enter · 有条件允许（leash_required） · layer：`OPERATOR_POLICY`（运营方政策） · mandatory_level：`operator_discretion`
- **evidence**：可靠二手（权威媒体直抓）
- **source**：新闻媒体（2026-08 星巴克宠物专区调整报道）
  - URL：None
  - license：display=True · redistribution=False · storage=True
- **evidence strength**：`secondary_reputable`
- **conflicts**：`xm-indoor-new`（OPERATOR_POLICY · prohibited · secondary_reputable）
- **AI recommendation**：**APPROVE**
- **reason**：EVIDENCE_TRACEABLE —— 证据可追溯、归属正确、许可允许
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

### 33. `xm-sd-legal` — 星巴克咖啡（徐汇西岸梦中心店）

- **candidate**：`6bf5128a-17ad-4a2f-83e5-eabecc7afb9f`
- **place**：星巴克咖啡（徐汇西岸梦中心店）（`xm-west-bund-gate-m`）· zone：`None`
- **proposed rule**：service_dog · enter · 允许 · layer：`LEGAL`（法规） · mandatory_level：`mandatory`
- **evidence**：官方/一手直抓（逐字）
- **source**：上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页）
  - URL：https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0bb43e938
  - license：display=True · redistribution=True · storage=True
- **evidence strength**：`primary_direct`
- **conflicts**：无（同归属同 scope/action 无相反效果）
- **AI recommendation**：**APPROVE_WITH_NOTE**
- **reason**：STATUTE_SCOPE_GENERALIZATION —— 法条原文为「盲人携带导盲犬」，建模为 service_dog 属 ADR-020 平台级泛化，须评审员确认
- **final_decision**：`________`（APPROVED / REJECTED / HOLD）
- **reviewer**：`________`
- **reviewed_at**：`________`

---

## 签署表（汇总）

| # | candidate | place | rule_id | proposed rule | AI 建议 | final_decision | reviewer | reviewed_at |
|---|---|---|---|---|---|---|---|---|
| 1 | `70cc7579` | 大吉路公园 | `dj-pilot` | ordinary_pet · enter · 有条件允许（leash_required） | APPROVE | | | |
| 2 | `f5a8d87f` | 上海迪士尼乐园 | `dl-legal-dog` | dog · enter · 禁止 | HOLD（pending） | | | |
| 3 | `cfe82cd4` | 上海迪士尼乐园 | `dl-pet-ban` | ordinary_pet · enter · 禁止 | APPROVE | | | |
| 4 | `393c6b89` | 上海迪士尼乐园 | `dl-sd-legal` | service_dog · enter · 允许 | APPROVE_WITH_NOTE | | | |
| 5 | `f799a74b` | 上海迪士尼乐园 | `dl-sd-op` | service_dog · enter · 有条件允许（leash_required） | APPROVE | | | |
| 6 | `c8a3f92b` | 和平饭店（费尔蒙） | `fp-legal-dog` | dog · enter · 禁止 | APPROVE | | | |
| 7 | `4c7aba30` | 和平饭店（费尔蒙） | `fp-pets-op` | ordinary_pet · enter · 禁止 | APPROVE | | | |
| 8 | `e94d2259` | 和平饭店（费尔蒙） | `fp-sd-legal` | service_dog · enter · 允许 | APPROVE_WITH_NOTE | | | |
| 9 | `7efddba6` | 和平饭店（费尔蒙） | `fp-sd-op` | service_dog · enter · 有条件允许 | APPROVE | | | |
| 10 | `8f98fd01` | 广场公园（黄浦段） | `gc-h6-pilot` | ordinary_pet · enter · 有条件允许（leash_required） | APPROVE | | | |
| 11 | `ffb804af` | 广场公园（黄浦段） | `gc-other-keep` | ordinary_pet · enter · 禁止 | HOLD（pending） | | | |
| 12 | `73448553` | 港汇恒隆广场 | `gh-indoor-new` | ordinary_pet · enter · 禁止 | APPROVE | | | |
| 13 | `70d10467` | 港汇恒隆广场 | `gh-legal-dog` | dog · enter · 禁止 | APPROVE | | | |
| 14 | `887f21ba` | 港汇恒隆广场 | `gh-outdoor-keep` | ordinary_pet · enter · 有条件允许（leash_required） | HOLD（pending） | | | |
| 15 | `d91706de` | 港汇恒隆广场 | `gh-sd-legal` | service_dog · enter · 允许 | APPROVE_WITH_NOTE | | | |
| 16 | `49f2894e` | 上海图书馆东馆 | `lib-legal-dog` | dog · enter · 禁止 | APPROVE | | | |
| 17 | `330abc76` | 上海图书馆东馆 | `lib-pets-op` | ordinary_pet · enter · 禁止 | APPROVE | | | |
| 18 | `caa28a93` | 上海图书馆东馆 | `lib-sd-legal` | service_dog · enter · 允许 | APPROVE_WITH_NOTE | | | |
| 19 | `76d0dfc3` | 上海图书馆东馆 | `lib-sd-op` | service_dog · enter · 允许 | APPROVE | | | |
| 20 | `c2b179b9` | Manner咖啡（凯德虹口商业中心店） | `mn-legal-dog` | dog · enter · 禁止 | APPROVE | | | |
| 21 | `ed79071d` | Manner咖啡（凯德虹口商业中心店） | `mn-outdoor-media` | ordinary_pet · enter · 有条件允许（leash_required） | REJECT | | | |
| 22 | `52936479` | Manner咖啡（凯德虹口商业中心店） | `mn-sd-legal` | service_dog · enter · 允许 | APPROVE_WITH_NOTE | | | |
| 23 | `8151db71` | 前滩太古里 | `qt-indoor-legal` | dog · enter · 禁止 | APPROVE | | | |
| 24 | `93fdbdf9` | 前滩太古里 | `qt-indoor-op` | ordinary_pet · enter · 禁止 | APPROVE | | | |
| 25 | `100d76af` | 前滩太古里 | `qt-outdoor-op` | ordinary_pet · enter · 有条件允许（leash_required、vaccination_required、max_count） | APPROVE | | | |
| 26 | `958d4d4c` | 前滩太古里 | `qt-sd-legal` | service_dog · enter · 允许 | APPROVE_WITH_NOTE | | | |
| 27 | `1249b621` | 前滩太古里 | `qt-sd-op` | service_dog · enter · 允许 | APPROVE | | | |
| 28 | `1a97f24e` | 星巴克臻选上海烘焙工坊 | `sb-legal-dog` | dog · enter · 禁止 | APPROVE | | | |
| 29 | `b8cffbee` | 星巴克臻选上海烘焙工坊 | `sb-sd-legal` | service_dog · enter · 允许 | APPROVE_WITH_NOTE | | | |
| 30 | `9c8b4b26` | 星巴克咖啡（徐汇西岸梦中心店） | `xm-indoor-new` | ordinary_pet · enter · 禁止 | APPROVE | | | |
| 31 | `6fc38502` | 星巴克咖啡（徐汇西岸梦中心店） | `xm-legal-dog` | dog · enter · 禁止 | APPROVE | | | |
| 32 | `fb003b3a` | 星巴克咖啡（徐汇西岸梦中心店） | `xm-outdoor-media` | ordinary_pet · enter · 有条件允许（leash_required） | APPROVE | | | |
| 33 | `6bf5128a` | 星巴克咖啡（徐汇西岸梦中心店） | `xm-sd-legal` | service_dog · enter · 允许 | APPROVE_WITH_NOTE | | | |

## 评审员声明（必填）

| 字段 | 值 |
|---|---|
| reviewer（具名） |  |
| reviewer_role |  |
| reviewed_at |  |
| 是否接受 APPROVE_WITH_NOTE 的 service_dog scope 泛化（ADR-020） | ☐ 是 ☐ 否 |
| 首批批准条数（≤ `--max-approve`） |  |
| 签名 |  |

> 签署后，将各行 `final_decision` / `reviewer` / `reviewed_at` 回填到
> `docs/reality_audit/review_decisions_r1.json`，再执行
> `python scripts/publish_reviewed_r1.py --execute --reviewer "<具名>"`。

