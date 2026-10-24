"""FakeProvider: inference provider simulado (ADR-0001).

Determinista, sin red y sin coste. Sirve para tests, CI, demos y desarrollo local.
No ejecuta ningún modelo: la respuesta depende solo de la petición.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
from collections.abc import AsyncIterator
from decimal import Decimal

from domain.completions import (
    CompletionChunk,
    CompletionRequest,
    CompletionResult,
    Cost,
    ProviderCapabilities,
    ProviderHealth,
    ProviderModel,
    Usage,
)
from providers.errors import ProviderError

# Misma aproximación que usa el router para estimar tokens.
CHARS_PER_TOKEN = 4
# Fragmento del último mensaje que se cita en la respuesta.
QUOTE_LENGTH = 80


class FakeProvider:
    capabilities = ProviderCapabilities(
        streaming=False, local=False, reports_cost=True, lists_models=False
    )

    def __init__(
        self,
        *,
        key: str = "fake",
        error: ProviderError | None = None,
        delay_seconds: float = 0.0,
    ) -> None:
        # `error` y `delay_seconds` simulan fallos y lentitud en los tests de ExecutionService.
        self._key = key
        self._error = error
        self._delay_seconds = delay_seconds

    @property
    def key(self) -> str:
        return self._key

    async def complete(self, request: CompletionRequest) -> CompletionResult:
        if self._delay_seconds:
            await asyncio.sleep(self._delay_seconds)
        if self._error is not None:
            raise self._error

        quote = request.messages[-1].content.strip()[:QUOTE_LENGTH]
        content = f"[Respuesta simulada de {request.provider_model_id}] Has escrito: «{quote}»."
        finish_reason = "stop"

        max_chars = request.max_output_tokens * CHARS_PER_TOKEN
        if len(content) > max_chars:
            content, finish_reason = content[:max_chars], "length"

        input_chars = sum(len(message.content) for message in request.messages)
        return CompletionResult(
            content=content,
            inference_provider=self.key,
            provider_model_id=request.provider_model_id,
            finish_reason=finish_reason,
            usage=Usage(
                input_tokens=math.ceil(input_chars / CHARS_PER_TOKEN),
                output_tokens=math.ceil(len(content) / CHARS_PER_TOKEN),
                source="reported",
            ),
            cost=Cost(amount=Decimal("0"), currency="USD", source="reported"),
            provider_request_id=f"fake-{_digest(request)}",
        )

    def stream(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]:
        raise NotImplementedError("FakeProvider no implementa streaming todavía.")

    async def list_models(self) -> list[ProviderModel]:
        raise NotImplementedError("FakeProvider no publica un catálogo de modelos.")

    async def health(self) -> ProviderHealth:
        return ProviderHealth(status="ok", latency_ms=0)


def _digest(request: CompletionRequest) -> str:
    """Huella estable de la petición: misma petición, mismo identificador."""
    parts = [request.provider_model_id, *(f"{m.role}:{m.content}" for m in request.messages)]
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]
