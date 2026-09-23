# qa_all.ps1 — one command for the whole quality gate (Windows / PowerShell).
#
#   pwsh -File scripts/qa_all.ps1
#   pwsh -File scripts/qa_all.ps1 -SkipFrontend   # backend only
#   pwsh -File scripts/qa_all.ps1 -SkipPlaywright # skip the E2E suite
#
# Any failing step is recorded and the script exits non-zero. It does NOT stop at
# the first failure: the point of a gate is to show everything that is broken.
#
# Deliberately excluded: `publish --execute`, any real human signature, and
# anything that writes to the governed rule tables.

param(
    [switch]$SkipFrontend,
    [switch]$SkipPlaywright
)
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$py = if (Test-Path ".venv/Scripts/python.exe") { ".venv/Scripts/python.exe" } else { "python" }
$results = New-Object System.Collections.Generic.List[object]
$started = Get-Date

function Invoke-Step {
    param([string]$Name, [string[]]$Command)

    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $output = & $Command[0] $Command[1..($Command.Length - 1)] 2>&1
    $code = $LASTEXITCODE
    $sw.Stop()
    $output | Select-Object -Last 12 | ForEach-Object { Write-Host "    $_" }
    $status = if ($code -eq 0) { "PASS" } else { "FAIL" }
    $color = if ($code -eq 0) { "Green" } else { "Red" }
    Write-Host "  -> $Name : $status ($([int]$sw.Elapsed.TotalSeconds)s)" -ForegroundColor $color
    $results.Add([pscustomobject]@{ Step = $Name; Status = $status; Seconds = [int]$sw.Elapsed.TotalSeconds })
}

# ---------------------------------------------------------------- python -----
Invoke-Step "ruff check"        @($py, "-m", "ruff", "check", "services/api", "services/worker", "tests", "scripts")
Invoke-Step "ruff format check" @($py, "-m", "ruff", "format", "--check", "services/api", "services/worker", "tests", "scripts")
Invoke-Step "mypy (api app)"    @($py, "-m", "mypy", "services/api/app")
Invoke-Step "mypy (scripts)"    @($py, "-m", "mypy", "scripts/gen_human_review_packet_r2_final.py", "scripts/gen_signature_readiness_audit_r1.py", "scripts/human_decisions.py", "scripts/publish_reviewed_r1.py", "scripts/governance_snapshot.py", "scripts/mutation_probe.py")
Invoke-Step "pytest"            @($py, "-m", "pytest", "-q")
Invoke-Step "mutation probe"    @($py, "scripts/mutation_probe.py")

# ------------------------------------------------------- governance guard -----

Invoke-Step "engineering quality gate" @($py, "scripts/check_engineering_quality.py")
Invoke-Step "secret scan" @($py, "scripts/scan_secrets.py")
Invoke-Step "governance snapshot" @($py, "scripts/governance_snapshot.py", "--compare", "baseline")
# alembic.ini lives in services/api, so the migration check runs from there
Push-Location (Join-Path $root "services/api")
try {
    Invoke-Step "alembic current" @($py, "-m", "alembic", "current")
}
finally {
    Pop-Location
}

# --------------------------------------------------------------- frontend -----
if (-not $SkipFrontend) {
    Invoke-Step "eslint"   @("pnpm", "lint:fe")
    Invoke-Step "prettier" @("pnpm", "format:check:fe")
    Invoke-Step "h5 build" @("pnpm", "--filter", "@petaccess/client-h5", "build")
    # `admin:build` runs `vue-tsc --noEmit` first, so this is also the typecheck
    Invoke-Step "admin build (typecheck + build)" @("pnpm", "--filter", "@petaccess/admin", "build")
    if (-not $SkipPlaywright) {
        Invoke-Step "playwright" @("pnpm", "exec", "playwright", "test")
    }
}

# ------------------------------------------------------------------ report ----
$elapsed = (Get-Date) - $started
Write-Host "`n================ SUMMARY ================" -ForegroundColor Cyan
$results | Format-Table -AutoSize | Out-Host

$failed = @($results | Where-Object { $_.Status -eq "FAIL" })
if ($failed.Count -gt 0) {
    Write-Host "FAILED STEPS: $($failed.Step -join ', ')" -ForegroundColor Red
    Write-Host "Total: $($results.Count) steps, $($failed.Count) failed, elapsed $([int]$elapsed.TotalSeconds)s" -ForegroundColor Red
    exit 1
}

Write-Host "All $($results.Count) steps passed in $([int]$elapsed.TotalSeconds)s." -ForegroundColor Green
exit 0
