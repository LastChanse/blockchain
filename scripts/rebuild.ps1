$ErrorActionPreference = "Stop"

Write-Host "==> docker compose up -d db" -ForegroundColor Cyan
docker compose up -d db

Write-Host "==> миграции" -ForegroundColor Cyan
docker compose up -d portal node0
Start-Sleep -Seconds 5
docker compose exec portal python manage.py makemigrations portal
docker compose exec node0 python manage.py makemigrations clinic

Write-Host "==> сборка и запуск" -ForegroundColor Cyan
docker compose up -d --build
docker compose ps