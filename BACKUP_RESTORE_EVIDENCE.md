# BACKUP_RESTORE_EVIDENCE.md

日期：2026-09-13（PART A · A13）· 演练：`bash scripts/backup_restore.sh`（本轮真实执行）

## 演练记录（实际输出）

| 步骤 | 结果 |
|---|---|
| 1. 打点：插入 audit marker 行（`drill-marker-20260912203540`） | OK；dump 时点 places=4 |
| 2. `pg_dump` 全库 | dump 109,195 bytes |
| 3. 新建 fresh DB `petaccess_restore_20260912203540` + postgis/pg_trgm 扩展 + 全量恢复 | OK |
| 4. 完整性比对 | marker=1 ✓；places=4/4 ✓；valid geometries=6 ✓ |
| 5. MinIO 对象存储策略检查 | bucket `petaccess-dev` 122 对象；随机抽检对象可读取（61 bytes）✓ |
| 6. 清理（marker 行、restore DB、dump 文件） | OK |

最终输出：`=== BACKUP/RESTORE DRILL PASS ===`

## 覆盖的 A13 要点

- **backup → mutate/delete → restore clean DB → integrity compare**：演练含打点行（mutate）
  与恢复后逐项比对；`docs/BACKUP_RESTORE_RUNBOOK.md` 为操作手册。
- **MinIO**：metadata（DB 行）为 source of truth；bucket 对象抽样可读；策略 =
  `mc mirror` + 版本化（脚本输出明示）。对象级删除/TTL 由 media 管线测试覆盖
  （`test_delete_removes_minio_object` / `test_ttl_purge_removes_expired`）。
- **migration 前保护**：`MIGRATION_V05.md` §6 已写明 downgrade 前先走本备份流程。

结论：**PASS**（真实演练，非文档推演）。
