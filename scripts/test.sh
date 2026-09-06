#!/usr/bin/env bash
# Run all backend tests. Usage: scripts/test.sh [pytest args]
set -euo pipefail
cd "$(dirname "$0")/.."
uv run pytest "${@:--q}"
