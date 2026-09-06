$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}
if (-not (Test-Path ".git")) {
  git init
}

$dirs = @(
  "apps/client","apps/admin",
  "services/api","services/worker",
  "packages/rule-spec","packages/api-client","packages/design-tokens",
  "infra/docker","infra/migrations",
  "tests/contract","tests/integration","tests/e2e"
)
foreach ($d in $dirs) {
  New-Item -ItemType Directory -Force -Path $d | Out-Null
}

Write-Host "Base directories ready. Give ZCode ZCODE_START_PROMPT.md."
