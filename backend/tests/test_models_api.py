from fastapi.testclient import TestClient

from core.config import Settings
from database.seed import SEED_MODELS
from main import create_app


def test_list_models_returns_200(catalog_client: TestClient) -> None:
    response = catalog_client.get("/api/v1/models")

    assert response.status_code == 200
    assert len(response.json()["models"]) == len(SEED_MODELS)


def test_list_models_response_shape(catalog_client: TestClient) -> None:
    [model, *_] = catalog_client.get("/api/v1/models").json()["models"]

    assert set(model) == {
        "id",
        "provider",
        "model_key",
        "display_name",
        "context_window",
        "active",
        "current_price",
    }
    assert set(model["current_price"]) == {
        "input_cost_per_million",
        "output_cost_per_million",
        "currency",
    }


def test_list_models_returns_pricing(catalog_client: TestClient) -> None:
    models = {m["model_key"]: m for m in catalog_client.get("/api/v1/models").json()["models"]}

    assert models["claude-sonnet"]["current_price"] == {
        "input_cost_per_million": 2.5,
        "output_cost_per_million": 12.0,
        "currency": "USD",
    }
    assert models["ollama-local"]["current_price"]["input_cost_per_million"] == 0


def test_list_models_returns_active_flag(catalog_client: TestClient) -> None:
    models = {m["model_key"]: m for m in catalog_client.get("/api/v1/models").json()["models"]}

    assert models["gpt-5"]["active"] is True
    assert models["ollama-local"]["active"] is False


def test_list_models_can_return_only_active_models(catalog_client: TestClient) -> None:
    models = catalog_client.get("/api/v1/models", params={"active_only": True}).json()["models"]

    assert models
    assert all(model["active"] for model in models)
    assert "ollama-local" not in {model["model_key"] for model in models}


def test_models_endpoint_returns_503_when_database_is_unavailable() -> None:
    # Puerto 1: nada escucha ahí, la conexión se rechaza al momento.
    settings = Settings(
        _env_file=None, database_url="postgresql+asyncpg://user:pass@127.0.0.1:1/missing"
    )
    client = TestClient(create_app(settings))

    response = client.get("/api/v1/models")

    assert response.status_code == 503
    assert "base de datos" in response.json()["detail"]
    # El router no depende de la base de datos.
    assert client.post("/api/v1/route", json={"prompt": "Hola"}).status_code == 200
