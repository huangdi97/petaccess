# SCOPE-REMODEL-R2 生产 Materialization 报告

| 项 | 值 |
|---|---|
| 执行 commit | `1c10bbe` |
| 工作树 | **clean worktree**（`git worktree add --detach` 固定到 `1c10bbe`，`git status --porcelain` = 0 行） |
| 目标库 | `petaccess`（生产） |
| 时间 | 2026-09-18 22:22 +08:00（主机钟）／候选 `created_at` 2026-09-18 14:14 UTC（容器钟，比主机快约 22s，两钟未混用） |
| 性质 | **数据动作**：仅新建 6 条 `REVIEW_PENDING` 候选 |

> 工作区里另有一批 **ADR-031 / holder_scope 未提交改动**（5 个文件）。它们**没有**进入本轮执行：
> 生产命令是从干净 worktree 跑的，也**没有**被混进任何 commit。

---

## 1. 授权边界（本轮做了 / 没做什么）

做了：新建 6 条候选、全部 `REVIEW_PENDING`、按生产 UUID 重新生成正式登记表、
生成 Human Review Packet / Quick Table、零副作用验证。

**没有做**：`final_decision`、`reviewer`、`decided_at`、人类签署、发布、`AccessRule` 创建、
`RuleException` 创建、`--execute` 批次、修改旧冻结候选、修改已发布规则、进入 Wave02。

## 2. 执行前（只读）

```
scope_remodel_r2_candidates.py --plan --db-name petaccess
→ NEW_CANDIDATES = 6
    Disney:      dog / cat / other
    Shanghai Zoo: dog / cat / other
```

冻结候选与旧人类审查（写入前快照 `artifacts/scope_remodel_r2/SCOPE_REMODEL_R2_PRE_MATERIALIZATION.json`）：
`rule_candidate` 68、`REVIEW_PENDING` 49、已发布候选 19、`access_rule` 14、`rule_exception` 5、
`jurisdiction_exception` 1、旧登记表 sha256 `d331efeb03e8…`。

## 3. 执行

```
.venv/Scripts/python.exe scripts/scope_remodel_r2_candidates.py \
  --apply --db-name petaccess --token-file .tmp/admin.jwt --production-confirm
```

| Candidate ID | 场所 | subject | 来源术语（逐字） |
|---|---|---|---|
| `7b595de9-e0c3-4092-aab4-348c4878c296` | 上海迪士尼乐园 | `dog` | 动物（导盲犬除外） |
| `4580ab21-60c2-4bfb-9a2c-47cde25c5678` | 上海迪士尼乐园 | `cat` | 动物（导盲犬除外） |
| `4ca5e55a-6aaf-4ef5-9e0d-cdefbfac98cd` | 上海迪士尼乐园 | `other` | 动物（导盲犬除外） |
| `a4e2ba26-f542-4ee6-a088-c073096db733` | 上海动物园 | `dog` | 动物 |
| `27893d75-aa05-422f-9797-2120e81db2ec` | 上海动物园 | `cat` | 动物 |
| `2a3de3ab-de8d-4074-a4d0-3039c715893d` | 上海动物园 | `other` | 动物 |

`CREATED = 6` · `UPDATED_OLD_CANDIDATE = 0` · `DELETED = 0` · `PUBLISHED = 0`
· 6/6 `REVIEW_PENDING`。

## 4. 允许 vs 实际 delta

**允许**：6 条新 `RuleCandidate` + 候选创建/流转的 canonical audit。

**实际**（指纹 `--compare`）：

```
rule_candidate : 68 -> 74   (+6 -0 ~0)
audit_log      : 9640 -> 9652 (+12 -0 ~0)
```

其余所有表**零变化**（`access_rule`、`rule_exception`、`jurisdiction_exception`、`place`、
`source`、`evidence_bundle` 均未出现在 diff 中）。+12 = 6 条 create + 6 条 transition 审计。

