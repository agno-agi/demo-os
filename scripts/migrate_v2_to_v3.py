"""
Agno v2 -> v3 database migration
================================

Run once per environment (local, staging, prd) BEFORE serving traffic on agno 3.0.

Two independent migrations are required, and ``MigrationManager`` only covers the
first one:

1. **Agno-managed tables** (sessions, runs, learnings, schedules, knowledge
   ``*_contents``). ``MigrationManager(db).up()`` handles these. Each ``Knowledge``
   gets its own ``contents_db`` with a distinct ``knowledge_table``, so the manager
   has to be run once per contents table -- migrating the core db alone silently
   leaves them behind and the app fails to boot with ``MigrationRequiredError``.

2. **PgVector tables** (the ``vector_db`` behind each ``Knowledge``). These are NOT
   agno-managed and ``MigrationManager`` never touches them. v3 adds a nullable
   ``user_id`` column for per-user isolation; a table without it raises
   ``ValueError`` on any search that passes ``user_id`` -- which is every knowledge
   search once ``AuthorizationConfig(user_isolation=True)`` is on. Unscoped search
   keeps working, so this stays invisible until RBAC is enabled.

Both table sets are discovered from the live database rather than hardcoded, so an
environment holding knowledge bases this checkout does not define (or missing ones
it does) still migrates correctly.

Both steps are idempotent.

Usage:
    python -m scripts.migrate_v2_to_v3
    railway run python -m scripts.migrate_v2_to_v3   # against a Railway environment
"""

from __future__ import annotations

import asyncio

from agno.db.migrations.manager import MigrationManager
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from db.session import get_postgres_db
from db.url import db_url

SCHEMA = "ai"

# Tables agno owns directly. They are migrated through the core db handle, so they
# must not be mistaken for per-knowledge contents tables.
AGNO_TABLE_PREFIX = "agno_"


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
def discover_vector_tables(engine: Engine) -> list[str]:
    """PgVector tables: any table in the schema carrying a ``vector`` column.

    Detected structurally rather than by name -- the table name comes from
    whatever each ``create_knowledge()`` call passes, so a naming convention is
    not something this script can rely on.
    """
    sql = text(
        """
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
        JOIN pg_type t ON t.oid = a.atttypid
        WHERE n.nspname = :schema AND c.relkind = 'r' AND t.typname = 'vector'
        GROUP BY c.relname
        ORDER BY c.relname
        """
    )
    with engine.connect() as conn:
        return [row[0] for row in conn.execute(sql, {"schema": SCHEMA})]


def discover_contents_tables(engine: Engine) -> list[str]:
    """Knowledge contents tables: agno's contents schema, one per Knowledge.

    Identified by the column signature agno gives them (``linked_to`` plus
    ``access_count`` is unique to this table type), so the ``*_contents`` naming
    convention is not load-bearing. ``agno_``-prefixed tables are excluded --
    those belong to the core db handle and are migrated with it.
    """
    sql = text(
        """
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = :schema
          AND c.relkind = 'r'
          AND c.relname NOT LIKE :agno_prefix
          AND EXISTS (
              SELECT 1 FROM pg_attribute a
              WHERE a.attrelid = c.oid AND a.attname = 'linked_to'
                AND a.attnum > 0 AND NOT a.attisdropped
          )
          AND EXISTS (
              SELECT 1 FROM pg_attribute a
              WHERE a.attrelid = c.oid AND a.attname = 'access_count'
                AND a.attnum > 0 AND NOT a.attisdropped
          )
        ORDER BY c.relname
        """
    )
    with engine.connect() as conn:
        return [row[0] for row in conn.execute(sql, {"schema": SCHEMA, "agno_prefix": f"{AGNO_TABLE_PREFIX}%"})]


# ---------------------------------------------------------------------------
# Migrations
# ---------------------------------------------------------------------------
async def migrate_agno_tables(contents_tables: list[str]) -> None:
    """Migrate the core tables plus every discovered knowledge contents table."""
    # The core AgentOS db (sessions, runs, memories, schedules, learnings).
    await MigrationManager(get_postgres_db()).up()
    print("  ok  core agno tables")

    if not contents_tables:
        print("  --  no knowledge contents tables found")
    for table in contents_tables:
        await MigrationManager(get_postgres_db(knowledge_table=table)).up()
        print(f"  ok  {table}")


def migrate_vector_tables(engine: Engine, vector_tables: list[str]) -> None:
    """Add v3's nullable ``user_id`` column (and its index) to each PgVector table.

    Mirrors what ``PgVector.get_table_v1`` creates for a fresh v3 table. Existing
    rows keep ``user_id IS NULL`` -- the shared bucket -- so nothing is reassigned.
    """
    if not vector_tables:
        print("  --  no PgVector tables found (agno creates them with user_id on first use)")
        return

    with engine.begin() as conn:
        for table in vector_tables:
            conn.execute(text(f'ALTER TABLE {SCHEMA}."{table}" ADD COLUMN IF NOT EXISTS user_id TEXT'))
            conn.execute(text(f'CREATE INDEX IF NOT EXISTS "idx_{table}_user_id" ON {SCHEMA}."{table}" (user_id)'))
            print(f"  ok  {table}")


def main() -> None:
    engine = create_engine(db_url)
    # Discovered up front so the plan is visible before anything is written.
    contents_tables = discover_contents_tables(engine)
    vector_tables = discover_vector_tables(engine)

    print("Agno v2 -> v3 migration")
    print(f"  schema:   {SCHEMA}")
    print(f"  contents: {', '.join(contents_tables) or 'none'}")
    print(f"  vector:   {', '.join(vector_tables) or 'none'}")

    print("\n[1/2] agno-managed tables")
    asyncio.run(migrate_agno_tables(contents_tables))

    print("\n[2/2] PgVector tables (user_id column)")
    migrate_vector_tables(engine, vector_tables)

    print("\nDone.")


if __name__ == "__main__":
    main()
