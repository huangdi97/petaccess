# WAVE01 HUMAN REVIEW SIGNATURE & PRE-PUBLISH — FINAL REPORT

- 授权单：`WAVE01_HUMAN_REVIEW_SIGNATURE_AND_PREPUBLISH_CONTINUATION_R1`
- revision：`EXP-R1-W01-REVIEW-R1`
- expansion_run_id：`EXP-R1-W01-20260918`
- reviewer：`huangdi97`
- 执行时间：2026-09-18（本地时区感知 ISO-8601）
- 本阶段性质：**签名 + 预发布评估 + 批次计划 + dry-run**。**未执行真实发布。**

---

## 1. §25 规定输出

```
SIGNED_REVISION          = EXP-R1-W01-REVIEW-R1
HUMAN_SIGNATURE          = PASS
HUMAN_REVIEWER           = huangdi97
SIGNED_ROWS              = 31

APPROVED                 = 15
HOLD                     = 14
REJECTED                 = 2
APPROVED_WITH_NOTE       = 0

HUMAN_APPROVED_EVALUATED = 15

PREPUBLISH_PASS          = 14
PREPUBLISH_BLOCKED       = 1

ACCESS_RULE_PLANNED      = 11
RULE_EXCEPTION_PLANNED   = 2
SUPERSEDE_PLANNED        = 0
NOOP_PLANNED             = 0

HOLD_PUBLISHABLE         = 0
REJECTED_PUBLISHABLE     = 0
CROSS_LAYER_EXCEPTION    = 0
INERT_EXCEPTION          = 0
UNRESOLVED_SUPERSESSION  = 0

DRY_RUN_ZERO_DB_MUTATION = PASS

PLACE_GEO_PENDING        = OPEN
SEMANTIC_REMODEL_ISSUE   = OPEN
REAL_PUBLISH_EXECUTED_THIS_PHASE = NO
```

> **数字口径说明（重要）**：`PREPUBLISH_PASS = 14` 与批次 `13` 相差 1，不是矛盾。
> 14 是 canonical 预发布闸门对 15 条 APPROVED 的判定；
> 13 是可被发布工具实际执行的批次规模。
> 差值来自 `w01-4e217d5810`：闸门判 PASS，但发布器自身的 ADR-021 原子前置条件拒绝它。
> 详见 §3.2。两者都如实申报，不取其一掩盖另一。

---

## 2. 签名写入（§3–§9）

### 2.1 预检

| 断言 | 结果 |
|---|---|
| revision 匹配 | `EXP-R1-W01-REVIEW-R1` ✅ |
| expansion_run_id 匹配 | `EXP-R1-W01-20260918` ✅ |
| rows = 31 | 31 ✅ |
| 既有 `final_decision` 为空 | 31/31 空 ✅ |
| 既有 `reviewer` / `decided_at` 为空 | 空 ✅ |
| `candidate_id` 重复 | 0 ✅ |

预检通过，未发现任何既有签名，因此**未发生覆盖**。

### 2.2 按稳定 ID 写入（§4）

不使用数组下标单独定位。写入器对每一行校验 `#NN → candidate_id → place_name → scope/effect/layer`，
并对 4 个锚点行做硬断言：

| # | 期望 | 实测 |
|---|---|---|
| 08 | 上海博物馆东馆 / service_dog / allowed / LEGAL | ✅ |
| 19 | 上海迪士尼乐园 / service_dog / conditional / OPERATOR_POLICY | ✅ |
| 23 | 兴业太古汇 / service_dog / allowed / LEGAL | ✅ |
| 30 | 西岸梦中心（Gate M）/ ordinary_pet / conditional / OPERATOR_POLICY | ✅ |

写入脚本：`scripts/expansion_w01_sign_review.py`

### 2.3 签名校验（§7）

