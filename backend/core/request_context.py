"""Identificador de la petición en curso (ADR-0002 §6).

Lo fija RequestIdMiddleware al empezar cada petición HTTP y lo leen los logs, los
errores y la ejecución de modelos para correlacionarlos.
"""

from __future__ import annotations

import re
import uuid
from contextvars import ContextVar, Token

REQUEST_ID_HEADER = "X-Request-ID"

# Valores aceptados en un X-Request-ID entrante; cualquier otro se sustituye.
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """request_id de la petición en curso; None fuera de una petición."""
    return _request_id.get()


def resolve_request_id(incoming: str | None) -> str:
    """Reutiliza el identificador entrante si es válido; si no, genera un UUID4."""
    if incoming is not None and _VALID_REQUEST_ID.fullmatch(incoming):
        return incoming
    return str(uuid.uuid4())


def bind_request_id(request_id: str) -> Token[str | None]:
    return _request_id.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    _request_id.reset(token)
