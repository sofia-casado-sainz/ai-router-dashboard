"""Contrato común de los inference providers (ADR-0001).

Un inference provider ejecuta modelos: OpenRouter, Ollama, FakeProvider… No
confundir con `provider` del catálogo, que es el vendor que crea el modelo.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from domain.completions import (
    CompletionChunk,
    CompletionRequest,
    CompletionResult,
    ProviderCapabilities,
    ProviderHealth,
    ProviderModel,
)


@runtime_checkable
class InferenceProvider(Protocol):
    @property
    def key(self) -> str:
        """Identificador estable; coincide con `inference_provider` en el catálogo."""
        ...

    @property
    def capabilities(self) -> ProviderCapabilities: ...

    async def complete(self, request: CompletionRequest) -> CompletionResult:
        """Una respuesta completa. Los errores se lanzan como `ProviderError` tipados."""
        ...

    def stream(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]:
        """Respuesta por fragmentos.

        Forma parte del contrato desde S2 aunque nadie lo use todavía. Los proveedores
        sin `capabilities.streaming` lanzan NotImplementedError.
        """
        ...

    async def list_models(self) -> list[ProviderModel]:
        """Modelos que publica el proveedor; base de la sincronización del catálogo.

        Forma parte del contrato desde S2 aunque nadie lo use todavía. Los proveedores
        sin `capabilities.lists_models` lanzan NotImplementedError.
        """
        ...

    async def health(self) -> ProviderHealth:
        """Disponibilidad y latencia, sin consumir tokens."""
        ...
