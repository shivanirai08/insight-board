#!/usr/bin/env bash
# Start local Postgres for InsightBoard (Podman or Docker).
# Prefer: podman compose / docker compose when the compose plugin is installed.
set -euo pipefail

NAME=insightboard-db
IMAGE=docker.io/library/postgres:16-alpine
VOLUME=insightboard_pgdata

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose up -d
  exit 0
fi

if command -v podman >/dev/null 2>&1 && podman compose version >/dev/null 2>&1; then
  podman compose up -d
  exit 0
fi

if command -v podman >/dev/null 2>&1; then
  echo "Compose plugin not found — starting with podman run…"
  podman volume create "$VOLUME" >/dev/null 2>&1 || true
  if podman container exists "$NAME"; then
    podman start "$NAME"
  else
    podman run -d \
      --name "$NAME" \
      -e POSTGRES_USER=insight \
      -e POSTGRES_PASSWORD=insight \
      -e POSTGRES_DB=insightboard \
      -p 5432:5432 \
      -v "$VOLUME:/var/lib/postgresql/data" \
      "$IMAGE"
  fi
  echo "Waiting for Postgres…"
  for _ in $(seq 1 30); do
    if podman exec "$NAME" pg_isready -U insight -d insightboard >/dev/null 2>&1; then
      echo "Postgres is ready on localhost:5432"
      exit 0
    fi
    sleep 1
  done
  echo "Postgres did not become ready in time" >&2
  exit 1
fi

echo "Neither docker nor podman found. Install one of them." >&2
exit 1
