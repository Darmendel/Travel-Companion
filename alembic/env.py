# alembic/env.py
import asyncio
import os
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.db.session import Base, DATABASE_URL
from app.models.trip import Trip
from app.models.stop import Stop

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


# Offline mode:
# Doesn't connect to a DB! Just creates SQL: alembic upgrade head --sql
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    # Get URL from environment or alembic.ini
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")

    # Convert asyncpg URL to sync for offline mode
    if url and "asyncpg" in url:
        url = url.replace("+asyncpg", "+psycopg2")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Helper function to run migrations with a given connection.

    This is called by run_sync from the async engine.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine.

    In this scenario we need to create an AsyncEngine
    and associate a connection with the context.
    """
    # Override the sqlalchemy.url with our async DATABASE_URL
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = DATABASE_URL

    # Create async engine
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Run migrations in sync context using run_sync
        await connection.run_sync(do_run_migrations)

    # Dispose of the engine
    await connectable.dispose()


# Online mode:
# When doing: alembic upgrade head ->
# connects to a real DB and runs commands like: 'CREATE TABLE' and 'ALTER TABLE'.
def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (async).

    This is the entry point for online migrations.
    It uses asyncio.run to execute the async migration function.
    """
    asyncio.run(run_async_migrations())


# Determine which mode to run in
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
