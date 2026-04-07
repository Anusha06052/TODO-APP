"""Alembic async migration environment for SQL Server via aioodbc.

Uses the ``run_async_migrations`` pattern with :func:`asyncio.run` so that
SQLAlchemy's async engine is used end-to-end.  ``render_as_batch`` is
explicitly disabled because SQL Server supports ``ALTER TABLE`` natively and
does not need the SQLite batch-alter workaround.
"""

import asyncio
import logging
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Load .env before importing app modules so all env vars are available.
load_dotenv()

# Import Base and every model so autogenerate detects all table changes.
from app.db.base import Base  # noqa: E402
import app.models.todo  # noqa: F401, E402 — side-effect: registers Todo on Base.metadata
import app.models.category  # noqa: F401, E402 — side-effect: registers Category on Base.metadata

# Alembic Config object — gives access to values in alembic.ini.
config = context.config

# Wire up Python logging from alembic.ini if a config file was provided.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# Resolve the database URL from app settings (reads individual DB_* env vars).
from app.config import settings  # noqa: E402

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the Alembic context with a URL only — no live DB connection is
    required.  SQL is emitted to stdout for manual review or scripted apply.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=False,  # Not needed for SQL Server; set explicitly for clarity.
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute pending migrations on an already-open synchronous connection.

    Called by :func:`run_async_migrations` via ``run_sync`` so that Alembic's
    synchronous migration runner has access to the live connection provided by
    the async engine.

    Args:
        connection: Active SQLAlchemy ``Connection`` passed in by ``run_sync``.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=False,  # Not needed for SQL Server; set explicitly for clarity.
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine, connect, and run all pending migrations.

    Uses :func:`~sqlalchemy.ext.asyncio.async_engine_from_config` with
    ``NullPool`` so that no connections are held open after the migration
    completes — safe for one-shot CLI execution.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the async engine.

    Delegates to :func:`run_async_migrations` via ``asyncio.run`` so that the
    fully async SQLAlchemy 2.x engine is used throughout.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
