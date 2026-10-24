import pytest
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ModelPriceRecord, ModelRecord
from database.seed import SEED_MODELS, seed_model_catalog

pytestmark = pytest.mark.anyio


async def test_seed_creates_catalog(session: AsyncSession) -> None:
    result = await seed_model_catalog(session)

    assert result.models_created == len(SEED_MODELS)
    assert result.prices_created == len(SEED_MODELS)


async def test_seed_is_idempotent(session: AsyncSession) -> None:
    await seed_model_catalog(session)

    second = await seed_model_catalog(session)

    assert (second.models_created, second.prices_created) == (0, 0)
    assert await session.scalar(select(func.count()).select_from(ModelRecord)) == len(SEED_MODELS)
    assert await session.scalar(select(func.count()).select_from(ModelPriceRecord)) == len(
        SEED_MODELS
    )


async def test_seed_does_not_overwrite_manual_changes(session: AsyncSession) -> None:
    await seed_model_catalog(session)
    await session.execute(
        update(ModelRecord).where(ModelRecord.model_key == "gpt-5").values(active=False)
    )
    await session.commit()

    await seed_model_catalog(session)

    gpt = await session.scalar(select(ModelRecord).where(ModelRecord.model_key == "gpt-5"))
    assert gpt is not None and gpt.active is False
