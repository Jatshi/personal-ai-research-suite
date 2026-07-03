param(
    [switch]$AllowMissingSecrets
)

$ErrorActionPreference = "Stop"

if (-not $env:LOCAL_MCP_CONFIG) {
    $env:LOCAL_MCP_CONFIG = "config.local_project.production.yaml"
}

function Invoke-JsonCheck {
    param(
        [string]$Label,
        [string[]]$Command,
        [switch]$AllowFailure
    )
    Write-Host "== $Label =="
    $output = & $Command[0] @($Command[1..($Command.Length - 1)])
    $output | Out-Host
    $json = $output | ConvertFrom-Json
    if (-not $json.success -and -not $AllowFailure) {
        throw "$Label failed"
    }
}

Write-Host "Using LOCAL_MCP_CONFIG=$env:LOCAL_MCP_CONFIG"
Invoke-JsonCheck "doctor-config" @("python", "-m", "src.cli", "doctor-config") -AllowFailure:$AllowMissingSecrets
Invoke-JsonCheck "doctor-mcp" @("python", "-m", "src.cli", "doctor-mcp") -AllowFailure:$AllowMissingSecrets
Invoke-JsonCheck "doctor-rag-bridge" @("python", "-m", "src.cli", "doctor-rag", "--query", "RAG") -AllowFailure:$AllowMissingSecrets
Write-Host "Bridge check finished."