指纹：`c571ad98edfe…` → `c28ef9f63c04…`
**`EXPECTED_DELTA_ONLY = PASS`**

## 5. 不变式（写入后实测）

| 项 | 值 |
|---|---|
| `NEW_SCOPE_REMODEL_CANDIDATES` | **6** |
| `REVIEW_PENDING` | **6** |
| `PUBLISHED`（`published_rule_id`） | **0** |
| `OLD_FROZEN_CANDIDATES_MUTATED` | **0**（3 条冻结行 12 个字段逐字段比对） |
| `ACCESS_RULE_DELTA` | **0** |
| `RULE_EXCEPTION_DELTA` | **0** |
| `JURISDICTION_EXCEPTION_DELTA` | **0** |
| `OLD_HUMAN_REVIEW_DIFF` | **0**（sha256 未变） |
| 已发布候选集合 | 未变（19） |

### 关于「人类字段非空」的一个必须说清的点

`reviewer_id` 在 6 条新行上是**非空**的（`ccfe8e68…` = `admin@demo-petaccess.com`），
`review_note` = `SCOPE-REMODEL-R2/SCOPE-R2-20260918: 待人工审核（不得自动批准或发布）`。

这两个字段由 **transition 端点按 API 操作者自动盖章**，不是人类决定：
现有 55 条 `REVIEW_PENDING` 里 26 条是 `admin@demo-petaccess.com`、26 条 `real-pilot-admin@…`、
3 条 `scope-split-ops@…`，全部同源同性质；31 条 Wave01 行同样如此。
**人类决定只存在于登记表**（`final_decision` + `reviewer=huangdi97`），本轮全为 `null`。
所以：`final_decision / reviewer(human) / decided_at / decision_note = 空`，`HUMAN_SIGNATURE = 0`。

## 6. Resolver 生产回归

候选未发布 ⇒ 生产答案必须完全不变。同一支探针前后各跑一次并 `diff`：

```
resolver_PRE.txt  vs  resolver_POST.txt  →  RESOLVER_IDENTICAL (mismatch = 0)
verdict = PASS（普通犬 11 条 LEGAL 基底 A/B 一致；导盲犬变化仅来自但书对照，非本轮写入）
```

`PRODUCTION_RESOLVER_REGRESSION = PASS`

## 7. 生产完整性

```
CRITICAL × 6 = 0   HIGH × 9 = 0
（CONFLICTING_CURRENT_RULES / CROSS_LAYER_EXCEPTION / HOLD_OR_REJECTED_PUBLISHED /
  ORPHAN_RULE_EXCEPTION / SELF_SUPERSEDE / SUPERSESSION_CYCLE / DUPLICATE_CURRENT_RULE /
  ORPHAN_* / PUBLISHED_WITHOUT_* / TEST_*_IN_PRODUCTION）
```

`PRODUCTION_INTEGRITY_CRITICAL = 0` · `PRODUCTION_INTEGRITY_HIGH = 0`
MEDIUM 仅历史遗留 `AUDIT_TARGET_ID_UNUSABLE`（本轮前后未变）。

## 8. 正式登记表

`docs/expansion/review_decisions_scope_remodel_r2.json`（**来自生产 UUID**，非演练库）

- `rows = 6`；每行 `final_decision = reviewer = decided_at = decision_note = null`
- sha256 `891834218a3cf8fdffe4642f3026c774f43dd8f884e1a5272affa02106d3d07`
- 无默认 reviewer；建议列（`ai_recommendation`）**未被**复制为决定
- caveat / advisory 字段由本轮后处理写入（生成器本身只产空决策单元），**未做 schema 迁移**

## 9. 来源范围限定（重要）

| 声明 | 值 |
|---|---|
| `SOURCE_SCOPE_FULL_REAL_WORLD_EXHAUSTIVE` | **NO** |
| `CURRENT_ONTOLOGY_EXPRESSIBLE_SPLIT` | **YES** |
| `UNMODELED_SOURCE_SCOPE_REMAINDER` | **YES** |

