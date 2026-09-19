# WAVE01 FINAL CLOSURE REPORT

轮次：`REAL_PUBLISH_AUTHORIZATION_FOR_CENTURY_PARK_BATCH`（Wave-01 收口）
授权人 / 决定人：`huangdi97`
执行基线：`ad936d7`（本轮开始时 HEAD）
生产库：`petaccess`（PRODUCTION）· alembic `f2a1c7d9e034`（前后一致）
性质：**真实生产写入 1 行**（本报告的全部结论都以该次写入的实测产物为据）

---

## 0. 结论指标（授权 §11 逐项）

```
REAL_PUBLISH_EXECUTED          = YES
BATCH_SELECTED                 = 1
ACCESS_RULE_CREATED            = 1
RULE_EXCEPTION_CREATED         = 0
SECOND_EXECUTE_NOOP            = 1
CENTURY_PARK_RESOLVER          = PASS
ZONE_SCOPE_PRESERVED           = PASS
UNcovered_ZONE_NOT_AUTO_ALLOWED= PASS
EVIDENCE_ACCEPTANCE_TRACE      = PASS
OPERATOR_FIRST_PARTY_VERIFIED  = false
FIRST_PARTY_OPERATOR_SOURCE_PENDING = true
SOURCE_NOTES_MUTATED           = NO
PRODUCTION_INTEGRITY_CRITICAL  = 0
PRODUCTION_INTEGRITY_HIGH      = 0
```

补充（授权 §9 / §12 要求的其余项）：

```
CROSS_LAYER_EXCEPTION          = 0
INERT_EXCEPTION                = 0        （ZERO_INERT_RULES = PASS）
DUPLICATE_CURRENT_NEW          = 0
OLD_FROZEN_CANDIDATES_MUTATED  = 0
OLD_HUMAN_REVIEW_DIFF          = 0
CURRENT_EXECUTABLE             = 0        ← Wave-01 不留「已批准且当前可执行但未处理」的候选
```

---

## 1. 执行前重检（授权 §3）— 十二项闸门逐项值

`BATCH_SELECTED = 1`（`docs/governance/publish_batches/EXP_R1_W01_REVIEW_R1_BATCH_03_CENTURY_PARK.json`，
`dependency_closed = true`，`supersedes = []`）。

闸门不是"跑了一次 dry-run 说 PASS"，而是逐项读出实值：

| # | 闸门 | 结果 | 实测值 |
|---|---|---|---|
| 1 | HUMAN_DECISION | PASS | `final_decision=APPROVED` · `reviewer=huangdi97` · `reviewed_at=2026-09-18T07:31:10.598135Z` |
| 2 | EVIDENCE | PASS | bundle `ccefd2ba…` · `quoted_fragment` 非空 · `content_hash=f61ff4e2…`（bundle 与 artifact 一致） |
| 3 | HUMAN_EVIDENCE_ACCEPTANCE | PASS | `CENTURY_PARK_EVIDENCE_ACCEPTANCE_R1` · structural_problems=[] · drift_problems=[] · released=true |
| 4 | SOURCE_IDENTITY | PASS | `source ca5b81a7…` · `source_type=government_service` · `issuer=上海市文化和旅游事业发展中心…（转述世纪公园官方口径）` · `directness=secondary` |
| 5 | SOURCE_DRIFT | PASS | 库中 source 与接受记录断言逐字一致（类型/issuer 均未漂移） |
| 6 | FRESHNESS | PASS | `collected_at=2026-09-18T01:47:31Z` · 证据龄 **1 天** · `STALE_DAYS=180` |
| 7 | LICENSE | PASS | `storage_allowed=true` · 非 `ordinary_user` lead-only 类型 · 弱证据由 acceptance 放行（ADR-021 未被绕过） |
| 8 | PLACE_MATCH | PASS | `zone.place_id == candidate.place_id` · `place_match_evidence.matched_by=canonical_name_and_address` |
| 9 | SCHEMA | PASS | `ordinary_pet / enter / prohibited / OPERATOR_POLICY / operator_discretion` · `subject_scope_normalized=ordinary_pet` + `normalization_type=exact` · conditions=[] |
| 10 | CONFLICT | PASS | `unresolved_conflict` 违反项 = []（该 place 发布前无任何 rules） |
| 11 | SUPERSESSION | PASS | `plan.supersedes=[]` · 该 `rule_id` 不在 `superseded_semantics.json` · `SUPERSEDED_SEMANTICS_SELECTED=0` |
| 12 | EXECUTION_CONTRACT | PASS | `DEPENDENCY_CLOSED=PASS` · `SELECTED_BUT_BLOCKED=0` · `preflight_problems=[]` · `DRY_RUN_ZERO_DB_MUTATION=true` · 发布前计数 19/6/75/9666 与指纹一致 |

