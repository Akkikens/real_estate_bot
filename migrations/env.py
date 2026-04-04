"""
Alembic env.py — configured to use the project's settings and models.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool

from alembic import context

# Ensure project root is on sys.path so imports work
sys.path.insert(0, str(Path(__file__).parents[1]))

from config import settings  # noqa: E402
from database.models import Base  # noqa: E402

# Alembic Config object
config = context.config

# We read the URL directly from settings instead of alembic.ini.
# (Don't use config.set_main_option — it chokes on % in passwords.)
_DB_URL = settings.DATABASE_URL

# Python logging config from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=_DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from sqlalchemy import create_engine

    connectable = create_engine(_DB_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Required for SQLite ALTER TABLE support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
