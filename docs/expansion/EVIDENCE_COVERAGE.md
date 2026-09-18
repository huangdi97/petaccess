# EVIDENCE_COVERAGE — 证据链覆盖与可追溯性

- expansion_run_id: `EXP-R1-W01-20260918`
- review_revision: `EXP-R1-W01-REVIEW-R1`
- generated_at: 2026-09-18T03:43:17.580156+00:00
- 生成方式：由 `scripts/expansion_w01_reports.py` 从生产库与运行清单派生，非手写

## 1. 链路形态

`DataSourceJob → Source → SourceArtifact → EvidenceBundle → RuleCandidate → Review → Publish`

Collector 绝不直接产出 AccessRule。

## 2. 覆盖

| 指标 | 值 |
|---|---|
| Wave01 候选 | 31 |
| 候选携带 evidence_bundle | 31 |
| 无 bundle 的候选（必须为 0） | 0 |
| Wave01 artifact | 14 |
| Wave01 bundle | 21 |
| 有 content_hash 的 artifact | 14 |

## 3. 原始证据与派生证据分离（§14）

- **ORIGINAL**：SourceArtifact（页面快照 + content_hash + 摘录）
- **DERIVED**：EvidenceBundle（quoted_text 逐字引用 + extracted_json 结构化抽取）

抽取不改变原文：bundle 保留逐字引文，结构化字段另存，两者可对照复核。

## 4. 抽取方式标注

| extraction_method | 候选数 |
|---|---|
| agent_assisted_extraction_2026_09_18 | 31 |

抽取方式被显式记录，使「这条候选是机器辅助抽取的」可审计，而不是混在人工录入里。

## 5. 可回答性（§27）

| 判定 | 含义 |
|---|---|
| ANSWERABLE | 有已发布规则可回答 |
| PARTIALLY_ANSWERABLE | 仅部分 Zone/情形有依据 |
| UNKNOWN | 无依据，附 reason code，不推断 |

本轮 31 条候选全部处于「待人工审核」，尚未进入 ANSWERABLE 状态。
