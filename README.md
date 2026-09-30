## Установка

### 1. uv и Python 3.14

    # Linux / macOS
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows (PowerShell)
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

Обновить PATH (Windows, текущая сессия):

    $env:Path = "C:\Users\<User>\.local\bin;$env:Path"

Установить Python:

    uv python install 3.14 --default

### 2. venv и зависимости

    cd clinic-consortium
    uv venv --python 3.14 --seed

    # Linux / macOS
    source .venv/bin/activate
    # Windows (PowerShell)
    .venv\Scripts\Activate.ps1

    python -m pip install -r requirements.txt

### 3. .env

    cp .env.example .env

Сгенерировать ключ и вписать в `.env`:

    python -c "import secrets; print(secrets.token_urlsafe(64))"

### 4. Миграции

    python manage.py migrate

---

## Запуск локально (без Docker)

### Портал

    .\scripts\run-portal.ps1
    # http://127.0.0.1:8000/portal/

### Один узел клиники

    .\scripts\run-clinic.ps1 clinic0 8001
    # http://127.0.0.1:8001/clinic/

### Портал + 2 узла сразу

    .\scripts\run-all.ps1 -Nodes 2

---

## Запуск в Docker

### 1. Портал (один контейнер)

    docker compose -f docker-compose.portal.yml up --build -d

Портал: http://localhost:8080/portal/

### 2. Узлы (2 шт. вручную)

    docker compose up --build -d

### 3. Или N узлов через генератор

    python scripts/generate_nodes.py 3 > docker-compose.yml
    docker compose up --build -d

### 4. Проверка

    curl http://localhost:8080/portal/
    curl http://localhost:8080/clinic/
    curl http://localhost:8081/clinic/    # clinic0
    curl http://localhost:8082/clinic/    # clinic1

### 5. Остановка

    docker compose down

С удалением томов (БД):

    docker compose down -v

---

## Переменные окружения

| Переменная | Назначение | Пример |
|---|---|---|
| `DJANGO_SECRET_KEY` | Секрет Django (обязательно) | `...` |
| `DJANGO_DEBUG` | Режим отладки | `0` / `1` |
| `DJANGO_ALLOWED_HOSTS` | Разрешённые хосты | `localhost,127.0.0.1` |
| `NODE_ROLE` | Роль узла | `portal` / `clinic` |
| `NODE_ID` | Идентификатор узла | `clinic0` |
| `DATABASE_URL` | Подключение к PostgreSQL | `postgres://...` |

Для N узлов — по одному `envs/clinicN.env` на узел.