`compound_term_split` 只表示：从宽泛来源术语里拆出**当前系统可表达**的 scope。
`dog ∪ cat ∪ other_pet` **不等于**来源「动物」的现实世界全集；鸟类、爬行类及词表外对象
没有任何行覆盖，对它们的答案仍是 `UNKNOWN` —— **绝不可读作 ALLOWED**。
每条 `source_scope_exact` 逐字保留原文，caveat 写入登记表与审查包（未新造字段、未迁移）。

## 10. 例外挂接与动物园法律未决

- 迪士尼导盲犬 carve-out `w01-305fa08c1e`：登记表的 `exception_plan` 已把挂接点改到新的
  **`dog` 基底 `7b595de9-e0c3-4092-aab4-348c4878c296`**；实测 `is_reachable_carveout = True`
  （旧 `other` 基底上为 `False`）。例外本身**仍是提案，未发布**。
- 动物园 `dog` 行：`rule_governs(guide_dog, dog)` 成立 ⇒ 拆分后导盲犬 `unknown → prohibited`。
  但导盲犬是否因上位法而例外属 **`LEGAL_APPLICABILITY` 未决**，不由 Agent 判断；
  `JPROV-001` 的 `applies_to_layer=LEGAL` 不匹配 `OPERATOR_POLICY` 层，救不了。
  `SHANGHAI_ZOO_LEGAL_APPLICABILITY = HUMAN_REVIEW_REQUIRED`。

## 11. 闸门输出（§20）

```
EXECUTION_COMMIT = 1c10bbe
WORKTREE_CLEAN = YES

PRODUCTION_MATERIALIZATION = PASS

NEW_CANDIDATES_CREATED = 6
REVIEW_PENDING = 6
HUMAN_FIELDS_NONEMPTY = 0            # final_decision/reviewer/decided_at/note 全 null
                                     # （reviewer_id/review_note 为 API 操作者盖章，见 §5）
OLD_CANDIDATES_MUTATED = 0

ACCESS_RULE_DELTA = 0
RULE_EXCEPTION_DELTA = 0

DISNEY_DOG_BASE_FOR_CARVEOUT = 7b595de9-e0c3-4092-aab4-348c4878c296
DISNEY_GUIDE_DOG_REACHABLE = YES

SOURCE_SCOPE_FULL_REAL_WORLD_EXHAUSTIVE = NO
CURRENT_ONTOLOGY_EXPRESSIBLE_SPLIT = YES
UNMODELED_SOURCE_SCOPE_REMAINDER = YES

SHANGHAI_ZOO_LEGAL_APPLICABILITY = HUMAN_REVIEW_REQUIRED

PRODUCTION_RESOLVER_REGRESSION = PASS
PRODUCTION_INTEGRITY_CRITICAL = 0
PRODUCTION_INTEGRITY_HIGH = 0

REAL_PUBLISH_EXECUTED = NO

HUMAN_ACTION_REQUIRED = SCOPE_REMODEL_R2_FINAL_DECISIONS
```

## 12. 产物

- 快照：`artifacts/scope_remodel_r2/SCOPE_REMODEL_R2_PRE_MATERIALIZATION.json`、
  `…_POST_MATERIALIZATION.json`（旧快照未覆盖）
- 指纹：`fingerprint_PRE.json` / `fingerprint_POST.json`
- 探针：`resolver_PRE.txt` / `resolver_POST.txt`；完整性 `integrity_POST.log`
- 审查材料：`docs/expansion/SCOPE_REMODEL_R2_HUMAN_REVIEW_PACKET.md`、
  `SCOPE_REMODEL_R2_HUMAN_REVIEW_QUICK_TABLE.md`、
  `review_decisions_scope_remodel_r2.json`

**STOP — 停在 Human Review Checkpoint。**
