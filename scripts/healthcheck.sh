#!/usr/bin/env bash
# Check infra health: Postgres+PostGIS / Redis / MinIO. Usage: scripts/healthcheck.sh
set -uo pipefail
cd "$(dirname "$0")/.."
STATUS=0
uv run python - <<'EOF' || STATUS=1
from app.db.session import check_db_health
print("db:", check_db_health())
EOF

redis-cli -u redis://localhost:6379/0 ping >/dev/null 2>&1 \
  && echo "redis: PONG" || { echo "redis: UNREACHABLE"; STATUS=1; }

curl -sf http://localhost:9000/minio/health/live >/dev/null 2>&1 \
  && echo "minio: live" || { echo "minio: UNREACHABLE"; STATUS=1; }

exit $STATUS
