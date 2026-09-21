# WAVE02_REAL_PUBLISH_AUTHORIZATION_PACKET

- 轮次：`30_50_PLACE_EXPANSION_R1 — WAVE_02` · revision：`EXP-R1-W02-REVIEW-R1`
- expansion_run_id：`EXP-R1-W02-20260919` · reviewer：`huangdi97`
- 本包目的：在 **REAL PUBLISH 授权检查点** 向 `huangdi97` 呈报全部材料。**未获明确授权前不执行任何真实发布。**

## 1. 材料清单（本包 = 指向以下产物的索引）

| 材料 | 路径 | 说明 |
|---|---|---|
| 本轮 Phase 0 全量审计 | `docs/status/V09_CURRENT_REALITY_AUDIT.md` | HEAD/worktree/DB/26 规则/20 候选/测试/完整性 |
| 二十条候选 AI 审核与签署建议 | `docs/expansion/WAVE02_REVIEW_RECOMMENDATIONS.md` | 逐条 22 维审核 + 10 列可签署表 |
| 已签决策登记表 | `docs/expansion/review_decisions_expansion_r1_wave02.json` | final_decision=16 APPROVED / 4 HOLD；reviewer=huangdi97；decided_at=2026-09-21T12:12:09.577578Z |
| 签名写入器 | `scripts/expansion_w02_sign_review.py` | 稳定 candidate_id 键控、no-overwrite、anchor 硬断言 |
| 预发布报告 | `docs/expansion/WAVE02_PREPUBLISH_REPORT.md` | 签名 freeze + 真实 gate + manifest + dry-run |
| Publishability 判定 | `docs/expansion/WAVE02_PUBLISHABILITY_DISPOSITION.md` | 16 可发布 / 4 HOLD 明细 |
| Safe batch manifest | `docs/expansion/WAVE02_SAFE_BATCH_MANIFESTS/EXP_R1_W02_REVIEW_R1_BATCH_01.json` | 16 候选，`PROPOSED_DRY_RUN_ONLY` |
| 预发布评估 dry-run 输出 | `scripts/wave02_prepublish_dryrun.py`（本会话已跑；报告存于会话 scratch） | 真实 gate、ZERO DB MUTATION |

## 2. 人类决定（已落盘，不可再改）

- **APPROVED 16 条**（过真实 pre-publish gate 全部 PASS）：
  上海世博文化公园 ×3、上海植物园 ×3、上海自然博物馆、上海野生动物园、共青森林公园 ×3、和平公园 ×2、昆山公园、豫园 ×2（含导盲犬 carve-out）。
- **HOLD 4 条**（来源核验缺口，不发布）：上海辰山植物园（官网逐字核验）、顾村公园 ×3（二级来源转一手）。

## 3. 请求授权的批次（仅此一个 batch）

```
batch_id           = EXP-R1-W02-REVIEW-R1-BATCH-01
candidate_ids      = 16（见 disposition §2）
execution_status   = PROPOSED_DRY_RUN_ONLY  → 授权后由发布器重估并置可执行
dependency_closure = PASS（豫园 base 先于 carve-out）
cross_layer        = 0（carve-out 与 base 同层 OPERATOR_POLICY）
```

## 4. 真实发布时将执行的核查（§6 步骤，当前**未执行**）

- production role verify → snapshot → exact manifest verify → freshness verify → real execute（含 Evidence/Source/Audit linkage）→ post snapshot → resolver verification → second execute（期望 NOOP）。
- 检查项：HOLD published=0、REJECTED published=0、excluded approved published=0、inert exception=0、cross-layer exception=0、obsolete semantic execution=0、UNKNOWN auto-allowed=0、unexpected mutation=0、CRITICAL=0、HIGH=0。

## 5. HOLD 续期路径（授权发布不需处理，但记入本包）

- 辰山：核验 `https://www.csnbgsh.cn/sites/chenshan2020/static/zhinan.ashx` 原页逐字后转 APPROVED。
- 顾村 ×3：核实圃方一手来源（官网/公众号）后转 APPROVED。

## 6. 授权入口（请 huangdi97 回复其一）

- **A. 授权批次 01 真实发布**：回复明确的 `REAL_PUBLISH_AUTHORIZATION = YES (batch EXP-R1-W02-REVIEW-R1-BATCH-01)`。
- **B. 不授权**：保持停止；或在回复中给出修改/抽取子集 / 暂停项。

> **未获 A 之前，任何真实写库、candidate transition 到 PUBLISHED、access_rule 插入、supersede、audit 发布记录都不会发生。**

---

```
HUMAN_ACTION_REQUIRED = WAVE02_REAL_PUBLISH_AUTHORIZATION
```