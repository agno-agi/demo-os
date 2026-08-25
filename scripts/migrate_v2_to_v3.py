"""
Agno v2 -> v3 database migration
================================

Run once per environment (local, staging, prd) BEFORE serving traffic on agno 3.0.

Two independent migrations are required, and ``MigrationManager`` only covers the
first one:

1. **Agno-managed tables** (sessions, runs, learnings, schedules, knowledge
   ``*_contents``). ``MigrationManager(db).up()`` handles these. Each ``Knowledge``
   gets its own ``contents_db`` with a distinct ``knowledge_table``, so the manager
   has to be run once per contents table -- migrating ``agent_db`` alone silently
   leaves them behind and the app fails to boot with ``MigrationRequiredError``.

2. **PgVector tables** (the ``vector_db`` behind each ``Knowledge``). These are NOT
   agno-managed and ``MigrationManager`` never touches them. v3 adds a nullable
   ``user_id`` column for per-user isolation; a table without it raises
   ``ValueError`` on any search that passes ``user_id`` -- which is every knowledge
   search once ``AuthorizationConfig(user_isolation=True)`` is on. Unscoped search
   keeps working, so this stays invisible until RBAC is enabled.

Both steps are idempotent.

Usage:
    python -m scripts.migrate_v2_to_v3
"""

from __future__ import annotations

import asyncio

from agno.db.migrations.manager import MigrationManager
from sqlalchemy import create_engine, inspect, text

from db.session import get_postgres_db
from db.url import db_url

# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
# Knowledge contents tables (agno-managed, one PostgresDb each).
CONTENTS_TABLES = [
    "clinic_records_contents",
    "coach_learnings_contents",
    "dash_knowledge_contents",
    "dash_learnings_contents",
    "investment_knowledge_contents",
    "investment_learnings_contents",
]

# PgVector tables (not agno-managed -- migrated by hand below).
VECTOR_TABLES = [
    "clinic_records",
    "coach_learnings",
    "dash_knowledge",
    "dash_learnings",
    "investment_knowledge",
    "investment_learnings",
]

SCHEMA = "ai"


# ---------------------------------------------------------------------------
# Migrations
# ---------------------------------------------------------------------------
async def migrate_agno_tables() -> None:
    """Migrate the core tables plus every knowledge contents table."""
    # The core AgentOS db (sessions, runs, memories, schedules, learnings).
    await MigrationManager(get_postgres_db()).up()
    print("  ok  core agno tables")

    for table in CONTENTS_TABLES:
        await MigrationManager(get_postgres_db(knowledge_table=table)).up()
        print(f"  ok  {table}")


def migrate_vector_tables() -> None:
    """Add v3's nullable ``user_id`` column (and its index) to each PgVector table.

    Mirrors what ``PgVector.get_table_v1`` creates for a fresh v3 table. Existing
    rows keep ``user_id IS NULL`` -- the shared bucket -- so nothing is reassigned.
    """
    engine = create_engine(db_url)
    inspector = inspect(engine)
    existing = set(inspector.get_table_names(schema=SCHEMA))

    with engine.begin() as conn:
        for table in VECTOR_TABLES:
            if table not in existing:
                print(f"  --  {table} (absent, will be created by agno on first use)")
                continue
            conn.execute(text(f"ALTER TABLE {SCHEMA}.{table} ADD COLUMN IF NOT EXISTS user_id TEXT"))
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table}_user_id ON {SCHEMA}.{table} (user_id)"))
            print(f"  ok  {table}")


def main() -> None:
    print("Agno v2 -> v3 migration")
    print("\n[1/2] agno-managed tables")
    asyncio.run(migrate_agno_tables())
    print("\n[2/2] PgVector tables (user_id column)")
    migrate_vector_tables()
    print("\nDone.")


if __name__ == "__main__":
    main()
