# PERFORMANCE_BASELINE.md

日期：2026-09-13（PART A · A11）· 探针：`scripts/perf_baseline.py`（本轮新增，可复跑）
环境：本地栈 — uvicorn(8010) + dockerized PostGIS 17.5 / Redis 7 / MinIO；4 个演示场所。
方法：每端点 50 次顺序请求，记录 p50/p95/mean/max。数值为**本地开发基线**，非生产容量结论。

## API 基线（真实运行输出）

| 端点 | n | p50 ms | p95 ms | max ms |
|---|---|---|---|---|
| GET /health | 50 | 1.41 | 1.80 | 2.48 |
| GET /api/v1/places?limit=20（列表+trgm） | 50 | 8.56 | 12.88 | 17.04 |
| GET /api/v1/places/nearby r=3000 | 50 | 9.68 | 13.62 | 14.81 |
| GET /api/v1/places/{id}（详情） | 50 | 6.60 | 11.94 | 13.27 |
| GET /api/v1/places/{id}/zones | 50 | 8.19 | 9.45 | 9.95 |
| POST /api/v1/rules/evaluate（确定性评估） | 50 | 14.09 | 16.41 | 18.11 |
| GET answerability | 50 | 19.00 | 27.16 | 31.39 |
| GET /api/v1/admin/candidates?limit=20（admin 分页） | 50 | 16.43 | 22.43 | 23.96 |
| POST effective-rules（分层解析） | 50 | 19.17 | 23.04 | 30.59 |

说明：
- `GET boundary-match` 需调用者已保存 BoundaryProfile（400 without），不纳入裸探测；
  其匹配逻辑为纯函数（`v05_boundary.match`，100% 覆盖），成本量级与 answerability 相当。
- resolver batch（批量多场所评估）当前无独立端点，评估为逐场所调用；
  单次 14ms 量级下批量场景按 N×14ms 估算，登记 TECH_DEBT TD-06（批量端点，规模化时再做）。

## 数据库层（EXPLAIN ANALYZE 实跑，见 DB_INTEGRITY_REPORT）

- nearby：GIST `ix_place_location_gist` 就位；4 行下 planner 选 lifecycle 索引 + 过滤（10ms）。
- trgm ILIKE：GIN 索引就位；4 行下 Seq Scan 0.06ms。
- 结论：索引结构与查询形态匹配，规模化路径清晰（空间索引接管 nearby、GIN 接管模糊搜索）。

## 组件健康基线

- Postgres 17.5 / PostGIS 3.5：`/health/ready` 实查 PASS
- Redis：PONG（healthcheck + E2E-C 通知链）
- MinIO：bucket `petaccess-dev` 122 对象可检索（backup drill 实证）
- Celery：1 node online（历史基线）+ 任务有界重试

## 结论

九个读写端点本地 p95 全部 ≤ 28ms；无异常慢查询；DB 索引与 EXPLAIN 佐证。
基线建立完成，**PASS**。
