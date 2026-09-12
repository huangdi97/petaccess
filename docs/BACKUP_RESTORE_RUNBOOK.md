# Backup / Restore Runbook（v0.5 演练记录见文末）

## 范围
本地/试点环境：dockerized PostgreSQL 17 + PostGIS（容器 `petaccess-db-1`）与
MinIO（容器 `petaccess-minio-1`，bucket `petaccess-dev`）。

## 数据库

### 备份（每日/每次发布前）
```bash
docker compose exec -T db pg_dump -U petaccess -d petaccess > backup_$(date -u +%Y%m%d%H%M%S).sql
```
- 逻辑备份，含 PostGIS 几何（WKB）；纯 SQL，可跨版本。
- 保留策略建议：7 天日备 + 4 周周备（试点阶段手工即可）。

### 恢复（演练已验证）
```bash
docker compose exec -T db psql -U petaccess -d postgres -c "CREATE DATABASE restored;"
docker compose exec -T db psql -U petaccess -d restored -c \
  "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS pg_trgm;"
cat backup_xxx.sql | docker compose exec -T db psql -U petaccess -d restored
```
注意：
- 必须先建 postgis/pg_trgm 扩展（扩展对象不在业务 dump 的 CREATE EXTENSION 段）。
- 迁移基线：恢复后 `alembic current` 应等于备份时的 head revision。

### 完整性验证（演练脚本自动执行）
- 点位 marker（备份前写入 audit_log）在恢复库中存在；
- `place` 行数一致；
- `ST_IsValid(geom)` 全部有效；
- 应用层 `uv run pytest tests/integration -q` 对恢复库跑通即为最终验收。

## 对象存储

### 策略
- `media_object` DB 行是元数据 source of truth；对象内容不可变（key 随机、不覆盖）。
- 备份 = `mc mirror` 到第二 bucket/远端 + MinIO server-side versioning（试点可选）。
- 恢复 = mirror 回来后按 DB 行校验（每个 stored 行 stat_object 可命中且 sha256 一致）。

### 检查命令
```bash
uv run python -c "
from minio import Minio
from app.core.config import get_settings
from app.providers.factory import get_storage_provider
s = get_settings(); get_storage_provider().ensure_bucket(s.s3_bucket)
mc = Minio(...); list(mc.list_objects(s.s3_bucket, recursive=True))"
```

### TTL
- scene_photo：`scene_photo_ttl_hours`（默认 72h）；evidence：`signage_retention_days`（默认 365d）。
- worker beat `cleanup_expired_scene_photos` 每小时清理；`upload_status=purge_failed` 行需要人工检查。

## 演练记录
- `bash scripts/backup_restore.sh` → **BACKUP/RESTORE DRILL PASS**
  （marker 恢复 1/1、place 7/7、有效几何 6、MinIO 对象可枚举可读取）
