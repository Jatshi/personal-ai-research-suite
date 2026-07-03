$ErrorActionPreference = "Stop"

$root = (Resolve-Path "$PSScriptRoot\..").Path

Write-Host "== personal-academic-rag-workspace =="
Push-Location (Join-Path $root "modules\personal-academic-rag-workspace")
python -m src.cli doctor-config
python -m src.cli doctor-llm
Pop-Location

Write-Host "== personal-agent-workspace =="
Push-Location (Join-Path $root "modules\personal-agent-workspace")
python -m src.cli scan-files --path messy_files | Out-Host
Pop-Location

Write-Host "== personal-ai-workspace =="
Push-Location (Join-Path $root "modules\personal-ai-workspace")
python -m src.cli doctor-config
python -m src.cli doctor-llm
Pop-Location

Write-Host "== local-mcp-toolkit =="
Push-Location (Join-Path $root "modules\local-mcp-toolkit")
python -m src.cli doctor-config
python -m src.cli doctor-mcp
python -m src.cli doctor-rag
Pop-Location
