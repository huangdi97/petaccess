# Round 6 · Wave-01 处置与 Century Park 放行（执行报告）

轮次：`ROUND6_WAVE01_DISPOSITION_AND_CENTURY_PARK_RELEASE_R1`
决定人：`huangdi97`（2026-09-19 四项决定 + 执行顺序 A–H）
基线：`d1a3dbe`（本轮开始时 HEAD）· 生产库 `petaccess`
性质：**无生产写入**（本轮没有发生任何生产写，所有闸门均为 dry-run）

---

## 0. 结论指标

```
# --- A. 旧 planning artifact 作废 ----------------------------------------
OLD_PLANNING_MANIFEST_MARKED            = 3
OLD_PLANNING_MANIFEST_REPLAY_REFUSED    = 3/3   （exit 4，dry-run 也拒绝）
NEW_MANIFEST_RELIST_REFUSED             = 2/2   （换一个新清单重列旧 id 一样被拒）

# --- B. WAVE01_APPROVED_DISPOSITION_AUDIT --------------------------------
APPROVED_TOTAL                          = 15
ALREADY_PUBLISHED_APPROVED              = 11
SUPERSEDED_APPROVED                     = 3
CURRENTLY_EXECUTABLE_APPROVED           = 1     （世纪公园，仅在 acceptance 之下）
PUBLISH_BLOCKED_APPROVED                = 0     （无 acceptance 时 = 1）
HUMAN_DECISION_REWRITTEN                = 0

# --- C. Century Park -----------------------------------------------------
CENTURY_PARK_GATE_RERUN                 = PASS
CENTURY_PARK_SOURCE_TYPE                = government_service   （库中实读，未改）
CENTURY_PARK_EVIDENCE_STRENGTH          = search_snippet       （未升级）
FIRST_PARTY_OPERATOR_SOURCE_PENDING     = YES
OPERATOR_FIRST_PARTY_VERIFIED_CLAIM     = 0
SAFE_BATCH_GENERATED                    = EXP-R1-W01-REVIEW-R1-BATCH-03-CENTURY-PARK
SAFE_BATCH_DRY_RUN                      = PASS（exit 0）· ACCESS_RULE_CREATE=1
REAL_PUBLISH_EXECUTED                   = NO    （停在授权点）

# --- D. dependency-closed 新批次 -----------------------------------------
NEW_BATCH_REUSES_OLD_MANIFEST           = NO
NEW_BATCH_DEPENDENCY_CLOSED             = PASS
NEW_BATCH_SELECTED                      = 1

# --- E. Shanghai Zoo dog HOLD -------------------------------------------
ZOO_DOG_FINAL_DECISION                  = HOLD  （未改）
ZOO_DOG_REASON                          = HIGHER_LEVEL_GUIDE_DOG_LEGAL_APPLICABILITY_UNRESOLVED
ZOO_DOG_ACCESS_RULE_IN_DB               = 0
JPROV001_CROSS_LAYER_RELAXATION         = 0     （applies_to_layer=LEGAL 实测）
ZOO_DOG_REGISTER_SHA256                 = ce97d75e2e2e5295…

# --- F. LegalProvision ---------------------------------------------------
ADR032_STATUS                           = ADR_ACCEPTED / SCHEMA_DRAFTED
EXISTING_PUBLISHED_ROWS_TOUCHED         = 0
MIGRATION_GENERATED                     = NO    （刻意）
PUBLIC_BETA_BLOCKER                     = NO

# --- G. B5 ---------------------------------------------------------------
PLACE_COORDINATED                       = 20/20
PLACE_MISSING_COORDINATES               = 0
ADDRESS_LEVEL_PENDING_HOUSE_NUMBER      = 2
NEW_STATUS                              = PUBLIC_BETA_REAL_MAP_DATA_QUALITY_ITEM

# --- 质量基线 -------------------------------------------------------------
PYTEST_BASELINE_BEFORE                  = 783 passed / 2 skipped
PYTEST_BASELINE_AFTER                   = 806 passed / 2 skipped（+23 新回归，0 失败）
RUFF                                    = PASS
MYPY                                    = Success（86 files）
NEW_REGRESSION_TESTS                    = 23 passed
```

```
HUMAN_ACTION_REQUIRED = REAL_PUBLISH_AUTHORIZATION_FOR_CENTURY_PARK_BATCH
```

---

## 1. A · 旧 Wave-01 planning artifact 作废

### 1.1 为什么这不是形式主义

先看实测。今天用生产库只读重跑 Wave-01 整份登记表（`--dry-run`，零写入），
两条已经"看起来无害"的旧 APPROVED 基底给出：