```
FINAL_EXECUTABLE = 1     （计划 1 行，publishable=true，gate=PASS）
dependency_closed = PASS
supersedes = []
```

可复现命令：

```bash
.venv/Scripts/python.exe scripts/verify_century_park_publish_gates.py \
  --database-url "postgresql+psycopg://…/petaccess" \
  --batch-file docs/governance/publish_batches/EXP_R1_W01_REVIEW_R1_BATCH_03_CENTURY_PARK.json \
  --registry artifacts/wave01_register_reprojected.json \
  --evidence-acceptance docs/governance/evidence_acceptance/CENTURY_PARK_EVIDENCE_ACCEPTANCE_R1.json \
  --dry-run-json artifacts/wave01_closure_r1/precheck_dryrun.json \
  --out artifacts/wave01_closure_r1/precheck_per_gate.json
```

---

## 2. 真实发布（授权 §4）

```
REAL_PUBLISH_EXECUTED  = YES
ACCESS_RULE_CREATED    = 1
RULE_EXCEPTION_CREATED = 0
FAILED                 = 0
PUBLISH_TARGET_DB      = petaccess / PRODUCTION
```

产物：

| 对象 | id |
|---|---|
| published `access_rule` | `149828d0-b995-4a99-986e-fd740cea4466` |
| 来源 `rule_candidate` | `4e217d58-1060-4945-9fa1-b9b7e17d7e64` → `PUBLISHED` |
| 落点 | place `c63f2199…`（世纪公园）/ zone `aee59c64…`（世纪公园其他区域） |
| 保真 | `layer_preserved=true` · `mandatory_preserved=true` |
| 审计契约 | `CLI_PUBLISH_AUDIT_CONTRACT = PASS`（checked=1 / missing=0 / exception_audit_without_base=0） |

**没有创建或修改其他规则**：

```
access_rule   19 → 20   (added=['149828d0-…'], removed=[], mutated=[])
rule_exception 6 →  6   (added=[], removed=[], mutated=[])
rule_candidate 75 → 75  (+0 -0 ~1，唯一 mutated = 4e217d58… 即本批候选)
audit_log   9666 → 9668 (+2 -0 ~0)
```

---

## 3. 幂等（授权 §5）

同一清单、同一 reviewer、同一 acceptance 再执行一次：

```
NOOP_COUNT                 = 1
ACCESS_RULE_CREATE_COUNT   = 0
rule 1  publication_type   = NOOP_ALREADY_EXISTS
counts.published = 0 · failed = 0
NEW_WRITES                 = 0
```

`SECOND_EXECUTE_NOOP = 1`。

---

## 4. 生产指纹前后（未改生产库之外任何东西的唯一可信证据）

```
PRODUCTION_FINGERPRINT_A = 45f995a9a52085101a39811531c79d67845d71f9b292142ac697d0d16ab63952   (pre)
PRODUCTION_FINGERPRINT_B = 67f7b19ef3c310ad6b07df749ac76fe4862f82653aa723ed900a4cbc083e853d   (post)
```

差异恰为本批应产生的 3 处，别无其他：

```
access_rule    +1 -0 ~0   added=['149828d0-b995-4a99-986e-fd740cea4466']
audit_log      +2 -0 ~0   added=['203d833e…','9dce4dec…']（transition + publish）
rule_candidate +0 -0 ~1   mutated=['4e217d58-1060-4945-9fa1-b9b7e17d7e64']
duplicate_current_groups = 0 → 0
```

