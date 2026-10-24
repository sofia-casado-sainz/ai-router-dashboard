"""Catálogo de modelos de ejemplo.

Los precios y contextos son datos de ejemplo, no tarifas reales de los proveedores.
El seed es idempotente: solo inserta lo que falta y nunca sobrescribe cambios
hechos a mano (por ejemplo, desactivar un modelo).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ModelPriceRecord, ModelRecord

SEED_CURRENCY = "USD"
# Fecha fija: así el seed sabe si el precio ya está cargado.
SEED_VALID_FROM = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class SeedModel:
    provider: str
    model_key: str
    display_name: str
    context_window: int
    active: bool
    input_cost_per_million: Decimal
    output_cost_per_million: Decimal


SEED_MODELS: tuple[SeedModel, ...] = (
    SeedModel("openai", "gpt-5", "GPT-5", 256_000, True, Decimal("2.00"), Decimal("8.00")),
    SeedModel(
        "anthropic", "claude-sonnet", "Claude Sonnet", 200_000, True, Decimal("2.50"), Decimal("12.00")
    ),
    SeedModel("google", "gemini", "Gemini", 1_000_000, True, Decimal("1.00"), Decimal("4.00")),
    SeedModel("deepseek", "deepseek", "DeepSeek", 128_000, True, Decimal("0.20"), Decimal("0.80")),
    # Inactivo hasta que exista la integración con Ollama (Sprint S3).
    SeedModel("ollama", "ollama-local", "Ollama Local", 32_768, False, Decimal("0"), Decimal("0")),
)


@dataclass(frozen=True, slots=True)
class SeedResult:
    models_created: int
    prices_created: int


async def seed_model_catalog(session: AsyncSession) -> SeedResult:
    models_created = prices_created = 0

    for item in SEED_MODELS:
        model = await session.scalar(
            select(ModelRecord).where(
                ModelRecord.provider == item.provider, ModelRecord.model_key == item.model_key
            )
        )
        if model is None:
            model = ModelRecord(
                provider=item.provider,
                model_key=item.model_key,
                display_name=item.display_name,
                context_window=item.context_window,
                active=item.active,
            )
            session.add(model)
            await session.flush()
            models_created += 1

        price_exists = await session.scalar(
            select(ModelPriceRecord.id).where(
                ModelPriceRecord.model_id == model.id,
                ModelPriceRecord.valid_from == SEED_VALID_FROM,
            )
        )
        if price_exists is None:
            session.add(
                ModelPriceRecord(
                    model_id=model.id,
                    input_cost_per_million=item.input_cost_per_million,
                    output_cost_per_million=item.output_cost_per_million,
                    currency=SEED_CURRENCY,
                    valid_from=SEED_VALID_FROM,
                )
            )
            prices_created += 1

    await session.commit()
    return SeedResult(models_created, prices_created)
