#!/usr/bin/env bash
# Lint backend (ruff) + check formatting. Usage: scripts/lint.sh
set -euo pipefail
cd "$(dirname "$0")/.."
uv run ruff check services/api services/worker tests scripts
uv run ruff format --check services/api services/worker tests scripts