`rule_candidate` 的**唯一** mutation 就是本批候选自身 —— 这就是
`OLD_FROZEN_CANDIDATES_MUTATED = 0` 的可复现依据（74 条旧候选行逐行摘要未变）。

---

## 5. 发布后解析器与 Zone 作用域（授权 §6）

走**真实 API**（`POST /api/v1/places/{place_id}/effective-rules`），不直连数据库：

| 查询 | zone | effect | compliance_state | 判定 |
|---|---|---|---|---|
| ordinary dog / cat（enter） | 世纪公园其他区域（规则所在 zone） | `prohibited` | CONSISTENT | 与已审 Candidate 一致 |
| guide_dog | 世纪公园其他区域 | `unknown` | UNKNOWN | 无 carve-out，**不臆造允许** |
| ordinary dog | 世纪宠物乐园（芳花园区域）**无规则覆盖** | `unknown` | UNKNOWN | **不得自动解释成 ALLOWED** |
| ordinary dog | **不带 zone**（place 级） | `unknown` | UNKNOWN | **Zone 规则未被提升成 Place 总状态** |

第二条引擎（`POST /api/v1/rules/evaluate`）独立复核，结论一致：

```
zone 级 : status=RESTRICTED  matched=['149828d0-…']  reason=['explicit_prohibition']  source_refs=['ca5b81a7-…']
place 级: status=UNKNOWN     matched=[]              reason=['no_rule_in_scope']      source_refs=[]
```

DB 层面同样成立：`access_rule.zone_id = aee59c64…`（**非 NULL**）、`place_id = c63f2199…`、
`supersedes_rule_id = NULL`。

```
CENTURY_PARK_RESOLVER           = PASS
ZONE_SCOPE_PRESERVED            = PASS
UNcovered_ZONE_NOT_AUTO_ALLOWED = PASS
```

---

## 6. 消费端答案与证据链（授权 §7 / §8）

### 6.1 可以显示的 / 不可以显示的

- 已发布的来源事实：`source_type = government_service`、`directness = secondary`、
  `issuer = 「上海市文化和旅游事业发展中心《…》（转述世纪公园官方口径）」`、
  `notes = "capture_method=search_snippet; needs_verification=True"`。
- 该来源**可以从公开读路径取到**：`GET /api/v1/sources?source_type=government_service` 命中，
  字段齐全（这是 AccessAnswer 要展示的证据面，不是内部表）。
- 全部已发布 surface（place detail / rules / zone rules / regulations / extras / answerability /
  sources）的原始 payload 中，禁用表述命中数 = **0**：
  `官方已确认` / `official_operator_policy` / `operator first-party verified` / `一手来源已核验`。

```
CONSUMER_NO_FORBIDDEN_CLAIM = PASS   （forbidden_claim_hits = []）
```

### 6.2 证据链可追溯性

```
Source  ca5b81a7-ca5b-495c-9026-6d8b69dbaea7   government_service / secondary / verified(issuer 标识核验)
  └─ SourceArtifact aadfcee9-…                 web_page_text / collected 2026-09-18T01:47:31Z
  └─ EvidenceBundle ccefd2ba-…                 evidence_class=original / publisher_type=government_official
       quoted: 「温馨提示：除世纪宠物乐园区域外，世纪公园其他区域仍禁止携带宠物入园。」
  └─ RuleCandidate 4e217d58-…                  REVIEW_PENDING → APPROVED → PUBLISHED
  └─ Human Evidence Acceptance                 CENTURY_PARK_EVIDENCE_ACCEPTANCE_R1（具名 huangdi97）
       operator_first_party_verified = false   first_party_operator_source_pending = true
  └─ AccessRule 149828d0-…                     current / zone 级
```

审计事件（`audit_log`，本候选 + 本规则共 4 条）：

```
2026-09-18T01:47:53Z  candidate.create      actor_role=admin  after=MATCH_PENDING
2026-09-18T01:47:53Z  candidate.transition  actor_role=admin  after=REVIEW_PENDING
                      note='WAVE01/EXP-R1-W01-20260918: 待人工审核（不得自动批准或发布）'
2026-09-19T05:11:30Z  candidate.transition  actor_role=admin  after=APPROVED
                      note='human review by huangdi97'
2026-09-19T05:11:30Z  candidate.publish     actor_role=admin  target=access_rule 149828d0-…
```

