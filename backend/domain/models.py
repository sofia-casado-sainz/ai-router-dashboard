"""Catálogo de modelos en el dominio: objetos inmutables, sin dependencias de base de datos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ModelPrice:
    input_cost_per_million: Decimal
    output_cost_per_million: Decimal
    currency: str
    valid_from: datetime


@dataclass(frozen=True, slots=True)
class CatalogModel:
    id: UUID
    provider: str
    model_key: str
    display_name: str
    context_window: int
    active: bool
    prices: tuple[ModelPrice, ...]

    def price_at(self, moment: datetime) -> ModelPrice | None:
        """Precio vigente en `moment`: el de `valid_from` más reciente que no sea posterior."""
        applicable = [price for price in self.prices if price.valid_from <= moment]
        return max(applicable, key=lambda price: price.valid_from, default=None)
