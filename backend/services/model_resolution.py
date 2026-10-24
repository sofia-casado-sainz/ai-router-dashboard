"""Mapeo transitorio router_id → modelo del catálogo (ADR-0001, Architectural Debt).

Deuda arquitectónica temporal, aprobada únicamente para S2. Se elimina en S2b,
cuando el router lea directamente el catálogo persistente, que será la fuente de
verdad de los modelos. No añadir lógica aquí ni usarlo fuera de ExecutionService
(a través de CatalogModelResolver). Nunca elige un modelo por su cuenta: si un id
no tiene correspondencia, falla con ModelNotAvailable.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from domain.execution import ResolvedModel
from providers.errors import ModelNotAvailable
from repositories.model_repository import ModelRepository

# Tabla de ADR-0001: id del router → (provider, model_key) del catálogo.
ROUTER_TO_CATALOG: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "claude-sonnet": ("anthropic", "claude-sonnet"),
        "gemini": ("google", "gemini"),
        "gpt": ("openai", "gpt-5"),
        "deepseek": ("deepseek", "deepseek"),
    }
)


class CatalogModelResolver:
    """ModelResolver sobre el catálogo persistente, usando el mapeo transitorio."""

    def __init__(self, repository: ModelRepository) -> None:
        self._repository = repository

    async def resolve(self, model_id: str) -> ResolvedModel:
        key = ROUTER_TO_CATALOG.get(model_id)
        if key is None:
            raise ModelNotAvailable(
                f"El modelo {model_id!r} del router no tiene correspondencia en el catálogo."
            )

        provider, model_key = key
        model = await self._repository.get_by_key(provider, model_key)
        if model is None:
            raise ModelNotAvailable(f"El modelo {provider}/{model_key} no existe en el catálogo.")
        if not model.active:
            raise ModelNotAvailable(f"El modelo {provider}/{model_key} está inactivo.")
        if model.inference_provider is None or model.provider_model_id is None:
            raise ModelNotAvailable(
                f"El modelo {provider}/{model_key} no tiene un inference provider asignado."
            )

        return ResolvedModel(
            inference_provider=model.inference_provider,
            provider_model_id=model.provider_model_id,
        )
