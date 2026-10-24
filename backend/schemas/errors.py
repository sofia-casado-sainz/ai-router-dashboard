from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Códigos estables (ADR-0002 §5): los clientes deben usar `code`, no interpretar `detail`.
ErrorCode = Literal[
    "completions_disabled",
    "provider_not_configured",
    "provider_unavailable",
    "provider_timeout",
    "provider_rate_limited",
    "provider_auth_error",
    "provider_bad_request",
    "model_not_available",
    "catalog_unavailable",
    "provider_error",
]


class ErrorResponse(BaseModel):
    """Error de la API, salvo la validación de la petición (422)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "detail": "El proveedor no respondió a tiempo.",
                    "code": "provider_timeout",
                    "request_id": "6f1c2b8e-3d4a-4f5b-9c6d-7e8f9a0b1c2d",
                }
            ]
        }
    )

    detail: str = Field(description="Mensaje fijo para el código; nunca texto de un proveedor.")
    code: ErrorCode
    request_id: str | None = Field(description="Mismo valor que la cabecera X-Request-ID.")
