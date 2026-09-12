# REAL_DATA_PILOT_STATE.md

> PART B（EVIDENCE-FIRST REAL DATA AUTONOMOUS PILOT）实时状态。
> 前置条件：PART A Quality Gate 全 PASS（见 `ENGINEERING_QUALITY_ACCEPTANCE.md`）。

## 状态

| 项 | 值 |
|---|---|
| PART A 状态 | IN_PROGRESS（见 ENGINEERING_QUALITY_ACCEPTANCE.md） |
| PART B 状态 | **NOT_STARTED — Quality Gate 未通过前禁止采集真实数据** |
| Pilot 区域 | 未定（要求：中国城市、官方公开数据丰富、证据可核验；确定后在报告写明依据） |
| 已建真实 Place 数 | 0 / 10 |
| real_place_claims（provenance manifest） | 0（保持，直到有合法真实素材入库） |

## Pilot 组成要求（B8）

3+ 餐饮/咖啡 · 2 商场 · 2 公园 · 1 酒店 · 1 景区/公共空间 · 1 其他；
≥3 source_type · ≥2 Zone · ≥2 conditional · ≥1 prohibited · ≥1 unknown ·
≥1 RuleCandidate · ≥1 ObservationCandidate · 全部候选有证据链。

## 候选台账（随采集实时更新）

| # | Place | 类型 | Zone | 来源(Tier/type) | 通道 | 候选状态 | 证据完整度 |
|---|---|---|---|---|---|---|---|
| （空） | | | | | | | |

## KPI（B14）

| KPI | 值 |
|---|---|
| Places discovered | 0 |
| Answerable Place Rate | — |
| RuleCandidate count | 0 |
| ObservationCandidate count | 0 |
| Evidence Completeness | — |
| Official/operator source ratio | — |
| Candidate approval rate | 0%（无人工审核，第一轮全部留待 Review Gate） |
| Attribution error | — |
| Schema gap rate | — |
| Stale rate | — |
| Conflict rate | — |
| Source change latency | — |

## 停止条件（B15，任一触发立即停）

Schema Gap > 20% · attribution error > 5% · evidence incomplete > 10% ·
AI major extraction error > 5% · unauthorized source usage · merge/duplicate instability。
