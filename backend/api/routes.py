import logging

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError

from api.dependencies import ModelCatalogServiceDep
from schemas.health import HealthResponse
from schemas.models import ModelListResponse, ModelResponse
from schemas.route_request import RouteRequest, RouteResponse
from services.routing_service import route_prompt

logger = logging.getLogger(__name__)

router = APIRouter()

# `name` fija el operationId de OpenAPI: los tipos y el cliente TS se generarán a partir de él.


@router.get("/health", response_model=HealthResponse, tags=["system"], name="get_health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/route", response_model=RouteResponse, tags=["router"], name="route_prompt")
def route(request: RouteRequest) -> RouteResponse:
    """Analiza el prompt y devuelve el modelo seleccionado (simulado)."""
    return route_prompt(request.prompt)


@router.get(
    "/models",
    response_model=ModelListResponse,
    tags=["models"],
    name="list_models",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Base de datos no disponible."}},
)
async def list_models(
    service: ModelCatalogServiceDep,
    active_only: bool = Query(False, description="Devolver solo los modelos activos."),
) -> ModelListResponse:
    """Catálogo persistente de modelos con su precio vigente."""
    try:
        entries = await (service.get_active_models() if active_only else service.get_models())
    # OSError: el driver no llega al servidor (conexión rechazada, host desconocido…).
    except (SQLAlchemyError, OSError) as error:
        logger.exception("No se pudo leer el catálogo de modelos")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "El catálogo de modelos no está disponible: no se pudo conectar con la base de datos.",
        ) from error

    return ModelListResponse(models=[ModelResponse.from_entry(entry) for entry in entries])
