# Wave 01 真实发布执行报告 — EXP-R1-W01-REVIEW-R1-BATCH-01A

状态：**REAL_PUBLISH_EXECUTED = YES** · 本文件只记录事实，不回改任何人工裁决。

---

## 1. 授权

Human Reviewer / Project Owner `huangdi97` 显式授权发布
`EXP_R1_W01_REVIEW_R1_BATCH_01A` 中的 **5 条**：

| # | rule_id | 场所 | 层 | 类型 |
|---|---------|------|----|------|
| 1 | `w01-1fb3d7f1c7` | 兴业太古汇 | LEGAL | CREATE_ACCESS_RULE |
| 2 | `w01-4710a68f56` | 上海博物馆东馆 | OPERATOR_POLICY | CREATE_ACCESS_RULE |
| 3 | `w01-fa5f33f122` | 上海博物馆东馆 | LEGAL | CREATE_ACCESS_RULE |
| 4 | `w01-6482477d8d` | 兴业太古汇 | LEGAL | CREATE_RULE_EXCEPTION（base = #1） |
| 5 | `w01-73de8e3357` | 上海博物馆东馆 | LEGAL | CREATE_RULE_EXCEPTION（base = #3） |

授权**不覆盖**其余 10 条 APPROVED，也不覆盖任何 HOLD / REJECTED。

## 2. 执行前 recheck（§1）

| 检查 | 结果 |
|------|------|
| 发布前生产库指纹 | `584c97ba…450b345308`（AccessRule 5 / RuleException 3 / audit 9608） |
| `BATCH_SELECTED` | 5 |
| `BATCH_ACCESS_RULE` / `BATCH_RULE_EXCEPTION` | 3 / 2 |
| `BATCH_DEPENDENCY_CLOSED` | PASS |
| `ZERO_INERT_RULES` | PASS |
| `CROSS_LAYER_EXCEPTION` / `UNREACHABLE_SELECTED` | 0 / 0 |
| `PREPUBLISH_PASS` / `BLOCKED` | 5 / 0 |
| `BLOCKED_COUNT` | 0 |

→ 5/5 通过，允许执行。

## 3. 真实发布结果

入口：`scripts/publish_reviewed_r1.py --execute --reviewer huangdi97
--batch-file docs/governance/publish_batches/EXP_R1_W01_REVIEW_R1_BATCH_01A.json
--registry docs/expansion/review_decisions_expansion_r1_wave01_publishable.json
--production-confirm`（PRODUCTION = `petaccess`）。

发布器回执：

```
counts.published = 5   counts.failed = 0
audit_contract.verdict = PASS (checked=5, missing_count=0)
```

实际落库对象：

| rule_id | 对象 | 落库 UUID |
|---------|------|-----------|
| `w01-1fb3d7f1c7` | access_rule | `47a1d679-1c19-4422-b3b9-02451a19adb8` |
| `w01-4710a68f56` | access_rule | `f07ffa88-bc3c-4d77-ab38-40f137f225bb` |
| `w01-fa5f33f122` | access_rule | `ca0b01c2-10b2-47ea-87bd-f76ac813d1f2` |
| `w01-6482477d8d` | rule_exception（base `47a1d679…`） | `64262b3b-d97f-4501-a059-c502deb75e9d` |
| `w01-73de8e3357` | rule_exception（base `ca0b01c2…`） | `39cbdef1-179d-441a-8001-6122ca18bce8` |

库计数：AccessRule 5→8（+3），RuleException 3→5（+2），audit_log 9608→9618（+10）。
发布后指纹 `e9f5f4ea…83489b16`。

## 4. 幂等（§5 §14）

第二次执行同一清单：`NOOP_COUNT = 5`、`ACCESS_RULE_CREATE_COUNT = 0`、
`RULE_EXCEPTION_CREATE_COUNT = 0`、`BLOCKED_COUNT = 0`，5 条全为
`NOOP_ALREADY_EXISTS`。第二次执行前后指纹完全相同 →
**第二执行零写入**。

## 5. 发布后语义（§6）

Resolver 直接探针（读取生产库真实行，`app.rulespec.v05_resolver.resolve`）：

| 查询 | 期望 | 实际 | 生效规则 | compliance |
|------|------|------|----------|-----------|
| 兴业太古汇 · 普通犬 | prohibited | **prohibited** | base `47a1d679…` | CONSISTENT |
| 兴业太古汇 · 导盲犬 | allowed | **allowed** | `exc-64262b3b…` | CONSISTENT |
| 上博东馆 · 普通宠物 | prohibited | **prohibited** | `f07ffa88…` | CONSISTENT |
| 上博东馆 · 普通犬 | prohibited | **prohibited** | `ca0b01c2…` + `f07ffa88…` | CONSISTENT |
| 上博东馆 · 导盲犬 | allowed | **allowed** | `exc-39cbdef1…` | CONSISTENT |

