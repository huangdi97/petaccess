# WAVE-02 START & R2-FINAL-R3 BACKLOG REPORT

轮次：`WAVE02_START_AND_R2FINALR3_BACKLOG_R1`
基线：`743dc2c`（本轮开始时 HEAD）
生产库：`petaccess`（PRODUCTION）· alembic `f2a1c7d9e034`
本轮对生产库的写入：**0**（全部动作为只读探测或打在演练克隆 `petaccess_publish_rehearsal_w02` 上）

---

## 0. 结论指标

```
# --- A. 授权 §7：统一 AccessAnswer（实现，不是核对） -------------------------
ACCESS_ANSWER_IMPLEMENTED          = YES
ACCESS_ANSWER_ENDPOINT             = POST /api/v1/places/{place_id}/access-answer
ACCESS_ANSWER_REQUIRED_FIELDS      = 13/13
ACCESS_ANSWER_UNIT_TESTS           = 12 passed
ACCESS_ANSWER_INTEGRATION_TESTS    = 7 passed
ACCESS_ANSWER_REAL                 = PASS（生产数据实测）
FORBIDDEN_CONFIRMATION_CLAIM       = ABSENT（「官方已确认」等 4 条实测不在任何响应里）
CONSUMER_SURFACE_MIGRATED          = Place Detail（第一屏 scope/provenance + 第 7 段逐规则来源）
CONSUMER_SURFACES_PENDING_MIGRATION= Home / Search / MatchExplain / Share / Watch

# --- B. 上一轮收口报告的口径修正 ---------------------------------------------
WAVE01_CLOSURE_SCOPE               = EXP-R1-W01-REVIEW-R1（31 行）· CURRENT_EXECUTABLE=0 仅对该 revision 成立
PROJECT_WIDE_APPROVED_UNPUBLISHED  = 18（跨全部 revision）
R2_FINAL_R3_APPROVED_TOTAL         = 23
R2_FINAL_R3_ALREADY_PUBLISHED      = 8
R2_FINAL_R3_GATE_PASS_UNPUBLISHED  = 13    ← 上一轮未披露
R2_FINAL_R3_PUBLISH_BLOCKED        = 2

# --- C. 计划层收窄（gate PASS ≠ 计划可写） -----------------------------------
PLAN_LEVEL_WRITABLE                = 11/13（dl-sd-op / qt-sd-op = UNREACHABLE → SEMANTIC_REMODEL_REQUIRED）

# --- D. 演练收敛（clone 上实测，生产零写） -----------------------------------
REHEARSAL_11                       = FAIL  —— HIGH DUPLICATE_CURRENT_RULE 2 rows / 1 group
DUPLICATE_CAUSE                    = qt-indoor-legal 与既有 current LEGAL dog/prohibited 重复（前滩太古里）
SAFE_9                             = 9 行（6 规则 + 3 例外）排除 qt-indoor-legal / qt-sd-legal
SAFE_9_PUBLISHED_ON_CLONE          = 9 · failed=0 · audit contract PASS
SAFE_9_SECOND_EXECUTE_NOOP         = 9 · NEW_WRITES = 0
SAFE_9_INTEGRITY                   = CRITICAL 0 / HIGH 0 / MEDIUM 1（历史项）· duplicate_current_groups = 0
PRODUCTION_TOUCHED_BY_REHEARSAL    = NO（指纹 67f7b19e… 前后一致）

# --- E. Wave-02 前置门禁 -----------------------------------------------------
ANIMAL_SCOPE_REMODEL_GATE          = PASS
PILOT_REVIEW_PUBLISH_GATE          = PASS（2026-09-17 起即为 PASS）
30_50_PLACE_EXPANSION              = ALLOWED（两 Gate 同时 PASS）
WAVE_02_INFRA_STARTED              = NO（见 §6：本次先做的是它真正的前置）
```

---

## 1. 授权 §7：统一 AccessAnswer —— 实现，不是核对

### 1.1 为什么上一轮的做法是错的

上一轮我把 §7 当成「核对已发布 surface 是否出现禁用表述」，并把它未实现写成 limitation。这不对：
母版 §10 要求首页 / Search / Map Card / Place Detail / H5 Share / Watch 消费**统一答案模型**
（13 个字段），且「禁止页面自行算 Rule」。仓库里**没有任何实现**（13 个字段名全仓 0 命中）。
一个未实现的东西不是 limitation，是 to-do。本轮补上。

