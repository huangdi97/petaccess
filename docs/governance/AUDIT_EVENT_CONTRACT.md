# 审计事件契约（AUDIT_EVENT_CONTRACT）

> 唯一权威：`services/api/app/core/audit_events.py`。
> 轮次：`PRODUCTION_INTEGRITY_LIMITATION_FINAL_CLOSURE`（L4）。
> 目的：让「HTTP 写一个事件名、CLI 写另一个」不再可能发生。

---

## 1. 为什么会需要这份文件

Batch-01B 真实发布了 3 条 `RuleException`。发布当时，这 3 条**没有任何发布审计**——
既没有 `candidate.publish_exception`，也没有 `rule_exception.create`。
治理血缘其实存在（`candidate.transition` 有），但 `verify_publish_r3.py` 的
`AUDIT_LINKAGE` 要求更严格，于是检查失败。

这不是「校验器太严」。缺的那一类事件，正是把「谁批准」和「谁执行」联系起来的那一段：
登记表上有 reviewer，审计里有 actor，两者之间如果没有一条显式记录，
追溯就只能靠时间戳猜。

根因是**事件名散落在代码里的字符串字面量**：

| 写入方 | 之前写什么 |
|---|---|
| HTTP `POST /rule-exceptions` | `candidate.publish_exception` |
| CLI `scripts/publish_reviewed_r1.py` | 只有 `candidate.transition` |

同一个动作两个名字，且没有任何一处声明过「这两个应该一致」。

---

## 2. 契约

1. **唯一词表**。`AuditEvent` 枚举是全部合法事件名的唯一来源。
   `canonical_events()` 返回完整清单，`is_canonical(name)` 判定合法性。
2. **禁止字面量**。写入方必须引用常量，不能直接写字符串。
   由 `tests/unit/test_audit_event_contract.py::test_no_literal_audit_actions_in_routes` 强制。
3. **发布事件三者齐备**，且发布器与校验器读同一份常量
   （`PUBLISH_AUDIT_REQUIRED`，由 `test_publish_audit_required_is_the_verifier_vocabulary` 强制）：

   | 事件 | 何时写 | 承载什么 |
   |---|---|---|
   | `candidate.transition` | 候选状态变化 | reviewer / 决策 |
   | `candidate.publish` | AccessRule 发布 | rule_id、reviewer、batch_id |
   | `candidate.publish_exception` | RuleException 发布 | exception_id、**base_rule_id**、reviewer、batch_id |

   `RuleException` 的发布审计**必须带 `base_rule_id`**：例外脱离了它依附的 base 就没有意义，
   只记 exception_id 等于记了半个事实。
4. **执行者与人分开**。`actor_user_id` / `actor_role` 是执行者；
   `detail.reviewer` 是人类复核署名。二者不可互相顶替。
5. **target_id 必须指向真实对象**。`record_audit` 对 `"None"` / 空值直接抛错。
   详见 §5。

---

## 3. CLI 发布器现在做什么

`scripts/publish_reviewed_r1.py` 在 execute 之后、返回之前做一次
`CLI_PUBLISH_AUDIT_CONTRACT` 自检：本批每一个已发布的候选，
是否都有对应的 canonical 发布审计（AccessRule → `candidate.publish`，
RuleException → `candidate.publish_exception`）。

缺失即 `FAIL` 并列出 `missing`。这不是为了给谁看绿字，
而是让「发布了却没留下痕迹」在同一次运行里就暴露出来，而不是等下一轮扫描。

---

## 4. Batch-01B 的历史回填（§16–17）

已发布的东西不能靠重跑发布来补审计——那会制造假事件。
回填规则：

- **范围严格限定**：仅 `R2-FINAL-R3-BATCH-01B` 的 3 条 carve-out。
  判定依据是登记表里的 `carve_out_of` 字段（确定性来源），不是按数组顺序猜。
- **只追加，不改写**：新增 `candidate.publish_exception` 行，既有审计一行未动。
- **必须自我标注**：

  | 字段 | 值 |
  |---|---|
  | `detail.backfilled` | `true` |
  | `detail.reason` | `CLI_AUDIT_EVENT_CONTRACT_RECONCILIATION` |
  | `detail.original_publish_at` | 原始发布时刻（从 `candidate.transition` 读取） |
  | `detail.rule_exception_id` / `base_rule_id` / `batch_id` | 对象身份 |
  | `created_at` | **回填当时时刻**（`now()`），不伪造原始时间 |

- **不批量猜测更老的历史**：没有确定性来源的部分只报告，不回填（§17）。

回执：`artifacts/integrity_final_closure/AUDIT_BACKFILL_RECEIPT.json`
（`backfill_count = 3`，`inserted = 3`）。

---

## 5. `target_id = "None"` 缺陷

完整性扫描报出 `AUDIT_TARGET_ID_UNUSABLE = 2647 行 / 4 组`
（`place` 1185、`source` 1379、`jurisdiction_rule` 68、`zone` 15）。

- **根因**：ORM 对象 `db.add()` 之后未 `flush()`，主键尚不存在，
  `str(obj.id)` 得到字符串 `"None"`，被写进 `audit_log.target_id`。
- **性质**：这是**活跃缺陷**，不是纯历史遗留——修复前的代码路径今天仍会产出同样的问题行。
- **已修**：
  1. 13 处 `record_audit` 调用点补 `db.flush()`（`places` / `sources` / `rules` /
     `regulations` / `disputes` / `operators` / `v05`）；
  2. `record_audit` 增加写入时断言，`"None"` / 空值直接 `ValueError`——
     在还能拿到对象的那一刻失败，而不是等下一轮扫描才发现；
  3. 静态回归锁（`test_audit_target_id_is_never_the_string_none`）+
     运行时断言测试（`test_record_audit_refuses_an_unusable_target_id`）。
- **历史行不回填**：没有任何确定性来源能还原那 2647 行本该指向哪个对象，
  按 §17 只保留并解释，不猜。

最后一条 `"None"` 行产生于 2026-09-17 07:40（早于本轮修复）；
修复之后无新增。

---

## 6. 复跑

```bash
export PATH="/c/Program Files/Git/cmd:/c/Program Files/Git/mingw64/bin:/usr/bin:/bin:$PATH"
cd "E:/AI/宠物管理"

# 契约与回填
PYTHONPATH= .venv/Scripts/python.exe -m pytest tests/unit/test_audit_event_contract.py -q

# 发布器自检（含 CLI_PUBLISH_AUDIT_CONTRACT）
PYTHONPATH= .venv/Scripts/python.exe scripts/publish_reviewed_r1.py \
  --execute --batch-file docs/governance/publish_batches/R2_FINAL_R3_BATCH_01B.json \
  --max-approve 8 --database-name <db> --reviewer huangdi97 --token <jwt>

# 血缘校验（AUDIT_LINKAGE 必须 PASS）
PYTHONPATH= .venv/Scripts/python.exe scripts/verify_publish_r3.py --db-name <db> \
  --batch-file docs/governance/publish_batches/R2_FINAL_R3_BATCH_01B.json
```
