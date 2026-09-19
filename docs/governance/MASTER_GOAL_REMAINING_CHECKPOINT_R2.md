# Master Goal 剩余闭环 · 检查点 R2（四项决定落地后）

> 上一版是 `MASTER_GOAL_REMAINING_CHECKPOINT_R1.md`（4 个待决事项）。
> 那 4 项已由 `huangdi97` 于 2026-09-19 全部裁决，本文件取代它。
> 执行与证据见 `ROUND6_DISPOSITION_AND_CENTURY_PARK_EXECUTION_REPORT.md`。

## 0. 四项决定的处置结果

| # | 项目 | 裁决 | 落地状态 |
|---|---|---|---|
| 1 | `SHANGHAI_ZOO_DOG` | 保持 `HOLD`，原因不变，禁用 JPROV-001 跨层放宽 | ✅ 一字未动（sha256 `ce97d75e…`，生产 dog 规则 = 0） |
| 2 | `CENTURY_PARK_4e217d58` | 接受政府来源，必须标 `government_service`，禁称一手，`FIRST_PARTY_OPERATOR_SOURCE_PENDING = YES`，不再作为 blocker | ✅ Gate 重跑 PASS，safe batch 已生成，**dry-run PASS，等发布授权** |
| 3 | `WAVE01 REMAINING APPROVED` | 禁止整批重跑；先做处置审计，分三类 | ✅ 旧 planning artifact 已作废 + 加载即拒 + planner 永久拒绝；新批次已立 |
| 4 | `LEGAL_PROVISION_MODEL` | 独立 additive track，`MUTATE_EXISTING_PUBLISHED_ROWS = NO` | ✅ ADR-032 + schema 草案；未生成 migration，未动一行历史数据 |

执行顺序 A–H 全部走完（A→B→C→D→E→F→G→H），未自动启动 Wave02，未执行任何生产写。

---

## 1. 唯一待决：世纪公园批次的真实发布授权

```
批次      = EXP-R1-W01-REVIEW-R1-BATCH-03-CENTURY-PARK
内容      = 1 条 · w01-4e217d5810（世纪公园 / ordinary_pet / OPERATOR_POLICY / prohibition）
计划动作  = CREATE_ACCESS_RULE（supersedes = []，不覆盖任何现行规则）
Dry-run   = PASS（exit 0）· BATCH_VALIDATION = PASS · DRY_RUN_ZERO_DB_MUTATION = PASS
执行需要  = --execute --batch-file <上> --reviewer huangdi97 --production-confirm
            --evidence-acceptance docs/governance/evidence_acceptance/CENTURY_PARK_EVIDENCE_ACCEPTANCE_R1.json
```

**授权前请看清楚的三件事**（不是警告，是这次决定的边界条件）：

1. **这不是证据升级。** `evidence_strength` 仍会是 `search_snippet`。改变的是"有署名人类接受"，不是"证据变一手"。
2. **两个缺口同时入档**：不得把 `source_type` 标成 `official_operator_policy`；不得声称 `operator first-party verified`。机器上已做硬拒绝（四个反事实全部 REFUSED）。
3. **Propagate 未铺**：`FIRST_PARTY_OPERATOR_SOURCE_PENDING = YES` 目前记录在治理文件里；若要同步进 `source.notes`（库的 canonical metadata），需要一次生产写 —— **这一条也在等授权**，可以和发布一起批，也可以单独批。

若决定不发布，用户可见结果是：世纪公园依然没有 `ordinary_pet` 规则 ⇒ **UNKNOWN**（不是 ALLOWED）。这是正确行为，不需要补位。

---

## 2. 已关闭的事项

| 事项 | 上一版状态 | 现在 |
|---|---|---|
| Wave01 旧整批能否重跑 | 存在 SUPERSEDE 新规则的风险 | **不可能** —— 3 个 planning artifact 作废（加载即拒）+ `superseded_semantics.json` 让新清单也拒绝同一批 id |
| Wave01 剩余 APPROVED 几类 | 未分 | **A=3 / B=1 / C=0**（另有 11 条 ALREADY_PUBLISHED 单列） |
| B5 Place 坐标 | 20/20 已有坐标，2 条待门牌 | 降级为 `PUBLIC_BETA_REAL_MAP_DATA_QUALITY_ITEM`，**不阻挡规则治理** |
| 法条级引用列 | 需要触碰历史行的新项目 | 升级为独立 track：**ADR-032**，`MUTATE_EXISTING_PUBLISHED_ROWS = NO`，非 Public Beta blocker |

---

## 3. 之后的决策点（本动作获授权之前不要动）

按决定人的 H：「上述完成后，输出新的 CURRENT STATE，再决定启动 Wave02。」若启动，建议的前置条件：

1. 世纪公园批次要么已发布、要么明确关闭（不留"半开"的发布意图）；
2. Wave-01 的 31 行登记表作为**已完结的一轮**归档，不再重跑；
3. LegalProvision 的新数据路径至少要有 `native_publish` 的写链路，否则新场次会继续累积无 provision 血缘的规则 —— 这条不是 Beta blocker，但越晚做回填面越大。

---

## 4. 现状快照（生产 `petaccess`，只读实读）

```
access_rule             = 19
rule_candidate          = 75
rule_exception          = 6
jurisdiction_exception  = 1    （JPROV-001, applies_to_layer=LEGAL）
place                   = 20   （缺坐标 = 0）
source_monitor          = 13
本轮实际写入            = 0
```

```
HUMAN_ACTION_REQUIRED = REAL_PUBLISH_AUTHORIZATION_FOR_CENTURY_PARK_BATCH
```
