# HUMAN_SIGNATURE_READINESS_AUDIT.md

> 审计对象：`HUMAN_REVIEW_PACKET_R2_FINAL.md` / `HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md` / `HUMAN_REVIEW_DECISIONS_R2_FINAL.json`
> 内部 revision：**R2-FINAL-R2** · 机器登记表：`docs/reality_audit/review_decisions_r2_final.json`
> 本文件由 `scripts/gen_signature_readiness_audit_r1.py` 从登记表生成，数字与签署包同源。

## 1. 推荐分布（全量 37 行）

构成变化：33 行基线，上海图书馆复合词拆分 +2，和平饭店一手来源改建 +2，共 37 行。

| 建议 | 条数 |
|---|---|
| `RECOMMEND_REJECT` | **5** |
| `RECOMMEND_HOLD` | **9** |
| `RECOMMEND_APPROVE` | **23** |
| **合计** | **37** |

## 2. 每个 HOLD / REJECT 的原因

### 2.1 `RECOMMEND_REJECT`（5 条）

| rule_id | 场所 | 结论 | 原因 | 证据链实况 |
|---|---|---|---|---|
| `fp-pets-op` | 和平饭店（费尔蒙） | SUPERSEDED_BY_FIRST_PARTY_SOURCE | SUPERSEDED_BY_FIRST_PARTY_SOURCE | strength=`search_snippet` / directness=`tertiary` / url=`有` |
| `fp-sd-op` | 和平饭店（费尔蒙） | SUPERSEDED_BY_FIRST_PARTY_SOURCE | SUPERSEDED_BY_FIRST_PARTY_SOURCE | strength=`search_snippet` / directness=`tertiary` / url=`有` |
| `gc-other-keep` | 广场公园（黄浦段） | CLAIM_NOT_SUPPORTED_BY_QUOTE | REJECT_CURRENT_CLAIM | strength=`primary_direct` / directness=`direct` / url=`有` |
| `gh-outdoor-keep` | 港汇恒隆广场 | INSUFFICIENT_PLACE_ZONE_EVIDENCE | REJECT_CURRENT_CLAIM | strength=`search_snippet` / directness=`secondary` / url=`有` |
| `mn-outdoor-media` | Manner咖啡（凯德虹口商业中心店） | PLACE_ATTRIBUTION_ERROR | REJECT_CURRENT_CLAIM | strength=`search_snippet` / directness=`secondary` / url=`有` |

- **`fp-pets-op`** — SUPERSEDED_BY_FIRST_PARTY_SOURCE：SOURCE_NOT_OPERATOR_OF_RECORD；替代行：fp-pets-op-firstparty
- **`fp-sd-op`** — SUPERSEDED_BY_FIRST_PARTY_SOURCE：SOURCE_NOT_OPERATOR_OF_RECORD；替代行：fp-sd-op-firstparty
- **`gc-other-keep`** — REJECT_CURRENT_CLAIM：INSUFFICIENT_PLACE_ZONE_EVIDENCE
- **`gh-outdoor-keep`** — REJECT_CURRENT_CLAIM：LEGAL_SCOPE_CONFLICT
- **`mn-outdoor-media`** — REJECT_CURRENT_CLAIM：INSUFFICIENT_PLACE_ZONE_EVIDENCE

### 2.2 `RECOMMEND_HOLD`（9 条）