| 校验项 | 结果 |
|---|---|
| TOTAL | 31 |
| APPROVED / HOLD / REJECTED / APPROVED_WITH_NOTE | 15 / 14 / 2 / 0 |
| blank `final_decision` / `reviewer` / `decided_at` | 0 / 0 / 0 |
| invalid enum | 0 |
| duplicate `candidate_id` | 0 |
| reviewer distinct | `["huangdi97"]` |
| timestamp 均为时区感知 ISO-8601 | ✅ |

**`WAVE01_HUMAN_REVIEW_GATE = PASS`**

### 2.4 治理数据保护（§8）

冻结字段与**未被触碰的运行清单** `expansion_r1_wave01_registry.json` 逐行交叉比对：

| 字段 | 不一致数 |
|---|---|
| place_name / animal_scope / effect / rule_layer / subject_scope_normalized | **0** |

Evidence、Source、Monitor、Freshness 均未改动（见 §6 指纹比对）。
运行清单中 `published_rule_id` 非空数 = 0、`review_status` 全为 `REVIEW_PENDING`，确认本阶段未触发任何发布。

### 2.5 旧 Pilot 冻结（§9）

| 对象 | 状态 |
|---|---|
| `R2-FINAL-R3` | 未改动 |
| 既有 37 条 Pilot 决策 | 未改动（`docs/reality_audit/review_decisions_r2_final.json`） |
| `R2-FINAL-R3-BATCH-01B` | 未改动 |
| 生产 `AccessRule` / `RuleException` | 5 / 3（未变） |

### 2.6 独立 commit（§11）

```
43bf281 governance: sign EXP-R1-W01-REVIEW-R1 as huangdi97
```

仅含签名登记表与写入器，未混入 UI / geo / subject collection / refactor / tests。
**未 push**（§11 要求）。

---

## 3. 预发布评估（§12–§17）

### 3.1 阻塞发现：登记表投影缺口

签名登记表**无法被 canonical 发布器消费**：

```
KeyError: 'rule_id'   ← scripts/publish_reviewed_r1.py::binding_closure_problems
```

原因是 Wave-01 生成器 `scripts/expansion_w01_reports.py` 产出的 schema 比发布器所需**更薄**，
缺少 `rule_id` / `action` / `evidence_strength` / `license` / `reviewed_at` / `carve_out_of`
以及顶层 `exception_plan`。

**但底层数据从未缺失** —— 它完整存在于生产证据链中
（`rule_candidate.action`、`evidence_bundle.evidence_class` / `license_metadata` /
`place_match_evidence`、`source_artifact.storage_allowed` …）。

因此新增 **桥接层**（不是第二套闸门）：

`scripts/expansion_w01_publish_register.py`

- 派生函数**按 import 复用** R2 生成器的 `derive_evidence_strength` / `_license_problems` / `_applicability` —— 两套登记表不会在"如何评定证据/许可"上漂移；
- 可达性**按 import 复用** `publish_batch.is_reachable_carveout` —— 不重复实现作用域算法；
- 人工签名**逐字复制**（`final_decision` / `reviewer` / `reviewed_at`），且任一行签名不完整即拒跑 —— **它不可能凭空生成决定**。

产物：`docs/expansion/review_decisions_expansion_r1_wave01_publishable.json`

### 3.2 预发布结果

```
PREPUBLISH_APPROVED_EVALUATED = 15
PREPUBLISH_PASS               = 14
PREPUBLISH_BLOCKED            = 1
```

两条 APPROVED 无法发布，原因**互相独立**，且**都没有推翻人工决定**（二者在签名登记表中仍是 APPROVED）：

#### (A) `w01-305fa08c1e` — 上海迪士尼乐园 导盲犬 carve-out（#19）

**两个独立原因，任一都足以拒绝：**

