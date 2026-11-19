# Nyaya Legal AI — Windows startup
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = "1"

Write-Host "=== Nyaya Legal AI ===" -ForegroundColor Cyan

# Ollama
try {
    $tags = Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[1/2] Ollama running ($($tags.models.Count) model(s))."
} catch {
    Write-Host "[1/2] Starting Ollama..."
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 4
}

# Chroma index check
python -X utf8 -c @"
from core.retrieve import get_collection_stats
s = get_collection_stats()
if not s['ready'] or s['chunk_count'] == 0:
    print('[Nyaya] Building search index (first run may take several minutes)...')
    from core.chunk import build_vector_store
    build_vector_store(refresh=True)
else:
    print(f'[Nyaya] Index ready: {s[\"chunk_count\"]:,} chunks')
"@

Write-Host "[2/2] Starting API at http://localhost:8000 ..."
python -X utf8 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
