#!/usr/bin/env bash
# Type check backend. Usage: scripts/typecheck.sh
set -euo pipefail
cd "$(dirname "$0")/.."
uv run mypy services/api/app
