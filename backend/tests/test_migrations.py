"""Las migraciones crean exactamente el esquema de los modelos ORM (solo con PostgreSQL)."""

import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from database.base import Base
from tests.conftest import TEST_DATABASE_URL

BACKEND_DIR = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL or make_url(TEST_DATABASE_URL).get_backend_name() != "postgresql",
    reason="Requiere TEST_DATABASE_URL con PostgreSQL",
)


def alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = url
    config.attributes["configure_logging"] = False
    return config


def run_sync(url: str, function):
    async def run():
        engine = create_async_engine(url, poolclass=NullPool)
        try:
            async with engine.begin() as connection:
                return await connection.run_sync(function)
        finally:
            await engine.dispose()

    return asyncio.run(run())


def drop_everything(connection: Connection) -> None:
    Base.metadata.drop_all(connection)
    connection.execute(text("DROP TABLE IF EXISTS alembic_version"))


def schema_diff(connection: Connection) -> list:
    return compare_metadata(MigrationContext.configure(connection), Base.metadata)


def table_names(connection: Connection) -> set[str]:
    return set(inspect(connection).get_table_names())


def test_migrations_upgrade_and_downgrade() -> None:
    url = TEST_DATABASE_URL
    assert url is not None
    config = alembic_config(url)
    run_sync(url, drop_everything)

    command.upgrade(config, "head")
    assert {"models", "model_prices"} <= run_sync(url, table_names)
    assert run_sync(url, schema_diff) == []

    command.downgrade(config, "base")
    assert not {"models", "model_prices"} & run_sync(url, table_names)
