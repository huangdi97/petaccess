# WAVE02_PUBLISHABILITY_DISPOSITION — 16 条可发布 / 4 条不可发布（已签）

- revision：`EXP-R1-W02-REVIEW-R1` · expansion_run_id：`EXP-R1-W02-20260919`
- reviewer：`huangdi97` · 判定时间：2026-09-21
- 依据：已签登记表 `docs/expansion/review_decisions_expansion_r1_wave02.json` + 真实 `publish_gate.evaluate_for_publish`（`scripts/wave02_prepublish_dryrun.py` 只读执行）

## 1. 汇总

```
HUMAN_APPROVED            = 16
HUMAN_HOLD                = 4
HUMAN_REJECTED            = 0
GATE_PASS                 = 16   （全部 APPROVED 均过真实预发布 gate）
GATE_BLOCKED              = 0
PUBLISHABLE               = 16
NOT_PUBLISHABLE           = 4    （全部为 HOLD，非 gate 阻止）
REAL_PUBLISH_EXECUTED     = NO
```

## 2. 可发布列表（16，按批次执行顺序 = base-before-exception）

| # | candidate_id | place | scope | effect | gate |
|---|---|---|---|---|---|
| 1 | 7774a487-dbe4-462a-9c36-433803a3563e | 上海世博文化公园 | dog | prohibited | PASS |
| 2 | afe409b1-3a21-41a5-bd3c-aa0996477c44 | 上海世博文化公园 | other | prohibited | PASS |
| 3 | f80c6071-28f0-4fe7-837d-41d6752ed0a4 | 上海世博文化公园 | cat | prohibited | PASS |
| 4 | 4b4b4e07-73e9-4a47-8728-cff6b3e1488a | 上海植物园 | cat | prohibited | PASS |
| 5 | 630e1c0d-c9b6-4a15-ad8d-d31e3268b126 | 上海植物园 | other | prohibited | PASS |
| 6 | 97d564fa-4de4-418a-bc40-ddcca0c1e8ea | 上海植物园 | dog | prohibited | PASS |
| 7 | 700dcd4d-6e15-4d87-bf13-5b77cab049cb | 上海自然博物馆 | ordinary_pet | prohibited | PASS |
| 8 | 237512f7-6ce0-43cb-a207-4481dd6e9056 | 上海野生动物园 | ordinary_pet | prohibited | PASS |
| 9 | c111a1a1-6660-43fe-a663-dd19e0c1d6eb | 共青森林公园 | dog | prohibited | PASS |
| 10 | eba1843a-46d2-4aab-9553-9efcbf74a5c5 | 共青森林公园 | other | prohibited | PASS |
| 11 | ec883c91-5c80-4754-8309-f6791ec9e565 | 共青森林公园 | cat | prohibited | PASS |
| 12 | 98d2b355-4fc1-4c15-ac7a-6b44188636ea | 和平公园 | dog | conditional | PASS |
| 13 | da0c270c-71b1-4163-bb4a-095ba6bfe8d7 | 和平公园 | cat | conditional | PASS |
| 14 | d5551907-08dc-4d66-a6b7-50631c81581e | 昆山公园 | dog | conditional | PASS |
| 15 | 5f22e9a1-fd74-44a2-a0d4-312d98939ba2 | 豫园 | ordinary_pet | prohibited | PASS（base） |
| 16 | 91970069-b691-4c3f-bd48-c4fca505e349 | 豫园 | service_dog（guide_dog） | conditional | PASS（carve-out，base 之后） |

## 3. 不可发布列表（4，HOLD — 来源核验缺口，非 gate 阻止）

| candidate_id | place | scope | final_decision | decision_note |
|---|---|---|---|---|
| 81eca767-c5dc-4c60-b165-a38e5db0aecd | 上海辰山植物园 | ordinary_pet | HOLD | OFFICIAL_PAGE_VERBATIM_VERIFICATION_REQUIRED |
| 36f6382f-ecd9-4b89-8109-db341f3876fa | 顾村公园 | dog | HOLD | SECONDARY_SOURCE_NEEDS_FIRST_PARTY_CONFIRMATION |
| b6abed36-993c-4861-981b-b392f917a07d | 顾村公园 | other | HOLD | SECONDARY_SOURCE_NEEDS_FIRST_PARTY_CONFIRMATION |
| c6c5b74d-86ec-45e8-b412-2db94e934969 | 顾村公园 | cat | HOLD | SECONDARY_SOURCE_NEEDS_FIRST_PARTY_CONFIRMATION |

- 辰山：官网页面可达但禁用句为外部收录（directness=secondary / needs_verification），逐字核验官网原页后可转入 APPROVED。
- 顾村 ×3：本地宝转述（external_web_reference / secondary），按 §27 二级来源仅作 lead；核实圃方一手来源后可转入 APPROVED。

> 这 4 条保持 `REVIEW_PENDING`（DB 不变），登记表签 HOLD；**不得**因 gate 未测而标注 PUBLISHABLE，也不得删除人类 HOLD。

## 4. 不变量

- HOLD published = 0 · REJECTED published = 0 · excluded approved published = 0
- inert exception = 0 · cross-layer exception = 0 · obsolete semantic execution = 0
- UNKNOWN auto-allowed = 0 · unexpected mutation = 0
- CRITICAL integrity = 0 · HIGH integrity = 0（本会话生产完整性实测，见 V09 §5.5）
- 本判定**未写任何 DB**（gate 评估 Session 只读）。

```
HUMAN_ACTION_REQUIRED = WAVE02_REAL_PUBLISH_AUTHORIZATION
```