| rule_id | 场所 | 结论 | 原因 | 证据链实况 |
|---|---|---|---|---|
| `dj-pilot` | 大吉路公园 | FRESHNESS_INCOMPLETE | TEMPORARY_STATUS_NOT_REVERIFIED | strength=`primary_direct` / directness=`direct` / url=`有` |
| `dl-legal-dog` | 上海迪士尼乐园 | APPLICABILITY_EVIDENCE_MISSING | STATUTORY_APPLICABILITY_NOT_EVIDENCED | strength=`primary_direct` / directness=`direct` / url=`有` |
| `dl-sd-legal` | 上海迪士尼乐园 | APPLICABILITY_EVIDENCE_MISSING | STATUTORY_APPLICABILITY_NOT_EVIDENCED | strength=`primary_direct` / directness=`direct` / url=`有` |
| `gc-h6-pilot` | 广场公园（黄浦段） | FRESHNESS_INCOMPLETE | TEMPORARY_STATUS_NOT_REVERIFIED | strength=`primary_direct` / directness=`direct` / url=`有` |
| `gh-indoor-new` | 港汇恒隆广场 | 证据强度 search_snippet 未达一手标准（ADR-021） | EVIDENCE_CHAIN_INCOMPLETE | strength=`search_snippet` / directness=`secondary` / url=`有` |
| `lib-sd-op-military` | 上海图书馆东馆 | LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED | LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED | strength=`primary_direct` / directness=`direct` / url=`有` |
| `lib-sd-op-police` | 上海图书馆东馆 | LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED | LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED | strength=`primary_direct` / directness=`direct` / url=`有` |
| `xm-indoor-new` | 星巴克咖啡（徐汇西岸梦中心店） | 证据强度 search_snippet 未达一手标准（ADR-021） | EVIDENCE_CHAIN_INCOMPLETE | strength=`search_snippet` / directness=`secondary` / url=`有` |
| `xm-outdoor-media` | 星巴克咖啡（徐汇西岸梦中心店） | 证据强度 search_snippet 未达一手标准（ADR-021） | EVIDENCE_CHAIN_INCOMPLETE | strength=`search_snippet` / directness=`secondary` / url=`有` |

- **`dj-pilot`** — TEMPORARY_STATUS_NOT_REVERIFIED：未复核该临时/试点政策当前是否仍有效
- **`dl-legal-dog`** — STATUTORY_APPLICABILITY_NOT_EVIDENCED：场所类型 place_type=scenic_area 不属于第二十三条枚举的任一类别（办公楼/学校/医院/体育场馆/博物馆/图书馆/文化娱乐场所/候车（机、船）室/餐饮场所/商场/宾馆）；将其纳入该法条适用范围属法律解释，需显式证据支撑。
- **`dl-sd-legal`** — STATUTORY_APPLICABILITY_NOT_EVIDENCED：场所类型 place_type=scenic_area 不属于第二十三条枚举的任一类别（办公楼/学校/医院/体育场馆/博物馆/图书馆/文化娱乐场所/候车（机、船）室/餐饮场所/商场/宾馆）；将其纳入该法条适用范围属法律解释，需显式证据支撑。
- **`gc-h6-pilot`** — TEMPORARY_STATUS_NOT_REVERIFIED：未复核该临时/试点政策当前是否仍有效
- **`gh-indoor-new`** — EVIDENCE_CHAIN_INCOMPLETE：source.directness=secondary / issuer_verification=verified / needs_verification=True —— 不代表运营方一手来源；bundle.license_metadata 为空
- **`lib-sd-op-military`** — LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED：该运营方豁免会放宽已生效的法规禁令 `lib-legal-dog`，但尚无针对 `military_working_dog` 的法律/行政依据；运营方政策不得作为法律禁令的例外（原则 B/C）。
- **`lib-sd-op-police`** — LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED：该运营方豁免会放宽已生效的法规禁令 `lib-legal-dog`，但尚无针对 `police_dog` 的法律/行政依据；运营方政策不得作为法律禁令的例外（原则 B/C）。
- **`xm-indoor-new`** — EVIDENCE_CHAIN_INCOMPLETE：source.directness=secondary / issuer_verification=verified / needs_verification=True —— 不代表运营方一手来源；bundle.license_metadata 为空
- **`xm-outdoor-media`** — EVIDENCE_CHAIN_INCOMPLETE：source.directness=secondary / issuer_verification=verified / needs_verification=True —— 不代表运营方一手来源；bundle.license_metadata 为空

## 3. Enum consistency（决策词表一致性）


| 检查项 | 值 |
|---|---|
| canonical set (human_decisions.py) | `APPROVED` | `APPROVED_WITH_NOTE` | `HOLD` | `REJECTED` |
| 登记表 human_decisions | `APPROVED` | `APPROVED_WITH_NOTE` | `HOLD` | `REJECTED` |
| 逐条决策文件 human_decisions | `APPROVED` | `APPROVED_WITH_NOTE` | `HOLD` | `REJECTED` |
| 发布器接受的执行值 | APPROVED / APPROVED_WITH_NOTE / REJECTED（HOLD 为不发布） |
| 速填表是否出现 APPROVE/REJECT | **否** |

结论：速填表、登记表与发布器**共用同一词表**（`scripts/human_decisions.py`），不存在别名，也不再有 `APPROVED_WITH_NOTE` 被误判为拒绝的路径。

## 4. Provenance consistency（证据链一致性）

