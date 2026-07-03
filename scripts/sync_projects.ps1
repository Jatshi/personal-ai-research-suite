param(
    [string]$SourceRoot = (Resolve-Path "$PSScriptRoot\..\..").Path,
    [string]$TargetRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"

$projects = @(
    "personal-academic-rag-workspace",
    "personal-agent-workspace",
    "personal-ai-workspace",
    "local-mcp-toolkit"
)

$rootExcludeDirs = @(
    "data",
    "workspace"
)

$segmentExcludeDirs = @(
    ".git",
    ".pytest_cache",
    "__pycache__",
    "personal_ai_workspace.egg-info",
    "local_mcp_toolkit.egg-info"
)

function Test-ExcludedPath {
    param([string]$RelativePath)
    $normalized = $RelativePath.Replace("/", "\")
    foreach ($pattern in $rootExcludeDirs) {
        if ($normalized -eq $pattern -or $normalized.StartsWith("$pattern\")) {
            return $true
        }
    }
    foreach ($pattern in $segmentExcludeDirs) {
        if ($normalized -eq $pattern -or $normalized.StartsWith("$pattern\") -or $normalized.Contains("\$pattern\") -or $normalized.EndsWith("\$pattern")) {
            return $true
        }
    }
    return $false
}

$modulesDir = Join-Path $TargetRoot "modules"
New-Item -ItemType Directory -Force -Path $modulesDir | Out-Null

foreach ($project in $projects) {
    $source = Join-Path $SourceRoot $project
    $target = Join-Path $modulesDir $project
    if (-not (Test-Path $source)) {
        throw "Missing source project: $source"
    }
    if (Test-Path $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $target | Out-Null

    Get-ChildItem -LiteralPath $source -Recurse -Force | ForEach-Object {
        $relative = $_.FullName.Substring($source.Length).TrimStart("\")
        if (-not $relative) { return }
        if (Test-ExcludedPath $relative) { return }
        if ($_.Name -eq ".env") { return }
        if ($_.Extension -in @(".pyc", ".pyo")) { return }
        $dest = Join-Path $target $relative
        if ($_.PSIsContainer) {
            New-Item -ItemType Directory -Force -Path $dest | Out-Null
        } else {
            New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $dest -Force
        }
    }
    Write-Host "Synced $project -> $target"
}
