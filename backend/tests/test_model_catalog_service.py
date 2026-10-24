from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ModelPriceRecord, ModelRecord
from database.seed import seed_model_catalog
from repositories.model_repository import ModelRepository
from services.model_catalog_service import ModelCatalogService

pytestmark = pytest.mark.anyio

NOW = datetime(2026, 6, 1, tzinfo=UTC)


def make_service(session: AsyncSession) -> ModelCatalogService:
    return ModelCatalogService(ModelRepository(session), clock=lambda: NOW)


def price(model: ModelRecord, amount: str, valid_from: datetime) -> ModelPriceRecord:
    return ModelPriceRecord(
        model=model,
        input_cost_per_million=Decimal(amount),
        output_cost_per_million=Decimal(amount),
        currency="USD",
        valid_from=valid_from,
    )


async def test_get_active_models_returns_only_active_models_with_price(
    session: AsyncSession,
) -> None:
    await seed_model_catalog(session)

    entries = await make_service(session).get_active_models()

    assert entries
    assert all(entry.model.active for entry in entries)
    assert "ollama-local" not in {entry.model.model_key for entry in entries}
    assert all(entry.current_price is not None for entry in entries)


async def test_get_models_includes_inactive_models(session: AsyncSession) -> None:
    await seed_model_catalog(session)

    entries = await make_service(session).get_models()

    assert "ollama-local" in {entry.model.model_key for entry in entries}


async def test_current_price_is_latest_price_not_in_the_future(session: AsyncSession) -> None:
    model = ModelRecord(
        provider="test", model_key="m", display_name="M", context_window=1000, active=True
    )
    session.add_all(
        [
            model,
            price(model, "1", datetime(2026, 1, 1, tzinfo=UTC)),
            price(model, "2", datetime(2026, 5, 1, tzinfo=UTC)),
            price(model, "3", datetime(2026, 7, 1, tzinfo=UTC)),
        ]
    )
    await session.commit()

    [entry] = await make_service(session).get_models()

    assert entry.current_price is not None
    assert entry.current_price.input_cost_per_million == Decimal("2")


async def test_model_without_current_price(session: AsyncSession) -> None:
    model = ModelRecord(
        provider="test", model_key="m", display_name="M", context_window=1000, active=True
    )
    session.add_all([model, price(model, "1", datetime(2027, 1, 1, tzinfo=UTC))])
    await session.commit()

    [entry] = await make_service(session).get_models()

    assert entry.current_price is None


async def test_provider_sync_is_not_implemented_yet(session: AsyncSession) -> None:
    service = make_service(session)

    with pytest.raises(NotImplementedError):
        await service.sync_openrouter_models()
    with pytest.raises(NotImplementedError):
        await service.sync_ollama_models()
