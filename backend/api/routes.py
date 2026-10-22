from fastapi import APIRouter

from schemas.route_request import RouteRequest, RouteResponse
from services.routing_service import route_prompt

router = APIRouter()


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/route", response_model=RouteResponse, tags=["router"])
def route(request: RouteRequest) -> RouteResponse:
    """Analiza el prompt y devuelve el modelo seleccionado (simulado)."""
    return route_prompt(request.prompt)
