$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
Push-Location $root

# Inspect Git publication candidates rather than all local runtime artifacts. Test
# runs legitimately create ignored data/, cache/, and pyc files in a developer tree.
$publishCandidates = @(git ls-files -co --exclude-standard)
$badFiles = @($publishCandidates | Where-Object {
    $path = $_ -replace "/", "\\"
    $path -match "(^|\\)(\.env|\.pytest_cache|__pycache__)(\\|$)" -or
    $path -match "\.egg-info(\\|$)" -or
    $path -match "\.(pyc|pyo)$" -or
    $path -match "(^|\\)modules\\[^\\]+\\data\\(logs|indexes|metadata|raw)(\\|$)" -or
    $path -match "(^|\\)modules\\[^\\]+\\data\\.*rag\.sqlite$"
})
$badDirs = @()

$requiredFiles = @(
    "README.md",
    ".env.example",
    ".gitignore",
    "docs\cn\SYSTEM_OVERVIEW.md",
    "docs\en\SYSTEM_OVERVIEW.md",
    "modules\personal-ai-workspace\run_production_check.ps1",
    "modules\local-mcp-toolkit\run_bridge_check.ps1",
    "modules\local-mcp-toolkit\config.local_project.production.yaml"
)

$missing = @()
foreach ($path in $requiredFiles) {
    if (-not (Test-Path $path)) {
        $missing += $path
    }
}

$result = [ordered]@{
    success = (($badDirs.Count -eq 0) -and ($badFiles.Count -eq 0) -and ($missing.Count -eq 0))
    bad_dir_count = $badDirs.Count
    bad_file_count = $badFiles.Count
    missing_required_files = $missing
    doc_count = (Get-ChildItem -Recurse -File docs).Count
    module_file_count = @($publishCandidates | Where-Object { $_ -like "modules/*" }).Count
}

$result | ConvertTo-Json -Depth 4 | Write-Host

if (-not $result.success) {
    if ($badDirs.Count -gt 0) {
        Write-Host "Bad directories:"
        $badDirs | Write-Host
    }
    if ($badFiles.Count -gt 0) {
        Write-Host "Bad files:"
        $badFiles | Write-Host
    }
    Pop-Location
    exit 1
}

Pop-Location