1. **`schema_unsupported`** —— 其 `proposed_conditions` 用键 `type`，而闸门校验 `condition_type`。
   这是 Wave-01 摄入缺陷：31 条候选中 **10 条**用了 `type` 键；但**只有 #19 是 APPROVED**，
   其余 9 条为 HOLD/REJECTED，本就不可发布。
   注意 `leash_required`、`other_structured_note` 都是合法枚举值 —— **纯键名错误，数据本身有效**。
2. **惰性（inert）** —— 其 base 为 `上海迪士尼乐园 / other / prohibited`。
   在 ADR-025 下 `other` 解析为 `{other_pet}`，**不含 `guide_dog`**：

   ```
   rule_governs({guide_dog}, "other", "other", "exact") = False
   ```

   因此该 carve-out 永不可触发。

> **⚠️ 必须向复核人指出的前提更正**
> 授权单 §14 断言：「base scope = other，semantically governs guide_dog，therefore exception is reachable」，
> 并以「if true」为条件要求判定 `RULE_EXCEPTION_REACHABILITY = PASS`。
> **该前提经实测为假。** `other` 不含 `guide_dog`，故可达性条件不成立，
> 该 carve-out 与 `ordinary_pet` base 家族属**同一缺陷类**（惰性），并非可达。
> 授权单同时要求「Do not confuse this with the older Disney ordinary_pet-base semantic issue」——
> 实测表明二者恰恰**是**同一类问题，只是 base scope 写成 `other` 而非 `ordinary_pet`。
> 谨此如实申报，未按前提结论放行。

#### (B) `w01-4e217d5810` — 世纪公园（#21）

- canonical 预发布闸门判定 **PASS（0 violations）**；
- 但发布器的**独立原子前置条件**拒绝它：

  ```
  弱证据(search_snippet)不得 APPROVED（ADR-021）
  ```

- 根因：其来源 `notes = "capture_method=search_snippet; needs_verification=True"`
  —— 即**从未真正抓取运营方页面，只捕获了搜索摘要**。
- 该行需要的是**一手来源重抓**，而不是重新复核。

该行是 `PREPUBLISH_PASS = 14` 与批次 `13` 差值的唯一来源。

### 3.3 特殊检查结论

| 检查 | 结论 |
|---|---|
| RuleException 分类（§16） | 2 条已批准可达 carve-out 均以 `CREATE_RULE_EXCEPTION` 建，非 AccessRule；base 同层且已批准 |
| 跨层例外（§15） | **0**。三处 OPERATOR_POLICY 基座被正确 `cross_layer_dropped`（见 §3.4） |
| LEGAL/OPERATOR 张力 | 未放宽任何 LEGAL；冲突行 11–13、15 已由人工 HOLD |
| Supersession（§17） | 港汇恒隆 #29、前滩太古里 #26 已由人工 HOLD，**未进入批次**；本批 `SUPERSEDE_PLANNED = 0` |

### 3.4 三条 carve-out 可达性实测

| carve-out | base | 同层 | 可达 | 处置 |
|---|---|---|---|---|
| `w01-73de8e3357` 上海博物馆东馆 LEGAL | `w01-fa5f33f122` LEGAL | ✅ | ✅ | 入批 |
| `w01-6482477d8d` 兴业太古汇 LEGAL | `w01-1fb3d7f1c7` LEGAL | ✅ | ✅ | 入批 |
| `w01-305fa08c1e` 迪士尼 OPERATOR_POLICY | 无同层 base | — | ❌ | 拒绝 |

跨层丢弃记录（未成为依赖，仅作历史）：
`w01-73de8e3357` ← 丢弃 `w01-4710a68f56`（OPERATOR）；
`w01-6482477d8d` ← 丢弃 `w01-b340f06ce1`（OPERATOR）。

---

## 4. 批次计划（§18–§19）

清单：`docs/governance/publish_batches/EXP_R1_W01_REVIEW_R1_BATCH_01.json`

