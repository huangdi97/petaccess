# WAVE02_PREPUBLISH_REPORT — signature + real pre-publish gate + dry-run

- 授权：huangdi97 明确接受建议（对话决定），对应 §5「Human Decision 之后的 Rule Track」
- revision：`EXP-R1-W02-REVIEW-R1`
- expansion_run_id：`EXP-R1-W02-20260919`
- reviewer：`huangdi97`
- 执行时间：2026-09-21（本会话实测；ISO-8601 见登记表 `decided_at`）
- 阶段性质：**签名 + 真实预发布评估 + publishability 判定 + safe batch manifest + dry-run**。**未执行真实发布。**

## 1. §5.1–5.3 Review Register freeze / diff / immutability

| 断言 | 结果 |
|---|---|
| 签名 revision 匹配 | `EXP-R1-W02-REVIEW-R1` ✅ |
| expansion_run_id 匹配 | `EXP-R1-W02-20260919` ✅ |
| rows = 20 | 20 ✅ |
| 既有签名覆盖 | 0（写入前 20/20 空；无覆盖）✅ |
| 写入后 total | 20 行全部 `final_decision` 非空 ✅ |
| final_decision 分布 | APPROVED 16 / HOLD 4 / REJECTED 0 / APPROVED_WITH_NOTE 0 ✅ |
| reviewer | `huangdi97`（唯一）✅ |
| decided_at | 时区感知 ISO-8601（2026-09-21T12:12:09.577578Z）✅ |
| HOLD 行 | `81eca767`（辰山，OFFICIAL_PAGE_VERBATIM_VERIFICATION_REQUIRED）/ `36f6382f`、`b6abed36`、`c6c5b74d`（顾村，SECONDARY_SOURCE_NEEDS_FIRST_PARTY_CONFIRMATION）✅ |
| 冻结字段（place/scope/effect/layer/normalization） | diff 仅含 final_decision/reviewer/decided_at/decision_note，其余字节级不变 ✅ |
| 历史 Human Decision 修改 | 无（Wave01 / Scope-R2 / R2-FINAL 均未触碰）✅ |
| AccessRule / RuleException 数量 | 26 / 9 未变 ✅ |

写入器：`scripts/expansion_w02_sign_review.py`（镜像 Wave01 的 `expansion_w01_sign_review.py`：稳定 candidate_id 键控 + anchor 硬断言 + no-overwrite + revision/rowcount 门禁）。

## 2. §5.4 Real pre-publish evaluation（真实 gate，非复述）

`uv run python scripts/wave02_prepublish_dryrun.py`（真实 `publish_gate.evaluate_for_publish`，live session，只读）：

```
signed rows       : 20
APPROVED          : 16
HOLD              : 4        → 不进入批次（HOLD_NOT_PUBLISHABLE）
REJECTED          : 0
gate distribution : {'PASS': 16, 'BLOCKED': 0, 'NOT_RUN': 0}
proposed batch    : 16 candidates (PASS only)
ZERO_DB_MUTATION  : True (nothing written)
```

逐条 PASS（16/16）：世博 ×3（dog/cat/other）、植物园 ×3、自然博物馆、野生动物园、共青 ×3、和平 ×2、昆山、豫园 base、豫园 guide-dog carve-out。

> 与 Wave01 语义一致：`rule_id` 前缀不存在于 Wave02 登记表（Wave02 用 UUID candidate_id 键控），故由独立 dry-run 工具消费同一份已签登记表并调用同一 canonical gate；不擅自改写 Wave01 发布器。

## 3. §5.5 Publishability disposition

| 判定类别 | 数量 | 说明 |
|---|---|---|
| WRITE（AccessRule 计划） | 16 | gate PASS 且人类 APPROVED |
| NOOP | 0 | — |
| HOLD_NOT_PUBLISHABLE | 4 | 辰山 + 顾村 ×3（来源核验缺口；登记表 HOLD） |
| REJECTED_NOT_PUBLISHABLE | 0 | — |
| SUPERSEDED_NON_EXECUTABLE | 0 | 无跨轮 supersede 关系冲突 |

详见 `WAVE02_PUBLISHABILITY_DISPOSITION.md`。

## 4. §5.6–5.10 Scope / supersede / exception / layer / dependency

- §29 gates（本轮已实测重跑，见 V09 审计 §5.4）：SOURCE_SCOPE / ZONE / EXCEPTION_REACHABILITY / ADR030 / ADR031 / EVIDENCE / FRESHNESS / LICENSE / CONFLICT / SUPERSESSION / GUIDE_DOG_SAFETY / CONDITION_SCHEMA 全部 PASS ×20。
- batch dependency closure：豫园 base（5f22e9a1）先于 guide-dog carve-out（91970069）执行（base-before-exception 顺序）；其余无跨行依赖。`BATCH_DEPENDENCY_CLOSED = PASS`。
- cross-layer：豫园 carve-out 与 base 同层（OPERATOR_POLICY），无跨层放宽。
- superseded semantics：Wave02 不做 supersede；不触碰 `superseded_semantics.json` 中任何 Wave01/Scope-R2 已退役行。
- obsolete manifest：`WAVE02_SAFE_BATCH_MANIFESTS/EXP_R1_W02_REVIEW_R1_BATCH_01.json` 声明 `execution_status: PROPOSED_DRY_RUN_ONLY`，不含任何旧语义基底；加载校验见 §6。

## 5. §5.11 Evidence / License / Freshness gates

| gate | 判定 |
|---|---|
| Evidence（bundle/quote/hash 可溯） | PASS ×16（真实 evaluate_for_publish 覆盖） |
| License（lead-only 不可发布） | PASS ×16（顾村/辰山 secondary 不在此批次） |
| Freshness（last_verified / review_due） | PASS ×16 |

## 6. §5.12 Safe batch manifest + dry-run

- Manifest：`docs/expansion/WAVE02_SAFE_BATCH_MANIFESTS/EXP_R1_W02_REVIEW_R1_BATCH_01.json`
  - batch_id：`EXP-R1-W02-REVIEW-R1-BATCH-01`
  - candidate_ids：16（与已签登记表 APPROVED 行一一对应）
  - execution_status：`PROPOSED_DRY_RUN_ONLY`（**无真实发布授权**）
- load/validate：manifest 经 `publish_batch.py` 兼容结构生成（revision/batch_id/reviewer/candidate_ids），执行状态不声明可执行；aria 语义扫描无 supersede 冲突项。
- **DRY-RUN ONLY**：已通过 `wave02_prepublish_dryrun.py` 完成（真实 planner = gate 全量评估、dependency 闭合、scope semantics、exception reachability；`ZERO_DB_MUTATION = True`）。未运行真实 execute。

## 7. 结论指标

```
HUMAN_SIGNATURE            = PASS (huangdi97, 16/4/0)
PREPUBLISH_PASS            = 16
PREPUBLISH_BLOCKED         = 0
HOLD_PUBLISHABLE           = 0
REJECTED_PUBLISHABLE       = 0
CROSS_LAYER_EXCEPTION      = 0
INERT_EXCEPTION            = 0
UNRESOLVED_SUPERSESSION    = 0
DRY_RUN_ZERO_DB_MUTATION   = PASS
REAL_PUBLISH_EXECUTED      = NO
HUMAN_ACTION_REQUIRED      = WAVE02_REAL_PUBLISH_AUTHORIZATION
```