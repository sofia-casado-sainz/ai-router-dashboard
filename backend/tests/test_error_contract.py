"""Contrato de errores de la API (ADR-0002 §5)."""

import asyncio
from typing import get_args

import pytest
from fastapi.testclient import TestClient

from api.errors import (
    ERROR_MESSAGES,
    from_provider_error,
    retry_after_header,
)
from core.config import Settings
from core.request_context import REQUEST_ID_HEADER
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
from schemas.errors import ErrorCode
from tests.conftest import prepare_database

UNREACHABLE_DB = "postgresql+asyncpg://user:pass@127.0.0.1:1/missing"
SECRET = "sk-or-SECRETO upstream account 42"


class CustomProviderError(ProviderError):
    """Un error de proveedor sin entrada propia en la tabla."""


@pytest.mark.parametrize(
    ("error", "status_code", "code"),
    [
        (ProviderNotConfigured("x"), 503, "provider_not_configured"),
        (ProviderUnavailable("x"), 503, "provider_unavailable"),
        (ProviderTimeout("x"), 504, "provider_timeout"),
        (ProviderRateLimited("x"), 429, "provider_rate_limited"),
        (ProviderAuthError("x"), 502, "provider_auth_error"),
        (ProviderBadRequest("x"), 400, "provider_bad_request"),
        (ModelNotAvailable("x"), 502, "model_not_available"),
        (CustomProviderError("x"), 502, "provider_error"),
    ],
    ids=lambda value: type(value).__name__ if isinstance(value, ProviderError) else str(value),
)
def test_provider_error_mapping(error: ProviderError, status_code: int, code: str) -> None:
    api_error = from_provider_error(error)

    assert (api_error.status_code, api_error.code) == (status_code, code)


def test_every_code_has_a_fixed_message() -> None:
    assert set(ERROR_MESSAGES) == set(get_args(ErrorCode))


@pytest.mark.parametrize(
    ("seconds", "header"), [(0, "1"), (0.4, "1"), (1, "1"), (1.2, "2"), (30, "30")]
)
def test_retry_after_rounds_up_with_minimum_one(seconds: float, header: str) -> None:
    assert retry_after_header(seconds) == header


def test_rate_limit_without_retry_after_has_no_header() -> None:
    assert from_provider_error(ProviderRateLimited("x")).headers is None


@pytest.fixture
def enabled_client(database_url: str) -> TestClient:
    settings = Settings(_env_file=None, database_url=database_url, completions_enabled=True)
    asyncio.run(prepare_database(settings, seed=True))
    return TestClient(create_app(settings))


def failing(client: TestClient, error: ProviderError) -> TestClient:
    registry = ProviderRegistry()
    registry.register(FakeProvider(error=error))
    client.app.state.provider_registry = registry  # type: ignore[attr-defined]
    return client


def test_error_response_shape_and_request_id(enabled_client: TestClient) -> None:
    client = failing(enabled_client, ProviderTimeout("lento"))

    response = client.post(
        "/api/v1/completions", json={"prompt": "Hola"}, headers={REQUEST_ID_HEADER: "trace-err"}
    )

    assert response.status_code == 504
    assert response.json() == {
        "detail": ERROR_MESSAGES["provider_timeout"],
        "code": "provider_timeout",
        "request_id": "trace-err",
    }
    assert response.headers[REQUEST_ID_HEADER] == "trace-err"


def test_provider_details_never_reach_the_client(enabled_client: TestClient) -> None:
    client = failing(enabled_client, ProviderUnavailable(SECRET, inference_provider="fake"))

    response = client.post("/api/v1/completions", json={"prompt": "Hola"})

    assert response.json()["code"] == "provider_unavailable"
    assert "SECRETO" not in response.text
    assert "sk-or" not in response.text


def test_provider_bad_request_is_400_not_422(enabled_client: TestClient) -> None:
    client = failing(enabled_client, ProviderBadRequest("contexto excedido"))

    response = client.post("/api/v1/completions", json={"prompt": "Hola"})

    assert response.status_code == 400
    assert response.json()["code"] == "provider_bad_request"


def test_validation_errors_keep_the_422_format(enabled_client: TestClient) -> None:
    response = enabled_client.post("/api/v1/completions", json={"prompt": ""})

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert "code" not in response.json()


def test_rate_limit_response_has_retry_after(enabled_client: TestClient) -> None:
    client = failing(enabled_client, ProviderRateLimited("límite", retry_after=0.4))

    response = client.post("/api/v1/completions", json={"prompt": "Hola"})

    assert response.status_code == 429
    assert response.headers["retry-after"] == "1"


def test_models_503_uses_error_response() -> None:
    client = TestClient(create_app(Settings(_env_file=None, database_url=UNREACHABLE_DB)))

    response = client.get("/api/v1/models")

    assert response.status_code == 503
    body = response.json()
    assert set(body) == {"detail", "code", "request_id"}
    assert body["code"] == "catalog_unavailable"
    assert body["detail"] == (
        "El catálogo de modelos no está disponible: no se pudo conectar con la base de datos."
    )
    assert body["request_id"] == response.headers[REQUEST_ID_HEADER]


def test_openapi_documents_error_responses() -> None:
    spec = create_app(Settings(_env_file=None)).openapi()
    completions = spec["paths"]["/api/v1/completions"]["post"]["responses"]
    models = spec["paths"]["/api/v1/models"]["get"]["responses"]
    error_ref = {"$ref": "#/components/schemas/ErrorResponse"}

    for code in ("400", "429", "502", "503", "504"):
        assert completions[code]["content"]["application/json"]["schema"] == error_ref
    assert models["503"]["content"]["application/json"]["schema"] == error_ref
    # 422 sigue siendo la validación de la petición.
    assert completions["422"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HTTPValidationError"
    }
