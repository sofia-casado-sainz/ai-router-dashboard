"""Acceso a datos del catálogo de modelos. Devuelve objetos de dominio, nunca filas ORM."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import ModelPriceRecord, ModelRecord
from domain.models import CatalogModel, ModelPrice


class ModelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_models(self, *, active: bool | None = None) -> list[CatalogModel]:
        """Modelos con todo su histórico de precios, ordenados por proveedor y nombre."""
        statement = (
            select(ModelRecord)
            .options(selectinload(ModelRecord.prices))
            .order_by(ModelRecord.provider, ModelRecord.display_name)
        )
        if active is not None:
            statement = statement.where(ModelRecord.active == active)

        records = await self._session.scalars(statement)
        return [_to_domain(record) for record in records]

    async def get_by_key(self, provider: str, model_key: str) -> CatalogModel | None:
        """Un modelo por su vendor y su clave, con su histórico de precios; None si no existe."""
        record = await self._session.scalar(
            select(ModelRecord)
            .options(selectinload(ModelRecord.prices))
            .where(ModelRecord.provider == provider, ModelRecord.model_key == model_key)
        )
        return None if record is None else _to_domain(record)


def _to_domain(record: ModelRecord) -> CatalogModel:
    return CatalogModel(
        id=record.id,
        provider=record.provider,
        model_key=record.model_key,
        display_name=record.display_name,
        context_window=record.context_window,
        active=record.active,
        prices=tuple(_price_to_domain(price) for price in record.prices),
        inference_provider=record.inference_provider,
        provider_model_id=record.provider_model_id,
    )


def _price_to_domain(record: ModelPriceRecord) -> ModelPrice:
    return ModelPrice(
        input_cost_per_million=record.input_cost_per_million,
        output_cost_per_million=record.output_cost_per_million,
        currency=record.currency,
        valid_from=_as_utc(record.valid_from),
    )


def _as_utc(value: datetime) -> datetime:
    # PostgreSQL devuelve fechas con zona; SQLite (tests) las devuelve sin ella.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
