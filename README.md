# Blockchain консорциум клиник

Django + PostgreSQL: портал пациента и три узла клиник с обменом цепочками по HTTP.

## Навигация

1. [Архитектура](#1-архитектура)
2. [Требования](#2-требования)
3. [Быстрый старт](#3-быстрый-старт)
4. [Структура проекта](#4-структура-проекта)
5. [Docker: команды](#5-docker-команды)
6. [Тесты и сценарии](#6-тесты-и-сценарии)
7. [API](#7-api)

---

## 1. Архитектура

| Сервис | Роль | URL | БД |
|---|---|---|---|
| portal | регистрация, список клиник | http://localhost:8080 | portal |
| node0  | узел клиники 0 | http://localhost:8081 | node0 |
| node1  | узел клиники 1 | http://localhost:8082 | node1 |
| node2  | узел клиники 2 | http://localhost:8083 | node2 |
| db     | PostgreSQL 16 (4 БД) | внутренняя сеть `db:5432` | — |

- Один `postgres:16-alpine`, четыре БД (`portal`, `node0..2`) создаются из `docker/initdb/01-databases.sql` при первом старте тома.
- Портал синхронизирует пользователей во все узлы: `POST /clinic/internal/users`.
- Узлы синхронизируют цепочки: `sync_chain` → `GET /clinic/network/height`, `GET /clinic/network/blocks`, `POST /clinic/network/blocks`.
- Внутренние вызовы защищены заголовком `X-Internal-Token` (значение `INTERNAL_SYNC_TOKEN` из `.env`).

## 2. Требования

- Docker Desktop (Windows/macOS/Linux) с Docker Compose v2.
- PowerShell 5+ (Windows) или bash (Linux/macOS).
- Свободные порты `8080..8083`.

## 3. Быстрый старт

Из корня проекта:

```powershell
copy .env.example .env
docker compose build
docker compose up -d
docker compose ps
```

Ожидаемо: 5 контейнеров в состоянии `running` (db — `healthy`).

Проверка в браузере:
- портал — http://localhost:8080/portal/
- клиника 0 — http://localhost:8081/clinic/
- клиника 1 — http://localhost:8082/clinic/
- клиника 2 — http://localhost:8083/clinic/

Регистрация и вход: зарегистрируйтесь на портале (`/portal/register/`), затем войдите с теми же учётными данными в любой клинике. Пользователь синхронизируется во все узлы автоматически.

## 4. Структура проекта

```
blockchain-dev/
│
├── clinic/                              # Приложение «Клиника»
│   ├── migrations/
│   ├── templates/clinic/
│   ├── management/commands/sync_chain.py
│   ├── internal_views.py                # POST /internal/users
│   ├── network_views.py                 # /network/height, /network/blocks
│   ├── models.py                        # ChainBlock, DoctorProfile
│   ├── services.py                      # цепочка, валидация, sync-хелперы
│   ├── urls.py
│   └── views.py
│
├── config/                              # Настройки Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── portal/                              # Приложение «Портал пациента»
│   ├── migrations/
│   ├── templates/portal/
│   ├── models.py                        # Clinic
│   ├── urls.py
│   └── views.py
│
├── scripts/                             # PowerShell-утилиты
│   ├── generate_nodes.py
│   ├── rebuild.ps1
│   ├── restart.ps1
│   ├── stop.ps1
│   ├── start.ps1
│   └── reset.ps1
│
├── static/                              # CSS, JS
│   ├── css/style.css
│   └── js/{api.js,crypto.js}
│
├── docker/initdb/01-databases.sql
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── README.md
├── API.md
└── requirements.txt
```

## 5. Docker: команды

Все команды — из корня проекта.

| Задача | Команда |
|---|---|
| Первый запуск / после правки `.py`, `Dockerfile`, `requirements.txt` | `.\scripts\rebuild.ps1` |
| Перезапуск без пересборки (после правки `.env`) | `.\scripts\restart.ps1` |
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

Правило: правка `.py`/`Dockerfile`/`requirements.txt` → `rebuild.ps1`. Правка `.env` → `restart.ps1`. Правка `docker-compose.yml` → `docker compose up -d`.

Для итеративной разработки без пересборки добавьте в `docker-compose.yml` для `portal` и узлов:

```yaml
    volumes:
      - .:/app
```

## 6. Тесты и сценарии

Все команды — из корня проекта. `TOKEN` ниже — значение `INTERNAL_SYNC_TOKEN` из `.env` (по умолчанию `change-me-internal-token`).

### Тест 1 — позитив: блок доезжает до другой ноды

**Что делаем:** создаём запись на `node0` и синхронизируем `node1`.

```powershell
docker compose exec node0 python manage.py shell -c "from clinic import services; print('node0 height:', services.local_height())"
docker compose exec node1 python manage.py sync_chain
docker compose exec node1 python manage.py shell -c "from clinic import services; print('node1 height:', services.local_height()); print('valid:', services.validate_chain())"
```

**Что получаем:** `node0 height: N`, затем `accepted block ...`, затем `node1 height: N` и `valid: (True, None)`.

### Тест 2 — негатив: подменённый хеш

**Что делаем:** берём блок `index=1` с `node0`, подменяем `hash` на `"0"*64` и отправляем POST на `node1`.

```powershell
docker compose exec node0 python manage.py shell -c "import requests; from clinic.models import ChainBlock; b=ChainBlock.objects.get(index=1); d={'index':b.index,'prev_hash':b.prev_hash,'type':b.type,'timestamp':b.timestamp,'content_hash':b.content_hash,'payload':b.payload,'hash':'0'*64}; r=requests.post('http://node1:8000/clinic/network/blocks',headers={'X-Internal-Token':'change-me-internal-token'},json=d); print(r.status_code, r.text)"
```

**Что получаем:** `400 {"ok": false, "error": "hash mismatch: sent=0000…, computed=…"}`.

### Тест 3 — негатив: неверный `prev_hash`

**Что делаем:** подменяем `prev_hash` на `"0"*64`.

```powershell
docker compose exec node0 python manage.py shell -c "import requests; from clinic.models import ChainBlock; b=ChainBlock.objects.get(index=1); d={'index':b.index,'prev_hash':'0'*64,'type':b.type,'timestamp':b.timestamp,'content_hash':b.content_hash,'payload':b.payload,'hash':b.hash}; r=requests.post('http://node1:8000/clinic/network/blocks',headers={'X-Internal-Token':'change-me-internal-token'},json=d); print(r.status_code, r.text)"
```

**Что получаем:** `400 {"ok": false, "error": "prev_hash mismatch: expected …, got …"}`.

### Тест 4 — негатив: разрыв индекса

**Что делаем:** подменяем `index` на `local_height + 2`.

```powershell
docker compose exec node0 python manage.py shell -c "import requests; from clinic.models import ChainBlock; b=ChainBlock.objects.get(index=1); d={'index':b.index+2,'prev_hash':b.prev_hash,'type':b.type,'timestamp':b.timestamp,'content_hash':b.content_hash,'payload':b.payload,'hash':b.hash}; r=requests.post('http://node1:8000/clinic/network/blocks',headers={'X-Internal-Token':'change-me-internal-token'},json=d); print(r.status_code, r.text)"
```

**Что получаем:** `400 {"ok": false, "error": "index gap: expected …, got …"}`.

### Тест 5 — негатив: подменённый `payload`

**Что делаем:** для `medical_record` меняем `payload` (но оставляем старый `content_hash`).

```powershell
docker compose exec node0 python manage.py shell -c "import requests; from clinic.models import ChainBlock; b=ChainBlock.objects.get(index=1); p=dict(b.payload); p['diagnosis']='HACKED'; d={'index':b.index,'prev_hash':b.prev_hash,'type':b.type,'timestamp':b.timestamp,'content_hash':b.content_hash,'payload':p,'hash':b.hash}; r=requests.post('http://node1:8000/clinic/network/blocks',headers={'X-Internal-Token':'change-me-internal-token'},json=d); print(r.status_code, r.text)"
```

**Что получаем:** `400 {"ok": false, "error": "hash mismatch: …"}` или `content_hash mismatch` — в зависимости от того, что пересчитается первым.

### Тест 6 — негатив: неверный токен

**Что делаем:** запрашиваем `/height` с неверным `X-Internal-Token`.

```powershell
docker compose exec node0 python manage.py shell -c "import requests; r=requests.get('http://node1:8000/clinic/network/height',headers={'X-Internal-Token':'wrong'}); print(r.status_code, r.text)"
```

**Что получаем:** `403 {"error": "forbidden"}`.

### Тест 7 — проверка целостности цепочки

**Что делаем:** прогоняем валидацию цепочки на каждом узле.

```powershell
docker compose exec node0 python manage.py shell -c "from clinic import services; print('node0:', services.validate_chain())"
docker compose exec node1 python manage.py shell -c "from clinic import services; print('node1:', services.validate_chain())"
docker compose exec node2 python manage.py shell -c "from clinic import services; print('node2:', services.validate_chain())"
```

**Что получаем:** `node0: (True, None)`, `node1: (True, None)`, `node2: (True, None)`.

## 7. API

Полное описание эндпоинтов, форматов запросов/ответов и кодов ошибок — в [API.md](API.md).