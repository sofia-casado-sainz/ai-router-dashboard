import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import SQLAlchemyError

from api.dependencies import ExecutionServiceDep, ModelCatalogServiceDep
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
from schemas.completions import (
    CompletionCreateRequest,
    CompletionResponse,
    CompletionResultResponse,
)
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


# Errores tipados de los inference providers → HTTP (tabla de ADR-0001).
PROVIDER_ERROR_STATUS: dict[type[ProviderError], int] = {
    ProviderNotConfigured: status.HTTP_503_SERVICE_UNAVAILABLE,
    ProviderUnavailable: status.HTTP_503_SERVICE_UNAVAILABLE,
    ProviderTimeout: status.HTTP_504_GATEWAY_TIMEOUT,
    ProviderRateLimited: status.HTTP_429_TOO_MANY_REQUESTS,
    ProviderAuthError: status.HTTP_502_BAD_GATEWAY,
    ProviderBadRequest: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ModelNotAvailable: status.HTTP_502_BAD_GATEWAY,
}

COMPLETIONS_DISABLED_DETAIL = (
    "La ejecución de modelos está desactivada (COMPLETIONS_ENABLED=false)."
)


def require_completions_enabled(request: Request) -> None:
    """El endpoint existe siempre; mientras la ejecución esté desactivada responde 503."""
    if not request.app.state.settings.completions_enabled:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, COMPLETIONS_DISABLED_DETAIL)


def provider_error_to_http(error: ProviderError) -> HTTPException:
    status_code = next(
        (code for kind, code in PROVIDER_ERROR_STATUS.items() if isinstance(error, kind)),
        status.HTTP_502_BAD_GATEWAY,
    )
    headers = None
    if isinstance(error, ProviderRateLimited) and error.retry_after is not None:
        headers = {"Retry-After": str(round(error.retry_after))}
    return HTTPException(status_code, str(error), headers=headers)


@router.post(
    "/completions",
    response_model=CompletionResponse,
    tags=["completions"],
    name="create_completion",
    dependencies=[Depends(require_completions_enabled)],
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "El proveedor limitó la petición."},
        status.HTTP_502_BAD_GATEWAY: {"description": "Modelo no disponible o credenciales rechazadas."},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Ejecución desactivada, proveedor no disponible o catálogo no disponible."
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {"description": "El proveedor no respondió a tiempo."},
    },
)
async def create_completion(
    body: CompletionCreateRequest, service: ExecutionServiceDep
) -> CompletionResponse:
    """Decide el modelo (igual que /route) y lo ejecuta con el inference provider del catálogo."""
    try:
        execution = await service.execute(
            body.prompt, max_output_tokens=body.max_output_tokens, temperature=body.temperature
        )
    except ProviderError as error:
        log = logger.error if isinstance(error, ProviderAuthError) else logger.warning
        log(
            "La ejecución del modelo falló",
            extra={"error": type(error).__name__, "inference_provider": error.inference_provider},
        )
        raise provider_error_to_http(error) from error
    except (SQLAlchemyError, OSError) as error:
        logger.exception("No se pudo leer el catálogo de modelos")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "El catálogo de modelos no está disponible: no se pudo conectar con la base de datos.",
        ) from error

    return CompletionResponse(
        decision=execution.decision.details,
        completion=CompletionResultResponse.from_result(execution.result),
    )
