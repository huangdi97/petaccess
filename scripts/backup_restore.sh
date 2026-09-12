#!/usr/bin/env bash
# Backup/restore drill (NEXT_GOAL §A4). Runs a REAL cycle against dockerized Postgres:
#   live DB → pg_dump → mutate → restore into fresh DB → integrity check
# Usage: bash scripts/backup_restore.sh
set -euo pipefail
cd "$(dirname "$0")/.."

STAMP=$(date -u +%Y%m%d%H%M%S)          # lowercase-safe DB name suffix
DUMP="/tmp/petaccess_backup_${STAMP}.sql"
RESTORE_DB="petaccess_restore_${STAMP}"

echo "=== 1. insert marker row so the dump carries a verifiable point-in-time record ==="
docker compose exec -T db psql -U petaccess -d petaccess -q -c \
  "INSERT INTO audit_log (id, action, target_type, target_id) VALUES ('drill-marker-${STAMP}', 'backup.drill', 'audit_log', 'drill');"
PLACES_BEFORE=$(docker compose exec -T db psql -U petaccess -d petaccess -t -A -c "SELECT count(*) FROM place")
echo "places at dump time: $PLACES_BEFORE"

echo "=== 2. dump current DB ==="
docker compose exec -T db pg_dump -U petaccess -d petaccess > "$DUMP"
echo "dump size: $(wc -c < "$DUMP") bytes"

echo "=== 3. create fresh restore DB and restore the dump ==="
docker compose exec -T db psql -U petaccess -d postgres -q -c "DROP DATABASE IF EXISTS ${RESTORE_DB};"
docker compose exec -T db psql -U petaccess -d postgres -q -c "CREATE DATABASE ${RESTORE_DB};"
docker compose exec -T db psql -U petaccess -d "${RESTORE_DB}" -q -c \
  "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS pg_trgm;"
cat "$DUMP" | docker compose exec -T db psql -U petaccess -d "${RESTORE_DB}" -q

echo "=== 4. integrity check on restored DB ==="
RESTORED_MARKER=$(docker compose exec -T db psql -U petaccess -d "${RESTORE_DB}" -t -A -c \
  "SELECT count(*) FROM audit_log WHERE id='drill-marker-${STAMP}';")
RESTORED_PLACES=$(docker compose exec -T db psql -U petaccess -d "${RESTORE_DB}" -t -A -c "SELECT count(*) FROM place")
RESTORED_GEOM=$(docker compose exec -T db psql -U petaccess -d "${RESTORE_DB}" -t -A -c \
  "SELECT count(*) FROM place_geometry WHERE ST_IsValid(geom);")
echo "marker in restored DB (expect 1): $RESTORED_MARKER"
echo "places in restored DB (expect $PLACES_BEFORE): $RESTORED_PLACES"
echo "valid geometries in restored DB: $RESTORED_GEOM"
if [ "$RESTORED_MARKER" != "1" ] || [ "$RESTORED_PLACES" != "$PLACES_BEFORE" ]; then
  echo "RESTORE INTEGRITY CHECK FAILED"; exit 1
fi

echo "=== 5. object-storage backup strategy check ==="
uv run python - <<'EOF'
from minio import Minio

from app.core.config import get_settings
from app.providers.factory import get_storage_provider

s = get_settings()
get_storage_provider().ensure_bucket(s.s3_bucket)
mc = Minio(s.s3_endpoint.replace("http://", "").replace("https://", ""),
           access_key=s.s3_access_key, secret_key=s.s3_secret_key, secure=s.s3_secure)
objects = list(mc.list_objects(s.s3_bucket, recursive=True))
print(f"minio bucket '{s.s3_bucket}' objects: {len(objects)}")
if objects:
    first = objects[0]
    resp = mc.get_object(s.s3_bucket, first.object_name)
    data = resp.read()
    resp.close()
    resp.release_conn()
    print(f"retrievable: {first.object_name[:40]}… ({len(data)} bytes)")
print("strategy: DB rows are the metadata source of truth; bucket sync via mc mirror + versioning")
EOF

echo "=== 6. cleanup drill artifacts ==="
docker compose exec -T db psql -U petaccess -d petaccess -q -c \
  "DELETE FROM audit_log WHERE id='drill-marker-${STAMP}';"
docker compose exec -T db psql -U petaccess -d postgres -q -c "DROP DATABASE IF EXISTS ${RESTORE_DB};"
rm -f "$DUMP"
echo "=== BACKUP/RESTORE DRILL PASS ==="
