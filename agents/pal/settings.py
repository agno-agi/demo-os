"""Pal-specific settings — DB, knowledge bases, SQL engine."""

from sqlalchemy import Engine, create_engine, text

from db import create_knowledge, db_url, get_postgres_db

PAL_SCHEMA = "pal"
_pal_engine: Engine | None = None

agent_db = get_postgres_db()
pal_knowledge = create_knowledge("Pal Knowledge", "pal_knowledge")
pal_learnings = create_knowledge("Pal Learnings", "pal_learnings")


def get_sql_engine() -> Engine:
    global _pal_engine
    if _pal_engine is not None:
        return _pal_engine
    bootstrap = create_engine(db_url)
    with bootstrap.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {PAL_SCHEMA}"))
        conn.commit()
    bootstrap.dispose()
    _pal_engine = create_engine(
        db_url,
        connect_args={"options": f"-c search_path={PAL_SCHEMA},public"},
        pool_size=10,
        max_overflow=20,
    )
    return _pal_engine