- 登记表自述强度与证据链推导**不一致的行**：**5**（这些行不再按自述强度放行）
- `source.source_url` 与 `bundle.source_url` **不一致的行**：**3**（逐条已并列展示，不再出现「引文取自 A 页、URL 写着 B 页」的静默矛盾）

| rule_id | 自述 | 链推导 | 链实况 | 处置 |
|---|---|---|---|---|
| `fp-pets-op` | `primary_direct` | `search_snippet` | directness=`tertiary` | RECOMMEND_REJECT |
| `fp-sd-op` | `primary_direct` | `search_snippet` | directness=`tertiary` | RECOMMEND_REJECT |
| `gh-indoor-new` | `secondary_reputable` | `search_snippet` | directness=`secondary` | RECOMMEND_HOLD |
| `xm-indoor-new` | `secondary_reputable` | `search_snippet` | directness=`secondary` | RECOMMEND_HOLD |
| `xm-outdoor-media` | `secondary_reputable` | `search_snippet` | directness=`secondary` | RECOMMEND_HOLD |

**和平饭店一手来源链（本轮修复）**

- `fp-pets-op-firstparty`：issuer=费尔蒙上海和平饭店官网《宾客信息·宠物政策》 · verification=`verified` · strength=`primary_direct` · url=https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html
- `fp-sd-op-firstparty`：issuer=费尔蒙上海和平饭店官网《宾客信息·宠物政策》 · verification=`verified` · strength=`primary_direct` · url=https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html

> 两个 OTA 行（`fp-sd-op` / `fp-pets-op`）被取代并建议 REJECT，**旧证据与 audit history 一条未删**。

## 5. Freshness completeness（时效完整性）

- 有时效性的行（`TEMPORARY_POLICY` / `REGULATORY_GUIDANCE`）：**2**
- 其中时效信息**不完整**：**2**（均已 HOLD 或标注）
- 常态化法规/运营方政策不强制 `effective_to`（长期有效属正常），因此不会因「没有到期日」被误判为缺陷。

| rule_id | layer | effective_from | effective_to | open-ended | last_verified_at | 缺口 | 建议 |
|---|---|---|---|---|---|---|---|
| `dj-pilot` | `TEMPORARY_POLICY` | 2025-09-01T00:00:00+00:00 | — | — | 2026-09-13 | 缺 effective_to 且未记录 open-ended 原因；缺 last_verified_at（捕获时间不能代替「当前是否仍有效」的复核） | RECOMMEND_HOLD |
| `gc-h6-pilot` | `TEMPORARY_POLICY` | 2025-09-01T00:00:00+00:00 | — | — | 2026-09-13 | 缺 effective_to 且未记录 open-ended 原因；缺 last_verified_at（捕获时间不能代替「当前是否仍有效」的复核） | RECOMMEND_HOLD |

## 6. Licence completeness（授权完整性）

- licence 记录**不完整**的行：**5** / 37
- licence 三态齐备的行：**32**

| rule_id | 缺口 | 建议 |
|---|---|---|
| `fp-pets-op` | bundle.license_metadata 为空 | RECOMMEND_REJECT |
| `fp-sd-op` | bundle.license_metadata 为空 | RECOMMEND_REJECT |
| `gh-indoor-new` | bundle.license_metadata 为空 | RECOMMEND_HOLD |
| `xm-indoor-new` | bundle.license_metadata 为空 | RECOMMEND_HOLD |
| `xm-outdoor-media` | bundle.license_metadata 为空 | RECOMMEND_HOLD |

> 缺口集中在那批以媒体转述为源的候选；它们同时缺少可核验取证位置，因此一并 HOLD，而不是靠 `EVIDENCE_TRACEABLE` 字样通过。

## 7. RuleException binding（层内绑定 · RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE）

| 检查项 | 结果 |
|---|---|
| 绑定策略 | `same-layer-only`（LEGAL 例外 → LEGAL base；OPERATOR carve-out → OPERATOR base） |
| 跨层绑定（cross-layer override） | **0** |
| HOLD / REJECT 基础规则收到「可执行例外」 | **0** |
| Legal / Operator 例外分离 | **PASS** |
| 旧算法遗留、已丢弃的跨层绑定（仅记录） | **6** |

**RuleException binding table**

