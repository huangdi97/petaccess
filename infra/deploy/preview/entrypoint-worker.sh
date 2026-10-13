#!/bin/sh
set -eu

petaccess-preview-env-check

cd /app/services/api

exec celery -A app.worker.celery_app worker \
  --beat \
  --loglevel="\${CELERY_LOG_LEVEL:-INFO}" \
  --concurrency="\${CELERY_CONCURRENCY:-2}" \
  --schedule=/tmp/petaccess-preview-celerybeat
