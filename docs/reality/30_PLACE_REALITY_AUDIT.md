# 30_PLACE_REALITY_AUDIT.md — 2026-09-23 实测

> 审计方式：DB 实测（petaccess, PostgreSQL 17）+ artifact 复核。只允许状态词：PASS / PASS_WITH_LIMITATIONS / NOT_VERIFIED / BLOCKED_EXTERNAL / BLOCKED_HUMAN / FAIL。

## 0. 数据基线（DB 实测）
| 指标 | 值 |
|---|---|
| REAL_PLACES | 30（全部 lifecycle=active，全部有真实上海坐标 lat 31.04–31.34 / lon 121.18–121.72） |
| PLACE_TYPES | park 10 / scenic_area 5 / cafe 4 / mall 4 / museum 2 / hotel 2 / restaurant 1 / library 1 / square 1 |
| ZONES | 44 |
| RULES | 42 current（LEGAL 14 / OPERATOR_POLICY 28） |
| RULES_WITH_SOURCE | 42/42 = 100% |
| RULE_CANDIDATES | 95（51 已 publish，95/95 有 evidence_bundle） |
| SOURCES | 36（official_operator_policy 16 / external_web_reference 13 / government_service 4 / statute_or_regulation 2 / ordinary_user 1） |
| SOURCE_MONITORS | 22（全部 active；21 个 next_check_at <= now() 到期未扫） |
| REALITY_CANDIDATES | 0 |
| OBSERVED_PRESENCE | 0 |
| STAFF_RESPONSE_OBSERVATION | 0 |
| ANIMAL_FACILITY | 0 |
| REALITY_REPORT / EFFORT / CONFIRMATION / EXTERNAL_REF | 0 |
| DATA_LICENSE | **0 行（表存在但无数据）** |
| RULE_EXCEPTIONS | 9 |

## 1. Reality-visible claim evidence coverage
- 目标 100%：**当前无可审计的 Reality-visible claim**（Reality 各表 = 0）。
- 结论：`PASS_WITH_LIMITATIONS` —— 因 0 claims 而空洞满足；实际含义是「尚无 Reality 数据，不能声称覆盖」，全部 30 Place 记为 **INSUFFICIENT_OBSERVATION**（未造数）。

## 2. 误推断检查（Observation → Rule 等）
| 检查 | 值 | 状态 |
|---|---|---|
| Observation→Rule false inference | 0（无 observation 数据） | PASS |
| StaffResponse→OperatorPolicy false inference | 0 | PASS |
| Facility→Policy false inference | 0 | PASS |
| Stale reality shown as recent | 0（无数据） | PASS |
| Staff personal identity leakage | 0（actor_role 模型，DB 无个人姓名列） | PASS |
| Parent-child misattribution (published claims) | 0（无 claims） | PASS |
| Publication time used as event time | 0（access_answer 强制 content_published_at ≠ observed_at；无数据） | PASS |
| Unresolved facility purpose shown as confirmed | 0（无 facility 数据） | PASS |
| Reality correction / dispute | NOT_VERIFIED（无 Reality claims 可纠错/争议） | NOT_VERIFIED |

> 注：以上「0」均为「无数据时的空洞零」，不是「有数据且核对通过」的零。母版要求的验收在 Phase 21 数据完成后才有实质意义。

## 3. 无 Reality 数据的 Place（30/30）
- 所有 30 Place：`reality_discovery_attempt = NOT_ATTEMPTED`、`observation_source_attempt = NOT_ATTEMPTED`、
  `staff_response_discovery_attempt = NOT_ATTEMPTED`、`animal_facility_audit = NOT_ATTEMPTED`、
  `reality_evidence_or_explicit_no_evidence = INSUFFICIENT_OBSERVATION`。
- **禁止造数**：本审计不发明任何现场/网上证据。Reality 数据必须来自真实贡献/核验（Phase 12 UX 就绪 + 人类核验）。
- 结论：`INSUFFICIENT_OBSERVATION`（30/30），诚实状态。

## 4. Rule Gate 复核（DB 实测）
| 门 | 值 | 状态 |
|---|---|---|
| Published Rule Evidence | 95/95 candidates 有 evidence_bundle；42/42 published rules 有 source | PASS |
| License | data_license 表 0 行 → **0/36 sources** | **FAIL** |
| Critical resolver error | 全量回归 889 passed / 0 resolver 失败 | PASS |
| UNKNOWN auto-allowed | access_answer 强制 unknown ≠ allowed（E2E 实测「信息不足」），无 UNKNOWN→ALLOWED 路径 | PASS |
| Inert exception | rule_exception 9 条存在且 resolver 测试覆盖 | PASS_WITH_LIMITATIONS（未逐条人工复核） |
| Obsolete semantics executable | 无 superseded 规则参与 current 求解（superseded=0） | PASS |
| Human Decision rewrite | Wave01/02 决策 artifact 与 DB 一致（review_decisions_expansion_r1_wave0{1,2}.json，huangdi97），无改写 | PASS |

## 5. 缺口清单（后续 Phase）
1. **License 缺口（FAIL）**：data_license 为空；OSM ODbL 出处仅在 evidence JSON 的 _readme 提及，未落库。→ 需 additive migration + 回填（人类确认各来源许可后）。
2. **SourceMonitor 到期未扫（21/22）**：Celery sweep 未运行（worker 仅测试时启动）。→ 生产 worker 部署后由 beat 驱动。
3. **Reality 数据 = 0**：Phase 21 30-Place Reality Completion 未开始（BLOCKED_EXTERNAL：需要真实现场/网上证据采集 + 人类核验，不可造数）。
4. **坐标**：30/30 有真实坐标（PASS）；place_geometry 全量几何表为空（设计允许，代表点已可用）。

## 6. 总评
30_PLACE_REALITY_AUDIT = PASS_WITH_LIMITATIONS（Rule 层健康、坐标齐全、无误推断、无造数；
License FAIL；Reality 数据为 INSUFFICIENT_OBSERVATION，30-Place Reality Completion 待真实证据）。
