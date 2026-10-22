"""Selección de modelo basada en reglas por palabras clave (versión mock).

Las reglas se evalúan en orden y gana la primera con alguna coincidencia.
Las keywords se comparan como subcadena, sin tildes ni mayúsculas, de modo
que "compara" cubre comparar/comparativa/comparación.
"""

from __future__ import annotations

import math
import unicodedata
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


@dataclass(frozen=True, slots=True)
class RoutingRule:
    model_id: ModelId
    keywords: tuple[str, ...]
    reason: str
    base_complexity: int


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    model: ModelInfo
    complexity: int
    estimated_tokens: int
    estimated_cost: float
    reason: str
    matched_keywords: list[str]

    @property
    def is_fallback(self) -> bool:
        return not self.matched_keywords


MODELS: dict[ModelId, ModelInfo] = {
    ModelId.CLAUDE_SONNET: ModelInfo(ModelId.CLAUDE_SONNET, "Claude Sonnet", "Anthropic", 0.015),
    ModelId.GEMINI: ModelInfo(ModelId.GEMINI, "Gemini", "Google", 0.005),
    ModelId.GPT: ModelInfo(ModelId.GPT, "GPT", "OpenAI", 0.01),
    ModelId.DEEPSEEK: ModelInfo(ModelId.DEEPSEEK, "DeepSeek", "DeepSeek", 0.001),
}

ROUTING_RULES: tuple[RoutingRule, ...] = (
    RoutingRule(
        model_id=ModelId.CLAUDE_SONNET,
        keywords=("arquitectura", "escalabilidad", "microservicio"),
        reason="Arquitectura software avanzada",
        base_complexity=8,
    ),
    RoutingRule(
        model_id=ModelId.GEMINI,
        keywords=("investiga", "compara", "analizar mercado", "analisis de mercado"),
        reason="Investigación y análisis comparativo",
        base_complexity=6,
    ),
    RoutingRule(
        model_id=ModelId.GPT,
        keywords=("programa", "bug", "typescript", "python"),
        reason="Tarea de programación",
        base_complexity=7,
    ),
    RoutingRule(
        model_id=ModelId.DEEPSEEK,
        keywords=("resumen", "resumir", "correo", "email", "texto corto"),
        reason="Texto breve: basta un modelo ligero de bajo coste",
        base_complexity=3,
    ),
)

FALLBACK_RULE = RoutingRule(
    model_id=ModelId.GPT,
    keywords=(),
    reason="Consulta de propósito general",
    base_complexity=5,
)

# Tokens de salida simulados por cada punto de complejidad.
OUTPUT_TOKENS_PER_COMPLEXITY = 150
# Aproximación habitual: ~4 caracteres por token.
CHARS_PER_TOKEN = 4


def normalize_text(text: str) -> str:
    """Minúsculas y sin tildes, para que "Código" y "codigo" coincidan."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def estimate_complexity(base: int, prompt: str) -> int:
    words = len(prompt.split())
    bonus = 2 if words > 120 else 1 if words > 60 else 0
    return max(1, min(10, base + bonus))


def select_model(prompt: str) -> RoutingDecision:
    text = normalize_text(prompt)

    for rule in ROUTING_RULES:
        matched = [kw for kw in rule.keywords if normalize_text(kw) in text]
        if matched:
            return _build_decision(rule, prompt, matched)

    return _build_decision(FALLBACK_RULE, prompt, [])


def _build_decision(rule: RoutingRule, prompt: str, matched: list[str]) -> RoutingDecision:
    model = MODELS[rule.model_id]
    complexity = estimate_complexity(rule.base_complexity, prompt)
    input_tokens = math.ceil(len(prompt) / CHARS_PER_TOKEN)
    estimated_tokens = input_tokens + complexity * OUTPUT_TOKENS_PER_COMPLEXITY
    estimated_cost = estimated_tokens / 1000 * model.price_per_1k_tokens

    return RoutingDecision(
        model=model,
        complexity=complexity,
        estimated_tokens=estimated_tokens,
        estimated_cost=round(estimated_cost, 4),
        reason=rule.reason,
        matched_keywords=matched,
    )
