# scripts/restart.ps1
# Быстрый перезапуск контейнеров без пересборки образов.
# Использовать после правки шаблонов/вьюх, если код смонтирован volume'ом.
# Сейчас volume'а нет — правки кода требуют rebuild.ps1, а этот скрипт
# полезен для рестарта после падения или изменения .env.
$ErrorActionPreference = "Stop"

Write-Host "==> docker compose stop" -ForegroundColor Cyan
docker compose stop

Write-Host "==> docker compose start" -ForegroundColor Cyan
docker compose start

Write-Host "==> docker compose ps" -ForegroundColor Cyan
docker compose ps