### 1.2 新增

`services/api/app/rulespec/access_answer.py` —— 纯函数构造器，输入是 resolver 自己的输出，
**绝不重新判定 effect**。三个「结构上做不到」而不是「约定不要做」：

1. **模型无法表达「官方已确认」。** 没有任何字段的取值能表示它；`evidence_state` 由库中的
   `source_type` / `directness` / `issuer_verification` 加「该规则自己的发布链」推导。
   `assert_no_unbacked_first_party_claim()` 在每次构造时执行：当 `first_party_operator_source_count == 0`
   时，答案里出现「官方已确认 / 运营方已确认 / operator first-party verified / 一手来源已核验」
   任一句即抛错。
   （注意：`official_operator_policy` **不在**禁用词表里——它是合法的 `source_type` 取值，
   上海动物园的来源真的就是运营方官网；该禁的是「声称」，不是「词汇」。）
2. **Zone 永不压平成 Place 结论。** `scope_summary.scope_level` 说明是哪一层真正决定了答案；
   「no rule in scope」没有任何代码路径能变成 `allowed`。
3. **被扣下的但书是 `conditional` + `missing_inputs`**，既不是裸禁令也不是无条件允许（ADR-031）。

端点：`POST /api/v1/places/{place_id}/access-answer`。目标 zone 不属于该场所时 **404 拒绝**，
而不是拿别处的 zone 去解析本场所的规则。

### 1.3 生产数据实测（`scripts/verify_access_answer_real.py`）

| 查询 | effect | scope_level | governing rules |
|---|---|---|---|
| ordinary dog @ 世纪公园其他区域 | `prohibited` | `zone` | 1（`149828d0…`） |
| ordinary dog @ 世纪宠物乐园（未覆盖） | `unknown` | `none` | 0 |
| ordinary dog @ 不带 zone | `unknown` | `none` | 0 |
| guide_dog @ 世纪公园其他区域 | `unknown` | `none` | 0 |

世纪公园那一条的 `provenance_statement` 逐字为：

> 来源：上海市文化和旅游事业发展中心《又一新地标！这个周末，带「毛孩子」来放飞》（转述世纪公园官方口径）；
> source_type=government_service；（政府平台转述园方口径）；directness=secondary；
> 未取得运营方一手来源（first-party operator source pending）。

恰是授权 §7 要求「必须准确展示」的五项。`ACCESS_ANSWER_REAL = PASS`。

### 1.4 消费端

H5 Place Detail 第一屏新增 `适用范围`（来自 `scope_summary`）与 `来源`（来自
`evidence_state.rules[0].provenance_statement`）；第 7 段逐规则列出 `provenance_statement`
（`source_type_semantics` 为空时**显示原始枚举值而不是编一句话**）。
H5 构建（含 `vue-tsc`）、ESLint、Prettier 全绿。

**未迁移**：Home / Search / MatchExplain / Share / Watch 仍读 `effective-rules` 的 `effect`
（它们只用到 effect，没有自行推导规则逻辑，因此不违反「禁止页面自行算 Rule」，
但**尚未统一到答案模型**）。这是明确列出的剩余项，不是「已完成」。

---

## 2. 上一轮收口报告的口径修正

`WAVE01_FINAL_CLOSURE_REPORT.md` 的 `CURRENT_EXECUTABLE = 0` **只对 `EXP-R1-W01-REVIEW-R1`
这 31 行成立**（报告正文写明了 revision，但标题与指标块容易被读成项目级）。项目级的真实情况：

```
全部登记表 revision：R2-FINAL-R3(37) · EXP-R1-W01-REVIEW-R1(31) · SCOPE-REMODEL-R2(14)
全部 rule_candidate = 75，其中已发布 26
APPROVED 且未发布 = 18
  ├─ 3 条 = SUPERSEDED_NON_EXECUTABLE（w01-3a04d4d1aa / w01-6f2bfd39d7 / w01-305fa08c1e）—— 永久不可执行，正确
  └─ 15 条 = R2-FINAL-R3 的遗留
```

这 15 条里：13 条单行 gate=PASS、2 条 gate 阻塞。**这是我上一轮没有披露的事实**。

---

## 3. R2-FINAL-R3 逐条处置（重跑当前版本全部闸门）

