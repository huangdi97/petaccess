# MIGRATION_AUDIT.md

日期：2026-09-13（PART A · A7）· 基线文档：`MIGRATION_V05.md`（V36 已验证）

## 迁移链（7 个 revision，全部实跑核验）

| # | Revision | 内容 | 性质 | 可逆 |
|---|---|---|---|---|
| 1 | `864ffcfc7ccb` | initial schema（17+ 表，PostGIS GIST + trgm GIN） | 基线 | 是（downgrade → 空） |
| 2 | `2e0155d834eb` | media_object | additive 新表 | 是 |
| 3 | `4930732f4783` | v0.5 域 16 表 + access_rule 6 可空列 | additive | 是 |
| 4 | `b2a1c7d9e001` | rule_layer 确定性回填（幂等） | additive 回填 | 是（仅清除确定性映射值） |
| 5 | `5cb24fc8e838` | evidence-first 三表 | additive | 是 |
| 6 | `4565819baf78` | source_monitor.last_excerpt | additive 可空列 | 是（trgm 索引显式保留） |
| 7 | `c81e02ba6d45` | rule_candidate.evidence_bundle_id（RESTRICT FK） | additive | 是 |

## 审计结论

- **additive first**：7/7 无 drop/rename/非空化破坏性操作。
- **reversible**：本日实跑 `downgrade base` 两次（populated 与 seeded 两种起点）均干净；
  `upgrade head` 复原后 demo seed 正常。
- **destructive 说明**：无 destructive 操作。唯一需要注意的数据语义是 downgrade 会删除
  业务数据（candidates/evidence 等），`MIGRATION_V05.md` §6 已写明"先 backup 再 downgrade"。
- **backfill 幂等**：`b2a1c7d9e001` 两条 UPDATE 均带 `AND rule_layer IS NULL`，重复执行零副作用；
  不猜测（非确定性映射保持 NULL → resolver REVIEW_REQUIRED），downgrade 不留发明数据。
- **silent data loss**：无。迁移 6 的 autogenerate 险些删除手写 trgm 索引——已在迁移中显式
  保留并在 `MIGRATION_V05.md` 记录（非 silent：有文档 + 有意决策）。
- **索引保护**：`ix_place_canonical_name_trgm` 在本轮 DB_INTEGRITY_REPORT 实查存在。

## 本日验证证据

```
populated → downgrade base（7 步）→ upgrade head（fresh）
→ seed --demo → downgrade base（seeded）→ upgrade head → seed --demo
→ alembic current = c81e02ba6d45 (head)
```

结论：**PASS**。迁移链满足 additive-first / reversible / 幂等回填 / 无 silent data loss 四项要求。