| rule_id | place | publication_type | supersedes |
|---|---|---|---|
| `w01-3a04d4d1aa` | 上海迪士尼乐园 | `SUPERSEDE_ACCESS_RULE` | `0d2f70f8…` |
| `w01-6f2bfd39d7` | 上海动物园 | `SUPERSEDE_ACCESS_RULE` | `352f6e0f…` |

而 `0d2f70f8` 和 `352f6e0f` 正是 Scope Remodel R2 **已经发布**的两条 current 规则
（分别来自 `sr2-4ca5e55a6a`、`sr2-2a3de3abde`）。

换言之：整体重跑旧清单不是"重复劳动"，而是让旧的 `other` 全域语义**覆盖**新的拆分语义。
决定人的担心被实测证实，而不是推测。

### 1.2 两层守卫

**第一层 — 清单作废，加载即拒。**
三个旧 planning artifact 都加了 `execution_status = OBSOLETE_NON_EXECUTABLE`：

- `EXP_R1_W01_REVIEW_R1_BATCH_01.json`
- `EXP_R1_W01_REVIEW_R1_BATCH_01A.json`
- `EXP_R1_W01_REVIEW_R1_BATCH_02.json`

`publish_batch.load_manifest` 现在对 `execution_status ∈ {OBSOLETE, NON_EXECUTABLE, OBSOLETE_NON_EXECUTABLE, SUPERSEDED_NON_EXECUTABLE}` 直接抛 `BatchManifestError` —— dry-run 与 execute 同等待遇，不存在"只看不写所以可以"。

实测三个清单重跑，输出见 §1.3。

**第二层 — planner 永久拒绝被取代的语义。**
标记文件回答的是"哪些文件不能跑"；如果这是唯一的守卫，那么新建一个清单把同样的 id 再列一遍就绕过去了。所以新增 `docs/governance/superseded_semantics.json` + 两处消费：

- `publish_batch.validate_manifest`（refusal 6）→ 清单层拒绝；
- `publish_reviewed_r1.build_plan` → 新增 `SUPERSEDED_NON_EXECUTABLE` 发布类型，**不在 `WRITING_TYPES` 里**，所以计划层面就不可写。

人的 `APPROVED` 一个字没动；变动的是执行状态。

### 1.3 反事实验证

```
### EXP_R1_W01_REVIEW_R1_BATCH_01/01A/02
REFUSED — 该批次清单已被标记为不可执行（execution_status='OBSOLETE_NON_EXECUTABLE'）

### 反事实：新清单重列旧 other 基底
BATCH_SELECTED              = 2
BATCH_DEPENDENCY_CLOSED     = PASS
SUPERSEDED_SEMANTICS_SELECTED  = 2
BATCH_VALIDATION = FAIL（2 项）
exit = 4
```

守卫生效前后，同一份登记表的计划对比（生产只读 dry-run）：

| 指标 | 守卫前 | 守卫后 |
|---|---|---|
| `ACCESS_RULE_SUPERSEDE_COUNT` | 2 | **0** |
| `SUPERSEDED_NON_EXECUTABLE` | 0 | **3** |
| 计划覆盖 `0d2f70f8` / `352f6e0f` 的可能性 | 有 | **无** |

---

## 2. B · WAVE01_APPROVED_DISPOSITION_AUDIT

可复现命令：

```bash
.venv/Scripts/python.exe scripts/wave01_approved_disposition_audit.py \
  --registry artifacts/wave01_register_reprojected.json \
  --database-url "postgresql+psycopg://…/petaccess" \
  --evidence-acceptance docs/governance/evidence_acceptance/CENTURY_PARK_EVIDENCE_ACCEPTANCE_R1.json \
  --out artifacts/wave01_disposition_audit.json
```

它**重新实跑**当前版本的全部闸门（Evidence / Freshness / License / Source Scope / ADR-030 / ADR-031 / Jurisdiction proviso / Holder scope / Service role / Supersession / Execution contract），而不是复述上次结论。

登记表的 `final_decision` / `reviewer` / `reviewed_at` / `decision_note` 全部逐字搬运（投影前后 sha256 比对：签名相关字段差异数 = 0）。

### A. SUPERSEDED_BY_SCOPE_REMODEL — 3 条

| rule_id | place | 取代方 | 人类的 final_decision |
|---|---|---|---|
| `w01-3a04d4d1aa` | 上海迪士尼乐园 | `sr2-7b595de9e0` / `sr2-4580ab2160` / `sr2-4ca5e55a6a` | APPROVED（不变） |
| `w01-6f2bfd39d7` | 上海动物园 | `sr2-a4e2ba26f5` / `sr2-27893d75aa` / `sr2-2a3de3abde` | APPROVED（不变） |
| `w01-305fa08c1e` | 上海迪士尼乐园 | `sr2-69e0916a2f` | APPROVED（不变） |

`EXECUTION_STATUS = SUPERSEDED_BY_SCOPE_REMODEL_R2`，planner 永久拒绝。

