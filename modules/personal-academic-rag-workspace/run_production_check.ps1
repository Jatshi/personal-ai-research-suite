param(
    [switch]$CallApi
)

$ErrorActionPreference = "Stop"

if (-not $env:PERSONAL_ACADEMIC_RAG_CONFIG) {
    $env:PERSONAL_ACADEMIC_RAG_CONFIG = "config.production.yaml"
}

Write-Host "Using config: $env:PERSONAL_ACADEMIC_RAG_CONFIG"
Write-Host "Running config diagnostics..."
python -m src.cli doctor-config

Write-Host "Running LLM/embedding diagnostics..."
if ($CallApi) {
    python -m src.cli doctor-llm --call-api
} else {
    python -m src.cli doctor-llm
    Write-Host "Skipped live API call. Re-run with -CallApi after setting OPENAI_API_KEY to verify the provider end-to-end."
}

Write-Host "Running sample search path. This requires an existing production index."
python -m src.cli search --query "RAG" --mode hybrid --top-k 3
