# 30_PLACE_CONSUMER_ANSWERABILITY_REPORT.md — 2026-09-23 实测

> DB 实测 + E2E（18/18）+ visual（47/47）。状态词：PASS / PASS_WITH_LIMITATIONS / NOT_VERIFIED / BLOCKED_EXTERNAL / BLOCKED_HUMAN / FAIL。

## 1. 「能回答」定义
- Rule 层：给定 place + animal scope，resolver 能产出 AccessAnswer（allowed / conditional / prohibited / unknown），且 unknown ≠ allowed。
- Reality 层：能展示 RealityAnswer；无数据时必须为 INSUFFICIENT_OBSERVATION（不假装「无动物」）。

## 2. 逐 Place 回答能力（30 个，DB 实测 rules 分布）
| 回答形态 | Place 数 | 说明 |
|---|---|---|
| 有 place/zone 级 current rules 可直接回答 | 24 | park/cafe/mall/museum/hotel/library 等（zones 1–3 + rules 1–4） |
| 无任何 rules（UNKNOWN，诚实未核验） | 5 | 上海辰山植物园 / 昌路公园 / 广场公园（外滩段）/ 上海世博(园?) / 豫园 等 z=1 pr=0 场所 |
| Reality 层 | 0/30 有数据 → 全部 INSUFFICIENT_OBSERVATION | 未造数 |

## 3. Consumer 面回答能力（本会话实测）
| 面 | 覆盖 | 状态 |
|---|---|---|
| Home（search-first 决策首页） | 渲染 + 附近已核验 + 搜索入口 | PASS（visual 基线通过） |
| Search | 模糊名搜索（trgm）+ 卡片显示 Rule/Reality/Evidence/Freshness | PASS（E2E search finds place by fuzzy name） |
| Map | mock 壳 + list fallback；真实地图 BLOCKED_EXTERNAL（TENCENT_MAP_KEY） | PASS_WITH_LIMITATIONS |
| Place passport | Rule / RealityPanel / Staff / Facility / Divergence / Evidence / Zones / Conditions / History / Corrections | PASS（E2E + visual） |
| Rule Trace（为什么） | 推导步骤可解释 | PASS（E2E + visual） |
| Contribution | 现场/过去/网上入口（v0.9-R1 基础） | PASS_WITH_LIMITATIONS（深化走 Phase 12-19） |
| My / Preference | mine hub + boundary 设置 | PASS（visual） |

## 4. 回答诚实性检查（DB + API 实测）
| 检查 | 值 | 状态 |
|---|---|---|
| unknown ≠ allowed | access_answer：effect=unknown 文案「未知 ≠ 允许」；E2E 断言「信息不足」 | PASS |
| zone 规则不拍平成场所结论 | access_answer 设计不变量；E2E/visual 断言 place=信息不足 + zone=明确限制/有条件 | PASS |
| 无数据不显示「无动物」 | RealityAnswer=INSUFFICIENT_OBSERVATION；RealityPanel「暂无记录 ≠ 没有动物」 | PASS |
| Publication time ≠ event time | 贡献模型 content_published_at 独立；测试固定不变量 | PASS |
| 服务犬语义 | E2E：服务犬通行 → 可以进入（本次修复 mode→working 映射） | PASS |

## 5. 结论
30_PLACE_CONSUMER_ANSWERABILITY_REPORT = PASS_WITH_LIMITATIONS
（24/30 Place 可回答 Rule；6/30 诚实 UNKNOWN；0/30 Reality 数据（INSUFFICIENT_OBSERVATION，未造数）；
真实地图为 BLOCKED_EXTERNAL（地图 Key）。）

