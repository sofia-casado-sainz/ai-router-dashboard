"""Catálogo de modelos: qué modelos existen y cuánto cuestan ahora.

El router todavía no lo usa (sigue con router/catalog.py); se conectará en el Sprint S2.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from domain.models import CatalogModel, ModelPrice
from repositories.model_repository import ModelRepository


@dataclass(frozen=True, slots=True)
class ModelCatalogEntry:
    model: CatalogModel
    # None si el modelo aún no tiene ningún precio vigente.
    current_price: ModelPrice | None


def utc_now() -> datetime:
    return datetime.now(UTC)


class ModelCatalogService:
    def __init__(
        self, repository: ModelRepository, clock: Callable[[], datetime] = utc_now
    ) -> None:
        self._repository = repository
        self._clock = clock

    async def get_models(self) -> list[ModelCatalogEntry]:
        return self._with_current_price(await self._repository.list_models())

    async def get_active_models(self) -> list[ModelCatalogEntry]:
        return self._with_current_price(await self._repository.list_models(active=True))

    async def sync_openrouter_models(self) -> None:
        """Importará modelos y precios desde la API de OpenRouter (Sprint S2)."""
        raise NotImplementedError("La sincronización con OpenRouter llega en el Sprint S2.")

    async def sync_ollama_models(self) -> None:
        """Importará los modelos instalados en Ollama (Sprint S3)."""
        raise NotImplementedError("La sincronización con Ollama llega en el Sprint S3.")

    def _with_current_price(self, models: list[CatalogModel]) -> list[ModelCatalogEntry]:
        now = self._clock()
        return [ModelCatalogEntry(model, model.price_at(now)) for model in models]
