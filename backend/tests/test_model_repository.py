from datetime import UTC

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.seed import SEED_MODELS, SEED_VALID_FROM, seed_model_catalog
from domain.models import CatalogModel
from repositories.model_repository import ModelRepository

pytestmark = pytest.mark.anyio


async def test_list_models_returns_domain_models_with_prices(session: AsyncSession) -> None:
    await seed_model_catalog(session)

    models = await ModelRepository(session).list_models()

    assert len(models) == len(SEED_MODELS)
    assert all(isinstance(model, CatalogModel) for model in models)
    assert [model.provider for model in models] == sorted(model.provider for model in models)

    claude = next(model for model in models if model.model_key == "claude-sonnet")
    assert claude.display_name == "Claude Sonnet"
    assert claude.context_window == 200_000
    assert len(claude.prices) == 1
    assert claude.prices[0].currency == "USD"
    assert claude.prices[0].valid_from == SEED_VALID_FROM
    assert claude.prices[0].valid_from.tzinfo is not None
    assert claude.prices[0].valid_from.utcoffset() == UTC.utcoffset(None)


async def test_list_models_filters_by_active_flag(session: AsyncSession) -> None:
    await seed_model_catalog(session)
    repository = ModelRepository(session)

    active = await repository.list_models(active=True)
    inactive = await repository.list_models(active=False)

    assert all(model.active for model in active)
    assert [model.model_key for model in inactive] == ["ollama-local"]
    assert len(active) + len(inactive) == len(SEED_MODELS)


async def test_list_models_with_empty_catalog(session: AsyncSession) -> None:
    assert await ModelRepository(session).list_models() == []