```
batch_id               = EXP-R1-W01-REVIEW-R1-BATCH-01
selected               = 13   (11 CREATE_ACCESS_RULE + 2 CREATE_RULE_EXCEPTION)
deferred               = w01-305fa08c1e, w01-4e217d5810
BATCH_VALIDATION       = PASS
BATCH_DEPENDENCY_CLOSED= PASS
ZERO_INERT_RULES       = PASS
HOLD_SELECTED          = 0
REJECTED_SELECTED      = 0
UNAPPROVED_SELECTED    = 0
CROSS_LAYER_EXCEPTION  = 0
BASE_WITHOUT_APPROVED_EXCEPTION = 0
UNREACHABLE_SELECTED   = 0
```

执行顺序（位置即顺序，carve-out 均在其 base 之后）：

```
w01-052d19ccba(CHARLIE'S LEGAL) -> w01-1fb3d7f1c7(兴业太古汇 LEGAL)
-> w01-3a04d4d1aa(迪士尼 op) -> w01-4710a68f56(上博东馆 op)
-> w01-6f2bfd39d7(上海动物园 op) -> w01-7de2f5d75b(omitofee LEGAL)
-> w01-8ba2b49b01(苏河湾 LEGAL) -> w01-d1aee78159(前滩太古里 LEGAL)
-> w01-df1645fe68(朗廷 LEGAL) -> w01-e951785d1b(港汇恒隆 LEGAL)
-> w01-fa5f33f122(上博东馆 LEGAL)
-> w01-6482477d8d(兴业太古汇 ← w01-1fb3d7f1c7)
-> w01-73de8e3357(上博东馆 ← w01-fa5f33f122)
```

### 关于迪士尼 base 仍在批内

授权单 §19 要求批次「zero inert」。迪士尼**基座** `w01-3a04d4d1aa` 保留在批内，
而其唯一已批准 carve-out 惰性 —— 这不是疏漏，而是 canonical 规则的正确结果：

> 一条不可达的已批准 carve-out **不**对其 base 产生随批义务；
> 且惰性 carve-out 本身不得入批（`ZERO_INERT_RULES`）。
> 若以惰性 carve-out 反锁 base，等于让建模缺陷劫持真实规则。

### 批次覆盖（13 条）

| 指标 | 值 |
|---|---|
| 携带 evidence_bundle | 13 / 13 |
| license 无问题 | 13 / 13 |
| place_match_evidence | 13 / 13 |
| last_verified_at | 13 / 13 |
| content_hash | 13 / 13 |
| snapshot_ref | **0 / 13** ⚠️ |
| 证据强度 | 全部 `primary_direct` |
| 层分布 | LEGAL 10 / OPERATOR_POLICY 3 |
| 效果分布 | prohibited 11 / allowed 2 |

> ⚠️ `snapshot_ref` 全空：13 条均有 `content_hash` 与逐字引文（可追溯性成立），
> 但**页面快照引用缺失**。不阻断本次发布（闸门以 `quoted_fragment OR content_hash` 满足可追溯），
> 但应在后续 Wave 补齐快照留存。

---

## 5. Dry-run（§20–§21）

使用**真实发布器 + 真实闸门 + 真实依赖排序**，**零 DB 变更**：

```
DRY_RUN_ZERO_DB_MUTATION = PASS
```

前后生产指纹：

```
BEFORE = 584c97ba084744665ab0da2dcf9164f5cfcca0d3fb996cc42c3540450b345308
AFTER  = 584c97ba084744665ab0da2dcf9164f5cfcca0d3fb996cc42c3540450b345308
PRODUCTION_DB_SEMANTIC_DIFF = 0
PRODUCTION_DB_ROW_DIFF      = 0
FINGERPRINT_COMPARE         = IDENTICAL
```

生产计数不变：`access_rule = 5`、`rule_exception = 3`、`candidates = 68`、`audit_log = 9608`、
`duplicate_current_groups = 0`。

