# FIRST_REAL_PUBLISH_BATCH_01A_CLOSURE

**REAL_PUBLISH_EXECUTED = NO**

本轮产出：Batch 01A 的清单、dry-run、rehearsal、resolver 结果、rollback / supersession / watch、
最终命令。正式 `--execute` **未对正式目标库执行**，等待人类明确授权。

---

## 0. 结论

```
SIGNED_REVISION                     = R2-FINAL-R3
HUMAN_REVIEWER                      = huangdi97
BATCH_ID                            = R2-FINAL-R3-BATCH-01A

BATCH_SELECTED                      = 10
ACCESS_RULE_SELECTED                = 5
RULE_EXCEPTION_SELECTED             = 5
DISNEY_SELECTED                     = 0
HOLD_SELECTED                       = 0
REJECTED_SELECTED                   = 0

BATCH_DEPENDENCY_CLOSED             = PASS
BATCH_PREPUBLISH_EVALUATED          = 10
BATCH_PREPUBLISH_PASS               = 10
BATCH_PREPUBLISH_BLOCKED            = 0

REHEARSAL_EXECUTE                   = PASS
REHEARSAL_ACCESS_RULE_CREATED       = 5
REHEARSAL_RULE_EXCEPTION_CREATED    = 5

RESOLVER_POST_PUBLISH_BATCH_01A     = PASS
ENGINE_CONSISTENCY_BATCH_01A        = PASS
CARVE_OUT_REACHABILITY              = PASS_WITH_LIMITATIONS   ← 见 §5

EVIDENCE_LINKAGE                    = PASS
SOURCE_LINKAGE                      = PASS
AUDIT_LINKAGE                       = PASS

IDEMPOTENCY                         = PASS
ROLLBACK                            = PASS
SUPERSESSION                        = PASS
WATCH                               = PASS

CROSS_LAYER_EXCEPTION               = 0
SELF_SUPERSEDE                      = 0
DUPLICATE_PLAN                      = 0

DISNEY_SEMANTIC_ISSUE               = OPEN
REAL_PUBLISH_EXECUTED               = NO

FIRST_REAL_PUBLISH_BATCH_01A_GATE   = PASS_WITH_LIMITATIONS
```

### 为什么是 PASS_WITH_LIMITATIONS 而不是 PASS

任务书 §7 要求的四条 Fairmont 断言中，三条成立，一条**不成立**：

| 断言 | 结果 |
| --- | --- |
| ordinary_pet → prohibited | ✅ `prohibited` |
| dog → legal prohibition as applicable | ✅ `prohibited` |
| guide_dog → legal exception correct | ✅ `allowed`，应用的是 LEGAL 例外 |
| **guide_dog operator policy → operator exception correct** | ❌ **运营层例外不可达，未生效** |

Library 的「allowed through valid same-layer exceptions」同理：生效的是 LEGAL 层例外，
运营层例外（`lib-sd-op-guide`）未生效。

**用户拿到的答案是正确的**（`allowed`，且 UNKNOWN≠ALLOWED 未被违反），
但「运营层 carve-out 生效」这一条没有被验证为 true。按 §8「不得掩盖」，
记为 `PASS_WITH_LIMITATIONS` 并在此显式列出，而不是写成 PASS。

若人类认为「LEGAL 层已给出正确答案、运营层例外不可达不构成用户可见缺陷」，
可将 `CARVE_OUT_REACHABILITY` 降级为已知限制并判定整体 PASS——**这一判断属于人类，不属于脚本**。

---

## 1. 批次清单

新建：`docs/governance/publish_batches/R2_FINAL_R3_BATCH_01A.json`

```json
{
  "revision": "R2-FINAL-R3",
  "batch_id": "R2-FINAL-R3-BATCH-01A",
  "reviewer": "huangdi97",
  "supersedes_batch": "R2-FINAL-R3-BATCH-01",
  "candidate_rule_ids": [
    "fp-legal-dog", "fp-sd-legal",
    "fp-pets-op-firstparty", "fp-sd-op-firstparty",
    "lib-legal-dog", "lib-sd-legal",
    "lib-pets-op", "lib-sd-op-guide",
    "sb-legal-dog", "sb-sd-legal"
  ]
}
```

`R2_FINAL_R3_BATCH_01.json`（12 条，含迪士尼）**保留未改动**，作为 rehearsal 历史证据。

迪士尼两条 `dl-pet-ban` / `dl-sd-op` 在签署登记表中**仍为 APPROVED**，
仅 `NOT_SELECTED_FOR_BATCH_01A`。未改 HOLD、未改 REJECTED、未重新签署、
未重写 Evidence、未修改 RuleException binding。

