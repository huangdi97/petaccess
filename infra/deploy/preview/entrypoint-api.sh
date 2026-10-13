#!/bin/sh
set -eu

petaccess-preview-env-check

PORT="\${PORT:-8000}"

cd /app/services/api

if [ "\${PETACCESS_RUN_MIGRATIONS:-1}" = "1" ]; then
  echo "Applying PetAccess database migrations..." >&2
  alembic upgrade head
fi

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips="\${PETACCESS_FORWARDED_ALLOW_IPS:-*}"
