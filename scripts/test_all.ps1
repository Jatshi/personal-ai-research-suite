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
    if ($LASTEXITCODE -ne 0) {
        throw "Tests failed for $project with exit code $LASTEXITCODE."
    }
    Pop-Location
}

$webDir = Join-Path $root "apps\web"
if (Test-Path (Join-Path $webDir "package.json")) {
    Write-Host "Building ScholarMind web workbench"
    Push-Location $webDir
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "Next.js production build failed with exit code $LASTEXITCODE."
    }
    Pop-Location
}