第三条容易误读：它是导盲犬 carve-out，本身因为遗留条件键 `type` 被 canonical 闸门 BLOCKED。ADR-029 §9 禁止原地改写已签署候选，正确救济是新候选 —— 救济候选 `sr2-69e0916a2f` 已签并随 `SCOPE_REMODEL_R2_BATCH_03` 发布（`rule_exception a9f564bb`，挂在 `892643b0` = `sr2-7b595de9e0` 下）。**它不是被否决，是被实现。**

### B. CURRENTLY_EXECUTABLE — 1 条

| rule_id | place | publication_type | gate |
|---|---|---|---|
| `w01-4e217d5810` | 世纪公园 | `CREATE_ACCESS_RULE` | PASS |

严格地说，它是"在 Evidence Acceptance 之下可执行"。没有 acceptance 时它落 C 类（ADR-021）。
详见 §3。

### C. PUBLISH_BLOCKED — 0 条（无 acceptance 时 1 条 = 世纪公园）

除了已被 A 类吸收的 `w01-305fa08c1e`（BLOCKED 原因在 `superseded_semantics.json.measured_evidence` 里有逐字记录），没有其它"暂时 BLOCKED"的行。
没有拿任何一行去做"改人类决定换它通过"的交易。

### 另外 11 条：ALREADY_PUBLISHED

单列而不是计入"剩余 APPROVED" —— 混在一起会让每个数字虚高。

---

## 3. C · Century Park：接受，但不是升级

### 3.1 库中实读（`source ca5b81a7`）

```
source_type          = government_service          ← 决定人要求的标识，库中已经是
issuer               = 上海市文化和旅游事业发展中心《又一新地标！这个周末，带「毛孩子」来放飞》
                       （转述世纪公园官方口径）
issuer_verification  = verified
directness           = secondary
source_availability  = available_online
notes                = capture_method=search_snippet; needs_verification=True
```

也就是说：**标记是对的，不需要改 semantic 标签。** 缺的不是标识，是一个"具名人类是否在此前提下行"的记录。

### 3.2 机制：signed evidence acceptance（`scripts/evidence_acceptance.py`）

刻意**不**做成"证据强度升级"。`evidence_strength` 在登记表、计划、审计里仍是 `search_snippet`。
改的是「是否有署名人类在知情前提下接受这条弱证据」，不是「这条证据变成一手」。

记录文件：`docs/governance/evidence_acceptance/CENTURY_PARK_EVIDENCE_ACCEPTANCE_R1.json`
—— 内容是决定人原话的逐字转录，不是机器生成的措辞。

每次运行都要与库重新比对：acceptance 断言什么类型的 source，就必须仍是那个类型。

### 3.3 四个反事实，全部 REFUSED（exit 4）

| 反事实 | 结果 |
|---|---|
| 不带 acceptance 跑同一批次 | `弱证据(search_snippet)不得 APPROVED（ADR-021）` → exit 3 |
| acceptance 声称 `official_operator_policy` | `REFUSED — 不在允许词表 ['government_service'] 内` |
| acceptance 声称 `operator_first_party_verified = true` | `REFUSED — 必须显式为 false` |
| acceptance 指向别的 source（漂移） | `REFUSED — source.source_type 已漂移…必须重新审阅` |

### 3.4 放行后的 Pre-Publish Gate：PASS

```
EVIDENCE_ACCEPTANCE_FILES = 1（放行 1 行弱证据；接受记录每次都要与库重新比对）
EVIDENCE_ACCEPTANCE: w01-4e217d5810 弱证据(search_snippet)已由具名人类评审员
  通过 signed evidence acceptance 接受放行；证据强度未提升，
  FIRST_PARTY_OPERATOR_SOURCE_PENDING 仍为真。
```

```
w01-4e217d5810  publication_type = CREATE_ACCESS_RULE  gate = PASS  supersedes = []
```

`supersedes = []` —— 它是新规则，不覆盖任何现行规则。

### 3.5 显式 safe batch（dry-run PASS，未执行）

`docs/governance/publish_batches/EXP_R1_W01_REVIEW_R1_BATCH_03-CENTURY-PARK`
只含 1 条，是新立的 dependency-closed 清单，不继承任何已作废 artifact：

```
BATCH_SELECTED              = 1
BATCH_DEPENDENCY_CLOSED     = PASS
BATCH_VALIDATION            = PASS
ACCESS_RULE_CREATE_COUNT    = 1
SELECTED_BUT_BLOCKED        = 0
DRY_RUN_ZERO_DB_MUTATION    = PASS
exit                        = 0
```

---

## 4. D · CURRENTLY_EXECUTABLE 的新批次

就是 §3.5 的那个清单。它满足：

