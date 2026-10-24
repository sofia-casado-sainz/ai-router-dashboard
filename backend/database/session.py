"""Motor y sesiones asíncronas de SQLAlchemy."""

from __future__ import annotations

from typing import Any

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Crea el motor sin conectar: la primera conexión se abre con la primera consulta."""
    url = make_url(settings.sqlalchemy_database_url)
    kwargs: dict[str, Any] = {"pool_pre_ping": True}
    if url.get_driver_name() == "asyncpg":
        # Sesiones en UTC: now() y las fechas devueltas no dependen de la zona del servidor.
        kwargs["connect_args"] = {"server_settings": {"timezone": "UTC"}}
    return create_async_engine(url, **kwargs)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False: los objetos siguen siendo legibles tras el commit.
    return async_sessionmaker(engine, expire_on_commit=False)
