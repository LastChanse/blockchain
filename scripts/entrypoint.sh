#!/usr/bin/env bash
set -euo pipefail

: "${NODE_ROLE:=portal}"
: "${NODE_ID:=portal}"
export NODE_ROLE NODE_ID

echo "[entrypoint] role=${NODE_ROLE} id=${NODE_ID}"

# Ждём БД (psycopg3 умеет postgres:// URL напрямую)
if [[ -n "${DATABASE_URL:-}" ]]; then
  python - <<'PY'
import os, sys, time, psycopg
url = os.environ["DATABASE_URL"]
for attempt in range(60):
    try:
        with psycopg.connect(url, connect_timeout=2):
            print("[entrypoint] db ready"); break
    except Exception as e:
        print(f"[entrypoint] waiting for db ({attempt+1}/60): {e}", file=sys.stderr)
        time.sleep(1)
else:
    sys.exit("db not ready")
PY
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-1}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --access-logfile - \
  --error-logfile -