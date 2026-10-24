import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ModelRecord
from database.seed import seed_model_catalog
from domain.execution import ResolvedModel
from main import app
from providers.errors import ModelNotAvailable
from repositories.model_repository import ModelRepository
from router.catalog import ModelId
from services.model_resolution import ROUTER_TO_CATALOG, CatalogModelResolver
from services.router_decider import RouterDecider

REFERENCE_PROMPTS = [
    "Resume este correo para mi equipo",
    "Diseña una arquitectura para una API",
    "Analiza este bug de producción en TypeScript",
    "Compara tres bases de datos vectoriales",
    "Hola",
]


def test_mapping_matches_adr_0001() -> None:
    assert dict(ROUTER_TO_CATALOG) == {
        "claude-sonnet": ("anthropic", "claude-sonnet"),
        "gemini": ("google", "gemini"),
        "gpt": ("openai", "gpt-5"),
        "deepseek": ("deepseek", "deepseek"),
    }


def test_mapping_covers_every_router_model() -> None:
    assert set(ROUTER_TO_CATALOG) == {str(model_id) for model_id in ModelId}


def test_mapping_is_read_only() -> None:
    with pytest.raises(TypeError):
        ROUTER_TO_CATALOG["gpt"] = ("openai", "otro")  # type: ignore[index]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("router_id", "provider_model_id"),
    [("claude-sonnet", "claude-sonnet"), ("gemini", "gemini"), ("gpt", "gpt-5"), ("deepseek", "deepseek")],
)
async def test_resolves_every_router_model_to_the_fake_provider(
    session: AsyncSession, router_id: str, provider_model_id: str
) -> None:
    await seed_model_catalog(session)

    resolved = await CatalogModelResolver(ModelRepository(session)).resolve(router_id)

    assert resolved == ResolvedModel(inference_provider="fake", provider_model_id=provider_model_id)


@pytest.mark.anyio
async def test_unknown_router_model_is_not_available(session: AsyncSession) -> None:
    await seed_model_catalog(session)

    with pytest.raises(ModelNotAvailable):
        await CatalogModelResolver(ModelRepository(session)).resolve("claude-opus")


@pytest.mark.anyio
async def test_model_missing_from_catalog_is_not_available(session: AsyncSession) -> None:
    with pytest.raises(ModelNotAvailable):
        await CatalogModelResolver(ModelRepository(session)).resolve("gpt")


@pytest.mark.anyio
async def test_inactive_model_is_not_available(session: AsyncSession) -> None:
    await seed_model_catalog(session)
    await session.execute(
        update(ModelRecord).where(ModelRecord.model_key == "gpt-5").values(active=False)
    )
    await session.commit()

    with pytest.raises(ModelNotAvailable):
        await CatalogModelResolver(ModelRepository(session)).resolve("gpt")


@pytest.mark.anyio
async def test_model_without_inference_provider_is_not_available(session: AsyncSession) -> None:
    await seed_model_catalog(session)
    await session.execute(
        update(ModelRecord)
        .where(ModelRecord.model_key == "deepseek")
        .values(inference_provider=None, provider_model_id=None)
    )
    await session.commit()

    with pytest.raises(ModelNotAvailable):
        await CatalogModelResolver(ModelRepository(session)).resolve("deepseek")


@pytest.mark.parametrize("prompt", REFERENCE_PROMPTS)
def test_router_decider_matches_route_endpoint(prompt: str) -> None:
    expected = TestClient(app).post("/api/v1/route", json={"prompt": prompt}).json()

    decision = RouterDecider().decide(prompt)

    assert decision.details.model_dump(mode="json") == expected
    assert decision.model_id == expected["selected_model"]
