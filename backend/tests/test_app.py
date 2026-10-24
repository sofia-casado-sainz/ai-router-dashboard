import json
import logging

from fastapi.testclient import TestClient

from core.config import Settings
from core.logging import JsonFormatter
from main import app, create_app

client = TestClient(app)


def test_health_is_versioned() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unversioned_routes_are_gone() -> None:
    assert client.get("/health").status_code == 404
    assert client.post("/route", json={"prompt": "Hola"}).status_code == 404


def test_operation_ids_are_stable() -> None:
    operation_ids = {
        operation["operationId"]
        for path in app.openapi()["paths"].values()
        for operation in path.values()
    }

    assert operation_ids == {"get_health", "route_prompt", "list_models"}


def test_cors_allows_configured_frontend() -> None:
    settings = Settings(_env_file=None, frontend_url="https://app.example.com/", cors_origins="")
    test_client = TestClient(create_app(settings))

    response = test_client.options(
        "/api/v1/route",
        headers={"Origin": "https://app.example.com", "Access-Control-Request-Method": "POST"},
    )

    assert response.headers["access-control-allow-origin"] == "https://app.example.com"


def test_settings_parse_comma_separated_origins() -> None:
    settings = Settings(
        _env_file=None,
        frontend_url="http://localhost:3000",
        cors_origins="http://a.test, http://b.test,http://localhost:3000",
        log_level="debug",
    )

    assert settings.allowed_origins == ["http://localhost:3000", "http://a.test", "http://b.test"]
    assert settings.log_level == "DEBUG"


def test_json_formatter_includes_required_fields() -> None:
    record = logging.LogRecord("ai_router", logging.INFO, __file__, 1, "hola %s", ("mundo",), None)
    record.request_id = "abc"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["module"] == "test_app"
    assert payload["message"] == "hola mundo"
    assert payload["request_id"] == "abc"
    assert payload["timestamp"].endswith("+00:00")
