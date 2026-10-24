"""Execution Layer (ADR-0001): ejecuta una petición en un inference provider.

No depende de FastAPI, SQLAlchemy, HTTP ni del router: recibe la clave del
inference provider ya resuelta y devuelve tipos normalizados. En S2 no hay
reintentos ni fallback: los errores se devuelven tipados.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import replace

from domain.completions import CompletionRequest, CompletionResult
from providers.errors import ProviderError, ProviderTimeout, ProviderUnavailable
from providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 60.0


class ExecutionService:
    def __init__(
        self,
        registry: ProviderRegistry,
        *,
        default_timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if default_timeout_seconds <= 0:
            raise ValueError("default_timeout_seconds debe ser positivo.")
        self._registry = registry
        self._default_timeout_seconds = default_timeout_seconds
        self._clock = clock

    async def complete(self, inference_provider: str, request: CompletionRequest) -> CompletionResult:
        """Ejecuta `request` en el proveedor indicado y mide la latencia en este proceso.

        Lanza ProviderNotConfigured si el proveedor no está registrado, ProviderTimeout
        si no responde a tiempo y ProviderUnavailable ante cualquier error no tipado.
        """
        provider = self._registry.get(inference_provider)
        timeout = request.timeout or self._default_timeout_seconds
        started = self._clock()

        try:
            async with asyncio.timeout(timeout):
                result = await provider.complete(request)
        except ProviderError:
            raise
        except TimeoutError as error:
            raise ProviderTimeout(
                f"El inference provider {inference_provider!r} no respondió en {timeout:g} s.",
                inference_provider=inference_provider,
            ) from error
        except Exception as error:
            # Un error sin tipar es un fallo del proveedor o de su integración: se registra
            # con la traza completa y se devuelve tipado. Nunca se registra el prompt.
            logger.exception(
                "Error inesperado en el inference provider",
                extra={"inference_provider": inference_provider, "request_id": request.request_id},
            )
            raise ProviderUnavailable(
                f"El inference provider {inference_provider!r} falló de forma inesperada.",
                inference_provider=inference_provider,
            ) from error

        latency_ms = round((self._clock() - started) * 1000)
        return replace(result, latency_ms=latency_ms)
