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
    Write-Host "Testing $project"
    Push-Location $dir
    if (Test-Path "run_tests.ps1") {
        .\run_tests.ps1
    } else {
        pytest -q
    }
    Pop-Location
}
