# scripts/reset.ps1
# ВНИМАНИЕ: удаляет том pgdata — все данные БД будут потеряны.
$ErrorActionPreference = "Stop"

$answer = Read-Host "Удалить том pgdata и все данные? [y/N]"
if ($answer -ne "y") { Write-Host "Отменено"; exit 0 }

Write-Host "==> docker compose down -v" -ForegroundColor Yellow
docker compose down -v

Write-Host "==> docker compose up -d --build" -ForegroundColor Cyan
docker compose up -d --build

docker compose ps