```
EVIDENCE_ACCEPTANCE_TRACE = PASS
```

### 6.3 本次的诚实局限（不修饰）

1. **统一 AccessAnswer 面仍未实现**（master goal 清单 `C UX | AccessAnswer` 项）。因此 §7 的
   断言只能落在**已发布**的 surface 与来源读路径上：数据面齐备（`source_type` 等可公开读到），
   但**没有一个统一答案模型替消费者把它组合成一句"政府平台转述园方口径"**。这是 Wave02/UX 的
   存量项，不是本次发布引入的缺陷，也不能被读成"已经具备"。
2. **DB 中评审人与执行者共用 `actor_user_id`**。`rule_candidate.reviewer_id` 指向执行账号
   （`ccfe8e68…`，与 `audit_log.actor_user_id` 同值，≠ 有人签字——陷阱 #86）。人类评审人
   `huangdi97` 按**现有 schema 的字段分工**记录在两处：`audit after_state.note`
   （`'human review by huangdi97'`）与签署产物（登记表 `reviewer/reviewed_at`、acceptance
   `reviewer/decided_at`）。**不能**从 `reviewer_id` 反推"是谁批的"。
3. **acceptance 不是 DB 行**，是仓库内具名签署文件（设计如此：它不做决定，只让人的决定可机器复核）。
   每次运行都与 `source` 表重新比对，漂移即失效。
4. `access_rule.last_verified_at` 为 NULL ⇒ `answerability` 的 `ordinary_dog_entry` 在 place 级报
   `unknown / 从未核验`（历史存量，本批未授权触碰）。

---

## 7. 生产完整性与旧 Wave01 作废守卫（授权 §9 / §10）

### 7.1 完整性扫描（`check_production_integrity.py`，23 项，只读）

```
PRODUCTION_INTEGRITY_SCAN = PASS
severity_counts = {'MEDIUM': 1}
CRITICAL = 0     （CONFLICTING_CURRENT_RULES / CROSS_LAYER_EXCEPTION / HOLD_OR_REJECTED_PUBLISHED /
                  ORPHAN_RULE_EXCEPTION / SELF_SUPERSEDE / SUPERSESSION_CYCLE 全为 0）
HIGH     = 0     （DUPLICATE_CURRENT_RULE / PUBLISHED_WITHOUT_{AUDIT,EVIDENCE,SOURCE,CANDIDATE} /
                  ORPHAN_{ZONE,PLACE_RELATION} / TEST_* 全为 0）
MEDIUM   = 1     AUDIT_TARGET_ID_UNUSABLE 2647 rows / 4 groups —— 历史存量项，与本次发布无关
```

`DUPLICATE_CURRENT_NEW = 0`（`DUPLICATE_CURRENT_RULE = 0`，且指纹 `duplicate_current_groups=0→0`）。

### 7.2 旧 Wave01 对象继续不可执行

三个旧 planning artifact 全部 `execution_status = OBSOLETE_NON_EXECUTABLE`，dry-run **也**被拒：

```
EXP_R1_W01_REVIEW_R1_BATCH_01   → REFUSED  exit 4
EXP_R1_W01_REVIEW_R1_BATCH_01A  → REFUSED  exit 4
EXP_R1_W01_REVIEW_R1_BATCH_02   → REFUSED  exit 4
```

反事实（新建清单重列被取代的 id，文件刻意放在 `artifacts/` 而非治理目录）：

```
BATCH_ID                    = COUNTERFACTUAL-RELIST-SUPERSEDED-WAVE01
BATCH_SELECTED              = 2
SUPERSEDED_SEMANTICS_SELECTED = 2
BATCH_VALIDATION            = FAIL（2 项）
  - w01-3a04d4d1aa: SUPERSEDED_BY_SCOPE_REMODEL_R2，已被 [sr2-7b595de9e0, sr2-4580ab2160, sr2-4ca5e55a6a] 取代
  - w01-6f2bfd39d7: SUPERSEDED_BY_SCOPE_REMODEL_R2，已被 [sr2-a4e2ba26f5, sr2-27893d75aa, sr2-2a3de3abde] 取代
exit = 4
```

