"""Contrato de errores de la API (ADR-0002 §5).

Todas las respuestas de error, salvo la validación de la petición (422), son un
ErrorResponse con un mensaje fijo por código. El mensaje original de un proveedor
nunca llega al cliente: se registra en el log, correlacionado por request_id.
"""

from __future__ import annotations

import math
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

from core.request_context import get_request_id
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
from schemas.errors import ErrorCode, ErrorResponse

ERROR_MESSAGES: dict[ErrorCode, str] = {
    "completions_disabled": "La ejecución de modelos está desactivada (COMPLETIONS_ENABLED=false).",
    "provider_not_configured": "El proveedor que ejecuta este modelo no está configurado.",
    "provider_unavailable": "El proveedor que ejecuta este modelo no está disponible.",
    "provider_timeout": "El proveedor no respondió a tiempo.",
    "provider_rate_limited": "El proveedor ha limitado las peticiones; vuelve a intentarlo más tarde.",
    "provider_auth_error": "El proveedor rechazó las credenciales configuradas.",
    "provider_bad_request": "El proveedor rechazó la petición.",
    "model_not_available": "El modelo elegido no está disponible para ejecutarse.",
    "catalog_unavailable": (
        "El catálogo de modelos no está disponible: no se pudo conectar con la base de datos."
    ),
    "provider_error": "El proveedor devolvió un error.",
}

# Errores tipados de los proveedores → HTTP y código (ADR-0001, con el cambio de ADR-0002:
# ProviderBadRequest pasa a 400 y 422 queda solo para la validación de la petición).
PROVIDER_ERRORS: tuple[tuple[type[ProviderError], int, ErrorCode], ...] = (
    (ProviderNotConfigured, status.HTTP_503_SERVICE_UNAVAILABLE, "provider_not_configured"),
    (ProviderUnavailable, status.HTTP_503_SERVICE_UNAVAILABLE, "provider_unavailable"),
    (ProviderTimeout, status.HTTP_504_GATEWAY_TIMEOUT, "provider_timeout"),
    (ProviderRateLimited, status.HTTP_429_TOO_MANY_REQUESTS, "provider_rate_limited"),
    (ProviderAuthError, status.HTTP_502_BAD_GATEWAY, "provider_auth_error"),
    (ProviderBadRequest, status.HTTP_400_BAD_REQUEST, "provider_bad_request"),
    (ModelNotAvailable, status.HTTP_502_BAD_GATEWAY, "model_not_available"),
)

ERROR_DESCRIPTIONS: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "El proveedor rechazó la petición (`provider_bad_request`).",
    status.HTTP_429_TOO_MANY_REQUESTS: "El proveedor limitó la petición (`provider_rate_limited`), con `Retry-After`.",
    status.HTTP_502_BAD_GATEWAY: (
        "Modelo no disponible, credenciales rechazadas u otro error del proveedor "
        "(`model_not_available`, `provider_auth_error`, `provider_error`)."
    ),
    status.HTTP_503_SERVICE_UNAVAILABLE: (
        "Ejecución desactivada, proveedor no configurado o no disponible, o catálogo no "
        "disponible (`completions_disabled`, `provider_not_configured`, `provider_unavailable`, "
        "`catalog_unavailable`)."
    ),
    status.HTTP_504_GATEWAY_TIMEOUT: "El proveedor no respondió a tiempo (`provider_timeout`).",
}


class ApiError(Exception):
    """Error de la API que se responde como ErrorResponse."""

    def __init__(
        self, status_code: int, code: ErrorCode, *, headers: dict[str, str] | None = None
    ) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.headers = headers


def retry_after_header(seconds: float) -> str:
    """Segundos enteros, redondeados hacia arriba y nunca menos de 1."""
    return str(max(1, math.ceil(seconds)))


def from_provider_error(error: ProviderError) -> ApiError:
    status_code, code = next(
        ((status_code, code) for kind, status_code, code in PROVIDER_ERRORS if isinstance(error, kind)),
        (status.HTTP_502_BAD_GATEWAY, "provider_error"),
    )
    headers = None
    if isinstance(error, ProviderRateLimited) and error.retry_after is not None:
        headers = {"Retry-After": retry_after_header(error.retry_after)}
    return ApiError(status_code, code, headers=headers)


async def api_error_handler(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, ApiError)
    body = ErrorResponse(
        detail=ERROR_MESSAGES[error.code], code=error.code, request_id=get_request_id()
    )
    return JSONResponse(body.model_dump(), status_code=error.status_code, headers=error.headers)


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """Documentación OpenAPI de las respuestas de error de un endpoint."""
    return {
        code: {"model": ErrorResponse, "description": ERROR_DESCRIPTIONS[code]} for code in status_codes
    }