| 分类 | 条数 | rule_id |
|---|---|---|
| `ALREADY_PUBLISHED` | 8 | fp-legal-dog / fp-pets-op-firstparty / fp-sd-legal / lib-legal-dog / lib-pets-op / lib-sd-legal / sb-legal-dog / sb-sd-legal |
| `CURRENTLY_EXECUTABLE`（单行 gate） | 13 | dl-pet-ban / dl-sd-op / gh-legal-dog / gh-sd-legal / mn-legal-dog / mn-sd-legal / qt-indoor-legal / qt-indoor-op / qt-outdoor-op / qt-sd-legal / qt-sd-op / xm-legal-dog / xm-sd-legal |
| `PUBLISH_BLOCKED` | 2 | fp-sd-op-firstparty / lib-sd-op-guide（不可达运营层但书） |

---

## 4. 把「单行 gate PASS」升级成「计划层可写」

陷阱 #94/#103 讲的是「批次校验 PASS 不等于可执行」；反向同样成立：**单行 gate PASS 不等于计划可写**。
把这 13 行放进一个探针清单跑发布器计划（dry-run，零写入）：

```
BATCH_SELECTED = 13 · BATCH_VALIDATION = FAIL（2 项）· exit 4
  - dl-sd-op:  该例外语义不可达（bases=['dl-pet-ban']）→ SEMANTIC_REMODEL_REQUIRED
  - qt-sd-op:  该例外语义不可达（bases=['qt-indoor-op']）→ SEMANTIC_REMODEL_REQUIRED
```

收窄到 11 行后 `BATCH_VALIDATION = PASS`、`UNREACHABLE_SELECTED = 0`、`ZERO_INERT_RULES = PASS`、
`SELECTED_BUT_BLOCKED = 0`、`DUPLICATE_PUBLICATION_PLAN = 0`。

---

## 5. 演练收敛：11 → 9（这是本轮最重要的发现）

`BATCH_VALIDATION = PASS` 仍不是安全证明。在克隆库 `petaccess_publish_rehearsal_w02` 上真执行 11 行：

```
published = 11 · failed = 0
但 post-integrity：HIGH DUPLICATE_CURRENT_RULE = 2 rows / 1 group
  前滩太古里 zone 12690b48 · LEGAL · dog · enter · prohibited
    ├─ 42c9a35e-… （既有，2026-09-18 记录）
    └─ a9124d56-… （本次由 qt-indoor-legal 新建）
duplicate_current_groups 0 → 1
```

即 `qt-indoor-legal` 会**新建一条与既有现行规则重复的规则**；`qt-sd-legal` 以它为 base，
随之失去基底。两条一并排除。

**重建克隆 → 执行 SAFE-9（6 规则 + 3 例外）**：

```
BATCH_SELECTED = 9 · BATCH_DEPENDENCY_CLOSED = PASS · BATCH_VALIDATION = PASS
published = 9 · failed = 0 · audit contract PASS（checked=9 / missing=0）
二次 execute：NOOP = 9 · ACCESS_RULE_CREATE = 0 · RULE_EXCEPTION_CREATE = 0
指纹 4844b7af… → b4cfa2af…（access_rule 20→26、rule_exception 6→9、audit 9668→9686）
post-integrity：CRITICAL 0 / HIGH 0（DUPLICATE_CURRENT_RULE = 0）/ duplicate_current_groups = 0
```

**生产库全程零写入**：演练前后生产指纹均为 `67f7b19e…`。

SAFE-9 名单：`dl-pet-ban · gh-legal-dog · gh-sd-legal · mn-legal-dog · mn-sd-legal ·
qt-indoor-op · qt-outdoor-op · xm-legal-dog · xm-sd-legal`

---

## 6. Wave-02 前置门禁与本次为何先做上面这些

母版 §30：`30–50 Place` 只有在
`ANIMAL_SCOPE_REMODEL_GATE = PASS` **且** `PILOT_REVIEW_PUBLISH_GATE = PASS` 时才允许启动。

```
ANIMAL_SCOPE_REMODEL_GATE = PASS   （ANIMAL_SCOPE_REMODEL_FINAL_REPORT.md + UNFINISHED_TASK_MATRIX）
PILOT_REVIEW_PUBLISH_GATE = PASS   （FIRST_REAL_PUBLISH_BATCH_01B_EXECUTION.md，2026-09-17 起）
30_50_PLACE_EXPANSION     = ALLOWED
```