---

## 2. 依赖闭包（清单生成期校验）

```
BATCH_DEPENDENCY_CLOSED             = PASS
BATCH_EXECUTION_ORDER = fp-legal-dog -> fp-sd-legal<-fp-legal-dog
                     -> fp-pets-op-firstparty -> fp-sd-op-firstparty<-fp-pets-op-firstparty
                     -> lib-legal-dog -> lib-sd-legal<-lib-legal-dog
                     -> lib-pets-op -> lib-sd-op-guide<-lib-pets-op
                     -> sb-legal-dog -> sb-sd-legal<-sb-legal-dog
```

五条例外全部满足：base 同批且排在前面。无孤儿例外，无跨层绑定
（所有 base / exception 均同层：3 对 LEGAL，2 对 OPERATOR_POLICY）。

---

## 3. Pre-publish 重新评估（当前时刻，真实 gate）

freshness 与时间有关，**未引用上一轮 12/12**。以当前时刻重新执行真实
`publish_gate.evaluate_for_publish()`，对 10 条全部重跑：

```
PREPUBLISH_GATE_RAN                 = True
PREPUBLISH_APPROVED_EVALUATED       = 10
PREPUBLISH_PASS                     = 10
PREPUBLISH_BLOCKED                  = 0
gate_status_counts                  = {"PASS": 10}
DRY_RUN_ZERO_DB_MUTATION            = True
db_cross_checked                    = True
preflight_problems                  = []
```

证据：`artifacts/batch01a_dryrun.json`（文本版 `artifacts/batch01a_dryrun.txt`）。

---

## 4. Rehearsal（真实执行，非 mock）

```
phase0  petaccess --(CREATE DATABASE TEMPLATE)--> petaccess_publish_rehearsal_r3
        guard = PASS, alembic = b8d2f4a1c556
        place=1140 zone=30 access_rule=1012 rule_exception=116
        rule_candidate=413 evidence_bundle=674 source=1327 source_artifact=665 audit_log=8466

phase1  -- 1/3 execute --
        PREPUBLISH_PASS=10  PREPUBLISH_BLOCKED=0
        ACCESS_RULE_CREATE_COUNT=5  RULE_EXCEPTION_CREATE_COUNT=5
        NOOP_COUNT=0  BLOCKED_COUNT=0

        -- 2/3 idempotency（同一批次再执行一次）--
        ACCESS_RULE_CREATE_COUNT=0  RULE_EXCEPTION_CREATE_COUNT=0
        NOOP_COUNT=10  SELF_SUPERSEDE=0  DUPLICATE_PLAN=0
```

走完整链路：signed registry → batch manifest → prepublish → transaction
→ 5 AccessRule → 5 RuleException → Evidence → Source linkage → Audit。**未 mock publication。**

---

## 5. 验证结果（§13–§20）

```
SOURCE_LINKAGE             = PASS
EVIDENCE_LINKAGE           = PASS
AUDIT_LINKAGE              = PASS
RESOLVER_POST_PUBLISH      = PASS
EFFECTIVE_RULES_API        = PASS
ENGINE_CONSISTENCY         = PASS
CARVE_OUT_REACHABILITY     = PASS_WITH_LIMITATIONS
ROLLBACK_DRILL             = PASS
SUPERSESSION_DRILL         = PASS
WATCH_DRILL                = PASS
```

### 5.1 Resolver（只验证本批发布的语义）

| place | query | effect | applied exceptions | expected | verdict |
| --- | --- | --- | --- | --- | --- |
| fairmont | ordinary_pet | `prohibited` | – | prohibited | PASS |
| fairmont | guide_dog | `allowed` | 1（**LEGAL**） | exception-applied | PASS |
| library | ordinary_pet | `prohibited` | – | prohibited | PASS |
| library | guide_dog | `allowed` | 1（**LEGAL**） | exception-applied | PASS |
| library | police_dog | `prohibited` | – | not-allowed | PASS |
| library | military_working_dog | `prohibited` | – | not-allowed | PASS |
| starbucks | ordinary_pet | `prohibited` | – | prohibited | PASS |
| starbucks | guide_dog | `allowed` | 1 | exception-applied | PASS |

HOLD 的 `lib-sd-op-police` / `lib-sd-op-military` **未**使 police / military 变成 ALLOWED。

Zone 级规则未被压平成 place 总状态：三个场所的
`guide_dog_place_level_no_zone` 均为 `unknown`。

