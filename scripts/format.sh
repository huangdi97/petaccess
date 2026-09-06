#!/usr/bin/env bash
# Auto-format backend. Usage: scripts/format.sh
set -euo pipefail
cd "$(dirname "$0")/.."
uv run ruff format services/api services/worker tests
uv run ruff check --fix services/api services/worker tests
