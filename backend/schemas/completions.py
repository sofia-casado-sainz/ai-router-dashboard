from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.completions import (
    MAX_OUTPUT_TOKENS_LIMIT,
    CompletionResult,
    CostSource,
    FinishReason,
    UsageSource,
)
from schemas.route_request import RouteResponse


class CompletionCreateRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"examples": [{"prompt": "Resume este correo para mi equipo"}]},
    )

    # Mismas reglas que el prompt de POST /api/v1/route.
    prompt: str = Field(min_length=1, max_length=20_000, description="Prompt del usuario.")
    max_output_tokens: int = Field(
        default=512, ge=1, le=MAX_OUTPUT_TOKENS_LIMIT, description="Tope de tokens de salida."
    )
    temperature: float | None = Field(default=None, ge=0, le=2)


class UsageResponse(BaseModel):
    input_tokens: int | None
    output_tokens: int | None
    source: UsageSource


class CostResponse(BaseModel):
    amount: float = Field(ge=0)
    currency: str = Field(description="Código ISO 4217.")
    source: CostSource


class CompletionResultResponse(BaseModel):
    content: str
    inference_provider: str = Field(description="Sistema que ejecutó el modelo (p. ej. fake).")
    provider_model_id: str = Field(description="Modelo usado realmente en ese sistema.")
    finish_reason: FinishReason
    usage: UsageResponse
    cost: CostResponse
    latency_ms: int | None = Field(description="Latencia medida por el backend.")
    provider_request_id: str | None

    @classmethod
    def from_result(cls, result: CompletionResult) -> CompletionResultResponse:
        return cls(
            content=result.content,
            inference_provider=result.inference_provider,
            provider_model_id=result.provider_model_id,
            finish_reason=result.finish_reason,
            usage=UsageResponse(
                input_tokens=result.usage.input_tokens,
                output_tokens=result.usage.output_tokens,
                source=result.usage.source,
            ),
            cost=CostResponse(
                amount=float(result.cost.amount),
                currency=result.cost.currency,
                source=result.cost.source,
            ),
            latency_ms=result.latency_ms,
            provider_request_id=result.provider_request_id,
        )


class CompletionResponse(BaseModel):
    # La misma decisión que devuelve POST /api/v1/route para ese prompt.
    decision: RouteResponse
    completion: CompletionResultResponse
