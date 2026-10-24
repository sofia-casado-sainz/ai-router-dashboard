"""Arranque de la Execution Layer (ADR-0001): registro de proveedores y dependencias."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from api.dependencies import get_execution_service
from core.config import Settings
from database.seed import seed_model_catalog
from main import create_app
from providers.errors import ProviderTimeout
from providers.fake import FakeProvider
from providers.registry import ProviderRegistry
from services.routing_service import route_prompt

UNREACHABLE_DB = "postgresql+asyncpg://user:pass@127.0.0.1:1/missing"


def request_for(app: object) -> Request:
    return Request({"type": "http", "app": app})


def test_registry_contains_only_fake_provider() -> None:
    app = create_app(Settings(_env_file=None))

    assert isinstance(app.state.provider_registry, ProviderRegistry)
    assert [provider.key for provider in app.state.provider_registry.list()] == ["fake"]


def test_settings_are_stored_in_app_state() -> None:
    settings = Settings(_env_file=None, completions_timeout_seconds=7)

    app = create_app(settings)

    assert app.state.settings is settings


def test_no_new_api_routes() -> None:
    # El esquema OpenAPI es la superficie pública de la API.
    paths = create_app(Settings(_env_file=None)).openapi()["paths"]

    routes = {(method.upper(), path) for path, operations in paths.items() for method in operations}

    assert routes == {
        ("GET", "/api/v1/health"),
        ("POST", "/api/v1/route"),
        ("GET", "/api/v1/models"),
    }


def test_app_starts_without_database() -> None:
    with TestClient(create_app(Settings(_env_file=None, database_url=UNREACHABLE_DB))) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert client.post("/api/v1/route", json={"prompt": "Hola"}).status_code == 200


@pytest.mark.anyio
async def test_execution_service_dependency_runs_the_full_flow(
    settings: Settings, session: AsyncSession
) -> None:
    await seed_model_catalog(session)
    app = create_app(settings)
    prompt = "Resume este correo para mi equipo"

    service = get_execution_service(request_for(app), session)
    execution = await service.execute(prompt, max_output_tokens=100)

    assert execution.decision.details == route_prompt(prompt)
    assert execution.result.inference_provider == "fake"
    assert execution.result.provider_model_id == "deepseek"


@pytest.mark.anyio
async def test_execution_service_uses_configured_timeout(
    database_url: str, session: AsyncSession
) -> None:
    await seed_model_catalog(session)
    app = create_app(
        Settings(_env_file=None, database_url=database_url, completions_timeout_seconds=0.05)
    )
    slow = ProviderRegistry()
    slow.register(FakeProvider(delay_seconds=5))
    app.state.provider_registry = slow

    service = get_execution_service(request_for(app), session)

    with pytest.raises(ProviderTimeout):
        await service.execute("Hola", max_output_tokens=10)
