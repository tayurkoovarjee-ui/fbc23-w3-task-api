import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.models import Base

# Alembic's own settings from alembic.ini.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# The tables the models describe. "alembic check" compares this to the real
# database, so it can tell if the models and migrations have drifted apart.
target_metadata = Base.metadata


def get_url() -> str:
    # Same environment variable as the app, so there is one source of truth.
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def run_migrations_online() -> None:
    engine = create_engine(get_url())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        # Postgres can undo schema changes, so a failed migration is rolled back
        # and leaves no half-built tables.
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations_online()
