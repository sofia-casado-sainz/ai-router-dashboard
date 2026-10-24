"""Dependencias de FastAPI: sesión de base de datos por petición y servicios."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.model_repository import ModelRepository
from services.model_catalog_service import ModelCatalogService


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_model_catalog_service(session: SessionDep) -> ModelCatalogService:
    return ModelCatalogService(ModelRepository(session))


ModelCatalogServiceDep = Annotated[ModelCatalogService, Depends(get_model_catalog_service)]