消费者 HTTP 路径（`POST /api/v1/places/{id}/effective-rules`）返回一致结果，
导盲犬查询显式给出：

```
"effect":"allowed",
"applied_exceptions":["64262b3b-…"],
"suppressed":[{"rule":"47a1d679-…",
  "reason":"exempted by exception 64262b3b-… (scope guide_dog · carve-out, source a11aff10-…)"}]
```

**这是本轮最关键的事实**：基底是 `dog`（含全部犬类角色），例外是
`guide_dog`——基底**语义上确实管辖**导盲犬，因此例外**可达**、真实生效，
不是惰性例外（`INERT_EXCEPTION = 0`）。

## 6. 链接与绑定（§7 §10）

- 5 行全部有 `source_id`，来源 `directness=direct`、`source_availability=available_online`：
  - 4 条 LEGAL → `a11aff10-…`《上海市养犬管理条例》（statute_or_regulation）
  - 1 条 OPERATOR_POLICY → `17f4080a-…` 上海博物馆官网《到访·东馆》（official_operator_policy）
- 两个来源均有 `active` 监控：上博 `url_hash` / 1440 分钟，条例 `url_hash` / 10080 分钟。
- 审计：5 个对象各有且仅有 1 条——3× `candidate.publish`（access_rule）、
  2× `candidate.publish_exception`（rule_exception）；`exception_audit_without_base = 0`。

## 7. 排除项与负向验证（§11）

| 检查 | 结果 |
|------|------|
| 10 条被排除 APPROVED 是否被发布 | **0**（全部仍 `REVIEW_PENDING`，`published_rule_id` 为空） |
| HOLD / REJECTED 是否被发布 | **0** |
| `CROSS_LAYER_EXCEPTION` | 0 |
| `INERT_EXCEPTION` | 0 |
| `UNREACHABLE_SELECTED` | 0 |

**收窄批次不推翻任何人工决定**：10 条被排除者仍在签署登记表中保持 `APPROVED`，
只是 `publishable=false`，未被撤销。

## 8. 生产库完整性（§12）

`scripts/check_production_integrity.py`：**PASS**，23 项检查。

- CRITICAL = **0**（含 `HOLD_OR_REJECTED_PUBLISHED`、`CROSS_LAYER_EXCEPTION`、
  `ORPHAN_RULE_EXCEPTION`、`CONFLICTING_CURRENT_RULES`、`SELF_SUPERSEDE`、`SUPERSESSION_CYCLE`）
- HIGH = **0**（含 `PUBLISHED_WITHOUT_AUDIT`、`PUBLISHED_WITHOUT_EVIDENCE`、
  `PUBLISHED_WITHOUT_SOURCE`、`PUBLISHED_OBJECT_WITHOUT_CANDIDATE`、`DUPLICATE_CURRENT_RULE`）
- MEDIUM = **1**：`AUDIT_TARGET_ID_UNUSABLE` 历史 2647 行——**发布前既有**，
  与本批次无关，已在 `PRODUCTION_INTEGRITY_LIMITATION_FINAL_CLOSURE.md` 中解释。

## 9. 唯一发现（非本批次缺陷）

`GET /api/v1/places/{id}/answerability` 对两地点返回
`ordinary_dog_entry = unknown（"从未核验"）`、`service_dog = unknown（"无服务犬规则"）`。

根因：`access_rule.last_verified_at` 为 `NULL`——**生产库全部 8 条 AccessRule 皆是**，
非本批次引入。`compute_answerability` 把「从未核验」如实报为 `unknown`，
而 `service_dog` 单元格只统计 `animal_scope='service_dog'` 的规则，
不含 `guide_dog` 例外。两者都不是本次发布产生的偏差，而是既有的
「新鲜度未核验」平台级状态。记为 **PRE_EXISTING_LIMITATION**，不计入本轮 FAIL。

## 10. 回归

- 全量 pytest：见 §11 数字（发布后复跑）。
- 生产库指纹在第二次执行前后一致 → 幂等且零副作用。

## 11. 失败与阻塞

`FAILED = 0`。本批次无未解释失败。

## 12. 结论

5 条授权规则已真实发布且**语义正确**：普通犬/宠物在两地均被判 `prohibited`，
导盲犬因**可达**的法定但书例外被判 `allowed`。幂等、审计、来源、依赖、
负向排除与生产完整性全部通过。未越权发布任何其他 Candidate。

**下一步不是 Wave 02**，而是 Master Goal Phase B（先做辖区级法定例外机制）。
