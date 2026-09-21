# WAVE02_RULE_PUBLISH_EXECUTION_REPORT — 真实发布执行记录

- 批次：`EXP-R1-W02-REVIEW-R1-BATCH-01` · revision：`EXP-R1-W02-REVIEW-R1`
- expansion_run_id：`EXP-R1-W02-20260919` · reviewer：`huangdi97`
- 执行入口：`scripts/publish_reviewed_r1.py --execute --batch-file … --registry … --production-confirm`
- 状态：**REAL_PUBLISH_EXECUTED = YES** · 本文件只记录已发生事实，不改写任何人工裁决、不回滚任何已完成写入。

## 1. 事实（数据库 / audit / 回执三方一致）

- 发布执行时点：`2026-09-21T13:20:04.808199+00:00`（回执 `artifacts/wave02_publish_receipt.json`，`mode=execute`）。
- 回执 counts：`approved=16 · rejected=0 · held=0 · published=16 · failed=0`。
- 回执 audit contract：`checked=16 · missing_count=0 · exception_audit_without_base=0 · verdict=PASS`。
- 落库审计（本会话只读复核，`created_at ∈ [13:20:00, 13:21:00)`）：
  - `candidate.transition` ×16（REVIEW_PENDING → PUBLISHED）
  - `candidate.publish` ×16（access_rule 新建）
- 落库对象：16 条 `access_rule`（`publication_type=CREATE_ACCESS_RULE`，全部 `layer_preserved=true / mandatory_preserved=true`），
  `access_rule` 总数 26 → **42**；`rule_exception` 保持 **9** 不变（本批无例外写入，豫园导盲犬按 ADR-025 建模为独立 conditional 规则，非 rule_exception）。
- 候选状态：20 条 Wave02 候选中 **16 PUBLISHED**（`published_rule_id` 均非空）/ **4 REVIEW_PENDING**（辰山 + 顾村 ×3，HOLD 未发布，`published_rule_id` 均空）。

## 2. 发布明细（rule_id → 落库 access_rule UUID）

| # | rule_id | 场所 | scope | effect | 落库 access_rule |
|---|---|---|---|---|---|
| 1 | w02-237512f76c | 上海野生动物园 | ordinary_pet | prohibited | `54a029b0-…` |
| 2 | w02-4b4b4e0773 | 上海植物园 | cat | prohibited | `ab9d515b-…` |
| 3 | w02-5f22e9a1fd | 豫园 | ordinary_pet | prohibited | `9cff3642-…` |
| 4 | w02-630e1c0dc9 | 上海植物园 | other | prohibited | `7ca334f5-…` |
| 5 | w02-700dcd4d6e | 上海自然博物馆 | ordinary_pet | prohibited | `80c60605-…` |
| 6 | w02-7774a487db | 上海世博文化公园 | dog | prohibited | `bae59ddf-…` |
| 7 | w02-91970069b6 | 豫园 | service_dog（guide_dog） | conditional（豁免） | `51d997e7-…` |
| 8 | w02-97d564fa4d | 上海植物园 | dog | prohibited | `f3891992-…` |
| 9 | w02-98d2b3554f | 和平公园 | dog | conditional | `c81a71d2-…` |
| 10 | w02-afe409b13a | 上海世博文化公园 | other | prohibited | `b0ec1fb7-…` |
| 11 | w02-c111a1a166 | 共青森林公园 | dog | prohibited | `c7ceabab-…` |
| 12 | w02-d555190708 | 昆山公园 | dog | conditional | `f06adaee-…` |
| 13 | w02-da0c270c71 | 和平公园 | cat | conditional | `ff574bec-…` |
| 14 | w02-eba1843a46 | 共青森林公园 | other | prohibited | `f006162d-…` |
| 15 | w02-ec883c915c | 共青森林公园 | cat | prohibited | `44134bf3-…` |
| 16 | w02-f80c607128 | 上海世博文化公园 | cat | prohibited | `53fb9b28-…` |

> 完整 UUID 见 `artifacts/wave02_publish_receipt.json`（16 条 `detail.published[]`）。

## 3. 执行前与执行对象

- 依赖顺序：豫园 base（w02-5f22e9a1fd）先于导盲犬豁免（w02-91970069b6）；其余规则无跨行依赖。
- 登记表：`docs/expansion/review_decisions_expansion_r1_wave02.json`（已签：16 APPROVED / 4 HOLD，reviewer=huangdi97）
- 发布器消费投影：`docs/expansion/review_decisions_expansion_r1_wave02_publishable.json`
- 批次清单：`docs/expansion/WAVE02_SAFE_BATCH_MANIFESTS/EXP_R1_W02_REVIEW_R1_BATCH_01.json`
- 真实 gate：16/16 `PREPUBLISH_PASS`，无 HOLD/REJECTED 入选，无跨层、无 inert、无 supersede 冲突。

## 4. 结论

```
REAL_PUBLISH_EXECUTED   = YES（2026-09-21T13:20:04Z，16 条 CREATE_ACCESS_RULE）
FAILED                  = 0
HOLD_PUBLISHED          = 0
REJECTED_PUBLISHED      = 0
SECOND_EXECUTE          = NOOP（见 WAVE02_RULE_POSTPUBLISH_VERIFY.md §2）
CRITICAL / HIGH         = 0 / 0（见 WAVE02_RULE_CLOSURE_REPORT.md §4）
```

详细后验见 `WAVE02_RULE_POSTPUBLISH_VERIFY.md`，收口判定见 `WAVE02_RULE_CLOSURE_REPORT.md`。