#!/usr/bin/env bash
# Infra up + migrations + synthetic seed. Usage: scripts/dev.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then cp .env.example .env; fi
docker compose up -d
echo "Waiting for postgres health..."
for i in $(seq 1 60); do
  if docker compose exec -T db pg_isready -U petaccess -d petaccess >/dev/null 2>&1; then break; fi
  sleep 2
done

pushd services/api >/dev/null
uv run alembic upgrade head
popd >/dev/null

uv run python -m app.db.seed --demo
echo "Dev environment ready: API → uv run uvicorn app.main:app --reload (port 8000)"
