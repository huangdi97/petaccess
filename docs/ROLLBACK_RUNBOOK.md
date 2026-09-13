# ROLLBACK_RUNBOOK.md

> P8/P13 · 回滚与发布回退手册
> 关联：`docs/BACKUP_RESTORE_RUNBOOK.md`、`BACKUP_RESTORE_EVIDENCE.md`、`MIGRATION_AUDIT.md`
>
> **重要**：本手册的操作**尚未在真实生产环境演练**（无生产环境，见 `FINAL_PRODUCTION_READINESS_REPORT.md`）。演练状态标注为 `NOT_RUN`。

---

## 1. 回滚的四个层级

| 层级 | 对象 | 触发条件 | 目标 RTO |
|---|---|---|---|
| L1 | 单条 AccessRule | 规则被证明有误 | 分钟级 |
| L2 | 一次发布批次 | 整批规则来源失效 | 小时级 |
| L3 | 应用版本 | 新版本引入 P0/P1 缺陷 | 分钟级 |
| L4 | 数据库 | 数据损坏 / 迁移失败 | 小时级 |

---

## 2. L1 — 撤回单条规则

规则撤回**不删除**记录，而是改变状态（保留证据链与审计）。

```bash
# 通过 Admin API（需 MODERATOR 角色）
curl -X POST "$API/api/v1/admin/rules/{rule_id}/withdraw" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason":"来源失效，经复核撤回","reviewer":"<具名>"}'
```

验证：
1. `GET /api/v1/admin/rules/{rule_id}` → `status = withdrawn`
2. `POST /api/v1/places/{place_id}/effective-rules` → 该规则不再出现在 `applicable_rules`，且 `explanation_steps` 记录撤回
3. `audit_log` 出现 `rule.withdraw` 记录，含 `before_state` / `after_state`

> **注意**：撤回后若该场所无其它规则，查询结果应回落为 `UNKNOWN`（**不是** `allowed`）。这是必须验证的行为。

---

## 3. L2 — 回退一个发布批次

每个批次有快照：`PUBLISHED_RULES_SNAPSHOT_R1.json`（结构见 P0 报告）。

```bash
# 1. 列出该批次发布的规则
python scripts/list_batch_rules.py --snapshot PUBLISHED_RULES_SNAPSHOT_R1.json

# 2. 逐条撤回（脚本内会逐条写审计）
python scripts/withdraw_batch.py --snapshot PUBLISHED_RULES_SNAPSHOT_R1.json \
  --reviewer "<具名>" --execute
```

批次回退后必须重跑：`reality_audit` 回归（`tests/unit/test_real_world_regression.py` 对应的真实数据版本）。

---

## 4. L3 — 回退应用版本

前提：发布时已打 tag（如 `v0.6.0-beta.1`）且记录了前一版本。

```bash
# 1. 确认当前与目标版本
git log --oneline -5
git tag --list 'v0.6*'

# 2. 回退（生产环境按实际部署方式执行）
git checkout <previous-tag>

# 3. 若含迁移，执行降级
cd services/api && alembic downgrade -1

# 4. 健康检查
curl -fsS "$API/api/health" | jq .
```

**迁移回滚风险**：本仓库迁移以 **additive** 为主（加列、加表、加约束）。`downgrade()` 已实现，但**仅在开发库演练过**（`MIGRATION_V05.md` 记录 double down/up 周期验证）。生产降级需先备份。

---

## 5. L4 — 数据库恢复

见 `docs/BACKUP_RESTORE_RUNBOOK.md`。要点：

1. 停止 API 与 worker 写入；
2. 从最近备份恢复（`scripts/backup_restore.sh`）；
3. 校验：迁移版本一致（`alembic current`）、审计日志连续、`PostGIS_Version()` 可用；
4. 恢复服务，跑 smoke。

**演练证据**：`BACKUP_RESTORE_EVIDENCE.md` 记录了一次真实备份/恢复演练（Track A4）。但该演练在**开发环境**，非生产。

---

## 6. 回滚决策表

| 现象 | 层级 | 首要动作 |
|---|---|---|
| 单条规则结论错误 | L1 | 撤回该规则，重跑回归 |
| 一批规则来源整体失效 | L2 | 批次回退 |
| 新版本接口 5xx 或数据损坏 | L3 | 版本回退 + 迁移降级 |
| 数据文件损坏 / 误删 | L4 | 从备份恢复 |
| 地图/AI provider 故障 | — | 切换 provider（`MAP_PROVIDER=mock` / `AI_PROVIDER=mock`），功能降级但服务可用 |

---

## 7. 演练状态

| 演练 | 状态 |
|---|---|
| 迁移 double down/up 周期 | ✅ 开发环境已演练（`MIGRATION_V05.md`） |
| 备份/恢复 | ✅ 开发环境已演练（`BACKUP_RESTORE_EVIDENCE.md`） |
| L1 单条撤回 | ⏸ `NOT_RUN`（需数据层） |
| L2 批次回退 | ⏸ `NOT_RUN`（无已发布批次） |
| L3 版本回退 | ⏸ `NOT_RUN`（无生产环境） |
| L4 生产恢复 | ⏸ `NOT_RUN`（无生产环境） |