```
w01-3a04d4d1aa / w01-6f2bfd39d7 / w01-305fa08c1e = SUPERSEDED_NON_EXECUTABLE（保持）
旧 planning manifests                             = OBSOLETE_NON_EXECUTABLE（保持）
重新列入新 manifest 的尝试                          = REFUSED（exit 4，实测）
OLD_HUMAN_REVIEW_DIFF = 0                         （本轮 git 无任何已跟踪文件变更）
```

---

## 8. Wave01 最终闭环分类（授权 §12）

> **⚠️ 口径声明（2026-09-19 补，见 `WAVE02_START_AND_R2FINALR3_BACKLOG_REPORT.md` §2）**
> 下表的 `CURRENT_EXECUTABLE = 0` **只对 `EXP-R1-W01-REVIEW-R1` 这 31 行成立**。
> 项目级并非 0：`R2-FINAL-R3` 登记表另有 **13 行「单行 gate=PASS 且未发布」**
> （另 2 行 publish blocked），加上本表 3 条 SUPERSEDED 与 2 条 REJECTED，
> 全局「APPROVED 且未发布」= 18。本表不能被读成项目级闭环。

登记表 `EXP-R1-W01-REVIEW-R1` 共 **31** 行，按处置分桶（发布后重新实测，非复述）：

| 分类 | 条数 | 说明 |
|---|---|---|
| `ALREADY_PUBLISHED_APPROVED` | 12 | 11 条历史 + 本次世纪公园 `w01-4e217d5810` |
| `SUPERSEDED_APPROVED` | 3 | `w01-3a04d4d1aa` / `w01-6f2bfd39d7` / `w01-305fa08c1e`；人类决定 APPROVED 未变，执行状态永久 SUPERSEDED |
| `HOLD` | 14 | 人类决定 = HOLD，未发布、未被推翻 |
| `REJECTED` | 2 | `w01-f25e4093dd`（CHARLIE'S）/ `w01-e3d398390d`（西岸梦中心） |
| `PUBLISH_BLOCKED` | 0 | 无「暂时被阻塞但可修」的行 |
| `CURRENT_EXECUTABLE` | **0** | ✅ Wave-01 不再留下"已批准且当前可执行但尚未处理"的 Candidate |

```
APPROVED_TOTAL                = 15
ALREADY_PUBLISHED_APPROVED    = 12
SUPERSEDED_APPROVED           = 3
CURRENTLY_EXECUTABLE_APPROVED = 0
PUBLISH_BLOCKED_APPROVED      = 0
HUMAN_DECISION_REWRITTEN      = 0
```

分类器：`scripts/wave01_approved_disposition_audit.py`（重跑当前版本全部闸门，不复述旧结论）。

---

## 9. 未闭合项（分类明确，均不阻塞 Wave01 收口）

| 项 | 状态 | 依据 |
|---|---|---|
| **上海动物园 dog** | 继续 `HOLD` | 候选 `a4e2ba26-f542-…` `REVIEW_PENDING` / `published_rule_id=None`；生产动物园 dog `access_rule = 0`（现有仅 cat/other）；`JPROV-001.applies_to_layer = LEGAL`（未跨层放宽）；登记表 sha256 `ce97d75e2e2e5295…` 未变 |
| **B5** | `PUBLIC_BETA_REAL_MAP_DATA_QUALITY_ITEM` | `place = 20/20` 有坐标、缺坐标为 0；2 条 address-level（CHARLIE'S 马当路店 / omitofee 上海首店）待运营方门牌确认；**不阻挡 Wave01 governance closure** |
| **ADR-032 LegalProvision** | 独立 engineering track | 未生成 migration、未触碰历史行（Touch=0）；**不阻挡 Wave02** |

---

## 10. 本轮形变与产物

**新增（未跟踪 → 已提交）**

- `scripts/verify_century_park_publish_gates.py` —— 十二项闸门逐项探针（复用 canonical 闸门，不新造）
- `scripts/verify_century_park_publish.py` —— 发布后解析器 / 追溯 / 消费端 / source.notes 四段验证
- `docs/governance/WAVE01_FINAL_CLOSURE_REPORT.md`（本文件）

