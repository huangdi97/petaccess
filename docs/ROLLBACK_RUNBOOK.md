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
# 注意：rules 的 admin 路由未加 /admin 前缀（见 §8），因此路径是 /api/v1/rules/{id}
curl -X PATCH "$API/api/v1/rules/{rule_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"withdrawn"}'
```

验证：
1. `GET /api/v1/places/{place_id}/rules` → 该规则 `status = withdrawn`（**仍在列表中，未被删除**）
2. `POST /api/v1/places/{place_id}/effective-rules` → 该规则不再出现在 `applicable_rules`
3. `GET /api/v1/admin/audit?target_id={rule_id}` → 出现 `action = rule.update`，
   且 `before_state.status = "current"` / `after_state.status = "withdrawn"`

> **注意**：撤回后若该场所无其它规则，查询结果应回落为 `UNKNOWN`（**不是** `allowed`）。
> 这是必须验证的行为。
>
> **已由集成测试固定**：`tests/integration/test_rollback_l1.py`（5 用例，真实 DB）覆盖
> 上述全部断言 —— 回落 UNKNOWN、行与证据链保留、审计留痕、权限校验、404。

---

## 3. L2 — 回退一个发布批次

每个批次有快照：`PUBLISHED_RULES_SNAPSHOT_R1.json`（由 `scripts/publish_reviewed_r1.py --execute`
在真实发布后写出；**尚未执行过真实发布，因此该文件当前不存在**——见 §7）。

> ⚠️ **当前状态：L2 的辅助脚本尚未实现。**
> `scripts/list_batch_rules.py` 与 `scripts/withdraw_batch.py` **不存在**。
> 批次回退目前只能按 L1 的方式**逐条**执行：

```bash
# 1. 从快照取出该批次发布的 rule_id 列表（快照存在时）
python - <<'PY'
import json
doc = json.load(open("PUBLISHED_RULES_SNAPSHOT_R1.json", encoding="utf-8"))
for row in doc["detail"]["published"]:
    print(row["published_rule_id"])
PY

# 2. 逐条撤回（每条都会写 audit）
for RID in $(...); do
  curl -X PATCH "$API/api/v1/rules/$RID" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"status":"withdrawn"}'
done
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
curl -fsS "$API/health" | jq .
curl -fsS "$API/health/components" | jq .   # 四依赖逐项：postgres/redis/minio/celery
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

> 2026-09-14 更新：ENV-01 已解除（PostGIS/Redis/MinIO/Celery 就绪），L1 与迁移周期已在
> **真实数据库**上演练。

| 演练 | 状态 |
|---|---|
| 迁移 up/down/up 周期 | ✅ **真实 DB 已演练**（2026-09-14，head `f4c9d2e7a831`）；另见 `MIGRATION_V05.md` |
| 备份/恢复 | ✅ 开发环境已演练（`BACKUP_RESTORE_EVIDENCE.md`） |
| **L1 单条撤回** | ✅ **真实 DB 已演练**（`tests/integration/test_rollback_l1.py`，5 用例：回落 UNKNOWN / 行保留 / 审计 / 权限 / 404） |
| L2 批次回退 | ⏸ `NOT_RUN`（无已发布批次；**且辅助脚本尚未实现**，见 §3） |
| L3 版本回退 | ⏸ `NOT_RUN`（无生产环境） |
| L4 生产恢复 | ⏸ `NOT_RUN`（无生产环境） |

---

## 8. 已知不一致（执行本手册前必读）

1. **`rules` 的 admin 路由未加 `/admin` 前缀。**
   本仓库 6 个模块（`rules` / `places` / `sources` / `operators` / `regulations` / `disputes`）的
   `admin = APIRouter(tags=[...])` **没有** `prefix="/admin"`，而 `v05` 与 `admin.py` 有。
   因此管理员写入落在**非 admin 路径**上，例如：

   | 操作 | 实际路径 | 期望（按其它模块约定） |
   |---|---|---|
   | 创建规则（OPERATOR） | `POST /api/v1/rules` | `POST /api/v1/admin/rules` |
   | 更新/撤回规则（MODERATOR） | `PATCH /api/v1/rules/{id}` | `PATCH /api/v1/admin/rules/{id}` |

   权限仍由 `require_role` 强制（**不是**越权漏洞），但路径语义误导，
   本手册早期版本即因此写错了端点。已登记为技术债（`TECH_DEBT_REGISTER.md` TD-20）。

2. **L2 辅助脚本缺失**：`scripts/list_batch_rules.py`、`scripts/withdraw_batch.py` 均不存在；
   批次回退暂只能按 L1 逐条执行（见 §3）。

3. **快照文件按需生成**：`PUBLISHED_RULES_SNAPSHOT_R1.json` 只在
   `publish_reviewed_r1.py --execute` 成功后写出。尚未执行真实发布 ⇒ 该文件当前不存在。
