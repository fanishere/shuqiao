#!/usr/bin/env bash
# Bring up the local dev stack: long-lived db container, host venv uvicorn API,
# and the Next.js dev server. Run from anywhere; operates on the repo root.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_CONTAINER="shuqiao-db"
DB_PORT=5440
API_PORT=8000
WEB_PORT=3000

command -v docker >/dev/null || { echo "docker is required"; exit 1; }

# 1. Long-lived postgres container on host port 5440.
if ! docker ps --format '{{.Names}}' | grep -qx "$DB_CONTAINER"; then
  if docker ps -a --format '{{.Names}}' | grep -qx "$DB_CONTAINER"; then
    docker start "$DB_CONTAINER"
  else
    docker run -d --name "$DB_CONTAINER" -p "${DB_PORT}":5432 \
      -e POSTGRES_USER=shuqiao -e POSTGRES_DB=shuqiao \
      -e POSTGRES_PASSWORD=devonly postgres:18
  fi
fi

DB_PASSWORD="$(docker inspect "$DB_CONTAINER" --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^POSTGRES_PASSWORD=//p')"
[ -n "$DB_PASSWORD" ] || { echo "could not read db password"; exit 1; }

# 2. Host venv with the API requirements.
if [ ! -x "$ROOT/.venv/bin/python" ]; then
  python3 -m venv "$ROOT/.venv"
fi
"$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements.txt"

# 3. uvicorn against the long-lived db, in the background.
( cd "$ROOT" && \
  SHUQIAO_SECRET_KEY=dev-secret \
  DATABASE_URL="postgresql://shuqiao:${DB_PASSWORD}@localhost:${DB_PORT}/shuqiao" \
  .venv/bin/uvicorn app.main:app --port "$API_PORT" ) &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT

# 4. Next.js dev server proxying to the API.
( cd "$ROOT/web" && \
  [ -d node_modules ] || npm install
  API_BASE_URL="http://localhost:${API_PORT}" npm run dev -- --port "$WEB_PORT" )
