# db

Postgres 18 schema for Shuqiao. Applied with plain SQL migrations under
`migrations/`, in numbered order.

## Applying

Against the compose database (host port 5440):

    psql -h localhost -p 5440 -U shuqiao -d shuqiao -v ON_ERROR_STOP=1 \
        -f migrations/0001_concepts.sql

From this repo without a local psql, pipe it through the compose container:

    docker compose -f ../.worktrees/SHU-12/compose.yaml exec -T db \
        psql -U shuqiao -d shuqiao -v ON_ERROR_STOP=1 \
        < migrations/0001_concepts.sql

Migrations are idempotent (`CREATE TABLE IF NOT EXISTS` /
`CREATE INDEX IF NOT EXISTS`); rerunning one is a safe no-op.
