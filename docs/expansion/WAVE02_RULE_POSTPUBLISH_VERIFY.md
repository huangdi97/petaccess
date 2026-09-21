# WAVE02_RULE_POSTPUBLISH_VERIFY — 发布后验证

- 批次：`EXP-R1-W02-REVIEW-R1-BATCH-01` · revision：`EXP-R1-W02-REVIEW-R1`
- 验证时点：2026-09-21（本会话只读复核；DB = production `petaccess`）
- 前置：`WAVE02_RULE_PUBLISH_EXECUTION_REPORT.md`（REAL_PUBLISH_EXECUTED = YES，2026-09-21T13:20:04Z）
- 方式：真实 canonical resolver（`app.rulespec.v05_resolver.resolve`，与 Consumer API 同函数）直连 live DB；零写入。

## 1. Post-publish snapshot（live DB 只读复核）

```
access_rule_total       = 42   （Wave02 前 26 → 发布后 42，+16 恰为本批）
rule_exception_total    = 9    （不变，本批无例外写入）
published_in_window     = 16   （created_at ∈ [13:20:00, 13:21:00)）
wave02_candidates       = PUBLISHED 16（published_rule_id 非空 16）/ REVIEW_PENDING 4（published_rule_id 非空 0）
audit_in_window         = candidate.transition 16 · candidate.publish 16
```

- 4 条 HOLD（辰山、顾村 ×3）保持 `REVIEW_PENDING`，无 `published_rule_id` → **HOLD published = 0**。

## 2. Second-execute 幂等（同一发布器管线，dry-run 重放）

`scripts/publish_reviewed_r1.py --dry-run --batch-file EXP_R1_W02_REVIEW_R1_BATCH_01.json
--registry review_decisions_expansion_r1_wave02_publishable.json`

```
SELECTED               = 16
ACCESS_RULE_CREATE     = 0
RULE_EXCEPTION_CREATE  = 0
NOOP_COUNT             = 16   （全部 NOOP_ALREADY_EXISTS —— 已发布，不重复写）
BLOCKED_COUNT          = 0
BATCH_VALIDATION       = PASS
```

→ **second execute = NOOP**：重放同一批次不产生任何新写入。

## 3. Consumer 解析验证（真实 resolver，逐条 16/16）

对每条本批发布规则，用该规则自身的 zone 与 scope 构造消费者查询，调用
`v05_resolver.resolve`（legal/operator/exceptions 均从 live DB 按 place 加载），断言解析效应与发布一致：

```
上海野生动物园 [dog]     prohibited → prohibited  ✅
上海植物园 [cat]         prohibited → prohibited  ✅
豫园 [dog]               prohibited → prohibited  ✅
上海植物园 [other]       prohibited → prohibited  ✅
上海自然博物馆 [dog]      prohibited → prohibited  ✅
上海世博文化公园 [dog]    prohibited → prohibited  ✅
豫园 [guide_dog]         conditional→ conditional  ✅（导盲犬豁免可达）
上海植物园 [dog]         prohibited → prohibited  ✅
和平公园 [dog]           conditional → conditional ✅
上海世博文化公园 [other]  prohibited → prohibited  ✅
共青森林公园 [dog]        prohibited → prohibited  ✅
昆山公园 [dog]           conditional → conditional ✅
和平公园 [cat]           conditional → conditional ✅
共青森林公园 [other]      prohibited → prohibited  ✅
共青森林公园 [cat]        prohibited → prohibited  ✅
上海世博文化公园 [cat]    prohibited → prohibited  ✅
```

- verdict：**PASS（16 probes / problems 0）**；工具：`scripts/wave02_postpublish_verify.py`（只读）。

## 4. Evidence / Source / License / Freshness linkage

- 发布投影（`review_decisions_expansion_r1_wave02_publishable.json`）每行携带
  `evidence_bundle_id`、`artifact_id`、`source_id`、`license_metadata`、`last_verified_at`。
- 发布器回执 `audit_contract = {checked:16, missing_count:0, verdict:PASS}`；
  生产完整性扫描 `PUBLISHED_WITHOUT_EVIDENCE = 0`、`PUBLISHED_WITHOUT_SOURCE = 0`、
  `PUBLISHED_WITHOUT_AUDIT = 0`（见 closure §4）。
- 本批 16 条 `license_problems = 0`、`weak evidence = 0`（投影脚本实测统计）。

## 5. 结论

```
SECOND_EXECUTE_NOOP     = PASS（16/16 NOOP，零写入）
RESOLVER_MATCH          = PASS（16/16 效应一致）
HOLD_UNPUBLISHED        = PASS（4 条保持 REVIEW_PENDING）
EVIDENCE_LINKAGE        = PASS
SOURCE_LINKAGE          = PASS
AUDIT_LINKAGE           = PASS
LIVE_SNAPSHOT_CONSISTENT = PASS
```

收口判定见 `WAVE02_RULE_CLOSURE_REPORT.md`。