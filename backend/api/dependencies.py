"""Dependencias de FastAPI: sesión de base de datos por petición y servicios."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import Settings
from providers.registry import ProviderRegistry
from repositories.model_repository import ModelRepository
from services.execution_service import ExecutionService
from services.model_catalog_service import ModelCatalogService
from services.model_resolution import CatalogModelResolver
from services.router_decider import RouterDecider


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_model_catalog_service(session: SessionDep) -> ModelCatalogService:
    return ModelCatalogService(ModelRepository(session))


ModelCatalogServiceDep = Annotated[ModelCatalogService, Depends(get_model_catalog_service)]


def get_execution_service(request: Request, session: SessionDep) -> ExecutionService:
    """ExecutionService con los puertos concretos (ADR-0001): el router decide y el
    catálogo resuelve dónde se ejecuta, usando el registro creado al arrancar."""
    settings: Settings = request.app.state.settings
    registry: ProviderRegistry = request.app.state.provider_registry
    return ExecutionService(
        registry,
        decider=RouterDecider(),
        resolver=CatalogModelResolver(ModelRepository(session)),
        default_timeout_seconds=settings.completions_timeout_seconds,
    )


ExecutionServiceDep = Annotated[ExecutionService, Depends(get_execution_service)]
