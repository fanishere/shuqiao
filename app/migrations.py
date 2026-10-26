"""Tiny SQL migration runner: applies db/migrations/*.sql in filename
order, one transaction each, recording filenames in schema_migrations."""
import logging
from pathlib import Path

logger = logging.getLogger("shuqiao.migrations")

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "db" / "migrations"

_CREATE_REGISTRY = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


def apply_pending(conn) -> list[str]:
    """Apply pending migrations on the given connection; returns filenames."""
    conn.execute(_CREATE_REGISTRY)
    applied = {
        row[0]
        for row in conn.execute("SELECT filename FROM schema_migrations").fetchall()
    }
    migrated = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if path.name in applied:
            continue
        with conn.transaction():
            conn.execute(path.read_text())
            conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,)
            )
        migrated.append(path.name)
        logger.info("applied migration %s", path.name)
    return migrated
