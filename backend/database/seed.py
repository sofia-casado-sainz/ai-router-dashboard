"""Catálogo de modelos de ejemplo.

Los precios y contextos son datos de ejemplo, no tarifas reales de los proveedores.
El seed es idempotente: solo inserta lo que falta y nunca sobrescribe cambios
hechos a mano (por ejemplo, desactivar un modelo). En modelos que ya existen,
solo rellena `inference_provider` y `provider_model_id` si ambos están vacíos.
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
# Los modelos de ejemplo ejecutables se ejecutan con el proveedor simulado (ADR-0001)
# hasta que exista la integración con OpenRouter.
SAMPLE_INFERENCE_PROVIDER = "fake"


@dataclass(frozen=True, slots=True)
class SeedModel:
    provider: str
    model_key: str
    display_name: str
    context_window: int
    active: bool
    input_cost_per_million: Decimal
    output_cost_per_million: Decimal
    # None: el modelo todavía no es ejecutable.
    inference_provider: str | None = None
    provider_model_id: str | None = None


def _executable(
    provider: str,
    model_key: str,
    display_name: str,
    context_window: int,
    input_cost: str,
    output_cost: str,
) -> SeedModel:
    """Modelo de ejemplo activo y ejecutable con el proveedor simulado."""
    return SeedModel(
        provider,
        model_key,
        display_name,
        context_window,
        True,
        Decimal(input_cost),
        Decimal(output_cost),
        inference_provider=SAMPLE_INFERENCE_PROVIDER,
        provider_model_id=model_key,
    )


SEED_MODELS: tuple[SeedModel, ...] = (
    _executable("openai", "gpt-5", "GPT-5", 256_000, "2.00", "8.00"),
    _executable("anthropic", "claude-sonnet", "Claude Sonnet", 200_000, "2.50", "12.00"),
    _executable("google", "gemini", "Gemini", 1_000_000, "1.00", "4.00"),
    _executable("deepseek", "deepseek", "DeepSeek", 128_000, "0.20", "0.80"),
    # Inactivo y sin ejecución hasta que exista la integración con Ollama (Sprint S3).
    SeedModel("ollama", "ollama-local", "Ollama Local", 32_768, False, Decimal("0"), Decimal("0")),
)


@dataclass(frozen=True, slots=True)
class SeedResult:
    models_created: int
    prices_created: int
    # Modelos existentes en los que se rellenaron inference_provider y provider_model_id.
    execution_targets_filled: int = 0


async def seed_model_catalog(session: AsyncSession) -> SeedResult:
    models_created = prices_created = execution_targets_filled = 0

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
                inference_provider=item.inference_provider,
                provider_model_id=item.provider_model_id,
            )
            session.add(model)
            await session.flush()
            models_created += 1
        elif (
            item.inference_provider is not None
            and model.inference_provider is None
            and model.provider_model_id is None
        ):
            # Bases de datos anteriores a la migración 0002: completar sin sobrescribir.
            model.inference_provider = item.inference_provider
            model.provider_model_id = item.provider_model_id
            execution_targets_filled += 1

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
    return SeedResult(models_created, prices_created, execution_targets_filled)
