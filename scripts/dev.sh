#!/usr/bin/env bash
# Bring up the local dev stack: long-lived db container, host venv uvicorn API,
# and the Next.js dev server. WEB_PORT/API_PORT/DB_NAME override the web port,
# API port, and database name; distinct values let concurrent runs (e.g. two
# agents) share the one db container without sharing data.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_CONTAINER="shuqiao-db"
DB_PORT=5440
API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"
DB_NAME="${DB_NAME:-shuqiao}"

command -v docker >/dev/null || { echo "docker is required"; exit 1; }

# The db container is long-lived on purpose; reuse it across runs.
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

# Idempotent: concurrent first-runs race here, so tolerate the "already
# exists" case rather than checking first.
docker exec "$DB_CONTAINER" psql -U shuqiao -d shuqiao -tc \
  "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
  docker exec "$DB_CONTAINER" createdb -U shuqiao "$DB_NAME"

if [ ! -x "$ROOT/.venv/bin/python" ]; then
  python3 -m venv "$ROOT/.venv"
fi
"$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements.txt"

# exec so $API_PID is uvicorn itself; a wrapping subshell would swallow the
# EXIT trap's signal and leave uvicorn holding the port.
(
  cd "$ROOT"
  export SHUQIAO_SECRET_KEY="${SHUQIAO_SECRET_KEY:-dev-secret}"
  export DATABASE_URL="postgresql://shuqiao:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}"
  exec .venv/bin/uvicorn app.main:app --port "$API_PORT"
) &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT

(
  cd "$ROOT/web"
  [ -d node_modules ] || npm install
  export API_BASE_URL="http://localhost:${API_PORT}"
  # Per-run dist dir: next dev locks inside distDir, and two servers in one
  # web/ checkout must not share .next. Web port is unique per run.
  export NEXT_DIST_DIR=".next-dev-${WEB_PORT}"
  npm run dev -- --port "$WEB_PORT"
)
