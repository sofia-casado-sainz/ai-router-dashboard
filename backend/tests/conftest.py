"""Fixtures de base de datos para los tests.

Por defecto los tests usan SQLite (aiosqlite) en un archivo temporal, sin infraestructura.
Con TEST_DATABASE_URL (p. ej. postgresql+asyncpg://...) se ejecutan contra PostgreSQL;
esa base de datos se vacía en cada test, así que debe ser exclusiva para tests.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from core.config import Settings
from database.base import Base
from database.seed import seed_model_catalog
from database.session import create_engine, create_session_factory
from main import create_app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def database_url(tmp_path: Path) -> str:
    return TEST_DATABASE_URL or f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def settings(database_url: str) -> Settings:
    return Settings(_env_file=None, database_url=database_url)


async def reset_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


async def prepare_database(settings: Settings, *, seed: bool) -> None:
    engine = create_engine(settings)
    try:
        await reset_schema(engine)
        if seed:
            async with create_session_factory(engine)() as session:
                await seed_model_catalog(session)
    finally:
        await engine.dispose()


@pytest.fixture
async def engine(settings: Settings) -> AsyncIterator[AsyncEngine]:
    engine = create_engine(settings)
    await reset_schema(engine)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with create_session_factory(engine)() as session:
        yield session


@pytest.fixture
def catalog_client(settings: Settings) -> Iterator[TestClient]:
    """Cliente HTTP de una app conectada a una base de datos con el seed cargado."""
    asyncio.run(prepare_database(settings, seed=True))
    with TestClient(create_app(settings)) as client:
        yield client
