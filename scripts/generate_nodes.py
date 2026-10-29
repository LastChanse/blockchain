#!/usr/bin/env python3
"""Генерация docker-compose.yml для N узлов клиник.

Usage:
    python scripts/generate_nodes.py 3 > docker-compose.yml

Схема: один Postgres, БД portal + node0..node(N-1),
портал на 8080, узлы на 8081..8080+N.
"""
import sys
from pathlib import Path

HEADER = """\
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: portal
      POSTGRES_USER: clinic
      POSTGRES_PASSWORD: clinic
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./docker/initdb:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U clinic -d portal"]
      interval: 3s
      timeout: 3s
      retries: 20
    command: >
      postgres
      -c shared_buffers=128MB
      -c max_connections=40
      -c fsync=off
      -c synchronous_commit=off
      -c full_page_writes=off

  portal:
    build: .
    env_file: .env
    environment:
      NODE_ROLE: portal
      NODE_ID: portal
      DATABASE_URL: postgres://clinic:clinic@db:5432/portal
    ports: ["8080:8000"]
    depends_on:
      db: { condition: service_healthy }
    restart: unless-stopped
"""

NODE = """
  node{i}:
    build: .
    env_file: .env
    environment:
      NODE_ROLE: clinic
      NODE_ID: node{i}
      DATABASE_URL: postgres://clinic:clinic@db:5432/node{i}
    ports: ["{port}:8000"]
    depends_on:
      db: {{ condition: service_healthy }}
    restart: unless-stopped
"""

FOOTER = """
volumes:
  pgdata:
"""


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    if n < 1:
        sys.exit("n must be >= 1")
    out = [HEADER]
    for i in range(n):
        out.append(NODE.format(i=i, port=8081 + i))
    out.append(FOOTER)
    sys.stdout.write("".join(out))

    ROOT = Path(__file__).resolve().parent.parent
    with open(ROOT / "docker/initdb/01-databases.sql", "w", encoding="utf-8") as f:
        f.write("".join(f"CREATE DATABASE node{i};\n" for i in range(n)))


if __name__ == "__main__":
    main()