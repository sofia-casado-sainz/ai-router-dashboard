import asyncio
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from core.config import Settings
from domain.completions import MAX_OUTPUT_TOKENS_LIMIT, CompletionRequest, CompletionResult
from main import app as default_app
from main import create_app
from providers.errors import (
    ModelNotAvailable,
    ProviderAuthError,
    ProviderBadRequest,
    ProviderError,
    ProviderNotConfigured,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)
from providers.fake import FakeProvider
from providers.registry import ProviderRegistry
from tests.conftest import prepare_database

URL = "/api/v1/completions"
REFERENCE_PROMPTS = [
    "Resume este correo para mi equipo",
    "Diseña una arquitectura para una API",
    "Analiza este bug de producción en TypeScript",
    "Compara tres bases de datos vectoriales",
    "Hola",
]
# Modelo del catálogo que ejecuta cada decisión (mapeo de ADR-0001).
EXPECTED_MODEL = {
    "deepseek": "deepseek",
    "claude-sonnet": "claude-sonnet",
    "gpt": "gpt-5",
    "gemini": "gemini",
}


def enabled_client(database_url: str, *, seed: bool = True) -> TestClient:
    settings = Settings(_env_file=None, database_url=database_url, completions_enabled=True)
    asyncio.run(prepare_database(settings, seed=seed))
    return TestClient(create_app(settings))


@pytest.fixture
def client(database_url: str) -> Iterator[TestClient]:
    with enabled_client(database_url) as client:
        yield client


def with_provider(client: TestClient, provider: FakeProvider) -> TestClient:
    registry = ProviderRegistry()
    registry.register(provider)
    client.app.state.provider_registry = registry  # type: ignore[attr-defined]
    return client


def test_disabled_by_default_returns_503(catalog_client: TestClient) -> None:
    response = catalog_client.post(URL, json={"prompt": "Hola"})

    assert response.status_code == 503
    assert "COMPLETIONS_ENABLED=false" in response.json()["detail"]


@pytest.mark.parametrize("prompt", REFERENCE_PROMPTS)
def test_decision_matches_route_and_completion_comes_from_fake_provider(
    client: TestClient, prompt: str
) -> None:
    route = TestClient(default_app).post("/api/v1/route", json={"prompt": prompt}).json()

    response = client.post(URL, json={"prompt": prompt})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"decision", "completion"}
    assert body["decision"] == route
    completion = body["completion"]
    assert completion["inference_provider"] == "fake"
    assert completion["provider_model_id"] == EXPECTED_MODEL[route["selected_model"]]
    assert completion["content"].startswith(f"[Respuesta simulada de {completion['provider_model_id']}]")
    assert completion["cost"] == {"amount": 0.0, "currency": "USD", "source": "reported"}
    assert completion["finish_reason"] == "stop"
    assert completion["usage"]["source"] == "reported"
    assert isinstance(completion["latency_ms"], int)


def test_max_output_tokens_is_applied(client: TestClient) -> None:
    completion = client.post(URL, json={"prompt": "Hola", "max_output_tokens": 5}).json()["completion"]

    assert completion["finish_reason"] == "length"
    assert completion["usage"]["output_tokens"] == 5


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"prompt": ""},
        {"prompt": "   "},
        {"prompt": "Hola", "max_output_tokens": 0},
        {"prompt": "Hola", "max_output_tokens": MAX_OUTPUT_TOKENS_LIMIT + 1},
        {"prompt": "Hola", "temperature": 3},
    ],
)
def test_invalid_requests_are_rejected(client: TestClient, payload: dict) -> None:
    assert client.post(URL, json=payload).status_code == 422


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (ProviderNotConfigured("sin clave"), 503),
        (ProviderUnavailable("caído"), 503),
        (ProviderTimeout("lento"), 504),
        (ProviderRateLimited("límite"), 429),
        (ProviderAuthError("clave inválida"), 502),
        (ProviderBadRequest("contexto excedido"), 422),
        (ModelNotAvailable("modelo retirado"), 502),
    ],
    ids=lambda value: type(value).__name__ if isinstance(value, ProviderError) else str(value),
)
def test_provider_errors_follow_adr_mapping(
    client: TestClient, error: ProviderError, status_code: int
) -> None:
    response = with_provider(client, FakeProvider(error=error)).post(URL, json={"prompt": "Hola"})

    assert response.status_code == status_code
    assert response.json()["detail"] == str(error)


def test_rate_limit_sets_retry_after_header(client: TestClient) -> None:
    error = ProviderRateLimited("límite", retry_after=30)

    response = with_provider(client, FakeProvider(error=error)).post(URL, json={"prompt": "Hola"})

    assert response.status_code == 429
    assert response.headers["retry-after"] == "30"


class BrokenProvider(FakeProvider):
    async def complete(self, request: CompletionRequest) -> CompletionResult:
        raise RuntimeError("respuesta inesperada")


def test_unexpected_provider_failure_returns_503(client: TestClient) -> None:
    response = with_provider(client, BrokenProvider()).post(URL, json={"prompt": "Hola"})

    assert response.status_code == 503


def test_empty_catalog_returns_502(database_url: str) -> None:
    with enabled_client(database_url, seed=False) as client:
        response = client.post(URL, json={"prompt": "Hola"})

    assert response.status_code == 502
    assert "no existe en el catálogo" in response.json()["detail"]


def test_database_unavailable_returns_503() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pass@127.0.0.1:1/missing",
        completions_enabled=True,
    )
    client = TestClient(create_app(settings))

    response = client.post(URL, json={"prompt": "Hola"})

    assert response.status_code == 503
    assert "base de datos" in response.json()["detail"]
    # /route no depende de la base de datos ni de la ejecución.
    assert client.post("/api/v1/route", json={"prompt": "Hola"}).status_code == 200
