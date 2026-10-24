import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
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


async def test_seed_sets_execution_targets_for_executable_models(session: AsyncSession) -> None:
    await seed_model_catalog(session)

    models = {m.model_key: m for m in await session.scalars(select(ModelRecord))}

    for key in ("gpt-5", "claude-sonnet", "gemini", "deepseek"):
        assert (models[key].inference_provider, models[key].provider_model_id) == ("fake", key)
    assert (models["ollama-local"].inference_provider, models["ollama-local"].provider_model_id) == (
        None,
        None,
    )


async def test_seed_fills_missing_execution_targets(session: AsyncSession) -> None:
    # Fila creada antes de la migración 0002: sin datos de ejecución.
    session.add(
        ModelRecord(
            provider="openai", model_key="gpt-5", display_name="GPT-5", context_window=1, active=True
        )
    )
    await session.commit()

    result = await seed_model_catalog(session)

    gpt = await session.scalar(select(ModelRecord).where(ModelRecord.model_key == "gpt-5"))
    assert gpt is not None
    assert (gpt.inference_provider, gpt.provider_model_id) == ("fake", "gpt-5")
    assert result.execution_targets_filled == 1
    # El resto de campos existentes no se tocan.
    assert gpt.context_window == 1


async def test_seed_never_overwrites_execution_targets(session: AsyncSession) -> None:
    await seed_model_catalog(session)
    await session.execute(
        update(ModelRecord)
        .where(ModelRecord.model_key == "gpt-5")
        .values(inference_provider="openrouter", provider_model_id="openai/gpt-5")
    )
    await session.commit()

    result = await seed_model_catalog(session)

    gpt = await session.scalar(select(ModelRecord).where(ModelRecord.model_key == "gpt-5"))
    assert gpt is not None
    assert (gpt.inference_provider, gpt.provider_model_id) == ("openrouter", "openai/gpt-5")
    assert result.execution_targets_filled == 0


async def test_execution_target_cannot_be_half_set(session: AsyncSession) -> None:
    session.add(
        ModelRecord(
            provider="test",
            model_key="m",
            display_name="M",
            context_window=1,
            active=True,
            inference_provider="fake",
        )
    )

    with pytest.raises(IntegrityError):
        await session.commit()
