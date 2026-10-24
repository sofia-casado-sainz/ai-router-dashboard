"""Puertos de la Execution Layer (ADR-0001).

ExecutionService depende de estas interfaces, no del router ni del catálogo. Las
implementaciones concretas viven en `services/` y se inyectan al construirlo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

from domain.completions import CompletionResult

DetailsT = TypeVar("DetailsT")
DetailsT_co = TypeVar("DetailsT_co", covariant=True)


@dataclass(frozen=True, slots=True)
class Decision(Generic[DetailsT]):
    # Id del modelo elegido por la capa de decisión (p. ej. "gpt").
    model_id: str
    # Decisión completa, que ExecutionService no interpreta y devuelve tal cual
    # (p. ej. la misma respuesta que POST /api/v1/route).
    details: DetailsT


@dataclass(frozen=True, slots=True)
class ResolvedModel:
    """Dónde se ejecuta un modelo: sistema de ejecución e id del modelo en él."""

    inference_provider: str
    provider_model_id: str


@dataclass(frozen=True, slots=True)
class Execution:
    decision: Decision[Any]
    result: CompletionResult


class Decider(Protocol[DetailsT_co]):
    """Capa de decisión: elige el modelo para un prompt."""

    def decide(self, prompt: str) -> Decision[DetailsT_co]: ...


class ModelResolver(Protocol):
    """Traduce el modelo elegido a dónde se ejecuta.

    Lanza ModelNotAvailable si el modelo no existe o no es ejecutable.
    """

    async def resolve(self, model_id: str) -> ResolvedModel: ...
