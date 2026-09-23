# 30_PLACE_DATA_QUALITY_REPORT.md — 2026-09-23 实测

> DB 实测（petaccess）+ artifact 复核。状态词：PASS / PASS_WITH_LIMITATIONS / NOT_VERIFIED / BLOCKED_EXTERNAL / BLOCKED_HUMAN / FAIL。

## 1. Place 数据质量
| 检查 | 值 | 状态 |
|---|---|---|
| canonical Place 数量 | 30 | PASS |
| 真实坐标（place.location） | 30/30 非空；lat 31.04–31.34 / lon 121.18–121.72（上海中心城区） | PASS |
| place_geometry 全量几何 | 0 行（代表点已可查询；全量几何表可选未填） | PASS_WITH_LIMITATIONS |
| canonical_name 唯一 | 见 §4 查重 | — |
| lifecycle_status | 30/30 active | PASS |
| parent/tenant 建模 | mall 4 + parent_place_id 关系可用（ADP 中台模型） | PASS |

## 2. Rule 数据质量
| 检查 | 值 | 状态 |
|---|---|---|
| Rules（current） | 42（LEGAL 14 / OPERATOR_POLICY 28） | PASS |
| Rules with source | 42/42 = 100% | PASS |
| Rules with evidence bundle | published candidates 95/95 有 evidence_bundle | PASS |
| Rule exceptions | 9 条（service dog 例外等） | PASS_WITH_LIMITATIONS |
| 唯一规则标识 | rule_candidate ↔ published_rule_id 映射齐全（51 published） | PASS |
| superseded 残留 current 求解 | superseded=0 参与 | PASS |
| License（data_license 表） | **0 行**；OSM ODbL 出处仅在 evidence JSON 的 geo.licence 字段记录 | **FAIL** |

## 3. Source 数据质量
| 检查 | 值 | 状态 |
|---|---|---|
| Sources | 36（official_operator_policy 16 / external_web_reference 13 / government_service 4 / statute_or_regulation 2 / ordinary_user 1） | PASS |
| source_url 非空 | 34/36（94.4%） | PASS_WITH_LIMITATIONS（2 条无 URL，应为 statute 类） |
| SourceMonitor | 22，全部 active | PASS |
| Monitor 到期未扫 | 21/22 next_check_at <= now()（worker 未常驻） | PASS_WITH_LIMITATIONS → BLOCKED_EXTERNAL（生产 worker 缺失） |
| Source 许可落库 | 0/36 | FAIL |

## 4. 查重 / 名称质量
```sql
-- canonical_name 重复检查（本会话实测）
SELECT canonical_name, count(*) FROM place GROUP BY 1 HAVING count(*) > 1;
-- 结果：无重复（0 行）
```
- 别名（alias_names）承载品牌短名/旧名；branch 建模为独立 place + parent_place_id。

## 5. 数据质量缺陷清单
1. **License 未落库（FAIL）**：`data_license` 0 行。证据 JSON 已含 OSM ODbL licence 串（geo.licence），但未回填到 data_license；各 source 的许可类型需人类逐条确认后回填（BLOCKED_HUMAN for 确认，非技术阻碍）。
2. **SourceMonitor 到期积压（21/22）**：sweep 任务存在（celery beat source-monitor-sweep）但 worker 未常驻；生产部署后自动清扫。
3. **2 个 source 无 URL**：statute_or_regulation 2 条（法条类可无 URL 但应有 statute ref；人工补全）。
4. **place_geometry 空表**：不影响 PostGIS 查询（代表点 location 已建 gist 索引）。

## 6. 结论
30_PLACE_DATA_QUALITY_REPORT = PASS_WITH_LIMITATIONS
（Place/Rule/Source 主体健康：坐标 100%、source 覆盖 100%、evidence 100%；
License 落库 FAIL、monitor 到期积压、2 source 无 URL 为真实缺陷待补。）
