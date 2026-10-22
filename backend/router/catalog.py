"""Catálogo de modelos: única fuente de verdad de los modelos disponibles.

El frontend no mantiene su propia lista; recibe id, nombre y proveedor en
cada respuesta de la API. En el Sprint S1 este catálogo pasará a PostgreSQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ModelId(StrEnum):
    CLAUDE_SONNET = "claude-sonnet"
    GEMINI = "gemini"
    GPT = "gpt"
    DEEPSEEK = "deepseek"


@dataclass(frozen=True, slots=True)
class ModelInfo:
    id: ModelId
    name: str
    provider: str
    # Precio simulado en € por cada 1.000 tokens.
    price_per_1k_tokens: float


MODELS: dict[ModelId, ModelInfo] = {
    ModelId.CLAUDE_SONNET: ModelInfo(ModelId.CLAUDE_SONNET, "Claude Sonnet", "Anthropic", 0.015),
    ModelId.GEMINI: ModelInfo(ModelId.GEMINI, "Gemini", "Google", 0.005),
    ModelId.GPT: ModelInfo(ModelId.GPT, "GPT", "OpenAI", 0.01),
    ModelId.DEEPSEEK: ModelInfo(ModelId.DEEPSEEK, "DeepSeek", "DeepSeek", 0.001),
}


def get_model(model_id: ModelId) -> ModelInfo:
    return MODELS[model_id]
