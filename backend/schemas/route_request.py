from pydantic import BaseModel, ConfigDict, Field

from router.catalog import ModelId


class RouteRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"examples": [{"prompt": "Diseña una arquitectura SaaS"}]},
    )

    prompt: str = Field(min_length=1, max_length=20_000, description="Prompt del usuario.")


class RouteResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "selected_model": "claude-sonnet",
                    "complexity": 8,
                    "estimated_cost": 0.0181,
                    "reason": "Arquitectura software avanzada",
                    "model_name": "Claude Sonnet",
                    "provider": "Anthropic",
                    "estimated_tokens": 1207,
                    "matched_keywords": ["arquitectura"],
                    "is_fallback": False,
                }
            ]
        }
    )

    selected_model: ModelId
    complexity: int = Field(ge=1, le=10)
    estimated_cost: float = Field(ge=0, description="Coste estimado en €.")
    reason: str

    # Campos adicionales para la UI (ModelSelectionCard).
    model_name: str
    provider: str
    estimated_tokens: int = Field(ge=0)
    matched_keywords: list[str]
    is_fallback: bool
