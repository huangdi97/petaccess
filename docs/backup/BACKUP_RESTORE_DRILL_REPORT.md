# BACKUP_RESTORE_DRILL_REPORT — 2026-09-23 实测

> 真实执行：live DB → pg_dump → 受控 mutation → restore 到全新 DB → integrity compare → 清理。
> 状态词：PASS / FAIL / BLOCKED_EXTERNAL。

## 1. 执行记录（2026-09-23，真实 dockerized PostgreSQL）
| 步骤 | 结果 |
|---|---|
| 1. 插入 point-in-time marker（audit_log） | 1 row |
| 2. pg_dump 全库 | **6,368,138 bytes**（schema + 数据） |
| 3. 全新 restore DB + postgis/pg_trgm + 导入 dump | 无错误 |
| 4. integrity compare（marker / places / rules / sources） | **marker=1、places=30、rules=42、sources=36 → PASS** |
| 4b. 受控 mutation → 灾难恢复 | live 改名 1 place + 删 marker → 重新 restore：**restored 中 mutated=0、marker=1（时间点保留）→ PASS** |
| 5. 清理 | live 复原（places=30）、drop restore DB×2、删 dump → 无残留 |

## 2. 覆盖核对
| 表 | live | restored | 一致 |
|---|---|---|---|
| place | 30 | 30 | ✓ |
| access_rule | 42 | 42 | ✓ |
| rule_exception | 9 | 9 | ✓ |
| source | 36 | 36 | ✓ |
| source_monitor | 22 | 22 | ✓ |
| zone | 44 | 44 | ✓ |
| reality_report / observed_presence / staff_response / animal_facility / evidence_bundle / audit_log 等 | 全库 dump 包含 | 全库恢复 | ✓（marker 行验证） |

> 注：reality 各表当前为 0 行（Phase 21 未开始）；dump/restore 机制不依赖行数，marker + 4 表计数 + 结构恢复已验证。

## 3. 结论
```
BACKUP_RESTORE_DRILL = PASS
```
- dump 完整（6.4MB，全 schema+数据）；
- restore 到全新 DB 无错误；
- 时间点一致性：dump 时 marker 保留、mutation 未混入；
- 清理后 live DB 恢复原状（places=30、无 drill 残留）。
- 对象存储：MinIO bucket petaccess-dev 可列出/读取对象；正式生产备份策略需含 mc mirror + 版本化（部署项）。
