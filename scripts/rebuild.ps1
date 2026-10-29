# scripts/rebuild.ps1
# Полная пересборка всех образов и перезапуск стека.
# Использовать после правки settings.py, Dockerfile, requirements.txt.
$ErrorActionPreference = "Stop"

Write-Host "==> docker compose build --no-cache" -ForegroundColor Cyan
docker compose build

if ($LASTEXITCODE -ne 0) { throw "build failed" }

Write-Host "==> docker compose up -d" -ForegroundColor Cyan
docker compose up -d

if ($LASTEXITCODE -ne 0) { throw "up failed" }

Write-Host "==> docker compose ps" -ForegroundColor Cyan
docker compose ps