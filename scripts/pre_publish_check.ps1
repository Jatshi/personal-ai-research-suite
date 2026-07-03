$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path
Push-Location $root

$badDirs = Get-ChildItem -Recurse -Force -Directory modules | Where-Object {
    $_.Name -in @("data", ".pytest_cache", "__pycache__") -or $_.Name -like "*.egg-info"
}
$badFiles = Get-ChildItem -Recurse -Force -File . | Where-Object {
    $_.Extension -in @(".pyc", ".pyo") -or
    $_.Name -eq ".env" -or
    $_.Name -eq "rag.sqlite" -or
    $_.FullName -match "\\data\\logs\\" -or
    $_.FullName -match "\\data\\indexes\\" -or
    $_.FullName -match "\\data\\raw\\"
}

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
    module_file_count = (Get-ChildItem -Recurse -File modules).Count
}

$result | ConvertTo-Json -Depth 4 | Write-Host

if (-not $result.success) {
    if ($badDirs.Count -gt 0) {
        Write-Host "Bad directories:"
        $badDirs.FullName | Write-Host
    }
    if ($badFiles.Count -gt 0) {
        Write-Host "Bad files:"
        $badFiles.FullName | Write-Host
    }
    Pop-Location
    exit 1
}

Pop-Location