### 5.2 引擎一致性

对 Batch 01A 涉及的 3 个场所 × 2 种 service_role = 6 组查询，
domain resolver / `/rules/evaluate` / effective-rules API 全部一致：

| place | service_role | resolver | evaluator | 一致 |
| --- | --- | --- | --- | --- |
| fairmont | none | `prohibited` | `RESTRICTED`(explicit_prohibition) | ✅ |
| fairmont | working | `allowed` | `MATCH`(explicitly_allowed) | ✅ |
| library | none | `prohibited` | `RESTRICTED` | ✅ |
| library | working | `allowed` | `MATCH` | ✅ |
| starbucks | none | `prohibited` | `RESTRICTED` | ✅ |
| starbucks | working | `allowed` | `MATCH` | ✅ |

`disagreements = []`。

**迪士尼不计入本批 gate，但其已知 inconsistency 保留为 open issue，不掩盖。**

### 5.3 Carve-out 可达性（本轮新增度量）

| carve-out | base | base scope | carve-out scope | base 覆盖该 subject |
| --- | --- | --- | --- | --- |
| `fp-sd-legal` | `fp-legal-dog` | `dog` | `guide_dog` | ✅ |
| `fp-sd-op-firstparty` | `fp-pets-op-firstparty` | `ordinary_pet` | `guide_dog` | ❌ **不可达** |
| `lib-sd-legal` | `lib-legal-dog` | `dog` | `guide_dog` | ✅ |
| `lib-sd-op-guide` | `lib-pets-op` | `ordinary_pet` | `guide_dog` | ❌ **不可达** |
| `sb-sd-legal` | `sb-legal-dog` | `dog` | `guide_dog` | ✅ |

**5 条例外中 2 条在语义上永不生效**——与迪士尼同一缺陷族
（`ordinary_pet` 不含 `guide_dog`，见 ADR-025）。

与迪士尼的差别在于：费尔蒙 / 上图同时发布了 LEGAL 层（`dog` base + `guide_dog` exception），
LEGAL 例外可达并给出正确答案；迪士尼只有 OPERATOR_POLICY 一层
（`dl-legal-dog` / `dl-sd-legal` 为 HOLD），所以结果是 `UNKNOWN`（错误的用户状态）。

详见 `docs/governance/DISNEY_SCOPE_EXCEPTION_SEMANTIC_ISSUE.md` §6。

### 5.4 Idempotency

第二次执行：`NOOP_COUNT = 10`，新建 AccessRule / RuleException / current RuleVersion 均为 0，
`SELF_SUPERSEDE = 0`，`DUPLICATE_PLAN = 0`。

### 5.5 Rollback（完整依赖对：sb-legal-dog + sb-sd-legal）

| step | access_rule 行 | rule_exception 行 | evidence | source | audit |
| --- | --- | --- | --- | --- | --- |
| before | ✅ | ✅ | 2 | 1 | 2 |
| 撤回例外后 | ✅ | ✅ | 2 | 1 | 3 |
| 撤回 base 后 | ✅ | ✅ | 2 | 1 | 3 |

- 撤回例外：guide_dog 从 `allowed` → `prohibited`（回到 base），**不是 ALLOWED**
- 撤回 base：guide_dog → `unknown`，ordinary_pet → `unknown`
- **WITHDRAWN → ALLOWED 未发生**；Evidence / Source / Audit / RuleVersion 全部保留

### 5.6 Supersession

```
V1 b572ed24…  status=superseded
V2 9160b6be…  status=current  supersedes_rule_id = b572ed24… (V1)
同一身份 current 版本数 = 1
supersession_edges = 1   cycles = []   self-supersede = 0
```

### 5.7 Watch

```
sink_baseline = 10   本次演练新增消息 = 1
first_sweep  notified_watches = 1
retry_sweep  notified_watches = 0
last_notified_at 两次 sweep 后完全相同（未推进）
本次订阅收到通知数 = 1（应恰好 1）
```

只允许 mock sink（`mock:notifications`）。
注：该场所无 `SourceMonitor` 记录，SSRF 守卫禁止抓取本机地址，
故不构造假的外部抓取——变更→证据链由 verification fixture 直接提供。

---

## 6. Evidence / Source / Audit

10/10 全部验证：Candidate → EvidenceBundle → Artifact → Source → Human Review → Published object → Audit。

