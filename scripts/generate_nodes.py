#!/usr/bin/env python3
"""Генерация docker-compose.yml для N узлов.

Usage:
    python scripts/generate_nodes.py 3 > docker-compose.yml
"""
import sys
from pathlib import Path

try:
    from jinja2 import Template
except ImportError:
    print("pip install jinja2", file=sys.stderr)
    sys.exit(1)

TMPL = '''services:
  portal:
    build: .
    env_file: .env
    environment:
      NODE_ROLE: portal
      NODE_ID: portal
    ports: ["8080:8000"]

{% for i in range(n) %}
  clinic{{ i }}:
    build: .
    env_file: .env
    environment:
      NODE_ROLE: clinic
      NODE_ID: clinic{{ i }}
      DATABASE_URL: postgres://clinic:clinic@db{{ i }}:5432/clinic
    depends_on: [db{{ i }}]

  db{{ i }}:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: clinic
      POSTGRES_USER: clinic
      POSTGRES_PASSWORD: clinic
    volumes:
      - pgdata{{ i }}:/var/lib/postgresql/data
{% endfor %}

volumes:
{% for i in range(n) %}
  pgdata{{ i }}:
{% endfor %}
'''

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    print(Template(TMPL).render(n=n))

if __name__ == "__main__":
    main()