| 例外行 | 层 | 精确 scope | 绑定基础规则（层） | base 裁决 | 可执行 |
|---|---|---|---|---|---|
| `dl-sd-legal` | LEGAL | `guide_dog` | `dl-legal-dog`（LEGAL） | HOLD | ❌ |
| `lib-sd-op-military` | OPERATOR_POLICY | `military_working_dog` | `lib-pets-op`（OPERATOR_POLICY） | APPROVE | ❌ |
| `lib-sd-op-police` | OPERATOR_POLICY | `police_dog` | `lib-pets-op`（OPERATOR_POLICY） | APPROVE | ❌ |
| `dl-sd-op` | OPERATOR_POLICY | `guide_dog` | `dl-pet-ban`（OPERATOR_POLICY） | APPROVE | ✅ |
| `fp-sd-legal` | LEGAL | `guide_dog` | `fp-legal-dog`（LEGAL） | APPROVE | ✅ |
| `fp-sd-op-firstparty` | OPERATOR_POLICY | `guide_dog` | `fp-pets-op-firstparty`（OPERATOR_POLICY） | APPROVE | ✅ |
| `gh-sd-legal` | LEGAL | `guide_dog` | `gh-legal-dog`（LEGAL） | APPROVE | ✅ |
| `lib-sd-legal` | LEGAL | `guide_dog` | `lib-legal-dog`（LEGAL） | APPROVE | ✅ |
| `lib-sd-op-guide` | OPERATOR_POLICY | `guide_dog` | `lib-pets-op`（OPERATOR_POLICY） | APPROVE | ✅ |
| `mn-sd-legal` | LEGAL | `guide_dog` | `mn-legal-dog`（LEGAL） | APPROVE | ✅ |
| `qt-sd-legal` | LEGAL | `guide_dog` | `qt-indoor-legal`（LEGAL） | APPROVE | ✅ |
| `qt-sd-op` | OPERATOR_POLICY | `guide_dog` | `qt-indoor-op`（OPERATOR_POLICY） | APPROVE | ✅ |
| `sb-sd-legal` | LEGAL | `guide_dog` | `sb-legal-dog`（LEGAL） | APPROVE | ✅ |
| `xm-sd-legal` | LEGAL | `guide_dog` | `xm-legal-dog`（LEGAL） | APPROVE | ✅ |

> 下列行在旧（层盲）算法下曾被指向更高一层的规则；现已丢弃，**不进入绑定表**：
> - `lib-sd-op-military` ← `lib-legal-dog`
> - `lib-sd-op-police` ← `lib-legal-dog`
> - `dl-sd-op` ← `dl-legal-dog`
> - `fp-sd-op-firstparty` ← `fp-legal-dog`
> - `lib-sd-op-guide` ← `lib-legal-dog`
> - `qt-sd-op` ← `qt-indoor-legal`

> 运营方豁免只在自身层内替换运营方 base；LEGAL 禁令不因任何运营方「允许」而放宽（原则 B/C/D）。未具法律依据者（上海图书馆 军警犬）已 HOLD。

## 8. Registry selected path（发布器将读取哪一份）

| 项 | 值 |
|---|---|
| 解析顺序 | `review_decisions_r2_final.json` → `review_decisions_r2.json` → `review_decisions_r1.json` |
| **实际选中** | `docs/reality_audit/review_decisions_r2_final.json` |
| revision | `R2-FINAL-R2` |
| 行数 | 37 |

结论：发布器读取的是**最新 final 登记表**，不会回退到旧 `review_decisions_r2.json`。

## 9. 签署状态

| 字段 | 状态 |
|---|---|
| final_decision | 全部空白 ✅ |
| reviewer | 全部空白 ✅ |
| reviewed_at | 全部空白 ✅ |

Agent **未**填写任何一条签署字段。

### 决策取值提示

| 值 | 含义 |
|---|---|
| `APPROVED` | 批准 |
| `APPROVED_WITH_NOTE` | 批准（附注意见） |
| `HOLD` | 挂起（证据不足） |
| `REJECTED` | 拒绝 |

## 10. 结论

| 门 | 结论 |
|---|---|
| A Animal Scope | PASS |
| C Consumer UX | PASS |
| B Publish | BLOCKED_HUMAN（9 HOLD + 5 REJECT 待人类裁决） |
| RuleException 层间隔离 | PASS（跨层绑定 0） |
| 30–50 Place 扩量 | NOT_ALLOWED |

**GOV01_READY_FOR_HUMAN_SIGNATURE = YES**

