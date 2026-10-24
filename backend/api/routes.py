import logging

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.exc import SQLAlchemyError

from api.dependencies import ExecutionServiceDep, ModelCatalogServiceDep
from api.errors import ApiError, error_responses, from_provider_error
from core.request_context import get_request_id
from providers.errors import ProviderAuthError, ProviderError
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
    responses=error_responses(status.HTTP_503_SERVICE_UNAVAILABLE),
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
        raise ApiError(status.HTTP_503_SERVICE_UNAVAILABLE, "catalog_unavailable") from error

    return ModelListResponse(models=[ModelResponse.from_entry(entry) for entry in entries])


def require_completions_enabled(request: Request) -> None:
    """El endpoint existe siempre; mientras la ejecución esté desactivada responde 503."""
    if not request.app.state.settings.completions_enabled:
        raise ApiError(status.HTTP_503_SERVICE_UNAVAILABLE, "completions_disabled")


@router.post(
    "/completions",
    response_model=CompletionResponse,
    tags=["completions"],
    name="create_completion",
    dependencies=[Depends(require_completions_enabled)],
    responses=error_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_429_TOO_MANY_REQUESTS,
        status.HTTP_502_BAD_GATEWAY,
        status.HTTP_503_SERVICE_UNAVAILABLE,
        status.HTTP_504_GATEWAY_TIMEOUT,
    ),
)
async def create_completion(
    body: CompletionCreateRequest, service: ExecutionServiceDep
) -> CompletionResponse:
    """Decide el modelo (igual que /route) y lo ejecuta con el inference provider del catálogo."""
    try:
        execution = await service.execute(
            body.prompt,
            max_output_tokens=body.max_output_tokens,
            temperature=body.temperature,
            request_id=get_request_id(),
        )
    except ProviderError as error:
        api_error = from_provider_error(error)
        log = logger.error if isinstance(error, ProviderAuthError) else logger.warning
        # La causa original solo va al log; al cliente le llega un mensaje fijo por código.
        log(
            "La ejecución del modelo falló",
            extra={
                "error": type(error).__name__,
                "code": api_error.code,
                "error_detail": str(error),
                "inference_provider": error.inference_provider,
            },
        )
        raise api_error from error
    except (SQLAlchemyError, OSError) as error:
        logger.exception("No se pudo leer el catálogo de modelos")
        raise ApiError(status.HTTP_503_SERVICE_UNAVAILABLE, "catalog_unavailable") from error

    result = execution.result
    # Correlación request_id ↔ provider_request_id (el filtro de logging añade el
    # request_id). Nunca se registra el prompt.
    logger.info(
        "Ejecución completada",
        extra={
            "inference_provider": result.inference_provider,
            "provider_model_id": result.provider_model_id,
            "provider_request_id": result.provider_request_id,
            "finish_reason": result.finish_reason,
            "latency_ms": result.latency_ms,
        },
    )
    return CompletionResponse(
        decision=execution.decision.details,
        completion=CompletionResultResponse.from_result(execution.result),
    )
