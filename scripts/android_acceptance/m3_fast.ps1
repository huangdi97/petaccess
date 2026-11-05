$ErrorActionPreference = "Stop"

# Thin Windows entry point only. The canonical FAST implementation lives in
# m3_fast.py so route coverage, CDP semantics and screenshot timing cannot
# drift between two scripts.
$script = Join-Path $PSScriptRoot "m3_fast.py"
python $script
exit $LASTEXITCODE
