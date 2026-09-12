# DB_INTEGRITY_REPORT.md

日期：2026-09-13（PART A · A6）· 数据库：PostgreSQL 17.5 + PostGIS 3.5（docker `petaccess-db-1`）

## 结构清单（实查）

| 项 | 值 | 来源命令 |
|---|---|---|
| 表 | 39 | `pg_tables` |
| FK 约束 | 66 | `pg_constraint contype='f'` |
| UNIQUE 约束 | 53 | `pg_constraint contype='u'` |
| CHECK 约束 | 8 | `pg_constraint contype='c'` |
| 索引 | 100 | `pg_indexes` |

关键专用索引（实查存在）：

- 空间：`ix_place_location_gist`（GIST，place.location 代表点，ADR-017）、
  `ix_place_geometry_geom_gist`（GIST，权威几何）
- 模糊搜索：`ix_place_canonical_name_trgm`（GIN/trgm；migration 6 曾被 autogenerate 误删、
  已显式保留——见 `MIGRATION_V05.md`）
- 候选队列：`ix_candidate_place` / `ix_candidate_status` / `ix_obs_candidate_place` /
  `ix_obs_candidate_status`
- SourceMonitor：`pk_source_monitor` + 行级字段；审计：`ix_audit_actor` / `ix_audit_created` /
  `ix_audit_target`

## 查询计划（EXPLAIN ANALYZE，实跑）

1. **nearby（ST_DWithin 3000m + 距离排序 LIMIT 30）**：4 行演示数据下，planner 选择
   `ix_place_lifecycle_status` 索引扫描 + ST_DWithin 过滤（10ms）。GIST `ix_place_location_gist`
   存在于表上，数据量增大后 planner 将自动切换空间索引；当前行数下选 lifecycle 前导是正常代价决策。
2. **trgm 模糊搜索（ILIKE '%星河%'）**：4 行下 Seq Scan（0.06ms）；GIN trgm 索引存在，
   规模化后生效。

## 约束语义抽查

- `place`：`parent_not_self` CHECK（父=自身禁止）。
- `rule_candidate.source_id` / `evidence_bundle_id`：FK 且 `evidence_bundle` 为 RESTRICT
  （发布闸门证据链不可悬空）——由本轮单测证实：插入不存在的 source/bundle 在 DB 层即被
  FK 拒绝（`test_publish_rejects_missing_source/_evidence_bundle` 以未落库对象测服务层守卫）。
- `boundary_preference` uq(profile+attribute)、`coexistence_policy` uq(place+zone+attr+source)、
  watch `uq_watch_user_target`（重复关注被 unique guard 挡下，E2E-C 依赖）。
- audit：全表审计时间/主体/目标索引齐备。

## 迁移循环（A6 要求的三种库状态）

实跑序列（同日）：

```
populated（测试后） → downgrade base（7 步干净）
→ upgrade head（fresh）→ seed --demo（4 places/15 zones/8 sources）
→ downgrade base（seeded → base，回填反向干净）
→ upgrade head → seed --demo 复跑 → alembic current = c81e02ba6d45 (head)
```

fresh DB / seed DB / populated DB 三态均通过 upgrade→downgrade→upgrade。

## N+1 与 query plan 抽查

- places 列表/详情：p95 ≤ 13ms（见 `PERFORMANCE_BASELINE.md`），无逐行子查询迹象。
- resolver/answerability/boundary-match：纯函数或单场所查询，p95 ≤ 27ms。
- 未发现 N+1 模式（列表端点为单查询 + 分页；v05 读端点经 5 集成测试）。

## 结论

结构完整性、空间/模糊/队列/审计索引、约束语义、三态迁移循环 —— **PASS**。
已知登记项：worker/shell 与 design-tokens 空目录与 DB 无关，见 TECH_DEBT_REGISTER。
