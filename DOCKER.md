# Docker: запуск демо (портал + 3 узла)

## Что где

| Сервис | URL | БД |
|---|---|---|
| portal | http://localhost:8080 | portal |
| node0  | http://localhost:8081 | node0 |
| node1  | http://localhost:8082 | node1 |
| node2  | http://localhost:8083 | node2 |
| db     | внутри сети `db:5432` (наружу не публикуется) | — |

Один контейнер `postgres:16-alpine`, четыре БД (`portal`, `node0..2`),
создаются из `docker/initdb/01-databases.sql` при **первом** старте тома.

## Быстрые команды (PowerShell, из корня проекта)

| Задача | Команда |
|---|---|
| Первый запуск / после правки `settings.py`, `Dockerfile`, `requirements.txt` | `.\scripts\rebuild.ps1` |
| Просто перезапустить (после падения, правки `.env`) | `.\scripts\restart.ps1` |
| Остановить | `.\scripts\stop.ps1` |
| Запустить обратно | `.\scripts\start.ps1` |
| Полный сброс (данные пропадут) | `.\scripts\reset.ps1` |
| Логи всех сервисов | `docker compose logs -f --tail=100` |
| Логи одного сервиса | `docker compose logs -f portal` |
| Статус | `docker compose ps` |
| Shell Django на портале | `docker compose exec portal python manage.py shell` |
| Shell Django на узле | `docker compose exec node0 python manage.py shell` |
| psql в БД узла | `docker compose exec db psql -U clinic -d node0` |
| Список БД | `docker compose exec db psql -U clinic -d portal -c "\l"` |
| Проверить движок БД | `docker compose exec portal python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'], settings.DATABASES['default']['NAME'])"` |

## Что требует пересборки, а что нет

- Правка `config/settings.py`, `Dockerfile`, `requirements.txt`, любых `.py` — **нужен** `rebuild.ps1`, потому что код копируется в образ (`COPY . .`) и volume'ом не смонтирован.
- Правка `.env` — достаточно `restart.ps1` (переменные читаются при старте).
- Правка `docker-compose.yml` — `docker compose up -d` (без `--build`, если образы не менялись).

Если хочется итеративной разработки без пересборки на каждую правку `.py` — добавьте в `docker-compose.yml` для `portal` и узлов:

```yaml
    volumes:
      - .:/app