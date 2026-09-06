# Windows PowerShell equivalents of scripts/*.sh (see README).

function Invoke-Dev {
    if (-not (Test-Path .env)) { Copy-Item .env.example .env }
    docker compose up -d
    Push-Location services/api
    uv run alembic upgrade head
    Pop-Location
    uv run python -m app.db.seed --demo
    Write-Host "Dev environment ready: uv run uvicorn app.main:app --reload"
}

function Invoke-Test { uv run pytest @args -q }
function Invoke-Lint {
    uv run ruff check services/api services/worker tests
    uv run ruff format --check services/api services/worker tests
}
function Invoke-Format {
    uv run ruff format services/api services/worker tests
    uv run ruff check --fix services/api services/worker tests
}
function Invoke-Typecheck { uv run mypy services/api/app }
function Invoke-Migrate {
    Push-Location services/api
    uv run alembic upgrade head @args
    Pop-Location
}
