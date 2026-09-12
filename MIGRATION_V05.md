# MIGRATION_V05.md

v0.5 数据库迁移文档 — 记录实际存在的迁移、回填策略、已验证的 up/down/up 证据，
以及旧数据/旧 API 的兼容性说明。规格来源：`docs/MIGRATION_SPEC_v0.5.md`、
`NEXT_GOAL_v0.5.md` §8。

- 代码基线：HEAD `88b4c70`
- 验证日期：2026-09-13
- 数据库：PostgreSQL 17.5 + PostGIS 3.5（本地 docker `petaccess-db-1`）

---

## 1. 迁移链（完整，6 个 revision）

| # | Revision | 名称 | 内容 | 性质 |
|---|---|---|---|---|
| 1 | `864ffcfc7ccb` | initial schema: all domain entities | v0.3 的 17+ 张基础表（place/zone/access_rule/source/user/pet/observation/operator/dispute/watch/audit…），含 PostGIS GIST 与 trgm GIN 索引 | 基线 |
| 2 | `2e0155d834eb` | track A: media_object | 新增 `media_object`（object_key/mime/size/sha256/upload_status/moderation_status/privacy_class/expires_at…） | additive（新表） |
| 3 | `4930732f4783` | v05 domain | 新增 16 张 v0.5 表 + `access_rule` 增量列（见 §2） | additive（新表 + 可空列） |
| 4 | `b2a1c7d9e001` | backfill rule_layer | 由 `source.source_type` 确定性回填 `access_rule.rule_layer`（见 §3） | additive（仅回填可空列，幂等） |
| 5 | `5cb24fc8e838` | evidence-first | 新增 `source_artifact`、`evidence_bundle`、`observation_candidate` | additive（新表） |
| 6 | `4565819baf78` | source_monitor last_excerpt | `source_monitor` 增加 `last_excerpt`（Text，可空），用于把检测到的源变化转成可追溯 EvidenceBundle | additive（可空列） |

无任何 drop/rename/非空化 破坏性操作。第 6 个迁移的 autogenerate 曾提议删除手写的
`ix_place_canonical_name_trgm` GIN/trgm 索引（Alembic 无法内省），已在迁移中显式保留
——该索引承载场所模糊搜索，删除会静默降级。

## 2. `4930732f4783`（v0.5 域）新增与增量明细

新表：`freshness_policy`、`organization`、`boundary_profile`（FK→user，CASCADE）、
`boundary_preference`（uq profile+attribute）、`data_license`（FK→source，CASCADE）、
`data_source_job`（ix job_type+state）、`policy_template`、`policy_template_rule`、
`place_policy_binding`（ix place+active）、`access_path`、`source_monitor`、
`amenity`（ix place+type）、`coexistence_policy`（uq place+zone+attr+source）、
`entrance`、`event_policy`（ix effective_from+to）、`rule_candidate`
（ix place、ix review_status）。

`access_rule` 增量列（全部可空，旧行可读）：
`rule_layer`、`origin_authority`、`organization_id`、`policy_template_id`、
`event_policy_id`、`freshness_policy_id`。

## 3. 回填策略（`b2a1c7d9e001`，幂等、保守、不猜）

只做两类**确定性**映射，其余一律不猜：

| source.source_type | 回填值 | 依据 |
|---|---|---|
| `statute_or_regulation`、`government_service` | `LEGAL` | 现有语义：法定来源 |
| `official_operator_policy` | `OPERATOR_POLICY` | 现有语义：管理方声明 |
| 其余（onsite signage / ordinary user / external refs…） | **保持 NULL** | resolver 输出 `REVIEW_REQUIRED`，绝不猜测 |

幂等性：两条 UPDATE 都带 `AND r.rule_layer IS NULL`，重复执行零副作用。
downgrade 仅清除这两类确定性映射值，恢复升级前 NULL 状态，不留下任何发明数据。
注：`REGULATORY_GUIDANCE` 没有可判定的旧字段，v0.3 数据中不存在确定性映射来源，
故无自动回填；如需升级为 GUIDANCE 由管理员在候选审核中显式赋予。

## 4. 旧数据 / 旧 API 兼容性

- **旧数据可读**：所有增量列可空；v0.3 行在新 schema 下原样可读，
  `rule_layer` 未定 → resolver 归入 `REVIEW_REQUIRED`/`UNKNOWN`，不猜。
- **旧 API 稳定**：v0.5 域全部走新增 `/api/v1/v05/*` 路由与新增表；
  v0.3 路由（places/zones/access-rules/observations/operator/dispute/watch/ai/…）
  的请求/响应模型未改动。`access_rule` 的响应模型只增可选字段，向后兼容。
- **seed 兼容**：`app/db/seed.py` 重置清单已按 FK 安全顺序纳入全部 v0.5 表
  （takeover 修复的 `fk_rule_candidate_source_id_source` 缺陷），`--demo` 可重复执行。

## 5. 已验证证据（真实命令，2026-09-13）

```text
$ uv run alembic downgrade base     # 6 个 downgrade 步全部执行
$ uv run alembic upgrade head       # 6 个 upgrade 步全部执行（第 1 轮）
$ uv run alembic downgrade base     # 6 个 downgrade 步全部执行（第 2 轮）
$ uv run alembic upgrade head       # 6 个 upgrade 步全部执行（第 2 轮）
$ uv run alembic current
4565819baf78 (head)
$ uv run python -m app.db.seed --demo
Demo seed complete: {'users': 4, 'pets': 3, 'places': 4, 'zones': 15, …, 'sources': 8, …}
```

即 **down → up → down → up 双循环干净通过**（每方向各 6 个 revision 步），
升级后 demo seed 正常。基线测试在同日重跑：pytest 129 passed、Playwright 7 passed。

## 6. 回滚说明

- `alembic downgrade <target>` 沿链路逆向 drop 新表/新列；上述全链 downgrade 已验证。
- `rule_layer` 回填数据可由重跑 upgrade 恢复（确定性映射，无损失）。
- 业务数据（candidates/observations/evidence 等）downgrade 即删；如需保留，
  先用 backup/restore 流程导出（`docs/BACKUP_RESTORE_RUNBOOK.md`），再执行 downgrade。
