"""Trazabilidad por request_id (ADR-0002 §6)."""

import asyncio
import json
import logging
import uuid

import pytest
from fastapi.testclient import TestClient

from core.config import Settings
from core.logging import RequestIdFilter
from core.request_context import (
    REQUEST_ID_HEADER,
    bind_request_id,
    get_request_id,
    reset_request_id,
    resolve_request_id,
)
from main import create_app
from providers.errors import ProviderUnavailable
from providers.fake import FakeProvider
from providers.registry import ProviderRegistry
from tests.conftest import prepare_database

UNREACHABLE_DB = "postgresql+asyncpg://user:pass@127.0.0.1:1/missing"
PROMPT = "Resume este correo confidencial para mi equipo"


def is_uuid4(value: str) -> bool:
    try:
        return uuid.UUID(value).version == 4
    except ValueError:
        return False


def json_log_lines(output: str) -> list[dict]:
    lines = []
    for line in output.splitlines():
        try:
            lines.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return lines


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Settings(_env_file=None, database_url=UNREACHABLE_DB)))


def enabled_client(database_url: str) -> TestClient:
    settings = Settings(_env_file=None, database_url=database_url, completions_enabled=True)
    asyncio.run(prepare_database(settings, seed=True))
    return TestClient(create_app(settings))


# --- Resolución del identificador ---------------------------------------------


@pytest.mark.parametrize("incoming", ["abc-123", "trace_42.x", "A" * 64])
def test_valid_incoming_request_id_is_reused(incoming: str) -> None:
    assert resolve_request_id(incoming) == incoming


@pytest.mark.parametrize("incoming", [None, "", "A" * 65, "con espacio", "id;drop", "ñandú"])
def test_missing_or_invalid_request_id_becomes_uuid4(incoming: str | None) -> None:
    assert is_uuid4(resolve_request_id(incoming))


# --- Filtro de logging ---------------------------------------------------------


def test_filter_adds_request_id_from_context() -> None:
    token = bind_request_id("trace-1")
    try:
        record = logging.makeLogRecord({"msg": "hola"})
        RequestIdFilter().filter(record)
    finally:
        reset_request_id(token)

    assert record.request_id == "trace-1"


def test_filter_keeps_explicit_request_id() -> None:
    token = bind_request_id("trace-1")
    try:
        record = logging.makeLogRecord({"msg": "hola", "request_id": "explícito"})
        RequestIdFilter().filter(record)
    finally:
        reset_request_id(token)

    assert record.request_id == "explícito"


def test_filter_outside_a_request_adds_nothing() -> None:
    record = logging.makeLogRecord({"msg": "hola"})

    RequestIdFilter().filter(record)

    assert not hasattr(record, "request_id")


# --- Cabecera en las respuestas ------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path", "body", "status_code"),
    [
        ("GET", "/api/v1/health", None, 200),
        ("POST", "/api/v1/route", {"prompt": "Hola"}, 200),
        ("POST", "/api/v1/route", {}, 422),
        ("GET", "/api/v1/models", None, 503),
        ("POST", "/api/v1/completions", {"prompt": "Hola"}, 503),
        ("GET", "/api/v1/no-existe", None, 404),
    ],
)
def test_every_response_has_a_request_id(
    client: TestClient, method: str, path: str, body: dict | None, status_code: int
) -> None:
    response = client.request(method, path, json=body)

    assert response.status_code == status_code
    assert is_uuid4(response.headers[REQUEST_ID_HEADER])


def test_valid_incoming_header_is_returned(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={REQUEST_ID_HEADER: "trace-42"})

    assert response.headers[REQUEST_ID_HEADER] == "trace-42"


def test_invalid_incoming_header_is_replaced(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={REQUEST_ID_HEADER: "no valido; drop"})

    assert is_uuid4(response.headers[REQUEST_ID_HEADER])


def test_each_request_gets_its_own_id(client: TestClient) -> None:
    first = client.get("/api/v1/health").headers[REQUEST_ID_HEADER]
    second = client.get("/api/v1/health").headers[REQUEST_ID_HEADER]

    assert first != second


def test_request_id_does_not_leak_outside_the_request(client: TestClient) -> None:
    client.get("/api/v1/health")

    assert get_request_id() is None


def test_cors_exposes_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})

    exposed = response.headers["access-control-expose-headers"].lower()
    assert REQUEST_ID_HEADER.lower() in exposed


def test_cors_preflight_allows_and_returns_request_id(client: TestClient) -> None:
    response = client.options(
        "/api/v1/completions",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-request-id",
        },
    )

    assert response.status_code == 200
    assert REQUEST_ID_HEADER.lower() in response.headers["access-control-allow-headers"].lower()
    assert is_uuid4(response.headers[REQUEST_ID_HEADER])


# --- Correlación en los logs ---------------------------------------------------


def test_execution_log_correlates_request_and_provider_ids(
    database_url: str, capsys: pytest.CaptureFixture[str]
) -> None:
    client = enabled_client(database_url)

    response = client.post(
        "/api/v1/completions", json={"prompt": PROMPT}, headers={REQUEST_ID_HEADER: "trace-ok"}
    )

    output = capsys.readouterr().out
    entry = next(
        line for line in json_log_lines(output) if line["message"] == "Ejecución completada"
    )
    assert response.status_code == 200
    assert entry["request_id"] == "trace-ok"
    assert entry["provider_request_id"] == response.json()["completion"]["provider_request_id"]
    assert entry["inference_provider"] == "fake"
    assert PROMPT not in output


def test_failure_log_has_request_id_and_no_prompt(
    database_url: str, capsys: pytest.CaptureFixture[str]
) -> None:
    client = enabled_client(database_url)
    registry = ProviderRegistry()
    registry.register(FakeProvider(error=ProviderUnavailable("caído")))
    client.app.state.provider_registry = registry  # type: ignore[attr-defined]

    response = client.post("/api/v1/completions", json={"prompt": PROMPT})

    output = capsys.readouterr().out
    entry = next(
        line
        for line in json_log_lines(output)
        if line["message"] == "La ejecución del modelo falló"
    )
    assert response.status_code == 503
    assert entry["request_id"] == response.headers[REQUEST_ID_HEADER]
    assert PROMPT not in output
