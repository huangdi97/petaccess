# OBSERVABILITY REPORT — 2026-09-23 实测

> 母版 Phase 29（Observability）。判定方式：真实启动 API（TEST DB `petaccess_test`，
> uvicorn :8011）+ 调用健康/指标端点 + 代码盘点（`app/core/observability.py` 等）。
> 状态词：PASS / PASS_WITH_LIMITATIONS / NOT_VERIFIED / BLOCKED_EXTERNAL / BLOCKED_HUMAN / FAIL。

## 0. 总判定

`OBSERVABILITY = PASS_WITH_LIMITATIONS`

- 应用层：`/health`、`/health/database`、`/health/ready`、`/health/components`、`/metrics`
  真实存在并实测可用；进程内指标（request total / 5xx / latency p50/p95）真实计数。
- 外部可观测（Prometheus 抓取、集中日志、告警通道、生产 worker/队列监控面板）：
  本机无生产环境 → `BLOCKED_EXTERNAL`（Phase 30 部署项）。
- Celery/beat/队列：当前 worker 仅在测试时按需启动（`-Q petaccess_test`），无常驻 worker，
  因此 `/health/components` 如实返回 `celery.ok=false`；生产部署 worker 后由 beat 驱动。

## 1. System 层（实测）

| 组件 | 判定 | 证据 |
|---|---|---|
| API | PASS | uvicorn :8011 实测；`/health` → `{"status":"ok","app":"pet-access-map","env":"development"}` |
| PostgreSQL | PASS | `/health/components` postgres ok=true（PostGIS 3.5 版本串返回） |
| Redis | PASS | `/health/components` redis ok=true |
| MinIO | PASS | `/health/components` minio ok=true |
| worker | PASS_WITH_LIMITATIONS | celery nodes=0（无常驻 worker，实测如实返回 false）；测试期按需启动可跑通全部 Celery 用例 |
| queue | PASS_WITH_LIMITATIONS | Redis db1 `petaccess_test` 队列真实承载；生产队列名/监控待部署 |
| publisher（Rule/Reality publish） | PASS | publish audit 事件 + `artifacts/wave02_publish_receipt.json`（REAL_PUBLISH_EXECUTED）；失败路径有 audit 记录（`record_audit` 全覆盖，测试覆盖） |
| migration | PASS | alembic current == heads == `e9f2c1d4a5b6`；`alembic check` = No new upgrade operations |
| backup | PASS | `docs/backup/BACKUP_RESTORE_DRILL_REPORT.md`：pg_dump 6.4MB → restore → integrity compare PASS（2026-09-23 实测） |
| 5xx / 403 / 429 | PASS_WITH_LIMITATIONS | `metrics.incr("http.requests.5xx")` 在 main.py 中间件真实挂载；403/429 有独立计数路径与测试；集中告警待生产 |

## 2. Domain 层（当前真实值）

| 指标 | 当前值 | 判定 |
|---|---|---|
| SourceMonitor overdue | 22 个 active，21 个 `next_check_at <= now()` 到期未扫 | PASS_WITH_LIMITATIONS（worker beat 未运行；生产启动 sweep 后闭环） |
| Rule Freshness | 42 current rules，superseded=0 | PASS |
| Reality Freshness | Reality 各表 0 行（无数据可过期） | PASS_WITH_LIMITATIONS（空洞满足，Phase 21 后才有实质意义） |
| Candidate backlog | rule_candidate 95（51 published）；reality_candidate 0 | PASS_WITH_LIMITATIONS |
| Reality Review backlog | 0（无 reality candidates） | PASS_WITH_LIMITATIONS |
| Rule-Reality Divergence | 无 reality 数据 → 无 divergence 可计算 | PASS_WITH_LIMITATIONS |
| publish failures | 0（wave01/02 publish 全部成功；fail-closed 门禁存在） | PASS |
| facility stale | 0（无 facility 数据） | PASS_WITH_LIMITATIONS |
| dispute backlog | dispute_case 表存在，当前 0 pending（DB 实测） | PASS_WITH_LIMITATIONS |
| obsolete manifest attempt | 0（publish 幂等门禁测试覆盖，second-run NOOP PASS） | PASS |
| place-match unresolved backlog | reality 贡献 0 条 → 0 | PASS_WITH_LIMITATIONS |

## 3. Product 层（当前实现）

| 事件 | 状态 |
|---|---|
| search failure / empty result | 前端空态（`暂无收录内容` token）存在；无独立埋点计数 |
| place load | 页面加载/错误/空态状态机已实现（PAGE_STATES） |
| evidence open / contribution start / submit / correction | 页面存在；埋点计数未实现（Product analytics 最小化原则，母版要求不保留不必要精确位置、不建个人轨迹） |
| map lens switch | Map 页 lens UI 存在；埋点未实现 |

## 4. 缺口（如实记录）

1. **无生产 Prometheus/集中日志/告警**：`/metrics` 是进程内 JSON snapshot，非 Prometheus 文本格式；
   生产部署需 exporter + 日志聚合 + 告警规则（Phase 30，BLOCKED_EXTERNAL：无生产环境）。
2. **无常驻 worker**：beat 任务（watch-notify / media-ttl / source-monitor sweep）本机未常驻；
   生产 `celery worker --beat` 启动后由调度驱动（部署项）。
3. **Product 埋点未实现**：母版允许最小化，但若上线需在 Phase 30 补齐受控事件（隐私边界内）。
4. **媒体对象存储监控**：MinIO healthy；bucket 大小/对象数/版本化监控待生产。

## 5. 结论

```
OBSERVABILITY = PASS_WITH_LIMITATIONS
```
应用层健康/指标端点全部实测可用；域级指标口径清晰且有真实 DB 基线；
生产级可观测性（exporter/告警/常驻 worker/集中日志）为部署项 → BLOCKED_EXTERNAL（Phase 30）。