**产物（`artifacts/wave01_closure_r1/`，gitignored）**

`fingerprint_pre.json` / `fingerprint_post.json` · `precheck_dryrun.json` · `precheck_per_gate.json` ·
`execute_1.txt` / `execute_2.txt` · `publish_snapshot_century_park{,_2nd}.json` ·
`post_publish_verify.json` · `integrity_post.json` · `guard_recheck.txt` ·
`counterfactual_relist_superseded.json` · `wave01_disposition_audit_post.json`

**质量基线（本轮实测）**

```
PYTEST      = 806 passed / 2 skipped   （与 ad936d7 基线一致；本轮未改任何源文件或测试文件）
RUFF        = 新增 2 个脚本 All checks passed
RUFF(全量)  = FAIL 3 项 —— 全部位于 ad936d7 引入的
              tests/unit/test_superseded_semantics_and_evidence_acceptance.py（E501 ×3，既有问题，见 §11-5）
MYPY        = NOT_RUN（本轮未改 services/api 下任何文件）
COMMIT      = 17209cd
```

**未做（刻意）**

- 没有重新打开任何已关闭的旧问题；没有改写任何人类决定（`HUMAN_DECISION_REWRITTEN = 0`）
- 没有写 `source.notes`（`SOURCE_NOTES_MUTATED = NO`：前后逐字节相同，且未写入治理标记）
- 没有生成 / 运行 migration；没有触碰 ADR-032 schema
- **没有启动 Wave02**（见 §11）

---

## 11. 诚实局限与下一步

### 局限

1. **本批次未跑演练库 rehearsal**。授权 §3 列举的重检集合不含演练；本批为单行 `CREATE_ACCESS_RULE`
   （无例外、无 supersede、依赖闭包 PASS），其可失败模式已由「生产 dry-run 零突变 + 前后指纹差异
   恰为预期 3 处 + 二次 execute NOOP=1」覆盖。**记录为限制，不宣称已演练。**
2. 统一 `AccessAnswer` 面未实现（见 §6.3-1）。
3. `answerability` 的 `ordinary_dog_entry` 因 `last_verified_at` NULL 报 unknown（历史存量）。
4. 低危观察：`POST /api/v1/rules/evaluate` 的 `matched_rules` 对同一规则重复列出两次：
   `['149828d0-…','149828d0-…']`（占位级重复，不影响 effect 判定；未修，避免本轮扩大范围）。
5. **既有 lint 失败，本轮发现并如实记录**：`ruff check services/api services/worker tests scripts`
   报 3 项 `E501`，全部在 `tests/unit/test_superseded_semantics_and_evidence_acceptance.py`
   （第 37 / 39 / 370 行，均为 101–107 字符），该文件由上一轮 `ad936d7` 引入且未再修改
   （`git status` 干净 ⇒ 提交版本即含此问题）。**这与 Round 6 报告里 `RUFF = PASS` 的写法不一致** ——
   经实测，该断言不成立。本轮**不修改**该文件（不重开已关闭轮次的产物），仅登记为
   `WAVE01_FINAL_CLOSURE_FINDING_R1`，交由 Kaiser 决定是否单独修一轮 lint。
   > **已关闭（2026-09-19 同日）**：该文件因 `superseded_semantics.json` 新增条目必须被编辑，
   > 编辑时随 `ruff format` 折行，3 项 E501 消失。`ruff check .` 现为全仓 All checks passed。
   > 详见 `R2_FINAL_R3_BATCH_02_EXECUTION_AND_BACKLOG_CLOSURE.md` §8。

### 下一步（需要 Kaiser 授权，本报告不自行推进）

Wave-01 已无 `CURRENT_EXECUTABLE`，且不存在新的 P0/P1 governance blocker。
因此 `30_50_PLACE_EXPANSION_R1 — WAVE_02` **在治理上已解锁**，但**本轮不得在同一生产事务中启动**。
启动前请确认：

```
HUMAN_ACTION_REQUIRED = WAVE_02_START_AUTHORIZATION
```
