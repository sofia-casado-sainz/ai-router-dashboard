from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from services.model_catalog_service import ModelCatalogEntry


class ModelPriceResponse(BaseModel):
    input_cost_per_million: float = Field(ge=0, description="Coste por millón de tokens de entrada.")
    output_cost_per_million: float = Field(ge=0, description="Coste por millón de tokens de salida.")
    currency: str = Field(description="Código ISO 4217.")


class ModelResponse(BaseModel):
    id: UUID
    provider: str
    model_key: str
    display_name: str
    context_window: int = Field(gt=0, description="Tokens de contexto.")
    active: bool = Field(description="Si el modelo está disponible para el enrutado.")
    current_price: ModelPriceResponse | None = Field(description="Precio vigente; null si no tiene.")

    @classmethod
    def from_entry(cls, entry: ModelCatalogEntry) -> ModelResponse:
        model, price = entry.model, entry.current_price
        return cls(
            id=model.id,
            provider=model.provider,
            model_key=model.model_key,
            display_name=model.display_name,
            context_window=model.context_window,
            active=model.active,
            current_price=None
            if price is None
            else ModelPriceResponse(
                input_cost_per_million=float(price.input_cost_per_million),
                output_cost_per_million=float(price.output_cost_per_million),
                currency=price.currency,
            ),
        )


class ModelListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "models": [
                        {
                            "id": "6f1c2b8e-3d4a-4f5b-9c6d-7e8f9a0b1c2d",
                            "provider": "anthropic",
                            "model_key": "claude-sonnet",
                            "display_name": "Claude Sonnet",
                            "context_window": 200000,
                            "active": True,
                            "current_price": {
                                "input_cost_per_million": 2.5,
                                "output_cost_per_million": 12.0,
                                "currency": "USD",
                            },
                        }
                    ]
                }
            ]
        }
    )

    models: list[ModelResponse]