```
audit_by_action            = {candidate.transition: 20, candidate.publish: 5, candidate.publish_exception: 5}
audit_exception_with_base  = 5（例外发布审计带 base 依赖记录）
notes_naming_reviewer      = 10（transition note 记录 huangdi97）
transition_before_after    = 10（REVIEW_PENDING → APPROVED 状态对）
linkage problems           = []
```

`candidate.transition = 20` = 10 条 × 2（每次 transition 落 2 条审计）。
上一轮 BATCH-01 的 12 条对应 24 条，比例一致，属既有行为，非本轮回归。

**评审员与执行者继续分离**：`reviewer = huangdi97`（人类署名，写在 audit note 里），
执行 actor 为脚本使用的 admin 账号，两者在审计中分别记录（`distinct_actors = 4`）。

---

## 7. 回归（本轮实跑，不引用旧数字）

| 项目 | 结果 |
| --- | --- |
| pytest 全量 | **594 passed** |
| Publisher 关键测试 ×3 | **112 passed / 112 / 112** |
| ruff check（api+worker+tests+scripts） | PASS |
| ruff format --check | 178 files already formatted |
| mypy（services/api） | Success: 77 source files |
| ESLint | PASS |
| Prettier --check | All matched files use Prettier code style |
| H5 build（E2E variant） | PASS |
| Admin build | PASS |
| 功能 E2E | **18 passed** |
| 视觉回归 | **47 passed** |
| a11y | **0 issues**（serious=0 moderate=0 minor=0） |

### 7.1 关于 pytest 的 3 条失败（已定位，非回归）

首次全量跑出现 3 failed：

```
tests/integration/test_media.py::test_ocr_task_updates_media_for_review_queue
tests/integration/test_media.py::test_ttl_purge_removes_expired
tests/integration/test_v05_e2e.py::test_e2e_a_signage_upload_to_published_rule
```

三者均为 `celery.exceptions.TimeoutError`——测试用 `.delay().get(timeout=30)` 等真实 worker 结果，
而当时**没有运行 celery worker**。启动 worker 后：

```
9 passed（这 3 条所在文件）
全量 594 passed, 0 failed
```

本轮改动只涉及 `scripts/` 与 `docs/`，未触碰 `services/`，可确认非本轮引入。

### 7.2 关于 a11y 的 1 serious（本轮实测为 0，差异已说明，不掩盖）

上一轮记录 `a11y serious = 1`（place 页无可见 h1）。**本轮连续两次实测均为 0**。

原因可从两次产物直接读出：

| | 上一轮 `artifacts/regression_a11y.json` | 本轮 `artifacts/batch01a/a11y.json` |
| --- | --- | --- |
| consumer/place-restricted headings | **0** | **12** |
| consumer/place-restricted interactive | **9** | **24** |
| issues | 1 serious（no visible `<h1>`） | 0 |

上一轮那一页是**退化渲染**（headings=0、可交互元素仅 9 个），
"没有 h1" 是页面没渲染出内容的症状，不是稳定的结构缺陷。

本轮 `git status` 确认 **`apps/` 下无任何改动**（0 个文件），未修前端、未改样式。
因此记录为：

```
A11Y_SERIOUS_THIS_RUN        = 0
A11Y_SERIOUS_PREVIOUS_RECORD = 1（退化渲染所致，本轮未复现）
A11Y_EXISTING_NONBLOCKER     = 0（本轮实测口径）
```

若按"既有缺陷"口径保留，则仍为 1；两种口径都在此列出，不二选一地隐藏。

---

## 8. Disney open issue

新建 `docs/governance/DISNEY_SCOPE_EXCEPTION_SEMANTIC_ISSUE.md`，STATUS = OPEN。

记录内容：base `dl-pet-ban`（`ordinary_pet`）/ exception `dl-sd-op`（`guide_dog`）、
`ORDINARY_PET_SUBJECTS` 不含 service 角色（ADR-025）、
resolver 结果 `UNKNOWN` vs `/rules/evaluate` 结果 `MATCH` 的矛盾、
三个后续模型（OPTION 1/2/3）与关闭条件，以及同一缺陷族的另外 4 条规则。

**本轮未修改 Resolver，未扩宽 `ordinary_pet`，未让例外跳过 base 适用性判断。**

---

## 9. 正式执行命令（**仅生成，未执行**）

正式入口是 `scripts/publish_reviewed_r1.py`（不是 `publish_batch.py`；
后者是清单校验模块，由前者调用）。

### PowerShell