- 新立，**不复用** Wave-01 任何整批 manifest；
- dependency-closed（`BATCH_DEPENDENCY_CLOSED = PASS`）；
- 只含真实通过当前版本全部闸门的那 1 条；
- **没有**"APPROVED ⇒ 自动 Publish"：发布仍需 `--execute --production-confirm --reviewer huangdi97`。

---

## 5. E · Shanghai Zoo dog：一字未动

```
final_decision     = HOLD
reviewer           = huangdi97
decided_at         = 2026-09-18T22:42:35+08:00
decision_note      = HIGHER_LEVEL_GUIDE_DOG_LEGAL_APPLICABILITY_UNRESOLVED：
                     现有 JPROV-001 属 LEGAL layer，不得跨层替代这一未解决的法律适用性问题。
```

生产实测：

| 检查 | 值 |
|---|---|
| 候选 `a4e2ba26` review_status | `REVIEW_PENDING`（未发布） |
| 候选 `published_rule_id` | `None` |
| 上海动物园 dog `access_rule` 数 | **0** |
| 上海动物园 `access_rule` 总数 | 2（cat / other，**dog 不在其中**） |
| `JPROV-001.applies_to_layer` | `LEGAL` |
| 注册表 sha256（前 16） | `ce97d75e2e2e5295` |

**没有**用 JPROV-001 跨层放宽 OPERATOR_POLICY —— `applies_to_layer=LEGAL` 是实测读出来的，不是承诺。
未来若取得新的法律依据，路径是：new candidate / new review revision / new human review。

---

## 6. F · LegalProvision：独立 track，已立项未动数据

`docs/governance/ADR032_LEGAL_PROVISION_LINEAGE_R1.md`

```
MUTATE_EXISTING_PUBLISHED_ROWS   = NO
EXISTING_PUBLISHED_ROWS_TOUCHED  = 0
EXISTING_AUDIT_EVENTS_REWRITTEN  = 0
MIGRATION_GENERATED              = NO   （刻意：本轮不动 schema）
NEW_DATA_PATH_IMPLEMENTED        = NO
PUBLIC_BETA_BLOCKER              = NO
```

additive model 见 ADR §3：`legal_instrument` / `legal_provision` / `statutory_proviso` /
`statutory_proviso_legal_provision_link` / `rule_legal_provision_link` / `provision_evidence_link`。

关键的一张表是 `statutory_proviso_legal_provision_link`：「这个但书是第几条第一款的例外」从一个隐含在同行里的事实，变成一条可查询、可校验的关系。

历史 backfill 合同写入 ADR §5：deterministic（同输入同输出）、只写 link 表、`linkage_origin` 区分原生与回填、禁用 place-name 推断、Human Review / Evidence / published timestamp / Audit event **一个字节都不改写**。

---

## 7. G · B5 降级为 PUBLIC_BETA 数据质量项

见 `docs/governance/B5_PUBLIC_BETA_MAP_DATA_QUALITY_R1.md`。

20/20 place 已有坐标；剩余 2 条（CHARLIE'S 粉红汉堡马当路店、omitofee 上海首店）精确到「所在商场/园区」，
待门牌确认。它不影响规则治理（Resolver 按 place/zone 判定，坐标不参与 resolution），
但会影响 Public Beta 的真实地图 —— 所以它是 **Beta 前必办的数据质量项**，不是被划掉的项。

---

## 8. 本轮的形变

**新增**

- `scripts/evidence_acceptance.py`
- `scripts/wave01_approved_disposition_audit.py`
- `docs/governance/superseded_semantics.json`
- `docs/governance/evidence_acceptance/CENTURY_PARK_EVIDENCE_ACCEPTANCE_R1.json`
- `docs/governance/publish_batches/EXP_R1_W01_REVIEW_R1_BATCH_03-CENTURY-PARK`
- `docs/governance/WAVE01_APPROVED_DISPOSITION_AUDIT_R1.json`
- `docs/governance/ADR032_LEGAL_PROVISION_LINEAGE_R1.md`
- `docs/governance/B5_PUBLIC_BETA_MAP_DATA_QUALITY_R1.md`
- `tests/unit/test_superseded_semantics_and_evidence_acceptance.py`（23 项）

**修改**

- `scripts/publish_batch.py` —— refusal 6 + 作废清单加载拒绝 + `superseded_semantics` 接线
- `scripts/publish_reviewed_r1.py` —— `SUPERSEDED_NON_EXECUTABLE` 发布类型、`--evidence-acceptance`、
  preflight 的 released 通道、`_source_rows`
- 三个旧 planning manifest —— 加 `execution_status`

**未做（刻意）**

- 没有执行任何生产写入（本轮所有 Execution Gate 都是 dry-run）
- 没有生成 / 运行 migration
- 没有启动 Wave02
- 没有修改任何人类决定
