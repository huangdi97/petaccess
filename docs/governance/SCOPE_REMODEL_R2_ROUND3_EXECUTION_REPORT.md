# SCOPE-REMODEL-R2 第三轮执行报告（授权：全部授权）

时间：2026-09-18（ Asia/Shanghai ）
执行者：buddy｜人类评审员：huangdi97
范围：① 真实发布 BATCH-02（4 条）② 给发布器加 selected-but-blocked 拒绝
③ 为迪士尼导盲犬 carve-out 建新候选 + 新审查

---

## ① 真实发布 SCOPE-REMODEL-R2-BATCH-02

```
REAL_PUBLISH_EXECUTED              = YES
BATCH_ID                           = SCOPE-REMODEL-R2-BATCH-02
SELECTED                           = 4   （迪士尼 cat / other、动物园 cat / other）
ACCESS_RULE_CREATE_COUNT           = 4
RULE_EXCEPTION_CREATE_COUNT        = 0
PREPUBLISH_EVALUATED / PASS / BLOCKED = 4 / 4 / 0
SELECTED_BUT_BLOCKED               = 0
CLI_PUBLISH_AUDIT_CONTRACT         = PASS（checked=4 missing=0）
幂等复跑                            = NOOP 4 / CREATE 0
```

| 表 | 前 | 后 | delta |
|---|---|---|---|
| access_rule | 14 | 18 | **+4** |
| rule_exception | 5 | 5 | 0 |
| jurisdiction_exception | 1 | 1 | 0 |
| rule_candidate | 74 | 74 | 0（4 条转 PUBLISHED） |
| audit_log | 9652 | 9660 | +8 |

- 生产指纹 `569d3bb6…` → `80f62e0f…`（仅新增 4 条规则与其审计）。
- 证据/来源/审计核验 `verify_scope_r2_publish.py --db-name petaccess`：**VERIFY = PASS**
  —— 4 条各有 original 证据包、`source_scope_exact` 逐字保留、audit 12 行全在词表内。
- 解析器对照（生产 vs 演练库）：`changed_cells = 0`。
  猫 / 其他宠物 = `prohibited`；**普通犬与导盲犬仍为 `unknown`**（没有任何错误禁止）。
- 完整性闸门：CRITICAL 0 / HIGH 0 / MEDIUM 1（`AUDIT_TARGET_ID_UNUSABLE` 2647 行，历史项，未变）。

**未发布、决策未被推翻的**：迪士尼 dog（APPROVED，受制于下方 carve-out）、
动物园 dog（HOLD）。收窄批次 ≠ 推翻决定。

---

## ② 发布器缺口修复：selected-but-blocked ⇒ refuse

**缺陷**：`build_plan` 把被闸门 BLOCK 的步骤标 `BLOCKED` 后跳过，`execute_plan` 也不计入
`failed`。于是「base 在批内 + 例外被 BLOCK」的清单会 `BATCH_VALIDATION = PASS`
却发布出不完整状态 —— 上一轮在演练库实测到导盲犬 = `prohibited`。

**修复**（`scripts/publish_reviewed_r1.py`，commit `dd3224f`）：

- 新增 `selected_but_blocked(plan)`：凡 `publication_type == BLOCKED` 的步骤都列出
  （HOLD / REJECTED / NOOP 是有意不发布，不计入）；
- `plan_integrity` 增加 `SELECTED_BUT_BLOCKED`（含 `details.selected_but_blocked`）；
- `render_plan` 打印该计数；
- `--execute` 非零即 `REFUSED`（退出码 4），`--dry-run` 退出码 3。

**反事实验证**（生产库只读 dry-run，6 条原意清单的等价副本）：

```
PREPUBLISH_PASS = 5   PREPUBLISH_BLOCKED = 1
ACCESS_RULE_CREATE_COUNT = 5   RULE_EXCEPTION_CREATE_COUNT = 0
BLOCKED_COUNT = 1     SELECTED_BUT_BLOCKED = 1   ← 修复前会执行、修复后拒绝
EXIT = 3
```

新增 4 条回归测试（`tests/unit/test_publish_plan.py`），含一条把这个 bug 的现场
写成命名的测试：`test_a_blocked_carve_out_makes_its_whole_batch_unexecutable`。
发布器相关单测 94 passed；ruff PASS。

> `docs/governance/publish_batches/SCOPE_REMODEL_R2_BATCH_01_BLOCKED.json` 保留为证据，
> 内含 `_BLOCKED_DO_NOT_EXECUTE` 标记（清单校验会因未知字段直接拒绝）。

---

## ③ 迪士尼导盲犬 carve-out：新候选 + 新审查

| 项 | 值 |
|---|---|
| 新候选 | `69e0916a-2f13-4b1e-b601-f8731e6869d1`（`sr2-69e0916a2f`），`REVIEW_PENDING` |
| 克隆自 | `305fa08c-1edd-4cc9-9b7e-554647e44b0a`（已签署、被闸门 BLOCKED） |
| 唯一改动 | 条件键 `type` → `condition_type`，走 `normalize_conditions`（canonical ingest 边界） |
| 冻结原候选 | **未改动**（行 sha256 `94cea72f…` 前后一致） |
| 发布器闸门 · 原候选 | BLOCKED（`schema_unsupported`） |
| 发布器闸门 · 新候选 | **PASS** |
| 可达性 | `guide_dog` on `dog` base = **True** |
| 生产 delta | `rule_candidate` 74 → 75，`audit_log` +2，其余表 0 |
| 指纹 | `80f62e0f…` → `2fafa05a…` |
| 审查表 | `docs/expansion/review_decisions_scope_remodel_r2_carveout.json`（1 行，全 null） |
| 审查包 | `docs/expansion/SCOPE_REMODEL_R2_CARVEOUT_HUMAN_REVIEW_PACKET.md` |

配套脚本：

- `scripts/scope_remodel_r2_carveout_candidate.py`（`--plan/--apply/--verify/--register`）；
- `scripts/scope_remodel_r2_carveout_publish_register.py` —— 签名后把「迪士尼 dog 基底 +
  新但书」投影进同一张可发布登记表（跨文件依赖对批次校验不可见）。未签名时实测 `REFUSED`
  （退出码 4）。

> 已知：admin create 端点不持久化 `projection_of_rule_id`（不在请求 schema 上），
> 克隆血缘因此记录在 `raw_text`。6 条 SCOPE-R2 基底候选同样是 `None`。记入 PITFALLS。

---

## 停点

```
REAL_PUBLISH_EXECUTED                  = YES（仅 BATCH-02 的 4 条）
DISNEY_DOG_PUBLISHED                   = NO
SHANGHAI_ZOO_DOG_PUBLISHED             = NO（HOLD，publishable = 0）
UNMODELED_SOURCE_SCOPE_REMAINDER       = YES（鸟类/爬行类等仍 UNKNOWN，不得读作 ALLOWED）
CROSS_LAYER_EXCEPTION                  = 0
INERT_EXCEPTION                        = 0
HUMAN_ACTION_REQUIRED                  = SCOPE_REMODEL_R2_CARVEOUT_FINAL_DECISION
```

签完那一行后，剩余动作仍是：投影 → 批次清单 → 演练库真执行 → 解析器实测 → 生产授权。
