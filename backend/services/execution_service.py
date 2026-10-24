"""Execution Layer (ADR-0001): decide, resuelve y ejecuta en un inference provider.

No depende de FastAPI, SQLAlchemy, HTTP ni del router: la decisión y la resolución
del modelo llegan como puertos inyectados (Decider, ModelResolver), y los resultados
son tipos normalizados. En S2 no hay reintentos ni fallback: los errores se
devuelven tipados.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import replace
from typing import Any

from domain.completions import CompletionRequest, CompletionResult, Message
from domain.execution import Decider, Execution, ModelResolver
from providers.errors import ProviderError, ProviderTimeout, ProviderUnavailable
from providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 60.0


class ExecutionService:
    def __init__(
        self,
        registry: ProviderRegistry,
        *,
        decider: Decider[Any] | None = None,
        resolver: ModelResolver | None = None,
        default_timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if default_timeout_seconds <= 0:
            raise ValueError("default_timeout_seconds debe ser positivo.")
        self._registry = registry
        # Solo hacen falta para execute(); complete() funciona sin ellos.
        self._decider = decider
        self._resolver = resolver
        self._default_timeout_seconds = default_timeout_seconds
        self._clock = clock

    async def execute(
        self,
        prompt: str,
        *,
        max_output_tokens: int,
        temperature: float | None = None,
        timeout: float | None = None,
        request_id: str | None = None,
    ) -> Execution:
        """Flujo completo de ADR-0001: decide el modelo, resuelve dónde se ejecuta y lo ejecuta.

        Los errores de resolución (ModelNotAvailable) y de ejecución se propagan tipados.
        """
        if self._decider is None or self._resolver is None:
            raise RuntimeError("ExecutionService.execute() necesita un Decider y un ModelResolver.")

        decision = self._decider.decide(prompt)
        target = await self._resolver.resolve(decision.model_id)
        request = CompletionRequest(
            provider_model_id=target.provider_model_id,
            messages=(Message("user", prompt),),
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            timeout=timeout,
            request_id=request_id,
        )
        result = await self.complete(target.inference_provider, request)
        return Execution(decision=decision, result=result)

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
