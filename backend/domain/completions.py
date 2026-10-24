"""Tipos normalizados de ejecución de modelos (ADR-0001).

Todos los inference providers reciben y devuelven estos tipos. No dependen de
ningún framework, proveedor ni transporte.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Role = Literal["system", "user", "assistant"]
FinishReason = Literal["stop", "length", "content_filter", "error"]
UsageSource = Literal["reported", "estimated"]
CostSource = Literal["reported", "estimated_from_catalog"]
HealthStatus = Literal["ok", "degraded", "unavailable"]

# Tope global de tokens de salida por petición: limita lo que puede gastar una sola ejecución.
MAX_OUTPUT_TOKENS_LIMIT = 8_192


@dataclass(frozen=True, slots=True)
class Message:
    role: Role
    content: str


@dataclass(frozen=True, slots=True)
class CompletionRequest:
    # Identificador del modelo en el inference provider (no el id del router).
    provider_model_id: str
    messages: tuple[Message, ...]
    max_output_tokens: int
    temperature: float | None = None
    # Segundos. None: se aplica el timeout por defecto de ExecutionService.
    timeout: float | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        # Acepta cualquier secuencia, pero guarda una tupla para que la petición sea inmutable.
        object.__setattr__(self, "messages", tuple(self.messages))
        if not self.provider_model_id:
            raise ValueError("provider_model_id no puede estar vacío.")
        if not self.messages:
            raise ValueError("La petición necesita al menos un mensaje.")
        if not 0 < self.max_output_tokens <= MAX_OUTPUT_TOKENS_LIMIT:
            raise ValueError(
                f"max_output_tokens debe estar entre 1 y {MAX_OUTPUT_TOKENS_LIMIT}."
            )
        if self.temperature is not None and not 0 <= self.temperature <= 2:
            raise ValueError("temperature debe estar entre 0 y 2.")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("timeout debe ser positivo.")


@dataclass(frozen=True, slots=True)
class Usage:
    # None si el proveedor no lo informa: nunca se inventa.
    input_tokens: int | None
    output_tokens: int | None
    source: UsageSource

    def __post_init__(self) -> None:
        for tokens in (self.input_tokens, self.output_tokens):
            if tokens is not None and tokens < 0:
                raise ValueError("El número de tokens no puede ser negativo.")


@dataclass(frozen=True, slots=True)
class Cost:
    amount: Decimal
    # Código ISO 4217: cada coste lleva su moneda.
    currency: str
    source: CostSource

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("El coste no puede ser negativo.")
        if len(self.currency) != 3 or self.currency != self.currency.upper():
            raise ValueError("currency debe ser un código ISO 4217 en mayúsculas.")


@dataclass(frozen=True, slots=True)
class CompletionResult:
    content: str
    inference_provider: str
    # El modelo que se usó realmente; puede no coincidir con el pedido.
    provider_model_id: str
    finish_reason: FinishReason
    usage: Usage
    cost: Cost
    # Lo mide ExecutionService en nuestro proceso; el proveedor puede dejarlo vacío.
    latency_ms: int | None = None
    provider_request_id: str | None = None


@dataclass(frozen=True, slots=True)
class CompletionChunk:
    delta: str
    # Solo en el último fragmento.
    finish_reason: FinishReason | None = None
    usage: Usage | None = None


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    streaming: bool = False
    # Los datos no salen de la máquina del usuario (p. ej. Ollama).
    local: bool = False
    reports_cost: bool = False
    lists_models: bool = False


@dataclass(frozen=True, slots=True)
class ProviderHealth:
    status: HealthStatus
    latency_ms: int | None = None
    detail: str | None = None