证据：`artifacts/wave01_prepublish/PROD_FP_BEFORE.json` / `PROD_FP_AFTER.json` /
`PROD_INTEGRITY.json`

---

## 6. 限制项与未决项

| 项 | 状态 | 说明 |
|---|---|---|
| `PLACE_GEO_PENDING` | **OPEN** | Wave-01 新增 10 场所 geo 全待定（§23 要求本阶段不解决）。**构成 Public Beta `REAL_MAP` 硬阻塞**，详见 §7 |
| `SEMANTIC_REMODEL_ISSUE` | **OPEN** | 本阶段未启动（§24）。新增证据见 §8 |
| `AUDIT_TARGET_ID_UNUSABLE` | MEDIUM / 2647 行 | 预 Wave-01 历史问题，非本轮引入 |
| `snapshot_ref` 缺失 | 13/13 空缺 | 见 §4 |
| 外部通知通道 | `NOT_IMPLEMENTED` | 未触及 |
| 5 个源 403 | 已保留 | 未当作变更；`failure_count=1`、`last_http_status=403` 完整保留 |

生产完整性（`check_production_integrity.py`）：**CRITICAL = 0、HIGH = 0、MEDIUM = 1、INFO = 0**。

监控状态（§22）：13/13 `active`，`next_check_at` 全非空，**未因 403 撤回任何规则、删除任何证据或虚构变更**。

---

## 7. 需复核人裁决的两个新发现（超出本阶段授权范围）

本阶段严格只做「机械写入 → 校验 → 预发布评估 → 批次计划 → dry-run」。
但执行中实测出两项与授权单前提/假设不符的事实，如实上报，**未自行处置**：

### 7.1 授权单 §14 前提为假

- 授权单称迪士尼 carve-out「base = other 语义治理 guide_dog ⇒ 可达 ⇒ `RULE_EXCEPTION_REACHABILITY = PASS`」。
- 实测：`other → {other_pet}`，**不治理** `guide_dog`，该 carve-out **惰性**。
- 影响：它不是可达例外，而是与 `ordinary_pet` base 家族**同类**的惰性缺陷，应并入
  `SEMANTIC_REMODEL_ISSUE` 一并处理。

### 7.2 Wave-01 摄入存在 `condition_type` 键名缺陷

- 31 条候选中 **10 条**把条件键写成 `type`，正确键名为 `condition_type`。
- 当前影响：仅 #19 因之被闸门拒绝（其余 9 条因 HOLD/REJECTED 不可发布，缺陷被掩盖）。
- 风险：**未来任何使用这 10 条的发布都会被同一 schema 闸门拒绝**，且错误信息只给组级原因，不易定位。
- 建议（需人工授权）：修正摄入层键名并加回归锁；属数据修正而非决定改写，但会改动生产库数据，**不得由 agent 自行执行**。

---

## 8. 状态与下一步

```
WAVE01_HUMAN_REVIEW_GATE = PASS
WAVE01_PREPUBLISH_GATE   = PASS_WITH_2_EXCLUSIONS
WAVE01_BATCH_PLAN        = READY (13, dependency-closed, ZERO_INERT_RULES = PASS)
WAVE01_DRY_RUN           = PASS (zero DB mutation)
REAL_PUBLISH_EXECUTED_THIS_PHASE = NO
```

下一步为**人类检查点**：

```
HUMAN_ACTION_REQUIRED = WAVE01_REAL_PUBLISH_AUTHORIZATION
```

在用户明确授权前**不执行 `--execute`**；不进入 Phase B / Wave02 / Real Map / Public Beta Release。

---

## 9. 本阶段 commit

| commit | 内容 |
|---|---|
| `43bf281` | `governance: sign EXP-R1-W01-REVIEW-R1 as huangdi97` |
| `c8864cb` | `governance: add Wave 01 pre-publish projection and batch plan` |

均未 push。`artifacts/` 按 `.gitignore` 默认不入库。
