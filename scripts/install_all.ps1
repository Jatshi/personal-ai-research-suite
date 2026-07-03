$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
$projects = @(
    "personal-academic-rag-workspace",
    "personal-agent-workspace",
    "personal-ai-workspace",
    "local-mcp-toolkit"
)

foreach ($project in $projects) {
    $dir = Join-Path $root "modules\$project"
    Write-Host "Installing $project"
    Push-Location $dir
    python -m pip install -r requirements.txt
    if (Test-Path "requirements-production.txt") {
        python -m pip install -r requirements-production.txt
    }
    if (Test-Path "pyproject.toml") {
        python -m pip install -e ".[dev]"
    }
    Pop-Location
}
