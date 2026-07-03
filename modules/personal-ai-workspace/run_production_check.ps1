param(
    [switch]$CallApi,
    [switch]$AllowMissingSecrets
)

$ErrorActionPreference = "Stop"

if (-not $env:PERSONAL_AI_CONFIG) {
    $env:PERSONAL_AI_CONFIG = "config.production.yaml"
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

$allowSecretFailure = [bool]$AllowMissingSecrets

Write-Host "Using PERSONAL_AI_CONFIG=$env:PERSONAL_AI_CONFIG"

Invoke-JsonCheck "doctor-config" @("python", "-m", "src.cli", "doctor-config") -AllowFailure:$allowSecretFailure

if ($CallApi) {
    Invoke-JsonCheck "doctor-llm-live-api" @("python", "-m", "src.cli", "doctor-llm", "--call-api") -AllowFailure:$allowSecretFailure
} else {
    Invoke-JsonCheck "doctor-llm-provider" @("python", "-m", "src.cli", "doctor-llm") -AllowFailure:$allowSecretFailure
    Write-Host "Skipped live API call. Re-run with -CallApi after setting OPENAI_API_KEY."
}

Write-Host "Production check finished."
