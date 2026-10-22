from fastapi import APIRouter

from schemas.health import HealthResponse
from schemas.route_request import RouteRequest, RouteResponse
from services.routing_service import route_prompt

router = APIRouter()

# `name` fija el operationId de OpenAPI: los tipos y el cliente TS se generarán a partir de él.


@router.get("/health", response_model=HealthResponse, tags=["system"], name="get_health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/route", response_model=RouteResponse, tags=["router"], name="route_prompt")
def route(request: RouteRequest) -> RouteResponse:
    """Analiza el prompt y devuelve el modelo seleccionado (simulado)."""
    return route_prompt(request.prompt)
