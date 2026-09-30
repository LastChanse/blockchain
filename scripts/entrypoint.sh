#!/usr/bin/env bash
set -e

export NODE_ID="${NODE_ID:-$(hostname)}"

echo "NODE_ROLE=${NODE_ROLE} NODE_ID=${NODE_ID}"

python manage.py migrate --noinput

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-2}"