```powershell
$token = (Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8010/api/v1/auth/login" `
  -Body (@{email="admin@demo-petaccess.com"; password="admin12345"} | ConvertTo-Json) `
  -ContentType "application/json").access_token

.venv\Scripts\python.exe scripts\publish_reviewed_r1.py `
  --execute `
  --batch-file docs/governance/publish_batches/R2_FINAL_R3_BATCH_01A.json `
  --max-approve 10 `
  --reviewer huangdi97 `
  --registry docs/reality_audit/review_decisions_r2_final.json `
  --database-name petaccess `
  --token "$token" `
  --snapshot-out artifacts/PUBLISHED_RULES_SNAPSHOT_BATCH_01A.json
```

### Git Bash / sh

```bash
TOKEN=$(.venv/Scripts/python.exe - <<'PY'
import httpx
print(httpx.post("http://127.0.0.1:8010/api/v1/auth/login",
                 json={"email":"admin@demo-petaccess.com","password":"admin12345"},
                 timeout=20.0, trust_env=False).json()["access_token"])
PY
)

.venv/Scripts/python.exe scripts/publish_reviewed_r1.py \
  --execute \
  --batch-file docs/governance/publish_batches/R2_FINAL_R3_BATCH_01A.json \
  --max-approve 10 \
  --reviewer huangdi97 \
  --registry docs/reality_audit/review_decisions_r2_final.json \
  --database-name petaccess \
  --token "$TOKEN" \
  --snapshot-out artifacts/PUBLISHED_RULES_SNAPSHOT_BATCH_01A.json
```

四个必要条件齐备：`--execute` + `--batch-file` + `--max-approve` + `--reviewer`。
缺 `--reviewer` 时执行态会因署名不一致被拒；缺 `--batch-file` 时裸 `--execute` 直接被拒。

执行前提：API 在 8010 且指向同一个库（闸门与 API 必须看同一个库，否则 preflight 跨库校验不成立）。

---

## 10. 停止点

达到 `FIRST_REAL_PUBLISH_BATCH_01A_GATE = PASS_WITH_LIMITATIONS` 后**停止**。

已交付：manifest、dry-run、rehearsal、resolver 结果、rollback / supersession / watch、
最终命令、本报告。

**等待人类明确授权后才会对正式目标库执行 `--execute`。**

另按 §22：即使本批通过，**整体 Public Beta readiness 不因本批通过而自动 PASS**
（迪士尼语义问题仍 OPEN，且 carve-out 可达性存在限制）。

---

## 11. 证据索引

| 文件 | 内容 |
| --- | --- |
| `docs/governance/publish_batches/R2_FINAL_R3_BATCH_01A.json` | Batch 01A 清单（10 条） |
| `docs/governance/publish_batches/R2_FINAL_R3_BATCH_01.json` | Batch 01 清单（12 条），保留为历史 |
| `docs/governance/DISNEY_SCOPE_EXCEPTION_SEMANTIC_ISSUE.md` | Disney 语义 open issue |
| `artifacts/batch01a_dryrun.json` / `.txt` | 真实 gate 的 dry-run（10/10 PASS） |
| `artifacts/batch01a/rehearsal_db_fingerprint.json` | 克隆源与指纹 |
| `artifacts/batch01a/rehearsal_execute_r3.json` / `_receipt.json` | 首次执行（5 AccessRule + 5 RuleException） |
| `artifacts/batch01a/rehearsal_idempotency_run2.txt` / `_receipt.json` | 幂等复跑（NOOP=10） |
| `artifacts/batch01a/publish_rehearsal_r3_verification.json` | §13–§20 全部演练与可达性度量 |
| `artifacts/batch01a/a11y.json` / `a11y_run2.json` | a11y 两次实测 |
| `artifacts/publish_rehearsal_r3_verification.json` | 上一轮 BATCH-01：迪士尼失败原文 |

### 本轮为支持 Batch 01A 所做的工具改动

| 文件 | 改动 |
| --- | --- |
| `scripts/verify_publish_r3.py` | 新增 `--batch-file`；审计期望（transition/publish/publish_exception）与 resolver 期望矩阵改为**从清单派生**；只对本批发布规则涉及的场所做 grade（迪士尼不再计入本批 gate）；新增 `CARVE_OUT_REACHABILITY` 度量 |
| `scripts/rehearsal_r3_runbook.sh` | 新增 `MAX_APPROVE` 环境变量（`--max-approve` 必须 ≥ 清单大小），并把 `--batch-file` 传给验证脚本 |

两处都是**参数化**，未放宽任何拒绝条件：清单校验的四类拒绝、发布闸门的 preflight、
`--execute` 必须有 `--batch-file` 等规则均未改动。
