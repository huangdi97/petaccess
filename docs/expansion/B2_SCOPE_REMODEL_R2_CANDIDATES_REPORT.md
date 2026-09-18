# B2 — SCOPE-REMODEL-R2：新 revision 候选已生成（**未写入生产库**）

日期：2026-09-18 · 闸门 B2 · 状态：**停在人类签署闸门**

---

## 1. 为什么必须是新 revision，而不是改那两行

上海动物园（`动物`）与上海迪士尼乐园（`动物（导盲犬除外）`）在已签署的
`EXP-R1-W01-REVIEW-R1` 里记录为 `animal_scope=other` + `normalization_type=exact`。
这个声明是假的：ADR-025 下 `other` = `{other_pet}`（一个主体），而「动物」指全部动物。
规范闸门因此以 `SOURCE_SCOPE_NORMALIZATION_NOT_SEMANTICALLY_EQUIVALENT` 拒绝它们，
它们**永远无法按现状发布**。

已签署候选不可原地修改（这是规则，不是保守）。所以修复形态是**新 revision 的新候选**，
而不是编辑：原两行保持 `REVIEW_PENDING`、在登记表里仍是 `APPROVED`，一条字节都没动。

## 2. 做了什么

新脚本 `scripts/scope_remodel_r2_candidates.py`，三种模式：`--plan` / `--apply` / `--verify`
（外加 `--register` 出审查登记表）。它从冻结候选**克隆**字段，按
`broad_term_split.py` 的穷尽拆分生成 3 行/场所：

| 场所 | 生成行 | `source_scope_exact` | `normalization_type` |
|---|---|---|---|
| 上海迪士尼乐园 | `dog` / `cat` / `other` | `动物（导盲犬除外）`（逐字） | `compound_term_split` |
| 上海动物园 | `dog` / `cat` / `other` | `动物`（逐字） | `compound_term_split` |

克隆时**刻意排除** `animal_scope` / `subject_scope_normalized` / `normalization_type`
（`CLONED_COLUMNS` 不含它们，并有回归锁），否则"新 revision"会和旧行逐字节相同。
`source_scope_exact` 保留在克隆列里——它是证据原文，不是解读。
每行带 `projection_of_rule_id` 指回被取代的冻结候选、`dedup_key` 确定性（重跑幂等），
落库后即 transition 到 `REVIEW_PENDING`。

**运行位置是演练库** `petaccess_publish_rehearsal_sr2`（生产克隆，克隆时
`rule_candidate=68` / `access_rule=14`）。6 行已创建，`rule_candidate` 68 → 74。

## 3. 闸门对照（同一套规范函数，A/B 实测）

| 行 | `「术语」→scope (type)` | 闸门 |
|---|---|---|
| 迪士尼 冻结 | `动物（导盲犬除外）` → `other` (`exact`) | **FAIL** — 收窄却声称等价，且内嵌但书未建模为例外 |
| 迪士尼 新 dog/cat/other | 同术语 → 各自成员 (`compound_term_split`) | **PASS** ×3 |
| 动物园 冻结 | `动物` → `other` (`exact`) | **FAIL** — 把全域归一为 `other_pet` |
| 动物园 新 dog/cat/other | 同术语 → 各自成员 (`compound_term_split`) | **PASS** ×3 |

**导盲犬 carve-out 可达性翻转**（迪士尼 `w01-305fa08c1e`，已 APPROVED）：

- 冻结 `other` 基底上：`is_reachable_carveout = **False**` ⇒ 这正是那条
  `UNREACHABLE_APPROVED_CARVE_OUT` 的成因——例外永远打不到，沉默会被读成禁止。
- 新 `dog` 基底上：`**True**`。拆分后不必改例外本身，只把挂接点换到新基底。

拆分后的答案变化（来自 `scope_remodel_proposals_r2.json` 的 resolver 对照）：
迪士尼 普通犬 `unknown → prohibited`、猫 `unknown → prohibited`、
导盲犬 `unknown → conditional`（carve-out 生效）；动物园 普通犬/猫
`unknown → prohibited`、**导盲犬 `unknown → prohibited`**（来源原文无但书）。

## 4. 冻结行未被动过（演练库实测）

```
3a04d4d1-…  other / other / exact / REVIEW_PENDING / published_rule_id=None
6f2bfd39-…  other / other / exact / REVIEW_PENDING / published_rule_id=None
```

`access_rule` 仍 14、`rule_exception` 5、`jurisdiction_exception` 1——本轮未发布任何东西。

## 5. 生产库状态

**未写入。** 脚本对 `petaccess` 有硬闸门：`--apply` 不带 `--production-confirm` 直接拒绝。
另外要注意：**候选 UUID 是落库时才生成的**，所以生产库 materialize 之后
`review_decisions_scope_remodel_r2.json` 必须用同样的流程重新生成一次，
不能用演练库里的 id。

## 6. 需要人做的事（按顺序）

1. **授权在生产库 materialize**（写 6 条 `REVIEW_PENDING` 候选，不改任何已签署行）：
   ```bash
   .venv/Scripts/python.exe scripts/scope_remodel_r2_candidates.py \
     --apply --db-name petaccess --token-file .tmp/admin.jwt --production-confirm
   ```
2. **重新生成登记表模板**（id 会变）：`--register --db-name petaccess`。
3. **逐条签署** `docs/expansion/review_decisions_scope_remodel_r2.json`——
   模板里 6 行 `final_decision` 全为 `null`，`reviewer`/`decided_at`/`decision_note` 也是 `null`；
   脚本不填、不推断。`exception_plan` 里已把导盲犬 carve-out 的挂接点改到新的 `dog` 基底。
4. 签署后才是 batch manifest + 演练 + 发布（同 BATCH_02 的流程）。

## 7. 仍未解决的两个问题（不因拆分而消失）

- **`ZOO_GUIDE_DOG_AFTER_REMODEL`（HUMAN_DECISION）**：动物园拆完后导盲犬由
  `unknown` 变 `prohibited`——来源原文确实没有但书。这是否受《无障碍环境建设法》等
  上位法影响，是**法律判断**，我不做。注意 `JPROV-001` 的 `applies_to_layer=LEGAL`
  不匹配动物园的 `OPERATOR_POLICY` 层，救不了它。
- **`VOCABULARY_NON_PET_ANIMALS`（已记录的局限）**：「动物」包含平台词表未建模的动物
  （观赏鸟、爬行类等）。拆分只覆盖词表内 9 个主体，超出部分平台继续沉默（`unknown`），
  **不算允许**。

## 8. 质量

新增 4 条回归锁（`tests/unit/test_scope_remodel_r2_candidates.py`）：dedup 确定性、
克隆列不含 scope、revision 标识稳定、**登记表模板必须全空**（防"模板自带签字"）。
ruff check / format 通过。