两 Gate 均已 PASS，因此 Wave-02 **在治理上已解锁**。但 Wave-02 是「30–50 个场所」的扩张，
而扩张的价值前提是**已有已批准规则真的落地**——本次一查就发现 13 行 gate-PASS 的遗留没落，
其中 11 行可写、再演练收敛到 9 行安全。**先把这 9 行落地，比再灌 10 个新场所更接近目标**
（当前 20 个场所里只有 14 个有现行规则）。

本次**没有启动 Wave-02 的场所采集**，原因见 §7；这不是「停下来」，是把它的真实前置做完了。

---

## 7. 未做（明确分类，不含自我设限）

| 项 | 状态 | 原因 |
|---|---|---|
| **SAFE-9 打生产** | **等授权** | 你的授权文档 §4 明写「不得创建或修改其他规则」，范围是世纪公园单条。9 行生产发布超出该范围，且属破坏性操作 —— 必须有你一句话的显式授权。演练证据已齐备（§5）。 |
| 2 条 `SEMANTIC_REMODEL_REQUIRED`（dl-sd-op / qt-sd-op） | **真阻塞** | 但书基底的 scope 不可达（OPERATOR_POLICY `ordinary_pet` base 管不到 `service_dog`）。需语义改造 + 新候选 + 新人工审查，不是收窄或授权能解决。 |
| Home / Search / MatchExplain / Share / Watch 迁移到答案模型 | 剩余工程项 | 可做，未做；本轮先把契约与 Place Detail 打通。 |
| Wave-02 场所采集（30–50） | 未启动 | 每个新场所需要真实可核验来源（Wave01 的硬约束），且人工审查必然 BLOCKED_HUMAN。先落地 §5 的 9 行更划算。 |
| 统一 AccessAnswer 的 200% zoom / reduced-motion 验证 | 遗留（母版 §26 的既有 PARTIAL） | 与本轮无关，未触碰。 |

---

## 8. 本轮产物

**新增（已提交 `f074ae9`）**

- `services/api/app/rulespec/access_answer.py`
- `tests/unit/test_access_answer.py`（12）· `tests/integration/test_access_answer_api.py`（7）
- `scripts/verify_access_answer_real.py`
- `services/api/app/api/v1/v05.py`（端点）· `packages/client-core/src/api/client.ts`（类型 + 方法）·
  `apps/client-h5/src/views/PlaceView.vue`（消费）

**探测/演练产物（`artifacts/`，gitignored）**

`wave02/` 下：`r3_executable_rehearsal_{pre,post}.json` · `r3_executable_rehearsal_execute.txt` ·
`r3_executable_rehearsal_integrity.json` · `safe9_{pre,post}.json` · `safe9_execute{,_2nd}.txt` ·
`safe9_integrity.json` · `production_untouched.json`；
另 `r2_final_r3_disposition_post.json` · `r2_final_r3_executable_probe*.json` ·
`access_answer_real.json`

**质量基线**

```
PYTEST       = 825 passed / 2 skipped   （806 → 818（+12 unit）→ 825（+7 integration））
RUFF         = 新增文件全绿；全仓仅剩 3 项既有 E501（ad936d7 引入，见 WAVE01_FINAL_CLOSURE_FINDING_R1）
MYPY         = Success（87 files，+1）
H5 BUILD     = PASS（vue-tsc + vite）· ESLint 0 · Prettier ✓
```

---

## 9. 需要你决定的一件事

```
HUMAN_ACTION_REQUIRED = REAL_PUBLISH_AUTHORIZATION_FOR_R3_SAFE_9_BATCH
```

授权即执行下列**已演练通过**的批次（生产零风险已验证，克隆上两次跑一致）：

- 清单：`artifacts/r2_final_r3_safe_9_probe.json`
  （若要作为正式治理产物，我会把它移到 `docs/governance/publish_batches/R2_FINAL_R3_BATCH_02.json` 并去掉探针措辞）
- 预期：`access_rule 20 → 26`、`rule_exception 6 → 9`、`failed = 0`、二次 execute `NOOP = 9`
- 复核人签名：`huangdi97`（登记表 `review_decisions_r2_final.json`，37/37 已签）

若不授权，Wave-02 的场所采集可以照常启动——但我会在报告里记明「先扩量后落地」的顺序风险。
