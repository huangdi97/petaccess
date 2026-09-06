#!/usr/bin/env sh
set -eu

[ -f .env ] || cp .env.example .env
[ -d .git ] || git init

mkdir -p   apps/client apps/admin   services/api services/worker   packages/rule-spec packages/api-client packages/design-tokens   infra/docker infra/migrations   tests/contract tests/integration tests/e2e

echo "Base directories ready. Give ZCode ZCODE_START_PROMPT.md."
