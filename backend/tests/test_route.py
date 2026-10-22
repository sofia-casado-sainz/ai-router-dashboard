import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@pytest.mark.parametrize(
    ("prompt", "expected_model"),
    [
        ("Diseña una arquitectura SaaS", "claude-sonnet"),
        ("Problemas de ESCALABILIDAD con microservicios", "claude-sonnet"),
        ("Investiga y compara bases de datos vectoriales", "gemini"),
        ("Necesito analizar mercado para un lanzamiento", "gemini"),
        ("Tengo un bug en TypeScript", "gpt"),
        ("Quiero programar un script en Python", "gpt"),
        ("Hazme un resumen de este correo", "deepseek"),
        ("Hola, ¿qué tal?", "gpt"),
    ],
)
def test_route_selects_expected_model(prompt: str, expected_model: str) -> None:
    response = client.post("/api/v1/route", json={"prompt": prompt})

    assert response.status_code == 200
    assert response.json()["selected_model"] == expected_model


def test_route_architecture_example() -> None:
    body = client.post("/api/v1/route", json={"prompt": "Diseña una arquitectura SaaS"}).json()

    assert body["selected_model"] == "claude-sonnet"
    assert body["complexity"] == 8
    assert body["reason"] == "Arquitectura software avanzada"
    assert round(body["estimated_cost"], 2) == 0.02
    assert body["matched_keywords"] == ["arquitectura"]
    assert body["is_fallback"] is False


def test_route_fallback_is_flagged() -> None:
    body = client.post("/api/v1/route", json={"prompt": "Hola"}).json()

    assert body["is_fallback"] is True
    assert body["matched_keywords"] == []


@pytest.mark.parametrize("payload", [{}, {"prompt": ""}, {"prompt": "   "}])
def test_route_rejects_empty_prompt(payload: dict) -> None:
    assert client.post("/api/v1/route", json=payload).status_code == 422
