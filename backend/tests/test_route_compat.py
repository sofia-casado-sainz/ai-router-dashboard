"""El catálogo persistente (S1) no cambia las decisiones del router."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_route_response_is_unchanged() -> None:
    response = client.post("/api/v1/route", json={"prompt": "Resume este correo para mi equipo"})

    assert response.json() == {
        "selected_model": "deepseek",
        "complexity": 3,
        "estimated_cost": 0.0005,
        "reason": "Texto breve: basta un modelo ligero de bajo coste",
        "model_name": "DeepSeek",
        "provider": "DeepSeek",
        "estimated_tokens": 459,
        "matched_keywords": ["correo"],
        "is_fallback": False,
    }
